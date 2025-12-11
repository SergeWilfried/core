#!/bin/bash
# Check script - verifies code quality (for CI/CD)

set -e

echo "🔍 Checking code formatting..."
uv run ruff format core/ tests/ --check

echo ""
echo "🔍 Checking code quality..."
uv run ruff check core/ tests/

echo ""
echo "🔍 Running type checks..."
uv run mypy core/

echo ""
echo "🧪 Running tests..."
uv run pytest

echo ""
echo "✅ All checks passed!"
