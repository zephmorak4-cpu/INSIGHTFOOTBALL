from __future__ import annotations

from typing import Any


class AudioQCValidator:
    def validate_inputs(self, voice_plan: dict[str, Any], dictionary: dict[str, Any], metadata: dict[str, Any], timestamps: dict[str, Any]) -> list[str]:
        issues = []
        ids = {voice_plan.get("production_id"), dictionary.get("production_id"), metadata.get("production_id"), timestamps.get("production_id")}
        if len(ids) != 1:
            issues.append("$.production_id: all voice inputs must match")
        for name, payload in [("voice_plan", voice_plan), ("pronunciation_dictionary", dictionary), ("ssml_metadata", metadata), ("voice_timestamps", timestamps)]:
            if payload.get("approval_status") != "approved":
                issues.append(f"$.{name}.approval_status: approved required")
        return issues

    def validate_report(self, report: dict[str, Any], min_quality_score: int) -> list[str]:
        issues = []
        if report.get("overall_score", 0) < min_quality_score:
            issues.append("$.overall_score: below minimum quality score")
        if report.get("approval_status") != "approved":
            issues.append("$.approval_status: approved required")
        return issues
