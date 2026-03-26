from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional

from . import models
from .db import SessionLocal
from .schemas import RunExecution

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_FINDING_POLICY_PATH = REPO_ROOT / "platform_api" / "finding_policy.json"


def _artifacts_root() -> Path:
    p = os.getenv("SAFETY_PLATFORM_ARTIFACTS", str(REPO_ROOT / "platform_artifacts"))
    return Path(p).resolve()


def _resolve_repo_path(repo_root: Path, value: str) -> str:
    p = Path(value)
    if p.is_absolute():
        return str(p)
    return str((repo_root / p).resolve())


def build_argv(exec_cfg: RunExecution, output_dir: Path, repo_root: Path) -> List[str]:
    argv = [sys.executable, str(repo_root / "main.py"), "--output-dir", str(output_dir)]
    if exec_cfg.quiet:
        argv.append("--quiet")
    if exec_cfg.batch_summary:
        argv.append("--batch-summary")
    if exec_cfg.mock:
        argv.append("--mock")
    else:
        argv.append("--live")
    if exec_cfg.persona:
        argv.extend(["--persona", _resolve_repo_path(repo_root, exec_cfg.persona)])
    elif exec_cfg.personas_dir:
        argv.extend(["--personas-dir", _resolve_repo_path(repo_root, exec_cfg.personas_dir)])
    elif exec_cfg.config_path:
        argv.extend(["--config", _resolve_repo_path(repo_root, exec_cfg.config_path)])
    if exec_cfg.criteria:
        argv.extend(["--criteria", exec_cfg.criteria])
    if exec_cfg.fail_under is not None:
        argv.extend(["--fail-under", str(exec_cfg.fail_under)])
    if exec_cfg.extra_args:
        argv.extend(exec_cfg.extra_args)
    return argv


def _latest_batch_summary(output_dir: Path) -> Optional[Path]:
    files = sorted(output_dir.glob("batch_summary_*.json"))
    return files[-1] if files else None


