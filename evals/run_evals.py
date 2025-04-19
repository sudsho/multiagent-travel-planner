"""run scenarios end-to-end (no LLM if OPENAI_API_KEY is unset; agents fall back)."""
from __future__ import annotations

import json
from typing import Any

from src.graph import run as run_graph
from src.state import Itinerary
from .scenarios import SCENARIOS, Scenario


def evaluate(it: Itinerary, sc: Scenario) -> dict[str, Any]:
    exp = sc.expected
    issues: list[str] = []
    if "destination" in exp and (it.query.destination or "").lower() != exp["destination"].lower():
        issues.append(f"destination mismatch: got {it.query.destination}")
    if "duration_days" in exp and it.query.duration_days != exp["duration_days"]:
        issues.append(f"duration mismatch: got {it.query.duration_days}")
    total_attractions = sum(
        len(d.morning) + len(d.afternoon) + len(d.evening) for d in it.days
    )
    if "min_attractions_total" in exp and total_attractions < exp["min_attractions_total"]:
        issues.append(f"too few attractions: {total_attractions}")
    if "budget_under_usd" in exp and it.budget.total > exp["budget_under_usd"]:
        issues.append(f"over budget: {it.budget.total} > {exp['budget_under_usd']}")
    if "min_food_attractions" in exp:
        food = sum(
            1 for d in it.days for a in d.morning + d.afternoon + d.evening
            if "food" in (a.category or "").lower()
        )
        if food < exp["min_food_attractions"]:
            issues.append(f"too few food stops: {food}")
    return {"scenario": sc.name, "ok": not issues, "issues": issues, "total_cost": it.budget.total}


def main() -> int:
    rows = []
    for sc in SCENARIOS:
        it = run_graph(sc.prompt)
        rows.append(evaluate(it, sc))
    print(json.dumps(rows, indent=2))
    return 0 if all(r["ok"] for r in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
