from __future__ import annotations

from typing import Any

from aiohttp import ContentTypeError

from .auth.abstract_auth import AbstractAuth
from .errors import PlaceFulfillmentError
from .models.discover_device import DiscoverDevice
from .config import FULFILLMENT_URL


async def _send_command(authorized_session: AbstractAuth, command: str) -> dict[str, Any]:
    """Send a fulfillment command and return the parsed response body."""
    body = {"command": command, "data": {}}
    resp = await authorized_session.request("POST", FULFILLMENT_URL, json=body)
    try:
        data = await resp.json()
    except (ContentTypeError, ValueError) as err:
        raise PlaceFulfillmentError(
            f"Invalid response from fulfillment API: {err}"
        ) from err
    if not isinstance(data, dict):
        raise PlaceFulfillmentError(f"Invalid response from fulfillment API: {data!r}")
    if not data.get("success", True):
        raise PlaceFulfillmentError(f"Home Assistant error: {data.get('message', data)}")
    return data


class Provider:
    def __init__(self, authorized_session: AbstractAuth) -> None:
        self.authorized_session = authorized_session

    async def discover(self) -> list[DiscoverDevice]:
        data = await _send_command(self.authorized_session, "DISCOVER")
        devices_raw = (data.get("data") or {}).get("devices") or []
        return [DiscoverDevice.from_dict(raw) for raw in devices_raw]

    async def enable(self):
        return await _send_command(self.authorized_session, "ENABLE")

    async def disable(self):
        return await _send_command(self.authorized_session, "DISABLE")
