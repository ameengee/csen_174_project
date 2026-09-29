#!/usr/bin/env bash
set -e

echo "=== Running MyPy Type Checker ==="
echo ""

cd "$(dirname "$0")/../.."

if ! command -v mypy &> /dev/null; then
    echo "Error: mypy is not installed. Run: pip install -r requirements/local.txt"
    exit 1
fi

export PYTHONPATH="${PYTHONPATH:+${PYTHONPATH}:}$(pwd)/src"

mypy src/backend

echo ""
echo "✓ Type checking passed"
