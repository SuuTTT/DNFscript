# QuestPilot approved-adapter roadmap

| Priority | Target | Intended interface | Status / gate |
|---|---|---|---|
| Now | Minecraft Education | Official Code Builder Agent API in an owned local/demo world | Implemented: bounded, human-stepped collection lane. |
| Next | Screeps | Native game scripting or a self-hosted community server | Design only; it is an intentional programmable-agent game, not a screen-input target. |
| Next | Factorio | Official Lua mod API in single-player or a server the operator controls | Design only; build a mod, not an external click bot. |
| Conditional | Mobile game | Official API or publisher-provided staging build | Blocked until a manifest passes `questpilot.integration_gate.evaluate_manifest`. |

All adapters use the same contract: declared target/environment, a verifiable
authorization reference, observation mode, explicit allowlisted capabilities,
bounded actions, audit records, and a safe stop. Production, anti-cheat,
CAPTCHA, credentials, chat, payments, trading, and PvP are rejected by design.

Minecraft Education is deliberately a native-agent adapter: it uses an
official in-game Agent sensor rather than pretending that screen OCR is the
right interface for every publisher-approved integration. The Phase 1 offline
mock remains the screen/OCR reference implementation.
