"""OpenWeather One Call / Daily Forecast wrapper with caching."""
from __future__ import annotations

import os
from typing import Any

import httpx

from ..cache import make_cache

_API = "https://api.openweathermap.org/data/2.5"


def _cache_key(city: str, on_date: str) -> str:
    return f"weather:{city.lower()}:{on_date}"


def get_forecast(city: str, on_date: str, *, _client: httpx.Client | None = None) -> dict[str, Any]:
    """returns a small dict with temp_c_min, temp_c_max, precipitation_mm, summary."""
    cache = make_cache()
    key = _cache_key(city, on_date)
    cached = cache.get(key)
    if cached:
        return cached

    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        # offline fallback: deterministic stub
        return _stub(city, on_date, cache, key)

    client = _client or httpx.Client(timeout=10.0)
    try:
        # geocode first
        g = client.get(
            "https://api.openweathermap.org/geo/1.0/direct",
            params={"q": city, "limit": 1, "appid": api_key},
        )
        g.raise_for_status()
        loc = g.json()
        if not loc:
            return _stub(city, on_date, cache, key)
        lat, lon = loc[0]["lat"], loc[0]["lon"]

        r = client.get(
            f"{_API}/forecast",
            params={"lat": lat, "lon": lon, "appid": api_key, "units": "metric"},
        )
        r.raise_for_status()
        data = r.json()
        bucket = [b for b in data.get("list", []) if b.get("dt_txt", "").startswith(on_date)]
        if not bucket:
            return _stub(city, on_date, cache, key)
        temps = [b["main"]["temp"] for b in bucket]
        rain = sum(b.get("rain", {}).get("3h", 0.0) for b in bucket)
        summary = bucket[len(bucket) // 2]["weather"][0]["description"]
        out = {
            "temp_c_min": round(min(temps), 1),
            "temp_c_max": round(max(temps), 1),
            "precipitation_mm": round(rain, 1),
            "summary": summary,
        }
        cache.set(key, out, ttl=3600)
        return out
    finally:
        if _client is None:
            client.close()


def _stub(city: str, on_date: str, cache, key) -> dict[str, Any]:
    seed = abs(hash((city.lower(), on_date))) % 100
    out = {
        "temp_c_min": 12 + (seed % 12),
        "temp_c_max": 18 + (seed % 14),
        "precipitation_mm": (seed % 7) * 0.6,
        "summary": "partly cloudy" if seed % 3 else "clear sky",
    }
    cache.set(key, out, ttl=3600)
    return out
