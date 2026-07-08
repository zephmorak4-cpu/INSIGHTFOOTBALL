from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .json_utils import load_json_file


@dataclass(frozen=True)
class TimestampGeneratorConfig:
    component_id: str
    component_name: str
    output_directory: Path
    log_directory: Path
    speech_rate: int
    pause_estimation: dict[str, float]
    max_duration_seconds: float
    next_component: str


def load_config(path: Path) -> TimestampGeneratorConfig:
    raw = load_json_file(path)
    base = Path.cwd()
    return TimestampGeneratorConfig(
        component_id=raw["component_id"],
        component_name=raw["component_name"],
        output_directory=_resolve(base, raw["output"]["output_directory"]),
        log_directory=_resolve(base, raw["output"]["log_directory"]),
        speech_rate=int(raw["speech_rate"]),
        pause_estimation={k: float(v) for k, v in raw["pause_estimation"].items()},
        max_duration_seconds=float(raw["max_duration_seconds"]),
        next_component=raw["next_component"],
    )


def _resolve(base: Path, value: str) -> Path:
    candidate = Path(value)
    return candidate if candidate.is_absolute() else (base / candidate).resolve()
