from __future__ import annotations

import logging
import os
from pathlib import Path

from alembic import command
from alembic.config import Config

logger = logging.getLogger(__name__)


def run_migrations() -> None:
    """Apply Alembic migrations; `SAFETY_PLATFORM_DB_URL` must match `platform_api.db`."""
    if os.getenv("SAFETY_PLATFORM_SKIP_MIGRATIONS", "").lower() in {"1", "true", "yes"}:
        return
    repo_root = Path(__file__).resolve().parent.parent
    ini_path = repo_root / "alembic.ini"
    if not ini_path.is_file():
        logger.warning("alembic.ini not found at %s; skipping migrations", ini_path)
        return
    cfg = Config(str(ini_path))
    command.upgrade(cfg, "head")
