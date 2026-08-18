SHELL := /bin/bash
PYTHON ?= python3
VENV ?= .venv
BIN := $(VENV)/bin

.PHONY: bootstrap install install-openai doctor demo validate test lint format format-check typecheck check schemas build pre-commit clean

bootstrap:
	$(PYTHON) -m venv $(VENV)
	$(BIN)/python -m pip install --upgrade pip
	$(BIN)/pip install -e ".[dev]"

install:
	$(PYTHON) -m pip install -e .

install-openai:
	$(PYTHON) -m pip install -e ".[openai]"

doctor:
	$(PYTHON) -m endurance_agent_lab doctor

demo:
	$(PYTHON) -m endurance_agent_lab demo --clean

validate:
	$(PYTHON) -m endurance_agent_lab validate

test:
	pytest --cov=endurance_agent_lab --cov-report=term-missing

lint:
	ruff check .

format:
	ruff check --fix .
	ruff format .

format-check:
	ruff format --check .

typecheck:
	mypy src/endurance_agent_lab

check: validate test format-check lint typecheck

schemas:
	$(PYTHON) -m endurance_agent_lab schema export --output schemas

build:
	$(PYTHON) -m build

pre-commit:
	pre-commit run --all-files

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage runs build dist *.egg-info src/*.egg-info
