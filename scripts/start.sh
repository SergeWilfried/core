#!/bin/bash

# BaaS Core Banking - Quick Start Script

set -e

echo "🏦 BaaS Core Banking - Quick Start"
echo "=================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Creating from .env.example..."
    cp .env.example .env
    echo "✅ Created .env file. Please update it with your Formance credentials."
    echo ""
fi

# Install dependencies
echo "📦 Installing dependencies..."
uv sync
echo "✅ Dependencies installed"
echo ""

# Run the API server
echo "🚀 Starting API server..."
echo "   API: http://localhost:8000"
echo "   Docs: http://localhost:8000/docs"
echo ""

uvicorn core.api.app:app --reload --port 8000
