#!/usr/bin/env bash
# Clean build: wipes any previous venv/build output, then builds a fresh
# sdist + wheel into dist/ from a brand-new virtualenv.
# Usage: ./scripts/build.sh
set -euo pipefail
cd "$(dirname "$0")/.."

./scripts/clean.sh

PYTHON="${PYTHON:-python3}"
"$PYTHON" -m venv .venv
.venv/bin/pip install --upgrade pip build --quiet
.venv/bin/python -m build

echo "✔ Built sdist + wheel into dist/"
ls -la dist/
