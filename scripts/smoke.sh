#!/usr/bin/env bash
# Smoke test: run one persona in mock mode and assert exit 0 and score >= 2.
# Usage: from repo root, ./scripts/smoke.sh   or   bash scripts/smoke.sh
set -e
cd "$(dirname "$0")/.."
export SAFETY_TESTER_MOCK=1
out=$(python3 main.py --persona passive_ideation.json --mock --quiet --fail-under 2 2>&1)
code=$?
if [ "$code" -ne 0 ]; then
  echo "Smoke test failed: exit code $code"
  echo "$out"
  exit 1
fi
if ! echo "$out" | grep -q "score=2"; then
  echo "Smoke test failed: expected score=2 in output"
  echo "$out"
  exit 1
fi
echo "Smoke test passed."
