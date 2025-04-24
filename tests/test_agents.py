"""agent unit tests with mocked LLM and tool calls."""
from __future__ import annotations

import json
from datetime import date
from unittest.mock import MagicMock

from src.agents.attractions import attractions_agent
from src.agents.budget import budget_agent
from src.agents.coordinator import _next_step
from src.agents.hotel import hotel_agent
from src.agents.research import research_agent
from src.agents.transport import transport_agent
from src.agents.weather import weather_agent
from src.state import GraphState, TravelQuery


def test_research_offline_fills_dates(base_state):
    out = research_agent(base_state, llm=None)
    q = out["query"]
    assert q.start_date is not None
    assert q.duration_days >= 1


def test_research_with_mock_llm():
    raw = TravelQuery(raw_text="3 days tokyo from sf, 1200 usd, anime")
    s = GraphState(query=raw)
    fake_llm = MagicMock()
    fake_llm.complete.return_value = MagicMock(text=json.dumps({
        "origin": "SFO", "destination": "tokyo",
        "start_date": "2025-11-04", "end_date": "2025-11-06",
        "duration_days": 3, "party_size": 1, "budget_total": 1200,
        "currency": "USD", "interests": ["anime", "food"], "pace": "moderate",
        "notes": None,
    }))
    out = research_agent(s, llm=fake_llm)
    q = out["query"]
    assert q.destination == "tokyo"
    assert q.party_size == 1
    assert "anime" in q.interests


def test_transport_agent_uses_stub(base_state, monkeypatch):
    monkeypatch.delenv("AMADEUS_CLIENT_ID", raising=False)
    out = transport_agent(base_state)
    assert "flights" in out
    assert len(out["flights"]) >= 1


def test_hotel_agent_picks_one(base_state, monkeypatch):
    monkeypatch.delenv("AMADEUS_CLIENT_ID", raising=False)
    out = hotel_agent(base_state)
    assert "hotel" in out


def test_attractions_agent(base_state):
    out = attractions_agent(base_state)
    assert "attractions" in out
    assert len(out["attractions"]) > 0


def test_weather_agent(base_state, monkeypatch):
    monkeypatch.delenv("OPENWEATHER_API_KEY", raising=False)
    out = weather_agent(base_state)
    assert "weather" in out
    assert len(out["weather"]) == 5  # 5 days


def test_supervisor_starts_with_research():
    q = TravelQuery(raw_text="hello")
    s = GraphState(query=q)
    assert _next_step(s) == "research"
