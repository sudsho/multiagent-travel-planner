"""3 evaluation scenarios with expected qualities. these are not strict tests,
they're qualitative checks: 'does the itinerary look reasonable for this prompt?'"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Scenario:
    name: str
    prompt: str
    expected: dict


SCENARIOS = [
    Scenario(
        name="lisbon-foodie-5d",
        prompt="plan me 5 days in lisbon late october 2025, mid budget around 1500 USD, mostly food and architecture, 2 people from new york",
        expected={
            "destination": "lisbon",
            "duration_days": 5,
            "min_food_attractions": 3,
            "budget_under_usd": 1700,  # +/- food/lodging variance
        },
    ),
    Scenario(
        name="tokyo-anime-3d-tight",
        prompt="3 days in tokyo, solo traveler from sf, tight budget under 1200 usd, anime + food",
        expected={
            "destination": "tokyo",
            "duration_days": 3,
            "min_attractions_total": 6,
            "budget_under_usd": 1300,
        },
    ),
    Scenario(
        name="paris-relaxed-7d-rainy",
        prompt="7 day relaxed trip to paris early november, 2 travelers from london, museums and cafes",
        expected={
            "destination": "paris",
            "duration_days": 7,
            "min_indoor_share": 0.4,
            "pace": "relaxed",
        },
    ),
]
