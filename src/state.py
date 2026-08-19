"""shared graph state + itinerary schema."""
from __future__ import annotations

from datetime import date as _date
from typing import Annotated, Any, Literal, Optional

from pydantic import BaseModel, Field


class TravelQuery(BaseModel):
    """raw user-facing query parsed by the supervisor."""

    raw_text: str
    origin: Optional[str] = None
    destination: Optional[str] = None
    start_date: Optional[_date] = None
    end_date: Optional[_date] = None
    duration_days: Optional[int] = None
    party_size: int = 1
    budget_total: Optional[float] = None
    currency: str = "USD"
    interests: list[str] = Field(default_factory=list)
    pace: Literal["relaxed", "moderate", "packed"] = "moderate"
    notes: Optional[str] = None


class FlightOption(BaseModel):
    carrier: str
    flight_number: str
    depart_iata: str
    arrive_iata: str
    depart_at: str
    arrive_at: str
    duration_minutes: int
    price: float
    currency: str = "USD"
    stops: int = 0


class HotelOption(BaseModel):
    name: str
    address: str
    rating: float
    price_per_night: float
    currency: str = "USD"
    amenities: list[str] = Field(default_factory=list)
    lat: Optional[float] = None
    lng: Optional[float] = None


class Attraction(BaseModel):
    name: str
    category: str
    rating: Optional[float] = None
    duration_hours: float = 2.0
    price: float = 0.0
    lat: Optional[float] = None
    lng: Optional[float] = None
    notes: Optional[str] = None


class WeatherDay(BaseModel):
    date: _date
    temp_c_min: float
    temp_c_max: float
    precipitation_mm: float
    summary: str


class DayPlan(BaseModel):
    day_index: int
    date: _date
    morning: list[Attraction] = Field(default_factory=list)
    afternoon: list[Attraction] = Field(default_factory=list)
    evening: list[Attraction] = Field(default_factory=list)
    notes: Optional[str] = None
    weather: Optional[WeatherDay] = None
    estimated_cost: float = 0.0


class BudgetBreakdown(BaseModel):
    transport: float = 0.0
    lodging: float = 0.0
    activities: float = 0.0
    food_buffer: float = 0.0
    total: float = 0.0
    currency: str = "USD"
    over_budget: bool = False


class Itinerary(BaseModel):
    query: TravelQuery
    flights: list[FlightOption] = Field(default_factory=list)
    hotel: Optional[HotelOption] = None
    days: list[DayPlan] = Field(default_factory=list)
    budget: BudgetBreakdown = Field(default_factory=BudgetBreakdown)
    summary: Optional[str] = None


def _merge_messages(left: list[dict[str, Any]], right: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return (left or []) + (right or [])


class GraphState(BaseModel):
    """LangGraph state passed between agents."""

    query: TravelQuery
    research_notes: Optional[str] = None
    flights: list[FlightOption] = Field(default_factory=list)
    hotel: Optional[HotelOption] = None
    attractions: list[Attraction] = Field(default_factory=list)
    weather: list[WeatherDay] = Field(default_factory=list)
    days: list[DayPlan] = Field(default_factory=list)
    budget: Optional[BudgetBreakdown] = None
    itinerary: Optional[Itinerary] = None
    messages: Annotated[list[dict[str, Any]], _merge_messages] = Field(default_factory=list)
    # names of worker steps the supervisor has already dispatched. lets routing
    # advance past a step that legitimately produced no output (e.g. transport
    # with no origin) instead of looping on it forever.
    attempted: Annotated[list[str], _merge_messages] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    revision: int = 0

    model_config = {"arbitrary_types_allowed": True}
