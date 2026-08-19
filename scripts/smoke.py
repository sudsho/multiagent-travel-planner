"""Offline smoke test for the multi-agent travel planner.

Runs the full planner -> researcher -> specialist -> budgeter loop with NO API
keys and NO network:

  - a deterministic MockLLM stands in for OpenAI/Anthropic (rule-based per role)
  - every travel tool (flights, hotels, weather, attractions) uses its bundled
    offline stub / sample data

It streams the LangGraph state machine so you can watch each agent fire and each
tool return, then prints the assembled day-by-day itinerary and budget total.

Run:  python scripts/smoke.py       (or: make smoke)
Exits non-zero if any core invariant fails.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

# make `src` importable when run as a plain script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# force fully offline mode: no provider keys, sqlite cache in a temp file
for _k in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "OPENWEATHER_API_KEY",
           "AMADEUS_CLIENT_ID", "AMADEUS_CLIENT_SECRET", "GOOGLE_MAPS_API_KEY"):
    os.environ.pop(_k, None)
os.environ["CACHE_BACKEND"] = "sqlite"
os.environ["SQLITE_CACHE_PATH"] = str(Path(tempfile.mkdtemp(prefix="travel_smoke_")) / "cache.db")

from src.graph import build_graph  # noqa: E402
from src.llm import mock_llm  # noqa: E402
from src.render import render_markdown  # noqa: E402
from src.state import GraphState, Itinerary, TravelQuery  # noqa: E402

SAMPLE_QUERY = (
    "plan me 5 days in lisbon late october 2025, mid budget around 1500 USD, "
    "mostly food and architecture, 2 people from new york"
)

# which tool each worker node exercises, for the trace line
_TOOL_BY_NODE = {
    "research_node": "MockLLM.complete (research role)",
    "transport_node": "tools.transport_api.search_flights (stub)",
    "hotel_node": "tools.hotel_api.search_hotels (stub)",
    "weather_node": "tools.openweather.get_forecast (stub)",
    "attractions_node": "tools.maps.nearby_attractions (sample_destinations.json)",
    "schedule_node": "scheduler.schedule_days (local)",
    "budget_node": "agents.budget (local reconcile)",
    "finalize_node": "MockLLM.complete (summary role)",
}


def _summarize_update(node: str, upd: dict) -> str:
    if not isinstance(upd, dict):
        return ""
    if "query" in upd:
        q = upd["query"]
        return f"parsed dest={q.destination} origin={q.origin} {q.duration_days}d party={q.party_size} budget={q.budget_total}"
    if "flights" in upd:
        fl = upd["flights"]
        return f"{len(fl)} flight option(s)" + (f", best {fl[0].carrier}{fl[0].flight_number} {fl[0].price:.0f} USD" if fl else "")
    if "hotel" in upd and upd["hotel"] is not None:
        h = upd["hotel"]
        return f"picked {h.name} @ {h.price_per_night:.0f} USD/night"
    if "weather" in upd:
        return f"{len(upd['weather'])} day forecast"
    if "attractions" in upd:
        return f"{len(upd['attractions'])} candidate attraction(s)"
    if "days" in upd and "budget" not in upd:
        return f"{len(upd['days'])} day plan(s) scheduled"
    if "budget" in upd:
        b = upd["budget"]
        return f"total {b.total:.0f} {b.currency} (over_budget={b.over_budget})"
    if "itinerary" in upd:
        return "itinerary finalized + summarized"
    if "errors" in upd:
        return "note: " + "; ".join(upd["errors"][-1:])
    return ""


def main() -> int:
    print("=" * 70)
    print("multiagent-travel-planner : OFFLINE SMOKE")
    print("=" * 70)
    print(f"LLM        : MockLLM (deterministic, no keys)")
    print(f"tools      : bundled stubs (no external API calls)")
    print(f"cache      : sqlite @ {os.environ['SQLITE_CACHE_PATH']}")
    print(f"request    : {SAMPLE_QUERY}")
    print("-" * 70)
    print("AGENT / TOOL TRACE")

    llm = mock_llm()
    graph = build_graph(llm=llm)
    state = GraphState(query=TravelQuery(raw_text=SAMPLE_QUERY))

    itinerary: Itinerary | None = None
    step = 0
    for chunk in graph.stream(state, config={"recursion_limit": 40}):
        for node, upd in chunk.items():
            step += 1
            if node == "supervisor":
                nxt = (upd.get("messages") or [{}])[-1].get("next", "?")
                print(f"  [{step:02d}] supervisor            -> route: {nxt}")
                continue
            tool = _TOOL_BY_NODE.get(node, "")
            detail = _summarize_update(node, upd)
            print(f"  [{step:02d}] {node:<21}-> {tool}")
            if detail:
                print(f"        {detail}")
            if isinstance(upd, dict) and upd.get("itinerary") is not None:
                itinerary = upd["itinerary"]

    print("-" * 70)
    if itinerary is None:
        print("FAIL: no itinerary produced")
        return 1

    print("STRUCTURED ITINERARY")
    print(render_markdown(itinerary))
    print("-" * 70)

    # invariants
    checks = {
        "destination parsed": itinerary.query.destination == "lisbon",
        "duration parsed (5d)": itinerary.query.duration_days == 5,
        "origin parsed (llm)": itinerary.query.origin == "new york",
        "flights found": len(itinerary.flights) >= 1,
        "hotel picked": itinerary.hotel is not None,
        "days scheduled": len(itinerary.days) == 5,
        "activities present": sum(
            len(d.morning) + len(d.afternoon) + len(d.evening) for d in itinerary.days
        ) >= 5,
        "budget total > 0": itinerary.budget.total > 0,
        "summary written": bool(itinerary.summary),
        "llm invoked": len(llm.calls) >= 2,
    }
    print("INVARIANTS")
    ok = True
    for name, passed in checks.items():
        print(f"  [{'PASS' if passed else 'FAIL'}] {name}")
        ok = ok and passed

    print("-" * 70)
    if ok:
        print(f"SMOKE OK - {len(itinerary.days)}-day itinerary, "
              f"budget {itinerary.budget.total:.0f} {itinerary.budget.currency}, "
              f"{len(llm.calls)} LLM calls, no network.")
        return 0
    print("SMOKE FAILED - see invariants above")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
