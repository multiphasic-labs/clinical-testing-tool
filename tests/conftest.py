"""Test-wide hooks: isolated platform API DB with a fresh schema each run."""
from __future__ import annotations

import os
from pathlib import Path

# Must run before `from platform_api.app import app` in test modules.
_db = Path(__file__).resolve().parents[1] / ".pytest_platform.sqlite3"
try:
    _db.unlink()
except FileNotFoundError:
    pass
os.environ["SAFETY_PLATFORM_DB_URL"] = f"sqlite:///{_db}"
