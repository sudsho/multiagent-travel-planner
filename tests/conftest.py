from __future__ import annotations

from datetime import date

import pytest

from src.state import GraphState, TravelQuery


@pytest.fixture
def base_query() -> TravelQuery:
    return TravelQuery(
        raw_text="5 days lisbon late october, food + architecture, mid budget 1500",
        origin="JFK",
        destination="lisbon",
        start_date=date(2025, 10, 22),
        end_date=date(2025, 10, 26),
        duration_days=5,
        party_size=2,
        budget_total=1500,
        currency="USD",
        interests=["food", "architecture"],
        pace="moderate",
    )


@pytest.fixture
def base_state(base_query) -> GraphState:
    return GraphState(query=base_query)
