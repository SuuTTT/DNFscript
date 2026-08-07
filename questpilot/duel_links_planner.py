"""Local-only, manually confirmed daily-planner logic.

This module deliberately has no game-client, capture, input, network, or
credential integration.  It plans user-entered chores and records the user's
own confirmation in an append-only audit log.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .audit import AuditLog


class PlannerConflict(ValueError):
    """Raised only for invalid local checklist state; it never triggers a game action."""


@dataclass
class PlannerTask:
    id: str
    title: str
    cadence: str
    estimate_minutes: int
    reset_time: str
    reward_note: str = ""
    completed_period: str | None = None
    streak: int = 0


@dataclass(frozen=True)
class PlannerDecision:
    safe_stop: bool
    reason: str
    tasks: tuple[PlannerTask, ...] = ()
    confidence: float = 0.0


@dataclass
class LocalPlanner:
    tasks: list[PlannerTask]
    hard_stop: bool = False
    audit: AuditLog = field(default_factory=AuditLog)

    @classmethod
    def from_config(cls, path: Path) -> "LocalPlanner":
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls([PlannerTask(**task) for task in data["tasks"]])

    @staticmethod
    def _period(task: PlannerTask, now: datetime) -> str:
        if now.tzinfo is None:
            raise PlannerConflict("timestamps must be timezone-aware")
        hour, minute = (int(part) for part in task.reset_time.split(":"))
        local = now.astimezone(timezone.utc)
        boundary = local.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if local < boundary:
            boundary -= timedelta(days=1)
        day = boundary.date()
        if task.cadence == "daily":
            return f"daily:{day.isoformat()}"
        if task.cadence == "weekly":
            monday = day - timedelta(days=day.weekday())
            return f"weekly:{monday.isoformat()}"
        raise PlannerConflict(f"unknown cadence for {task.id}: {task.cadence}")

    def validate(self) -> None:
        ids = [task.id for task in self.tasks]
        if not self.tasks:
            raise PlannerConflict("no manually entered tasks")
        if len(ids) != len(set(ids)):
            raise PlannerConflict("duplicate task IDs conflict")
        for task in self.tasks:
            if not task.id or not task.title.strip() or task.estimate_minutes < 1:
                raise PlannerConflict(f"invalid local task: {task.id or '<missing id>'}")
            if task.cadence not in {"daily", "weekly"} or not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", task.reset_time):
                raise PlannerConflict(f"invalid cadence or reset time: {task.id}")
            if task.completed_period and not task.completed_period.startswith(f"{task.cadence}:"):
                raise PlannerConflict(f"conflicting completion state: {task.id}")

    def stop(self, reason: str = "hard stop manually engaged") -> None:
        self.hard_stop = True
        self.audit.emit("hard_stop", reason=reason)

    def recommend(self, now: datetime) -> PlannerDecision:
        if self.hard_stop:
            self.audit.emit("safe_stop", reason="hard stop engaged")
            return PlannerDecision(True, "hard stop engaged")
        try:
            self.validate()
        except PlannerConflict as error:
            self.audit.emit("safe_stop", reason=str(error))
            return PlannerDecision(True, str(error))
        due = [task for task in self.tasks if task.completed_period != self._period(task, now)]
        ordered = tuple(sorted(due, key=lambda task: (task.estimate_minutes, task.cadence, task.title.casefold())))
        self.audit.emit("recommendation", confidence=0.99, task_ids=[task.id for task in ordered], mode="local_manual_only")
        return PlannerDecision(False, "shortest manually entered order", ordered, 0.99)

    def reminders(self, now: datetime) -> PlannerDecision:
        """Return locally due items; callers decide how (or whether) to display them."""
        decision = self.recommend(now)
        if decision.safe_stop:
            return decision
        self.audit.emit("reminder_due", task_ids=[task.id for task in decision.tasks], mode="local_manual_only")
        return decision

    def confirm_manually(self, task_id: str, now: datetime) -> bool:
        if self.hard_stop:
            self.audit.emit("safe_stop", reason="hard stop engaged", task_id=task_id)
            return False
        try:
            self.validate()
            task = next(task for task in self.tasks if task.id == task_id)
        except (PlannerConflict, StopIteration) as error:
            self.audit.emit("safe_stop", reason="unknown or conflicting task", task_id=task_id)
            return False
        period = self._period(task, now)
        if task.completed_period == period:
            self.audit.emit("manual_confirmation_ignored", task_id=task_id, reason="already confirmed for period")
            return False
        task.completed_period = period
        task.streak += 1
        self.audit.emit("manual_confirmation", task_id=task_id, period=period, streak=task.streak, mode="human_confirmed")
        return True


@dataclass(frozen=True)
class DuelLinksPermissionDecision:
    enabled: bool
    reason: str


class DuelLinksPermissionGate:
    """A disabled placeholder; no adapter exists behind it in Phase 1."""

    AUTHORIZATION_DIR = Path("docs/authorizations/duel_links")

    @classmethod
    def evaluate(cls, root: Path, enable_requested: bool = False) -> DuelLinksPermissionDecision:
        if not enable_requested:
            return DuelLinksPermissionDecision(False, "disabled by default; no real-game adapter is present")
        directory = root / cls.AUTHORIZATION_DIR
        evidence = list(directory.glob("*.md")) if directory.is_dir() else []
        if not evidence:
            return DuelLinksPermissionDecision(False, "dated official API authorization or written publisher permission is not stored")
        content = "\n".join(path.read_text(encoding="utf-8") for path in evidence)
        dated = re.search(r"\b20\d{2}-\d{2}-\d{2}\b", content)
        approved = "OFFICIAL_API_AUTHORIZATION" in content or "WRITTEN_PUBLISHER_PERMISSION" in content
        if not (dated and approved):
            return DuelLinksPermissionDecision(False, "stored authorization is missing a date or required authorization marker")
        return DuelLinksPermissionDecision(True, "authorization evidence is present; separate implementation review still required")
