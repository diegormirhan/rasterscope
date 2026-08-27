.PHONY: install test lint train evaluate export frontend run dev

install:
	uv sync --all-extras
	cd frontend && npm ci

test:
	uv run pytest --cov
	cd frontend && npm test -- --run

lint:
	uv run ruff check .
	uv run ruff format --check .
	cd frontend && npm run lint

train:
	uv run rasterscope train --model unet

evaluate:
	uv run rasterscope evaluate

export:
	uv run rasterscope export-onnx

frontend:
	cd frontend && npm run build

run: frontend
	uv run fastapi run --host 127.0.0.1 --port 8000

dev:
	uv run fastapi dev --host 127.0.0.1 --port 8000
