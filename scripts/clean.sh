#!/usr/bin/env bash
# Removes venv, build artifacts, and caches for a totally clean tree.
# Usage: ./scripts/clean.sh
set -euo pipefail
cd "$(dirname "$0")/.."

rm -rf .venv build dist *.egg-info qcp.egg-info .pytest_cache .mypy_cache .ruff_cache
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

echo "✔ Cleaned (.venv, build/, dist/, caches)"
