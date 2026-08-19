"""tests for the deterministic offline MockLLM and the mock-LLM graph path."""
from __future__ import annotations

import json

from src.graph import run as run_graph
from src.llm import MockLLM, llm_from_env, mock_llm
from src.prompts import RESEARCH_SYSTEM, SUMMARY_SYSTEM


def test_mock_llm_never_needs_a_key():
    llm = mock_llm()
    assert isinstance(llm, MockLLM)
    # research role returns strict JSON with the extracted fields
    out = llm.complete(RESEARCH_SYSTEM, "3 days in tokyo, solo from sf, under 1200 usd, anime + food")
    data = json.loads(out.text)
    assert data["destination"] == "tokyo"
    assert data["origin"] == "san francisco"
    assert data["duration_days"] == 3
    assert data["party_size"] == 1
    assert data["budget_total"] == 1200.0
    assert "anime" in data["interests"]


def test_mock_llm_does_not_grab_year_as_budget():
    llm = mock_llm()
    data = json.loads(llm.complete(RESEARCH_SYSTEM,
                                   "5 days in lisbon late october 2025, around 1500 usd").text)
    assert data["budget_total"] == 1500.0


def test_mock_llm_summary_role():
    llm = mock_llm()
    itin = {
        "query": {"destination": "lisbon", "duration_days": 5, "party_size": 2},
        "days": [{"morning": [{"name": "Belem Tower"}], "afternoon": [], "evening": []}],
        "budget": {"total": 1415.0, "currency": "USD"},
    }
    text = llm.complete(SUMMARY_SYSTEM, json.dumps(itin)).text
    assert "Lisbon" in text
    assert "1415" in text


def test_llm_from_env_selects_mock(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    assert isinstance(llm_from_env(), MockLLM)


def test_graph_runs_with_mock_llm(monkeypatch, tmp_path):
    for k in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "OPENWEATHER_API_KEY",
              "AMADEUS_CLIENT_ID", "AMADEUS_CLIENT_SECRET"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("SQLITE_CACHE_PATH", str(tmp_path / "c.db"))

    llm = mock_llm()
    it = run_graph(
        "plan me 5 days in lisbon late october 2025, mid budget around 1500 USD, "
        "mostly food and architecture, 2 people from new york",
        llm=llm,
    )
    # the LLM parsed the origin, so transport actually runs (vs the no-llm path)
    assert it.query.origin == "new york"
    assert it.query.party_size == 2
    assert len(it.flights) >= 1
    assert len(it.days) == 5
    assert it.budget.total > 0
    assert it.summary
    assert len(llm.calls) >= 2  # research + summary
