from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .json_utils import load_json_file


@dataclass(frozen=True)
class SSMLGeneratorConfig:
    component_id: str
    component_name: str
    output_directory: Path
    log_directory: Path
    provider: str
    supported_tags: list[str]
    pause_rules: dict[str, int]
    next_component: str


def load_config(path: Path) -> SSMLGeneratorConfig:
    raw = load_json_file(path)
    base = Path.cwd()
    return SSMLGeneratorConfig(
        component_id=raw["component_id"],
        component_name=raw["component_name"],
        output_directory=_resolve(base, raw["output"]["output_directory"]),
        log_directory=_resolve(base, raw["output"]["log_directory"]),
        provider=raw["provider"],
        supported_tags=list(raw["supported_tags"]),
        pause_rules={k: int(v) for k, v in raw["pause_rules"].items()},
        next_component=raw["next_component"],
    )


def _resolve(base: Path, value: str) -> Path:
    candidate = Path(value)
    return candidate if candidate.is_absolute() else (base / candidate).resolve()
