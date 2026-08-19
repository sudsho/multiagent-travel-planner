# multiagent-travel-planner

A multi-agent travel itinerary planner. You give a vague prompt like *"plan me 5
days in lisbon late october, mid budget, mostly food and architecture"* and a
set of specialist agents (research, transport, hotel, weather, attractions,
budget) coordinate through a supervisor to produce a day-by-day plan with a
reconciled budget.

Orchestration is a LangGraph state machine: a supervisor node routes to one
worker at a time and each worker returns to the supervisor for the next
decision, until the plan is finalized.

## Quick start (runs offline, no keys)

No API keys, no network, no downloads. A deterministic mock LLM stands in for
OpenAI/Anthropic and every travel tool uses bundled stub/sample data.

```
pip install -r requirements.txt
python scripts/smoke.py      # or: make smoke
```

Real output (trimmed):

```
======================================================================
multiagent-travel-planner : OFFLINE SMOKE
======================================================================
LLM        : MockLLM (deterministic, no keys)
tools      : bundled stubs (no external API calls)
request    : plan me 5 days in lisbon late october 2025, mid budget around 1500 USD, mostly food and architecture, 2 people from new york
----------------------------------------------------------------------
AGENT / TOOL TRACE
  [01] supervisor            -> route: research
  [02] research_node        -> MockLLM.complete (research role)
        parsed dest=lisbon origin=new york 5d party=2 budget=1500.0
  [03] supervisor            -> route: transport
  [04] transport_node       -> tools.transport_api.search_flights (stub)
        3 flight option(s), best VY2138 318 USD
  [05] supervisor            -> route: hotel
  [06] hotel_node           -> tools.hotel_api.search_hotels (stub)
        picked Lisbon Budget Inn @ 143 USD/night
  [07] supervisor            -> route: weather
  [08] weather_node         -> tools.openweather.get_forecast (stub)
        5 day forecast
  [09] supervisor            -> route: attractions
  [10] attractions_node     -> tools.maps.nearby_attractions (sample_destinations.json)
        14 candidate attraction(s)
  [11] supervisor            -> route: schedule
  [12] schedule_node        -> scheduler.schedule_days (local)
        5 day plan(s) scheduled
  [13] supervisor            -> route: budget
  [14] budget_node          -> agents.budget (local reconcile)
        total 1709 USD (over_budget=True)
  [15] supervisor            -> route: finalize
  [16] finalize_node        -> MockLLM.complete (summary role)
        itinerary finalized + summarized
----------------------------------------------------------------------
STRUCTURED ITINERARY
# Trip to lisbon

_5 days, 2 traveler(s), 2025-10-22 to 2025-10-26_

A 5-day trip to Lisbon for 2 traveler(s), built around Alfama walking tour,
Pasteis de Belem, Miradouro da Graca. Estimated all-in cost is about 1709 USD.

**Flight**: VY2138 JFK -> LIS, depart 2025-10-22T08:25, 195min, 0 stops, 318.0 USD
**Hotel**: Lisbon Budget Inn (3.6 stars), 143.0 USD/night, Old Town 7, Lisbon

## Day 1, 2025-10-22
...
## Budget
- transport: 636.0 USD
- lodging:   715.0 USD
- activities:8.0 USD
- food:      350.0 USD
- **total**: 1709.0 USD (over budget)
----------------------------------------------------------------------
INVARIANTS
  [PASS] destination parsed   ... [PASS] llm invoked   (10/10)
SMOKE OK - 5-day itinerary, budget 1709 USD, 2 LLM calls, no network.
```

The result above is deterministic (stable across runs and `PYTHONHASHSEED`). In
this sample the fixed costs (flights + lodging + food) already exceed the 1500
USD target, so the budget agent trims discretionary activities and flags the
plan as over budget. That is the reconciliation loop doing real work, not an
error.

## What runs offline vs what a real backend adds

The offline mode is a first-class fallback, not a stub-out of the logic. The
same supervisor, agents, scheduler and budget reconciler run in both modes. Only
the "outside world" pieces are swapped:

| Piece | Offline default (no keys) | With real backend |
|---|---|---|
| LLM | `MockLLM`: rule-based per role (research JSON, trip summary) | OpenAI / Anthropic via `src/llm.py` for free-form parsing and prose |
| Flights | deterministic stub in `tools/transport_api.py` | Amadeus Flight Offers (`AMADEUS_CLIENT_ID/SECRET`) |
| Hotels | deterministic stub in `tools/hotel_api.py` | Amadeus Hotel Search |
| Weather | deterministic stub in `tools/openweather.py` | OpenWeather forecast (`OPENWEATHER_API_KEY`) |
| Attractions | `data/sample_destinations.json` | Google Maps Places (`GOOGLE_MAPS_API_KEY`) |
| Cache | SQLite file | Redis (`CACHE_BACKEND=redis`) |

A real LLM improves query understanding (dates like "late october", fuzzy
interests, multi-city trips) and writes a richer summary. Real APIs give live
prices, availability and geocoded attractions so the scheduler can cluster by
actual location. To use them, set the keys in `.env` (see `.env.example`) and
pass a real provider, e.g. `LLM_PROVIDER=openai python -m src.cli "..."`.

## CLI

```
# offline heuristic parser (no LLM at all)
python -m src.cli "5 days lisbon, food, 1500 usd" --no-llm

# deterministic mock LLM in the loop
LLM_PROVIDER=mock python -m src.cli "5 days lisbon late october, food, from nyc"

# JSON instead of markdown
python -m src.cli "3 days tokyo, anime, from sf" --no-llm --format json
```

## Agents

- `research_agent` parses the user query and fills missing fields
- `transport_agent` looks up flights (needs an origin)
- `hotel_agent` picks lodging within a per-night budget target
- `attractions_agent` pulls candidate things to do
- `weather_agent` builds a per-day forecast, flags rainy days
- `scheduler` clusters attractions into morning/afternoon/evening slots,
  weather-aware
- `budget_agent` reconciles total cost against the target and trims if over
- `coordinator.supervisor` routes between agents and decides when to stop

## Architecture

```
        +-----------+
        | streamlit |
        +-----+-----+
              |
              v
        +-----+-----+
        | fastapi   |
        +-----+-----+
              |
              v   +---------------+
       +------+---|  supervisor   |---+
       |          +---------------+   |
       v                              v
   research                       budget
       |                              ^
       v                              |
   transport / hotel / weather / attractions
       |
       v
   day scheduler --> itinerary
```

## Testing

```
pytest -q                 # 53 unit + integration tests, offline, no keys
python -m evals.run_evals # 3 end-to-end scenarios with quality checks
```

Integration tests and evals use the stub tools and the no-LLM / mock-LLM paths,
so they need no real API keys.

## Endpoints

- `POST /plan` - body: `{"query": "5 days lisbon...", "profile": "default"}`
- `GET  /healthz` - liveness
- `GET  /readyz`  - checks presence of an llm api key, and (only when
  `CACHE_BACKEND=redis`) pings redis

Note: the FastAPI `/plan` route builds a real provider via `llm_from_env()`, so
run it with `LLM_PROVIDER=mock` to serve requests without keys.

## Deploy

Local docker:

```
cp .env.example .env  # fill keys if you have them
docker compose up --build
# api: http://localhost:8000
# ui:  http://localhost:8501
```
