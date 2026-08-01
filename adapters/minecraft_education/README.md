# Minecraft Education adapter

This is QuestPilot's first publisher-supported integration. It is a
**MakeCode JavaScript** program for the official Minecraft Education Agent,
not a screen/OCR bot and not an adapter for consumer Minecraft or a live game
service. Minecraft Education documents Code Builder as the supported way to
code Agent movement/tasks with MakeCode JavaScript or Python.

## Run on a MacBook Air

1. Install Minecraft Education or launch its free demo, then open an owned
   local world. The official Hour of Code materials describe this demo path.
2. In the world, open Code Builder, choose **JavaScript**, and paste
   [`questpilot_collection.ts`](questpilot_collection.ts).
3. Make a flat, clear eight-block lane. Stand at its start and face down it.
4. In the Minecraft chat, run `qp_start`; then run `qp_step` once at a time.
   Each step moves once and collects nearby items. Inspect the world before
   entering the next step.
5. Use `qp_stop` at any time. `qp_status` prints the bounded run state.

The maximum is eight human-approved steps and sixteen actions. A detected
block in front, a limit, or `qp_stop` writes a `SAFE_STOP` status and disables
the script. There is no chat, PvP, payment, trading, credential, anti-cheat,
or unattended loop capability.

## Evidence and compatibility

- [Minecraft Education's official Agent lesson](https://education.minecraft.net/en-us/lessons/hour-of-ai-the-first-night)
- [Official Agent `collectAll` reference](https://minecraft.makecode.com/reference/agent/collect-all)
- [Official Code Builder/Agent movement curriculum](https://education.minecraft.net/fr-ca/lessons/computing-the-agency)

Use a current Minecraft Education MakeCode world. This repository validates
the safety contract statically; it cannot launch Minecraft Education or verify
the local licence/world from a headless CI process.
