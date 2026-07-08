from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .json_utils import load_json_file


@dataclass(frozen=True)
class MotionPlannerConfig:
    component_id: str
    component_name: str
    output_directory: Path
    log_directory: Path
    allowed_motion_presets: list[str]
    next_component: str


def load_config(path: Path) -> MotionPlannerConfig:
    raw = load_json_file(path)
    base = Path.cwd()
    return MotionPlannerConfig(
        component_id=raw["component_id"],
        component_name=raw["component_name"],
        output_directory=_resolve(base, raw["output"]["output_directory"]),
        log_directory=_resolve(base, raw["output"]["log_directory"]),
        allowed_motion_presets=list(raw["allowed_motion_presets"]),
        next_component=raw["next_component"],
    )


def _resolve(base: Path, value: str) -> Path:
    candidate = Path(value)
    return candidate if candidate.is_absolute() else (base / candidate).resolve()
