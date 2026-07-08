from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import CameraPlannerConfig
from .json_utils import load_json_file, write_json_file
from .logging_utils import StructuredLogger
from .validation import CameraPlannerValidator


CAMERA_BY_TYPE = {
    "Brand Opening": ("Reveal", 1.0, "center", "brand logo"),
    "Surprising Fact": ("Punch In", 1.08, "center", "fact card"),
    "Central Question": ("Slow Zoom", 1.06, "center", "question text"),
    "Tactical Moment": ("Pan", 1.0, "right", "pitch board"),
    "Team Comparison": ("Slide Left", 1.0, "left", "team comparison"),
    "Evidence Card": ("Punch In", 1.05, "center", "evidence card"),
    "Insight Dashboard": ("Static", 1.0, "center", "dashboard"),
    "X-Factor Player": ("Slow Zoom", 1.07, "center", "x-factor card"),
    "Final Question / CTA": ("Pull Back", 0.96, "center", "CTA text"),
}


class CameraPlannerService:
    def __init__(self, config: CameraPlannerConfig):
        self.config = config
        self.validator = CameraPlannerValidator(config.allowed_camera_moves)

    def run_from_file(self, visual_plan_path: Path) -> dict[str, Any]:
        return self.run(load_json_file(visual_plan_path))

    def run(self, visual_plan: dict[str, Any]) -> dict[str, Any]:
        production_id = visual_plan.get("production_id", "unknown-production")
        logger = StructuredLogger(self.config.log_directory, f"camera-planner-{production_id}")
        issues = self.validator.validate_input(visual_plan)
        scenes = []
        for scene in visual_plan.get("scenes", []):
            preset, zoom, pan, target = CAMERA_BY_TYPE.get(scene["scene_type"], ("Static", 1.0, "center", "primary text"))
            duration = float(scene.get("duration_seconds", 0) or 0) or 4.0
            scenes.append({
                "scene_id": scene["scene_id"],
                "camera_preset": preset,
                "camera_duration": duration,
                "zoom_level": zoom,
                "pan_direction": pan,
                "focus_target": target,
                "camera_reason": f"{preset} supports the {scene['scene_type'].lower()} without random movement.",
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
            logger.log({"event": "camera_planning_failed", "issues": issues})
            return {"success": False, "error": {"code": "CAMERA_PLANNING_FAILED", "issues": issues}, "camera_plan": plan}
        path = self.config.output_directory / "camera_plan.json"
        write_json_file(path, plan)
        logger.log({"event": "camera_plan_written", "output_path": str(path)})
        return {"success": True, "camera_plan": plan, "camera_plan_path": str(path)}
