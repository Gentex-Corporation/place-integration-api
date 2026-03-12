from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Credentials:
    access_key_id: str
    secret_access_key: str
    session_token: str
    identity_id: str
    access_token: str | None = None

