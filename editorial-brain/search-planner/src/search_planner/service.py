from __future__ import annotations

from pathlib import Path
from typing import Any

from .config import SearchPlannerConfig
from .errors import ValidationError
from .json_utils import load_json_file, write_json_file
from .logging_utils import StructuredLogger
from .planner import build_search_plan
from .validation import SearchPlannerValidator


class SearchPlannerService:
    def __init__(self, config: SearchPlannerConfig):
        self.config = config
        self.validator = SearchPlannerValidator(config.input_schema, config.output_schema, config.blocked_source_types)

    def run_from_file(self, manifest_path: Path) -> dict[str, Any]:
        return self.run(load_json_file(manifest_path))

    def run(self, manifest: dict[str, Any]) -> dict[str, Any]:
        production_id = manifest.get("production_id", "unknown-production")
        logger = StructuredLogger(self.config.log_directory, f"search-planner-{production_id}")
        try:
            self.validator.validate_input(manifest)
            plan = build_search_plan(manifest, self.config)
            self.validator.validate_output(plan, manifest)
        except ValidationError as exc:
            logger.log({"event": "search_planning_failed", "issues": exc.issues})
            return {"success": False, "component_id": self.config.component_id, "component_name": self.config.component_name, "production_id": production_id, "error": {"code": "SEARCH_PLANNING_FAILED", "issues": exc.issues}, "approval_status": "blocked"}
        output_path = self.config.output_directory / "asset_search_plan.json"
        write_json_file(output_path, plan)
        logger.log({"event": "asset_search_plan_written", "output_path": str(output_path)})
        return {"success": True, "asset_search_plan": plan, "asset_search_plan_path": str(output_path)}

