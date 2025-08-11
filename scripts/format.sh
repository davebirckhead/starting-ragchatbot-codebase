#!/bin/bash

# Format code script for RAG chatbot codebase
# Format code with Black and sort imports with isort

set -e

echo "📝 Formatting code..."

# Format code with Black
echo "📝 Running Black formatter..."
uv run black backend/ main.py

# Sort imports with isort
echo "📦 Sorting imports with isort..."
uv run isort backend/ main.py

echo "✅ Code formatting completed!"