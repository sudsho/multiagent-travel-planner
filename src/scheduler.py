"""day scheduler: turns a flat attractions list into morning/afternoon/evening slots."""
from __future__ import annotations

from datetime import timedelta
from typing import Iterable

from .state import Attraction, DayPlan, GraphState, WeatherDay


# pace -> hours-per-day budget
PACE_HOURS = {"relaxed": 5.0, "moderate": 7.0, "packed": 9.0}


def _is_indoor(a: Attraction) -> bool:
    cat = (a.category or "").lower()
    return any(t in cat for t in ("museum", "art", "shopping", "food"))


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

        morn = _bucket(sorted_pool, block_h)
        for x in morn:
            sorted_pool.remove(x)
        aft = _bucket(sorted_pool, block_h)
        for x in aft:
            sorted_pool.remove(x)
        eve = _bucket(sorted_pool, block_h)
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
