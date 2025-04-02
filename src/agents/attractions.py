"""attractions agent: picks places to visit, returns a flat ranked list."""
from __future__ import annotations

from ..state import Attraction, GraphState
from ..tools.maps import nearby_attractions


def attractions_agent(state: GraphState) -> dict:
    q = state.query
    if not q.destination:
        return {"errors": state.errors + ["attractions: no destination"]}

    raw = nearby_attractions(city=q.destination, interests=q.interests, limit=24)
    out = [Attraction(**a) for a in raw]
    return {"attractions": out}
