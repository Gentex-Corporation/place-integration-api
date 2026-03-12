from __future__ import annotations

from typing import Any, Dict

import boto3

from .aws_srp import AWSSRP
from ..config import REGION
from ..models import Credentials


def get_tokens_via_srp(
    *,
    user_pool_id: str,
    client_id: str,
    username: str,
    password: str,
    region: str = REGION,
    client_secret: str | None = None,
) -> Dict[str, Any]:
    aws = AWSSRP(
        username=username,
        password=password,
        pool_id=user_pool_id,
        client_id=client_id,
        pool_region=region,
        client_secret=client_secret,
    )
    return aws.authenticate_user()


def get_credentials_via_cognito(
    *,
    user_pool_id: str,
    client_id: str,
    identity_pool_id: str,
    username: str,
    password: str,
    region: str = REGION,
) -> Credentials:
    identity = boto3.client("cognito-identity", region_name=region)

    resp = get_tokens_via_srp(
        user_pool_id=user_pool_id,
        client_id=client_id,
        username=username,
        password=password,
        region=region,
    )
    auth_result = resp.get("AuthenticationResult")
    if not auth_result:
        raise RuntimeError("No AuthenticationResult from Cognito")
    id_token = auth_result["IdToken"]
    access_token = auth_result["AccessToken"]
    provider_key = f"cognito-idp.{region}.amazonaws.com/{user_pool_id}"
    logins = {provider_key: id_token}

    identity_id = identity.get_id(IdentityPoolId=identity_pool_id, Logins=logins)[
        "IdentityId"
    ]
    creds = identity.get_credentials_for_identity(
        IdentityId=identity_id,
        Logins=logins,
    )["Credentials"]
    return Credentials(
        access_key_id=creds["AccessKeyId"],
        secret_access_key=creds["SecretKey"],
        session_token=creds["SessionToken"],
        identity_id=identity_id,
        access_token=access_token,
    )
