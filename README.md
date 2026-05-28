# multiagent-travel-planner

design sketch for a multi-agent travel itinerary planner. the intended flow: a
user gives a vague prompt like *"plan me 5 days in lisbon late october, mid
budget, mostly food and architecture"* and specialist agents (research,
transport, hotel, weather, attractions, budget) coordinate through a
supervisor to produce a day-by-day plan.

## status

prototype / scaffold. the graph wiring in `src/graph.py` does not currently
compile: four node names (`hotel`, `weather`, `attractions`, `budget`) collide
with fields on `GraphState`, which the pinned `langgraph==0.2.55` rejects.
POST /plan surfaces the same error as HTTP 500. treat this repo as a reference
for the module layout, agent interfaces and pydantic state schema rather than
a runnable service.

## agents

- `research_agent` parses the user query, fills missing fields
- `transport_agent` looks up flights / trains
- `hotel_agent` picks lodging
- `attractions_agent` picks things to do, clusters by neighborhood
- `weather_agent` pulls forecast, flags rainy days
- `budget_agent` reconciles cost vs target
- `coordinator.supervisor` routes between agents and decides when to stop

## stack

- LangGraph 0.2 for orchestration (state machine + conditional edges)
- OpenAI / Anthropic providers via a thin abstraction in `src/llm.py`
- FastAPI service
- Streamlit chat UI with day-by-day tabs
- SQLite or Redis cache (TTL keyed per data type)
- external APIs: OpenWeather (forecast); flights and hotels use stub tools by
  default

## architecture

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

## quickstart

```
pip install -r requirements.txt
cp .env.example .env  # fill keys if you have them
uvicorn src.api.main:app --reload --port 8000
streamlit run streamlit_app.py
```

note: because the graph currently fails to compile, POST /plan returns HTTP
500. the individual agent modules and stub tools can still be imported and
inspected in isolation.

## endpoints

- `POST /plan` - body: `{"query": "5 days lisbon...", "profile": "default"}`
- `GET  /healthz` - liveness
- `GET  /readyz`  - checks presence of an llm api key, and (only when
  `CACHE_BACKEND=redis`) pings redis

## testing

`pytest -q` runs unit + integration. integration tests use stub tools so they
do not need real API keys. `python -m evals.run_evals` iterates the scenarios
in `evals/scenarios.py` and reports pass/fail per scenario. the eval harness
currently fails against the un-fixed graph.

## deploy

local docker:

```
cp .env.example .env  # fill keys if you have them
docker compose up --build
# api: http://localhost:8000
# ui:  http://localhost:8501
```
