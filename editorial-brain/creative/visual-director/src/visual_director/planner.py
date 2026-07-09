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
INTERNAL_REPLACEMENTS = {
    "X-Factor": "One Thing That Could Change Everything",
    "Tactical Edge": "Biggest Advantage",
    "Form Index": "Recent Form",
    "Risk Meter": "What Could Go Wrong",
}


def build_visual_plan(storyboard: dict[str, Any], asset_package: dict[str, Any], config: Any) -> dict[str, Any]:
    asset_lookup = _asset_lookup(asset_package)
    graphics = {item["scene_id"]: item["graphic_id"] for item in asset_package["graphic_requirements"]["scene_graphic_map"]}
    scenes = []
    for scene in storyboard["scenes"]:
        asset_ids = scene.get("required_assets", [])
        visual_elements = _visual_elements(scene, asset_ids, graphics.get(scene["scene_id"], scene["template_id"]))
        scenes.append(
            {
                "scene_id": scene["scene_id"],
                "scene_type": scene["scene_type"],
                "template_id": scene["template_id"],
                "layout_type": LAYOUT_BY_TYPE.get(scene["scene_type"], "card"),
                "background_asset": _background_for(scene, asset_lookup),
                "foreground_assets": asset_ids,
                "primary_text": _viewer_text(scene.get("primary_text", "")),
                "secondary_text": _viewer_text(scene.get("secondary_text", "")),
                "team_badges": [asset for asset in asset_ids if "team" in asset or "logo" in asset],
                "player_assets": [asset for asset in asset_ids if "player" in asset],
                "graphic_assets": [graphics.get(scene["scene_id"], scene["template_id"])],
                "visual_elements": visual_elements,
                "broadcast_elements": _broadcast_elements(scene, visual_elements),
                "onscreen_text_policy": {"max_blocks": 3, "headline_plus_two_supporting_lines": True},
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
        "visual_consistency": {"aspect_ratio": "9:16", "style": "premium football broadcast", "safe_area": "center 80%", "version": "2.0"},
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
        "Insight Dashboard": "Slow Zoom",
        "Final Question / CTA": "Pull Back",
    }.get(scene_type, "Slow Zoom")


def _visual_elements(scene: dict[str, Any], asset_ids: list[str], graphic_id: str) -> list[str]:
    base = ["stadium_background", "lower_third", "motion_graphics"]
    scene_type = scene.get("scene_type", "")
    if scene_type == "Brand Opening":
        return ["club_badge_home", "club_badge_away", "competition_logo", "match_title", "modern_scoreboard", "broadcast_animation"]
    if "Tactical" in scene_type:
        base.extend(["pitch_graphic", "arrow_animation", "formation_board"])
    elif "Dashboard" in scene_type or "Evidence" in scene_type:
        base.extend(["dashboard_card", "animated_statistic", graphic_id])
    elif "Comparison" in scene_type:
        base.extend(["club_badge_home", "club_badge_away", "scoreboard"])
    else:
        base.extend(["club_badge_home", "club_badge_away", graphic_id])
    for asset_id in asset_ids:
        if asset_id not in base:
            base.append(asset_id)
    return base[:8]


def _broadcast_elements(scene: dict[str, Any], visual_elements: list[str]) -> dict[str, Any]:
    return {
        "live_score_bar": True,
        "competition_bug": True,
        "ticker": scene.get("scene_type") not in {"Brand Opening"},
        "premium_transition": True,
        "club_badges_visible": "club_badge_home" in visual_elements and "club_badge_away" in visual_elements,
    }


def _viewer_text(text: str) -> str:
    clean = str(text)
    for internal, replacement in INTERNAL_REPLACEMENTS.items():
        clean = clean.replace(internal, replacement)
    return clean
