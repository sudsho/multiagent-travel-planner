"""weather agent: forecast for each day of the trip."""
from __future__ import annotations

from datetime import timedelta

from ..state import GraphState, WeatherDay
from ..tools.openweather import get_forecast


def weather_agent(state: GraphState) -> dict:
    q = state.query
    if not q.destination or not q.start_date or not q.end_date:
        return {"errors": state.errors + ["weather: missing dates/destination"]}

    days = []
    cursor = q.start_date
    while cursor <= q.end_date:
        try:
            f = get_forecast(city=q.destination, on_date=cursor.isoformat())
            days.append(WeatherDay(date=cursor, **f))
        except Exception as e:
            state.errors.append(f"weather error {cursor}: {e}")
        cursor += timedelta(days=1)
    return {"weather": days}
