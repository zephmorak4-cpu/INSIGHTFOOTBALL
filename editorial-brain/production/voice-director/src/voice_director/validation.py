from __future__ import annotations

from typing import Any


class VoiceDirectorValidator:
    def __init__(self, min_wpm: int = 120, max_wpm: int = 145):
        self.min_wpm = min_wpm
        self.max_wpm = max_wpm

    def validate_input(self, script_package: dict[str, Any]) -> list[str]:
        issues = []
        for field in ["production_id", "match", "final_voiceover", "word_count", "approval_status"]:
            if field not in script_package:
                issues.append(f"$.{field}: required")
        if script_package.get("approval_status") != "approved":
            issues.append("$.approval_status: approved script package required")
        if not str(script_package.get("final_voiceover", "")).strip():
            issues.append("$.final_voiceover: cannot be empty")
        return issues

    def validate_output(self, voice_plan: dict[str, Any]) -> list[str]:
        issues = []
        if not voice_plan.get("sections"):
            issues.append("$.sections: required")
        if voice_plan.get("target_speed_wpm", 0) < self.min_wpm or voice_plan.get("target_speed_wpm", 999) > self.max_wpm:
            issues.append("$.target_speed_wpm: must be between 120 and 145")
        for section in voice_plan.get("sections", []):
            for field in ["section_id", "voice_style", "emotion", "pace", "pitch", "energy", "pause_before", "pause_after", "emphasis_words", "breathing_points"]:
                if field not in section:
                    issues.append(f"{section.get('section_id', '<unknown>')}.{field}: required")
        return issues
