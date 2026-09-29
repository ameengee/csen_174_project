#!/usr/bin/env bash
set -e

echo "=== Running Ruff Linter ==="
echo ""

cd "$(dirname "$0")/../.."

if ! command -v ruff &> /dev/null; then
    echo "Error: ruff is not installed. Run: pip install -r requirements/local.txt"
    exit 1
fi

export PYTHONPATH="${PYTHONPATH:+${PYTHONPATH}:}$(pwd)/src"

ruff check src/ tests/ --fix

echo ""
echo "✓ Linting passed"
