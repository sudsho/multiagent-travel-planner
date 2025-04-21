"""day scheduler: turns a flat attractions list into morning/afternoon/evening slots."""
from __future__ import annotations

from datetime import timedelta
from typing import Iterable

from .state import Attraction, DayPlan, GraphState, WeatherDay


# pace -> hours-per-day budget
PACE_HOURS = {"relaxed": 5.0, "moderate": 7.0, "packed": 9.0}


def _is_indoor(a: Attraction) -> bool:
    cat = (a.category or "").lower()
    return any(t in cat for t in ("museum", "art", "shopping", "food", "gallery", "theater"))


def _haversine(a, b) -> float:
    import math
    if not (a and b):
        return 0.0
    lat1, lon1 = a
    lat2, lon2 = b
    if None in (lat1, lon1, lat2, lon2):
        return 0.0
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def _cluster_by_location(items: list[Attraction]) -> list[Attraction]:
    """greedy nearest-neighbor ordering to keep each block geographically close."""
    rest = list(items)
    if not rest:
        return rest
    out = [rest.pop(0)]
    while rest:
        prev = (out[-1].lat, out[-1].lng) if out[-1].lat else None
        if prev is None:
            out.append(rest.pop(0))
            continue
        rest.sort(key=lambda a: _haversine(prev, (a.lat, a.lng)) if a.lat else 1e6)
        out.append(rest.pop(0))
    return out


def _bucket(items: list[Attraction], hours: float) -> list[Attraction]:
    out, used = [], 0.0
    for a in items:
        if used + a.duration_hours > hours:
            continue
        out.append(a)
        used += a.duration_hours
    return out


def _weather_aware_sort(items: list[Attraction], w: WeatherDay | None) -> list[Attraction]:
    if w is None:
        return list(items)
    rainy = w.precipitation_mm > 4.0
    if not rainy:
        return list(items)
    return sorted(items, key=lambda a: (0 if _is_indoor(a) else 1, -(a.rating or 0)))


def schedule_days(state: GraphState) -> dict:
    q = state.query
    if not q.start_date or not q.duration_days:
        return {"errors": state.errors + ["scheduler: missing start_date/duration"]}
    if not state.attractions:
        return {"errors": state.errors + ["scheduler: no attractions"]}

    pool = sorted(state.attractions, key=lambda a: -(a.rating or 0))
    weather_by_day = {w.date: w for w in state.weather}

    days: list[DayPlan] = []
    cursor = q.start_date
    pool_iter = list(pool)

    daily_budget_h = PACE_HOURS.get(q.pace, 7.0)
    block_h = daily_budget_h / 3.0

    for d in range(q.duration_days):
        w = weather_by_day.get(cursor)
        sorted_pool = _weather_aware_sort(pool_iter, w)

        morn = _cluster_by_location(_bucket(sorted_pool, block_h))
        for x in morn:
            sorted_pool.remove(x)
        aft = _cluster_by_location(_bucket(sorted_pool, block_h))
        for x in aft:
            sorted_pool.remove(x)
        eve = _cluster_by_location(_bucket(sorted_pool, block_h))
        for x in eve:
            sorted_pool.remove(x)

        # write back the consumed pool order
        pool_iter = sorted_pool

        cost = sum(a.price for a in morn + aft + eve)
        notes = "rainy day, indoor-leaning" if (w and w.precipitation_mm > 4.0) else None
        days.append(DayPlan(
            day_index=d + 1,
            date=cursor,
            morning=morn,
            afternoon=aft,
            evening=eve,
            weather=w,
            estimated_cost=round(cost, 2),
            notes=notes,
        ))
        cursor += timedelta(days=1)

    return {"days": days}
