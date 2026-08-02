# Craftium SmallRoom oracle diagnostic (development only)

Date: 2026-08-03 (Asia/Singapore)

## Decision

The deterministic v2 oracle lower-bound exceeded its fixed random control,
but this does **not** validate the RGB agent or any product integration. It
shows only that a privileged, documented local Craftium state representation
plus shaped training reward can obtain some native-reward success on the frozen
SmallRoom task. Continue by turning this into a deterministic curriculum and
then testing RGB-derived state; do not scale compute or rent a GPU.

## Scope lock

- Runner commits: `a740c98d7468375fe5cc24d30c0e1f9f95bc93e3` (oracle
  runner) and `897b5b50a7fe084bb7af2edc219970fb26311768` (deterministic
  random-control correction).
- Environment: open-source `Craftium/SmallRoom-v0` at Craftium
  `8eb8707cb756df47e76131a0058ab724d2383c76`.
- Observation: documented local voxel-grid target offset and player yaw. This
  is explicitly marked `oracle_not_for_deployment`; it is not screen/OCR,
  mobile automation, or a permitted commercial-game adapter.
- Action allowlist: `nop`, `forward`, `mouse x+`, `mouse x-`.
- Training seed `0`; evaluation seeds `10--14`, all development seeds. No
  held-out seed, commercial game, account, networked player, portal EC2 host,
  new rental, or cloud lifecycle action was used.
- Existing worker only: Vast instance `45306784` via `ssh8.vast.ai:26784`,
  tmux `questpilot-oracle-v2-20260802` (completed). Workspace is ephemeral;
  artifacts were pulled to `/Users/suu/QuestPilot-Evidence/oracle-v2`.

## Configuration and guards

The CPU-only MLP PPO run used 10,000 requested / 10,240 actual steps (SB3
rollout rounding), learning rate 0.00025, 256 rollout steps, batch 64, four
epochs, gamma 0.99, GAE 0.95, clip 0.1, and entropy coefficient 0.01. Progress
shaping was used **only in training** (`4.0 * decrease in normalized target
distance`). Every reported evaluation return is the original native `-1` per
step reward. Guards: 7,200-second wall cap, 4-GiB free-disk floor, immutable
output directory, checkpoint every 5,000 steps, and off-box evidence sync.

## Result

| Metric | Deterministic v2 value |
| --- | ---: |
| Random native-reward mean | `-415.4` |
| Oracle-policy native-reward mean | `-313.2` |
| Difference | `+102.2` |
| Completed evaluation episodes | `2 / 5` |
| Train time | `339.533 s` |
| Train throughput | `30.159 steps/s` |
| Safe-stop reason | none |

Seed 11 terminated in 38 steps and seed 14 in 28 steps. Seeds 10, 12, and 13
truncated at 500 steps. The result beat the deterministic random baseline but
is far below a robust completion claim; it is a lower-bound diagnostic only.

## Failure retained and correction

Oracle v1 initially seeded each Craftium environment but did not seed Gym's
independent action-space RNG. Its random control was therefore not replayable,
so v1 is excluded from comparison. Commit `897b5b5` explicitly calls
`environment.action_space.seed(seed)` for each fixed control episode. V2 is the
only oracle comparison reported here.

## Evidence integrity and cost

The v2 local evidence hashes are:

- `result.json`: `05573a09a41c68fe420b4cb875e4dc33e02fd7f381241830d054886ca9de1f09`
- `random_control.json`: `a9d425fa3ac2f13c159b33f255d589174383e71ec6d522828c8e1886d9271758`
- `events.jsonl`: `e6221e19566284c00f20ed4a3e14edbbcdca2c5d24533ee103ca942d9178bb70`
- `oracle-v2-runner.log`: `b2fe3a2df22a5da71527fd2a1205dee4d7d43ee640317e972ad6a29c5024b3aa`

Incremental project spend was **US$0.00**. The GPU was not used: prior probes
showed only a 12.7% CUDA speedup, below the 15% gate, while simulator/evaluation
time remains the bottleneck.

## Next action

Freeze a deterministic target-distance curriculum and report seed-level
variance across multiple development training seeds. Only after that lower
bound is stable should an RGB-to-state perception module be trained and
compared with the same action vocabulary and native-reward evaluation.
