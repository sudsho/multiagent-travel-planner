"""budget agent: reconciles total cost against the user's target."""
from __future__ import annotations

from ..state import BudgetBreakdown, GraphState


FOOD_PER_PERSON_PER_DAY = 35.0  # rough USD


def budget_agent(state: GraphState) -> dict:
    q = state.query
    flights_cost = sum(f.price for f in state.flights[:1]) * max(1, q.party_size)
    nights = max(1, len(state.days) or (q.duration_days or 1))
    lodging_cost = (state.hotel.price_per_night * nights) if state.hotel else 0.0
    activities = sum(a.price for d in state.days for a in d.morning + d.afternoon + d.evening)
    food_buffer = FOOD_PER_PERSON_PER_DAY * nights * max(1, q.party_size)

    total = flights_cost + lodging_cost + activities + food_buffer
    over = bool(q.budget_total and total > q.budget_total)
    bb = BudgetBreakdown(
        transport=round(flights_cost, 2),
        lodging=round(lodging_cost, 2),
        activities=round(activities, 2),
        food_buffer=round(food_buffer, 2),
        total=round(total, 2),
        currency=q.currency,
        over_budget=over,
    )
    return {"budget": bb}
