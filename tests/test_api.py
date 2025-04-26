"""FastAPI smoke tests."""
from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

from src.api.main import app


@pytest.fixture
def client(monkeypatch, tmp_path):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENWEATHER_API_KEY", raising=False)
    monkeypatch.delenv("AMADEUS_CLIENT_ID", raising=False)
    monkeypatch.setenv("SQLITE_CACHE_PATH", str(tmp_path / "c.db"))
    return TestClient(app)


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_plan_endpoint(client):
    r = client.post("/plan", json={"query": "3 days in lisbon, food, 800 usd, from new york"})
    assert r.status_code == 200
    body = r.json()
    assert "summary" in body
    assert "itinerary" in body
    assert "markdown" in body
