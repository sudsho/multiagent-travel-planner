"""transport agent: fetches flight/train options."""
from __future__ import annotations

from ..state import FlightOption, GraphState
from ..tools.transport_api import search_flights


def transport_agent(state: GraphState) -> dict:
    q = state.query
    if not q.origin or not q.destination or not q.start_date:
        return {"errors": state.errors + ["transport: missing origin/destination/start_date"]}

    options = search_flights(
        origin=q.origin,
        destination=q.destination,
        date_str=q.start_date.isoformat(),
        party_size=q.party_size,
    )
    flights = [FlightOption(**o) for o in options[:3]]
    return {"flights": flights}
