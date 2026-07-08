from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .json_utils import load_json_file


@dataclass(frozen=True)
class VisualDirectorConfig:
    component_id: str
    component_name: str
    storyboard_schema: Path
    asset_package_schema: Path
    output_schema: Path
    output_directory: Path
    log_directory: Path
    allowed_templates: list[str]
    allowed_layouts: list[str]
    next_component: str


def load_config(path: Path) -> VisualDirectorConfig:
    raw = load_json_file(path)
    base = Path.cwd()
    return VisualDirectorConfig(
        component_id=raw["component_id"],
        component_name=raw["component_name"],
        storyboard_schema=_resolve(base, raw["storyboard_schema"]),
        asset_package_schema=_resolve(base, raw["asset_package_schema"]),
        output_schema=_resolve(base, raw["output_schema"]),
        output_directory=_resolve(base, raw["output"]["output_directory"]),
        log_directory=_resolve(base, raw["output"]["log_directory"]),
        allowed_templates=list(raw["allowed_templates"]),
        allowed_layouts=list(raw["allowed_layouts"]),
        next_component=raw["next_component"],
    )


def _resolve(base: Path, value: str) -> Path:
    candidate = Path(value)
    return candidate if candidate.is_absolute() else (base / candidate).resolve()

