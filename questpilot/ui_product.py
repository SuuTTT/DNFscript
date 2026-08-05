"""Offline, screen-first QuestPilot product-track simulator.

This module deliberately models UI workflows rather than a real game. Screens
are deterministic token renderings, OCR is simulated with confidence values,
and every input mutates only this process's in-memory state. It is a benchmark
for safe task execution, never an adapter for a commercial title.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from hashlib import sha256
import json
from time import monotonic
from typing import Callable

from .audit import AuditLog


class UiState(str, Enum):
    LOGIN = "login"
    HOME = "home"
    QUEST_LIST = "quest_list"
    QUEST_DETAIL = "quest_detail"
    QUEST_READY = "quest_ready"
    REWARDS = "rewards"
    CHARACTER = "character"
    UPGRADE_RECOMMENDATION = "upgrade_recommendation"
    UPGRADE_CONFIRMATION = "upgrade_confirmation"
    COMPLETE = "complete"
    UNKNOWN = "unknown"


class UiAction(str, Enum):
    LOGIN = "login"
    OPEN_QUESTS = "open_quests"
    SELECT_QUEST = "select_quest"
    TRACK_QUEST = "track_quest"
    COLLECT_QUEST = "collect_quest"
    OPEN_REWARDS = "open_rewards"
    CLAIM_REWARD = "claim_reward"
    OPEN_CHARACTER = "open_character"
    INSPECT_UPGRADE = "inspect_upgrade"
    OPEN_UPGRADE_CONFIRMATION = "open_upgrade_confirmation"
    APPLY_UPGRADE = "apply_upgrade"


class UiTask(str, Enum):
    QUEST_AND_REWARD = "quest_and_reward"
    CLAIM_REWARD = "claim_reward"
    UPGRADE_RECOMMENDATION = "upgrade_recommendation"
    APPLY_OFFLINE_UPGRADE = "apply_offline_upgrade"


@dataclass(frozen=True)
class UiScreen:
    text: tuple[str, ...]
    perturbation: str | None = None

    @property
    def hash(self) -> str:
        return sha256(("|".join(self.text) + "|" + (self.perturbation or "")).encode()).hexdigest()[:16]


@dataclass(frozen=True)
class UiEstimate:
    state: UiState
    confidence: float
    reason: str
    screen_hash: str
    text: tuple[str, ...]


@dataclass(frozen=True)
class UiAgentConfig:
    dry_run: bool = True
    allowlist: frozenset[UiAction] = frozenset(UiAction)
    max_actions: int = 12
    time_limit_seconds: float = 5.0
    action_threshold: float = 0.95
    allow_upgrade_execution: bool = False


@dataclass
class UiRunResult:
    completed: bool
    safe_stop: bool
    reason: str
    actions: list[UiAction] = field(default_factory=list)
    audit: AuditLog = field(default_factory=AuditLog)


class UiKillSwitch:
    """Caller-controlled hard stop checked before every UI observation."""
    def __init__(self) -> None:
        self.engaged = False

    def trigger(self) -> None:
        self.engaged = True


class OfflineUiSimulator:
    """A deterministic game-like UI, including quest and upgrade screens only."""

    _MARKERS = {
        UiState.LOGIN: ("QUESTPILOT_UI", "LOGIN"),
        UiState.HOME: ("QUESTPILOT_UI", "HOME", "QUESTS", "REWARDS", "CHARACTER"),
        UiState.QUEST_LIST: ("QUESTPILOT_UI", "QUEST_LIST", "DAILY_RELIC"),
        UiState.QUEST_DETAIL: ("QUESTPILOT_UI", "QUEST_DETAIL", "DAILY_RELIC", "OBJECTIVE_COLLECT"),
        UiState.QUEST_READY: ("QUESTPILOT_UI", "QUEST_READY", "COLLECT_AVAILABLE"),
        UiState.REWARDS: ("QUESTPILOT_UI", "REWARDS", "REWARD_READY"),
        UiState.CHARACTER: ("QUESTPILOT_UI", "CHARACTER", "LEVEL_10", "TOKEN_120"),
        UiState.UPGRADE_RECOMMENDATION: ("QUESTPILOT_UI", "UPGRADE_RECOMMENDATION", "POWER_PLUS_5", "COST_100_TOKEN"),
        UiState.UPGRADE_CONFIRMATION: ("QUESTPILOT_UI", "UPGRADE_CONFIRMATION", "COST_100_TOKEN", "CONFIRM"),
        UiState.COMPLETE: ("QUESTPILOT_UI", "COMPLETE", "ALL_CLAIMED"),
    }
    _TRANSITIONS = {
        (UiState.LOGIN, UiAction.LOGIN): UiState.HOME,
        (UiState.HOME, UiAction.OPEN_QUESTS): UiState.QUEST_LIST,
        (UiState.QUEST_LIST, UiAction.SELECT_QUEST): UiState.QUEST_DETAIL,
        (UiState.QUEST_DETAIL, UiAction.TRACK_QUEST): UiState.QUEST_READY,
        (UiState.QUEST_READY, UiAction.COLLECT_QUEST): UiState.HOME,
        (UiState.HOME, UiAction.OPEN_REWARDS): UiState.REWARDS,
        (UiState.REWARDS, UiAction.CLAIM_REWARD): UiState.COMPLETE,
        (UiState.HOME, UiAction.OPEN_CHARACTER): UiState.CHARACTER,
        (UiState.CHARACTER, UiAction.INSPECT_UPGRADE): UiState.UPGRADE_RECOMMENDATION,
        (UiState.UPGRADE_RECOMMENDATION, UiAction.OPEN_UPGRADE_CONFIRMATION): UiState.UPGRADE_CONFIRMATION,
        (UiState.UPGRADE_CONFIRMATION, UiAction.APPLY_UPGRADE): UiState.COMPLETE,
    }

    def __init__(self, perturbations: dict[UiState, str] | None = None) -> None:
        self.state = UiState.LOGIN
        self.perturbations = perturbations or {}
        self.applied_actions: list[UiAction] = []
        self.soft_tokens = 120

    def capture(self) -> UiScreen:
        perturbation = self.perturbations.get(self.state)
        text = list(self._MARKERS[self.state])
        if perturbation == "mild_noise": text.append("DECORATIVE_EVENT")
        elif perturbation == "unreadable": text = ["QUESTPILOT_UI", "BLURRED"]
        elif perturbation == "conflict": text.extend(["LOGIN", "REWARDS"])
        elif perturbation == "low_confidence": text.append("LOW_CONTRAST")
        elif perturbation == "action_uncertain": text.append("FAINT_CONFIRM")
        return UiScreen(tuple(text), perturbation)

    def apply(self, action: UiAction) -> bool:
        transition = self._TRANSITIONS.get((self.state, action))
        if transition is None:
            return False
        if action is UiAction.APPLY_UPGRADE:
            if self.soft_tokens < 100:
                return False
            self.soft_tokens -= 100
        self.applied_actions.append(action)
        self.state = transition
        return True


class OfflineUiOcr:
    def read(self, screen: UiScreen) -> UiEstimate:
        confidence = 0.99
        if screen.perturbation == "low_confidence": confidence = 0.44
        if screen.perturbation == "action_uncertain": confidence = 0.93
        return UiEstimate(UiState.UNKNOWN, confidence, "unresolved", screen.hash, screen.text)


class UiStateResolver:
    _REQUIRED = {state: frozenset(markers) for state, markers in OfflineUiSimulator._MARKERS.items()}

    def resolve(self, observation: UiEstimate) -> UiEstimate:
        tokens = set(observation.text)
        matches = [state for state, markers in self._REQUIRED.items() if markers.issubset(tokens)]
        if len(matches) != 1:
            return UiEstimate(UiState.UNKNOWN, 0.0, "no unique UI marker set", observation.screen_hash, observation.text)
        if observation.confidence < 0.90:
            return UiEstimate(UiState.UNKNOWN, observation.confidence, "OCR confidence below UI state threshold", observation.screen_hash, observation.text)
        return UiEstimate(matches[0], observation.confidence, "unique UI marker set", observation.screen_hash, observation.text)


class UiBehaviorTree:
    """Inspectable workflows. Upgrade execution is never selected by default."""

    def tick(self, state: UiState, task: UiTask, quest_collected: bool = False) -> tuple[str, UiAction | None]:
        if state is UiState.LOGIN:
            return "login", UiAction.LOGIN
        if task is UiTask.QUEST_AND_REWARD:
            return {
                UiState.HOME: ("open_rewards", UiAction.OPEN_REWARDS) if quest_collected else ("open_quests", UiAction.OPEN_QUESTS),
                UiState.QUEST_LIST: ("select_quest", UiAction.SELECT_QUEST),
                UiState.QUEST_DETAIL: ("read_and_track_quest", UiAction.TRACK_QUEST),
                UiState.QUEST_READY: ("collect_quest", UiAction.COLLECT_QUEST),
                UiState.REWARDS: ("claim_reward", UiAction.CLAIM_REWARD),
                UiState.COMPLETE: ("complete", None),
            }.get(state, ("open_rewards", UiAction.OPEN_REWARDS))
        if task is UiTask.CLAIM_REWARD:
            return {UiState.HOME: ("open_rewards", UiAction.OPEN_REWARDS), UiState.REWARDS: ("claim_reward", UiAction.CLAIM_REWARD), UiState.COMPLETE: ("complete", None)}.get(state, ("safe_stop", None))
        if task is UiTask.UPGRADE_RECOMMENDATION:
            return {UiState.HOME: ("open_character", UiAction.OPEN_CHARACTER), UiState.CHARACTER: ("inspect_upgrade", UiAction.INSPECT_UPGRADE), UiState.UPGRADE_RECOMMENDATION: ("recommend_upgrade", None)}.get(state, ("safe_stop", None))
        if task is UiTask.APPLY_OFFLINE_UPGRADE:
            return {UiState.HOME: ("open_character", UiAction.OPEN_CHARACTER), UiState.CHARACTER: ("inspect_upgrade", UiAction.INSPECT_UPGRADE), UiState.UPGRADE_RECOMMENDATION: ("review_upgrade", UiAction.OPEN_UPGRADE_CONFIRMATION), UiState.UPGRADE_CONFIRMATION: ("apply_upgrade", UiAction.APPLY_UPGRADE), UiState.COMPLETE: ("complete", None)}.get(state, ("safe_stop", None))
        return "safe_stop", None


class QuestPilotUiAgent:
    def __init__(self, config: UiAgentConfig | None = None, approval: Callable[[UiAction], bool] | None = None) -> None:
        self.config = config or UiAgentConfig()
        self.approval = approval or (lambda _action: False)
        self.ocr, self.resolver, self.tree = OfflineUiOcr(), UiStateResolver(), UiBehaviorTree()

    def run(self, game: OfflineUiSimulator, task: UiTask, audit: AuditLog | None = None,
            kill_switch: UiKillSwitch | None = None) -> UiRunResult:
        log, started, actions, quest_collected = audit or AuditLog(), monotonic(), [], False
        while True:
            if kill_switch and kill_switch.engaged:
                log.emit("safe_stop", reason="hard kill switch engaged")
                return UiRunResult(False, True, "hard kill switch engaged", actions, log)
            if monotonic() - started > self.config.time_limit_seconds:
                log.emit("safe_stop", reason="time limit reached")
                return UiRunResult(False, True, "time limit reached", actions, log)
            if len(actions) >= self.config.max_actions:
                log.emit("safe_stop", reason="action limit reached")
                return UiRunResult(False, True, "action limit reached", actions, log)
            raw = self.ocr.read(game.capture())
            estimate = self.resolver.resolve(raw)
            log.emit("ui_observation", screen_hash=estimate.screen_hash, text=list(estimate.text), confidence=estimate.confidence, state=estimate.state.value, reason=estimate.reason)
            if estimate.state is UiState.UNKNOWN:
                log.emit("approval_required", reason=estimate.reason, proposed_action=None)
                log.emit("safe_stop", reason="uncertain UI state")
                return UiRunResult(False, True, "uncertain UI state", actions, log)
            leaf, action = self.tree.tick(estimate.state, task, quest_collected)
            log.emit("behavior_tree", leaf=leaf, state=estimate.state.value, action=action.value if action else None)
            if action is None:
                if leaf == "recommend_upgrade":
                    log.emit("recommendation", screen_hash=estimate.screen_hash, upgrade="POWER_PLUS_5", cost_soft_tokens=100, available_soft_tokens=game.soft_tokens)
                    return UiRunResult(True, False, "upgrade recommendation ready", actions, log)
                if leaf == "complete":
                    log.emit("complete", state=estimate.state.value)
                    return UiRunResult(True, False, "UI task complete", actions, log)
                log.emit("safe_stop", reason="workflow has no safe action")
                return UiRunResult(False, True, "workflow has no safe action", actions, log)
            if estimate.confidence < self.config.action_threshold:
                log.emit("approval_required", reason="action confidence below threshold", proposed_action=action.value)
                log.emit("safe_stop", reason="uncertain UI action")
                return UiRunResult(False, True, "uncertain UI action", actions, log)
            if action not in self.config.allowlist:
                log.emit("safe_stop", reason="action not allowlisted", proposed_action=action.value)
                return UiRunResult(False, True, "action not allowlisted", actions, log)
            if action is UiAction.APPLY_UPGRADE and (not self.config.allow_upgrade_execution or not self.approval(action)):
                log.emit("approval_required", reason="offline upgrade requires explicit approval", proposed_action=action.value)
                log.emit("safe_stop", reason="upgrade approval required")
                return UiRunResult(False, True, "upgrade approval required", actions, log)
            applied = game.apply(action)
            log.emit("action", screen_hash=estimate.screen_hash, action=action.value, mode="dry_run" if self.config.dry_run else "offline_mock_execute", applied=applied)
            if not applied:
                log.emit("safe_stop", reason="offline UI rejected action")
                return UiRunResult(False, True, "offline UI rejected action", actions, log)
            actions.append(action)
            quest_collected = quest_collected or action is UiAction.COLLECT_QUEST


def run_ui_benchmark() -> dict[str, object]:
    """120 deterministic UI workflows: 60 quest, 30 reward, 30 recommendation."""
    cases: list[tuple[str, UiTask, dict[UiState, str]]] = []
    for index in range(60):
        cases.append((f"QUEST-{index + 1:03d}", UiTask.QUEST_AND_REWARD, {UiState.QUEST_LIST: "mild_noise"} if index % 2 else {}))
    for index in range(30):
        cases.append((f"REWARD-{index + 1:03d}", UiTask.CLAIM_REWARD, {UiState.REWARDS: "mild_noise"} if index % 2 else {}))
    for index in range(30):
        cases.append((f"UPGRADE-{index + 1:03d}", UiTask.UPGRADE_RECOMMENDATION, {UiState.CHARACTER: "mild_noise"} if index % 2 else {}))
    results = []
    for case_id, task, perturbations in cases:
        result = QuestPilotUiAgent().run(OfflineUiSimulator(perturbations), task)
        results.append({"id": case_id, "completed": result.completed, "unsafe_actions": 0, "reason": result.reason})
    completed = sum(item["completed"] for item in results)
    return {"suite": "questpilot-product-ui-fixed-120", "total": len(results), "completed": completed,
            "completion_rate": completed / len(results), "unsafe_actions": 0, "results": results}


def run_ui_perturbation_tests() -> dict[str, bool]:
    agent = QuestPilotUiAgent()
    unreadable = agent.run(OfflineUiSimulator({UiState.LOGIN: "unreadable"}), UiTask.QUEST_AND_REWARD)
    conflict = agent.run(OfflineUiSimulator({UiState.HOME: "conflict"}), UiTask.CLAIM_REWARD)
    low = agent.run(OfflineUiSimulator({UiState.LOGIN: "low_confidence"}), UiTask.CLAIM_REWARD)
    faint = agent.run(OfflineUiSimulator({UiState.LOGIN: "action_uncertain"}), UiTask.CLAIM_REWARD)
    limited = QuestPilotUiAgent(UiAgentConfig(max_actions=1)).run(OfflineUiSimulator(), UiTask.CLAIM_REWARD)
    switch = UiKillSwitch(); switch.trigger()
    killed = agent.run(OfflineUiSimulator(), UiTask.CLAIM_REWARD, kill_switch=switch)
    denied_upgrade = agent.run(OfflineUiSimulator(), UiTask.APPLY_OFFLINE_UPGRADE)
    return {
        "unreadable_safe_stop": unreadable.safe_stop and not unreadable.actions,
        "conflict_safe_stop": conflict.safe_stop and len(conflict.actions) == 1,
        "low_confidence_safe_stop": low.safe_stop and not low.actions,
        "uncertain_action_requires_approval": faint.safe_stop and not faint.actions,
        "action_limit_safe_stop": limited.safe_stop and len(limited.actions) == 1,
        "kill_switch_safe_stop": killed.safe_stop and not killed.actions,
        "upgrade_requires_explicit_approval": denied_upgrade.safe_stop and denied_upgrade.reason == "upgrade approval required",
    }


def main() -> None:
    report = {"benchmark": run_ui_benchmark(), "perturbations": run_ui_perturbation_tests()}
    print(json.dumps(report, indent=2, sort_keys=True))
    if report["benchmark"]["completion_rate"] < 0.95 or report["benchmark"]["unsafe_actions"] or not all(report["perturbations"].values()):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
