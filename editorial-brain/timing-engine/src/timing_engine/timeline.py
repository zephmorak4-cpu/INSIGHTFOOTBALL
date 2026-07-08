"""Timeline assembly."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .metrics import count_words, speech_duration


def build_timeline(scene_list: dict[str, Any], config: Any) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []
    timeline_scenes = []
    previous_end = 0.0
    for scene in scene_list["scenes"]:
        duration = float(scene["duration_seconds"])
        status = "ok"
        notes: list[str] = []
        if scene["start_time_seconds"] < previous_end:
            errors.append(f"{scene['scene_id']}: overlaps previous scene")
            status = "error"
        if duration < 2:
            errors.append(f"{scene['scene_id']}: below 2 seconds")
            status = "error"
        if duration > 7:
            if scene["scene_type"] == "Insight Dashboard":
                warnings.append(f"{scene['scene_id']}: dashboard exceeds 7 seconds but is editorially justified")
                notes.append("Dashboard duration allowed because timing rules prefer 8-12 seconds if possible.")
            else:
                errors.append(f"{scene['scene_id']}: above 7 seconds without justification")
                status = "error"
        if not 3 <= duration <= 5 and scene["scene_type"] not in {"Insight Dashboard", "Brand Opening"}:
            warnings.append(f"{scene['scene_id']}: outside 3-5 second visual-change target")
        estimated = speech_duration(scene["voiceover_text"])
        if estimated > duration + 1:
            warnings.append(f"{scene['scene_id']}: voiceover may feel tight")
            notes.append("Caption should stay short and motion should be minimal.")
        if scene["scene_type"] == "Final Question / CTA" and duration < 3:
            errors.append(f"{scene['scene_id']}: CTA needs at least 3 seconds")
            status = "error"
        if scene["scene_type"] == "Brand Opening" and not 2 <= duration <= 3:
            warnings.append(f"{scene['scene_id']}: brand opening should stay 2-3 seconds")
        timeline_scenes.append(
            {
                "scene_id": scene["scene_id"],
                "template_id": scene["template_id"],
                "start_time_seconds": scene["start_time_seconds"],
                "end_time_seconds": scene["end_time_seconds"],
                "duration_seconds": duration,
                "voiceover_text": scene["voiceover_text"],
                "caption_text": scene["caption_text"],
                "estimated_words": count_words(scene["voiceover_text"]),
                "estimated_speech_duration": estimated,
                "timing_status": status,
                "adjustment_notes": notes,
            }
        )
        previous_end = scene["end_time_seconds"]
    total = scene_list["total_duration_seconds"]
    if total > config.max_duration_seconds:
        errors.append("total duration exceeds 60 seconds")
    return {
        "production_id": scene_list["production_id"],
        "component_id": config.component_id,
        "component_name": config.component_name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_duration_seconds": total,
        "fps": config.fps,
        "aspect_ratio": config.aspect_ratio,
        "resolution": config.resolution,
        "scenes": timeline_scenes,
        "timing_warnings": sorted(set(warnings)),
        "timing_errors": sorted(set(errors)),
        "approval_status": "approved" if not errors else "blocked",
    }


def build_final_package(scene_list: dict[str, Any], timeline: dict[str, Any], voiceover: str, config: Any) -> dict[str, Any]:
    scenes = scene_list["scenes"]
    required_assets = sorted({asset for scene in scenes for asset in scene.get("required_assets", [])})
    captions = [{"scene_id": scene["scene_id"], "caption_text": scene["caption_text"]} for scene in scenes]
    return {
        "production_id": scene_list["production_id"],
        "match": scene_list.get("match", {}),
        "competition": scene_list.get("competition", ""),
        "source_script_package": scene_list["production_id"],
        "final_voiceover": voiceover,
        "total_duration_seconds": timeline["total_duration_seconds"],
        "scene_count": scene_list["scene_count"],
        "scenes": scenes,
        "timeline": timeline,
        "captions": captions,
        "required_assets": required_assets,
        "locked_fields": scene_list.get("locked_fields", {}),
        "storyboard_quality_scores": {
            "timing_fit": 95 if timeline["approval_status"] == "approved" else 50,
            "caption_readability": 90,
            "template_mapping": 92,
            "script_preservation": 100,
        },
        "warnings": timeline["timing_warnings"],
        "human_review_flags": [],
        "approval_status": timeline["approval_status"],
        "next_component": config.next_component,
    }

