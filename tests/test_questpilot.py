import json
import tempfile
import unittest
from pathlib import Path
from questpilot.agent import AgentConfig, KillSwitch, QuestPilotAgent
from questpilot.audit import AuditLog
from questpilot.benchmark import run_benchmark, run_perturbation_tests
from questpilot.mock_game import MockGame
from questpilot.model import Action, GameState
from questpilot.integration_gate import AdapterManifest, Environment, LUANTI_MANIFEST, MINECRAFT_EDUCATION_MANIFEST, evaluate_manifest
from questpilot.ui_product import OfflineUiSimulator, QuestPilotUiAgent, UiAction, UiAgentConfig, UiKillSwitch, UiState, UiTask, run_ui_benchmark, run_ui_perturbation_tests

class QuestPilotTests(unittest.TestCase):
    def test_fixed_30_chore_benchmark_hits_safety_gate(self):
        result = run_benchmark(); self.assertEqual(result["total"], 30); self.assertGreaterEqual(result["completion_rate"], .95); self.assertEqual(result["unsafe_actions"], 0)
    def test_each_uncertain_case_stops_without_unsafe_action(self): self.assertTrue(all(run_perturbation_tests().values()))
    def test_dry_run_is_default_and_generates_replayable_jsonl(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "audit.jsonl"; result = QuestPilotAgent().run(MockGame(), audit=AuditLog(path))
            self.assertTrue(result.completed); self.assertTrue(result.audit.replayable())
            actions = [json.loads(line) for line in path.read_text().splitlines() if json.loads(line)["kind"] == "action"]
            self.assertTrue(actions); self.assertTrue(all(item["payload"]["mode"] == "dry_run" for item in actions))
    def test_allowlist_blocks_nonapproved_action(self):
        result = QuestPilotAgent(AgentConfig(allowlist=frozenset({Action.LOGIN}))).run(MockGame())
        self.assertTrue(result.safe_stop); self.assertEqual(result.reason, "action not allowlisted"); self.assertEqual(result.actions, [Action.LOGIN])
    def test_hard_kill_switch_precedes_observation_and_action(self):
        kill_switch = KillSwitch(); kill_switch.trigger(); result = QuestPilotAgent().run(MockGame(), kill_switch)
        self.assertTrue(result.safe_stop); self.assertEqual(result.actions, [])
    def test_mock_execute_is_explicit_and_never_has_external_input(self):
        result = QuestPilotAgent(AgentConfig(dry_run=False)).run(MockGame()); self.assertTrue(result.completed); self.assertEqual(result.actions[-1], Action.CLAIM_REWARD)
    def test_unreadable_screen_stops_after_known_login_only(self):
        result = QuestPilotAgent().run(MockGame({GameState.HOME: "unreadable"})); self.assertTrue(result.safe_stop); self.assertEqual(result.actions, [Action.LOGIN])
    def test_borderline_action_confidence_requests_approval_and_stops(self):
        result = QuestPilotAgent().run(MockGame({GameState.LOGIN: "action_uncertain"}))
        self.assertTrue(result.safe_stop); self.assertEqual(result.reason, "uncertain action"); self.assertEqual(result.actions, [])
        self.assertTrue(any(event.kind == "approval_required" for event in result.audit.events))
    def test_minecraft_education_manifest_is_authorized_and_bounded(self):
        self.assertTrue(evaluate_manifest(MINECRAFT_EDUCATION_MANIFEST).allowed)
    def test_luanti_manifest_is_authorized_and_bounded(self):
        self.assertTrue(evaluate_manifest(LUANTI_MANIFEST).allowed)
    def test_future_production_mobile_adapter_is_rejected(self):
        manifest = AdapterManifest("future mobile", Environment.PRODUCTION, "", MINECRAFT_EDUCATION_MANIFEST.observation, frozenset({"agent.move", "payment"}))
        decision = evaluate_manifest(manifest)
        self.assertFalse(decision.allowed)
        self.assertIn("production environments are never eligible", decision.reasons)
        self.assertTrue(any("missing" in reason for reason in decision.reasons))
        self.assertTrue(any("payment" in reason for reason in decision.reasons))
    def test_minecraft_script_uses_only_bounded_human_stepped_flow(self):
        script = (Path(__file__).parents[1] / "adapters/minecraft_education/questpilot_collection.ts").read_text()
        self.assertIn('player.onChat("qp_start"', script)
        self.assertIn('player.onChat("qp_stop"', script)
        self.assertIn("agent.collectAll()", script)
        self.assertNotIn("loops.forever", script)
        self.assertNotIn("agent.attack", script)
    def test_luanti_script_is_singleplayer_only_and_never_uses_web_or_credentials(self):
        script = (Path(__file__).parents[1] / "adapters/luanti/init.lua").read_text()
        self.assertIn("mt.is_singleplayer()", script)
        self.assertIn('mt.register_chatcommand("qp_stop"', script)
        self.assertIn('"questpilot_luanti:token"', script)
        self.assertNotIn("request_http_api", script)
        self.assertNotIn("credentials", script)
    def test_product_ui_benchmark_has_120_safe_offline_workflows(self):
        result = run_ui_benchmark()
        self.assertEqual(result["total"], 120)
        self.assertEqual(result["completed"], 120)
        self.assertEqual(result["unsafe_actions"], 0)
    def test_quest_ui_reads_then_claims_reward(self):
        game = OfflineUiSimulator(); result = QuestPilotUiAgent().run(game, UiTask.QUEST_AND_REWARD)
        self.assertTrue(result.completed)
        self.assertEqual(game.applied_actions[-1], UiAction.CLAIM_REWARD)
        self.assertTrue(any(event.kind == "ui_observation" for event in result.audit.events))
        self.assertTrue(result.audit.replayable())
    def test_upgrade_is_recommendation_only_by_default(self):
        game = OfflineUiSimulator(); result = QuestPilotUiAgent().run(game, UiTask.UPGRADE_RECOMMENDATION)
        self.assertTrue(result.completed); self.assertEqual(result.reason, "upgrade recommendation ready")
        self.assertEqual(game.soft_tokens, 120)
        self.assertTrue(any(event.kind == "recommendation" for event in result.audit.events))
    def test_offline_upgrade_needs_two_explicit_gates(self):
        result = QuestPilotUiAgent().run(OfflineUiSimulator(), UiTask.APPLY_OFFLINE_UPGRADE)
        self.assertTrue(result.safe_stop); self.assertEqual(result.reason, "upgrade approval required")
        approved = QuestPilotUiAgent(UiAgentConfig(allow_upgrade_execution=True), approval=lambda action: action is UiAction.APPLY_UPGRADE).run(OfflineUiSimulator(), UiTask.APPLY_OFFLINE_UPGRADE)
        self.assertTrue(approved.completed)
    def test_product_ui_uncertainty_stops_before_any_input(self):
        result = QuestPilotUiAgent().run(OfflineUiSimulator({UiState.LOGIN: "unreadable"}), UiTask.QUEST_AND_REWARD)
        self.assertTrue(result.safe_stop); self.assertEqual(result.actions, [])
    def test_product_ui_perturbations_and_hard_stop_are_safe(self):
        self.assertTrue(all(run_ui_perturbation_tests().values()))
        switch = UiKillSwitch(); switch.trigger()
        result = QuestPilotUiAgent().run(OfflineUiSimulator(), UiTask.CLAIM_REWARD, kill_switch=switch)
        self.assertEqual(result.actions, [])
