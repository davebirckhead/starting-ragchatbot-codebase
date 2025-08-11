#!/bin/bash

# Linting script for RAG chatbot codebase
# Run linting checks without formatting

set -e

echo "🔍 Running linting checks..."

# Run flake8 linting
echo "🔍 Running flake8 linting..."
uv run flake8 backend/ main.py

# Run mypy type checking
echo "🔍 Running mypy type checking..."
uv run mypy backend/ main.py

echo "✅ Linting checks completed!"