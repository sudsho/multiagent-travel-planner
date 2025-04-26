from src.agents.research import _heuristic_parse, research_agent
from src.state import GraphState, TravelQuery


def test_heuristic_extracts_city_and_days():
    q = TravelQuery(raw_text="3 days in tokyo, anime + food, 1200 usd")
    out = _heuristic_parse(q)
    assert out.destination == "tokyo"
    assert out.duration_days == 3
    assert "food" in out.interests
    assert "anime" in out.interests


def test_heuristic_solo():
    q = TravelQuery(raw_text="solo trip 5 days lisbon", party_size=0)
    out = _heuristic_parse(q)
    assert out.party_size == 1


def test_heuristic_no_match_keeps_query_intact():
    q = TravelQuery(raw_text="vague vibes")
    out = _heuristic_parse(q)
    assert out.destination is None


def test_research_offline_falls_back_to_heuristic():
    s = GraphState(query=TravelQuery(raw_text="5 days in lisbon, food"))
    out = research_agent(s, llm=None)
    q = out["query"]
    assert q.destination == "lisbon"
    assert q.duration_days == 5
