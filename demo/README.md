# QuestPilot Offline UI Playground

This is a local browser demonstration, not a game client or integration.

From the repository root, run:

```bash
python3 -m http.server 8080 -d demo
```

Then open <http://127.0.0.1:8080/questpilot-ui-demo.html>.

Use **Manual play** to click through the offline mock yourself. Use **Run agent
step** to watch the behavior tree make one screen-state decision at a time, or
**Run until stop** to replay it. The trace remains entirely in the browser.

The upgrade task remains recommendation-only unless both checkboxes explicitly
enable and approve the offline mock execution. No real account, currency, or
network service is ever used.
