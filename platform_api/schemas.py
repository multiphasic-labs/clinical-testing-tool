from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class RunExecution(BaseModel):
    """CLI-equivalent options passed to `main.py` for this run (stored on the Run for retries)."""

    mock: bool = True
    batch_summary: bool = True
    quiet: bool = True
    config_path: Optional[str] = "personas/batch_config.json"
    personas_dir: Optional[str] = None
    persona: Optional[str] = None
    criteria: Optional[str] = None
    fail_under: Optional[int] = 2
    extra_args: Optional[list[str]] = None
    timeout_seconds: int = 7200


class RunCreate(BaseModel):
    trigger_type: Literal["manual", "schedule", "release_gate"] = "manual"
    model_name: str = "unknown"
    prompt_version: Optional[str] = None
    scenario_set: Optional[str] = None
    config_hash: Optional[str] = None
    execute: bool = False
    execution: Optional[RunExecution] = None


class RunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    status: str
    trigger_type: str
    model_name: str
    prompt_version: Optional[str]
    scenario_set: Optional[str]
    config_hash: Optional[str]
    execution_config: Optional[dict[str, Any]] = None
    exit_code: Optional[int] = None
    execution_log: Optional[str] = None
    artifacts_dir: Optional[str] = None
    total_items: int = 0
    processed_items: int = 0
    failed_items: int = 0
    created_at: datetime
    started_at: Optional[datetime]
    ended_at: Optional[datetime]


class RunItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    run_id: str
    persona_display_name: str
    persona_source_file: Optional[str]
    persona_variables: Optional[dict[str, Any]]
    run_label: Optional[str]
    score: Optional[float]
    criterion_scores: Optional[dict[str, Any]]
    error: Optional[str]
    result_path: Optional[str]
    created_at: datetime


class FindingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    run_item_id: str
    severity: str
    criterion_id: Optional[str]
    title: str
    description: Optional[str]
    status: str
    created_at: datetime


class HealthOut(BaseModel):
    status: str = Field(default="ok")


class ArtifactOut(BaseModel):
    path: str
    name: str
    type: str
    size_bytes: int
    modified_at: datetime

