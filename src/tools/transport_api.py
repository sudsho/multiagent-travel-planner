"""flight search wrapper. uses Amadeus Flight Offers if configured, else stub."""
from __future__ import annotations

import os
from datetime import datetime
from typing import Any

import httpx

from ..cache import make_cache
from .auth import amadeus_token


def _key(origin: str, dest: str, date_str: str, party_size: int) -> str:
    return f"flights:{origin}:{dest}:{date_str}:{party_size}"


def search_flights(origin: str, destination: str, date_str: str, party_size: int = 1) -> list[dict[str, Any]]:
    cache = make_cache()
    k = _key(origin, destination, date_str, party_size)
    if (c := cache.get(k)) is not None:
        return c

    cid = os.getenv("AMADEUS_CLIENT_ID")
    sec = os.getenv("AMADEUS_CLIENT_SECRET")
    if cid and sec:
        try:
            out = _amadeus_flights(origin, destination, date_str, party_size, cid, sec)
            cache.set(k, out, ttl=1800)
            return out
        except Exception:
            pass

    out = _stub_flights(origin, destination, date_str)
    cache.set(k, out, ttl=1800)
    return out


def _amadeus_flights(origin, dest, date_str, party_size, cid, sec) -> list[dict[str, Any]]:
    token = amadeus_token(cid, sec)
    with httpx.Client(timeout=12.0) as client:
        r = client.get(
            "https://test.api.amadeus.com/v2/shopping/flight-offers",
            headers={"Authorization": f"Bearer {token}"},
            params={
                "originLocationCode": origin[:3].upper(),
                "destinationLocationCode": dest[:3].upper(),
                "departureDate": date_str,
                "adults": party_size,
                "max": 5,
                "currencyCode": "USD",
            },
        )
        r.raise_for_status()
        out = []
        for offer in r.json().get("data", []):
            seg = offer["itineraries"][0]["segments"][0]
            last = offer["itineraries"][0]["segments"][-1]
            duration = _iso_duration_to_minutes(offer["itineraries"][0].get("duration", "PT2H"))
            out.append({
                "carrier": seg.get("carrierCode", "??"),
                "flight_number": seg.get("number", "?"),
                "depart_iata": seg["departure"]["iataCode"],
                "arrive_iata": last["arrival"]["iataCode"],
                "depart_at": seg["departure"]["at"],
                "arrive_at": last["arrival"]["at"],
                "duration_minutes": duration,
                "price": float(offer["price"]["total"]),
                "currency": offer["price"].get("currency", "USD"),
                "stops": len(offer["itineraries"][0]["segments"]) - 1,
            })
        return out


def _iso_duration_to_minutes(s: str) -> int:
    # PT3H45M -> 225
    s = s.replace("PT", "")
    h = m = 0
    if "H" in s:
        h_part, _, rest = s.partition("H")
        h = int(h_part)
        s = rest
    if "M" in s:
        m = int(s.replace("M", ""))
    return h * 60 + m


def _stub_flights(origin, dest, date_str) -> list[dict[str, Any]]:
    seed = abs(hash((origin, dest, date_str)))
    base = 180 + (seed % 320)
    return [
        {
            "carrier": "VY",
            "flight_number": str(2000 + seed % 800),
            "depart_iata": origin[:3].upper(),
            "arrive_iata": dest[:3].upper(),
            "depart_at": f"{date_str}T08:25",
            "arrive_at": f"{date_str}T11:40",
            "duration_minutes": 195,
            "price": float(base),
            "currency": "USD",
            "stops": 0,
        },
        {
            "carrier": "TP",
            "flight_number": str(800 + seed % 200),
            "depart_iata": origin[:3].upper(),
            "arrive_iata": dest[:3].upper(),
            "depart_at": f"{date_str}T13:10",
            "arrive_at": f"{date_str}T16:55",
            "duration_minutes": 225,
            "price": float(base + 60),
            "currency": "USD",
            "stops": 0,
        },
        {
            "carrier": "AF",
            "flight_number": str(1500 + seed % 600),
            "depart_iata": origin[:3].upper(),
            "arrive_iata": dest[:3].upper(),
            "depart_at": f"{date_str}T19:45",
            "arrive_at": f"{date_str}T23:30",
            "duration_minutes": 225,
            "price": float(max(120, base - 40)),
            "currency": "USD",
            "stops": 1,
        },
    ]
