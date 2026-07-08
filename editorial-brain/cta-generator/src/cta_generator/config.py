"""Configuration loading."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .json_utils import load_json_file


@dataclass(frozen=True)
class CtaGeneratorConfig:
    component_id: str
    component_name: str
    prompt_path: Path
    script_schema: Path
    brief_schema: Path
    cta_schema: Path
    final_package_schema: Path
    output_directory: Path
    log_directory: Path
    max_cta_options: int
    max_retries: int
    temperature: float
    max_tokens: int
    target_duration_seconds: int
    next_agent: str


def load_config(path: Path) -> CtaGeneratorConfig:
    raw = load_json_file(path)
    base = Path.cwd()
    return CtaGeneratorConfig(
        component_id=raw["component_id"],
        component_name=raw["component_name"],
        prompt_path=_resolve(base, raw["prompt_path"]),
        script_schema=_resolve(base, raw["script_schema"]),
        brief_schema=_resolve(base, raw["brief_schema"]),
        cta_schema=_resolve(base, raw["cta_schema"]),
        final_package_schema=_resolve(base, raw["final_package_schema"]),
        output_directory=_resolve(base, raw["output"]["output_directory"]),
        log_directory=_resolve(base, raw["output"]["log_directory"]),
        max_cta_options=int(raw["max_cta_options"]),
        max_retries=int(raw["generation"]["max_retries"]),
        temperature=float(raw["generation"]["temperature"]),
        max_tokens=int(raw["generation"]["max_tokens"]),
        target_duration_seconds=int(raw["target_duration_seconds"]),
        next_agent=raw["next_agent"],
    )


def _resolve(base: Path, value: str) -> Path:
    candidate = Path(value)
    return candidate if candidate.is_absolute() else (base / candidate).resolve()

