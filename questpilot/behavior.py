"""Explicit state resolver and a small inspectable behavior tree."""
from __future__ import annotations

from .model import Action, GameState, Observation, StateEstimate

class StateResolver:
    _REQUIRED = {
        GameState.LOGIN: frozenset(("QUESTPILOT", "LOGIN")),
        GameState.HOME: frozenset(("QUESTPILOT", "HOME", "DAILY_CHORES")),
        GameState.COLLECTION: frozenset(("QUESTPILOT", "COLLECTION", "CHEST_READY")),
        GameState.REWARDS: frozenset(("QUESTPILOT", "REWARDS", "REWARD_READY")),
        GameState.COMPLETE: frozenset(("QUESTPILOT", "COMPLETE", "ALL_CLAIMED")),
    }
    def resolve(self, observation: Observation) -> StateEstimate:
        matches = []
        tokens = set(observation.text)
        for state, required in self._REQUIRED.items():
            if required.issubset(tokens):
                matches.append((state, min(observation.confidence_for(t) for t in required)))
        if len(matches) != 1: return StateEstimate(GameState.UNKNOWN, 0.0, "no unique state marker set")
        state, confidence = matches[0]
        if confidence < 0.90: return StateEstimate(GameState.UNKNOWN, confidence, "OCR confidence below state threshold")
        return StateEstimate(state, confidence, "unique marker set")

class ChoreBehaviorTree:
    """Priority leaves: login → collection → collect → rewards → claim."""
    def tick(self, state: GameState, collection_done: bool) -> tuple[str, Action | None]:
        if state is GameState.LOGIN: return "login", Action.LOGIN
        if state is GameState.HOME: return ("open_rewards", Action.OPEN_REWARDS) if collection_done else ("open_collection", Action.OPEN_COLLECTION)
        if state is GameState.COLLECTION: return "collect", Action.COLLECT_DAILY
        if state is GameState.REWARDS: return "claim", Action.CLAIM_REWARD
        if state is GameState.COMPLETE: return "complete", None
        return "safe_stop", None
