# Luanti adapter report

Date: 2026-08-01 (Asia/Singapore)

## Deliverable

Initial implementation commit:
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

On the 8 GB M1 MacBook Air, Luanti 5.16.1 was installed locally and Minetest
Game was fetched from its public source into the ignored `.luanti-user/` test
folder. The engine was run against an isolated local world with
`bind_address = 127.0.0.1` and `server_announce = false`. Its audit log
recorded:

```text
ACTION[Main]: [questpilot_luanti] loaded; local singleplayer guard active
ACTION[Main]: Server for gameid="minetest" listening on 127.0.0.1:30000.
```

The graphical client then connected to that local server as `QuestPilotTest`.
No external game account, paid service, or cloud compute was used.

```text
PYTHONPATH=. python3 -m unittest discover -s tests -v
# 13 tests passed
PYTHONPATH=. python3 -m questpilot.benchmark
# fixed mock benchmark: 30/30, completion_rate=1.0, unsafe_actions=0
luajit -b adapters/luanti/init.lua /private/tmp/questpilot_luanti.luac
# passed
```

The static test verifies that the Lua source checks `is_singleplayer`,
registers `qp_stop`, uses only its own token identifier, and does not request
HTTP or reference credentials. The engine run confirmed it loads cleanly.

The Mac desktop capture service denied `screencapture`, and the GUI's OpenGL
context could not be exposed to the automation bridge. A scripted `/qp_seed`
attempt therefore produced Luanti's `Empty command` message; no token was
created and it is **not** counted as a functional action test or a video.
This is a safe-stop test limitation, not a QuestPilot success claim.

## Cost and next step

Incremental cost: **US$0.00**. Next action: grant the terminal screen-recording
and accessibility permission (or enter the five documented commands manually
in the local Luanti window) to capture a real action-level video. No AWS/Vast.ai
resource is needed or authorized.
