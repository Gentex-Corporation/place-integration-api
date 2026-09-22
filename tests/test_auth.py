from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp import ClientResponseError

from place.auth import get_iot_credentials
from place.auth.abstract_auth import AbstractAuth


class _FakeAuth(AbstractAuth):
    async def async_get_access_token(self) -> str:
        return "token"


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


def test_request_raises_for_non_2xx_status() -> None:
    response = MagicMock()
    response.raise_for_status.side_effect = ClientResponseError(
        request_info=MagicMock(), history=(), status=401
    )
    websession = MagicMock()
    websession.request = AsyncMock(return_value=response)

    auth = _FakeAuth(websession)

    with pytest.raises(ClientResponseError):
        asyncio.run(auth.request("POST", "https://example.com"))


def test_request_returns_response_for_2xx_status() -> None:
    response = MagicMock()
    response.raise_for_status.return_value = None
    websession = MagicMock()
    websession.request = AsyncMock(return_value=response)

    auth = _FakeAuth(websession)

    result = asyncio.run(auth.request("POST", "https://example.com"))

    assert result is response
    response.raise_for_status.assert_called_once()
