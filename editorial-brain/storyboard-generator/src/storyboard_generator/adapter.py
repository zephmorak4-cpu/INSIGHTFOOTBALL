"""Deterministic storyboard adapter."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any


SCENE_BLUEPRINTS = [
    ("A", "Brand Opening", "brand_opening", "logo_pulse", ["brand_logo", "background_graphic"]),
    ("B", "Surprising Fact", "stat_card", "fact_reveal", ["team_logos", "data_card"]),
    ("D", "Central Question", "question_card", "question_push", ["team_logos"]),
    ("G", "Tactical Moment", "pitch_tactics", "pitch_pan", ["pitch_graphic", "team_logos"]),
    ("F", "Team Comparison", "comparison_split", "side_by_side", ["team_logos"]),
    ("E", "Evidence Card", "evidence_card", "stat_slide", ["data_card", "team_logo_home"]),
    ("F", "Team Comparison", "comparison_split", "balance_shift", ["team_logos"]),
    ("I", "Insight Dashboard", "insight_dashboard", "dashboard_build", ["dashboard_panel", "team_logos"]),
    ("I", "Insight Dashboard", "insight_dashboard", "dashboard_hold", ["dashboard_panel", "team_logos"]),
    ("H", "X-Factor Player", "player_focus", "spotlight", ["player_image", "pitch_graphic"]),
    ("J", "Final Question / CTA", "cta_card", "final_push", ["team_logos", "comment_icon"]),
]


def build_storyboard(package: dict[str, Any], voiceover: str, config: Any) -> dict[str, Any]:
    sentences = _split_sentences(voiceover)
    durations = _durations_for(sentences)
    scenes = []
    cursor = 0.0
    for index, text in enumerate(sentences, start=1):
        blueprint = SCENE_BLUEPRINTS[min(index - 1, len(SCENE_BLUEPRINTS) - 1)]
        duration = durations[index - 1]
        start = round(cursor, 2)
        end = round(cursor + duration, 2)
        scene_type = blueprint[1]
        scenes.append(
            {
                "scene_id": f"scene-{index:02d}",
                "scene_number": index,
                "scene_type": scene_type,
                "start_time_seconds": start,
                "end_time_seconds": end,
                "duration_seconds": round(duration, 2),
                "voiceover_text": text,
                "caption_text": _caption(text),
                "on_screen_text": _screen_text(scene_type, text, package),
                "visual_goal": _visual_goal(scene_type),
                "visual_description": _visual_description(scene_type, package),
                "suggested_template": blueprint[2],
                "required_assets": blueprint[4],
                "optional_assets": ["stadium_image", "manager_image"] if index in {2, 8} else [],
                "motion_hint": blueprint[3],
                "transition_hint": "quick_cut" if index < len(sentences) else "hold_then_out",
                "notes": "Preserve script wording; visuals support the line only.",
            }
        )
        cursor += duration
    return {
        "production_id": package["production_id"],
        "agent_id": config.agent_id,
        "agent_name": config.agent_name,
        "prompt_id": config.prompt_id,
        "prompt_version": config.prompt_version,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source_script_package_id": package["production_id"],
        "match": package["match"],
        "competition": package["competition"],
        "total_estimated_duration_seconds": round(cursor, 2),
        "scene_count": len(scenes),
        "scenes": scenes,
        "locked_fields": package["locked_fields"],
        "warnings": [],
        "human_review_flags": [],
        "approval_status": "approved",
        "next_component": config.next_component,
    }


def _split_sentences(text: str) -> list[str]:
    protected = text.strip().replace("...", "<ellipsis>")
    parts = [part.strip().replace("<ellipsis>", "...") for part in re.split(r"(?<=[.!?])\s+", protected) if part.strip()]
    if len(parts) >= 2 and parts[-1].lower() == "tell us below.":
        parts[-2] = f"{parts[-2]} {parts[-1]}"
        parts.pop()
    return parts


def _durations_for(sentences: list[str]) -> list[float]:
    raw = [max(2.0, len(sentence.split()) / 2.6) for sentence in sentences]
    total = sum(raw)
    scale = min(56.0 / total, 1.0)
    return [round(min(7.0, max(2.0, value * scale)), 2) for value in raw]


def _caption(text: str) -> str:
    words = text.split()
    return " ".join(words[:12]).rstrip(".,") + ("..." if len(words) > 12 else "")


def _screen_text(scene_type: str, text: str, package: dict[str, Any]) -> str:
    if scene_type == "Brand Opening":
        return "Before the first whistle"
    if scene_type == "Central Question":
        return package["central_question"]
    if scene_type == "Final Question / CTA":
        return "Tell us below"
    if scene_type == "Insight Dashboard":
        return "Slight Home Edge"
    return _caption(text)


def _visual_goal(scene_type: str) -> str:
    return f"Make the {scene_type.lower()} easy to understand in one glance."


def _visual_description(scene_type: str, package: dict[str, Any]) -> str:
    home = package["match"].get("home_team", "Home")
    away = package["match"].get("away_team", "Away")
    return f"Vertical 9:16 {scene_type.lower()} using {home} and {away} context, clean captions, and restrained motion."
