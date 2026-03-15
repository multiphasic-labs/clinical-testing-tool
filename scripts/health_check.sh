#!/usr/bin/env bash
# Health check: run one mock persona and exit 0 if the pipeline works. For deploy verification.
# Usage: bash scripts/health_check.sh   or   python3 main.py --health-check
set -e
cd "$(dirname "$0")/.."
export SAFETY_TESTER_MOCK=1
python3 main.py --health-check
