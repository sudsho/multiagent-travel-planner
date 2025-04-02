"""agent registry. each agent is a node in the LangGraph state machine."""
from .research import research_agent
from .transport import transport_agent
from .hotel import hotel_agent
from .attractions import attractions_agent
from .weather import weather_agent
from .budget import budget_agent
from .coordinator import supervisor

__all__ = [
    "research_agent",
    "transport_agent",
    "hotel_agent",
    "attractions_agent",
    "weather_agent",
    "budget_agent",
    "supervisor",
]
