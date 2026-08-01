"""Safety-gated offline slice: observe → state → tree → action → audit."""
from __future__ import annotations

from dataclasses import dataclass, field
from time import monotonic
from typing import Callable

from .audit import AuditLog
from .behavior import ChoreBehaviorTree, StateResolver
from .mock_game import MockGame
from .model import Action, GameState
from .observation import OfflineOcr

@dataclass(frozen=True)
class AgentConfig:
    dry_run: bool = True
    allowlist: frozenset[Action] = frozenset((Action.LOGIN, Action.OPEN_COLLECTION, Action.COLLECT_DAILY, Action.OPEN_REWARDS, Action.CLAIM_REWARD))
    max_actions: int = 8
    time_limit_seconds: float = 5.0
    action_threshold: float = 0.95

@dataclass
class RunResult:
    completed: bool
    safe_stop: bool
    reason: str
    actions: list[Action] = field(default_factory=list)
    audit: AuditLog = field(default_factory=AuditLog)

class KillSwitch:
    """External caller can stop the run before every observation/action."""
    def __init__(self) -> None: self.engaged = False
    def trigger(self) -> None: self.engaged = True

class QuestPilotAgent:
    def __init__(self, config: AgentConfig | None = None, approval: Callable[[Action], bool] | None = None) -> None:
        self.config = config or AgentConfig()
        self.approval = approval or (lambda _: False)
        self.ocr, self.resolver, self.tree = OfflineOcr(), StateResolver(), ChoreBehaviorTree()
    def run(self, game: MockGame, kill_switch: KillSwitch | None = None, audit: AuditLog | None = None) -> RunResult:
        log, started, actions, collection_done = audit or AuditLog(), monotonic(), [], False
        while True:
            if kill_switch and kill_switch.engaged:
                log.emit("safe_stop", reason="hard kill switch engaged")
                return RunResult(False, True, "hard kill switch engaged", actions, log)
            if monotonic() - started > self.config.time_limit_seconds:
                log.emit("safe_stop", reason="time limit reached")
                return RunResult(False, True, "time limit reached", actions, log)
            if len(actions) >= self.config.max_actions:
                log.emit("safe_stop", reason="action limit reached")
                return RunResult(False, True, "action limit reached", actions, log)
            observation = self.ocr.read(game.capture()); estimate = self.resolver.resolve(observation)
            log.emit("observation", screen_hash=observation.screen_hash, text=list(observation.text), confidence=estimate.confidence, state=estimate.state.value, reason=estimate.reason)
            if estimate.state is GameState.UNKNOWN:
                # No uncertain action may be dispatched. Human review is an
                # explicit new approval/restart, not a fall-through action.
                log.emit("approval_required", reason=estimate.reason, proposed_action=None)
                log.emit("safe_stop", reason="uncertain state")
                return RunResult(False, True, "uncertain state", actions, log)
            leaf, action = self.tree.tick(estimate.state, collection_done)
            log.emit("behavior_tree", leaf=leaf, state=estimate.state.value, action=action.value if action else None)
            if action is None:
                log.emit("complete", state=estimate.state.value)
                return RunResult(True, False, "daily chores complete", actions, log)
            if estimate.confidence < self.config.action_threshold:
                log.emit("approval_required", reason="action confidence below threshold", proposed_action=action.value)
                log.emit("safe_stop", reason="uncertain action")
                return RunResult(False, True, "uncertain action", actions, log)
            if action not in self.config.allowlist:
                log.emit("safe_stop", reason="action not allowlisted", proposed_action=action.value)
                return RunResult(False, True, "action not allowlisted", actions, log)
            # Dry-run advances only the in-memory mock to make the planned
            # trace testable. It never sends an input outside this process.
            applied = game.apply(action)
            log.emit("action", screen_hash=observation.screen_hash, action=action.value, mode="dry_run" if self.config.dry_run else "mock_execute", applied=applied)
            if not applied:
                log.emit("safe_stop", reason="mock rejected action")
                return RunResult(False, True, "mock rejected action", actions, log)
            actions.append(action); collection_done = collection_done or action is Action.COLLECT_DAILY
