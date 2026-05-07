from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


def _as_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _as_bool(value: Any) -> bool | None:
    if value is None:
        return None
    return bool(value)


@dataclass
class DiscoverDevice:
    location: str | None
    shadow: dict[str, Any]
    device_name: str | None
    thing_name: str | None
    firmware_version: str | None
    model_number: str | None
    device_id: str | None
    online: bool | None

    @staticmethod
    def from_dict(data: Mapping[str, Any]) -> DiscoverDevice:
        return DiscoverDevice(
            location=_as_str(data.get("location")),
            shadow=dict(data.get("shadow") or {}),
            device_name=_as_str(data.get("deviceName")),
            thing_name=_as_str(data.get("thingName")),
            firmware_version=_as_str(data.get("firmwareVersion")),
            model_number=_as_str(data.get("modelNumber")),
            device_id=_as_str(data.get("deviceId")),
            online=_as_bool(data.get("online")),
        )
