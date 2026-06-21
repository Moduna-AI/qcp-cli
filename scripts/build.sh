#!/usr/bin/env bash
# Clean build: wipes previous output, then builds with uv.
# Usage: ./scripts/build.sh
set -euo pipefail
cd "$(dirname "$0")/.."

./scripts/clean.sh

uv build

echo "Built sdist + wheel into dist/"
ls -la dist/
