"""Scene Planner service."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .config import ScenePlannerConfig
from .errors import ValidationError
from .json_utils import load_json_file, write_json_file
from .logging_utils import StructuredLogger
from .planner import plan_scenes
from .validation import ScenePlannerValidator


class ScenePlannerService:
    def __init__(self, config: ScenePlannerConfig):
        self.config = config
        self.validator = ScenePlannerValidator(config.input_schema, config.script_package_schema, config.output_schema, config.allowed_scene_types, config.allowed_template_ids, config.max_text_per_scene)

    def run_from_files(self, storyboard_path: Path, script_package_path: Path) -> dict[str, Any]:
        return self.run(load_json_file(storyboard_path), load_json_file(script_package_path))

    def run(self, storyboard: dict[str, Any], script_package: dict[str, Any]) -> dict[str, Any]:
        production_id = storyboard.get("production_id", "unknown-production")
        logger = StructuredLogger(self.config.log_directory, f"scene-planner-{production_id}")
        try:
            self.validator.validate_inputs(storyboard, script_package)
            scene_list = plan_scenes(storyboard, script_package, self.config)
            self.validator.validate_output(scene_list, script_package)
        except ValidationError as exc:
            logger.log({"event": "scene_planning_failed", "issues": exc.issues})
            return {"success": False, "component_id": self.config.component_id, "component_name": self.config.component_name, "production_id": production_id, "error": {"code": "SCENE_PLANNING_FAILED", "issues": exc.issues}, "approval_status": "blocked"}
        output_path = self.config.output_directory / "scene_list.json"
        write_json_file(output_path, scene_list)
        logger.log({"event": "scene_list_written", "output_path": str(output_path), "scene_count": scene_list["scene_count"]})
        return {"success": True, "scene_list": scene_list, "scene_list_path": str(output_path)}

