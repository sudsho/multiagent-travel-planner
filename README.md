# multiagent-travel-planner

multi-agent travel itinerary planner. you give it a vague prompt like
*"plan me 5 days in lisbon late october, mid budget, mostly food and architecture"*
and it returns a fully detailed day-by-day itinerary with flights, a hotel pick,
weather-aware activities and a budget reconciliation.

## why multi-agent

a single LLM call is bad at: keeping track of constraints (budget, dates),
keeping facts current (prices, weather), and producing structured plans.
splitting the work into specialist agents and validating each agent's output
against real APIs gives much better results.

## agents

- `research_agent` parses the user query, fills missing fields
- `transport_agent` looks up flights/trains
- `hotel_agent` picks lodging
- `attractions_agent` picks things to do, clusters by neighborhood
- `weather_agent` pulls forecast, flags rainy days
- `budget_agent` reconciles cost vs target
- `coordinator.supervisor` routes between agents and decides when to stop

## stack

- LangGraph 0.2 for orchestration (state machine + conditional edges)
- LangChain 0.3 for prompt management
- OpenAI / Anthropic providers via a thin abstraction
- FastAPI service
- Streamlit chat UI with day-by-day tabs
- SQLite or Redis cache (TTL keyed per data type)
- real APIs: OpenWeather (forecast), Amadeus or stub (flights),
  hotel API stub, Maps for nearby attractions

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
cp .env.example .env  # fill keys
uvicorn src.api.main:app --reload --port 8000
streamlit run streamlit_app.py
```

or via Make:

```
make install
make api    # uvicorn on :8000
make ui     # streamlit on :8501
make test
make evals
```

## config

profiles in `configs/`. defaults at `configs/default.yaml`,
strict-budget at `configs/budget_strict.yaml`. select via
`PLANNER_PROFILE=budget_strict` env var.

## endpoints

- `POST /plan` — body: `{"query": "5 days lisbon...", "profile": "default"}`
- `GET  /healthz` — liveness
- `GET  /readyz`  — readiness (checks cache + at least one llm key)

## limits

- requests are rate-limited per ip, see `api.rate_limit_per_minute`
- max recursion depth on the graph is 30 (configurable)
- itinerary length capped at 14 days; longer queries get rejected upfront

## testing

`make test` runs unit + integration. integration tests use stub tools so
they don't need real API keys. `make evals` runs three end-to-end
scenarios and prints pass/fail per agent.

## deploy

local docker:

```
cp .env.example .env  # fill keys
docker compose up --build
# api: http://localhost:8000
# ui:  http://localhost:8501
```

production checklist:

- set `PLANNER_PROFILE=production` (uses redis cache, json logs, stricter rate limit)
- supply `OPENAI_API_KEY` (or anthropic) and at least `OPENWEATHER_API_KEY`
- run behind a reverse proxy with TLS; the api itself is plain http
- set `CORS_ALLOW_ORIGINS` to your UI origin(s), not `*`
- scale `WORKERS` to ~2x cpu cores
- mount a persistent volume for the redis service or point at a managed redis

cloud notes are in `_planning/deploy.md`.
