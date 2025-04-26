"""research agent: parses the vague user prompt and fills in TravelQuery gaps."""
from __future__ import annotations

import json
import re
from datetime import date, timedelta
from typing import Any

from ..llm import LLM
from ..prompts import RESEARCH_SYSTEM as SYSTEM_PROMPT
from ..state import GraphState, TravelQuery


def _strip_code_fences(s: str) -> str:
    s = s.strip()
    if s.startswith("```"):
        s = re.sub(r"^```[a-zA-Z]*\n", "", s)
        s = re.sub(r"\n```$", "", s)
    return s


def _parse_query(text: str) -> dict[str, Any]:
    try:
        return json.loads(_strip_code_fences(text))
    except Exception:
        return {}


_KNOWN_CITIES = {
    "lisbon", "porto", "madrid", "barcelona", "paris", "london", "amsterdam",
    "rome", "berlin", "tokyo", "kyoto", "osaka", "bangkok", "singapore",
    "delhi", "mumbai", "bangalore", "new york", "san francisco",
    "los angeles", "chicago", "louisville", "boston", "miami",
}


def _heuristic_parse(q: TravelQuery) -> TravelQuery:
    """very small regex parser used when no LLM is available."""
    text = (q.raw_text or "").lower()
    updates: dict[str, Any] = {}

    if not q.destination:
        for c in _KNOWN_CITIES:
            if c in text:
                updates["destination"] = c
                break

    m = re.search(r"(\d+)\s*(?:day|days|d)\b", text)
    if m and not q.duration_days:
        updates["duration_days"] = int(m.group(1))

    m = re.search(r"\$?(\d{3,5})\s*(?:usd|dollars|\$)?", text)
    if m and not q.budget_total:
        updates["budget_total"] = float(m.group(1))

    if "solo" in text and not q.party_size:
        updates["party_size"] = 1

    interests = []
    for kw in ("food", "museum", "art", "hike", "park", "beach", "shop", "anime",
              "architecture", "history", "nightlife", "cafe"):
        if kw in text:
            interests.append(kw)
    if interests and not q.interests:
        updates["interests"] = interests

    return q.model_copy(update=updates)


def research_agent(state: GraphState, llm: LLM | None = None) -> dict:
    """fill out TravelQuery from raw_text."""
    q = state.query
    if not q.raw_text:
        return {"errors": state.errors + ["no raw_text"]}

    if llm is None:
        # offline / smoke-test default fallback. try a tiny regex-based parse.
        merged = _heuristic_parse(q)
    else:
        try:
            out = llm.complete(SYSTEM_PROMPT, q.raw_text)
            parsed = _parse_query(out.text)
        except Exception:
            parsed = {}
        merged = q.model_copy(update={
            k: v for k, v in parsed.items()
            if v is not None and k in TravelQuery.model_fields
        })

    if not merged.duration_days and merged.start_date and merged.end_date:
        merged = merged.model_copy(update={
            "duration_days": (merged.end_date - merged.start_date).days + 1
        })
    if merged.duration_days and not merged.end_date and merged.start_date:
        merged = merged.model_copy(update={
            "end_date": merged.start_date + timedelta(days=merged.duration_days - 1)
        })
    if not merged.start_date:
        # default: 30 days out for 5 days
        merged = merged.model_copy(update={
            "start_date": date.today() + timedelta(days=30),
            "end_date": date.today() + timedelta(days=34),
            "duration_days": 5,
        })

    notes = (merged.notes or "")[:200]
    return {
        "query": merged,
        "research_notes": f"parsed query for {merged.destination or 'destination?'} ({merged.duration_days}d). {notes}",
    }
