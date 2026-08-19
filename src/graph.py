"""LangGraph state machine wiring all agents together."""
from __future__ import annotations

from typing import Any

from langgraph.graph import END, StateGraph

from .agents.attractions import attractions_agent
from .agents.budget import budget_agent
from .agents.coordinator import _next_step, supervisor
from .agents.hotel import hotel_agent
from .agents.research import research_agent
from .agents.transport import transport_agent
from .agents.weather import weather_agent
from .llm import LLM
from .scheduler import schedule_days
from .state import GraphState, Itinerary


def _finalize(state: GraphState, llm: LLM | None = None) -> dict:
    it = Itinerary(
        query=state.query,
        flights=state.flights,
        hotel=state.hotel,
        days=state.days,
        budget=state.budget or _empty_budget(state),
    )
    base = (
        f"trip to {state.query.destination} for {state.query.duration_days} days, "
        f"{state.query.party_size} traveler(s); "
        f"est. total {it.budget.total} {it.budget.currency}"
    )
    if llm is not None:
        try:
            from .prompts import SUMMARY_SYSTEM
            res = llm.complete(SUMMARY_SYSTEM, it.model_dump_json())
            it.summary = res.text.strip() or base
        except Exception:
            it.summary = base
    else:
        it.summary = base
    return {"itinerary": it}


def _empty_budget(state: GraphState):
    from .state import BudgetBreakdown
    return BudgetBreakdown(currency=state.query.currency)


# route value (from _next_step) -> graph node name. the node names carry a
# `_node` suffix so they never collide with fields on GraphState (langgraph
# rejects a node whose name equals a state key, e.g. `hotel`, `weather`,
# `attractions`, `budget`).
_ROUTE_TO_NODE = {
    "research": "research_node",
    "transport": "transport_node",
    "hotel": "hotel_node",
    "weather": "weather_node",
    "attractions": "attractions_node",
    "schedule": "schedule_node",
    "budget": "budget_node",
    "finalize": "finalize_node",
}


def _mark_attempted(route_name: str, fn):
    """wrap a worker so every dispatch records itself in state.attempted."""
    def _inner(state: GraphState) -> dict:
        out = dict(fn(state) or {})
        out["attempted"] = [route_name]
        return out
    return _inner


def build_graph(llm: LLM | None = None):
    sg = StateGraph(GraphState)
    sg.add_node("supervisor", supervisor)
    sg.add_node("research_node", _mark_attempted("research", lambda s: research_agent(s, llm=llm)))
    sg.add_node("transport_node", _mark_attempted("transport", transport_agent))
    sg.add_node("hotel_node", _mark_attempted("hotel", hotel_agent))
    sg.add_node("weather_node", _mark_attempted("weather", weather_agent))
    sg.add_node("attractions_node", _mark_attempted("attractions", attractions_agent))
    sg.add_node("schedule_node", _mark_attempted("schedule", schedule_days))
    sg.add_node("budget_node", _mark_attempted("budget", budget_agent))
    sg.add_node("finalize_node", lambda s: _finalize(s, llm=llm))

    def _route(state: GraphState) -> str:
        # _next_step returns a logical route value ("hotel", "budget", ...);
        # the path map below turns it into the matching graph node name.
        return _next_step(state)

    sg.set_entry_point("supervisor")
    sg.add_conditional_edges("supervisor", _route, _ROUTE_TO_NODE)
    # every worker returns to the supervisor for the next routing decision
    for node in [
        "research_node", "transport_node", "hotel_node", "weather_node",
        "attractions_node", "schedule_node", "budget_node",
    ]:
        sg.add_edge(node, "supervisor")
    sg.add_edge("finalize_node", END)
    return sg.compile()


def run(query_text: str, llm: LLM | None = None) -> Itinerary:
    from .state import TravelQuery
    g = build_graph(llm=llm)
    state = GraphState(query=TravelQuery(raw_text=query_text))
    out = g.invoke(state, config={"recursion_limit": 30})
    return out["itinerary"]  # type: ignore[index]
