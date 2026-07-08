"""Configuration loading for Match Selector."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .errors import ConfigError
from .json_utils import load_json_file


@dataclass(frozen=True)
class MatchSelectorConfig:
    prompt_library_path: Path
    input_schema_path: Path
    output_schema_path: Path
    log_directory: Path
    minimum_confidence: int
    max_retries: int
    temperature: float
    max_tokens: int
    provider: str
    model: str
    api_key_env: str
    endpoint: str
    timeout_seconds: int


def load_config(path: Path) -> MatchSelectorConfig:
    raw = load_json_file(path)
    try:
        validation = raw["validation_policy"]
        retry = raw["retry_policy"]
        generation = raw["generation"]
        model_selection = raw["model_selection"]
        output = raw["output"]
        provider_config = raw["llm_provider"]
    except KeyError as exc:
        raise ConfigError(f"Missing config section: {exc.args[0]}") from exc

    base = Path.cwd()
    return MatchSelectorConfig(
        prompt_library_path=_resolve(base, raw["prompt_library_path"]),
        input_schema_path=_resolve(base, raw["input_schema_path"]),
        output_schema_path=_resolve(base, raw["output_schema_path"]),
        log_directory=_resolve(base, output["log_directory"]),
        minimum_confidence=int(validation["minimum_confidence"]),
        max_retries=int(retry["max_retries"]),
        temperature=float(generation["temperature"]),
        max_tokens=int(generation["max_tokens"]),
        provider=str(provider_config["provider"]),
        model=str(model_selection["default_model"]),
        api_key_env=str(provider_config["api_key_env"]),
        endpoint=str(provider_config["endpoint"]),
        timeout_seconds=int(provider_config["timeout_seconds"]),
    )


def _resolve(base: Path, value: str) -> Path:
    candidate = Path(value)
    if candidate.is_absolute():
        return candidate
    return (base / candidate).resolve()
