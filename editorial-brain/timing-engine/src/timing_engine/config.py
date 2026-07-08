"""Configuration loading."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .json_utils import load_json_file


@dataclass(frozen=True)
class TimingEngineConfig:
    component_id: str
    component_name: str
    input_schema: Path
    timeline_schema: Path
    final_package_schema: Path
    output_directory: Path
    log_directory: Path
    fps: int
    aspect_ratio: str
    resolution: str
    max_duration_seconds: int
    next_component: str


def load_config(path: Path) -> TimingEngineConfig:
    raw = load_json_file(path)
    base = Path.cwd()
    return TimingEngineConfig(
        component_id=raw["component_id"],
        component_name=raw["component_name"],
        input_schema=_resolve(base, raw["input_schema"]),
        timeline_schema=_resolve(base, raw["timeline_schema"]),
        final_package_schema=_resolve(base, raw["final_package_schema"]),
        output_directory=_resolve(base, raw["output"]["output_directory"]),
        log_directory=_resolve(base, raw["output"]["log_directory"]),
        fps=int(raw["fps"]),
        aspect_ratio=raw["aspect_ratio"],
        resolution=raw["resolution"],
        max_duration_seconds=int(raw["max_duration_seconds"]),
        next_component=raw["next_component"],
    )


def _resolve(base: Path, value: str) -> Path:
    candidate = Path(value)
    return candidate if candidate.is_absolute() else (base / candidate).resolve()

