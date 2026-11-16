from __future__ import annotations

import logging
from threading import Event, Thread
from typing import cast
from unittest.mock import MagicMock, call, patch

import paho.mqtt.client as mqtt
from paho.mqtt.packettypes import PacketTypes
from paho.mqtt.reasoncodes import ReasonCode
import pytest

from place.errors import PlaceMqttConnectionError, PlaceMqttSubscriptionError
from place.messages import PlaceMessages
from place.models import Credentials
from place.mqtt_client import get_signed_uri, MqttClient


def test_get_signed_uri_includes_host_and_token() -> None:
    uri = get_signed_uri(
        access_key_id="AKIA...",
        secret_access_key="secret",
        session_token="token123",
        host="example.iot.amazonaws.com",
    )
    assert uri.startswith("wss://example.iot.amazonaws.com/mqtt?")
    assert "X-Amz-Algorithm=" in uri
    assert "X-Amz-Signature=" in uri
    assert "X-Amz-Security-Token=token123" in uri


@patch("place.mqtt_client.mqtt.Client")
@patch("place.mqtt_client.get_signed_uri")
def test_mqtt_client_connect_sets_up_client(
    mock_get_signed_uri: MagicMock,
    mock_client_cls: MagicMock,
) -> None:
    mock_get_signed_uri.return_value = "wss://example.iot.amazonaws.com/mqtt?x=1"
    client = MagicMock()
    mock_client_cls.return_value = client

    creds = Credentials(
        access_key_id="AKIA...",
        secret_access_key="secret",
        session_token="token",
        identity_id="identity-123",
    )

    mqtt_client = MqttClient(
        endpoint="example.iot.amazonaws.com",
        credentials=creds,
    )
    mqtt_client.connect()

    client.on_pre_connect(client, None)
    mock_get_signed_uri.assert_called_once()
    client.ws_set_options.assert_called()
    client.tls_set.assert_called_once()
    client.connect.assert_called_once()


def test_reconnect_resigns_static_credentials() -> None:
    credentials = Credentials("key", "secret", "token", "identity")
    wrapper = MqttClient(endpoint="example.iot.amazonaws.com", credentials=credentials)
    paths: list[str] = []

    def create_socket(client: mqtt.Client) -> MagicMock:
        paths.append(client._websocket_path)
        return MagicMock()

    with (
        patch.object(
            mqtt.Client, "_create_socket", autospec=True, side_effect=create_socket
        ),
        patch.object(mqtt.Client, "_send_connect", return_value=mqtt.MQTT_ERR_SUCCESS),
        patch(
            "place.mqtt_client.get_signed_uri",
            side_effect=[
                "wss://example.iot.amazonaws.com/mqtt?signature=first",
                "wss://example.iot.amazonaws.com/mqtt?signature=second",
            ],
        ) as sign,
    ):
        wrapper.connect()
        assert wrapper._client is not None
        wrapper._client.reconnect()

    assert paths == ["/mqtt?signature=first", "/mqtt?signature=second"]
    expected = call(
        access_key_id="key",
        secret_access_key="secret",
        session_token="token",
        host=wrapper.endpoint,
    )
    assert sign.call_args_list == [expected, expected]


