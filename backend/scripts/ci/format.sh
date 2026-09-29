#!/usr/bin/env bash
set -e

echo "=== Running Black Formatter ==="
echo ""

cd "$(dirname "$0")/../.."

if ! command -v black &> /dev/null; then
    echo "Error: black is not installed. Run: pip install -r requirements/local.txt"
    exit 1
fi

export PYTHONPATH="${PYTHONPATH:+${PYTHONPATH}:}$(pwd)/src"

black src/ tests/ --line-length 100

echo ""
echo "✓ Formatting complete"
