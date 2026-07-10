from __future__ import annotations

import json
from typing import Any

from .mqtt_client import MqttClient


HOUSEHOLD_PREFIX = "connectedsmoke/household"
SHADOW_GET_PREFIX = "$aws/things"


def parse_payload(raw: bytes) -> dict[str, Any]:
    if not raw or not raw.strip():
        return {}
    try:
        return json.loads(raw.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}


def message_kind(topic: str, payload: dict[str, Any]) -> str:
    checks = [
        (lambda: "state" in payload and payload.get("state", {}).get("reported") is not None, "shadow"),
        (lambda: "connectivity" in topic.lower(), "presence"),
        (lambda: "command/response" in topic, "command"),
        (lambda: "events/" in topic, "event"),
        (lambda: topic.startswith("connectedsmoke/household/"), "household"),
    ]
    return next((label for pred, label in checks if pred()), "msg")


def household_subscription_topic(household_id: str) -> str:
    return f"{HOUSEHOLD_PREFIX}/{household_id}/#"


def shadow_get_topic(thing_name: str) -> str:
    return f"{SHADOW_GET_PREFIX}/{thing_name}/shadow/get"


def shadow_subscription_topic(thing_name: str) -> str:
    return f"{SHADOW_GET_PREFIX}/{thing_name}/shadow/#"


def describe_message(topic: str, raw: bytes) -> str:
    payload = parse_payload(raw)
    kind = message_kind(topic, payload)
    extra = (
        f" -> reported: {list(payload.get('state', {}).get('reported', {}).keys())}"
        if kind == "shadow"
        else f" {payload}"
        if kind == "msg"
        else ""
    )
    return f"[{kind}] {topic}{extra}"


class PlaceMessages:
    def __init__(self, client: MqttClient):
        self._client = client

    def subscribe_household(self, household_id: str, qos: int = 1) -> str:
        hid = household_id.strip()
        assert hid
        topic = household_subscription_topic(hid)
        self._client.subscribe(topic, qos=qos)
        return hid

    def subscribe_shadow(self, thing_name: str, qos: int = 1) -> str:
        name = thing_name.strip()
        assert name
        topic = shadow_subscription_topic(name)
        self._client.subscribe(topic, qos=qos)
        return name

    def publish_shadow_get(self, thing_name: str, qos: int = 1) -> str:
        name = thing_name.strip()
        assert name
        topic = shadow_get_topic(name)
        self._client.publish(topic, qos=qos)
        return name

    def describe(self, topic: str, raw: bytes) -> str:
        return describe_message(topic, raw)


    @staticmethod
    def _thing_name_from_topic(topic: str) -> str | None:
        """Extract thing_name from an AWS IoT shadow topic ($aws/things/{name}/shadow/...)."""
        parts = topic.split("/")
        if len(parts) >= 3 and parts[0] == "$aws" and parts[1] == "things":
            return parts[2]
        return None
