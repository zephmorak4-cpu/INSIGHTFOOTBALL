from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import AudioQCConfig
from .json_utils import load_json_file, load_text_file, write_json_file
from .logging_utils import StructuredLogger
from .validation import AudioQCValidator


class AudioQCService:
    def __init__(self, config: AudioQCConfig):
        self.config = config
        self.validator = AudioQCValidator()

    def run_from_files(self, voice_plan_path: Path, pronunciation_dictionary_path: Path, ssml_path: Path, ssml_metadata_path: Path, timestamps_path: Path) -> dict[str, Any]:
        return self.run(
            load_json_file(voice_plan_path),
            load_json_file(pronunciation_dictionary_path),
            load_text_file(ssml_path),
            load_json_file(ssml_metadata_path),
            load_json_file(timestamps_path),
        )

    def run(self, voice_plan: dict[str, Any], pronunciation_dictionary: dict[str, Any], ssml: str, ssml_metadata: dict[str, Any], voice_timestamps: dict[str, Any]) -> dict[str, Any]:
        production_id = voice_plan.get("production_id", "unknown-production")
        logger = StructuredLogger(self.config.log_directory, f"audio-qc-{production_id}")
        issues = self.validator.validate_inputs(voice_plan, pronunciation_dictionary, ssml_metadata, voice_timestamps)
        report = _build_report(voice_plan, pronunciation_dictionary, ssml, voice_timestamps, self.config)
        issues.extend(self.validator.validate_report(report, self.config.min_quality_score))
        if issues:
            logger.log({"event": "audio_qc_failed", "issues": issues})
            return {"success": False, "error": {"code": "AUDIO_QC_FAILED", "issues": issues}, "audio_qc_report": report}
        package = _build_package(voice_plan, pronunciation_dictionary, ssml, ssml_metadata, voice_timestamps, report, self.config)
        report_path = self.config.output_directory / "audio_qc_report.json"
        package_path = self.config.output_directory / "voice-production-package.json"
        write_json_file(report_path, report)
        write_json_file(package_path, package)
        logger.log({"event": "voice_production_package_written", "report_path": str(report_path), "package_path": str(package_path)})
        return {"success": True, "audio_qc_report": report, "voice_production_package": package, "audio_qc_report_path": str(report_path), "voice_production_package_path": str(package_path)}


def _build_report(voice_plan: dict[str, Any], dictionary: dict[str, Any], ssml: str, timestamps: dict[str, Any], config: AudioQCConfig) -> dict[str, Any]:
    narration = " ".join(section.get("narration_text", "") for section in voice_plan.get("sections", []))
    word_count = len(re.findall(r"\b[\w'-]+\b", narration))
    duration = float(timestamps.get("total_estimated_duration", 0))
    wpm = round((word_count / duration) * 60, 2) if duration else 0
    warnings = []
    clarity = 95 if ssml.startswith("<speak>") else 60
    naturalness = 92 if len(timestamps.get("pauses", [])) >= len(voice_plan.get("sections", [])) else 78
    pace = 95 if config.min_wpm <= wpm <= config.max_wpm and duration <= config.max_duration_seconds else 65
    pronunciation = _pronunciation_score(narration, dictionary, warnings)
    brand_voice = _brand_score(narration, config.forbidden_language, warnings)
    if _has_repeated_words(narration):
        warnings.append("Repeated adjacent word detected.")
        naturalness -= 20
    overall = round((clarity + naturalness + pace + pronunciation + brand_voice) / 5)
    approval = "approved" if overall >= config.min_quality_score and not any("Forbidden" in warning for warning in warnings) and duration <= config.max_duration_seconds else "blocked"
    return {
        "production_id": voice_plan["production_id"],
        "component_id": config.component_id,
        "component_name": config.component_name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "overall_score": overall,
        "clarity": clarity,
        "naturalness": naturalness,
        "pace": pace,
        "pronunciation": pronunciation,
        "brand_voice": brand_voice,
        "word_count": word_count,
        "estimated_duration_seconds": round(duration, 2),
        "estimated_wpm": wpm,
        "warnings": warnings,
        "approval_status": approval,
    }


def _pronunciation_score(narration: str, dictionary: dict[str, Any], warnings: list[str]) -> int:
    terms = [item["term"] for item in dictionary.get("items", [])]
    missing = [term for term in ["Liverpool", "Arsenal", "Premier League"] if term.lower() in narration.lower() and term not in terms]
    if missing:
        warnings.append("Pronunciation coverage missing: " + ", ".join(missing))
        return 70
    return 95


def _brand_score(narration: str, forbidden: list[str], warnings: list[str]) -> int:
    found = [word for word in forbidden if re.search(rf"\b{re.escape(word)}\b", narration, flags=re.IGNORECASE)]
    if found:
        warnings.append("Forbidden betting or hype language found: " + ", ".join(found))
        return 45
    return 96


def _has_repeated_words(text: str) -> bool:
    return bool(re.search(r"\b(\w+)\s+\1\b", text, flags=re.IGNORECASE))


def _build_package(voice_plan: dict[str, Any], dictionary: dict[str, Any], ssml: str, metadata: dict[str, Any], timestamps: dict[str, Any], report: dict[str, Any], config: AudioQCConfig) -> dict[str, Any]:
    return {
        "production_id": voice_plan["production_id"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "voice_plan": voice_plan,
        "pronunciation_dictionary": dictionary,
        "voice_ssml": ssml,
        "ssml_metadata": metadata,
        "voice_timestamps": timestamps,
        "audio_qc_report": report,
        "provider_compatibility": {
            "mode": "metadata_only_no_audio_generation",
            "compatible_providers": config.compatible_providers,
            "required_methods": ["generate_voice", "list_voices", "validate_ssml", "estimate_duration"],
        },
        "approval_status": "approved",
        "next_component": "Future Rendering Engine",
    }
