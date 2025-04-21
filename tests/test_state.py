from datetime import date

from src.state import Attraction, BudgetBreakdown, DayPlan, GraphState, TravelQuery


def test_query_round_trip():
    q = TravelQuery(raw_text="hi", destination="lisbon", duration_days=3)
    j = q.model_dump_json()
    back = TravelQuery.model_validate_json(j)
    assert back.destination == "lisbon"
    assert back.duration_days == 3


def test_graph_state_messages_concat():
    s = GraphState(query=TravelQuery(raw_text="x"), messages=[{"a": 1}])
    s.messages = s.messages + [{"a": 2}]
    assert len(s.messages) == 2


def test_dayplan_estimated_cost_default():
    d = DayPlan(day_index=1, date=date(2025, 10, 22))
    assert d.estimated_cost == 0.0


def test_budget_breakdown_currency_default():
    b = BudgetBreakdown()
    assert b.currency == "USD"
    assert b.over_budget is False
