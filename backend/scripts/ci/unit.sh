#!/usr/bin/env bash
set -e

echo "=== Running Unit Tests ==="
echo ""

cd "$(dirname "$0")/../.."

if ! command -v pytest &> /dev/null; then
    echo "Error: pytest is not installed. Run: pip install -r requirements/local.txt"
    exit 1
fi

export PYTHONPATH="${PYTHONPATH:+${PYTHONPATH}:}$(pwd)/src"
export PYTHONDONTWRITEBYTECODE=1

pytest tests/ \
    --cov=backend \
    --cov-report=term-missing \
    -v

echo ""
echo "✓ All tests passed"
