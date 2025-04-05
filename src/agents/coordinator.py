"""supervisor: routes between sub-agents and decides the next step."""
from __future__ import annotations

from typing import Literal

from ..state import GraphState


AgentName = Literal[
    "research", "transport", "hotel", "weather",
    "attractions", "schedule", "budget", "finalize", "end",
]


def supervisor(state: GraphState) -> dict:
    """returns the next node name in `messages[-1].next`. real routing happens in graph.py."""
    nxt = _next_step(state)
    return {
        "messages": [{"role": "supervisor", "next": nxt, "rev": state.revision}],
        "revision": state.revision + 1,
    }


def _next_step(state: GraphState) -> AgentName:
    q = state.query
    # phase 1: research must run first
    if not q.destination or not q.start_date:
        return "research"
    # phase 2: parallel-ish lookups
    if not state.flights:
        return "transport"
    if not state.hotel:
        return "hotel"
    if not state.weather:
        return "weather"
    if not state.attractions:
        return "attractions"
    # phase 3: assemble + reconcile
    if not state.days:
        return "schedule"
    if not state.budget:
        return "budget"
    return "finalize"
