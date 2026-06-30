"""Public data models for the Place device shadow."""

from dataclasses import dataclass
from typing import Any

from enum import IntEnum


class AlarmStatus(IntEnum):
    """Alarm status values."""

    IDLE = 0
    TEST = 1
    PRE_ALARM = 2
    ALARM = 3
    CRITICAL_ALARM = 4
    HUSHED = 5
    NOT_PRESENT = 6


def _parse_alarm(value: Any) -> AlarmStatus:
    """Convert a raw shadow value to an AlarmStatus."""
    if value is None:
        return AlarmStatus.NOT_PRESENT
    try:
        return AlarmStatus(int(value))
    except (ValueError, TypeError):
        return AlarmStatus.NOT_PRESENT


@dataclass
class PlaceDeviceShadow:
    """Subset of the Place device shadow consumed by the integration."""

    co_alarm_status: AlarmStatus = AlarmStatus.NOT_PRESENT
    heat_alarm_status: AlarmStatus = AlarmStatus.NOT_PRESENT
    smoke_alarm_status: AlarmStatus = AlarmStatus.NOT_PRESENT

    @staticmethod
    def from_shadow(shadow: dict[str, Any]) -> "PlaceDeviceShadow":
        """Parse a full shadow from a raw dict."""
        reported = shadow.get("state", shadow).get("reported", shadow)
        return PlaceDeviceShadow(
            co_alarm_status=_parse_alarm(reported.get("coAlarmStatus")),
            heat_alarm_status=_parse_alarm(reported.get("heatAlarmStatus")),
            smoke_alarm_status=_parse_alarm(reported.get("smokeAlarmStatus")),
        )

    def merge(self, partial: dict[str, Any]) -> None:
        """Merge a sparse shadow update into the current state."""
        reported = partial.get("state", partial).get("reported", partial)
        if "coAlarmStatus" in reported:
            self.co_alarm_status = _parse_alarm(reported["coAlarmStatus"])
        if "heatAlarmStatus" in reported:
            self.heat_alarm_status = _parse_alarm(reported["heatAlarmStatus"])
        if "smokeAlarmStatus" in reported:
            self.smoke_alarm_status = _parse_alarm(reported["smokeAlarmStatus"])
