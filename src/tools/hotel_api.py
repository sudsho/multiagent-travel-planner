"""hotel API wrapper. uses Amadeus Hotel Search if configured, else a stub list."""
from __future__ import annotations

import os
from typing import Any

import httpx

from ..cache import make_cache
from .auth import amadeus_token


def _key(city: str, ci: str, co: str, guests: int) -> str:
    return f"hotel:{city.lower()}:{ci}:{co}:{guests}"


def search_hotels(
    city: str,
    check_in: str,
    check_out: str,
    guests: int = 1,
    price_target: float | None = None,
) -> list[dict[str, Any]]:
    cache = make_cache()
    key = _key(city, check_in, check_out, guests)
    if (c := cache.get(key)) is not None:
        return _filter_by_price(c, price_target)

    # try Amadeus
    cid = os.getenv("AMADEUS_CLIENT_ID")
    sec = os.getenv("AMADEUS_CLIENT_SECRET")
    if cid and sec:
        try:
            results = _amadeus_hotels(city, check_in, check_out, guests, cid, sec)
            cache.set(key, results, ttl=1800)
            return _filter_by_price(results, price_target)
        except Exception:
            pass  # fall through to stub

    out = _stub_hotels(city, check_in, check_out, guests)
    cache.set(key, out, ttl=1800)
    return _filter_by_price(out, price_target)


def _filter_by_price(items: list[dict[str, Any]], price_target: float | None) -> list[dict[str, Any]]:
    if not price_target:
        return sorted(items, key=lambda h: -h.get("rating", 0))
    return sorted(
        items,
        key=lambda h: (abs(h["price_per_night"] - price_target), -h.get("rating", 0)),
    )


def _amadeus_hotels(city, ci, co, guests, cid, sec) -> list[dict[str, Any]]:
    token = amadeus_token(cid, sec)
    with httpx.Client(timeout=12.0) as client:
        r = client.get(
            "https://test.api.amadeus.com/v1/reference-data/locations/hotels/by-city",
            headers={"Authorization": f"Bearer {token}"},
            params={"cityCode": city[:3].upper()},
        )
        r.raise_for_status()
        ids = [h["hotelId"] for h in r.json().get("data", [])][:8]
        if not ids:
            return []
        offers = client.get(
            "https://test.api.amadeus.com/v3/shopping/hotel-offers",
            headers={"Authorization": f"Bearer {token}"},
            params={
                "hotelIds": ",".join(ids),
                "checkInDate": ci,
                "checkOutDate": co,
                "adults": guests,
            },
        )
        offers.raise_for_status()
        out = []
        for item in offers.json().get("data", []):
            h = item.get("hotel", {})
            offer = (item.get("offers") or [{}])[0]
            price = float(offer.get("price", {}).get("total", 0))
            out.append({
                "name": h.get("name", "?"),
                "address": h.get("address", {}).get("countryCode", ""),
                "rating": float(h.get("rating", 4.0) or 4.0),
                "price_per_night": round(price / max(1, _nights(ci, co)), 2),
                "currency": offer.get("price", {}).get("currency", "USD"),
                "amenities": h.get("amenities", []),
                "lat": h.get("latitude"),
                "lng": h.get("longitude"),
            })
        return out


def _nights(ci: str, co: str) -> int:
    from datetime import date
    return max(1, (date.fromisoformat(co) - date.fromisoformat(ci)).days)


def _stub_hotels(city, ci, co, guests) -> list[dict[str, Any]]:
    import hashlib
    # stable across processes (builtin hash() is PYTHONHASHSEED-randomized)
    seed = int(hashlib.md5(city.lower().encode()).hexdigest()[:8], 16)
    base = 80 + (seed % 120)
    return [
        {
            "name": f"{city.title()} Centro Boutique",
            "address": f"Plaza Mayor 1, {city.title()}",
            "rating": 4.4,
            "price_per_night": float(base),
            "currency": "USD",
            "amenities": ["wifi", "breakfast", "ac"],
            "lat": None,
            "lng": None,
        },
        {
            "name": f"Hotel {city.title()} Riverside",
            "address": f"Riverside 22, {city.title()}",
            "rating": 4.1,
            "price_per_night": float(base + 25),
            "currency": "USD",
            "amenities": ["wifi", "gym"],
            "lat": None,
            "lng": None,
        },
        {
            "name": f"{city.title()} Budget Inn",
            "address": f"Old Town 7, {city.title()}",
            "rating": 3.6,
            "price_per_night": float(max(40, base - 35)),
            "currency": "USD",
            "amenities": ["wifi"],
            "lat": None,
            "lng": None,
        },
    ]
