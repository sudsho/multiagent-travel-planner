"""transport agent: fetches flight/train options."""
from __future__ import annotations

from ..state import FlightOption, GraphState
from ..tools.iata import to_iata
from ..tools.transport_api import search_flights


def transport_agent(state: GraphState) -> dict:
    q = state.query
    if not q.destination or not q.start_date:
        return {"errors": state.errors + ["transport: missing destination/start_date"]}
    if not q.origin:
        # default fallback origin so the graph still progresses
        return {"errors": state.errors + ["transport: no origin specified, skipping flight lookup"]}

    origin_code = to_iata(q.origin) or q.origin
    dest_code = to_iata(q.destination) or q.destination
    if len(origin_code) > 3:
        # avoid Amadeus error on unknown city names
        origin_code = origin_code[:3].upper()
    if len(dest_code) > 3:
        dest_code = dest_code[:3].upper()
    options = search_flights(
        origin=origin_code,
        destination=dest_code,
        date_str=q.start_date.isoformat(),
        party_size=q.party_size,
    )
    flights = [FlightOption(**o) for o in options[:3]]
    return {"flights": flights}
