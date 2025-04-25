from datetime import date

from src.agents.coordinator import _next_step
from src.state import (Attraction, BudgetBreakdown, DayPlan, FlightOption, GraphState,
                       HotelOption, TravelQuery, WeatherDay)


def _q():
    return TravelQuery(raw_text="x", destination="lisbon", start_date=date(2025, 10, 22),
                       end_date=date(2025, 10, 26), duration_days=5, party_size=2)


def test_route_research_when_blank():
    assert _next_step(GraphState(query=TravelQuery(raw_text=""))) == "research"


def test_route_transport_after_research():
    s = GraphState(query=_q())
    assert _next_step(s) == "transport"


def test_route_hotel_after_transport():
    s = GraphState(query=_q())
    s.flights = [FlightOption(carrier="x", flight_number="1", depart_iata="JFK", arrive_iata="LIS",
                              depart_at="x", arrive_at="x", duration_minutes=600, price=300)]
    assert _next_step(s) == "hotel"


def test_route_weather_after_hotel():
    s = GraphState(query=_q())
    s.flights = [FlightOption(carrier="x", flight_number="1", depart_iata="JFK", arrive_iata="LIS",
                              depart_at="x", arrive_at="x", duration_minutes=600, price=300)]
    s.hotel = HotelOption(name="h", address="a", rating=4.0, price_per_night=100.0)
    assert _next_step(s) == "weather"


def test_route_finalize_when_all_set():
    s = GraphState(query=_q())
    s.flights = [FlightOption(carrier="x", flight_number="1", depart_iata="JFK", arrive_iata="LIS",
                              depart_at="x", arrive_at="x", duration_minutes=600, price=300)]
    s.hotel = HotelOption(name="h", address="a", rating=4.0, price_per_night=100.0)
    s.weather = [WeatherDay(date=date(2025, 10, 22), temp_c_min=10, temp_c_max=15,
                            precipitation_mm=0, summary="clear")]
    s.attractions = [Attraction(name="a", category="x", duration_hours=1.0, price=0.0)]
    s.days = [DayPlan(day_index=1, date=date(2025, 10, 22))]
    s.budget = BudgetBreakdown(total=100, currency="USD")
    assert _next_step(s) == "finalize"
