"""Configuration loading."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .json_utils import load_json_file


@dataclass(frozen=True)
class AssetPlannerConfig:
    component_id: str
    component_name: str
    input_schema: Path
    output_schema: Path
    output_directory: Path
    log_directory: Path
    allowed_asset_types: list[str]
    allowed_asset_categories: list[str]
    default_dimensions: dict
    legal_risk_rules: list[str]
    next_component: str


def load_config(path: Path) -> AssetPlannerConfig:
    raw = load_json_file(path)
    base = Path.cwd()
    return AssetPlannerConfig(
        component_id=raw["component_id"],
        component_name=raw["component_name"],
        input_schema=_resolve(base, raw["input_schema"]),
        output_schema=_resolve(base, raw["output_schema"]),
        output_directory=_resolve(base, raw["output"]["output_directory"]),
        log_directory=_resolve(base, raw["output"]["log_directory"]),
        allowed_asset_types=list(raw["allowed_asset_types"]),
        allowed_asset_categories=list(raw["allowed_asset_categories"]),
        default_dimensions=dict(raw["default_dimensions"]),
        legal_risk_rules=list(raw["legal_risk_rules"]),
        next_component=raw["next_component"],
    )


def _resolve(base: Path, value: str) -> Path:
    candidate = Path(value)
    return candidate if candidate.is_absolute() else (base / candidate).resolve()

