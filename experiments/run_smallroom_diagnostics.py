"""Reproducible, development-only Craftium SmallRoom diagnostic launcher.

This launcher is for an open-source, single-player benchmark only.  It never
opens held-out seeds or commercial games.  It creates immutable run snapshots,
bounded checkpoints, JSONL/TensorBoard evidence, and resource-stop events.
"""
from __future__ import annotations

import argparse
import copy
import importlib.metadata
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from functools import partial
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
    if config.get("action_vocabulary") != REQUIRED_ACTIONS:
        raise ValueError("action vocabulary must remain the frozen SmallRoom allowlist")
    environment_kwargs = config.get("environment_kwargs")
    if not isinstance(environment_kwargs, dict) or not isinstance(environment_kwargs.get("offscreen_sdl"), bool):
        raise ValueError("an explicit offscreen_sdl environment setting is required")
    seeds = [config.get("train_seed"), *config.get("evaluation_seeds", [])]
    if any(not isinstance(seed, int) or seed not in DEVELOPMENT_SEEDS for seed in seeds):
        raise ValueError("held-out or invalid seeds are forbidden")
    if config.get("max_episode_steps", 0) <= 0 or config.get("max_wall_seconds", 0) <= 0:
        raise ValueError("positive episode and wall-clock limits are required")
    if config.get("minimum_free_disk_gib", -1) < 4:
        raise ValueError("at least 4 GiB of free-disk guard is required")
    if not config.get("safety", {}).get("heldout_seeds_forbidden"):
        raise ValueError("held-out seed guard is required")
    if not config.get("safety", {}).get("new_rental_forbidden"):
        raise ValueError("new-rental guard is required")
    if not config.get("safety", {}).get("instance_lifecycle_forbidden"):
        raise ValueError("instance-lifecycle guard is required")
    if not config.get("safety", {}).get("output_sync_required"):
        raise ValueError("output-sync requirement is required")
    if any(device not in {"cpu", "cuda"} for device in config.get("device_order", [])):
        raise ValueError("only cpu and cuda devices are supported")
    if not config.get("ppo_timesteps") or min(config["ppo_timesteps"]) <= 0:
        raise ValueError("positive PPO step budgets are required")


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


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def host_snapshot(torch: Any) -> dict[str, Any]:
    disk = shutil.disk_usage(".")
    ram_total = os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")
    snapshot: dict[str, Any] = {
        "platform": platform.platform(),
        "python": sys.version.split()[0],
        "pid": os.getpid(),
        "cpu_count": os.cpu_count(),
        "ram_total_bytes": ram_total,
        "free_disk_bytes": disk.free,
        "torch_version": torch.__version__,
        "cuda_available": bool(torch.cuda.is_available()),
    }
    if torch.cuda.is_available():
        snapshot["cuda_device_count"] = torch.cuda.device_count()
        snapshot["cuda_name"] = torch.cuda.get_device_name(0)
    return snapshot


def choose_device(probes: list[dict[str, Any]], minimum_cuda_speedup: float) -> str:
    by_device = {probe["device"]: probe for probe in probes if probe.get("status") == "complete"}
    cpu = by_device.get("cpu")
    cuda = by_device.get("cuda")
    if not cpu or not cuda:
        return "cpu"
    if cuda["steps_per_second"] >= cpu["steps_per_second"] * minimum_cuda_speedup:
        return "cuda"
    return "cpu"


def choose_parallelism(samples: list[dict[str, Any]]) -> int:
    complete = [sample for sample in samples if sample.get("status") == "complete"]
    if not complete:
        return 1
    return int(max(complete, key=lambda sample: sample["transitions_per_second"])["parallelism"])


def normalize_craftium_action(action: Any) -> Any:
    if (getattr(action, "size", None) == 1 or getattr(action, "ndim", None) == 0) and hasattr(action, "item"):
        return int(action.item())
    return int(action) if isinstance(action, int) else action


def make_smallroom_environment(max_episode_steps: int, environment_kwargs: dict[str, Any]) -> Any:
    """Top-level factory so ``SubprocVecEnv(..., start_method='spawn')`` can pickle it."""
    import craftium  # noqa: F401 - child process must also register the environment
    import gymnasium as gym

    return gym.make("Craftium/SmallRoom-v0", max_timesteps=max_episode_steps, **environment_kwargs)


