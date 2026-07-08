from __future__ import annotations

from typing import Any


class MotionPlannerValidator:
    def __init__(self, allowed_presets: list[str]):
        self.allowed_presets = set(allowed_presets)

    def validate_input(self, visual_plan: dict[str, Any]) -> list[str]:
        issues = []
        if not visual_plan.get("production_id"):
            issues.append("$.production_id: required")
        if not visual_plan.get("scenes"):
            issues.append("$.scenes: required")
        return issues

    def validate_output(self, motion_plan: dict[str, Any]) -> list[str]:
        issues = []
        for scene in motion_plan.get("scenes", []):
            if scene.get("motion_preset") not in self.allowed_presets:
                issues.append(f"{scene.get('scene_id')}: unsupported motion preset")
            if scene.get("duration", 0) <= 0:
                issues.append(f"{scene.get('scene_id')}: duration must be positive")
            if not scene.get("animation_reason"):
                issues.append(f"{scene.get('scene_id')}: animation_reason required")
        return issues
