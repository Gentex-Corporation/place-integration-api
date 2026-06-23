from __future__ import annotations

import hashlib
import hmac
import uuid
from datetime import datetime, timezone
from typing import Callable
from urllib.parse import quote

import paho.mqtt.client as mqtt

from .config import ALGORITHM, EXPIRE_SEC, KEEP_ALIVE_SEC, PATH, REGION, SCHEME, SERVICE
from .models import Credentials


def _hmac_sha256(key: bytes, msg: str) -> bytes:
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()


def _sha256_hex(msg: str) -> str:
    return hashlib.sha256(msg.encode("utf-8")).hexdigest().lower()


def _sign(key: bytes, msg: str) -> bytes:
    return _hmac_sha256(key, msg)


def get_signed_uri(
    *,
    access_key_id: str,
    secret_access_key: str,
    session_token: str,
    host: str,
) -> str:
    now = datetime.now(timezone.utc)
    date_stamp = now.strftime("%Y%m%d")
    amz_date = now.strftime("%Y%m%dT%H%M%SZ")
    credential_scope = f"{access_key_id}/{date_stamp}/{REGION}/{SERVICE}/aws4_request"
    signed_headers = "host"
    canonical_headers = f"host:{host}\n"
    payload_hash = _sha256_hex("")

    def enc(s: str) -> str:
        return quote(str(s), safe="")

    query = {
        "X-Amz-Algorithm": ALGORITHM,
        "X-Amz-Credential": credential_scope,
        "X-Amz-Date": amz_date,
        "X-Amz-Expires": str(EXPIRE_SEC),
        "X-Amz-SignedHeaders": signed_headers,
    }
    canonical_query = "&".join(f"{enc(k)}={enc(v)}" for k, v in sorted(query.items()))
    canonical_request = "\n".join(
        [
            "GET",
            PATH,
            canonical_query,
            canonical_headers,
            signed_headers,
            payload_hash,
        ]
    )
    request_hash = _sha256_hex(canonical_request)
    string_to_sign = "\n".join(
        [
            ALGORITHM,
            amz_date,
            f"{date_stamp}/{REGION}/{SERVICE}/aws4_request",
            request_hash,
        ]
    )
    k_date = _sign(("AWS4" + secret_access_key).encode("utf-8"), date_stamp)
    k_region = _sign(k_date, REGION)
    k_service = _sign(k_region, SERVICE)
    k_signing = _sign(k_service, "aws4_request")
    signature = hmac.new(k_signing, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

    query["X-Amz-Signature"] = signature
    query["X-Amz-Security-Token"] = session_token
    query_string = "&".join(f"{enc(k)}={enc(v)}" for k, v in sorted(query.items()))
    return f"{SCHEME}://{host}{PATH}?{query_string}"


class MqttClient:
    def __init__(
        self,
        *,
        endpoint: str,
        credentials: Credentials,
    ):
        self.endpoint = endpoint
        self.credentials = credentials
        self._client: mqtt.Client | None = None

    def connect(
        self,
        on_message: Callable[[str, bytes], None] | None = None,
        on_connect: Callable[[], None] | None = None,
    ) -> None:
        signed_uri = get_signed_uri(
            access_key_id=self.credentials.access_key_id,
            secret_access_key=self.credentials.secret_access_key,
            session_token=self.credentials.session_token,
            host=self.endpoint,
        )
        client_id = f"{self.credentials.identity_id}-{uuid.uuid4()}"

        client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=client_id,
            transport="websockets",
            protocol=mqtt.MQTTv311,
        )
        path_with_query = "/mqtt" + signed_uri.split("/mqtt", 1)[1]
        client.ws_set_options(path=path_with_query, headers={"Host": self.endpoint})
        client.tls_set()

        def _on_connect(_client, _userdata, _flags, reason_code, _properties):
            if reason_code.is_failure:
                print(f"Connect failed: {reason_code}")
                return
            print("Connected")
            if on_connect:
                try:
                    on_connect()
                except Exception as exc:
                    print(f"on_connect error: {exc}")

        def _on_message(_client, _userdata, msg):
            if on_message:
                on_message(msg.topic, msg.payload)

        def _on_disconnect(_client, _userdata, _flags, reason_code, _properties):
            print(f"Disconnected: {reason_code}")

        client.on_connect = _on_connect
        client.on_message = _on_message
        client.on_disconnect = _on_disconnect
        client.enable_logger()
        client.connect(self.endpoint, 443, KEEP_ALIVE_SEC)
        self._client = client

    def disconnect(self):
        if self._client:
            self._client.loop_stop()
            self._client.disconnect()

    def subscribe(self, topic: str, qos: int = 1) -> None:
        assert self._client is not None
        self._client.subscribe(topic, qos=qos)

    def publish(self, topic: str, payload: str | bytes = b"", qos: int = 1) -> None:
        assert self._client is not None
        data = payload.encode("utf-8") if isinstance(payload, str) else payload
        self._client.publish(topic, data, qos=qos)

    def loop_start(self):
        assert self._client is not None
        self._client.loop_start()

    def loop_forever(self) -> None:
        assert self._client is not None
        self._client.loop_forever()

