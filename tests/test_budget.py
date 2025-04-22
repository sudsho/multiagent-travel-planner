from datetime import date

from src.agents.budget import budget_agent
from src.state import Attraction, DayPlan, FlightOption, GraphState, HotelOption, TravelQuery


def _state(budget=1500, days_count=3, attr_price=20.0, hotel_pn=110.0, flight=300.0):
    q = TravelQuery(
        raw_text="x",
        origin="JFK", destination="lisbon",
        start_date=date(2025, 10, 22), end_date=date(2025, 10, 24),
        duration_days=days_count, party_size=2, budget_total=budget, currency="USD",
        interests=["food"],
    )
    days = [
        DayPlan(
            day_index=i + 1, date=date(2025, 10, 22 + i),
            morning=[Attraction(name="m", category="landmark", duration_hours=1.5, price=attr_price)],
            afternoon=[Attraction(name="a", category="museum", duration_hours=2.0, price=attr_price)],
            evening=[Attraction(name="e", category="food", duration_hours=2.0, price=attr_price)],
        )
        for i in range(days_count)
    ]
    return GraphState(
        query=q,
        flights=[FlightOption(carrier="VY", flight_number="123", depart_iata="JFK", arrive_iata="LIS",
                              depart_at="2025-10-22T08:00", arrive_at="2025-10-22T19:00",
                              duration_minutes=600, price=flight, currency="USD", stops=0)],
        hotel=HotelOption(name="h", address="x", rating=4.0, price_per_night=hotel_pn),
        days=days,
    )


def test_budget_under():
    s = _state(budget=2500, days_count=3)
    out = budget_agent(s)
    bb = out["budget"]
    assert bb.over_budget is False
    assert bb.total > 0


def test_budget_over_triggers_drop():
    s = _state(budget=400, days_count=3, attr_price=80.0, hotel_pn=200.0, flight=400.0)
    out = budget_agent(s)
    bb = out["budget"]
    # after dropping priciest items, total should be lower than naive total
    naive_total = 400 * 2 + 200 * 3 + 80 * 9 + 35 * 3 * 2
    assert bb.total < naive_total
