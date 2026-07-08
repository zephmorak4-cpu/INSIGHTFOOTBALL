"""Asset Planner validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .errors import ValidationError
from .json_utils import load_json_file
from .schema_validator import SchemaValidator


class AssetPlannerValidator:
    def __init__(self, input_schema: Path, output_schema: Path):
        self.input_schema = load_json_file(input_schema)
        self.output_schema = load_json_file(output_schema)
        self.schema_validator = SchemaValidator()

    def validate_input(self, storyboard: dict[str, Any]) -> None:
        issues = self.schema_validator.validate(storyboard, self.input_schema)
        if not storyboard:
            issues.append("final-storyboard-package.json: required")
        if not storyboard.get("scenes"):
            issues.append("$.scenes: required")
        if issues:
            raise ValidationError("Asset Planner input validation failed", issues)

    def validate_output(self, manifest: dict[str, Any], storyboard: dict[str, Any]) -> None:
        issues = self.schema_validator.validate(manifest, self.output_schema)
        scene_ids = {scene["scene_id"] for scene in storyboard.get("scenes", [])}
        mapped = {item["scene_id"] for item in manifest.get("scene_asset_map", [])}
        if scene_ids != mapped:
            issues.append("$.scene_asset_map: every scene must receive asset mapping")
        assets = manifest.get("required_assets", []) + manifest.get("optional_assets", [])
        for asset in assets:
            if "fallback_strategy" not in asset or not asset["fallback_strategy"]:
                issues.append(f"{asset.get('asset_id')}: fallback_strategy required")
            if "legal_status" not in asset or not asset["legal_status"]:
                issues.append(f"{asset.get('asset_id')}: legal_status required")
        asset_ids = {asset["asset_id"] for asset in assets}
        if "dashboard_panel" not in asset_ids:
            issues.append("dashboard asset required")
        if "comment_icon" not in asset_ids:
            issues.append("CTA asset required")
        if any(scene.get("scene_type") == "Tactical Moment" for scene in storyboard.get("scenes", [])) and "pitch_graphic" not in asset_ids:
            issues.append("tactical graphic required")
        if issues:
            raise ValidationError("Asset Planner output validation failed", sorted(set(issues)))

