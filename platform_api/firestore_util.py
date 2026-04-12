from __future__ import annotations

import os
from functools import lru_cache
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from google.cloud.firestore import Client as FirestoreClient


@lru_cache(maxsize=1)
def get_firestore_client() -> "FirestoreClient":
    from google.cloud import firestore

    project = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GCP_PROJECT") or os.getenv("GCLOUD_PROJECT")
    return firestore.Client(project=project) if project else firestore.Client()


def use_firestore() -> bool:
    v = os.getenv("SAFETY_PLATFORM_USE_FIRESTORE", "").strip().lower()
    return v in {"1", "true", "yes", "on"}


def dt_to_iso(obj: Any) -> Any:
    """Convert Firestore datetimes to Python datetime for Pydantic."""
    if obj is None:
        return None
    if hasattr(obj, "isoformat"):
        return obj
    return obj


def doc_to_run_dict(d: dict[str, Any]) -> dict[str, Any]:
    out = dict(d)
    for k in ("created_at", "started_at", "ended_at"):
        if k in out and out[k] is not None:
            v = out[k]
            if hasattr(v, "timestamp"):
                from datetime import datetime, timezone

                out[k] = datetime.fromtimestamp(v.timestamp(), tz=timezone.utc).replace(tzinfo=None)
            elif hasattr(v, "isoformat"):
                pass
    return out


def doc_to_item_dict(d: dict[str, Any]) -> dict[str, Any]:
    out = dict(d)
    if out.get("created_at") is not None:
        v = out["created_at"]
        if hasattr(v, "timestamp"):
            from datetime import datetime, timezone

            out["created_at"] = datetime.fromtimestamp(v.timestamp(), tz=timezone.utc).replace(tzinfo=None)
    return out


def doc_to_finding_dict(d: dict[str, Any]) -> dict[str, Any]:
    out = dict(d)
    if out.get("created_at") is not None:
        v = out["created_at"]
        if hasattr(v, "timestamp"):
            from datetime import datetime, timezone

            out["created_at"] = datetime.fromtimestamp(v.timestamp(), tz=timezone.utc).replace(tzinfo=None)
    return out


def doc_to_baseline_dict(d: dict[str, Any]) -> dict[str, Any]:
    out = dict(d)
    if out.get("created_at") is not None:
        v = out["created_at"]
        if hasattr(v, "timestamp"):
            from datetime import datetime, timezone

            out["created_at"] = datetime.fromtimestamp(v.timestamp(), tz=timezone.utc).replace(tzinfo=None)
    return out
