"""Structured logging for the Editorial Orchestrator."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class ExecutionLogger:
    def __init__(self, log_directory: Path, production_id: str):
        self.log_directory = log_directory
        self.production_id = production_id
        self.log_directory.mkdir(parents=True, exist_ok=True)
        safe_id = production_id or "unknown-production"
        self.path = self.log_directory / f"editorial-orchestrator-{safe_id}.log.jsonl"

    def log(self, event: dict[str, Any]) -> None:
        event = dict(event)
        event.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=True) + "\n")
