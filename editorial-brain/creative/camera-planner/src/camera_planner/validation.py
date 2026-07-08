from __future__ import annotations

from typing import Any


class CameraPlannerValidator:
    def __init__(self, allowed_moves: list[str]):
        self.allowed_moves = set(allowed_moves)

    def validate_input(self, visual_plan: dict[str, Any]) -> list[str]:
        issues = []
        if not visual_plan.get("production_id"):
            issues.append("$.production_id: required")
        if not visual_plan.get("scenes"):
            issues.append("$.scenes: required")
        return issues

    def validate_output(self, camera_plan: dict[str, Any]) -> list[str]:
        issues = []
        for scene in camera_plan.get("scenes", []):
            if scene.get("camera_preset") not in self.allowed_moves:
                issues.append(f"{scene.get('scene_id')}: unsupported camera preset")
            if scene.get("camera_duration", 0) <= 0:
                issues.append(f"{scene.get('scene_id')}: camera_duration must be positive")
            if not scene.get("camera_reason"):
                issues.append(f"{scene.get('scene_id')}: camera_reason required")
        return issues
