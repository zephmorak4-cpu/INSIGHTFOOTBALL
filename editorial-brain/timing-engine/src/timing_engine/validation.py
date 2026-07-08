"""Timing Engine validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .errors import ValidationError
from .json_utils import load_json_file
from .schema_validator import SchemaValidator


class TimingEngineValidator:
    def __init__(self, input_schema: Path, timeline_schema: Path, final_package_schema: Path, max_duration: int):
        self.input_schema = load_json_file(input_schema)
        self.timeline_schema = load_json_file(timeline_schema)
        self.final_package_schema = load_json_file(final_package_schema)
        self.max_duration = max_duration
        self.schema_validator = SchemaValidator()

    def validate_input(self, scene_list: dict[str, Any], voiceover: str) -> None:
        issues = self.schema_validator.validate(scene_list, self.input_schema)
        if not voiceover.strip():
            issues.append("voiceover_final.txt: required")
        previous_end = 0
        for scene in scene_list.get("scenes", []):
            if scene.get("start_time_seconds", 0) < previous_end:
                issues.append(f"{scene.get('scene_id')}: overlaps previous scene")
            previous_end = scene.get("end_time_seconds", previous_end)
        if scene_list.get("total_duration_seconds", 999) > self.max_duration:
            issues.append("$.total_duration_seconds: exceeds 60 seconds")
        if issues:
            raise ValidationError("Timing Engine input validation failed", sorted(set(issues)))

    def validate_timeline(self, timeline: dict[str, Any]) -> None:
        issues = self.schema_validator.validate(timeline, self.timeline_schema)
        if timeline.get("timing_errors"):
            issues.extend(timeline["timing_errors"])
        if issues:
            raise ValidationError("Timing validation failed", sorted(set(issues)))

    def validate_final_package(self, final_package: dict[str, Any]) -> None:
        issues = self.schema_validator.validate(final_package, self.final_package_schema)
        if final_package.get("next_component") != "Asset Planner":
            issues.append("$.next_component: must be Asset Planner")
        if final_package.get("approval_status") != "approved":
            issues.append("$.approval_status: must be approved")
        if issues:
            raise ValidationError("Final storyboard package validation failed", sorted(set(issues)))

