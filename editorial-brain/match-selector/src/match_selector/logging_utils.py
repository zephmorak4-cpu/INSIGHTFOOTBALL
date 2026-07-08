"""Structured JSON logging for Match Selector."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class StructuredLogger:
    def __init__(self, log_directory: Path):
        self.log_directory = log_directory
        self.log_directory.mkdir(parents=True, exist_ok=True)

    def log(self, event: dict[str, Any]) -> None:
        event = dict(event)
        event.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
        path = self.log_directory / "match-selector.log.jsonl"
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=True) + "\n")
