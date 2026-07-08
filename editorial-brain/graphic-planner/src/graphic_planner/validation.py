from __future__ import annotations

from pathlib import Path
from typing import Any

from .errors import ValidationError
from .json_utils import load_json_file
from .schema_validator import SchemaValidator


class GraphicPlannerValidator:
    def __init__(self, storyboard_schema: Path, manifest_schema: Path, search_schema: Path, output_schema: Path, final_schema: Path, allowed_graphic_types: list[str]):
        self.storyboard_schema = load_json_file(storyboard_schema)
        self.manifest_schema = load_json_file(manifest_schema)
        self.search_schema = load_json_file(search_schema)
        self.output_schema = load_json_file(output_schema)
        self.final_schema = load_json_file(final_schema)
        self.allowed_graphic_types = set(allowed_graphic_types)
        self.schema_validator = SchemaValidator()

    def validate_inputs(self, storyboard: dict[str, Any], manifest: dict[str, Any], search_plan: dict[str, Any]) -> None:
        issues = []
        issues.extend(self.schema_validator.validate(storyboard, self.storyboard_schema))
        issues.extend(self.schema_validator.validate(manifest, self.manifest_schema))
        issues.extend(self.schema_validator.validate(search_plan, self.search_schema))
        if storyboard.get("production_id") != manifest.get("production_id") or manifest.get("production_id") != search_plan.get("production_id"):
            issues.append("$.production_id: all inputs must match")
        if issues:
            raise ValidationError("Graphic Planner input validation failed", sorted(set(issues)))

    def validate_graphics(self, graphics: dict[str, Any], storyboard: dict[str, Any]) -> None:
        issues = self.schema_validator.validate(graphics, self.output_schema)
        types = {graphic["graphic_type"] for graphic in graphics.get("required_graphics", [])}
        if "insight_dashboard" not in types:
            issues.append("dashboard graphics required")
        if any(scene["scene_type"] == "Tactical Moment" for scene in storyboard.get("scenes", [])) and "tactical_pitch_diagram" not in types:
            issues.append("tactical graphics required")
        if "cta_card" not in types:
            issues.append("CTA graphics required")
        for graphic in graphics.get("required_graphics", []) + graphics.get("caption_graphics", []):
            if graphic.get("graphic_type") not in self.allowed_graphic_types:
                issues.append(f"{graphic.get('graphic_id')}: invalid graphic type")
            if not graphic.get("recommended_dimensions"):
                issues.append(f"{graphic.get('graphic_id')}: dimensions required")
        scene_ids = {scene["scene_id"] for scene in storyboard.get("scenes", [])}
        mapped = {item["scene_id"] for item in graphics.get("scene_graphic_map", [])}
        if scene_ids != mapped:
            issues.append("$.scene_graphic_map: every scene must be mapped")
        if issues:
            raise ValidationError("Graphic requirements validation failed", sorted(set(issues)))

    def validate_final_package(self, package: dict[str, Any], storyboard: dict[str, Any]) -> None:
        issues = self.schema_validator.validate(package, self.final_schema)
        if package.get("locked_fields") != storyboard.get("locked_fields"):
            issues.append("$.locked_fields: must be preserved")
        if package.get("next_component") != "Visual Director":
            issues.append("$.next_component: must be Visual Director")
        if issues:
            raise ValidationError("Final asset package validation failed", sorted(set(issues)))

