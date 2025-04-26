"""end-to-end graph test (no LLM, offline stubs)."""
from __future__ import annotations

import os

from src.graph import run as run_graph


def test_run_offline(monkeypatch, tmp_path):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENWEATHER_API_KEY", raising=False)
    monkeypatch.delenv("AMADEUS_CLIENT_ID", raising=False)
    monkeypatch.delenv("AMADEUS_CLIENT_SECRET", raising=False)
    monkeypatch.setenv("SQLITE_CACHE_PATH", str(tmp_path / "c.db"))

    it = run_graph("3 days in lisbon, food and architecture, 800 usd, from new york")
    assert it.query.destination == "lisbon"
    assert len(it.days) >= 1
    assert it.budget.total > 0


def test_run_short_query_still_returns(monkeypatch, tmp_path):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("SQLITE_CACHE_PATH", str(tmp_path / "c.db"))
    it = run_graph("4 days lisbon")
    assert it.query.destination == "lisbon"
    assert it.query.duration_days == 4
