from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .json_utils import load_json_file


@dataclass(frozen=True)
class DashboardComposerConfig:
    component_id: str
    component_name: str
    output_directory: Path
    log_directory: Path
    allowed_card_types: list[str]
    next_component: str


def load_config(path: Path) -> DashboardComposerConfig:
    raw = load_json_file(path)
    base = Path.cwd()
    return DashboardComposerConfig(
        component_id=raw["component_id"],
        component_name=raw["component_name"],
        output_directory=_resolve(base, raw["output"]["output_directory"]),
        log_directory=_resolve(base, raw["output"]["log_directory"]),
        allowed_card_types=list(raw["allowed_card_types"]),
        next_component=raw["next_component"],
    )


def _resolve(base: Path, value: str) -> Path:
    candidate = Path(value)
    return candidate if candidate.is_absolute() else (base / candidate).resolve()
