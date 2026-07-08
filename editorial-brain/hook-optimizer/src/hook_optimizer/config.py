"""Configuration loading."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .json_utils import load_json_file


@dataclass(frozen=True)
class HookOptimizerConfig:
    component_id: str
    component_name: str
    prompt_path: Path
    script_schema: Path
    brief_schema: Path
    optimization_schema: Path
    optimized_script_schema: Path
    output_directory: Path
    log_directory: Path
    max_hook_options: int
    max_retries: int
    temperature: float
    max_tokens: int
    next_component: str


def load_config(path: Path) -> HookOptimizerConfig:
    raw = load_json_file(path)
    base = Path.cwd()
    return HookOptimizerConfig(
        component_id=raw["component_id"],
        component_name=raw["component_name"],
        prompt_path=_resolve(base, raw["prompt_path"]),
        script_schema=_resolve(base, raw["script_schema"]),
        brief_schema=_resolve(base, raw["brief_schema"]),
        optimization_schema=_resolve(base, raw["optimization_schema"]),
        optimized_script_schema=_resolve(base, raw["optimized_script_schema"]),
        output_directory=_resolve(base, raw["output"]["output_directory"]),
        log_directory=_resolve(base, raw["output"]["log_directory"]),
        max_hook_options=int(raw["max_hook_options"]),
        max_retries=int(raw["generation"]["max_retries"]),
        temperature=float(raw["generation"]["temperature"]),
        max_tokens=int(raw["generation"]["max_tokens"]),
        next_component=raw["next_component"],
    )


def _resolve(base: Path, value: str) -> Path:
    candidate = Path(value)
    return candidate if candidate.is_absolute() else (base / candidate).resolve()

