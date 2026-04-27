from __future__ import annotations

from typing import Any, Dict

import boto3
from botocore import UNSIGNED
from botocore.config import Config


from .aws_srp import AWSSRP
from ..config import REGION, COGNITO_CLIENT_ID, COGNITO_USER_POOL_ID, COGNITO_IDENTITY_POOL_ID
from ..models import Credentials


def login(username: str, password: str) -> Dict[str, Any]:
    return get_tokens_via_srp(
        user_pool_id=COGNITO_USER_POOL_ID,
        client_id=COGNITO_CLIENT_ID,
        username=username,
        password=password,
    )

def get_iot_credentials(id_token: str, access_token: str) -> Credentials:
    """Exchange a Cognito ID token for AWS IoT credentials."""
    identity = boto3.client(
        "cognito-identity",
        region_name=REGION,
        config=Config(signature_version=UNSIGNED),
    )
    provider_key = f"cognito-idp.{REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}"
    logins = {provider_key: id_token}

    identity_id = identity.get_id(
        IdentityPoolId=COGNITO_IDENTITY_POOL_ID, Logins=logins
    )["IdentityId"]

    creds = identity.get_credentials_for_identity(
        IdentityId=identity_id, Logins=logins
    )["Credentials"]

    return Credentials(
        access_key_id=creds["AccessKeyId"],
        secret_access_key=creds["SecretKey"],
        session_token=creds["SessionToken"],
        identity_id=identity_id,
        access_token=access_token,
    )


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