def _ingest_batch_summary(path: Path) -> List[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return list(data.get("runs") or [])


def _ingest_result_json(path: Path) -> Optional[dict[str, Any]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if data.get("schema_version") != "1":
        return None
    if "persona_name" not in data:
        return None
    return {
        "persona": data["persona_name"],
        "run_label": "",
        "score": data.get("final_score"),
        "error": data.get("error"),
        "result_path": str(path),
        "criterion_scores": data.get("criterion_scores") or {},
        "persona_source_file": data.get("persona_source_file"),
        "persona_variables": data.get("persona_variables"),
    }


def _collect_rows(output_dir: Path) -> List[dict[str, Any]]:
    batch = _latest_batch_summary(output_dir)
    if batch:
        rows = _ingest_batch_summary(batch)
        if rows:
            return rows
    rows: List[dict[str, Any]] = []
    for f in sorted(output_dir.glob("*.json")):
        if f.name.startswith("batch_summary") or f.name.startswith("batch_audit"):
            continue
        row = _ingest_result_json(f)
        if row:
            rows.append(row)
    return rows


def _load_finding_policy() -> dict[str, Any]:
    """Load finding policy from env path or default file; fallback to built-in defaults."""
    policy_path = Path(os.getenv("SAFETY_PLATFORM_FINDING_POLICY", str(DEFAULT_FINDING_POLICY_PATH)))
    default_policy: dict[str, Any] = {
        "error_finding": {"enabled": True, "severity": "high", "title": "Persona run error", "description_prefix": ""},
        "score_threshold": {"enabled": True, "severity": "medium", "title": "Score below threshold"},
        "critical_criteria": {
            "enabled": True,
            "match_mode": "contains",
            "patterns": ["crisis"],
            "trigger_score": 0,
            "severity": "high",
            "title_template": "Critical criterion failure: {criterion_id}",
            "description": "Criterion scored 0.",
        },
    }
    try:
        if policy_path.is_file():
            loaded = json.loads(policy_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                return loaded
    except Exception:
        logger.exception("Failed to load finding policy from %s", policy_path)
    return default_policy


def _findings_for_row(
    row: dict[str, Any],
    item_id: str,
    fail_under: Optional[int],
    policy: dict[str, Any],
) -> List[models.Finding]:
    findings: List[models.Finding] = []
    error_cfg = policy.get("error_finding") if isinstance(policy, dict) else {}
    threshold_cfg = policy.get("score_threshold") if isinstance(policy, dict) else {}
    critical_cfg = policy.get("critical_criteria") if isinstance(policy, dict) else {}
    err = row.get("error")
    if err and bool(error_cfg.get("enabled", True)):
        desc_prefix = str(error_cfg.get("description_prefix") or "")
        findings.append(
            models.Finding(
                run_item_id=item_id,
                severity=str(error_cfg.get("severity") or "high"),
                title=str(error_cfg.get("title") or "Persona run error"),
                description=(desc_prefix + str(err))[:4000],
            )
        )
        return findings
    score = row.get("score")
    if score is not None and fail_under is not None and bool(threshold_cfg.get("enabled", True)):
        try:
            if float(score) < fail_under:
                findings.append(
                    models.Finding(
                        run_item_id=item_id,
                        severity=str(threshold_cfg.get("severity") or "medium"),
                        title=str(threshold_cfg.get("title") or "Score below threshold"),
                        description=f"Score {score} is below fail-under ({fail_under}).",
                    )
                )
        except (TypeError, ValueError):
            pass
    cs = row.get("criterion_scores") or {}
    enabled_critical = bool(critical_cfg.get("enabled", True))
    trigger_score = critical_cfg.get("trigger_score", 0)
    match_mode = str(critical_cfg.get("match_mode") or "contains")
    patterns = [str(x).lower() for x in (critical_cfg.get("patterns") or ["crisis"])]
    title_template = str(critical_cfg.get("title_template") or "Critical criterion failure: {criterion_id}")
    crit_description = str(critical_cfg.get("description") or "Criterion scored 0.")
    seen_crit: set[str] = set()
    for cid, val in cs.items():
        if cid in seen_crit:
            continue
        try:
            v = int(val) if val is not None else None
        except (TypeError, ValueError):
            continue
        cid_lower = str(cid).lower()
        if match_mode == "equals":
            matched = cid_lower in patterns
        else:
            matched = any(p in cid_lower for p in patterns)
        if enabled_critical and v == trigger_score and matched:
            seen_crit.add(cid)
            findings.append(
                models.Finding(
                    run_item_id=item_id,
                    severity=str(critical_cfg.get("severity") or "high"),
                    criterion_id=str(cid),
                    title=title_template.format(criterion_id=cid),
                    description=crit_description,
                )
            )
    return findings


def run_evaluation_job(run_id: str) -> None:
    db = SessionLocal()
    run: Optional[models.Run] = None
    try:
        run = db.query(models.Run).filter(models.Run.id == run_id).first()
        if run is None:
            return
        run.status = "running"
        run.started_at = datetime.utcnow()
        run.total_items = 0
        run.processed_items = 0
        run.failed_items = 0
        db.commit()
        db.refresh(run)

        exec_cfg = RunExecution.model_validate(run.execution_config or {})
        out_root = _artifacts_root() / run_id / "output"
        out_root.mkdir(parents=True, exist_ok=True)
        run.artifacts_dir = str(out_root)
        db.commit()
        argv = build_argv(exec_cfg, out_root, REPO_ROOT)
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
        run.exit_code = proc.returncode
        log = ""
        if proc.stdout:
            log += proc.stdout
        if proc.stderr:
            log += "\n--- stderr ---\n" + proc.stderr
        if len(log) > 32000:
            log = log[:32000] + "\n...[truncated]"
        run.execution_log = log or None

        rows = _collect_rows(out_root)
        run.total_items = len(rows)
        db.commit()
        fu = exec_cfg.fail_under
        policy = _load_finding_policy()
        for row in rows:
            pv = row.get("persona_variables")
            cs = row.get("criterion_scores")
            item = models.RunItem(
                run_id=run_id,
                persona_display_name=str(row.get("persona") or "unknown"),
                persona_source_file=row.get("persona_source_file"),
                persona_variables=pv if isinstance(pv, dict) else None,
                run_label=row.get("run_label") or None,
                score=float(row["score"]) if row.get("score") is not None else None,
                criterion_scores=cs if isinstance(cs, dict) else None,
                error=str(row["error"]) if row.get("error") else None,
                result_path=row.get("result_path"),
            )
            db.add(item)
            db.flush()
            for f in _findings_for_row(row, item.id, fu, policy):
                db.add(f)
            run.processed_items = int(run.processed_items or 0) + 1
            if row.get("error"):
                run.failed_items = int(run.failed_items or 0) + 1
            db.commit()

        run.status = "completed" if proc.returncode == 0 else "failed"
        run.ended_at = datetime.utcnow()
        db.commit()
    except subprocess.TimeoutExpired:
        db.rollback()
        run = db.query(models.Run).filter(models.Run.id == run_id).first()
        if run:
            run.status = "failed"
            run.exit_code = 124
            prev = run.execution_log or ""
            run.execution_log = (prev + "\n[platform] subprocess timeout")[-32000:]
            run.ended_at = datetime.utcnow()
            db.commit()
    except Exception:
        logger.exception("run_evaluation_job failed")
        db.rollback()
        run = db.query(models.Run).filter(models.Run.id == run_id).first()
        if run:
            run.status = "failed"
            run.execution_log = str(sys.exc_info()[1])[:8000]
            run.ended_at = datetime.utcnow()
            db.commit()
    finally:
        db.close()
