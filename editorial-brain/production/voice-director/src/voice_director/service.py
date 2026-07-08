from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import VoiceDirectorConfig
from .json_utils import load_json_file, write_json_file
from .logging_utils import StructuredLogger
from .validation import VoiceDirectorValidator


class VoiceDirectorService:
    def __init__(self, config: VoiceDirectorConfig):
        self.config = config
        self.validator = VoiceDirectorValidator()

    def run_from_file(self, script_package_path: Path) -> dict[str, Any]:
        return self.run(load_json_file(script_package_path))

    def run(self, script_package: dict[str, Any]) -> dict[str, Any]:
        production_id = script_package.get("production_id", "unknown-production")
        logger = StructuredLogger(self.config.log_directory, f"voice-director-{production_id}")
        issues = self.validator.validate_input(script_package)
        sections = _build_sections(script_package, self.config)
        voice_plan = {
            "production_id": production_id,
            "component_id": self.config.component_id,
            "component_name": self.config.component_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source_script_package": production_id,
            "voice_profile": self.config.voice_profile,
            "preferred_provider": self.config.preferred_provider,
            "fallback_provider": self.config.fallback_provider,
            "target_speed_wpm": self.config.target_speed_wpm,
            "pronunciation_profile": "football_names_en_gb",
            "sections": sections,
            "warnings": [],
            "approval_status": "approved" if not issues else "blocked",
            "next_component": self.config.next_component,
        }
        issues.extend(self.validator.validate_output(voice_plan))
        if issues:
            logger.log({"event": "voice_direction_failed", "issues": issues})
            return {"success": False, "error": {"code": "VOICE_DIRECTION_FAILED", "issues": issues}, "voice_plan": voice_plan}
        path = self.config.output_directory / "voice_plan.json"
        write_json_file(path, voice_plan)
        logger.log({"event": "voice_plan_written", "output_path": str(path), "sections": len(sections)})
        return {"success": True, "voice_plan": voice_plan, "voice_plan_path": str(path)}


def _build_sections(script: dict[str, Any], config: VoiceDirectorConfig) -> list[dict[str, Any]]:
    sentences = _sentences(script["final_voiceover"])
    candidates = [
        ("hook", " ".join(sentences[:2])),
        ("central_question", sentences[2] if len(sentences) > 2 else script.get("central_question", "")),
        ("main_body", " ".join(sentences[3:-3]) if len(sentences) > 6 else script.get("main_body", "")),
        ("conclusion", " ".join(sentences[-3:-1]) if len(sentences) > 3 else script.get("conclusion", "")),
        ("cta", sentences[-1] if sentences else script.get("cta", "")),
    ]
    sections = []
    for index, (name, text) in enumerate((item for item in candidates if str(item[1]).strip()), start=1):
        emotion = config.emotion_rules.get(name, "curious")
        sections.append({
            "section_id": f"voice-section-{index:02d}",
            "source_section": name,
            "narration_text": str(text).strip(),
            "voice_style": config.voice_profile,
            "emotion": emotion,
            "pace": _pace(name),
            "pitch": "medium",
            "energy": "medium-high" if name in {"hook", "cta"} else "medium",
            "pause_before": 0.25 if index > 1 else 0.0,
            "pause_after": 0.4 if name in {"hook", "central_question", "cta"} else 0.25,
            "emphasis_words": _emphasis_words(str(text), script),
            "breathing_points": _breathing_points(str(text)),
        })
    return sections


def _sentences(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", text.strip()) if part.strip()]


def _pace(name: str) -> str:
    return {"hook": "measured", "central_question": "slightly_slow", "main_body": "natural", "conclusion": "natural", "cta": "warm_prompt"}.get(name, "natural")


def _emphasis_words(text: str, script: dict[str, Any]) -> list[str]:
    terms = [script.get("match", {}).get("home_team", ""), script.get("match", {}).get("away_team", ""), "fast start", "slight home edge", "x-factor"]
    return [term for term in terms if term and term.lower() in text.lower()][:4]


def _breathing_points(text: str) -> list[str]:
    return [mark for mark in [",", ";", ":", "?"] if mark in text]
