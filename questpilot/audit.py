"""Append-only JSONL audit records and deterministic replay checks."""
from __future__ import annotations

import json
from pathlib import Path
from .model import AuditEvent

class AuditLog:
    def __init__(self, path: Path | None = None) -> None:
        self.path, self.events = path, []
    def emit(self, kind: str, **payload: object) -> AuditEvent:
        event = AuditEvent(len(self.events) + 1, kind, dict(payload)); self.events.append(event)
        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as handle: handle.write(json.dumps(event.as_dict(), sort_keys=True) + "\n")
        return event
    def replayable(self) -> bool:
        return [event.seq for event in self.events] == list(range(1, len(self.events) + 1)) and all(
            "screen_hash" in event.payload and "action" in event.payload for event in self.events if event.kind == "action")
