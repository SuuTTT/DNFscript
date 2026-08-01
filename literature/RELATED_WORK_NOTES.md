# Related-work extraction notes — QuestPilot-Safe

Search and source-verification date: 2026-08-01.

## Decision rule

No work is called a universal "SOTA" here. The meaningful frontier is conditional
on environment, observation channel, action API, compute, model/API budget, and
the definition of safety. A quoted score under a different interface is never
entered into a matched result table.

## Closest and strongest works inspected beyond abstracts

### Craftium (ICML 2025)

The paper's method and task details were inspected. Craftium exposes 64x64 RGB
observations and simplified discrete Luanti controls, and its source includes
PPO/PPO+LSTM and an illustrative LLaVA agent. Its single-agent PPO curves use
five runs and one million steps, but the authors explicitly describe these as
examples rather than tuned benchmarks. Its LLaVA agent receives the current
objective as text, then selects actions from a prompt; that is extra task access
relative to our screen-only condition. We adopt Craftium's four non-combat RGB
tasks for external coverage, not its illustrative numbers as a safety SOTA.

### Horizon Imagination (ICLR 2026)

The method and main control experiment were inspected. HI uses a 97M tokenizer,
world model, and actor-critic, evaluates ChopTree, Speleo, Room, and SmallRoom
over five seeds, and runs the Craftium tasks for 100K interactions (30K for
SmallRoom). The reported hardware includes A100, RTX 5090, RTX 4090, and A40
GPUs. Its paper evaluates diffusion-world-model efficiency and control return,
not unsafe actions or human approval. It is therefore the strongest *published
Craftium visual-RL comparator*, but only in a separately labelled
compute-unmatched tier until an equivalent resource budget is available.

### Voyager (arXiv 2023)

Voyager is the closest open-ended LLM-agent architecture: automatic curriculum,
skill library, iterative feedback, and GPT-4 code generation. It is not a matched
benchmark because it uses proprietary Minecraft and a black-box API/code-execution
loop. Its results inform a contextual LLM baseline, not a direct numerical claim.

## Baseline selection

The confirmatory table will contain the following prespecified systems:

1. PPO-CNN (classical visual-RL anchor; exact Craftium/CleanRL implementation).
2. PPO+LSTM (strong reproducible memory baseline from the Craftium source).
3. Horizon Imagination (published Craftium visual-RL frontier; resource-mismatch
   tier unless reproduced under a matched budget).
4. CPO-vision (CPO reimplemented on the same RGB/action interface with evaluator
   cost available only during training; not a screen oracle at inference).
5. HACO-style approval budget (human-takeover/approval protocol reimplemented on
   the same tasks; it may not access evaluator labels beyond an approval response).
6. Craftium LLaVA-style prompted policy or Voyager-style local planner, using one
   fixed local open model and a frozen prompt/action parser. It is an LLM baseline,
   not a paid-API comparison.

All except PPO-CNN/PPO+LSTM require a reproduction feasibility gate before final
inclusion. If a system cannot be reproduced under the frozen interface, it remains
a clearly labelled contextual/quoted comparison and cannot support a superiority
claim.

## Dataset selection

- **SmallRoom:** simple navigation/calibration.
- **Room:** larger randomized navigation.
- **Speleo:** vertical, long-horizon navigation and recovery.
- **ChopTree:** visual target selection plus an allowed local interaction.
- **ProcDungeons-safe:** procedural multi-room navigation and owned-object
  collection with `max_monsters_per_room=0`; no attack action is exposed.
- **SafeChores:** new held-out local fixture families for visual ambiguity,
  approval, and safe stop. See `docs/SAFECHORES_BENCHMARK_SPEC.md`.

SpidersAttack, Craftium combat examples, and open-world hunt/defend tracks are
excluded because they do not serve this safety/assistive-task claim.
