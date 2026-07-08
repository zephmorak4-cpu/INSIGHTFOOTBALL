from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .json_utils import load_json_file


@dataclass(frozen=True)
class CaptionDesignerConfig:
    component_id: str
    component_name: str
    output_directory: Path
    log_directory: Path
    max_words_per_line: int
    max_lines: int
    next_component: str


def load_config(path: Path) -> CaptionDesignerConfig:
    raw = load_json_file(path)
    base = Path.cwd()
    return CaptionDesignerConfig(
        component_id=raw["component_id"],
        component_name=raw["component_name"],
        output_directory=_resolve(base, raw["output"]["output_directory"]),
        log_directory=_resolve(base, raw["output"]["log_directory"]),
        max_words_per_line=int(raw["max_words_per_line"]),
        max_lines=int(raw["max_lines"]),
        next_component=raw["next_component"],
    )


def _resolve(base: Path, value: str) -> Path:
    candidate = Path(value)
    return candidate if candidate.is_absolute() else (base / candidate).resolve()
