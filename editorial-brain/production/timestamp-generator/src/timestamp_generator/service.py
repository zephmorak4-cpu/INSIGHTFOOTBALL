from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import TimestampGeneratorConfig
from .json_utils import load_json_file, write_json_file
from .logging_utils import StructuredLogger
from .validation import TimestampGeneratorValidator


class TimestampGeneratorService:
    def __init__(self, config: TimestampGeneratorConfig):
        self.config = config
        self.validator = TimestampGeneratorValidator()

    def run_from_files(self, voice_plan_path: Path, ssml_metadata_path: Path) -> dict[str, Any]:
        return self.run(load_json_file(voice_plan_path), load_json_file(ssml_metadata_path))

    def run(self, voice_plan: dict[str, Any], ssml_metadata: dict[str, Any]) -> dict[str, Any]:
        production_id = voice_plan.get("production_id", "unknown-production")
        logger = StructuredLogger(self.config.log_directory, f"timestamp-generator-{production_id}")
        issues = self.validator.validate_inputs(voice_plan, ssml_metadata)
        timestamps = _build_timestamps(voice_plan, ssml_metadata, self.config)
        issues.extend(self.validator.validate_output(timestamps, self.config.max_duration_seconds))
        if issues:
            logger.log({"event": "timestamp_generation_failed", "issues": issues})
            return {"success": False, "error": {"code": "TIMESTAMP_GENERATION_FAILED", "issues": issues}, "voice_timestamps": timestamps}
        path = self.config.output_directory / "voice_timestamps.json"
        write_json_file(path, timestamps)
        logger.log({"event": "voice_timestamps_written", "output_path": str(path), "entries": len(timestamps["entries"])})
        return {"success": True, "voice_timestamps": timestamps, "voice_timestamps_path": str(path)}


def _build_timestamps(voice_plan: dict[str, Any], ssml_metadata: dict[str, Any], config: TimestampGeneratorConfig) -> dict[str, Any]:
    current = 0.0
    entries = []
    emphasis_points = []
    pauses = []
    sentence_index = 1
    for section_index, section in enumerate(voice_plan.get("sections", []), start=1):
        pause_before = float(section.get("pause_before", 0))
        if pause_before:
            pauses.append({"section_id": section["section_id"], "type": "before", "start": round(current, 2), "end": round(current + pause_before, 2), "duration": pause_before})
            current += pause_before
        for sentence in _sentences(section["narration_text"]):
            duration = _duration(sentence, config.speech_rate, config.pause_estimation)
            start = current
            end = current + duration
            entry = {
                "scene_id": f"voice-scene-{section_index:02d}",
                "section_id": section["section_id"],
                "sentence_id": f"sentence-{sentence_index:02d}",
                "sentence": sentence,
                "start": round(start, 2),
                "end": round(end, 2),
                "estimated_duration": round(duration, 2),
            }
            entries.append(entry)
            for word in section.get("emphasis_words", []):
                if word.lower() in sentence.lower():
                    emphasis_points.append({"word": word, "sentence_id": entry["sentence_id"], "time": round(start + min(duration * 0.45, 1.6), 2)})
            current = end + config.pause_estimation["sentence"]
            sentence_index += 1
        pause_after = float(section.get("pause_after", 0))
        if pause_after:
            pauses.append({"section_id": section["section_id"], "type": "after", "start": round(current, 2), "end": round(current + pause_after, 2), "duration": pause_after})
            current += pause_after
    payload = {
        "production_id": voice_plan["production_id"],
        "component_id": config.component_id,
        "component_name": config.component_name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source_voice_plan": voice_plan.get("production_id", ""),
        "source_ssml_metadata": ssml_metadata.get("production_id", ""),
        "speech_rate": config.speech_rate,
        "entries": entries,
        "emphasis_points": emphasis_points,
        "pauses": pauses,
        "total_estimated_duration": round(current, 2),
        "warnings": [],
        "approval_status": "approved",
        "next_component": config.next_component,
    }
    return _fit_to_duration(payload, config.max_duration_seconds)


def _sentences(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", text.strip()) if part.strip()]


def _duration(sentence: str, speech_rate: int, pauses: dict[str, float]) -> float:
    words = len(re.findall(r"\b[\w'-]+\b", sentence))
    base = (words / speech_rate) * 60
    punctuation = 0.0
    punctuation += sentence.count(",") * pauses["comma"]
    punctuation += sentence.count(";") * pauses["semicolon"]
    punctuation += sentence.count(":") * pauses["colon"]
    punctuation += pauses["question"] if sentence.endswith("?") else 0.0
    return max(1.0, base + punctuation)


def _fit_to_duration(timestamps: dict[str, Any], max_duration: float) -> dict[str, Any]:
    total = float(timestamps.get("total_estimated_duration", 0))
    if total <= max_duration or total <= 0:
        return timestamps
    target = max_duration
    factor = target / total
    for entry in timestamps.get("entries", []):
        entry["start"] = round(entry["start"] * factor, 2)
        entry["end"] = round(entry["end"] * factor, 2)
        entry["estimated_duration"] = round(entry["estimated_duration"] * factor, 2)
    for point in timestamps.get("emphasis_points", []):
        point["time"] = round(point["time"] * factor, 2)
    for pause in timestamps.get("pauses", []):
        pause["start"] = round(pause["start"] * factor, 2)
        pause["end"] = round(pause["end"] * factor, 2)
        pause["duration"] = round(pause["duration"] * factor, 2)
    timestamps["total_estimated_duration"] = round(target, 2)
    timestamps["warnings"].append("Timing normalized to fit the 60-second production limit without changing script text.")
    return timestamps
