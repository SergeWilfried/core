#!/bin/bash
# Format script - automatically fixes code formatting

set -e

echo "🎨 Running Ruff formatter..."
uv run ruff format core/ tests/

echo ""
echo "🔧 Running Ruff auto-fix..."
uv run ruff check core/ tests/ --fix

echo ""
echo "✅ Formatting complete!"
