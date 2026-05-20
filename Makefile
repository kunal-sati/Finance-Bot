# ── Trading Bot Makefile ─────────────────────────────────────────────
# Usage:
#   make install   — Install dependencies
#   make run       — Run the bot (pass ARGS="...")
#   make test      — Run unit tests
#   make lint      — Run linter
#   make fmt       — Auto-format code
#   make docker    — Build Docker image
#   make clean     — Remove caches and build artifacts
# ─────────────────────────────────────────────────────────────────────

.PHONY: install run test lint fmt docker clean help

PYTHON ?= python3
PIP ?= pip3
ARGS ?=

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install project dependencies
	$(PIP) install -r requirements.txt

install-dev: ## Install with dev dependencies
	$(PIP) install -r requirements.txt
	$(PIP) install -e ".[dev]"

run: ## Run the trading bot (use ARGS="--symbol BTCUSDT ...")
	$(PYTHON) -m bot.cli.main $(ARGS)

test: ## Run all unit tests
	$(PYTHON) -m pytest tests/ -v --tb=short

test-cov: ## Run tests with coverage report
	$(PYTHON) -m pytest tests/ -v --cov=bot --cov-report=term-missing

lint: ## Lint with ruff
	$(PYTHON) -m ruff check bot/ tests/

fmt: ## Auto-format with ruff
	$(PYTHON) -m ruff format bot/ tests/
	$(PYTHON) -m ruff check --fix bot/ tests/

docker: ## Build Docker image
	docker build -t trading-bot:latest .

docker-run: ## Run in Docker (use ARGS="...")
	docker run --rm --env-file .env trading-bot:latest $(ARGS)

clean: ## Remove caches and build artifacts
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ htmlcov/ .coverage
