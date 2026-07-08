"""Configuration loading for the Editorial Orchestrator."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .errors import ConfigError
from .json_utils import load_json_file


@dataclass(frozen=True)
class OrchestratorConfig:
    match_selector_config_path: Path
    story_hunter_config_path: Path
    evidence_filter_config_path: Path
    insight_engine_config_path: Path
    package_schema_path: Path
    output_directory: Path
    log_directory: Path
    minimum_confidence: int
    provider: str


def load_config(path: Path) -> OrchestratorConfig:
    raw = load_json_file(path)
    try:
        modules = raw["modules"]
        output = raw["output"]
        validation = raw["validation_policy"]
    except KeyError as exc:
        raise ConfigError(f"Missing config section: {exc.args[0]}") from exc

    base = Path.cwd()
    return OrchestratorConfig(
        match_selector_config_path=_resolve(base, modules["match_selector_config_path"]),
        story_hunter_config_path=_resolve(base, modules["story_hunter_config_path"]),
        evidence_filter_config_path=_resolve(base, modules["evidence_filter_config_path"]),
        insight_engine_config_path=_resolve(base, modules["insight_engine_config_path"]),
        package_schema_path=_resolve(base, raw["package_schema_path"]),
        output_directory=_resolve(base, output["package_directory"]),
        log_directory=_resolve(base, output["log_directory"]),
        minimum_confidence=int(validation["minimum_confidence"]),
        provider=str(raw.get("provider", "deterministic")),
    )


def _resolve(base: Path, value: str) -> Path:
    candidate = Path(value)
    if candidate.is_absolute():
        return candidate
    return (base / candidate).resolve()
