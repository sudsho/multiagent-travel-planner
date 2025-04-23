"""tool tests with mocked HTTP."""
from __future__ import annotations

from unittest.mock import patch

from src.tools import iata
from src.tools.openweather import _stub as ow_stub
from src.tools.transport_api import _stub_flights
from src.tools.hotel_api import _stub_hotels


def test_iata_lookup():
    assert iata.to_iata("Lisbon") == "LIS"
    assert iata.to_iata("LISBON") == "LIS"
    assert iata.to_iata("nowhere") is None
    assert iata.to_iata(None) is None


def test_stub_flights_three_options():
    out = _stub_flights("JFK", "LIS", "2025-10-22")
    assert len(out) == 3
    assert all(f["depart_iata"] == "JFK" for f in out)
    assert all(f["price"] > 0 for f in out)


def test_stub_hotels_three_options():
    out = _stub_hotels("lisbon", "2025-10-22", "2025-10-26", 2)
    assert len(out) == 3
    assert all("price_per_night" in h for h in out)


def test_stub_weather_keys(tmp_path, monkeypatch):
    monkeypatch.setenv("SQLITE_CACHE_PATH", str(tmp_path / "c.db"))
    monkeypatch.setenv("CACHE_BACKEND", "sqlite")

    class _C:
        def set(self, *a, **k): pass

    out = ow_stub("lisbon", "2025-10-22", _C(), "k")
    for k in ("temp_c_min", "temp_c_max", "precipitation_mm", "summary"):
        assert k in out


def test_search_flights_uses_stub_when_no_keys(monkeypatch, tmp_path):
    monkeypatch.delenv("AMADEUS_CLIENT_ID", raising=False)
    monkeypatch.delenv("AMADEUS_CLIENT_SECRET", raising=False)
    monkeypatch.setenv("SQLITE_CACHE_PATH", str(tmp_path / "c.db"))
    from src.tools.transport_api import search_flights
    out = search_flights("JFK", "LIS", "2025-10-22", 1)
    assert len(out) == 3
