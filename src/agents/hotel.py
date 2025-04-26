"""hotel agent: picks one lodging option."""
from __future__ import annotations

from ..state import GraphState, HotelOption
from ..tools.hotel_api import search_hotels


def hotel_agent(state: GraphState) -> dict:
    q = state.query
    if not q.destination or not q.start_date or not q.end_date:
        return {"errors": state.errors + ["hotel: missing dates/destination"]}

    nights = max(1, (q.end_date - q.start_date).days)
    target_per_night = None
    if q.budget_total:
        # leave ~30% for flights, ~40% for lodging, rest for activities + food
        target_per_night = (q.budget_total * 0.4) / nights / max(1, q.party_size)

    options = search_hotels(
        city=q.destination,
        check_in=q.start_date.isoformat(),
        check_out=q.end_date.isoformat(),
        guests=q.party_size,
        price_target=target_per_night,
    )
    if not options:
        return {"errors": state.errors + ["hotel: no options found"]}

    pick = options[0]
    return {"hotel": HotelOption(**pick)}
