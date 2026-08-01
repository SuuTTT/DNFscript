"""A deterministic, no-network mock game. It never reads a real screen."""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from .model import Action, GameState

@dataclass(frozen=True)
class MockScreen:
    ocr_text: tuple[str, ...]
    perturbation: str | None = None
    @property
    def hash(self) -> str:
        return sha256(("|".join(self.ocr_text) + "|" + (self.perturbation or "")).encode()).hexdigest()[:16]

class MockGame:
    """Six-step daily loop. This is a token renderer, not a commercial adapter."""
    _MARKERS = {
        GameState.LOGIN: ("QUESTPILOT", "LOGIN"),
        GameState.HOME: ("QUESTPILOT", "HOME", "DAILY_CHORES"),
        GameState.COLLECTION: ("QUESTPILOT", "COLLECTION", "CHEST_READY"),
        GameState.REWARDS: ("QUESTPILOT", "REWARDS", "REWARD_READY"),
        GameState.COMPLETE: ("QUESTPILOT", "COMPLETE", "ALL_CLAIMED"),
    }
    _TRANSITIONS = {
        (GameState.LOGIN, Action.LOGIN): GameState.HOME,
        (GameState.HOME, Action.OPEN_COLLECTION): GameState.COLLECTION,
        (GameState.COLLECTION, Action.COLLECT_DAILY): GameState.HOME,
        (GameState.HOME, Action.OPEN_REWARDS): GameState.REWARDS,
        (GameState.REWARDS, Action.CLAIM_REWARD): GameState.COMPLETE,
    }
    def __init__(self, perturbations: dict[GameState, str] | None = None) -> None:
        self.state = GameState.LOGIN
        self.perturbations = perturbations or {}
        self.applied_actions: list[Action] = []
    def capture(self) -> MockScreen:
        perturbation = self.perturbations.get(self.state)
        tokens = list(self._MARKERS[self.state])
        if perturbation == "mild_noise": tokens.append("DECORATIVE_TEXT")
        elif perturbation == "unreadable": tokens = ["QUESTPILOT", "BLURRED"]
        elif perturbation == "conflict": tokens.extend(["LOGIN", "REWARDS"])
        elif perturbation == "low_confidence": tokens.append("LOW_CONTRAST")
        elif perturbation == "action_uncertain": tokens.append("FAINT_LABEL")
        return MockScreen(tuple(tokens), perturbation)
    def apply(self, action: Action) -> bool:
        transition = self._TRANSITIONS.get((self.state, action))
        if transition is None: return False
        self.applied_actions.append(action); self.state = transition
        return True