def evaluate(model: Any, gym: Any, seeds: list[int], max_episode_steps: int,
             environment_kwargs: dict[str, Any]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for seed in seeds:
        environment = gym.make("Craftium/SmallRoom-v0", max_timesteps=max_episode_steps,
                               **environment_kwargs)
        try:
            observation, _ = environment.reset(seed=seed)
            reward_sum, steps = 0.0, 0
            terminated = truncated = False
            while steps < max_episode_steps and not (terminated or truncated):
                action, _ = model.predict(observation, deterministic=True)
                observation, reward, terminated, truncated, _ = environment.step(normalize_craftium_action(action))
                reward_sum += float(reward)
                steps += 1
            results.append({"seed": seed, "steps": steps, "reward_sum": reward_sum,
                            "terminated": bool(terminated), "truncated": bool(truncated)})
        finally:
            environment.close()
    return results


def random_control(gym: Any, config: dict[str, Any]) -> dict[str, Any]:
    episodes: list[dict[str, Any]] = []
    for seed in config["evaluation_seeds"]:
        environment = gym.make(config["environment"], max_timesteps=config["max_episode_steps"],
                               **config["environment_kwargs"])
        try:
            observation, _ = environment.reset(seed=seed)
            del observation
            reward_sum, steps = 0.0, 0
            terminated = truncated = False
            while steps < config["max_episode_steps"] and not (terminated or truncated):
                _, reward, terminated, truncated, _ = environment.step(environment.action_space.sample())
                reward_sum += float(reward)
                steps += 1
            episodes.append({"seed": seed, "steps": steps, "reward_sum": reward_sum,
                             "terminated": bool(terminated), "truncated": bool(truncated)})
        finally:
            environment.close()
    return {"policy": "random", "episodes": episodes,
            "mean_return": sum(item["reward_sum"] for item in episodes) / len(episodes)}


def throughput_probe(gym: Any, config: dict[str, Any], parallelism: int) -> dict[str, Any]:
    """Measure independent Craftium simulators in actual spawned worker processes."""
    from stable_baselines3.common.vec_env import SubprocVecEnv

    environment_fns = [partial(make_smallroom_environment, config["max_episode_steps"], config["environment_kwargs"])
                       for _ in range(parallelism)]
    environment = SubprocVecEnv(environment_fns, start_method="spawn")
    try:
        environment.seed(config["train_seed"])
        environment.reset()
        transitions = parallelism * config["throughput_steps_per_environment"]
        started = time.monotonic()
        for _ in range(config["throughput_steps_per_environment"]):
            actions = [environment.action_space.sample() for _ in range(parallelism)]
            environment.step(actions)
        wall_seconds = time.monotonic() - started
        return {"parallelism": parallelism, "transitions": transitions,
                "wall_seconds": round(wall_seconds, 6),
                "transitions_per_second": transitions / wall_seconds,
                "execution": "SubprocVecEnv-spawn"}
    finally:
        environment.close()


def _run_ppo(PPO: Any, Monitor: Any, gym: Any, config: dict[str, Any], run_dir: Path,
             device: str, total_timesteps: int, event_log: Path, parallelism: int) -> dict[str, Any]:
    from stable_baselines3.common.callbacks import BaseCallback, CheckpointCallback
    from stable_baselines3.common.vec_env import SubprocVecEnv, VecMonitor

    started = time.monotonic()
    min_free_bytes = config["minimum_free_disk_gib"] * 1024 ** 3

    class GuardedMetricsCallback(BaseCallback):
        def __init__(self) -> None:
            super().__init__()
            self.last_steps = 0
            self.last_time = started
            self.stop_reason: str | None = None

        def _on_step(self) -> bool:
            elapsed = time.monotonic() - started
            free = shutil.disk_usage(run_dir).free
            if elapsed >= config["max_wall_seconds"]:
                self.stop_reason = "wall_clock_cap"
            elif free < min_free_bytes:
                self.stop_reason = "free_disk_guard"
            if self.stop_reason:
                _append_jsonl(event_log, {"event": "safe_stop", "reason": self.stop_reason,
                                          "timesteps": self.num_timesteps, "elapsed_seconds": elapsed,
                                          "free_disk_bytes": free})
                return False
            if self.num_timesteps - self.last_steps >= 1024:
                now = time.monotonic()
                _append_jsonl(event_log, {"event": "progress", "timesteps": self.num_timesteps,
                                          "elapsed_seconds": now - started,
                                          "recent_steps_per_second": (self.num_timesteps - self.last_steps) / (now - self.last_time),
                                          "free_disk_bytes": free})
                self.last_steps, self.last_time = self.num_timesteps, now
            return True

    if parallelism == 1:
        environment: Any = Monitor(gym.make(config["environment"], max_timesteps=config["max_episode_steps"],
                                             **config["environment_kwargs"]))
    else:
        environment = VecMonitor(SubprocVecEnv(
            [partial(make_smallroom_environment, config["max_episode_steps"], config["environment_kwargs"])
             for _ in range(parallelism)],
            start_method="spawn",
        ))
    callback = GuardedMetricsCallback()
    checkpoint = CheckpointCallback(
        save_freq=max(1, config["checkpoint_interval"] // parallelism),
        save_path=str(run_dir / "checkpoints"),
        name_prefix="ppo_cnn_smallroom",
    )
    try:
        model = PPO("CnnPolicy", environment, seed=config["train_seed"], device=device, verbose=0,
                    tensorboard_log=str(run_dir / "tensorboard"), **config["ppo"])
        model.learn(total_timesteps=total_timesteps, callback=[callback, checkpoint], progress_bar=False)
        model.save(str(run_dir / "model"))
        evaluation = evaluate(model, gym, config["evaluation_seeds"], config["max_episode_steps"],
                              config["environment_kwargs"])
    finally:
        environment.close()
    wall_seconds = time.monotonic() - started
    actual_steps = callback.num_timesteps
    result = {
        "device": device, "parallelism": parallelism, "requested_timesteps": total_timesteps,
        "actual_timesteps": actual_steps,
        "wall_seconds": round(wall_seconds, 6),
        "steps_per_second": actual_steps / wall_seconds if wall_seconds else 0.0,
        "safe_stop_reason": callback.stop_reason, "evaluation": evaluation,
        "mean_return": sum(item["reward_sum"] for item in evaluation) / len(evaluation),
        "completion_count": sum(1 for item in evaluation if item["terminated"]),
    }
    _append_jsonl(event_log, {"event": "completed", **result})
    return result


def run(config: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    validate_config(config)
    import craftium  # noqa: F401 - registers environments
    import gymnasium as gym
    import torch
    from stable_baselines3 import PPO
    from stable_baselines3.common.monitor import Monitor

    output_dir.mkdir(parents=True, exist_ok=False)
    event_log = output_dir / "events.jsonl"
    _write_json(output_dir / "config.snapshot.json", config)
    _write_json(output_dir / "seed_manifest.json", {
        "phase": "development", "train_seed": config["train_seed"],
        "evaluation_seeds": config["evaluation_seeds"], "heldout_seeds_inspected": False,
    })
    _write_json(output_dir / "manifest.json", {
        "run_id": config["run_id"], "code_commit": _git_head(), "craftium_commit": config["craftium_commit"],
        "versions": _versions(), "host": host_snapshot(torch), "started_at_unix": time.time(),
        "workspace_sync_required": True,
    })
    _append_jsonl(event_log, {"event": "started", "host": host_snapshot(torch)})

    throughput: list[dict[str, Any]] = []
    for amount in config["throughput_parallelism"]:
        try:
            throughput.append({"status": "complete", **throughput_probe(gym, config, amount)})
        except Exception as error:
            throughput.append({"status": "failed", "parallelism": amount, "error": repr(error)})
            _append_jsonl(event_log, {"event": "throughput_probe_failed", "parallelism": amount,
                                      "error": repr(error)})
    _write_json(output_dir / "throughput.json", {"samples": throughput})
    selected_parallelism = choose_parallelism(throughput)
    random = random_control(gym, config)
    _write_json(output_dir / "random_control.json", random)

    probes: list[dict[str, Any]] = []
    for device in config["device_order"]:
        if device == "cuda" and not torch.cuda.is_available():
            probes.append({"device": "cuda", "status": "skipped", "reason": "cuda_unavailable"})
            continue
        probe_dir = output_dir / "device_probes" / device
        probe_dir.mkdir(parents=True)
        try:
            probe = _run_ppo(PPO, Monitor, gym, config, probe_dir, device,
                             config["device_probe_timesteps"], event_log, parallelism=1)
            probes.append({"device": device, "status": "complete", **probe})
        except Exception as error:  # Evidence must preserve device failures, then safely prefer CPU.
            probes.append({"device": device, "status": "failed", "error": repr(error)})
            _append_jsonl(event_log, {"event": "device_probe_failed", "device": device, "error": repr(error)})
    selected_device = choose_device(probes, config["minimum_cuda_speedup"])
    _write_json(output_dir / "device_selection.json", {"probes": probes, "selected_device": selected_device,
                                                         "selected_parallelism": selected_parallelism,
                                                         "minimum_cuda_speedup": config["minimum_cuda_speedup"]})

    runs: list[dict[str, Any]] = []
    for budget in config["ppo_timesteps"]:
        run_dir = output_dir / f"ppo_{budget:07d}_{selected_device}"
        run_dir.mkdir(parents=True)
        result = _run_ppo(PPO, Monitor, gym, config, run_dir, selected_device, budget, event_log,
                          parallelism=selected_parallelism)
        result["budget"] = budget
        runs.append(result)
        _write_json(output_dir / "progress.json", {"selected_device": selected_device,
                                                     "selected_parallelism": selected_parallelism, "runs": runs})
        if result["safe_stop_reason"]:
            break
    report = {"run_id": config["run_id"], "selected_device": selected_device,
              "selected_parallelism": selected_parallelism, "throughput": throughput,
              "random_control": random, "runs": runs, "heldout_seeds_inspected": False,
              "commercial_game_interaction": False, "incremental_project_cost_usd": 0.0}
    _write_json(output_dir / "result.json", report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path,
                        default=REPO_ROOT / "experiments/configs/smallroom_diagnostics_dev.json")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(load_config(args.config), args.output_dir), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
