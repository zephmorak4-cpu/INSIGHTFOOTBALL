from __future__ import annotations

from pathlib import Path
from typing import Any

from .config import VisualDirectorConfig
from .errors import ValidationError
from .json_utils import load_json_file, write_json_file
from .logging_utils import StructuredLogger
from .planner import build_visual_plan
from .validation import VisualDirectorValidator


class VisualDirectorService:
    def __init__(self, config: VisualDirectorConfig):
        self.config = config
        self.validator = VisualDirectorValidator(config.storyboard_schema, config.asset_package_schema, config.output_schema, config.allowed_templates, config.allowed_layouts)

    def run_from_files(self, storyboard_path: Path, asset_package_path: Path) -> dict[str, Any]:
        return self.run(load_json_file(storyboard_path), load_json_file(asset_package_path))

    def run(self, storyboard: dict[str, Any], asset_package: dict[str, Any]) -> dict[str, Any]:
        production_id = storyboard.get("production_id", "unknown-production")
        logger = StructuredLogger(self.config.log_directory, f"visual-director-{production_id}")
        try:
            self.validator.validate_inputs(storyboard, asset_package)
            plan = build_visual_plan(storyboard, asset_package, self.config)
            self.validator.validate_output(plan, storyboard)
        except ValidationError as exc:
            logger.log({"event": "visual_direction_failed", "issues": exc.issues})
            return {"success": False, "component_id": self.config.component_id, "component_name": self.config.component_name, "production_id": production_id, "error": {"code": "VISUAL_DIRECTION_FAILED", "issues": exc.issues}, "approval_status": "blocked"}
        output_path = self.config.output_directory / "visual_plan.json"
        write_json_file(output_path, plan)
        logger.log({"event": "visual_plan_written", "output_path": str(output_path)})
        return {"success": True, "visual_plan": plan, "visual_plan_path": str(output_path)}

