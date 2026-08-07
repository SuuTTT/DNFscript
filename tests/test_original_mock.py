import unittest

from questpilot.original_mock import (
    MockAction,
    MockAgentConfig,
    MockHardStop,
    MockState,
    OriginalMockAdapter,
    OriginalMockAutomation,
    run_original_mock_benchmark,
    run_original_mock_safety_probes,
)


class OriginalMockTests(unittest.TestCase):
    def test_original_daily_loop_completes_in_memory_with_replayable_audit(self):
        adapter = OriginalMockAdapter()
        result = OriginalMockAutomation().run(adapter)
        self.assertTrue(result.completed)
        self.assertFalse(result.safe_stop)
        self.assertEqual(adapter.state, MockState.COMPLETE)
        self.assertEqual(len(result.actions), 11)
        self.assertEqual(result.actions[-1], MockAction.CLAIM_REWARD)
        self.assertTrue(result.audit.replayable())
        self.assertTrue(all(event.payload.get("adapter") == "original_mock_adapter"
                            for event in result.audit.events if event.kind == "action"))

    def test_fixed_original_mock_suite_meets_safety_gate(self):
        result = run_original_mock_benchmark()
        self.assertEqual(result["total"], 32)
        self.assertEqual(result["completed"], 32)
        self.assertEqual(result["unsafe_actions"], 0)

    def test_uncertainty_and_hard_stop_probes_never_apply_mock_actions(self):
        self.assertTrue(all(run_original_mock_safety_probes().values()))
        switch = MockHardStop()
        switch.trigger()
        result = OriginalMockAutomation().run(OriginalMockAdapter(), switch)
        self.assertEqual(result.actions, [])

    def test_allowlist_and_execution_gate_stop_before_mutating_mock(self):
        adapter = OriginalMockAdapter()
        denied = OriginalMockAutomation(MockAgentConfig(allowlist=frozenset({MockAction.ENTER_PATROL}))).run(adapter)
        self.assertTrue(denied.safe_stop)
        self.assertEqual(denied.actions, [MockAction.ENTER_PATROL])
        dry_adapter = OriginalMockAdapter()
        dry = OriginalMockAutomation(MockAgentConfig(execute_original_mock=False)).run(dry_adapter)
        self.assertTrue(dry.safe_stop)
        self.assertEqual(dry_adapter.state, MockState.HUB)

    def test_original_adapter_has_no_real_game_or_network_surface(self):
        source = (self._repo_root() / "questpilot/original_mock.py").read_text(encoding="utf-8")
        self.assertIn("original in-memory world", source)
        self.assertNotIn("requests", source)
        self.assertNotIn("socket", source)
        self.assertNotIn("selenium", source)
        self.assertNotIn("pyautogui", source)

    def test_browser_mock_stays_local_and_labels_automation_scope(self):
        page = (self._repo_root() / "demo/original-mock-game.html").read_text(encoding="utf-8")
        self.assertIn("Skyforge Ledger", page)
        self.assertIn("Run mock strategy", page)
        self.assertIn("Mock-only automation", page)
        self.assertIn("Hard stop", page)
        self.assertNotIn("fetch(", page)
        self.assertNotIn("WebSocket", page)

    @staticmethod
    def _repo_root():
        from pathlib import Path
        return Path(__file__).parents[1]
