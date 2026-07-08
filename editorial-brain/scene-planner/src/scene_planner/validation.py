"""Scene Planner validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .errors import ValidationError
from .json_utils import load_json_file
from .schema_validator import SchemaValidator


class ScenePlannerValidator:
    def __init__(self, input_schema: Path, script_schema: Path, output_schema: Path, allowed_scene_types: list[str], allowed_template_ids: list[str], max_text_per_scene: int):
        self.input_schema = load_json_file(input_schema)
        self.script_schema = load_json_file(script_schema)
        self.output_schema = load_json_file(output_schema)
        self.allowed_scene_types = set(allowed_scene_types)
        self.allowed_template_ids = set(allowed_template_ids)
        self.max_text_per_scene = max_text_per_scene
        self.schema_validator = SchemaValidator()

    def validate_inputs(self, storyboard: dict[str, Any], script_package: dict[str, Any]) -> None:
        issues = []
        issues.extend(self.schema_validator.validate(storyboard, self.input_schema))
        issues.extend(self.schema_validator.validate(script_package, self.script_schema))
        if storyboard.get("production_id") != script_package.get("production_id"):
            issues.append("$.production_id: storyboard and script package must match")
        for scene in storyboard.get("scenes", []):
            if scene.get("scene_type") not in self.allowed_scene_types:
                issues.append(f"{scene.get('scene_id')}.scene_type: unknown")
            if not scene.get("caption_text"):
                issues.append(f"{scene.get('scene_id')}.caption_text: required")
        if issues:
            raise ValidationError("Scene Planner input validation failed", sorted(set(issues)))

    def validate_output(self, scene_list: dict[str, Any], script_package: dict[str, Any]) -> None:
        issues = self.schema_validator.validate(scene_list, self.output_schema)
        scene_types = {scene.get("scene_type") for scene in scene_list.get("scenes", [])}
        templates = {scene.get("template_id") for scene in scene_list.get("scenes", [])}
        if "Final Question / CTA" not in scene_types:
            issues.append("$.scenes: CTA scene required")
        if "Insight Dashboard" not in scene_types:
            issues.append("$.scenes: dashboard scene required")
        for template in templates:
            if template not in self.allowed_template_ids:
                issues.append(f"template_id unknown: {template}")
        if not scene_list.get("locked_fields_preserved"):
            issues.append("$.locked_fields_preserved: must be true")
        previous_end = 0
        voiceover_parts = []
        for scene in scene_list.get("scenes", []):
            if scene.get("start_time_seconds", 0) < previous_end:
                issues.append(f"{scene.get('scene_id')}: overlaps previous scene")
            previous_end = scene.get("end_time_seconds", previous_end)
            voiceover_parts.append(scene.get("voiceover_text", ""))
        if " ".join(voiceover_parts).strip() != script_package.get("final_voiceover", "").strip():
            issues.append("$.scenes: must preserve script order")
        if issues:
            raise ValidationError("Scene Planner output validation failed", sorted(set(issues)))

