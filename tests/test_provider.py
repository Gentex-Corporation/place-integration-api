from __future__ import annotations

import asyncio

from place_integration_api.auth.abstract_auth import AbstractAuth
from place_integration_api.config import FULFILLMENT_URL
from place_integration_api.provider import Provider


def test_provider_discover_parses_response() -> None:
    payload = {
        "success": True,
        "data": {
            "devices": [
                {"householdId": "h1", "thingName": "t1", "deviceId": "d1"},
                {"householdId": "h2", "thingName": "t2", "deviceId": "d2"},
            ]
        },
    }

    class DummyAuth(AbstractAuth):
        def __init__(self) -> None:
            self.calls: list[tuple[str, str, dict]] = []

        async def async_get_access_token(self) -> str:
            return "token"

        async def request(self, method, url, **kwargs):
            self.calls.append((method, url, kwargs))

            class DummyResponse:
                async def json(self_inner):
                    return payload

            return DummyResponse()

    auth = DummyAuth()
    provider = Provider(auth)
    devices = asyncio.run(provider.discover())

    assert auth.calls == [("POST", FULFILLMENT_URL, {"json": {"command": "DISCOVER", "data": {}}})]

    household_ids = sorted(
        {d.household_id for d in devices if d.household_id is not None}
    )
    thing_names = sorted(
        {d.thing_name for d in devices if d.thing_name is not None}
    )

    assert household_ids == ["h1", "h2"]
    assert thing_names == ["t1", "t2"]
    assert [d.device_id for d in devices] == ["d1", "d2"]


def test_provider_enable_sends_enable_command() -> None:
    payload = {"success": True, "data": {"status": "enabled"}}

    class DummyAuth(AbstractAuth):
        def __init__(self) -> None:
            self.calls: list[tuple[str, str, dict]] = []

        async def async_get_access_token(self) -> str:
            return "token"

        async def request(self, method, url, **kwargs):
            self.calls.append((method, url, kwargs))

            class DummyResponse:
                async def json(self_inner):
                    return payload

            return DummyResponse()

    auth = DummyAuth()
    provider = Provider(auth)
    result = asyncio.run(provider.enable())

    assert auth.calls == [("POST", FULFILLMENT_URL, {"json": {"command": "ENABLE", "data": {}}})]
    assert result == payload


def test_provider_disable_sends_disable_command() -> None:
    payload = {"success": True, "data": {"status": "disabled"}}

    class DummyAuth(AbstractAuth):
        def __init__(self) -> None:
            self.calls: list[tuple[str, str, dict]] = []

        async def async_get_access_token(self) -> str:
            return "token"

        async def request(self, method, url, **kwargs):
            self.calls.append((method, url, **kwargs))

            class DummyResponse:
                async def json(self_inner):
                    return payload

            return DummyResponse()

    auth = DummyAuth()
    provider = Provider(auth)
    result = asyncio.run(provider.disable())

    assert auth.calls == [("POST", FULFILLMENT_URL, {"json": {"command": "DISABLE", "data": {}}})]
    assert result == payload

