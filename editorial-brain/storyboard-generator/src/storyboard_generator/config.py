"""Configuration loading."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .json_utils import load_json_file


@dataclass(frozen=True)
class StoryboardGeneratorConfig:
    agent_id: str
    agent_name: str
    prompt_id: str
    prompt_version: str
    model: str
    temperature: float
    max_tokens: int
    max_retries: int
    min_scene_duration_seconds: int
    max_scene_duration_seconds: int
    target_visual_change_seconds: int
    prompt_path: Path
    script_package_schema: Path
    output_schema: Path
    output_directory: Path
    log_directory: Path
    next_component: str


def load_config(path: Path) -> StoryboardGeneratorConfig:
    raw = load_json_file(path)
    base = Path.cwd()
    return StoryboardGeneratorConfig(
        agent_id=raw["agent_id"],
        agent_name=raw["agent_name"],
        prompt_id=raw["prompt_id"],
        prompt_version=raw["prompt_version"],
        model=raw["generation"]["model"],
        temperature=float(raw["generation"]["temperature"]),
        max_tokens=int(raw["generation"]["max_tokens"]),
        max_retries=int(raw["generation"]["max_retries"]),
        min_scene_duration_seconds=int(raw["timing"]["min_scene_duration_seconds"]),
        max_scene_duration_seconds=int(raw["timing"]["max_scene_duration_seconds"]),
        target_visual_change_seconds=int(raw["timing"]["target_visual_change_seconds"]),
        prompt_path=_resolve(base, raw["prompt_path"]),
        script_package_schema=_resolve(base, raw["script_package_schema"]),
        output_schema=_resolve(base, raw["output_schema"]),
        output_directory=_resolve(base, raw["output"]["output_directory"]),
        log_directory=_resolve(base, raw["output"]["log_directory"]),
        next_component=raw["next_component"],
    )


def _resolve(base: Path, value: str) -> Path:
    candidate = Path(value)
    return candidate if candidate.is_absolute() else (base / candidate).resolve()

