"""
OmniSight — SQLAlchemy ORM Models
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Defines the database schema for storing scan runs and detected bugs.
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, Column, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from backend.db.database import Base
from backend.models.schemas import BugCategory, BugSeverity, ScanStatus


class ScanRunModel(Base):
    """SQLAlchemy model for a UI scan run."""

    __tablename__ = "scan_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)
    url: Mapped[str] = mapped_column(String, index=True)
    status: Mapped[ScanStatus] = mapped_column(Enum(ScanStatus))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    total_bugs: Mapped[int] = mapped_column(Integer, default=0)
    pr_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    # Relationship to bugs
    bugs: Mapped[List["BugModel"]] = relationship(
        "BugModel", back_populates="scan_run", cascade="all, delete-orphan"
    )
    # Relationship to PR history
    pr_records: Mapped[List["PullRequestHistoryModel"]] = relationship(
        "PullRequestHistoryModel", back_populates="scan_run", cascade="all, delete-orphan"
    )


class BugModel(Base):
    """SQLAlchemy model for a detected UI bug."""

    __tablename__ = "bugs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)
    scan_run_id: Mapped[str] = mapped_column(String(36), ForeignKey("scan_runs.id"), index=True)
    category: Mapped[BugCategory] = mapped_column(Enum(BugCategory))
    severity: Mapped[BugSeverity] = mapped_column(Enum(BugSeverity))
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    element_selector: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    viewport: Mapped[str] = mapped_column(String)
    screenshot_path: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    suggested_fix: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    confidence: Mapped[float] = mapped_column(Float)
    verification_status: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    verification_screenshot_path: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Relationships
    scan_run: Mapped["ScanRunModel"] = relationship("ScanRunModel", back_populates="bugs")
    remediations: Mapped[List["RemediationActionModel"]] = relationship(
        "RemediationActionModel", back_populates="bug", cascade="all, delete-orphan"
    )


class RemediationActionModel(Base):
    """SQLAlchemy model for autonomous code remediation actions (Day 4 Architecture)."""

    __tablename__ = "remediation_actions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)
    bug_id: Mapped[str] = mapped_column(String(36), ForeignKey("bugs.id"), index=True)
    patch_type: Mapped[str] = mapped_column(String(50), default="css_override")
    patch_content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())
    is_verified: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationship to bug
    bug: Mapped["BugModel"] = relationship("BugModel", back_populates="remediations")


class PullRequestHistoryModel(Base):
    """SQLAlchemy model for tracking autonomous Pull Request publications (Day 4 Architecture)."""

    __tablename__ = "pull_request_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)
    scan_run_id: Mapped[str] = mapped_column(String(36), ForeignKey("scan_runs.id"), index=True)
    pr_url: Mapped[str] = mapped_column(String)
    pr_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    branch_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    target_repo: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="open")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())

    # Relationship to scan_run
    scan_run: Mapped["ScanRunModel"] = relationship("ScanRunModel", back_populates="pr_records")
