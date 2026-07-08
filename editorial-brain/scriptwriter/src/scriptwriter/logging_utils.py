"""Structured JSON logging."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class StructuredLogger:
    def __init__(self, log_directory: Path, name: str):
        self.path = log_directory / f"{name}.log.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, event: dict[str, Any]) -> None:
        payload = {"logged_at": datetime.now(timezone.utc).isoformat(), **event}
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=True) + "\n")