def test_reconnect_retries_provider_failure_and_resubscribes(
    caplog: pytest.LogCaptureFixture,
) -> None:
    initial = Credentials("old-key", "old-secret", "old-token", "identity")
    refreshed = Credentials("new-key", "new-secret", "new-token", "identity")
    provider = MagicMock(side_effect=[RuntimeError("sensitive-token"), refreshed])
    wrapper = MqttClient(
        endpoint="example.iot.amazonaws.com",
        credentials=initial,
        credentials_provider=provider,
    )
    messages = PlaceMessages(wrapper)
    paths: list[str] = []
    reconnected = Event()
    stop_loop = Event()
    loop_calls = 0

    def on_connect() -> None:
        messages.subscribe_shadow_and_get("one")

    def connack(client: mqtt.Client) -> None:
        cast(MagicMock, client.on_connect)(
            client, None, None, ReasonCode(PacketTypes.CONNACK, identifier=0), None
        )

    def create_socket(client: mqtt.Client) -> MagicMock:
        paths.append(client._websocket_path)
        return MagicMock()

    def network_loop(client: mqtt.Client, timeout: float) -> mqtt.MQTTErrorCode:
        nonlocal loop_calls
        loop_calls += 1
        if loop_calls <= 2:
            return mqtt.MQTT_ERR_CONN_LOST
        connack(client)
        cast(MagicMock, client.on_subscribe)(
            client, None, 2, [ReasonCode(PacketTypes.SUBACK, identifier=1)], None
        )
        reconnected.set()
        stop_loop.wait(2)
        return mqtt.MQTT_ERR_CONN_LOST

    with (
        patch.object(
            mqtt.Client, "_create_socket", autospec=True, side_effect=create_socket
        ),
        patch.object(mqtt.Client, "_send_connect", return_value=mqtt.MQTT_ERR_SUCCESS),
        patch.object(mqtt.Client, "_loop", autospec=True, side_effect=network_loop),
        patch.object(mqtt.Client, "_reconnect_wait"),
        patch.object(
            mqtt.Client,
            "subscribe",
            side_effect=[(mqtt.MQTT_ERR_SUCCESS, 1), (mqtt.MQTT_ERR_SUCCESS, 2)],
        ) as subscribe,
        patch.object(mqtt.Client, "publish") as publish,
        caplog.at_level(logging.WARNING),
    ):
        wrapper.connect(on_connect=on_connect)
        client = wrapper._client
        assert client is not None
        connack(client)
        wrapper.loop_start()
        try:
            assert reconnected.wait(2)
            assert provider.call_count == 2
            assert len(paths) == 2
            assert "old-key" in paths[0] and "old-token" in paths[0]
            assert "new-key" in paths[1] and "new-token" in paths[1]
            assert wrapper.credentials == refreshed
            assert subscribe.call_count == 2
            publish.assert_called_once_with("$aws/things/one/shadow/get", b"", qos=1)
            assert "Unable to refresh MQTT credentials" in caplog.text
            assert "sensitive-token" not in caplog.text
        finally:
            wrapper.disconnect()
            stop_loop.set()
            wrapper.loop_stop()


def test_disconnect_during_credential_refresh_prevents_reconnect() -> None:
    initial = Credentials("key", "secret", "token", "identity")
    entered = Event()
    release = Event()

    def provider() -> Credentials:
        entered.set()
        assert release.wait(2)
        return initial

    wrapper = MqttClient(
        endpoint="example.iot.amazonaws.com",
        credentials=initial,
        credentials_provider=provider,
    )
    with (
        patch.object(mqtt.Client, "_create_socket", return_value=MagicMock()) as create_socket,
        patch.object(mqtt.Client, "_send_connect", return_value=mqtt.MQTT_ERR_SUCCESS),
        patch.object(mqtt.Client, "_loop", return_value=mqtt.MQTT_ERR_CONN_LOST),
        patch.object(mqtt.Client, "_reconnect_wait"),
    ):
        wrapper.connect()
        wrapper.loop_start()
        try:
            assert entered.wait(2)
            wrapper.disconnect()
        finally:
            release.set()
            wrapper.loop_stop()
        assert create_socket.call_count == 1


def test_loop_stop_during_credential_refresh_prevents_reconnect() -> None:
    credentials = Credentials("key", "secret", "token", "identity")
    entered = Event()
    release = Event()
    stopped = Event()

    def provider() -> Credentials:
        entered.set()
        assert release.wait(2)
        return credentials

    wrapper = MqttClient(
        endpoint="example.iot.amazonaws.com",
        credentials=credentials,
        credentials_provider=provider,
    )

    def stop() -> None:
        wrapper.loop_stop()
        stopped.set()

    with (
        patch.object(mqtt.Client, "_create_socket", return_value=MagicMock()) as create_socket,
        patch.object(mqtt.Client, "_send_connect", return_value=mqtt.MQTT_ERR_SUCCESS),
        patch.object(mqtt.Client, "_loop", return_value=mqtt.MQTT_ERR_CONN_LOST),
        patch.object(mqtt.Client, "_reconnect_wait"),
    ):
        wrapper.connect()
        wrapper.loop_start()
        stop_thread = Thread(target=stop)
        try:
            assert entered.wait(2)
            stop_thread.start()
            assert wrapper._stopping.wait(2)
        finally:
            release.set()
            stop_thread.join(timeout=2)
        assert stopped.is_set()
        assert create_socket.call_count == 1


