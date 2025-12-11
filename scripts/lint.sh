#!/bin/bash
# Lint script - checks code quality without making changes

set -e

echo "🔍 Running Ruff linter..."
uv run ruff check core/ tests/

echo ""
echo "🔍 Running mypy type checker..."
uv run mypy core/

echo ""
echo "✅ Linting complete!"
