"""Structured logging."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class ComponentLogger:
    def __init__(self, log_directory: Path, production_id: str):
        self.path = log_directory / f"editorial-validator-{production_id}.log.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, event: dict[str, Any]) -> None:
        event = dict(event)
        event.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=True) + "\n")
