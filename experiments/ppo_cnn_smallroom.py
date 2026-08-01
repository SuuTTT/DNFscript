"""Development-only, CPU-only PPO-CNN baseline for Craftium SmallRoom.

This runner deliberately refuses held-out seeds and GPU devices. It is a
reproducibility pilot, not a safety claim or a commercial-game integration.
"""
from __future__ import annotations

import argparse
import importlib.metadata
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEVELOPMENT_SEEDS = range(0, 400)
REQUIRED_ACTIONS = ["nop", "forward", "mouse x+", "mouse x-"]


def load_config(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_config(config: dict[str, Any]) -> None:
    if config.get("phase") != "development":
        raise ValueError("only development phase is permitted")
    if config.get("environment") != "Craftium/SmallRoom-v0":
        raise ValueError("only the non-combat SmallRoom environment is permitted")
    if config.get("device") != "cpu" or config.get("safety", {}).get("allow_gpu"):
        raise ValueError("GPU execution is forbidden for this development pilot")
    if config.get("action_vocabulary") != REQUIRED_ACTIONS:
        raise ValueError("action vocabulary must remain the frozen SmallRoom allowlist")
    seeds = [config.get("seed"), *config.get("evaluation_seeds", [])]
    if any(not isinstance(seed, int) or seed not in DEVELOPMENT_SEEDS for seed in seeds):
        raise ValueError("held-out or invalid seeds are forbidden")
    if config.get("total_timesteps", 0) <= 0 or config.get("max_episode_steps", 0) <= 0:
        raise ValueError("positive training and episode limits are required")


def _git_head() -> str | None:
    result = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def _versions() -> dict[str, str]:
    names = ("craftium", "gymnasium", "stable-baselines3", "torch")
    return {name: importlib.metadata.version(name) for name in names}


def evaluate(model: Any, gym: Any, seeds: list[int], max_episode_steps: int) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for seed in seeds:
        environment = gym.make("Craftium/SmallRoom-v0", max_timesteps=max_episode_steps)
        try:
            observation, _ = environment.reset(seed=seed)
            reward_sum = 0.0
            terminated = truncated = False
            steps = 0
            while steps < max_episode_steps and not (terminated or truncated):
                action, _ = model.predict(observation, deterministic=True)
                observation, reward, terminated, truncated, _ = environment.step(action)
                reward_sum += float(reward)
                steps += 1
            results.append(
                {
                    "seed": seed,
                    "steps": steps,
                    "reward_sum": reward_sum,
                    "terminated": bool(terminated),
                    "truncated": bool(truncated),
                }
            )
        finally:
            environment.close()
    return results


def run(config: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    validate_config(config)
    # Imports are intentionally delayed: local safety/config tests need no ML stack.
    import craftium  # noqa: F401  # registers the Gymnasium environments
    import gymnasium as gym
    from stable_baselines3 import PPO
    from stable_baselines3.common.monitor import Monitor

    output_dir.mkdir(parents=True, exist_ok=False)
    started = time.time()
    manifest = {
        "run_id": config["run_id"],
        "phase": config["phase"],
        "code_commit": _git_head(),
        "craftium_commit": config["craftium_commit"],
        "versions": _versions(),
        "config": config,
        "started_at_unix": started,
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    environment = Monitor(
        gym.make("Craftium/SmallRoom-v0", max_timesteps=config["max_episode_steps"])
    )
    try:
        model = PPO(
            "CnnPolicy",
            environment,
            seed=config["seed"],
            device="cpu",
            verbose=1,
            tensorboard_log=str(output_dir / "tensorboard"),
            **config["ppo"],
        )
        model.learn(total_timesteps=config["total_timesteps"], progress_bar=False)
        evaluation = evaluate(model, gym, config["evaluation_seeds"], config["max_episode_steps"])
        model.save(str(output_dir / "ppo_cnn_smallroom"))
    finally:
        environment.close()

    report = {
        "run_id": config["run_id"],
        "suite": "Craftium/SmallRoom-v0 development pilot",
        "device": "cpu",
        "training_timesteps": config["total_timesteps"],
        "evaluation": evaluation,
        "wall_seconds": round(time.time() - started, 3),
        "heldout_seeds_inspected": False,
        "commercial_game_interaction": False,
    }
    (output_dir / "result.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        type=Path,
        default=REPO_ROOT / "experiments/configs/ppo_cnn_smallroom_dev.json",
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    report = run(load_config(args.config), args.output_dir)
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