@patch("place.mqtt_client.mqtt.Client")
@patch("place.mqtt_client.get_signed_uri")
def test_wait_for_connection_succeeds_on_connack_success(
    mock_get_signed_uri: MagicMock,
    mock_client_cls: MagicMock,
) -> None:
    mock_get_signed_uri.return_value = "wss://example.iot.amazonaws.com/mqtt?x=1"
    client = MagicMock()
    mock_client_cls.return_value = client

    creds = Credentials(
        access_key_id="AKIA...",
        secret_access_key="secret",
        session_token="token",
        identity_id="identity-123",
    )
    mqtt_client = MqttClient(endpoint="example.iot.amazonaws.com", credentials=creds)
    mqtt_client.connect()

    client.on_connect(
        client, None, None, ReasonCode(PacketTypes.CONNACK, identifier=0), None
    )

    mqtt_client.wait_for_connection(timeout=1)

    client.disconnect.assert_not_called()
    client.loop_stop.assert_not_called()


@patch("place.mqtt_client.mqtt.Client")
@patch("place.mqtt_client.get_signed_uri")
def test_wait_for_connection_raises_on_connack_rejection(
    mock_get_signed_uri: MagicMock,
    mock_client_cls: MagicMock,
) -> None:
    mock_get_signed_uri.return_value = "wss://example.iot.amazonaws.com/mqtt?x=1"
    client = MagicMock()
    mock_client_cls.return_value = client

    creds = Credentials(
        access_key_id="AKIA...",
        secret_access_key="secret",
        session_token="token",
        identity_id="identity-123",
    )
    mqtt_client = MqttClient(endpoint="example.iot.amazonaws.com", credentials=creds)
    mqtt_client.connect()

    client.on_connect(
        client, None, None, ReasonCode(PacketTypes.CONNACK, identifier=135), None
    )

    with pytest.raises(PlaceMqttConnectionError, match="rejected"):
        mqtt_client.wait_for_connection(timeout=1)

    client.disconnect.assert_called_once()
    client.loop_stop.assert_called_once()


@patch("place.mqtt_client.mqtt.Client")
@patch("place.mqtt_client.get_signed_uri")
def test_wait_for_connection_raises_on_timeout(
    mock_get_signed_uri: MagicMock,
    mock_client_cls: MagicMock,
) -> None:
    mock_get_signed_uri.return_value = "wss://example.iot.amazonaws.com/mqtt?x=1"
    client = MagicMock()
    mock_client_cls.return_value = client

    creds = Credentials(
        access_key_id="AKIA...",
        secret_access_key="secret",
        session_token="token",
        identity_id="identity-123",
    )
    mqtt_client = MqttClient(endpoint="example.iot.amazonaws.com", credentials=creds)
    mqtt_client.connect()

    with pytest.raises(PlaceMqttConnectionError, match="Timed out"):
        mqtt_client.wait_for_connection(timeout=0.05)

    client.disconnect.assert_called_once()
    client.loop_stop.assert_called_once()


@pytest.fixture
def mqtt_pair() -> tuple[MqttClient, MagicMock]:
    """Set up the wrapper with a mocked Paho client."""
    with patch("place.mqtt_client.mqtt.Client") as client_cls:
        client = client_cls.return_value
        credentials = Credentials(
            access_key_id="key",
            secret_access_key="secret",
            session_token="token",
            identity_id="identity",
        )
        wrapper = MqttClient(
            endpoint="example.iot.amazonaws.com", credentials=credentials
        )
        wrapper.connect()
    return wrapper, client


def test_shadow_get_waits_for_each_successful_suback(
    mqtt_pair: tuple[MqttClient, MagicMock],
) -> None:
    wrapper, client = mqtt_pair
    messages = PlaceMessages(wrapper)
    client.subscribe.side_effect = [(mqtt.MQTT_ERR_SUCCESS, mid) for mid in range(1, 5)]

    for name in ("one", "two", "three", "four"):
        messages.subscribe_shadow_and_get(name)

    client.publish.assert_not_called()
    for mid, name in ((3, "three"), (1, "one"), (4, "four"), (2, "two")):
        client.on_subscribe(
            client, None, mid, [ReasonCode(PacketTypes.SUBACK, identifier=1)], None
        )
        assert client.publish.call_args == call(
            f"$aws/things/{name}/shadow/get", b"", qos=1
        )
    assert client.publish.call_count == 4
    client.on_subscribe(
        client, None, 1, [ReasonCode(PacketTypes.SUBACK, identifier=1)], None
    )
    assert client.publish.call_count == 4


