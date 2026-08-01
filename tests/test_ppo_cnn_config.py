import json
import unittest
from pathlib import Path

from experiments.ppo_cnn_smallroom import REQUIRED_ACTIONS, load_config, normalize_craftium_action, validate_config
from experiments.run_smallroom_diagnostics import (
    choose_device,
    choose_parallelism,
    validate_config as validate_diagnostics_config,
)


CONFIG_PATH = Path(__file__).parents[1] / "experiments/configs/ppo_cnn_smallroom_dev.json"
DIAGNOSTIC_CONFIG_PATH = Path(__file__).parents[1] / "experiments/configs/smallroom_diagnostics_dev.json"


class PpoCnnConfigTests(unittest.TestCase):
    def test_scalar_ppo_action_is_made_a_craftium_discrete_action(self):
        class ScalarAction:
            ndim = 0

            def item(self):
                return 2

        self.assertEqual(normalize_craftium_action(ScalarAction()), 2)
        self.assertEqual(normalize_craftium_action(3), 3)
        self.assertEqual(normalize_craftium_action([1, 2]), [1, 2])

    def test_frozen_development_config_is_valid(self):
        config = load_config(CONFIG_PATH)
        validate_config(config)
        self.assertEqual(config["action_vocabulary"], REQUIRED_ACTIONS)
        self.assertEqual(config["device"], "cpu")

    def test_heldout_seed_and_gpu_are_rejected(self):
        config = load_config(CONFIG_PATH)
        config["evaluation_seeds"] = [500]
        with self.assertRaisesRegex(ValueError, "held-out"):
            validate_config(config)
        config = load_config(CONFIG_PATH)
        config["device"] = "cuda"
        with self.assertRaisesRegex(ValueError, "GPU"):
            validate_config(config)

    def test_config_is_json_and_has_positive_limits(self):
        config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        self.assertGreater(config["total_timesteps"], 0)
        self.assertGreater(config["max_episode_steps"], 0)

    def test_diagnostics_config_has_reproducibility_and_stop_guards(self):
        config = json.loads(DIAGNOSTIC_CONFIG_PATH.read_text(encoding="utf-8"))
        validate_diagnostics_config(config)
        self.assertEqual(config["ppo_timesteps"], [10000, 50000, 100000])
        self.assertEqual(config["throughput_parallelism"], [1, 2, 4, 8])
        self.assertGreaterEqual(config["minimum_free_disk_gib"], 4)

    def test_diagnostics_rejects_heldout_and_missing_lifecycle_guard(self):
        config = json.loads(DIAGNOSTIC_CONFIG_PATH.read_text(encoding="utf-8"))
        config["evaluation_seeds"] = [401]
        with self.assertRaisesRegex(ValueError, "held-out"):
            validate_diagnostics_config(config)
        config = json.loads(DIAGNOSTIC_CONFIG_PATH.read_text(encoding="utf-8"))
        config["safety"]["instance_lifecycle_forbidden"] = False
        with self.assertRaisesRegex(ValueError, "instance-lifecycle"):
            validate_diagnostics_config(config)

    def test_cuda_is_selected_only_for_material_measured_speedup(self):
        probes = [
            {"device": "cpu", "status": "complete", "steps_per_second": 100.0},
            {"device": "cuda", "status": "complete", "steps_per_second": 114.0},
        ]
        self.assertEqual(choose_device(probes, 1.15), "cpu")
        probes[1]["steps_per_second"] = 115.0
        self.assertEqual(choose_device(probes, 1.15), "cuda")

    def test_parallelism_uses_fastest_working_probe_with_safe_fallback(self):
        samples = [
            {"status": "complete", "parallelism": 1, "transitions_per_second": 100.0},
            {"status": "failed", "parallelism": 2, "error": "worker failed"},
            {"status": "complete", "parallelism": 4, "transitions_per_second": 220.0},
        ]
        self.assertEqual(choose_parallelism(samples), 4)
        self.assertEqual(choose_parallelism([]), 1)
