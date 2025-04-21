from datetime import date

from src.scheduler import _haversine, _is_indoor, schedule_days
from src.state import Attraction, GraphState, TravelQuery, WeatherDay


def _attr(name, dur=1.5, price=10.0, cat="landmark", rating=4.4, lat=None, lng=None):
    return Attraction(name=name, category=cat, rating=rating, duration_hours=dur, price=price, lat=lat, lng=lng)


def test_haversine_zero():
    assert _haversine((10.0, 20.0), (10.0, 20.0)) == 0.0


def test_haversine_nonzero():
    d = _haversine((38.7, -9.1), (38.7, -9.2))
    assert 5 < d < 15  # ~9km


def test_is_indoor():
    assert _is_indoor(_attr("Museum X", cat="museum"))
    assert not _is_indoor(_attr("Park", cat="park"))


def test_schedule_basic(base_query):
    items = [_attr(f"a{i}", price=5.0, lat=38.7 + 0.01 * i, lng=-9.1 + 0.01 * i) for i in range(12)]
    s = GraphState(query=base_query, attractions=items)
    out = schedule_days(s)
    assert "days" in out
    assert len(out["days"]) == 5
    total = sum(len(d.morning) + len(d.afternoon) + len(d.evening) for d in out["days"])
    assert total >= 5


def test_schedule_skips_outdoor_in_rain(base_query):
    items = [
        _attr("Outdoor Park", cat="park", dur=2.0, lat=38.7, lng=-9.1),
        _attr("Indoor Museum", cat="museum", dur=2.0, lat=38.71, lng=-9.11),
    ]
    weather = [WeatherDay(
        date=base_query.start_date,
        temp_c_min=10, temp_c_max=15, precipitation_mm=12.0, summary="rain",
    )]
    s = GraphState(query=base_query, attractions=items, weather=weather)
    out = schedule_days(s)
    day1 = out["days"][0]
    morning_first = (day1.morning or [None])[0]
    if morning_first:
        assert morning_first.category == "museum"
