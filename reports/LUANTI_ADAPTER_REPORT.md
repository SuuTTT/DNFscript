# Luanti adapter report

Date: 2026-08-01 (Asia/Singapore)

## Deliverable

Implementation commit:
`ca80a61113f0d1dd6fc3b932b0a0b4465e8ad3cf` on
`gpt-5/questpilot-phase1`.

The adapter in `adapters/luanti/` is a Lua mod for a **local singleplayer
Luanti world**. It is an open-source, official-API target, not Minecraft,
Minecraft Education, or a commercial-game adapter. `qp_seed` creates the
adapter's own non-solid test tokens, and a human enters `qp_start` then up to
eight individual `qp_step` commands. Each step only removes the next expected
test token; an unexpected node, a 16-action cap, completion, or `qp_stop`
causes `SAFE_STOP`.

The mod refuses a non-singleplayer world, makes no HTTP requests, has no
credential, payment, PvP, trading, anti-cheat, or external input path, and
does not affect nodes other than its own token identifier.

## Validation

```text
PYTHONPATH=. python3 -m py_compile questpilot/*.py
PYTHONPATH=. python3 -m unittest discover -s tests -v
# 13 tests passed
PYTHONPATH=. python3 -m questpilot.benchmark
# fixed mock benchmark: 30/30, completion_rate=1.0, unsafe_actions=0
```

The new static test verifies that the Lua source checks `is_singleplayer`,
registers `qp_stop`, uses only its own token identifier, and does not request
HTTP or reference credentials. Luanti is not installed on this Mac yet, so an
actual world run and recording remain pending.

## Cost and next step

Incremental cost: **US$0.00**. Install Luanti locally, create an owned
singleplayer world, enable this mod, then run the documented five commands.
No AWS/Vast.ai resource is needed or authorized.
