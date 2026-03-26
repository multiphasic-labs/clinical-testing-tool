from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class Run(Base):
    __tablename__ = "runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    status: Mapped[str] = mapped_column(String(32), default="queued", index=True)
    trigger_type: Mapped[str] = mapped_column(String(32), default="manual")
    model_name: Mapped[str] = mapped_column(String(128), default="unknown")
    prompt_version: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    scenario_set: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    config_hash: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    execution_config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    exit_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    execution_log: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    artifacts_dir: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    total_items: Mapped[int] = mapped_column(Integer, default=0)
    processed_items: Mapped[int] = mapped_column(Integer, default=0)
    failed_items: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    items: Mapped[list["RunItem"]] = relationship("RunItem", back_populates="run", cascade="all, delete-orphan")


class RunItem(Base):
    __tablename__ = "run_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id: Mapped[str] = mapped_column(String(36), ForeignKey("runs.id"), index=True)
    persona_display_name: Mapped[str] = mapped_column(String(256), index=True)
    persona_source_file: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    persona_variables: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    run_label: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    criterion_scores: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    result_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    run: Mapped[Run] = relationship("Run", back_populates="items")
    findings: Mapped[list["Finding"]] = relationship("Finding", back_populates="item", cascade="all, delete-orphan")


class Finding(Base):
    __tablename__ = "findings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_item_id: Mapped[str] = mapped_column(String(36), ForeignKey("run_items.id"), index=True)
    severity: Mapped[str] = mapped_column(String(24), default="medium")
    criterion_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    title: Mapped[str] = mapped_column(String(256))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(24), default="new")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    item: Mapped[RunItem] = relationship("RunItem", back_populates="findings")

