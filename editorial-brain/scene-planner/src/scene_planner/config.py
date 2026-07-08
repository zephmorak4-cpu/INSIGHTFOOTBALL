"""Configuration loading."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .json_utils import load_json_file


@dataclass(frozen=True)
class ScenePlannerConfig:
    component_id: str
    component_name: str
    input_schema: Path
    script_package_schema: Path
    output_schema: Path
    output_directory: Path
    log_directory: Path
    allowed_scene_types: list[str]
    allowed_template_ids: list[str]
    max_text_per_scene: int
    target_visual_change_seconds: int
    next_component: str


def load_config(path: Path) -> ScenePlannerConfig:
    raw = load_json_file(path)
    base = Path.cwd()
    return ScenePlannerConfig(
        component_id=raw["component_id"],
        component_name=raw["component_name"],
        input_schema=_resolve(base, raw["input_schema"]),
        script_package_schema=_resolve(base, raw["script_package_schema"]),
        output_schema=_resolve(base, raw["output_schema"]),
        output_directory=_resolve(base, raw["output"]["output_directory"]),
        log_directory=_resolve(base, raw["output"]["log_directory"]),
        allowed_scene_types=list(raw["allowed_scene_types"]),
        allowed_template_ids=list(raw["allowed_template_ids"]),
        max_text_per_scene=int(raw["max_text_per_scene"]),
        target_visual_change_seconds=int(raw["target_visual_change_seconds"]),
        next_component=raw["next_component"],
    )


def _resolve(base: Path, value: str) -> Path:
    candidate = Path(value)
    return candidate if candidate.is_absolute() else (base / candidate).resolve()

