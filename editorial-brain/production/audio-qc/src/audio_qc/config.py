from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .json_utils import load_json_file


@dataclass(frozen=True)
class AudioQCConfig:
    component_id: str
    component_name: str
    output_directory: Path
    log_directory: Path
    min_quality_score: int
    max_wpm: int
    min_wpm: int
    max_duration_seconds: float
    forbidden_language: list[str]
    compatible_providers: list[str]


def load_config(path: Path) -> AudioQCConfig:
    raw = load_json_file(path)
    base = Path.cwd()
    return AudioQCConfig(
        component_id=raw["component_id"],
        component_name=raw["component_name"],
        output_directory=_resolve(base, raw["output"]["output_directory"]),
        log_directory=_resolve(base, raw["output"]["log_directory"]),
        min_quality_score=int(raw["min_quality_score"]),
        max_wpm=int(raw["max_wpm"]),
        min_wpm=int(raw["min_wpm"]),
        max_duration_seconds=float(raw["max_duration_seconds"]),
        forbidden_language=list(raw["forbidden_language"]),
        compatible_providers=list(raw["compatible_providers"]),
    )


def _resolve(base: Path, value: str) -> Path:
    candidate = Path(value)
    return candidate if candidate.is_absolute() else (base / candidate).resolve()
