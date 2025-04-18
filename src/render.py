"""itinerary -> markdown rendering."""
from __future__ import annotations

from .state import Itinerary


def render_markdown(it: Itinerary) -> str:
    q = it.query
    lines = [f"# Trip to {q.destination}", ""]
    lines.append(f"_{q.duration_days} days, {q.party_size} traveler(s), {q.start_date} to {q.end_date}_")
    lines.append("")
    if it.summary:
        lines.append(it.summary)
        lines.append("")
    if it.flights:
        f = it.flights[0]
        lines.append(f"**Flight**: {f.carrier}{f.flight_number} {f.depart_iata} -> {f.arrive_iata}, "
                     f"depart {f.depart_at}, {f.duration_minutes}min, {f.stops} stops, {f.price} {f.currency}")
        lines.append("")
    if it.hotel:
        h = it.hotel
        lines.append(f"**Hotel**: {h.name} ({h.rating} stars), {h.price_per_night} {h.currency}/night, {h.address}")
        lines.append("")

    for d in it.days:
        lines.append(f"## Day {d.day_index}, {d.date.isoformat()}")
        if d.weather:
            lines.append(f"_{d.weather.summary}, {d.weather.temp_c_min}-{d.weather.temp_c_max} C, "
                         f"rain {d.weather.precipitation_mm}mm_")
        if d.notes:
            lines.append(f"> {d.notes}")
        for slot in ("morning", "afternoon", "evening"):
            items = getattr(d, slot)
            if not items:
                continue
            lines.append(f"\n**{slot.title()}**")
            for a in items:
                px = f"{a.price:.0f} {it.budget.currency}" if a.price else "free"
                lines.append(f"- {a.name} ({a.duration_hours}h, {px})")
        lines.append(f"\n_estimated day cost: {d.estimated_cost} {it.budget.currency}_")
        lines.append("")

    b = it.budget
    lines.append("## Budget")
    lines.append(f"- transport: {b.transport} {b.currency}")
    lines.append(f"- lodging:   {b.lodging} {b.currency}")
    lines.append(f"- activities:{b.activities} {b.currency}")
    lines.append(f"- food:      {b.food_buffer} {b.currency}")
    lines.append(f"- **total**: {b.total} {b.currency}{' (over budget)' if b.over_budget else ''}")
    return "\n".join(lines)
