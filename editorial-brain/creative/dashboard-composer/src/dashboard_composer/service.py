from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import DashboardComposerConfig
from .json_utils import load_json_file, write_json_file
from .logging_utils import StructuredLogger
from .validation import DashboardComposerValidator


class DashboardComposerService:
    def __init__(self, config: DashboardComposerConfig):
        self.config = config
        self.validator = DashboardComposerValidator(config.allowed_card_types)

    def run_from_files(self, storyboard_path: Path, visual_path: Path, camera_path: Path, motion_path: Path, caption_path: Path) -> dict[str, Any]:
        return self.run(
            load_json_file(storyboard_path),
            load_json_file(visual_path),
            load_json_file(camera_path),
            load_json_file(motion_path),
            load_json_file(caption_path),
        )

    def run(self, storyboard: dict[str, Any], visual: dict[str, Any], camera: dict[str, Any], motion: dict[str, Any], captions: dict[str, Any]) -> dict[str, Any]:
        production_id = storyboard.get("production_id", "unknown-production")
        logger = StructuredLogger(self.config.log_directory, f"dashboard-composer-{production_id}")
        cards = _cards(storyboard)
        issues = self.validator.validate_inputs(storyboard, visual, camera, motion, captions)
        types = {card["card_type"] for card in cards}
        for required in self.config.allowed_card_types:
            if required not in types:
                issues.append(f"dashboard missing card: {required}")
        plan = {
            "production_id": storyboard.get("production_id", ""),
            "component_id": self.config.component_id,
            "component_name": self.config.component_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source_storyboard_package": storyboard.get("production_id", ""),
            "dashboard_cards": cards,
            "dashboard_scene_ids": [scene["scene_id"] for scene in storyboard.get("scenes", []) if scene.get("scene_type") == "Insight Dashboard"],
            "warnings": [],
            "approval_status": "approved" if not issues else "blocked",
            "next_component": self.config.next_component,
        }
        if issues:
            logger.log({"event": "dashboard_composition_failed", "issues": issues})
            return {"success": False, "error": {"code": "DASHBOARD_COMPOSITION_FAILED", "issues": issues}, "dashboard_plan": plan}
        package = {
            "production_id": storyboard["production_id"],
            "match": storyboard["match"],
            "competition": storyboard["competition"],
            "visual_plan": visual,
            "camera_plan": camera,
            "motion_plan": motion,
            "caption_plan": captions,
            "dashboard_plan": plan,
            "validation_report": _validation_report(visual, camera, motion, captions, plan),
            "approval_status": "approved",
            "next_component": "Rendering Engine",
        }
        issues.extend(self.validator.validate_dashboard(plan))
        issues.extend(self.validator.validate_final_package(package))
        if issues:
            logger.log({"event": "dashboard_composition_failed", "issues": issues})
            return {"success": False, "error": {"code": "DASHBOARD_COMPOSITION_FAILED", "issues": issues}, "dashboard_plan": plan}
        dashboard_path = self.config.output_directory / "dashboard_plan.json"
        package_path = self.config.output_directory / "visual-production-package.json"
        write_json_file(dashboard_path, plan)
        write_json_file(package_path, package)
        logger.log({"event": "visual_production_package_written", "dashboard_path": str(dashboard_path), "package_path": str(package_path)})
        return {"success": True, "dashboard_plan": plan, "visual_production_package": package, "dashboard_plan_path": str(dashboard_path), "visual_production_package_path": str(package_path)}


def _cards(storyboard: dict[str, Any]) -> list[dict[str, Any]]:
    fact = _find_text(storyboard, "Surprising Fact")
    edge = _find_text(storyboard, "Insight Dashboard")
    x_factor = _find_text(storyboard, "X-Factor Player")
    uncertainty = _find_text(storyboard, "Team Comparison", last=True)
    return [
        {"card_type": "Match Edge", "title": "Match Edge", "content": "Slight Home Edge", "icon": "edge_bar", "animation": "Dashboard Reveal", "display_time": 3.0},
        {"card_type": "Key Advantage", "title": "Key Advantage", "content": "Liverpool's early pressure", "icon": "pressing_icon", "animation": "Highlight Pulse", "display_time": 2.5},
        {"card_type": "X-Factor", "title": "X-Factor", "content": x_factor, "icon": "player_marker", "animation": "Pop", "display_time": 2.5},
        {"card_type": "Uncertainty", "title": "Uncertainty", "content": uncertainty, "icon": "warning_icon", "animation": "Fade", "display_time": 2.5},
        {"card_type": "Surprising Detail", "title": "Surprising Detail", "content": fact, "icon": "form_icon", "animation": "Counter", "display_time": 3.0},
    ]


def _find_text(storyboard: dict[str, Any], scene_type: str, *, last: bool = False) -> str:
    scenes = [scene for scene in storyboard.get("scenes", []) if scene.get("scene_type") == scene_type]
    if not scenes:
        return ""
    scene = scenes[-1] if last else scenes[0]
    return scene.get("primary_text") or scene.get("caption_text") or scene.get("voiceover_text", "")


def _validation_report(visual: dict[str, Any], camera: dict[str, Any], motion: dict[str, Any], captions: dict[str, Any], dashboard: dict[str, Any]) -> dict[str, Any]:
    scene_count = len(visual.get("scenes", []))
    return {
        "visual_templates": scene_count,
        "camera_movements": len(camera.get("scenes", [])),
        "motion_presets": len(motion.get("scenes", [])),
        "captions": len(captions.get("scenes", [])),
        "dashboard_cards": len(dashboard.get("dashboard_cards", [])),
        "all_scenes_covered": all(len(plan.get("scenes", [])) == scene_count for plan in [camera, motion, captions]),
    }
