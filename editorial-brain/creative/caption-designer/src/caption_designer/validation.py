from __future__ import annotations

from typing import Any


class CaptionDesignerValidator:
    def __init__(self, max_words_per_line: int, max_lines: int):
        self.max_words_per_line = max_words_per_line
        self.max_lines = max_lines

    def validate_input(self, visual_plan: dict[str, Any]) -> list[str]:
        issues = []
        if not visual_plan.get("production_id"):
            issues.append("$.production_id: required")
        if not visual_plan.get("scenes"):
            issues.append("$.scenes: required")
        return issues

    def validate_output(self, caption_plan: dict[str, Any]) -> list[str]:
        issues = []
        for scene in caption_plan.get("scenes", []):
            lines = str(scene.get("caption", "")).split("\n")
            if len(lines) > self.max_lines:
                issues.append(f"{scene.get('scene_id')}: too many caption lines")
            if any(len(line.split()) > self.max_words_per_line for line in lines):
                issues.append(f"{scene.get('scene_id')}: caption line too long")
            if "safe" not in scene.get("caption_position", ""):
                issues.append(f"{scene.get('scene_id')}: safe caption position required")
        return issues
