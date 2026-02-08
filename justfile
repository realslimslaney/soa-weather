# SOA Weather — common development tasks

set windows-shell := ["powershell", "-NoProfile", "-Command"]

# List available recipes
default:
    @just --list

# Run the linter
lint:
    uv run ruff check src/ scripts/ tests/

# Auto-format code
format:
    uv run ruff format src/ scripts/ tests/

# Check formatting without modifying files
format-check:
    uv run ruff format --check src/ scripts/ tests/

# Run tests
test:
    uv run pytest

# Run all checks (lint + format check + test)
check: lint format-check test

# Install pre-commit hooks
install-hooks:
    uv run pre-commit install

# Sync dependencies
sync:
    uv sync
