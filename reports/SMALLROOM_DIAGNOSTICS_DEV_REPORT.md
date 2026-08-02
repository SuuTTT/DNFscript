# Craftium SmallRoom diagnostic: measured development result

Date: 2026-08-02 (Asia/Singapore)  
Scope: development only. This is an open-source, single-player Craftium/Luanti
environment; it does not access a commercial game, account, networked player,
held-out seed, paid API, or new cloud capacity.

## Decision

Do **not** rent a GPU or continue this PPO configuration. The automatically
selected CPU was the right choice: CUDA improved the short end-to-end probe by
only 12.7%, below the frozen 15% selection threshold. More importantly, the
10k-step model returned `-500.0`, worse than the random control's `-395.2`.
The guarded monitor wrote `negative_10k_vs_random` and stopped the run before
the conditional 50k and 100k stages.

This is a negative, reproducible development diagnostic, not a performance or
SOTA claim. It gives us an evidence-backed next optimization target: the
observation/action/reward design and simulator/evaluation path, not more GPUs.

## Reproducibility lock

- Executed runner commit: `1a543be051c9d7d51cf822611bb2add2b44dc532`
- Stop-monitor commit: `655a32323eff62c6d1d9070971a30b441cbe3867`
- Craftium commit: `8eb8707cb756df47e76131a0058ab724d2383c76`
- Environment: `Craftium/SmallRoom-v0`; `64 x 64 x 3` RGB only
- Native allowlist: `nop`, `forward`, `mouse x+`, `mouse x-`
- Development train seed: `0`; evaluation seeds: `10, 11, 12, 13, 14`
  (all in the frozen development range `0..399`)
- PPO: learning rate `0.00025`, `n_steps=256`, batch `64`, 4 epochs,
  gamma `0.99`, GAE lambda `0.95`, clip range `0.1`, entropy coefficient `0.01`
- Global wall-clock cap: 27,000 seconds; free-disk stop guard: 4 GiB

The actual run used existing Vast instance `45306784` through
`ssh8.vast.ai:26784`, in tmux sessions
`questpilot-diagnostics-v4-20260802` and
`questpilot-early-stop-v4-20260802`. Both sessions had stopped cleanly when
checked. The workspace was explicitly treated as ephemeral and the evidence
bundle was pulled off-box immediately. No instance lifecycle operation was
performed.

Host snapshot: 56 vCPU, 64 GiB RAM, one NVIDIA GeForce RTX 3060 (12 GiB),
Python 3.11.9, PyTorch 2.4.1+cu124, and 11.3 GiB free disk at run start.

## Timing and result log

| Stage | Device / execution | Result |
| --- | --- | --- |
| Random control | serial | mean return `-395.2` across five seeds |
| Simulator throughput | `SubprocVecEnv` spawn, 1 worker | 39.879 transitions/s (64 transitions in 1.605 s) |
| Device probe | CPU, 2,048 actual steps | 8.792 end-to-end steps/s; 232.929 s; mean return `-500.0` |
| Device probe | CUDA, 2,048 actual steps | 9.909 end-to-end steps/s; 206.691 s; mean return `-500.0` |
| Selected training | CPU, requested 10,000 / actual 10,240 steps | 16.420 steps/s; 623.642 s; mean return `-500.0`; 0/5 completions |

CUDA's probe ratio was `1.127` (`9.909 / 8.792`), below the configured `1.15`
threshold, so CPU was selected deterministically. All five trained-policy
episodes truncated at the 500-step cap; none terminated. The 10k stage was
therefore below random by 104.8 reward points. The 50k and 100k values in the
config were conditional candidates, **not completed runs**.

Parallelism 2+ was deliberately excluded from the final timing loop. A prior
Xvfb-backed Craftium probe closed Luanti peer connections at two spawned
environments; the config freezes a serial fallback rather than hiding that
failure with unreliable data.

## Commands and recoveries

The bounded runner command was:

```text
xvfb-run -a .venv/bin/python experiments/run_smallroom_diagnostics.py \
  --config experiments/configs/smallroom_diagnostics_dev.json \
  --output-dir /workspace/questpilot-diagnostics-20260802/diagnostics-output-v4
```

The external, narrow stop monitor read only `progress.json` and
`random_control.json`, and could kill only a tmux session whose name starts
`questpilot-`. It stopped the sweep after the first completed 10k stage.

Recovery observations retained in the failure ledger:

1. The initial candidate repository was not the Craftium source; the pinned
   upstream source was used instead.
2. Headless rendering first lacked OpenGL/SDL/Freetype/Xvfb dependencies. They
   were installed only on the already-approved worker, and the normal visible
   UI was exercised through Xvfb without anti-cheat or game modification.
3. Parallel Xvfb Craftium lost peer connections at two environments. The run
   fell back to one spawned environment and records that restriction.
4. A missing TensorBoard dependency stopped one pre-training attempt. It was
   installed, then the valid v4 run was started from a fresh immutable output
   directory.

## Evidence and integrity

The local pull-only evidence bundle is
`/private/tmp/questpilot-diagnostics-artifacts-20260802/v4`. SHA-256:

- `config.snapshot.json`: `3fbff9ad4f41650bd5c3c52c10a2f9a20f838efec1e89d79117351fc3b46f475`
- `manifest.json`: `59b61212057da3fec6802b65b5bd6066983a27200164e3b89e1d06a263dd11c7`
- `random_control.json`: `e3db9041ddb9810eb8473d6b30e0a10ffdf25a726c5b32bb146ac5a0e8220c89`
- `throughput.json`: `c6bd76ac0c6a2972c001d8009201981a841ad8c935e5d7b759f6d064e79c6d71`
- `device_selection.json`: `194a6a2f071001e4e38c95a1b0e5affde414330a41c11b7d6c7803ed2f12d6ae`
- `progress.json`: `a69a3c242990a78670f35388d966e5f842c3b4faa2a1b76b852490ea98aea15c`
- `early_stop_reason.txt`: `92cd71075260a8430b103081573c9d865ce212b32c43a2c6abf5f07edc78cea0`
- `events.jsonl`: `601050341bf22e785633bc4ad5ea08468148891d250412ba957e80949a8c58eb`
- `ppo_0010000_cpu/model.zip`: `014dcf1202ae83c632bb59f97f1639702b31df7a0822d7d98d345b9aa316b77b`
- `diagnostics-v4-runner.log`: `62ad7057f57bcbec33eb88d60b36ebcc391aba3aa420466bbc272cd6deb7e5eb`

## Cost and next milestone

Incremental project spend: **US$0.00**. No GPU was rented, and no provider
lifecycle action was requested. Existing-instance billing is outside this
project's incremental cost accounting.

The next bounded development milestone is to add a compact state-oriented
observation/action diagnostic (with controlled reward and curriculum variants),
measure simulator versus end-to-end evaluation time again, and require a
development-only result above the fixed random control before scaling training.
Keep the same stop monitor, artifact pull, time/disk limits, and no-heldout
policy. Do not rent a GPU until that diagnostic shows a material end-to-end
benefit.
