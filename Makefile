.PHONY: install dev dev-ui test lint format typecheck clean

install:
	uv sync

dev:
	PYTHONPATH=. uv run python -m uvicorn apps.api.main:app --reload --host 0.0.0.0 --port 8000

dev-ui:
	cd apps/ui && npm install && npm run dev

test:
	uv run pytest -v

lint:
	uv run ruff check .

format:
	uv run ruff format .

typecheck:
	uv run mypy packages apps

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	find . -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
