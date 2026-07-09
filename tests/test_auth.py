from __future__ import annotations

from unittest.mock import MagicMock, patch
from place.auth import get_iot_credentials


@patch("place.auth.srp_auth.boto3")
def test_get_iot_credentials_success(mock_boto3: MagicMock) -> None:
    identity_client = MagicMock()
    mock_boto3.client.return_value = identity_client

    identity_client.get_id.return_value = {"IdentityId": "identity-123"}
    identity_client.get_credentials_for_identity.return_value = {
        "Credentials": {
            "AccessKeyId": "AKIA...",
            "SecretKey": "secret",
            "SessionToken": "session",
        }
    }


    creds = get_iot_credentials(
        id_token="id-token",
        access_token="access-token",
    )

    assert creds.access_key_id == "AKIA..."
    assert creds.secret_access_key == "secret"
    assert creds.session_token == "session"
    assert creds.identity_id == "identity-123"
    assert creds.access_token == "access-token"
