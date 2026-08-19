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
    done = set(state.attempted or [])
    # phase 1: research must run first
    if (not q.destination or not q.start_date) and "research" not in done:
        return "research"
    # phase 2: parallel-ish lookups. a step already dispatched is skipped even
    # if it produced nothing (e.g. transport with no origin), so the supervisor
    # never loops on it.
    if not state.flights and "transport" not in done:
        return "transport"
    if not state.hotel and "hotel" not in done:
        return "hotel"
    if not state.weather and "weather" not in done:
        return "weather"
    if not state.attractions and "attractions" not in done:
        return "attractions"
    # phase 3: assemble + reconcile
    if not state.days and "schedule" not in done:
        return "schedule"
    if not state.budget and "budget" not in done:
        return "budget"
    return "finalize"
