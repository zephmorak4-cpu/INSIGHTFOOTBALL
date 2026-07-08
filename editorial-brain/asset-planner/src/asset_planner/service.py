"""Asset Planner service."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .config import AssetPlannerConfig
from .errors import ValidationError
from .json_utils import load_json_file, write_json_file
from .logging_utils import StructuredLogger
from .planner import build_manifest
from .validation import AssetPlannerValidator


class AssetPlannerService:
    def __init__(self, config: AssetPlannerConfig):
        self.config = config
        self.validator = AssetPlannerValidator(config.input_schema, config.output_schema)

    def run_from_file(self, storyboard_path: Path) -> dict[str, Any]:
        return self.run(load_json_file(storyboard_path))

    def run(self, storyboard: dict[str, Any]) -> dict[str, Any]:
        production_id = storyboard.get("production_id", "unknown-production") if isinstance(storyboard, dict) else "unknown-production"
        logger = StructuredLogger(self.config.log_directory, f"asset-planner-{production_id}")
        try:
            self.validator.validate_input(storyboard)
            manifest = build_manifest(storyboard, self.config)
            self.validator.validate_output(manifest, storyboard)
        except ValidationError as exc:
            logger.log({"event": "asset_planning_failed", "issues": exc.issues})
            return {"success": False, "component_id": self.config.component_id, "component_name": self.config.component_name, "production_id": production_id, "error": {"code": "ASSET_PLANNING_FAILED", "issues": exc.issues}, "approval_status": "blocked"}
        output_path = self.config.output_directory / "asset_manifest.json"
        write_json_file(output_path, manifest)
        logger.log({"event": "asset_manifest_written", "output_path": str(output_path), "missing_assets": manifest["missing_assets"]})
        return {"success": True, "asset_manifest": manifest, "asset_manifest_path": str(output_path)}

