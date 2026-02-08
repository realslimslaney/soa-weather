# SOA Weather — common development tasks

# List available recipes
default:
    @just --list

# Run the linter
lint:
    uv run ruff check src/ scripts/

# Auto-format code
format:
    uv run ruff format src/ scripts/

# Check formatting without modifying files
format-check:
    uv run ruff format --check src/ scripts/

# Run tests
test:
    uv run pytest

# Run all checks (lint + format check + test)
check: lint format-check test

# Sync dependencies
sync:
    uv sync
