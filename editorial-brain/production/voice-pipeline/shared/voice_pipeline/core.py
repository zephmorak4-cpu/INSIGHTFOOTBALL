from __future__ import annotations

from pathlib import Path
from typing import Any


SUPPORTED_FORMATS = {"wav", "mp3", "m4a"}


def validate_voice_input(audio_path: str | Path, *, mode: str = "human_recorded") -> dict[str, Any]:
    path = Path(audio_path)
    suffix = path.suffix.lower().lstrip(".")
    issues = []
    if mode not in {"human_recorded", "voice_clone", "fallback_ai_voice"}:
        issues.append("unsupported narration mode")
    if suffix not in SUPPORTED_FORMATS:
        issues.append("unsupported audio format")
    if mode == "human_recorded" and not path.exists():
        issues.append("human recorded narration file missing")
    return {
        "module": "voice-input",
        "audio_path": str(path),
        "mode": mode,
        "format": suffix,
        "supported_formats": sorted(SUPPORTED_FORMATS),
        "issues": issues,
        "approval_status": "approved" if not issues else "blocked",
    }


def process_voice(input_report: dict[str, Any]) -> dict[str, Any]:
    return {
        "module": "voice-processing",
        "source": input_report["audio_path"],
        "steps": ["decode_audio", "preserve_breaths", "prepare_for_cleaning"],
        "approval_status": input_report["approval_status"],
    }


def clean_voice(processing_report: dict[str, Any]) -> dict[str, Any]:
    return {
        "module": "voice-cleaning",
        "source": processing_report["source"],
        "noise_reduction": "planned",
        "volume_normalization": "planned",
        "silence_trimming": "planned",
        "breath_preservation": True,
        "approval_status": processing_report["approval_status"],
    }


def align_speech_to_scenes(cleaning_report: dict[str, Any], storyboard: dict[str, Any]) -> dict[str, Any]:
    scenes = storyboard.get("scenes", [])
    entries = []
    cursor = 0.0
    for scene in scenes:
        words = len(str(scene.get("voiceover_text", "")).split())
        duration = max(1.2, round(words / 2.6, 2))
        entries.append({"scene_id": scene["scene_id"], "start_time_seconds": round(cursor, 2), "end_time_seconds": round(cursor + duration, 2), "word_alignment": "estimated"})
        cursor += duration
    return {
        "module": "speech-alignment",
        "source": cleaning_report["source"],
        "entries": entries,
        "total_duration_seconds": round(cursor, 2),
        "approval_status": cleaning_report["approval_status"] if entries else "blocked",
    }


def sync_voice_to_timeline(alignment: dict[str, Any], timeline: dict[str, Any]) -> dict[str, Any]:
    aligned_by_scene = {entry["scene_id"]: entry for entry in alignment.get("entries", [])}
    scene_timing = []
    for scene in timeline.get("scenes", []):
        aligned = aligned_by_scene.get(scene["scene_id"], {})
        scene_timing.append({
            "scene_id": scene["scene_id"],
            "timeline_start": scene.get("start_time_seconds"),
            "timeline_end": scene.get("end_time_seconds"),
            "voice_start": aligned.get("start_time_seconds"),
            "voice_end": aligned.get("end_time_seconds"),
            "timing_adjustment": "stretch_or_compress_scene_to_voice",
        })
    return {
        "module": "voice-sync",
        "scene_timing": scene_timing,
        "timeline_auto_adjust": True,
        "captions_from_narration": True,
        "approval_status": alignment.get("approval_status", "blocked"),
    }
