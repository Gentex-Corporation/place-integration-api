from __future__ import annotations

from unittest.mock import MagicMock, patch

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

    mock_get_signed_uri.assert_called_once()
    client.ws_set_options.assert_called()
    client.tls_set.assert_called_once()
    client.connect.assert_called_once()
