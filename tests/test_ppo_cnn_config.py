import json
import unittest
from pathlib import Path

from experiments.ppo_cnn_smallroom import REQUIRED_ACTIONS, load_config, normalize_craftium_action, validate_config


CONFIG_PATH = Path(__file__).parents[1] / "experiments/configs/ppo_cnn_smallroom_dev.json"


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
