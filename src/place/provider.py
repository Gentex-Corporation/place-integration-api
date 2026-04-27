from __future__ import annotations

from .auth.abstract_auth import AbstractAuth
from .models.discover_device import DiscoverDevice
from .config import FULFILLMENT_URL

class Provider:
    def __init__(self, authorized_session: AbstractAuth) -> None:
        self.authorized_session = authorized_session


    async def discover(self) -> list[DiscoverDevice]:
        body = {"command": "DISCOVER", "data": {}}
        resp = await self.authorized_session.request("POST", FULFILLMENT_URL, json=body)
        data = await resp.json()
        if not data.get("success", True):
            raise RuntimeError(f"Home Assistant error: {data.get('message', data)}")
        devices_raw = (data.get("data") or {}).get("devices") or []
        devices: list[DiscoverDevice] = []
        for raw in devices_raw:
            devices.append(DiscoverDevice.from_dict(raw))
        return devices

    async def enable(self):
        body = {"command": "ENABLE", "data": {}}
        resp = await self.authorized_session.request("POST", FULFILLMENT_URL, json=body)
        data = await resp.json()
        if not data.get("success", True):
            raise RuntimeError(f"Home Assistant error: {data.get('message', data)}")
        return data
    
    async def disable(self):
        body = {"command": "DISABLE", "data": {}}
        resp = await self.authorized_session.request("POST", FULFILLMENT_URL, json=body)
        data = await resp.json()
        if not data.get("success", True):
            raise RuntimeError(f"Home Assistant error: {data.get('message', data)}")
        return data
