from __future__ import annotations

import logging
import subprocess
import sys
import uuid
from datetime import datetime
from typing import Any

from . import firestore_service
from .firestore_util import get_firestore_client
from .schemas import RunExecution
from .worker import (
    REPO_ROOT,
    _artifacts_root,
    _collect_rows,
    _findings_for_row,
    _load_finding_policy,
    build_argv,
)

logger = logging.getLogger(__name__)


def _finding_to_dict(f: Any) -> dict[str, Any]:
    return {
        "run_item_id": f.run_item_id,
        "severity": f.severity,
        "criterion_id": f.criterion_id,
        "title": f.title,
        "description": f.description,
        "status": f.status,
        "created_at": getattr(f, "created_at", None) or datetime.utcnow(),
    }


def run_evaluation_job(run_id: str) -> None:
    run_out = firestore_service.get_run(run_id)
    if run_out is None:
        return

    try:
        firestore_service.patch_run(
            run_id,
            status="running",
            started_at=datetime.utcnow(),
            total_items=0,
            processed_items=0,
            failed_items=0,
        )

        exec_cfg = RunExecution.model_validate(run_out.execution_config or {})
        out_root = _artifacts_root() / run_id / "output"
        out_root.mkdir(parents=True, exist_ok=True)
        firestore_service.patch_run(run_id, artifacts_dir=str(out_root))

        argv = build_argv(exec_cfg, out_root, REPO_ROOT)
        import os

        env = os.environ.copy()
        if exec_cfg.mock:
            env["SAFETY_TESTER_MOCK"] = "1"
        else:
            env.pop("SAFETY_TESTER_MOCK", None)

        proc = subprocess.run(
            argv,
            cwd=str(REPO_ROOT),
            env=env,
            capture_output=True,
            text=True,
            timeout=exec_cfg.timeout_seconds,
        )

        log = ""
        if proc.stdout:
            log += proc.stdout
        if proc.stderr:
            log += "\n--- stderr ---\n" + proc.stderr
        if len(log) > 32000:
            log = log[:32000] + "\n...[truncated]"

        firestore_service.patch_run(
            run_id,
            exit_code=proc.returncode,
            execution_log=log or None,
        )

        rows = _collect_rows(out_root)
        firestore_service.patch_run(run_id, total_items=len(rows))

        fu = exec_cfg.fail_under
        policy = _load_finding_policy()
        run_ref = get_firestore_client().collection("runs").document(run_id)

        processed = 0
        failed = 0
        for row in rows:
            pv = row.get("persona_variables")
            cs = row.get("criterion_scores")
            item_id = str(uuid.uuid4())
            now = datetime.utcnow()
            item_doc = {
                "run_id": run_id,
                "persona_display_name": str(row.get("persona") or "unknown"),
                "persona_source_file": row.get("persona_source_file"),
                "persona_variables": pv if isinstance(pv, dict) else None,
                "run_label": row.get("run_label") or None,
                "score": float(row["score"]) if row.get("score") is not None else None,
                "criterion_scores": cs if isinstance(cs, dict) else None,
                "error": str(row["error"]) if row.get("error") else None,
                "result_path": row.get("result_path"),
                "created_at": now,
            }
            run_ref.collection("items").document(item_id).set(item_doc)

            for f in _findings_for_row(row, item_id, fu, policy):
                fd = _finding_to_dict(f)
                fid = str(uuid.uuid4())
                fd["created_at"] = fd.get("created_at") or datetime.utcnow()
                run_ref.collection("findings").document(fid).set(fd)

            processed += 1
            if row.get("error"):
                failed += 1
            firestore_service.patch_run(run_id, processed_items=processed, failed_items=failed)

        firestore_service.patch_run(
            run_id,
            status="completed" if proc.returncode == 0 else "failed",
            ended_at=datetime.utcnow(),
        )
    except subprocess.TimeoutExpired:
        prev = firestore_service.get_run(run_id)
        prev_log = (prev.execution_log or "") if prev else ""
        firestore_service.patch_run(
            run_id,
            status="failed",
            exit_code=124,
            execution_log=(prev_log + "\n[platform] subprocess timeout")[-32000:],
            ended_at=datetime.utcnow(),
        )
    except Exception:
        logger.exception("run_evaluation_job (firestore) failed")
        firestore_service.patch_run(
            run_id,
            status="failed",
            execution_log=str(sys.exc_info()[1])[:8000],
            ended_at=datetime.utcnow(),
        )
