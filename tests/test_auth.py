from __future__ import annotations

from unittest.mock import MagicMock, patch

from place_integration_api.auth import get_credentials_via_cognito


@patch("place_integration_api.auth.srp_auth.boto3")
@patch("place_integration_api.auth.srp_auth.get_tokens_via_srp")
def test_get_credentials_via_cognito_success(
    mock_get_tokens_via_srp: MagicMock, mock_boto3: MagicMock
) -> None:
    identity_client = MagicMock()
    mock_boto3.client.return_value = identity_client

    mock_get_tokens_via_srp.return_value = {
        "AuthenticationResult": {
            "IdToken": "id-token",
            "AccessToken": "access-token",
        }
    }
    identity_client.get_id.return_value = {"IdentityId": "identity-123"}
    identity_client.get_credentials_for_identity.return_value = {
        "Credentials": {
            "AccessKeyId": "AKIA...",
            "SecretKey": "secret",
            "SessionToken": "session",
        }
    }

    creds = get_credentials_via_cognito(
        user_pool_id="pool",
        client_id="client",
        identity_pool_id="identity-pool",
        username="user",
        password="pass",
        region="us-east-2",
    )

    assert creds.access_key_id == "AKIA..."
    assert creds.secret_access_key == "secret"
    assert creds.session_token == "session"
    assert creds.identity_id == "identity-123"
    assert creds.access_token == "access-token"

