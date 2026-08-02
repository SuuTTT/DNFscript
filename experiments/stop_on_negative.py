"""Stop one named QuestPilot tmux run when the 10k PPO result fails its random control."""
from __future__ import annotations

import argparse
import json
import subprocess
import time
from pathlib import Path


def should_stop(run_dir: Path) -> bool:
    progress = run_dir / "progress.json"
    control = run_dir / "random_control.json"
    if not progress.exists() or not control.exists():
        return False
    latest = json.loads(progress.read_text(encoding="utf-8")).get("runs", [])
    if not latest or latest[-1].get("budget") != 10000:
        return False
    random_mean = json.loads(control.read_text(encoding="utf-8"))["mean_return"]
    return float(latest[-1]["mean_return"]) <= float(random_mean)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--session", required=True)
    parser.add_argument("--interval-seconds", type=float, default=30.0)
    args = parser.parse_args()
    if not args.session.startswith("questpilot-"):
        raise ValueError("refusing to control a non-QuestPilot tmux session")
    while True:
        if should_stop(args.run_dir):
            (args.run_dir / "early_stop_reason.txt").write_text(
                "negative_10k_vs_random\n", encoding="utf-8"
            )
            subprocess.run(["tmux", "kill-session", "-t", args.session], check=False)
            return
        time.sleep(args.interval_seconds)


if __name__ == "__main__":
    main()
