from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .json_utils import load_json_file


@dataclass(frozen=True)
class VoiceDirectorConfig:
    component_id: str
    component_name: str
    output_directory: Path
    log_directory: Path
    voice_profile: str
    preferred_provider: str
    fallback_provider: str
    target_speed_wpm: int
    emotion_rules: dict[str, str]
    next_component: str


def load_config(path: Path) -> VoiceDirectorConfig:
    raw = load_json_file(path)
    base = Path.cwd()
    return VoiceDirectorConfig(
        component_id=raw["component_id"],
        component_name=raw["component_name"],
        output_directory=_resolve(base, raw["output"]["output_directory"]),
        log_directory=_resolve(base, raw["output"]["log_directory"]),
        voice_profile=raw["voice_profile"],
        preferred_provider=raw["preferred_provider"],
        fallback_provider=raw["fallback_provider"],
        target_speed_wpm=int(raw["target_speed_wpm"]),
        emotion_rules=dict(raw["emotion_rules"]),
        next_component=raw["next_component"],
    )


def _resolve(base: Path, value: str) -> Path:
    candidate = Path(value)
    return candidate if candidate.is_absolute() else (base / candidate).resolve()
