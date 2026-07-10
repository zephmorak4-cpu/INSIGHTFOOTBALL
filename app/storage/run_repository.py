from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class RunRepository:
    def __init__(self, data_dir: str, run_id: str):
        self.run_id = run_id
        self.run_dir = Path(data_dir) / "runs" / run_id
        self.run_dir.mkdir(parents=True, exist_ok=True)

    def write_json(self, name: str, payload: dict[str, Any]) -> Path:
        path = self.run_dir / name
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
        return path

    def write_text(self, name: str, text: str) -> Path:
        path = self.run_dir / name
        path.write_text(text, encoding="utf-8")
        return path

    def append_error(self, text: str) -> None:
        with (self.run_dir / "errors.log").open("a", encoding="utf-8") as handle:
            handle.write(text + "\n")
