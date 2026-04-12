from __future__ import annotations

"""Unified persistence: SQLAlchemy (default) or Firestore when SAFETY_PLATFORM_USE_FIRESTORE is set."""

from typing import Optional, Tuple

from sqlalchemy.orm import Session

from . import schemas
from .firestore_util import use_firestore


def create_run(db: Optional[Session], payload: schemas.RunCreate) -> schemas.RunOut:
    if use_firestore():
        from . import firestore_service

        return firestore_service.create_run(payload)
    from . import service

    assert db is not None
    return schemas.RunOut.model_validate(service.create_run(db, payload))


def list_runs(db: Optional[Session], limit: int = 50, offset: int = 0) -> list[schemas.RunOut]:
    if use_firestore():
        from . import firestore_service

        return firestore_service.list_runs(limit=limit, offset=offset)
    from . import service

    assert db is not None
    return [schemas.RunOut.model_validate(r) for r in service.list_runs(db, limit=limit, offset=offset)]


def get_run(db: Optional[Session], run_id: str) -> Optional[schemas.RunOut]:
    if use_firestore():
        from . import firestore_service

        return firestore_service.get_run(run_id)
    from . import service

    assert db is not None
    r = service.get_run(db, run_id)
    return schemas.RunOut.model_validate(r) if r is not None else None


def retry_failed_run(db: Optional[Session], run_id: str) -> Tuple[Optional[schemas.RunOut], bool]:
    if use_firestore():
        from . import firestore_service

        return firestore_service.retry_failed_run(run_id)
    from . import service

    a, b = service.retry_failed_run(db, run_id)
    if a is None:
        return None, False
    return schemas.RunOut.model_validate(a), b


def list_run_items(
    db: Optional[Session], run_id: str, limit: int = 200, offset: int = 0
) -> list[schemas.RunItemOut]:
    if use_firestore():
        from . import firestore_service

        return firestore_service.list_run_items(run_id, limit=limit, offset=offset)
    from . import service

    assert db is not None
    return [schemas.RunItemOut.model_validate(x) for x in service.list_run_items(db, run_id=run_id, limit=limit, offset=offset)]


def list_findings(db: Optional[Session], run_id: str, limit: int = 200, offset: int = 0) -> list[schemas.FindingOut]:
    if use_firestore():
        from . import firestore_service

        return firestore_service.list_findings(run_id, limit=limit, offset=offset)
    from . import service

    assert db is not None
    return [schemas.FindingOut.model_validate(x) for x in service.list_findings(db, run_id=run_id, limit=limit, offset=offset)]


def list_run_artifacts(db: Optional[Session], run_id: str) -> list[schemas.ArtifactOut]:
    if use_firestore():
        from . import firestore_service

        return firestore_service.list_run_artifacts(run_id)
    from . import service

    assert db is not None
    return service.list_run_artifacts(db, run_id=run_id)


def create_baseline(db: Optional[Session], payload: schemas.BaselineCreate) -> Optional[schemas.BaselineOut]:
    if use_firestore():
        from . import firestore_service

        return firestore_service.create_baseline(payload)
    from . import service

    assert db is not None
    b = service.create_baseline(db, payload)
    return schemas.BaselineOut.model_validate(b) if b is not None else None


def list_baselines(db: Optional[Session], limit: int = 100, offset: int = 0) -> list[schemas.BaselineOut]:
    if use_firestore():
        from . import firestore_service

        return firestore_service.list_baselines(limit=limit, offset=offset)
    from . import service

    assert db is not None
    return [schemas.BaselineOut.model_validate(x) for x in service.list_baselines(db, limit=limit, offset=offset)]


def get_run_diff(db: Optional[Session], run_id: str, against: str) -> Optional[schemas.RunDiffOut]:
    if use_firestore():
        from . import firestore_service

        return firestore_service.get_run_diff(run_id, against)
    from . import service

    assert db is not None
    return service.get_run_diff(db, run_id=run_id, against=against)


def evaluate_release_gate(db: Optional[Session], run_id: str, against: str) -> Optional[schemas.RunGateOut]:
    if use_firestore():
        from . import firestore_service

        return firestore_service.evaluate_release_gate(run_id, against)
    from . import service

    assert db is not None
    return service.evaluate_release_gate(db, run_id=run_id, against=against)
