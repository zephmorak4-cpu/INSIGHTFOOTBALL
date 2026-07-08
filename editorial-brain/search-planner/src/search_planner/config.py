from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .json_utils import load_json_file


@dataclass(frozen=True)
class SearchPlannerConfig:
    component_id: str
    component_name: str
    input_schema: Path
    output_schema: Path
    output_directory: Path
    log_directory: Path
    approved_source_types: list[str]
    blocked_source_types: list[str]
    task_priority_rules: dict
    next_component: str


def load_config(path: Path) -> SearchPlannerConfig:
    raw = load_json_file(path)
    base = Path.cwd()
    return SearchPlannerConfig(
        component_id=raw["component_id"],
        component_name=raw["component_name"],
        input_schema=_resolve(base, raw["input_schema"]),
        output_schema=_resolve(base, raw["output_schema"]),
        output_directory=_resolve(base, raw["output"]["output_directory"]),
        log_directory=_resolve(base, raw["output"]["log_directory"]),
        approved_source_types=list(raw["approved_source_types"]),
        blocked_source_types=list(raw["blocked_source_types"]),
        task_priority_rules=dict(raw["task_priority_rules"]),
        next_component=raw["next_component"],
    )


def _resolve(base: Path, value: str) -> Path:
    candidate = Path(value)
    return candidate if candidate.is_absolute() else (base / candidate).resolve()

