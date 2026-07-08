from __future__ import annotations

from typing import Any


class TimestampGeneratorValidator:
    def validate_inputs(self, voice_plan: dict[str, Any], ssml_metadata: dict[str, Any]) -> list[str]:
        issues = []
        if voice_plan.get("production_id") != ssml_metadata.get("production_id"):
            issues.append("$.production_id: voice plan and SSML metadata must match")
        if not voice_plan.get("sections"):
            issues.append("$.voice_plan.sections: required")
        return issues

    def validate_output(self, timestamps: dict[str, Any], max_duration: float) -> list[str]:
        issues = []
        entries = timestamps.get("entries", [])
        if not entries:
            issues.append("$.entries: required")
        previous_end = 0.0
        for entry in entries:
            if entry.get("end", 0) < entry.get("start", 0):
                issues.append(f"{entry.get('scene_id')}: end must be after start")
            if entry.get("start", 0) < previous_end - 0.01:
                issues.append(f"{entry.get('scene_id')}: timestamps overlap")
            previous_end = entry.get("end", previous_end)
        if timestamps.get("total_estimated_duration", 0) > max_duration:
            issues.append("$.total_estimated_duration: narration exceeds 60 seconds")
        return issues
