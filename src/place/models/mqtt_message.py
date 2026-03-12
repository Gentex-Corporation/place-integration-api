from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class MqttMessage:
    topic: str
    payload: dict[str, Any]

