from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .json_utils import load_json_file


@dataclass(frozen=True)
class PronunciationEngineConfig:
    component_id: str
    component_name: str
    output_directory: Path
    log_directory: Path
    supported_languages: list[str]
    phonetic_standard: str
    fallback_rules: dict[str, str]
    next_component: str


def load_config(path: Path) -> PronunciationEngineConfig:
    raw = load_json_file(path)
    base = Path.cwd()
    return PronunciationEngineConfig(
        component_id=raw["component_id"],
        component_name=raw["component_name"],
        output_directory=_resolve(base, raw["output"]["output_directory"]),
        log_directory=_resolve(base, raw["output"]["log_directory"]),
        supported_languages=list(raw["supported_languages"]),
        phonetic_standard=raw["phonetic_standard"],
        fallback_rules=dict(raw["fallback_rules"]),
        next_component=raw["next_component"],
    )


def _resolve(base: Path, value: str) -> Path:
    candidate = Path(value)
    return candidate if candidate.is_absolute() else (base / candidate).resolve()
