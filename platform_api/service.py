from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from . import models, schemas


def _execution_config_snapshot(payload: schemas.RunCreate) -> Optional[dict]:
    if payload.execute:
        return (payload.execution or schemas.RunExecution()).model_dump()
    if payload.execution is not None:
        return payload.execution.model_dump()
    return None


def create_run(db: Session, payload: schemas.RunCreate) -> models.Run:
    run = models.Run(
        trigger_type=payload.trigger_type,
        model_name=payload.model_name,
        prompt_version=payload.prompt_version,
        scenario_set=payload.scenario_set,
        config_hash=payload.config_hash,
        status="queued",
        execution_config=_execution_config_snapshot(payload),
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def list_runs(db: Session, limit: int = 50, offset: int = 0) -> list[models.Run]:
    return (
        db.query(models.Run)
        .order_by(models.Run.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


def get_run(db: Session, run_id: str) -> Optional[models.Run]:
    return db.query(models.Run).filter(models.Run.id == run_id).first()


def retry_failed_run(db: Session, run_id: str) -> Tuple[Optional[models.Run], bool]:
    """Create a follow-up run. If the source run has execution_config, re-queue execution."""
    old = get_run(db, run_id)
    if old is None:
        return None, False
    if old.execution_config:
        payload = schemas.RunCreate(
            trigger_type="manual",
            model_name=old.model_name,
            prompt_version=old.prompt_version,
            scenario_set=old.scenario_set,
            config_hash=old.config_hash,
            execute=True,
            execution=schemas.RunExecution.model_validate(old.execution_config),
        )
        return create_run(db, payload), True
    payload = schemas.RunCreate(
        trigger_type="manual",
        model_name=old.model_name,
        prompt_version=old.prompt_version,
        scenario_set=old.scenario_set,
        config_hash=old.config_hash,
        execute=False,
    )
    return create_run(db, payload), False


def list_run_items(db: Session, run_id: str, limit: int = 200, offset: int = 0) -> list[models.RunItem]:
    return (
        db.query(models.RunItem)
        .filter(models.RunItem.run_id == run_id)
        .order_by(models.RunItem.created_at.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )


def list_findings(db: Session, run_id: str, limit: int = 200, offset: int = 0) -> list[models.Finding]:
    return (
        db.query(models.Finding)
        .join(models.RunItem, models.Finding.run_item_id == models.RunItem.id)
        .filter(models.RunItem.run_id == run_id)
        .order_by(models.Finding.created_at.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )


def list_run_artifacts(db: Session, run_id: str) -> list[schemas.ArtifactOut]:
    run = get_run(db, run_id)
    if run is None or not run.artifacts_dir:
        return []
    out_dir = Path(run.artifacts_dir)
    if not out_dir.exists() or not out_dir.is_dir():
        return []

    artifacts: list[schemas.ArtifactOut] = []
    for p in sorted(out_dir.rglob("*")):
        if not p.is_file():
            continue
        suffix = p.suffix.lower()
        if suffix == ".json":
            ftype = "json"
        elif suffix == ".md":
            ftype = "markdown"
        elif suffix == ".csv":
            ftype = "csv"
        elif suffix == ".html":
            ftype = "html"
        elif suffix in {".log", ".txt"}:
            ftype = "text"
        else:
            ftype = "file"

        stat = p.stat()
        artifacts.append(
            schemas.ArtifactOut(
                path=str(p),
                name=p.name,
                type=ftype,
                size_bytes=int(stat.st_size),
                modified_at=datetime.fromtimestamp(stat.st_mtime),
            )
        )
    return artifacts

