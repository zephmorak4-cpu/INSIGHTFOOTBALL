"""Scene planning adapter."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def plan_scenes(storyboard: dict[str, Any], script_package: dict[str, Any], config: Any) -> dict[str, Any]:
    issues_found: list[str] = []
    fixes_applied: list[str] = []
    planned = []
    for scene in storyboard["scenes"]:
        words = scene["voiceover_text"].split()
        if len(words) > config.max_text_per_scene:
            issues_found.append(f"{scene['scene_id']}: overloaded voiceover")
            fixes_applied.append(f"{scene['scene_id']}: shortened caption and primary text")
        template_id = scene["suggested_template"]
        planned.append(
            {
                "scene_id": scene["scene_id"],
                "template_id": template_id,
                "scene_type": scene["scene_type"],
                "start_time_seconds": scene["start_time_seconds"],
                "end_time_seconds": scene["end_time_seconds"],
                "duration_seconds": scene["duration_seconds"],
                "voiceover_text": scene["voiceover_text"],
                "caption_text": _shorten(scene["caption_text"], 14),
                "primary_text": _shorten(scene["on_screen_text"], 9),
                "secondary_text": _secondary_text(scene),
                "visual_priority": _priority(scene["scene_type"]),
                "required_assets": scene["required_assets"],
                "motion_preset": scene["motion_hint"],
                "transition_preset": scene["transition_hint"],
                "safe_area_notes": "Keep primary text within center 80% vertical safe area.",
            }
        )
    return {
        "production_id": storyboard["production_id"],
        "component_id": config.component_id,
        "component_name": config.component_name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source_storyboard_id": storyboard["production_id"],
        "match": storyboard.get("match", {}),
        "competition": storyboard.get("competition", ""),
        "total_duration_seconds": storyboard["total_estimated_duration_seconds"],
        "scene_count": len(planned),
        "scenes": planned,
        "scene_quality_score": 92 if not issues_found else 84,
        "issues_found": issues_found,
        "fixes_applied": fixes_applied,
        "locked_fields": storyboard.get("locked_fields", {}),
        "locked_fields_preserved": storyboard.get("locked_fields") == script_package.get("locked_fields"),
        "approval_status": "approved",
        "next_component": config.next_component,
    }


def _shorten(text: str, max_words: int) -> str:
    words = str(text).split()
    return " ".join(words[:max_words]) + ("..." if len(words) > max_words else "")


def _secondary_text(scene: dict[str, Any]) -> str:
    if scene["scene_type"] == "Insight Dashboard":
        return "Edge, uncertainty, x-factor"
    if scene["scene_type"] == "Final Question / CTA":
        return "Comments open"
    return scene["visual_goal"]


def _priority(scene_type: str) -> str:
    if scene_type in {"Insight Dashboard", "Final Question / CTA", "Central Question"}:
        return "high"
    return "medium"
