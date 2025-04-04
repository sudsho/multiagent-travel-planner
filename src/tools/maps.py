"""Google Maps Places wrapper for nearby attractions + geocoding."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import httpx

from ..cache import make_cache


_DATA_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "sample_destinations.json"


def geocode(address: str) -> dict[str, float] | None:
    cache = make_cache()
    k = f"geocode:{address.lower()}"
    if (c := cache.get(k)) is not None:
        return c

    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return None
    with httpx.Client(timeout=10.0) as client:
        r = client.get(
            "https://maps.googleapis.com/maps/api/geocode/json",
            params={"address": address, "key": api_key},
        )
        r.raise_for_status()
        results = r.json().get("results", [])
        if not results:
            return None
        loc = results[0]["geometry"]["location"]
        out = {"lat": loc["lat"], "lng": loc["lng"]}
        cache.set(k, out, ttl=86400)
        return out


def nearby_attractions(city: str, interests: list[str], limit: int = 24) -> list[dict[str, Any]]:
    cache = make_cache()
    k = f"attr:{city.lower()}:{','.join(sorted(interests))}:{limit}"
    if (c := cache.get(k)) is not None:
        return c

    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if api_key and (loc := geocode(city)):
        try:
            res = _places_nearby(loc, interests, limit, api_key)
            cache.set(k, res, ttl=86400)
            return res
        except Exception:
            pass

    res = _stub_attractions(city, interests, limit)
    cache.set(k, res, ttl=86400)
    return res


def _places_nearby(loc, interests, limit, api_key) -> list[dict[str, Any]]:
    types = []
    for i in interests:
        i = i.lower()
        if "food" in i or "restaur" in i:
            types.append("restaurant")
        elif "museum" in i or "art" in i:
            types.append("museum")
        elif "park" in i or "nature" in i:
            types.append("park")
        elif "shop" in i:
            types.append("shopping_mall")
        else:
            types.append("tourist_attraction")
    if not types:
        types = ["tourist_attraction"]

    out: list[dict[str, Any]] = []
    with httpx.Client(timeout=10.0) as client:
        for t in set(types):
            r = client.get(
                "https://maps.googleapis.com/maps/api/place/nearbysearch/json",
                params={
                    "location": f"{loc['lat']},{loc['lng']}",
                    "radius": 5000,
                    "type": t,
                    "key": api_key,
                },
            )
            r.raise_for_status()
            for p in r.json().get("results", [])[:8]:
                out.append({
                    "name": p.get("name", "?"),
                    "category": t,
                    "rating": p.get("rating"),
                    "duration_hours": 1.5 if t == "restaurant" else 2.0,
                    "price": _estimate_price(t, p.get("price_level", 1)),
                    "lat": p.get("geometry", {}).get("location", {}).get("lat"),
                    "lng": p.get("geometry", {}).get("location", {}).get("lng"),
                    "notes": ", ".join(p.get("types", [])[:3]),
                })
    return out[:limit]


def _estimate_price(t: str, level: int) -> float:
    if t == "restaurant":
        return 12.0 * max(1, level)
    if t == "museum":
        return 14.0
    if t == "shopping_mall":
        return 0.0
    return 5.0 * max(1, level)


def _stub_attractions(city: str, interests: list[str], limit: int) -> list[dict[str, Any]]:
    if _DATA_FILE.exists():
        all_data = json.loads(_DATA_FILE.read_text(encoding="utf-8"))
        rows = all_data.get(city.lower(), all_data.get("default", []))
        return rows[:limit]
    return [
        {"name": f"{city.title()} Old Town Walk", "category": "walking", "rating": 4.5,
         "duration_hours": 2.5, "price": 0.0, "notes": "free, scenic"},
        {"name": f"{city.title()} National Museum", "category": "museum", "rating": 4.4,
         "duration_hours": 2.0, "price": 14.0, "notes": "rainy-day option"},
    ][:limit]
