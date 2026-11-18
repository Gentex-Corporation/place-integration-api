from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp import ClientResponseError
import boto3
from botocore import UNSIGNED
from botocore.config import Config
from botocore.exceptions import EndpointConnectionError, ReadTimeoutError

from place.auth import get_iot_credentials, login
from place.auth.abstract_auth import AbstractAuth
from place.errors import (
    PlaceCredentialExchangeAuthError,
    PlaceCredentialExchangeConnectionError,
    PlaceCredentialExchangeError,
    PlaceInvalidCredentialsError,
    PlaceLoginConnectionError,
    PlaceLoginError,
)


@pytest.mark.parametrize("operation", ["initiate_auth", "respond_to_auth_challenge"])
@pytest.mark.parametrize(
    ("code", "expected"),
    [
        ("NotAuthorizedException", PlaceInvalidCredentialsError),
        ("UserNotFoundException", PlaceInvalidCredentialsError),
        ("UserNotConfirmedException", PlaceInvalidCredentialsError),
        ("PasswordResetRequiredException", PlaceInvalidCredentialsError),
        ("TooManyRequestsException", PlaceLoginConnectionError),
        ("InternalErrorException", PlaceLoginConnectionError),
        ("InvalidParameterException", PlaceLoginError),
    ],
)
def test_login_translates_service_errors(
    operation: str, code: str, expected: type[Exception]
) -> None:
    client = boto3.client(
        "cognito-idp",
        region_name="us-east-1",
        config=Config(signature_version=UNSIGNED),
    )
    error = client.exceptions.from_code(code)(
        {"Error": {"Code": code, "Message": "failure"}}, operation
    )
    with (
        patch("place.auth.aws_srp.boto3.client", return_value=client),
        patch.object(
            client,
            "initiate_auth",
            return_value={
                "ChallengeName": "PASSWORD_VERIFIER",
                "ChallengeParameters": {},
            },
        ),
        patch.object(client, "respond_to_auth_challenge"),
        patch("place.auth.aws_srp.AWSSRP.process_challenge", return_value={}),
        patch.object(client, operation, side_effect=error),
    ):
        with pytest.raises(expected) as exc_info:
            login("user", "password")
    assert exc_info.value.__cause__ is error


@pytest.mark.parametrize("operation", ["initiate_auth", "respond_to_auth_challenge"])
@pytest.mark.parametrize(
    "error",
    [
        EndpointConnectionError(endpoint_url="https://example.com"),
        ReadTimeoutError(endpoint_url="https://example.com", error="timeout"),
    ],
)
def test_login_translates_connection_errors(operation: str, error: Exception) -> None:
    client = boto3.client(
        "cognito-idp",
        region_name="us-east-1",
        config=Config(signature_version=UNSIGNED),
    )
    with (
        patch("place.auth.aws_srp.boto3.client", return_value=client),
        patch.object(
            client,
            "initiate_auth",
            return_value={
                "ChallengeName": "PASSWORD_VERIFIER",
                "ChallengeParameters": {},
            },
        ),
        patch.object(client, "respond_to_auth_challenge"),
        patch("place.auth.aws_srp.AWSSRP.process_challenge", return_value={}),
        patch.object(client, operation, side_effect=error),
    ):
        with pytest.raises(PlaceLoginConnectionError) as exc_info:
            login("user", "password")
    assert exc_info.value.__cause__ is error


def test_login_unexpected_error_propagates() -> None:
    error = ValueError("unexpected")
    client = boto3.client(
        "cognito-idp",
        region_name="us-east-1",
        config=Config(signature_version=UNSIGNED),
    )
    with (
        patch("place.auth.aws_srp.boto3.client", return_value=client),
        patch.object(client, "initiate_auth", side_effect=error),
    ):
        with pytest.raises(ValueError) as exc_info:
            login("user", "password")
    assert exc_info.value is error


