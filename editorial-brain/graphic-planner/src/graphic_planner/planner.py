"""Graphic requirements and final package assembly."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


GRAPHIC_BY_SCENE = {
    "Brand Opening": ("match_title_card", "Match title card"),
    "Surprising Fact": ("surprising_fact_card", "Surprising fact card"),
    "Central Question": ("central_question_card", "Central question card"),
    "Evidence Card": ("evidence_card", "Evidence card"),
    "Team Comparison": ("team_comparison_card", "Team comparison card"),
    "Tactical Moment": ("tactical_pitch_diagram", "Tactical pitch diagram"),
    "X-Factor Player": ("x_factor_card", "X-factor card"),
    "Insight Dashboard": ("insight_dashboard", "Insight dashboard"),
    "Final Question / CTA": ("cta_card", "CTA card"),
}


def build_graphics(storyboard: dict[str, Any], manifest: dict[str, Any], search_plan: dict[str, Any], config: Any) -> dict[str, Any]:
    graphics = []
    scene_map = []
    seen = {}
    for scene in storyboard["scenes"]:
        graphic_type, name = GRAPHIC_BY_SCENE.get(scene["scene_type"], ("template_card", "Template card"))
        graphic_id = f"graphic-{graphic_type}"
        if graphic_id not in seen:
            seen[graphic_id] = _graphic(graphic_id, name, graphic_type, scene, config)
        else:
            seen[graphic_id]["scenes_used"].append(scene["scene_id"])
            seen[graphic_id]["text_content"].append(scene["primary_text"])
        scene_map.append({"scene_id": scene["scene_id"], "graphic_id": graphic_id, "graphic_type": graphic_type})
    graphics = list(seen.values())
    return {
        "production_id": storyboard["production_id"],
        "component_id": config.component_id,
        "component_name": config.component_name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source_storyboard_package": storyboard["production_id"],
        "required_graphics": graphics,
        "dashboard_graphics": [g for g in graphics if g["graphic_type"] == "insight_dashboard"],
        "tactical_graphics": [g for g in graphics if g["graphic_type"] == "tactical_pitch_diagram"],
        "caption_graphics": [_caption_graphic(scene, config) for scene in storyboard["scenes"]],
        "reusable_template_graphics": [g for g in graphics if g["graphic_type"] in {"match_title_card", "team_comparison_card", "insight_dashboard", "cta_card"}],
        "scene_graphic_map": scene_map,
        "approval_status": "approved",
        "next_component": config.next_component,
    }


def build_final_asset_package(storyboard: dict[str, Any], manifest: dict[str, Any], search_plan: dict[str, Any], graphics: dict[str, Any], config: Any) -> dict[str, Any]:
    manual_actions = [task["description"] for task in search_plan.get("manual_tasks", []) + search_plan.get("legal_review_tasks", []) + search_plan.get("generation_tasks", [])]
    readiness = "blocked_pending_manual_assets" if search_plan.get("legal_review_tasks") or search_plan.get("manual_tasks") else "ready_for_visual_direction"
    warnings = sorted(set(manifest.get("legal_warnings", []) + [task["legal_notes"] for task in search_plan.get("legal_review_tasks", [])]))
    return {
        "production_id": storyboard["production_id"],
        "match": storyboard["match"],
        "competition": storyboard["competition"],
        "source_storyboard_package": storyboard["production_id"],
        "asset_manifest": manifest,
        "asset_search_plan": search_plan,
        "graphic_requirements": graphics,
        "missing_assets": manifest["missing_assets"],
        "legal_warnings": manifest["legal_warnings"],
        "required_manual_actions": manual_actions,
        "render_readiness_status": readiness,
        "locked_fields": storyboard["locked_fields"],
        "warnings": warnings,
        "human_review_flags": ["LEGAL_REVIEW_REQUIRED"] if search_plan.get("legal_review_tasks") else [],
        "approval_status": "approved",
        "next_component": config.next_component,
    }


def _graphic(graphic_id: str, name: str, graphic_type: str, scene: dict[str, Any], config: Any) -> dict[str, Any]:
    return {
        "graphic_id": graphic_id,
        "graphic_name": name,
        "graphic_type": graphic_type,
        "scenes_used": [scene["scene_id"]],
        "purpose": f"Support {scene['scene_type']} with a clean production graphic.",
        "text_content": [scene.get("primary_text", "")],
        "data_content": {"voiceover": scene.get("voiceover_text", ""), "caption": scene.get("caption_text", "")},
        "layout_requirements": "Vertical 9:16, safe-area centered, large readable headline.",
        "animation_requirements": scene.get("motion_preset", "subtle_push"),
        "required_assets": scene.get("required_assets", []),
        "recommended_format": config.default_format,
        "recommended_dimensions": config.default_dimensions,
        "fallback_design": "Use minimal text card with internal icons and pitch texture.",
    }


def _caption_graphic(scene: dict[str, Any], config: Any) -> dict[str, Any]:
    return {
        "graphic_id": f"caption-{scene['scene_id']}",
        "graphic_name": f"Caption overlay {scene['scene_id']}",
        "graphic_type": "caption_overlay",
        "scenes_used": [scene["scene_id"]],
        "purpose": "Readable caption overlay.",
        "text_content": [scene.get("caption_text", "")],
        "data_content": {},
        "layout_requirements": "Two-line maximum lower-third caption inside safe area.",
        "animation_requirements": "fade_in_fast",
        "required_assets": [],
        "recommended_format": config.default_format,
        "recommended_dimensions": config.default_dimensions,
        "fallback_design": "Plain white text with dark translucent backing.",
    }

