"""JSON helpers for Insight Engine."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


def load_json_file(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return data


def write_json_file(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=True)
        handle.write("\n")


def parse_json_object(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    fence_match = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", cleaned, re.DOTALL)
    if fence_match:
        cleaned = fence_match.group(1).strip()
    data = json.loads(cleaned)
    if not isinstance(data, dict):
        raise ValueError("LLM response must be a JSON object")
    return data
