from __future__ import annotations

from pathlib import Path
from typing import Any

from .errors import ValidationError
from .json_utils import load_json_file
from .schema_validator import SchemaValidator


class VisualDirectorValidator:
    def __init__(self, storyboard_schema: Path, asset_schema: Path, output_schema: Path, templates: list[str], layouts: list[str]):
        self.storyboard_schema = load_json_file(storyboard_schema)
        self.asset_schema = load_json_file(asset_schema)
        self.output_schema = load_json_file(output_schema)
        self.templates = set(templates)
        self.layouts = set(layouts)
        self.schema_validator = SchemaValidator()

    def validate_inputs(self, storyboard: dict[str, Any], asset_package: dict[str, Any]) -> None:
        issues = []
        issues.extend(self.schema_validator.validate(storyboard, self.storyboard_schema))
        issues.extend(self.schema_validator.validate(asset_package, self.asset_schema))
        if storyboard.get("production_id") != asset_package.get("production_id"):
            issues.append("$.production_id: inputs must match")
        if issues:
            raise ValidationError("Visual Director input validation failed", sorted(set(issues)))

    def validate_output(self, plan: dict[str, Any], storyboard: dict[str, Any]) -> None:
        issues = self.schema_validator.validate(plan, self.output_schema)
        if len(plan.get("scenes", [])) != len(storyboard.get("scenes", [])):
            issues.append("$.scenes: every storyboard scene must be mapped")
        for scene in plan.get("scenes", []):
            for field in ["template_id", "layout_type", "background_asset", "foreground_assets", "camera_style", "motion_style", "transition_style", "caption_style", "dashboard_usage", "safe_area_notes"]:
                if field not in scene or scene[field] in ("", []):
                    issues.append(f"{scene.get('scene_id')}.{field}: required")
            if scene.get("template_id") not in self.templates:
                issues.append(f"{scene.get('scene_id')}.template_id: unsupported")
            if scene.get("layout_type") not in self.layouts:
                issues.append(f"{scene.get('scene_id')}.layout_type: unsupported")
        if issues:
            raise ValidationError("Visual Director output validation failed", sorted(set(issues)))

