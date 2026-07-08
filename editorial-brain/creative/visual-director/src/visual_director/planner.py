from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


LAYOUT_BY_TYPE = {
    "Brand Opening": "center_brand",
    "Surprising Fact": "stat_focus",
    "Central Question": "question_focus",
    "Tactical Moment": "pitch_board",
    "Team Comparison": "split_comparison",
    "Evidence Card": "evidence_card",
    "Insight Dashboard": "dashboard",
    "X-Factor Player": "player_focus",
    "Final Question / CTA": "cta_focus",
}


def build_visual_plan(storyboard: dict[str, Any], asset_package: dict[str, Any], config: Any) -> dict[str, Any]:
    asset_lookup = _asset_lookup(asset_package)
    graphics = {item["scene_id"]: item["graphic_id"] for item in asset_package["graphic_requirements"]["scene_graphic_map"]}
    scenes = []
    for scene in storyboard["scenes"]:
        asset_ids = scene.get("required_assets", [])
        scenes.append(
            {
                "scene_id": scene["scene_id"],
                "scene_type": scene["scene_type"],
                "template_id": scene["template_id"],
                "layout_type": LAYOUT_BY_TYPE.get(scene["scene_type"], "card"),
                "background_asset": _background_for(scene, asset_lookup),
                "foreground_assets": asset_ids,
                "primary_text": scene.get("primary_text", ""),
                "secondary_text": scene.get("secondary_text", ""),
                "team_badges": [asset for asset in asset_ids if "team" in asset or "logo" in asset],
                "player_assets": [asset for asset in asset_ids if "player" in asset],
                "graphic_assets": [graphics.get(scene["scene_id"], scene["template_id"])],
                "camera_style": _camera_style(scene["scene_type"]),
                "motion_style": scene.get("motion_preset", "Fade"),
                "transition_style": scene.get("transition_preset", "Fade"),
                "caption_style": "lower_safe_two_line",
                "dashboard_usage": "visible" if scene["scene_type"] == "Insight Dashboard" else "hidden",
                "safe_area_notes": scene.get("safe_area_notes", "Keep text inside 80% vertical safe area."),
            }
        )
    return {
        "production_id": storyboard["production_id"],
        "component_id": config.component_id,
        "component_name": config.component_name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source_storyboard_package": storyboard["production_id"],
        "source_asset_package": asset_package["production_id"],
        "match": storyboard["match"],
        "competition": storyboard["competition"],
        "scenes": scenes,
        "visual_consistency": {"aspect_ratio": "9:16", "style": "clean football newsroom", "safe_area": "center 80%"},
        "warnings": asset_package.get("warnings", []),
        "approval_status": "approved",
        "next_component": config.next_component,
    }


def _asset_lookup(package: dict[str, Any]) -> dict[str, Any]:
    assets = package["asset_manifest"]["required_assets"] + package["asset_manifest"]["optional_assets"]
    return {asset["asset_id"]: asset for asset in assets}


def _background_for(scene: dict[str, Any], assets: dict[str, Any]) -> str:
    if scene["scene_type"] == "Tactical Moment":
        return "pitch_graphic"
    if scene["scene_type"] == "Insight Dashboard":
        return "dashboard_panel"
    return "background_graphic" if "background_graphic" in assets else "stadium_image"


def _camera_style(scene_type: str) -> str:
    return {
        "Brand Opening": "Reveal",
        "Surprising Fact": "Punch In",
        "Central Question": "Slow Zoom",
        "Tactical Moment": "Pan",
        "Team Comparison": "Slide Left",
        "Insight Dashboard": "Static",
        "Final Question / CTA": "Pull Back",
    }.get(scene_type, "Static")

