from datetime import date

from src.render import render_markdown
from src.state import (Attraction, BudgetBreakdown, DayPlan, FlightOption,
                       HotelOption, Itinerary, TravelQuery, WeatherDay)


def _it():
    q = TravelQuery(
        raw_text="x", origin="JFK", destination="lisbon",
        start_date=date(2025, 10, 22), end_date=date(2025, 10, 23),
        duration_days=2, party_size=2, currency="USD",
    )
    return Itinerary(
        query=q,
        flights=[FlightOption(
            carrier="VY", flight_number="2010", depart_iata="JFK", arrive_iata="LIS",
            depart_at="2025-10-22T08:25", arrive_at="2025-10-22T19:00",
            duration_minutes=635, price=320.0, currency="USD", stops=0,
        )],
        hotel=HotelOption(name="Hotel A", address="x", rating=4.4, price_per_night=110.0),
        days=[
            DayPlan(
                day_index=1, date=date(2025, 10, 22),
                morning=[Attraction(name="Belem", category="landmark", duration_hours=1.5, price=8.0)],
                afternoon=[Attraction(name="Time Out Market", category="food", duration_hours=2.0, price=25.0)],
                evening=[Attraction(name="Alfama walk", category="walking", duration_hours=2.0, price=0.0)],
                weather=WeatherDay(date=date(2025, 10, 22), temp_c_min=14, temp_c_max=22,
                                   precipitation_mm=0.0, summary="clear sky"),
                estimated_cost=33.0,
            ),
            DayPlan(day_index=2, date=date(2025, 10, 23)),
        ],
        budget=BudgetBreakdown(transport=640.0, lodging=110.0, activities=33.0,
                               food_buffer=140.0, total=923.0, currency="USD"),
        summary="2 days in Lisbon with food and architecture.",
    )


def test_render_contains_summary_and_days():
    md = render_markdown(_it())
    assert "Lisbon" in md or "lisbon" in md
    assert "Day 1" in md
    assert "Belem" in md
    assert "Time Out Market" in md
    assert "Budget" in md
