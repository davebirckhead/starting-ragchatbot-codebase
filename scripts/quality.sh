#!/bin/bash

# Quality check script for RAG chatbot codebase
# Run all code quality tools

set -e

echo "🔍 Running code quality checks..."

# Format code with Black
echo "📝 Formatting code with Black..."
uv run black backend/ main.py

# Sort imports with isort
echo "📦 Sorting imports with isort..."
uv run isort backend/ main.py

# Run flake8 linting
echo "🔍 Running flake8 linting..."
uv run flake8 backend/ main.py

# Run mypy type checking
echo "🔍 Running mypy type checking..."
uv run mypy backend/ main.py

echo "✅ All quality checks completed!"