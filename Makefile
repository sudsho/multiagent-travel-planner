.PHONY: install smoke test lint fmt run api ui evals docker

install:
	pip install -r requirements.txt

smoke:
	python scripts/smoke.py

test:
	pytest -q

lint:
	python -m pyflakes src tests || true

run:
	python -m src.cli "5 days lisbon, food, 1500 usd" --no-llm

api:
	uvicorn src.api.main:app --reload --port 8000

ui:
	streamlit run streamlit_app.py

evals:
	python -m evals.run_evals

docker:
	docker compose up --build
