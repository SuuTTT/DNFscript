"""Typed state and audit records for the deterministic offline mock only."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any

class GameState(str, Enum):
    LOGIN = "login"
    HOME = "home"
    COLLECTION = "collection"
    REWARDS = "rewards"
    COMPLETE = "complete"
    UNKNOWN = "unknown"

class Action(str, Enum):
    LOGIN = "login"
    OPEN_COLLECTION = "open_collection"
    COLLECT_DAILY = "collect_daily"
    OPEN_REWARDS = "open_rewards"
    CLAIM_REWARD = "claim_reward"
    STOP = "stop"

@dataclass(frozen=True)
class Observation:
    text: tuple[str, ...]
    confidences: dict[str, float]
    screen_hash: str
    perturbation: str | None = None
    def confidence_for(self, marker: str) -> float:
        return self.confidences.get(marker, 0.0)

@dataclass(frozen=True)
class StateEstimate:
    state: GameState
    confidence: float
    reason: str

@dataclass
class AuditEvent:
    seq: int
    kind: str
    payload: dict[str, Any] = field(default_factory=dict)
    def as_dict(self) -> dict[str, Any]:
        return asdict(self)
