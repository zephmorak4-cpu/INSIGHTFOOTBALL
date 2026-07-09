"""Storyboard validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .errors import ValidationError
from .json_utils import load_json_file
from .schema_validator import SchemaValidator


ALLOWED_SCENE_TYPES = {"Brand Opening", "Surprising Fact", "Match Card", "Central Question", "Evidence Card", "Team Comparison", "Tactical Moment", "X-Factor Player", "Insight Dashboard", "Final Question / CTA"}


class StoryboardValidator:
    def __init__(self, script_schema: Path, output_schema: Path):
        self.script_schema = load_json_file(script_schema)
        self.output_schema = load_json_file(output_schema)
        self.schema_validator = SchemaValidator()

    def validate_inputs(self, package: dict[str, Any], voiceover: str) -> None:
        if "final_voiceover" not in package and "full_voiceover" in package:
            package["final_voiceover"] = package["full_voiceover"]
        issues = self.schema_validator.validate(package, self.script_schema)
        if not package.get("production_id"):
            issues.append("$.production_id: required")
        if not voiceover.strip():
            issues.append("voiceover_final.txt: required")
        if package.get("final_voiceover") and package["final_voiceover"].strip() != voiceover.strip():
            issues.append("voiceover_final.txt: must match final script package")
        if issues:
            raise ValidationError("Storyboard Generator input validation failed", issues)

    def validate_output(self, storyboard: dict[str, Any], package: dict[str, Any]) -> None:
        issues = self.schema_validator.validate(storyboard, self.output_schema)
        scenes = storyboard.get("scenes", [])
        if not 8 <= len(scenes) <= 12:
            issues.append("$.scenes: scene count should be between 8 and 12")
        if storyboard.get("total_estimated_duration_seconds", 999) > 60:
            issues.append("$.total_estimated_duration_seconds: must be <= 60")
        previous_end = 0
        voiceover_parts = []
        for scene in scenes:
            for field in ["start_time_seconds", "end_time_seconds", "duration_seconds", "voiceover_text", "caption_text", "on_screen_text", "required_assets"]:
                if field not in scene or scene[field] in ("", []):
                    issues.append(f"{scene.get('scene_id', '$.scene')}.{field}: required")
            if scene.get("scene_type") not in ALLOWED_SCENE_TYPES:
                issues.append(f"{scene.get('scene_id')}.scene_type: invalid")
            if scene.get("start_time_seconds", 0) < previous_end:
                issues.append(f"{scene.get('scene_id')}: overlaps previous scene")
            previous_end = scene.get("end_time_seconds", previous_end)
            voiceover_parts.append(scene.get("voiceover_text", ""))
        if "Insight Dashboard" not in {scene.get("scene_type") for scene in scenes}:
            issues.append("$.scenes: dashboard scene required")
        if "Final Question / CTA" not in {scene.get("scene_type") for scene in scenes}:
            issues.append("$.scenes: CTA scene required")
        expected_voiceover = package.get("final_voiceover") or package.get("full_voiceover", "")
        if " ".join(voiceover_parts).strip() != expected_voiceover.strip():
            issues.append("$.scenes.voiceover_text: must preserve final script order")
        if storyboard.get("locked_fields") != package.get("locked_fields"):
            issues.append("$.locked_fields: must be preserved")
        if issues:
            raise ValidationError("Storyboard Generator output validation failed", sorted(set(issues)))
