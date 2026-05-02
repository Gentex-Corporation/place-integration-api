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
    updated_by: str | None
    activated_at: str | None
    updated_at: str | None
    location: str | None
    entity_type: str | None
    status: str | None
    created_by: str | None
    household_id: str | None
    shadow: dict[str, Any]
    device_name: str | None
    thing_name: str | None
    firmware_version: str | None
    created_at: str | None
    model_number: str | None
    device_id: str | None
    online: bool | None
    warranty_registration: bool | None

    @staticmethod
    def from_dict(data: Mapping[str, Any]) -> DiscoverDevice:
        return DiscoverDevice(
            updated_by=_as_str(data.get("updatedBy")),
            activated_at=_as_str(data.get("activatedAt")),
            updated_at=_as_str(data.get("updatedAt")),
            location=_as_str(data.get("location") or []),
            entity_type=_as_str(data.get("entityType")),
            status=_as_str(data.get("status")),
            created_by=_as_str(data.get("createdBy")),
            household_id=_as_str(data.get("householdId")),
            shadow=dict(data.get("shadow") or {}),
            device_name=_as_str(data.get("deviceName")),
            thing_name=_as_str(data.get("thingName")),
            firmware_version=_as_str(data.get("firmwareVersion")),
            created_at=_as_str(data.get("createdAt")),
            model_number=_as_str(data.get("modelNumber")),
            device_id=_as_str(data.get("deviceId")),
            online=_as_bool(data.get("online")),
            warranty_registration=_as_bool(data.get("warrantyRegistration")),
        )
