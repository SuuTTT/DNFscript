"""Bounded development-only oracle lower-bound for Craftium SmallRoom.

The wrapper consumes Craftium's documented local voxel observation and player
pose. It is deliberately not a QuestPilot deployment path: privileged state is
used only to test whether the frozen task/action/reward interface is learnable.
"""
from __future__ import annotations

import argparse
import importlib.metadata
import json
import math
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEVELOPMENT_SEEDS = range(0, 400)
REQUIRED_ACTIONS = ["nop", "forward", "mouse x+", "mouse x-"]


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_jsonl(path: Path, value: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(value, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def validate_config(config: dict[str, Any]) -> None:
    if config.get("phase") != "development" or config.get("benchmark_role") != "non_deployable_oracle_lower_bound":
        raise ValueError("only the development-only oracle lower bound is permitted")
    if config.get("environment") != "Craftium/SmallRoom-v0":
        raise ValueError("only Craftium SmallRoom is permitted")
    if config.get("action_vocabulary") != REQUIRED_ACTIONS:
        raise ValueError("the SmallRoom action allowlist is immutable")
    kwargs = config.get("environment_kwargs", {})
    if not kwargs.get("enable_voxel_obs") or kwargs.get("offscreen_sdl") is not False:
        raise ValueError("explicit local voxel observations and Xvfb-compatible rendering are required")
    seeds = [config.get("train_seed"), *config.get("evaluation_seeds", [])]
    if any(not isinstance(seed, int) or seed not in DEVELOPMENT_SEEDS for seed in seeds):
        raise ValueError("held-out or invalid seed is forbidden")
    required = ("heldout_seeds_forbidden", "commercial_games_forbidden", "networked_players_forbidden",
                "new_rental_forbidden", "instance_lifecycle_forbidden", "output_sync_required", "oracle_not_for_deployment")
    if not all(config.get("safety", {}).get(name) for name in required):
        raise ValueError("required safety guard is missing")
    if config.get("train_timesteps", 0) <= 0 or config.get("max_wall_seconds", 0) <= 0:
        raise ValueError("positive time and train limits are required")
    if config.get("minimum_free_disk_gib", -1) < 4:
        raise ValueError("free-disk guard must be at least 4 GiB")


def oracle_state(info: dict[str, Any], target_node_id: int) -> tuple[Any, float]:
    """Return normalized North/East target offset and yaw; reject ambiguous state."""
    import numpy as np

    voxels = np.asarray(info.get("voxel_obs"))
    if voxels.ndim != 4 or voxels.shape[-1] < 1:
        raise ValueError("voxel observation unavailable")
    locations = np.argwhere(voxels[..., 0] == target_node_id)
    if len(locations) != 1:
        raise ValueError(f"expected exactly one target node {target_node_id}, got {len(locations)}")
    location = locations[0].astype(np.float32)
    center = (np.asarray(voxels.shape[:3], dtype=np.float32) - 1.0) / 2.0
    offset = (location - center) / np.maximum(center, 1.0)
    yaw = math.radians(float(info.get("player_yaw", 0.0)))
    state = np.asarray([offset[0], offset[2], math.sin(yaw), math.cos(yaw)], dtype=np.float32)
    return state, float(math.hypot(offset[0], offset[2]))


def make_oracle_environment(config: dict[str, Any], shaped: bool) -> Any:
    """Create lazily so static tests do not require Craftium or Gymnasium."""
    import numpy as np
    import craftium  # noqa: F401  # Registers environments.
    import gymnasium as gym
    from gymnasium import Wrapper
    from gymnasium.spaces import Box

    class OracleStateWrapper(Wrapper):
        def __init__(self, environment: Any) -> None:
            super().__init__(environment)
            self.observation_space = Box(low=-1.0, high=1.0, shape=(4,), dtype=np.float32)
            self.previous_distance: float | None = None

        def reset(self, **kwargs: Any) -> tuple[np.ndarray, dict[str, Any]]:
            _rgb, info = self.env.reset(**kwargs)
            state, self.previous_distance = oracle_state(info, int(config["target_node_id"]))
            return state, info

        def step(self, action: Any) -> tuple[np.ndarray, float, bool, bool, dict[str, Any]]:
            _rgb, reward, terminated, truncated, info = self.env.step(action)
            state, distance = oracle_state(info, int(config["target_node_id"]))
            if shaped and self.previous_distance is not None:
                reward = float(reward) + float(config["progress_shaping_scale"]) * (self.previous_distance - distance)
            self.previous_distance = distance
            return state, float(reward), terminated, truncated, info

    base = gym.make(config["environment"], max_timesteps=config["max_episode_steps"], **config["environment_kwargs"])
    return OracleStateWrapper(base)


def rollout(model: Any | None, config: dict[str, Any], random_policy: bool) -> list[dict[str, Any]]:
    """Always calculate reported return under native, unshaped environment reward."""
    import numpy as np

    episodes: list[dict[str, Any]] = []
    for seed in config["evaluation_seeds"]:
        environment = make_oracle_environment(config, shaped=False)
        try:
            state, _info = environment.reset(seed=seed)
            # Gym's action-space RNG is independent of Env.reset(seed=...).
            # Seed it explicitly so the fixed random-control policy is replayable.
            environment.action_space.seed(seed)
            reward_sum, steps, terminated, truncated = 0.0, 0, False, False
            while steps < config["max_episode_steps"] and not (terminated or truncated):
                action = environment.action_space.sample() if random_policy else model.predict(state, deterministic=True)[0]
                state, reward, terminated, truncated, _info = environment.step(int(np.asarray(action).item()))
                reward_sum += reward
                steps += 1
            episodes.append({"seed": seed, "steps": steps, "reward_sum": reward_sum,
                             "terminated": bool(terminated), "truncated": bool(truncated)})
        finally:
            environment.close()
    return episodes


def git_head() -> str | None:
    result = subprocess.run(["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"], capture_output=True, text=True, check=False)
    return result.stdout.strip() if result.returncode == 0 else None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    arguments = parser.parse_args()
    config = json.loads(arguments.config.read_text(encoding="utf-8"))
    validate_config(config)
    output = arguments.output_dir
    if output.exists():
        raise FileExistsError(f"immutable output directory already exists: {output}")
    output.mkdir(parents=True)
    minimum_free = int(config["minimum_free_disk_gib"]) * 1024 ** 3
    if shutil.disk_usage(output).free < minimum_free:
        raise RuntimeError("free-disk guard triggered before launch")
    started, deadline = time.monotonic(), time.monotonic() + float(config["max_wall_seconds"])
    write_json(output / "config.snapshot.json", config)
    write_json(output / "seed_manifest.json", {"phase": "development", "train_seed": config["train_seed"],
                                                  "evaluation_seeds": config["evaluation_seeds"], "heldout_seeds_inspected": False})
    write_json(output / "manifest.json", {"run_id": config["run_id"], "code_commit": git_head(),
                                            "started_at_unix": time.time(), "platform": platform.platform(),
                                            "python": sys.version.split()[0], "versions": {name: importlib.metadata.version(name) for name in ("craftium", "gymnasium", "stable-baselines3", "torch")},
                                            "workspace_sync_required": True, "oracle_not_for_deployment": True})
    events = output / "events.jsonl"
    append_jsonl(events, {"event": "started", "deadline_seconds": config["max_wall_seconds"], "free_disk_bytes": shutil.disk_usage(output).free})
    control_episodes = rollout(None, config, random_policy=True)
    control_mean = sum(item["reward_sum"] for item in control_episodes) / len(control_episodes)
    write_json(output / "random_control.json", {"policy": "random_native_reward", "episodes": control_episodes, "mean_return": control_mean})
    if time.monotonic() >= deadline:
        write_json(output / "safe_stop.json", {"reason": "wall_clock_cap_before_training"})
        return 0
    from stable_baselines3 import PPO
    from stable_baselines3.common.callbacks import BaseCallback, CheckpointCallback
    environment = make_oracle_environment(config, shaped=True)

    class Guard(BaseCallback):
        def __init__(self) -> None:
            super().__init__()
            self.reason: str | None = None
        def _on_step(self) -> bool:
            if time.monotonic() >= deadline:
                self.reason = "wall_clock_cap"
            elif shutil.disk_usage(output).free < minimum_free:
                self.reason = "free_disk_guard"
            if self.reason:
                append_jsonl(events, {"event": "safe_stop", "reason": self.reason, "timesteps": self.num_timesteps})
                return False
            return True

    guard = Guard()
    checkpoint = CheckpointCallback(save_freq=int(config["checkpoint_interval"]), save_path=str(output / "checkpoints"), name_prefix="ppo_oracle_smallroom")
    model = PPO("MlpPolicy", environment, seed=int(config["train_seed"]), verbose=0, device="cpu", **config["ppo"])
    train_started = time.monotonic()
    model.learn(total_timesteps=int(config["train_timesteps"]), callback=[guard, checkpoint])
    actual_steps, train_seconds = int(model.num_timesteps), time.monotonic() - train_started
    model.save(str(output / "ppo_oracle_smallroom"))
    evaluation = rollout(model, config, random_policy=False)
    native_mean = sum(item["reward_sum"] for item in evaluation) / len(evaluation)
    result = {"requested_timesteps": config["train_timesteps"], "actual_timesteps": actual_steps, "train_wall_seconds": train_seconds,
              "train_steps_per_second": actual_steps / train_seconds, "evaluation": evaluation, "native_mean_return": native_mean,
              "completion_count": sum(item["terminated"] for item in evaluation), "random_control_mean_return": control_mean,
              "safe_stop_reason": guard.reason, "beats_random": native_mean > control_mean, "oracle_not_for_deployment": True}
    write_json(output / "result.json", result)
    append_jsonl(events, {"event": "completed", **result})
    environment.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
