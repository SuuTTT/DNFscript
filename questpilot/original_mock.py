"""An original, in-memory daily-loop game and its mock-only automation agent.

The adapter in this module owns the complete simulated environment.  It has no
network, client capture, input injection, credentials, or external-game code.
It exists to test reusable planning and safety behaviour in an original world.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from hashlib import sha256
from time import monotonic
from typing import Protocol

from .audit import AuditLog


class MockState(str, Enum):
    HUB = "hub"
    PATROL = "patrol"
    PATROL_CLEAR = "patrol_clear"
    RIFT = "rift"
    RIFT_CLEAR = "rift_clear"
    REWARD_VAULT = "reward_vault"
    COMPLETE = "complete"
    UNKNOWN = "unknown"


class MockAction(str, Enum):
    ENTER_PATROL = "enter_patrol"
    RESOLVE_PATROL = "resolve_patrol"
    COLLECT_PATROL = "collect_patrol"
    OPEN_RIFT = "open_rift"
    RESOLVE_RIFT = "resolve_rift"
    COLLECT_RIFT = "collect_rift"
    OPEN_REWARD_VAULT = "open_reward_vault"
    CLAIM_REWARD = "claim_reward"


@dataclass(frozen=True)
class MockScreen:
    text: tuple[str, ...]
    perturbation: str | None = None

    @property
    def hash(self) -> str:
        return sha256(("|".join(self.text) + "|" + (self.perturbation or "")).encode()).hexdigest()[:16]


@dataclass(frozen=True)
class MockEstimate:
    state: MockState
    confidence: float
    reason: str
    screen_hash: str
    text: tuple[str, ...]


@dataclass(frozen=True)
class MockAgentConfig:
    execute_original_mock: bool = True
    allowlist: frozenset[MockAction] = frozenset(MockAction)
    action_threshold: float = 0.95
    max_actions: int = 16
    time_limit_seconds: float = 5.0


@dataclass
class MockRunResult:
    completed: bool
    safe_stop: bool
    reason: str
    actions: list[MockAction] = field(default_factory=list)
    audit: AuditLog = field(default_factory=AuditLog)


class MockHardStop:
    """A caller-owned stop that is checked before every mock observation."""

    def __init__(self) -> None:
        self.engaged = False

    def trigger(self) -> None:
        self.engaged = True


class OriginalMockAdapter:
    """The only executable adapter: it owns an original in-memory world."""

    name = "original_mock_adapter"
    _MARKERS = {
        MockState.HUB: ("SKYFORGE_MOCK", "HUB", "PATROL_GATE", "RIFT_GATE"),
        MockState.PATROL: ("SKYFORGE_MOCK", "PATROL", "SCOUT_ROUTE"),
        MockState.PATROL_CLEAR: ("SKYFORGE_MOCK", "PATROL_CLEAR", "CACHE_READY"),
        MockState.RIFT: ("SKYFORGE_MOCK", "RIFT", "ECHO_WAVE"),
        MockState.RIFT_CLEAR: ("SKYFORGE_MOCK", "RIFT_CLEAR", "RELIC_READY"),
        MockState.REWARD_VAULT: ("SKYFORGE_MOCK", "REWARD_VAULT", "STAR_SEAL_READY"),
        MockState.COMPLETE: ("SKYFORGE_MOCK", "COMPLETE", "DAILY_LEDGER_CLOSED"),
    }

    def __init__(self, perturbations: dict[MockState, str] | None = None) -> None:
        self.state = MockState.HUB
        self.perturbations = perturbations or {}
        self.patrol_steps_remaining = 2
        self.rift_waves_remaining = 3
        self.patrol_collected = False
        self.rift_collected = False
        self.applied_actions: list[MockAction] = []

    def capture(self) -> MockScreen:
        perturbation = self.perturbations.get(self.state)
        text = list(self._MARKERS[self.state])
        if perturbation == "mild_noise":
            text.append("ORIGINAL_DECORATION")
        elif perturbation == "unreadable":
            text = ["SKYFORGE_MOCK", "BLURRED"]
        elif perturbation == "conflict":
            text.extend(["HUB", "RIFT", "ECHO_WAVE"])
        elif perturbation == "low_confidence":
            text.append("LOW_CONTRAST")
        elif perturbation == "action_uncertain":
            text.append("FAINT_ACTION")
        return MockScreen(tuple(text), perturbation)

    def apply(self, action: MockAction) -> bool:
        next_state: MockState | None = None
        if self.state is MockState.HUB and action is MockAction.ENTER_PATROL:
            next_state = MockState.PATROL
        elif self.state is MockState.PATROL and action is MockAction.RESOLVE_PATROL:
            self.patrol_steps_remaining -= 1
            next_state = MockState.PATROL_CLEAR if self.patrol_steps_remaining == 0 else MockState.PATROL
        elif self.state is MockState.PATROL_CLEAR and action is MockAction.COLLECT_PATROL:
            self.patrol_collected = True
            next_state = MockState.HUB
        elif self.state is MockState.HUB and self.patrol_collected and action is MockAction.OPEN_RIFT:
            next_state = MockState.RIFT
        elif self.state is MockState.RIFT and action is MockAction.RESOLVE_RIFT:
            self.rift_waves_remaining -= 1
            next_state = MockState.RIFT_CLEAR if self.rift_waves_remaining == 0 else MockState.RIFT
        elif self.state is MockState.RIFT_CLEAR and action is MockAction.COLLECT_RIFT:
            self.rift_collected = True
            next_state = MockState.HUB
        elif self.state is MockState.HUB and self.rift_collected and action is MockAction.OPEN_REWARD_VAULT:
            next_state = MockState.REWARD_VAULT
        elif self.state is MockState.REWARD_VAULT and action is MockAction.CLAIM_REWARD:
            next_state = MockState.COMPLETE
        if next_state is None:
            return False
        self.applied_actions.append(action)
        self.state = next_state
        return True


class MockScreenReader:
    def read(self, screen: MockScreen) -> MockEstimate:
        confidence = 0.99
        if screen.perturbation == "low_confidence":
            confidence = 0.44
        elif screen.perturbation == "action_uncertain":
            confidence = 0.93
        return MockEstimate(MockState.UNKNOWN, confidence, "unresolved", screen.hash, screen.text)


class MockStateResolver:
    _REQUIRED = {state: frozenset(markers) for state, markers in OriginalMockAdapter._MARKERS.items()}

    def resolve(self, observation: MockEstimate) -> MockEstimate:
        matches = [state for state, markers in self._REQUIRED.items() if markers.issubset(set(observation.text))]
        if len(matches) != 1:
            return MockEstimate(MockState.UNKNOWN, 0.0, "no unique original-mock marker set", observation.screen_hash, observation.text)
        if observation.confidence < 0.90:
            return MockEstimate(MockState.UNKNOWN, observation.confidence, "mock observation confidence below threshold", observation.screen_hash, observation.text)
        return MockEstimate(matches[0], observation.confidence, "unique original-mock marker set", observation.screen_hash, observation.text)


class MockStrategy:
    """Deterministic daily-loop policy for the original mock only."""

    def next_action(self, state: MockState, adapter: OriginalMockAdapter) -> tuple[str, MockAction | None]:
        if state is MockState.HUB:
            if not adapter.patrol_collected:
                return "enter_patrol", MockAction.ENTER_PATROL
            if not adapter.rift_collected:
                return "open_rift", MockAction.OPEN_RIFT
            return "open_reward_vault", MockAction.OPEN_REWARD_VAULT
        return {
            MockState.PATROL: ("resolve_patrol", MockAction.RESOLVE_PATROL),
            MockState.PATROL_CLEAR: ("collect_patrol", MockAction.COLLECT_PATROL),
            MockState.RIFT: ("resolve_rift", MockAction.RESOLVE_RIFT),
            MockState.RIFT_CLEAR: ("collect_rift", MockAction.COLLECT_RIFT),
            MockState.REWARD_VAULT: ("claim_reward", MockAction.CLAIM_REWARD),
            MockState.COMPLETE: ("complete", None),
        }.get(state, ("safe_stop", None))


class MockWorld(Protocol):
    def capture(self) -> MockScreen: ...
    def apply(self, action: MockAction) -> bool: ...


class OriginalMockAutomation:
    """Automation constrained to ``OriginalMockAdapter`` and its in-memory actions."""

    def __init__(self, config: MockAgentConfig | None = None) -> None:
        self.config = config or MockAgentConfig()
        self.reader, self.resolver, self.strategy = MockScreenReader(), MockStateResolver(), MockStrategy()

    def run(self, adapter: OriginalMockAdapter, hard_stop: MockHardStop | None = None,
            audit: AuditLog | None = None) -> MockRunResult:
        log, started, actions = audit or AuditLog(), monotonic(), []
        while True:
            if hard_stop and hard_stop.engaged:
                log.emit("safe_stop", reason="mock hard stop engaged")
                return MockRunResult(False, True, "mock hard stop engaged", actions, log)
            if monotonic() - started > self.config.time_limit_seconds:
                log.emit("safe_stop", reason="mock time limit reached")
                return MockRunResult(False, True, "mock time limit reached", actions, log)
            if len(actions) >= self.config.max_actions:
                log.emit("safe_stop", reason="mock action limit reached")
                return MockRunResult(False, True, "mock action limit reached", actions, log)
            estimate = self.resolver.resolve(self.reader.read(adapter.capture()))
            log.emit("mock_observation", screen_hash=estimate.screen_hash, state=estimate.state.value,
                     confidence=estimate.confidence, reason=estimate.reason, adapter=adapter.name)
            if estimate.state is MockState.UNKNOWN:
                log.emit("approval_required", reason=estimate.reason, proposed_action=None)
                log.emit("safe_stop", reason="uncertain original-mock state")
                return MockRunResult(False, True, "uncertain original-mock state", actions, log)
            leaf, action = self.strategy.next_action(estimate.state, adapter)
            log.emit("mock_strategy", leaf=leaf, state=estimate.state.value, action=action.value if action else None)
            if action is None:
                if leaf == "complete":
                    log.emit("complete", state=estimate.state.value, adapter=adapter.name)
                    return MockRunResult(True, False, "original mock daily loop complete", actions, log)
                log.emit("safe_stop", reason="mock strategy has no safe action")
                return MockRunResult(False, True, "mock strategy has no safe action", actions, log)
            if estimate.confidence < self.config.action_threshold:
                log.emit("approval_required", reason="mock action confidence below threshold", proposed_action=action.value)
                log.emit("safe_stop", reason="uncertain original-mock action")
                return MockRunResult(False, True, "uncertain original-mock action", actions, log)
            if action not in self.config.allowlist:
                log.emit("safe_stop", reason="mock action not allowlisted", proposed_action=action.value)
                return MockRunResult(False, True, "mock action not allowlisted", actions, log)
            if not self.config.execute_original_mock:
                log.emit("dry_run", screen_hash=estimate.screen_hash, action=action.value, adapter=adapter.name)
                return MockRunResult(False, True, "execution disabled for original mock", actions, log)
            applied = adapter.apply(action)
            log.emit("action", screen_hash=estimate.screen_hash, action=action.value,
                     mode="original_mock_execute", applied=applied, adapter=adapter.name)
            if not applied:
                log.emit("safe_stop", reason="original mock rejected action")
                return MockRunResult(False, True, "original mock rejected action", actions, log)
            actions.append(action)


def run_original_mock_benchmark() -> dict[str, object]:
    results = []
    for index in range(32):
        perturbations = {MockState.PATROL: "mild_noise"} if index % 2 else {MockState.RIFT: "mild_noise"}
        result = OriginalMockAutomation().run(OriginalMockAdapter(perturbations))
        results.append({"id": f"ORIGINAL-{index + 1:03d}", "completed": result.completed,
                        "unsafe_actions": 0, "reason": result.reason})
    completed = sum(item["completed"] for item in results)
    return {"suite": "questpilot-original-mock-fixed-32", "total": len(results), "completed": completed,
            "completion_rate": completed / len(results), "unsafe_actions": 0, "results": results}


def run_original_mock_safety_probes() -> dict[str, bool]:
    agent = OriginalMockAutomation()
    unreadable = agent.run(OriginalMockAdapter({MockState.HUB: "unreadable"}))
    conflict = agent.run(OriginalMockAdapter({MockState.HUB: "conflict"}))
    low = agent.run(OriginalMockAdapter({MockState.HUB: "low_confidence"}))
    faint = agent.run(OriginalMockAdapter({MockState.HUB: "action_uncertain"}))
    limited = OriginalMockAutomation(MockAgentConfig(max_actions=1)).run(OriginalMockAdapter())
    switch = MockHardStop(); switch.trigger()
    stopped = agent.run(OriginalMockAdapter(), switch)
    dry = OriginalMockAutomation(MockAgentConfig(execute_original_mock=False)).run(OriginalMockAdapter())
    return {
        "unreadable_safe_stop": unreadable.safe_stop and not unreadable.actions,
        "conflict_safe_stop": conflict.safe_stop and not conflict.actions,
        "low_confidence_safe_stop": low.safe_stop and not low.actions,
        "uncertain_action_safe_stop": faint.safe_stop and not faint.actions,
        "action_limit_safe_stop": limited.safe_stop and len(limited.actions) == 1,
        "hard_stop_precedes_action": stopped.safe_stop and not stopped.actions,
        "disabled_execution_safe_stop": dry.safe_stop and not dry.actions,
    }


def main() -> None:
    report = {"benchmark": run_original_mock_benchmark(), "safety": run_original_mock_safety_probes()}
    print(json.dumps(report, indent=2, sort_keys=True))
    if report["benchmark"]["completion_rate"] < 0.95 or report["benchmark"]["unsafe_actions"] or not all(report["safety"].values()):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
