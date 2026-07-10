from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def log_event(run_dir: Path, *, run_id: str, stage: str, event: str, message: str, level: str = "INFO", provider: str = "", duration_ms: int = 0, error_type: str = "") -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    entry: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": level,
        "run_id": run_id,
        "stage": stage,
        "event": event,
        "message": message,
        "provider": provider,
        "duration_ms": duration_ms,
    }
    if error_type:
        entry["error_type"] = error_type
    with (run_dir / "events.log").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=True) + "\n")
