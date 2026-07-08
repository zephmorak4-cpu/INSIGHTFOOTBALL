"""Config loading."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .json_utils import load_json_file


@dataclass(frozen=True)
class ProductionBriefConfig:
    component_id: str
    component_name: str
    input_schema: Path
    output_schema: Path
    output_directory: Path
    log_directory: Path
    target_duration_seconds: int
    target_platforms: list[str]
    next_agent: str


def load_config(path: Path) -> ProductionBriefConfig:
    raw = load_json_file(path)
    base = Path.cwd()
    return ProductionBriefConfig(
        component_id=raw["component_id"],
        component_name=raw["component_name"],
        input_schema=_resolve(base, raw["input_schema"]),
        output_schema=_resolve(base, raw["output_schema"]),
        output_directory=_resolve(base, raw["output"]["directory"]),
        log_directory=_resolve(base, raw["output"]["log_directory"]),
        target_duration_seconds=int(raw["target_duration_seconds"]),
        target_platforms=list(raw["target_platforms"]),
        next_agent=raw["next_agent"],
    )


def _resolve(base: Path, value: str) -> Path:
    candidate = Path(value)
    return candidate if candidate.is_absolute() else (base / candidate).resolve()
