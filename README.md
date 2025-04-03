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

LangGraph 0.2 for orchestration, LangChain 0.3 for prompt management,
OpenAI / Anthropic providers via a thin abstraction, FastAPI service,
Streamlit chat UI, SQLite/Redis cache.

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
python -m src.api.main  # FastAPI on :8000
streamlit run streamlit_app.py
```

## config

profiles in `configs/`. defaults at `configs/default.yaml`,
strict-budget at `configs/budget_strict.yaml`.

WIP — see `_planning/` for design notes.
