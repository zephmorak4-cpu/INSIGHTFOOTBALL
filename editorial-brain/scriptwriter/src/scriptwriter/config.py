"""Configuration loading for Scriptwriter."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .errors import ConfigError
from .json_utils import load_json_file


@dataclass(frozen=True)
class ScriptwriterConfig:
    agent_id: str
    agent_name: str
    prompt_id: str
    prompt_version: str
    prompt_path: Path
    input_schema: Path
    output_schema: Path
    output_directory: Path
    log_directory: Path
    model: str
    temperature: float
    max_tokens: int
    max_retries: int
    target_duration_seconds: int
    min_words: int
    max_words: int
    next_agent: str


def load_config(path: Path) -> ScriptwriterConfig:
    raw = load_json_file(path)
    try:
        generation = raw["generation"]
        output = raw["output"]
        validation = raw["validation"]
    except KeyError as exc:
        raise ConfigError(f"Missing config section: {exc.args[0]}") from exc
    base = Path.cwd()
    return ScriptwriterConfig(
        agent_id=str(raw["agent_id"]),
        agent_name=str(raw["agent_name"]),
        prompt_id=str(raw["prompt_id"]),
        prompt_version=str(raw["prompt_version"]),
        prompt_path=_resolve(base, raw["prompt_path"]),
        input_schema=_resolve(base, raw["input_schema"]),
        output_schema=_resolve(base, raw["output_schema"]),
        output_directory=_resolve(base, output["output_directory"]),
        log_directory=_resolve(base, output["log_directory"]),
        model=str(generation["model"]),
        temperature=float(generation["temperature"]),
        max_tokens=int(generation["max_tokens"]),
        max_retries=int(generation["max_retries"]),
        target_duration_seconds=int(validation["target_duration_seconds"]),
        min_words=int(validation["min_words"]),
        max_words=int(validation["max_words"]),
        next_agent=str(raw["next_agent"]),
    )


def _resolve(base: Path, value: str) -> Path:
    candidate = Path(value)
    return candidate if candidate.is_absolute() else (base / candidate).resolve()