@pytest.mark.parametrize("reason_codes", [[ReasonCode(PacketTypes.SUBACK, identifier=128)], []])
def test_failed_suback_does_not_request_shadow(
    mqtt_pair: tuple[MqttClient, MagicMock],
    caplog: pytest.LogCaptureFixture,
    reason_codes: list[ReasonCode],
) -> None:
    wrapper, client = mqtt_pair
    client.subscribe.return_value = (mqtt.MQTT_ERR_SUCCESS, 1)
    PlaceMessages(wrapper).subscribe_shadow_and_get("one")

    with caplog.at_level(logging.ERROR):
        client.on_subscribe(client, None, 1, reason_codes, None)

    client.publish.assert_not_called()
    assert "$aws/things/one/shadow/#" in caplog.text


def test_shadow_subscription_preserves_name_and_qos(
    mqtt_pair: tuple[MqttClient, MagicMock],
) -> None:
    wrapper, client = mqtt_pair
    client.subscribe.return_value = (mqtt.MQTT_ERR_SUCCESS, 1)
    assert PlaceMessages(wrapper).subscribe_shadow_and_get(" one ", qos=0) == "one"
    client.subscribe.assert_called_once_with("$aws/things/one/shadow/#", qos=0)
    client.on_subscribe(
        client, None, 1, [ReasonCode(PacketTypes.SUBACK, identifier=0)], None
    )
    client.publish.assert_called_once_with("$aws/things/one/shadow/get", b"", qos=0)


def test_subscribe_send_failure_raises(
    mqtt_pair: tuple[MqttClient, MagicMock],
) -> None:
    wrapper, client = mqtt_pair
    client.subscribe.return_value = (mqtt.MQTT_ERR_NO_CONN, None)

    with pytest.raises(PlaceMqttSubscriptionError, match="one"):
        PlaceMessages(wrapper).subscribe_shadow_and_get("one")

    client.publish.assert_not_called()


def test_reconnect_discards_pending_subscriptions(
    mqtt_pair: tuple[MqttClient, MagicMock],
) -> None:
    wrapper, client = mqtt_pair
    messages = PlaceMessages(wrapper)
    client.subscribe.side_effect = [
        (mqtt.MQTT_ERR_SUCCESS, 1),
        (mqtt.MQTT_ERR_SUCCESS, 2),
    ]
    with patch("place.mqtt_client.mqtt.Client", return_value=client):
        wrapper.connect(on_connect=lambda: messages.subscribe_shadow_and_get("one"))
    client.on_connect(
        client, None, None, ReasonCode(PacketTypes.CONNACK, identifier=0), None
    )
    client.on_disconnect(client, None, None, None, None)
    client.on_connect(
        client, None, None, ReasonCode(PacketTypes.CONNACK, identifier=0), None
    )

    client.on_subscribe(
        client, None, 1, [ReasonCode(PacketTypes.SUBACK, identifier=1)], None
    )
    client.publish.assert_not_called()
    client.on_subscribe(
        client, None, 2, [ReasonCode(PacketTypes.SUBACK, identifier=1)], None
    )
    assert client.subscribe.call_count == 2
    client.publish.assert_called_once_with("$aws/things/one/shadow/get", b"", qos=1)


def test_suback_cannot_arrive_before_subscription_is_registered(
    mqtt_pair: tuple[MqttClient, MagicMock],
) -> None:
    wrapper, client = mqtt_pair
    attempted_ack = Event()
    ack_finished = Event()

    def acknowledge() -> None:
        attempted_ack.set()
        client.on_subscribe(
            client, None, 1, [ReasonCode(PacketTypes.SUBACK, identifier=1)], None
        )
        ack_finished.set()

    def subscribe(topic: str, qos: int) -> tuple[int, int]:
        ack_thread.start()
        assert attempted_ack.wait(1)
        assert not ack_finished.is_set()
        return mqtt.MQTT_ERR_SUCCESS, 1

    ack_thread = Thread(target=acknowledge)
    client.subscribe.side_effect = subscribe
    PlaceMessages(wrapper).subscribe_shadow_and_get("one")
    ack_thread.join(timeout=1)

    assert not ack_thread.is_alive()
    client.publish.assert_called_once_with("$aws/things/one/shadow/get", b"", qos=1)
