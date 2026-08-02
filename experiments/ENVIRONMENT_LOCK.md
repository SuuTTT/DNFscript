# QuestPilot-Safe environment lock (pre-installation)

This pre-registration lock records the environment actually available when the
research protocol was designed. It is **not** a claim that Craftium is installed
or that a training run has occurred.

| Component | Pin / state |
| --- | --- |
| Host | Apple M1 MacBook Air, 8 GB RAM |
| OS | macOS 26.2 (Darwin 25.2.0) |
| Luanti | 5.16.1, arm64, locally installed |
| Base game | Minetest Game, public source fetched only into ignored local test data |
| QuestPilot source base | `cf670461415e8a4c8b11be3b1d51410ffc4274fd` |
| Craftium | not installed; source commit and package checksum must be pinned before any experiment |
| Python/RL packages | not installed; exact versions must be recorded before any experiment |
| Network | local test world binds to `127.0.0.1` only |
| Cost ceiling | US$0.00; no paid APIs, compute rental, or commercial-game account |

## Execution-target denylist (2026-08-02)

`54.179.195.54` is the research-portal EC2 host, not an experiment worker.
It is explicitly **forbidden** for QuestPilot training, simulation, builds,
benchmark runs, model serving, or any other resource-intensive process. Do not
SSH to it, deploy to it, or use it as a fallback worker. Portal-card edits are
Git-only and do not authorize remote execution there.

The only approved remote experiment target recorded for the current
development-only Craftium work is the pre-existing Vast worker reached through
`ssh8.vast.ai:26784`. New capacity or any instance lifecycle action still
requires a separate explicit approval.

Any held-out result recorded under a different engine, mod, source SHA, package
lock, or action vocabulary is a new protocol and must not be pooled with the
pre-registered results without an explicit amendment.
