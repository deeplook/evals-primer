.DEFAULT_GOAL := help
EXAMPLE ?= examples/01_exact_match.py
LIVE_CORE := examples/04_live_api.py
LOCAL := $(wildcard examples/0[35689]_*.py examples/1[0-9]_*.py examples/2[01]_*.py)
export INSPECT_LOG_DIR := out/inspect-logs
EVALS_LOCAL_MODEL ?= llama3.2:latest
GARAK_VERSION := 0.17.1
GARAK_SPEC ?= probes.promptinject.HijackHateHumans

.PHONY: help install run format lint typecheck test check-all live-core local gate redteam redteam-gate clean

help: ## Show targets
	@grep -E '^[a-zA-Z_-]+:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS=":.*## "}; {printf "  %-12s %s\n", $$1, $$2}'

install: ## Install dependencies
	uv sync --all-groups

run: ## Run one example offline (EXAMPLE=examples/NN_name.py)
	uv run python $(EXAMPLE)

format: ## Format and autofix examples and tests
	uv run ruff format examples tests
	uv run ruff check --fix examples tests

lint: ## Check formatting and linting (no writes)
	uv run ruff format --check examples tests
	uv run ruff check examples tests

typecheck: ## Run strict mypy
	uv run mypy examples tests

test: ## Run offline tests
	uv run python -m pytest -v

check-all: lint typecheck test ## Safe quality gate (what CI runs)

live-core: ## Run the hosted-API lessons against EVALS_MODEL (uses API credits)
	@for example in $(LIVE_CORE); do uv run python $$example --live || exit $$?; done

local: ## Run lessons that can use a local Ollama or llama-server
	@for example in $(LOCAL); do uv run python $$example --local || exit $$?; done

gate: ## Fail when the scripted release candidate misses the thresholds (lesson 21)
	uv run python examples/21_ci_gate.py --gate

redteam: ## Narrow garak scan via uvx against a local Ollama model (lesson 16)
	@mkdir -p out/garak
	@printf 'reporting:\n  report_dir: %s\n' "$(CURDIR)/out/garak" > out/garak/config.yaml
	uvx --from garak==$(GARAK_VERSION) garak --target_type ollama \
		--target_name $(EVALS_LOCAL_MODEL) --spec $(GARAK_SPEC) --generations 1 \
		--report_prefix evals-primer --config out/garak/config.yaml

redteam-gate: redteam ## Scan with garak, then gate on its attack-success rates
	uv run python examples/21_ci_gate.py --gate --garak-report out/garak/evals-primer.report.jsonl

clean: ## Remove caches and generated output
	rm -rf .pytest_cache .ruff_cache .mypy_cache out
	find . -type d -name __pycache__ -not -path './.venv/*' -exec rm -rf {} +
