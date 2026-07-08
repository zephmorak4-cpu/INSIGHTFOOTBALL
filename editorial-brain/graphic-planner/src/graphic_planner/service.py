from __future__ import annotations

from pathlib import Path
from typing import Any

from .config import GraphicPlannerConfig
from .errors import ValidationError
from .json_utils import load_json_file, write_json_file
from .logging_utils import StructuredLogger
from .planner import build_final_asset_package, build_graphics
from .validation import GraphicPlannerValidator


class GraphicPlannerService:
    def __init__(self, config: GraphicPlannerConfig):
        self.config = config
        self.validator = GraphicPlannerValidator(config.storyboard_schema, config.manifest_schema, config.search_plan_schema, config.output_schema, config.final_package_schema, config.allowed_graphic_types)

    def run_from_files(self, storyboard_path: Path, manifest_path: Path, search_plan_path: Path) -> dict[str, Any]:
        return self.run(load_json_file(storyboard_path), load_json_file(manifest_path), load_json_file(search_plan_path))

    def run(self, storyboard: dict[str, Any], manifest: dict[str, Any], search_plan: dict[str, Any]) -> dict[str, Any]:
        production_id = storyboard.get("production_id", "unknown-production")
        logger = StructuredLogger(self.config.log_directory, f"graphic-planner-{production_id}")
        try:
            self.validator.validate_inputs(storyboard, manifest, search_plan)
            graphics = build_graphics(storyboard, manifest, search_plan, self.config)
            self.validator.validate_graphics(graphics, storyboard)
            final_package = build_final_asset_package(storyboard, manifest, search_plan, graphics, self.config)
            self.validator.validate_final_package(final_package, storyboard)
        except ValidationError as exc:
            logger.log({"event": "graphic_planning_failed", "issues": exc.issues})
            return {"success": False, "component_id": self.config.component_id, "component_name": self.config.component_name, "production_id": production_id, "error": {"code": "GRAPHIC_PLANNING_FAILED", "issues": exc.issues}, "approval_status": "blocked"}
        graphics_path = self.config.output_directory / "graphic_requirements.json"
        final_path = self.config.output_directory / "final-asset-package.json"
        write_json_file(graphics_path, graphics)
        write_json_file(final_path, final_package)
        logger.log({"event": "graphic_requirements_written", "graphics_path": str(graphics_path), "final_asset_package": str(final_path)})
        return {"success": True, "graphic_requirements": graphics, "final_asset_package": final_package, "graphic_requirements_path": str(graphics_path), "final_asset_package_path": str(final_path)}

