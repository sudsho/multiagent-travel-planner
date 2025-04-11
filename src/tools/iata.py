"""tiny city-to-IATA mapping for stub mode. for prod use Amadeus reference data."""
from __future__ import annotations

CITY_TO_IATA = {
    "lisbon": "LIS",
    "porto": "OPO",
    "madrid": "MAD",
    "barcelona": "BCN",
    "paris": "CDG",
    "london": "LHR",
    "amsterdam": "AMS",
    "rome": "FCO",
    "berlin": "BER",
    "tokyo": "HND",
    "kyoto": "ITM",
    "osaka": "KIX",
    "bangkok": "BKK",
    "singapore": "SIN",
    "delhi": "DEL",
    "mumbai": "BOM",
    "bangalore": "BLR",
    "new york": "JFK",
    "san francisco": "SFO",
    "los angeles": "LAX",
    "chicago": "ORD",
    "louisville": "SDF",
    "washington": "IAD",
    "boston": "BOS",
    "miami": "MIA",
}


def to_iata(city: str | None) -> str | None:
    if not city:
        return None
    return CITY_TO_IATA.get(city.strip().lower())