def test_login_password_change_required() -> None:
    client = boto3.client(
        "cognito-idp",
        region_name="us-east-1",
        config=Config(signature_version=UNSIGNED),
    )
    with (
        patch("place.auth.aws_srp.boto3.client", return_value=client),
        patch.object(
            client,
            "initiate_auth",
            return_value={
                "ChallengeName": "PASSWORD_VERIFIER",
                "ChallengeParameters": {},
            },
        ),
        patch.object(
            client,
            "respond_to_auth_challenge",
            return_value={"ChallengeName": "NEW_PASSWORD_REQUIRED"},
        ),
        patch("place.auth.aws_srp.AWSSRP.process_challenge", return_value={}),
    ):
        with pytest.raises(PlaceInvalidCredentialsError):
            login("user", "password")


def test_login_success() -> None:
    client = boto3.client(
        "cognito-idp",
        region_name="us-east-1",
        config=Config(signature_version=UNSIGNED),
    )
    tokens = {"AuthenticationResult": {"AccessToken": "token"}}
    with (
        patch("place.auth.aws_srp.boto3.client", return_value=client),
        patch.object(
            client,
            "initiate_auth",
            return_value={
                "ChallengeName": "PASSWORD_VERIFIER",
                "ChallengeParameters": {},
            },
        ),
        patch.object(client, "respond_to_auth_challenge", return_value=tokens),
        patch("place.auth.aws_srp.AWSSRP.process_challenge", return_value={}),
    ):
        assert login("user", "password") is tokens


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


@pytest.mark.parametrize("operation", ["get_id", "get_credentials_for_identity"])
@pytest.mark.parametrize(
    ("code", "expected"),
    [
        ("NotAuthorizedException", PlaceCredentialExchangeAuthError),
        ("TooManyRequestsException", PlaceCredentialExchangeConnectionError),
        ("InternalErrorException", PlaceCredentialExchangeConnectionError),
        ("ExternalServiceException", PlaceCredentialExchangeConnectionError),
        ("InvalidParameterException", PlaceCredentialExchangeError),
    ],
)
def test_get_iot_credentials_service_errors(
    operation: str, code: str, expected: type[Exception]
) -> None:
    client = boto3.client(
        "cognito-identity",
        region_name="us-east-1",
        config=Config(signature_version=UNSIGNED),
    )
    error = client.exceptions.from_code(code)(
        {"Error": {"Code": code, "Message": "failure"}}, operation
    )
    with (
        patch("place.auth.srp_auth.boto3.client", return_value=client),
        patch.object(client, "get_id", return_value={"IdentityId": "identity-123"}),
        patch.object(client, operation, side_effect=error),
        pytest.raises(expected) as exc_info,
    ):
        get_iot_credentials("id-token", "access-token")
    assert exc_info.value.__cause__ is error


@pytest.mark.parametrize("operation", ["get_id", "get_credentials_for_identity"])
@pytest.mark.parametrize(
    "error",
    [
        EndpointConnectionError(endpoint_url="https://example.com"),
        ReadTimeoutError(endpoint_url="https://example.com", error="timeout"),
    ],
)
def test_get_iot_credentials_connection_errors(operation: str, error: Exception) -> None:
    client = boto3.client(
        "cognito-identity",
        region_name="us-east-1",
        config=Config(signature_version=UNSIGNED),
    )
    with (
        patch("place.auth.srp_auth.boto3.client", return_value=client),
        patch.object(client, "get_id", return_value={"IdentityId": "identity-123"}),
        patch.object(client, operation, side_effect=error),
        pytest.raises(PlaceCredentialExchangeConnectionError) as exc_info,
    ):
        get_iot_credentials("id-token", "access-token")
    assert exc_info.value.__cause__ is error


def test_get_iot_credentials_unexpected_error_propagates() -> None:
    client = boto3.client(
        "cognito-identity",
        region_name="us-east-1",
        config=Config(signature_version=UNSIGNED),
    )
    error = ValueError("unexpected")
    with (
        patch("place.auth.srp_auth.boto3.client", return_value=client),
        patch.object(client, "get_id", side_effect=error),
        pytest.raises(ValueError) as exc_info,
    ):
        get_iot_credentials("id-token", "access-token")
    assert exc_info.value is error


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
