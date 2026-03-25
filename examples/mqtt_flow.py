#!/usr/bin/env python3
"""
Example CLI that wires environment variables to the MQTT flow APIs.

It authenticates via Cognito, optionally calls Home Assistant DISCOVER,
then connects to AWS IoT Core over MQTT and prints incoming messages.
"""

from __future__ import annotations

import asyncio
import os
import sys

from aiohttp import ClientSession

from place.auth import get_credentials_via_cognito
from place.auth.abstract_auth import AbstractAuth
from place.config import REGION
from place.messages import PlaceMessages
from place.mqtt_client import MqttClient
from place.provider import Provider


class HomeAssistantAuth(AbstractAuth):
    def __init__(self, websession: ClientSession, access_token: str) -> None:
        super().__init__(websession)
        self._access_token = access_token

    async def async_get_access_token(self) -> str:
        return self._access_token


async def main() -> None:
    env = os.environ

    endpoint = env.get("IOT_ENDPOINT", "").strip()
    assert endpoint, "Set IOT_ENDPOINT"

    region = env.get("AWS_REGION", REGION)

    assert env.get("COGNITO_USER_POOL_ID"), "Set COGNITO_USER_POOL_ID"
    assert env.get("COGNITO_CLIENT_ID"), "Set COGNITO_CLIENT_ID"
    assert env.get("COGNITO_IDENTITY_POOL_ID"), "Set COGNITO_IDENTITY_POOL_ID"
    assert env.get("COGNITO_USERNAME"), "Set COGNITO_USERNAME"
    assert env.get("COGNITO_PASSWORD"), "Set COGNITO_PASSWORD"

    credentials = get_credentials_via_cognito(
        user_pool_id=env["COGNITO_USER_POOL_ID"],
        client_id=env["COGNITO_CLIENT_ID"],
        identity_pool_id=env["COGNITO_IDENTITY_POOL_ID"],
        username=env["COGNITO_USERNAME"],
        password=env["COGNITO_PASSWORD"],
        region=region,
        # mfa_code=env.get("COGNITO_MFA_CODE") or None,
    )

    assert credentials.access_token, "Cognito credentials missing access token"

    async with ClientSession() as session:
        auth = HomeAssistantAuth(session, credentials.access_token)
        provider = Provider(auth)
        devices = await provider.discover()
    household_ids = sorted(
        {d.household_id for d in devices if d.household_id is not None}
    )
    thing_names = sorted(
        {d.thing_name for d in devices if d.thing_name is not None}
    )
    print(
        f"Home Assistant DISCOVER: {len(household_ids)} households, {len(thing_names)} devices"
    )

    client = MqttClient(endpoint=endpoint, credentials=credentials)
    messages = PlaceMessages(client)

    def on_message(topic: str, raw: bytes) -> None:
        print(messages.describe(topic, raw))

    client.connect(on_message=on_message)

    for hid in household_ids:
        subscribed = messages.subscribe_household(hid, qos=1)
        print(f"Subscribed household: {subscribed}")

    for thing in thing_names or []:
        published = messages.publish_shadow_get(thing, qos=1)
        print(f"Published shadow get: {published}")

    client.loop_forever()


if __name__ == "__main__":
    asyncio.run(main())
