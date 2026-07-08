from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .json_utils import load_json_file


@dataclass(frozen=True)
class GraphicPlannerConfig:
    component_id: str
    component_name: str
    storyboard_schema: Path
    manifest_schema: Path
    search_plan_schema: Path
    output_schema: Path
    final_package_schema: Path
    output_directory: Path
    log_directory: Path
    allowed_graphic_types: list[str]
    default_format: str
    default_dimensions: str
    next_component: str


def load_config(path: Path) -> GraphicPlannerConfig:
    raw = load_json_file(path)
    base = Path.cwd()
    return GraphicPlannerConfig(
        component_id=raw["component_id"],
        component_name=raw["component_name"],
        storyboard_schema=_resolve(base, raw["storyboard_schema"]),
        manifest_schema=_resolve(base, raw["manifest_schema"]),
        search_plan_schema=_resolve(base, raw["search_plan_schema"]),
        output_schema=_resolve(base, raw["output_schema"]),
        final_package_schema=_resolve(base, raw["final_package_schema"]),
        output_directory=_resolve(base, raw["output"]["output_directory"]),
        log_directory=_resolve(base, raw["output"]["log_directory"]),
        allowed_graphic_types=list(raw["allowed_graphic_types"]),
        default_format=raw["default_format"],
        default_dimensions=raw["default_dimensions"],
        next_component=raw["next_component"],
    )


def _resolve(base: Path, value: str) -> Path:
    candidate = Path(value)
    return candidate if candidate.is_absolute() else (base / candidate).resolve()

