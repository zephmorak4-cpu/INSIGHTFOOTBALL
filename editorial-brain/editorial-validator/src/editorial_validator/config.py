"""Config loading for Editorial Validator."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .json_utils import load_json_file


@dataclass(frozen=True)
class EditorialValidatorConfig:
    component_id: str
    component_name: str
    input_schema: Path
    output_schema: Path
    validated_package_schema: Path
    output_directory: Path
    log_directory: Path
    confidence_threshold: int
    publishability_threshold: int
    next_component: str


def load_config(path: Path) -> EditorialValidatorConfig:
    raw = load_json_file(path)
    base = Path.cwd()
    return EditorialValidatorConfig(
        component_id=raw["component_id"],
        component_name=raw["component_name"],
        input_schema=_resolve(base, raw["input_schema"]),
        output_schema=_resolve(base, raw["output_schema"]),
        validated_package_schema=_resolve(base, raw["validated_package_schema"]),
        output_directory=_resolve(base, raw["output"]["directory"]),
        log_directory=_resolve(base, raw["output"]["log_directory"]),
        confidence_threshold=int(raw["confidence_threshold"]),
        publishability_threshold=int(raw["publishability_threshold"]),
        next_component=raw["next_component"],
    )


def _resolve(base: Path, value: str) -> Path:
    candidate = Path(value)
    return candidate if candidate.is_absolute() else (base / candidate).resolve()
