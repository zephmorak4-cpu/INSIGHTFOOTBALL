from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import MotionPlannerConfig
from .json_utils import load_json_file, write_json_file
from .logging_utils import StructuredLogger
from .validation import MotionPlannerValidator


PRESET_BY_TYPE = {
    "Brand Opening": "Fade",
    "Surprising Fact": "Counter",
    "Central Question": "Text Reveal",
    "Tactical Moment": "Arrow Animation",
    "Team Comparison": "Slide",
    "Evidence Card": "Pop",
    "Insight Dashboard": "Dashboard Reveal",
    "X-Factor Player": "Highlight Pulse",
    "Final Question / CTA": "Scale",
}


class MotionPlannerService:
    def __init__(self, config: MotionPlannerConfig):
        self.config = config
        self.validator = MotionPlannerValidator(config.allowed_motion_presets)

    def run_from_file(self, visual_plan_path: Path) -> dict[str, Any]:
        return self.run(load_json_file(visual_plan_path))

    def run(self, visual_plan: dict[str, Any]) -> dict[str, Any]:
        production_id = visual_plan.get("production_id", "unknown-production")
        logger = StructuredLogger(self.config.log_directory, f"motion-planner-{production_id}")
        issues = self.validator.validate_input(visual_plan)
        scenes = []
        for index, scene in enumerate(visual_plan.get("scenes", [])):
            preset = PRESET_BY_TYPE.get(scene["scene_type"], "Fade")
            scenes.append({
                "scene_id": scene["scene_id"],
                "motion_preset": preset,
                "duration": 0.8 if preset not in {"Dashboard Reveal", "Arrow Animation"} else 1.2,
                "delay": 0.1 if index else 0.0,
                "easing": "easeOutCubic",
                "animation_reason": f"{preset} clarifies the {scene['scene_type'].lower()} without flashy effects.",
            })
        plan = {
            "production_id": visual_plan.get("production_id", ""),
            "component_id": self.config.component_id,
            "component_name": self.config.component_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source_visual_plan": visual_plan.get("production_id", ""),
            "scenes": scenes,
            "warnings": [],
            "approval_status": "approved" if not issues else "blocked",
            "next_component": self.config.next_component,
        }
        issues.extend(self.validator.validate_output(plan))
        if issues:
            logger.log({"event": "motion_planning_failed", "issues": issues})
            return {"success": False, "error": {"code": "MOTION_PLANNING_FAILED", "issues": issues}, "motion_plan": plan}
        path = self.config.output_directory / "motion_plan.json"
        write_json_file(path, plan)
        logger.log({"event": "motion_plan_written", "output_path": str(path)})
        return {"success": True, "motion_plan": plan, "motion_plan_path": str(path)}
