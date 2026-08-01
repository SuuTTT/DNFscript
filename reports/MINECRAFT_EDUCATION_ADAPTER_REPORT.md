# Minecraft Education adapter report

Date: 2026-08-01 (Asia/Singapore)

## Deliverable

Implementation commit:
`c9af35a9c7f5b63388364319d23701d7a4247dc6` on
`gpt-5/questpilot-phase1`.

`adapters/minecraft_education/questpilot_collection.ts` is a MakeCode
JavaScript script for Minecraft Education's publisher-supported Agent. It is a
human-stepped collection-lane exercise: `qp_start`, then at most eight manual
`qp_step` commands, and `qp_stop` for the hard stop. A step performs only
`agent.move` and `agent.collectAll`; a block ahead, the action cap, completion,
or `qp_stop` produces a visible `SAFE_STOP` message.

This is not a consumer-Minecraft, mobile-client, screen-scraping, or input
injection adapter. It uses native Agent detection as its observation mode,
while the Phase 1 mock remains the screen/OCR reference path.

## General framework

`questpilot.integration_gate` defines an adapter manifest with target,
environment, authorization reference, observation type, and explicit
capability allowlist. It rejects production environments and any request for
anti-cheat, CAPTCHA, credentials, chat, payments, trading, or PvP. The roadmap
records Minecraft Education now, and Screeps/Factorio as future native-interface
targets; a mobile adapter stays blocked without verifiable publisher authority.

## Validation

```text
PYTHONPATH=. python3 -m py_compile questpilot/*.py
PYTHONPATH=. python3 -m unittest discover -s tests -v
# 11 tests passed
PYTHONPATH=. python3 -m questpilot.benchmark
# fixed mock benchmark: 30/30, completion_rate=1.0, unsafe_actions=0
```

The test suite statically verifies the Minecraft script has start/stop commands,
uses `agent.collectAll`, contains no forever loop, and contains no `agent.attack`.
Minecraft Education itself is not installed or launched by CI, so final
in-game compatibility requires pasting the script into Code Builder in an
owned/demo world.

## Cost and next step

Incremental cost: **US$0.00**. No cloud VM, paid API, production game, or test
credential was used. Next: user runs the documented local/demo-world smoke test
and reports the visible MakeCode output; only then adjust compatibility issues
from that authorized environment.
