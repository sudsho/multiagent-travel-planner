"""shared auth helpers (Amadeus OAuth)."""
from __future__ import annotations

import time
from typing import Optional

import httpx

_TOKEN: Optional[dict] = None


def amadeus_token(cid: str, sec: str) -> str:
    global _TOKEN
    now = time.time()
    if _TOKEN and _TOKEN.get("exp", 0) > now + 30:
        return _TOKEN["t"]
    r = httpx.post(
        "https://test.api.amadeus.com/v1/security/oauth2/token",
        data={"grant_type": "client_credentials", "client_id": cid, "client_secret": sec},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=10.0,
    )
    r.raise_for_status()
    j = r.json()
    _TOKEN = {"t": j["access_token"], "exp": now + int(j.get("expires_in", 1700))}
    return _TOKEN["t"]
