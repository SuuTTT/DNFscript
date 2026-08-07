import unittest
from datetime import datetime, timezone
from pathlib import Path

from questpilot.duel_links_planner import DuelLinksPermissionGate, LocalPlanner, PlannerTask


NOW = datetime(2026, 8, 7, 9, 0, tzinfo=timezone.utc)


def task(task_id: str, minutes: int, cadence: str = "daily", reset: str = "00:00") -> PlannerTask:
    return PlannerTask(task_id, f"Manual {task_id}", cadence, minutes, reset)


class DuelLinksPlannerTests(unittest.TestCase):
    def test_reminders_recommend_shortest_due_order_and_audit_locally(self):
        planner = LocalPlanner([task("slow", 12), task("quick", 2), task("weekly", 5, "weekly")])
        decision = planner.reminders(NOW)
        self.assertFalse(decision.safe_stop)
        self.assertEqual([item.id for item in decision.tasks], ["quick", "weekly", "slow"])
        self.assertEqual(decision.confidence, 0.99)
        self.assertEqual(planner.audit.events[-1].kind, "reminder_due")

    def test_reset_boundary_reopens_only_after_user_configured_reset(self):
        item = task("reset", 3, reset="04:00")
        item.completed_period = "daily:2026-08-06"
        planner = LocalPlanner([item])
        before = datetime(2026, 8, 7, 3, 59, tzinfo=timezone.utc)
        after = datetime(2026, 8, 7, 4, 0, tzinfo=timezone.utc)
        self.assertEqual(planner.recommend(before).tasks, ())
        self.assertEqual([entry.id for entry in planner.recommend(after).tasks], ["reset"])

    def test_manual_confirmation_is_required_and_updates_local_streak(self):
        planner = LocalPlanner([task("manual", 4)])
        self.assertTrue(planner.confirm_manually("manual", NOW))
        self.assertFalse(planner.confirm_manually("manual", NOW))
        self.assertEqual(planner.tasks[0].streak, 1)
        self.assertEqual(planner.tasks[0].completed_period, "daily:2026-08-07")
        self.assertEqual(planner.audit.events[-1].kind, "manual_confirmation_ignored")

    def test_conflicting_state_safe_stops_without_confirmation(self):
        planner = LocalPlanner([task("same", 2), task("same", 3)])
        decision = planner.recommend(NOW)
        self.assertTrue(decision.safe_stop)
        self.assertIn("duplicate", decision.reason)
        self.assertFalse(planner.confirm_manually("same", NOW))
        self.assertIsNone(planner.tasks[0].completed_period)

    def test_hard_stop_prevents_reminder_and_manual_confirmation(self):
        planner = LocalPlanner([task("stopped", 2)])
        planner.stop()
        self.assertTrue(planner.reminders(NOW).safe_stop)
        self.assertFalse(planner.confirm_manually("stopped", NOW))
        self.assertIsNone(planner.tasks[0].completed_period)

    def test_config_is_original_manual_data(self):
        planner = LocalPlanner.from_config(Path(__file__).parents[1] / "config/duel_links_tasks.json")
        self.assertEqual(len(planner.tasks), 3)
        self.assertFalse(planner.recommend(NOW).safe_stop)

    def test_future_real_game_adapter_is_disabled_without_repository_evidence(self):
        root = Path(__file__).parents[1]
        self.assertFalse(DuelLinksPermissionGate.evaluate(root).enabled)
        decision = DuelLinksPermissionGate.evaluate(root, enable_requested=True)
        self.assertFalse(decision.enabled)
        self.assertIn("authorization", decision.reason)

    def test_planner_ui_is_local_manual_only(self):
        page = (Path(__file__).parents[1] / "demo/duel-links-planner.html").read_text(encoding="utf-8")
        self.assertIn("Confirm manually", page)
        self.assertIn("127.0.0.1", page)
        self.assertIn("Offline synthetic workflow simulator", page)
        self.assertIn("Hard stop", page)
        self.assertNotIn("fetch(", page)
        self.assertNotIn("WebSocket", page)
