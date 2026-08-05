# Playable QuestPilot UI demo

Date: 2026-08-06 (Asia/Singapore)

## Deliverable

`demo/questpilot-ui-demo.html` is a standalone local browser playground for the
offline QuestPilot UI simulator. It has no dependencies, network calls, game
client, credentials, or external service.

The mock uses an original fantasy-game presentation—a HUD, character and
resources, quest card, map scene, bottom navigation, and contextual in-world
action buttons—so a human can play the UI while seeing the same screen state
that the agent reads. It does not copy or connect to a commercial game's UI.

Launch from the repository root:

```bash
python3 -m http.server 8080 --bind 127.0.0.1 --directory demo
```

Open <http://127.0.0.1:8080/questpilot-ui-demo.html>.

## Interaction modes

- **Manual play:** click the currently available offline UI controls.
- **Run agent step:** displays one observation, explicit state estimate,
  behavior-tree leaf, and dry-run action at a time.
- **Run until stop:** replays the same bounded, visible agent policy locally.
- **Safety controls:** choose unreadable/conflicting/low-confidence/faint UI,
  activate the hard kill switch, or exercise the two-gate offline upgrade path.

The page is a JavaScript reimplementation of the fixed product-track flow for
interactive teaching and inspection. It is not an input bridge to a real game.

## Browser verification

The local page was opened and tested in the browser on 2026-08-06:

1. Manual **Login** moved the mock from `login` to `home`.
2. **Run until stop** completed the quest → collect → reward path and showed
   audit entries with `mode=dry_run` and `complete state=complete`.
3. **Apply offline upgrade** stopped with `upgrade approval required` when the
   two execution/approval controls were not both enabled.
4. Browser console had no warning or error entries.

The page is intentionally retained on the local `127.0.0.1:8080` server for
interactive use in this session. No portal EC2 host or cloud worker was used.
