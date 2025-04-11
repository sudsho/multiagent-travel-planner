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


def research_agent(state: GraphState, llm: LLM | None = None) -> dict:
    """fill out TravelQuery from raw_text."""
    q = state.query
    if not q.raw_text:
        return {"errors": state.errors + ["no raw_text"]}

    if llm is None:
        # offline / smoke-test default fallback
        merged = q
    else:
        out = llm.complete(SYSTEM_PROMPT, q.raw_text)
        parsed = _parse_query(out.text)
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
