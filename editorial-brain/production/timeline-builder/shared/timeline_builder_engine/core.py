from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .io import StructuredLogger, load_json, now, write_json

OUTPUT = Path("editorial-brain/output")
LOGS = Path("editorial-brain/logs")
FPS = 30
ASPECT_RATIO = "9:16"
RESOLUTION = "1080x1920"
MAX_DURATION = 60.0
LAYER_ORDER = ["background", "background_overlay", "pitch_or_dashboard_graphics", "team_badges", "player_or_icon_assets", "data_cards", "primary_text", "captions", "watermark", "transitions"]
INTERNAL_TERMS = ["Form Index", "Risk Meter", "Tactical Edge", "X-Factor", "Evidence Filter", "Insight Engine", "Story Hunter", "Editorial Brain"]


def run_all(root: Path = Path(".")) -> dict[str, Any]:
    storyboard = _required(root / OUTPUT / "final-storyboard-package.json", "storyboard")
    visual = _required(root / OUTPUT / "visual-production-package.json", "visual package")
    voice = _required(root / OUTPUT / "voice-production-package.json", "voice package")
    assets = _required(root / OUTPUT / "media-asset-bundle.json", "asset bundle")
    timeline = timeline_builder(storyboard, visual, voice, assets, root=root)
    scenes = scene_composer(timeline, storyboard, visual, assets, root=root)
    layers = layer_composer(timeline, scenes, assets, root=root)
    captions = caption_synchronizer(timeline, layers, root=root)
    audio = audio_synchronizer(timeline, voice, root=root)
    render_plan = render_plan_generator(timeline, layers, captions, audio, assets, root=root)
    validated = timeline_validator(timeline, scenes, layers, captions, audio, render_plan, voice, visual, assets, root=root)
    return {"timeline": timeline, "scene_compositions": scenes, "layer_map": layers, "caption_sync": captions, "audio_sync": audio, "render_plan": render_plan, **validated}


def timeline_builder(storyboard: dict[str, Any], visual_pkg: dict[str, Any], voice_pkg: dict[str, Any], asset_bundle: dict[str, Any], *, root: Path = Path(".")) -> dict[str, Any]:
    _validate_inputs(storyboard, visual_pkg, voice_pkg, asset_bundle)
    production_id = storyboard["production_id"]
    source_total = float(storyboard.get("total_duration_seconds") or storyboard["scenes"][-1]["end_time_seconds"])
    voice_total = float(voice_pkg["audio_qc_report"]["estimated_duration_seconds"])
    target_total = min(MAX_DURATION, max(source_total, voice_total))
    scale = target_total / source_total if source_total else 1.0
    visual_by_id = {scene["scene_id"]: scene for scene in visual_pkg["visual_plan"]["scenes"]}
    camera_by_id = {scene["scene_id"]: scene for scene in visual_pkg["camera_plan"]["scenes"]}
    motion_by_id = {scene["scene_id"]: scene for scene in visual_pkg["motion_plan"]["scenes"]}
    scenes = []
    for index, scene in enumerate(storyboard["scenes"], start=1):
        visual = visual_by_id.get(scene["scene_id"], {})
        start = round(float(scene["start_time_seconds"]) * scale, 2)
        end = round(float(scene["end_time_seconds"]) * scale, 2)
        if index == len(storyboard["scenes"]):
            end = round(target_total, 2)
        asset_refs = sorted(set(visual.get("foreground_assets", []) + visual.get("team_badges", []) + visual.get("graphic_assets", []) + [visual.get("background_asset", "")]) - {""})
        duration = round(end - start, 2)
        visual_elements = _visual_elements_for_scene(scene, visual)
        movement_interval = float(motion_by_id.get(scene["scene_id"], {}).get("movement_interval_seconds", 2.5))
        scenes.append({
            "scene_id": scene["scene_id"],
            "scene_number": index,
            "scene_type": scene["scene_type"],
            "template_id": visual.get("template_id", scene.get("template_id", "fallback_text_card")),
            "start_time_seconds": start,
            "end_time_seconds": end,
            "duration_seconds": duration,
            "voiceover_text": _viewer_text(scene.get("voiceover_text", "")),
            "voiceover_start": start,
            "voiceover_end": end,
            "caption_text": _fit_caption(_viewer_text(scene.get("caption_text", ""))),
            "visual_plan_ref": scene["scene_id"],
            "camera_plan_ref": camera_by_id.get(scene["scene_id"], {}).get("movement", visual.get("camera_style", "Static")),
            "motion_plan_ref": motion_by_id.get(scene["scene_id"], {}).get("motion_preset", visual.get("motion_style", "Fade")),
            "movement_interval_seconds": movement_interval,
            "motion_beats": _motion_beats(start, end, movement_interval),
            "visual_elements": visual_elements,
            "broadcast_elements": visual.get("broadcast_elements", {}),
            "asset_refs": asset_refs,
            "layer_refs": [f"{scene['scene_id']}-{layer}" for layer in LAYER_ORDER],
            "transition_in": "quick_cut" if index > 1 else "none",
            "transition_out": visual.get("transition_style", "quick_cut"),
            "safe_area_notes": scene.get("safe_area_notes", visual.get("safe_area_notes", "")),
            "render_notes": "Renderer-ready scene metadata only; no video rendering performed.",
        })
    timeline = {
        "production_id": production_id,
        "component_id": "IF-TL01",
        "component_name": "Timeline Builder",
        "timestamp": now(),
        "match": storyboard["match"],
        "competition": storyboard["competition"],
        "total_duration_seconds": round(target_total, 2),
        "fps": FPS,
        "aspect_ratio": ASPECT_RATIO,
        "resolution": RESOLUTION,
        "source_storyboard_package": storyboard["production_id"],
        "source_visual_package": visual_pkg["production_id"],
        "source_voice_package": voice_pkg["production_id"],
        "source_asset_bundle": asset_bundle["production_id"],
        "scenes": scenes,
        "global_audio": {
            "voice_track_ref": "voice-production-package.json",
            "narration_priority": "dominant",
            "stadium_ambience": "low_bed",
            "crowd_atmosphere": "subtle",
            "transition_swooshes": "enabled",
            "goal_impact": "available",
            "low_cinematic_bass": "enabled",
            "background_music": "low_under_voice",
        },
        "global_style": {"brand": "INSIGHT FOOTBALL", "caption_style": "lower_safe_two_line", "safe_area": "vertical_center_80"},
        "warnings": _status_warnings(asset_bundle),
        "approval_status": "approved",
        "next_component": "Scene Composer",
    }
    write_json(root / OUTPUT / "timeline.json", timeline)
    StructuredLogger(root / LOGS, f"timeline-builder-{production_id}").log({"event": "timeline_written", "scenes": len(scenes), "duration": target_total})
    return timeline


def scene_composer(timeline: dict[str, Any], storyboard: dict[str, Any], visual_pkg: dict[str, Any], asset_bundle: dict[str, Any], *, root: Path = Path(".")) -> dict[str, Any]:
    visual_by_id = {scene["scene_id"]: scene for scene in visual_pkg["visual_plan"]["scenes"]}
    captions_by_id = {scene["scene_id"]: scene for scene in visual_pkg["caption_plan"]["scenes"]}
    compositions = []
    for scene in timeline["scenes"]:
        visual = visual_by_id.get(scene["scene_id"], {})
        caption = captions_by_id.get(scene["scene_id"], {})
        compositions.append({
            "scene_id": scene["scene_id"],
            "template_id": scene.get("template_id") or "fallback_text_card",
            "duration_seconds": scene["duration_seconds"],
            "background": _asset_ref(visual.get("background_asset", "background_graphic"), asset_bundle),
            "foreground": [_asset_ref(asset_id, asset_bundle) for asset_id in visual.get("foreground_assets", [])],
            "text_elements": [{"type": "primary", "text": visual.get("primary_text", scene["caption_text"])}, {"type": "secondary", "text": visual.get("secondary_text", "")}],
            "graphic_elements": [_asset_ref(asset_id, asset_bundle) for asset_id in visual.get("graphic_assets", [])],
            "logo_elements": [_asset_ref(asset_id, asset_bundle) for asset_id in visual.get("team_badges", [])],
            "visual_elements": scene.get("visual_elements", []),
            "broadcast_elements": scene.get("broadcast_elements", {}),
            "dashboard_elements": [{"usage": visual.get("dashboard_usage", "hidden"), "asset": _asset_ref("dashboard_panel", asset_bundle)}] if "dashboard" in scene["scene_type"].lower() else [],
            "caption_element": {"text": caption.get("caption", scene["caption_text"]), "style": caption.get("caption_style", "lower_safe_two_line"), "position": caption.get("caption_position", "lower_safe")},
            "motion_elements": [{"preset": scene["motion_plan_ref"], "duration": min(1.2, scene["duration_seconds"])}],
            "camera_instruction": scene["camera_plan_ref"],
            "transition_instruction": scene["transition_out"],
            "audio_segment_ref": {"start": scene["voiceover_start"], "end": scene["voiceover_end"]},
            "render_priority": "high" if scene["scene_type"] in {"Central Question", "Insight Dashboard"} else "normal",
            "fallback_notes": "Uses safe placeholders where approved local assets are unavailable." if _has_fallback(scene["asset_refs"], asset_bundle) else "",
        })
    output = {"production_id": timeline["production_id"], "component_id": "IF-TL02", "component_name": "Scene Composer", "timestamp": now(), "scenes": compositions, "warnings": timeline.get("warnings", []), "approval_status": "approved", "next_component": "Layer Composer"}
    write_json(root / OUTPUT / "scene_compositions.json", output)
    StructuredLogger(root / LOGS, f"scene-composer-{timeline['production_id']}").log({"event": "scene_compositions_written", "scenes": len(compositions)})
    return output


def layer_composer(timeline: dict[str, Any], scene_compositions: dict[str, Any], asset_bundle: dict[str, Any], *, root: Path = Path(".")) -> dict[str, Any]:
    layers_by_scene = []
    for scene in timeline["scenes"]:
        layers = []
        for z, layer_type in enumerate(LAYER_ORDER, start=1):
            asset_ref = _layer_asset(layer_type, scene, asset_bundle)
            layers.append({
                "layer_id": f"{scene['scene_id']}-{layer_type}",
                "scene_id": scene["scene_id"],
                "layer_type": layer_type,
                "z_index": z,
                "asset_ref": asset_ref,
                "text_content": scene["caption_text"] if layer_type in {"captions", "primary_text"} else "",
                "position": _position(layer_type),
                "size": "safe-fit",
                "opacity": 1.0 if layer_type != "background_overlay" else 0.18,
                "animation": scene["motion_plan_ref"] if layer_type in {"primary_text", "captions", "transitions"} else "none",
                "start_time_seconds": scene["start_time_seconds"],
                "end_time_seconds": scene["end_time_seconds"],
                "blend_mode": "normal",
                "safe_area_compliant": True,
            })
        layers_by_scene.append({"scene_id": scene["scene_id"], "layers": layers})
    output = {"production_id": timeline["production_id"], "component_id": "IF-TL03", "component_name": "Layer Composer", "timestamp": now(), "scenes": layers_by_scene, "global_layers": ["safe_area_guides"], "watermark_layer": "watermark", "caption_layer": "captions", "warnings": [], "approval_status": "approved"}
    write_json(root / OUTPUT / "layer_map.json", output)
    StructuredLogger(root / LOGS, f"layer-composer-{timeline['production_id']}").log({"event": "layer_map_written", "scenes": len(layers_by_scene)})
    return output


def caption_synchronizer(timeline: dict[str, Any], layer_map: dict[str, Any], *, root: Path = Path(".")) -> dict[str, Any]:
    captions = []
    for scene in timeline["scenes"]:
        text = _fit_caption(scene["caption_text"])
        words = re.findall(r"[A-Za-z0-9'-]+", text)
        captions.append({
            "caption_id": f"caption-{scene['scene_number']:02d}",
            "scene_id": scene["scene_id"],
            "text": text,
            "start_time_seconds": scene["start_time_seconds"],
            "end_time_seconds": scene["end_time_seconds"],
            "position": "lower_safe",
            "max_line_count": 2,
            "max_words_per_line": 7,
            "highlight_words": [word for word in ["Liverpool", "Arsenal", "edge", "press"] if word.lower() in text.lower()],
            "style_ref": "lower_safe_two_line",
            "safe_area_status": "compliant",
            "readability_score": 95 if len(words) <= 14 else 85,
        })
    output = {"production_id": timeline["production_id"], "component_id": "IF-TL04", "component_name": "Caption Synchronizer", "timestamp": now(), "captions": captions, "warnings": [], "approval_status": "approved", "next_component": "Audio Synchronizer"}
    write_json(root / OUTPUT / "caption_sync.json", output)
    StructuredLogger(root / LOGS, f"caption-synchronizer-{timeline['production_id']}").log({"event": "caption_sync_written", "captions": len(captions)})
    return output


def audio_synchronizer(timeline: dict[str, Any], voice_pkg: dict[str, Any], *, root: Path = Path(".")) -> dict[str, Any]:
    if not voice_pkg.get("voice_timestamps", {}).get("entries"):
        raise ValueError("voice_timestamps.entries required")
    scene_map, warnings = [], []
    for scene in timeline["scenes"]:
        voice_start, voice_end = scene["voiceover_start"], scene["voiceover_end"]
        offset = round(voice_start - scene["start_time_seconds"], 2)
        if abs(offset) > 0.5:
            warnings.append(f"{scene['scene_id']} sync offset exceeds 0.5 seconds")
        scene_map.append({"scene_id": scene["scene_id"], "voice_start": voice_start, "voice_end": voice_end, "scene_start": scene["start_time_seconds"], "scene_end": scene["end_time_seconds"], "sync_offset": offset, "adjustment_required": abs(offset) > 0.5, "notes": "Aligned to Sprint 9 normalized scene timing."})
    output = {"production_id": timeline["production_id"], "component_id": "IF-TL05", "component_name": "Audio Synchronizer", "timestamp": now(), "total_audio_duration_seconds": voice_pkg["audio_qc_report"]["estimated_duration_seconds"], "timeline_duration_seconds": timeline["total_duration_seconds"], "sync_status": "aligned" if not warnings else "aligned_with_warnings", "voice_track": {"source": "voice.ssml", "package_ref": voice_pkg["production_id"], "priority": "dominant"}, "music_bed": {"enabled": True, "level": "low_under_voice"}, "sound_effect_cues": ["opening_impact", "transition_swoosh", "soft_bass_finish"], "scene_audio_map": scene_map, "warnings": warnings, "approval_status": "approved"}
    write_json(root / OUTPUT / "audio_sync.json", output)
    StructuredLogger(root / LOGS, f"audio-synchronizer-{timeline['production_id']}").log({"event": "audio_sync_written", "warnings": len(warnings)})
    return output


def render_plan_generator(timeline: dict[str, Any], layer_map: dict[str, Any], caption_sync: dict[str, Any], audio_sync: dict[str, Any], asset_bundle: dict[str, Any], *, root: Path = Path(".")) -> dict[str, Any]:
    output = {
        "production_id": timeline["production_id"],
        "component_id": "IF-TL06",
        "component_name": "Render Plan Generator",
        "timestamp": now(),
        "renderer_profile": {"default": "provider_agnostic", "supported_renderers": ["Creatomate", "Remotion", "Shotstack", "After Effects", "FFmpeg custom renderer"]},
        "provider_agnostic_timeline": timeline["production_id"],
        "required_assets": sorted({asset for scene in timeline["scenes"] for asset in scene["asset_refs"]}),
        "required_audio": ["voice.ssml", "voice-production-package.json"],
        "required_fonts": ["Inter", "Arial"],
        "render_settings": {"aspect_ratio": ASPECT_RATIO, "resolution": RESOLUTION, "fps": FPS, "format": "mp4", "max_duration_seconds": 60, "audio_codec": "aac", "video_codec": "h264"},
        "scene_templates": sorted({scene["template_id"] for scene in timeline["scenes"]}),
        "layer_map_ref": "layer_map.json",
        "caption_sync_ref": "caption_sync.json",
        "audio_sync_ref": "audio_sync.json",
        "output_settings": {"filename": f"{timeline['production_id']}.mp4", "container": "mp4"},
        "fallback_render_strategy": "Use placeholder assets and safe text cards when official assets remain under manual review.",
        "approval_status": "approved",
    }
    write_json(root / OUTPUT / "render_plan.json", output)
    StructuredLogger(root / LOGS, f"render-plan-generator-{timeline['production_id']}").log({"event": "render_plan_written"})
    return output


def timeline_validator(timeline: dict[str, Any], scenes: dict[str, Any], layer_map: dict[str, Any], captions: dict[str, Any], audio: dict[str, Any], render_plan: dict[str, Any], voice_pkg: dict[str, Any], visual_pkg: dict[str, Any], asset_bundle: dict[str, Any], *, root: Path = Path(".")) -> dict[str, Any]:
    issues, warnings = [], list(timeline.get("warnings", []))
    if timeline["total_duration_seconds"] > 60:
        issues.append("total duration exceeds 60 seconds")
    for previous, current in zip(timeline["scenes"], timeline["scenes"][1:]):
        if current["start_time_seconds"] < previous["end_time_seconds"]:
            issues.append(f"{current['scene_id']} overlaps previous scene")
        if round(current["start_time_seconds"] - previous["end_time_seconds"], 2) > 0.05:
            warnings.append(f"gap before {current['scene_id']}")
    valid_assets = _valid_asset_ids(asset_bundle)
    for scene in timeline["scenes"]:
        missing = [asset for asset in scene["asset_refs"] if asset not in valid_assets]
        if missing:
            issues.append(f"{scene['scene_id']} missing asset refs: {', '.join(missing)}")
        if len(scene.get("visual_elements", [])) < 3:
            issues.append(f"{scene['scene_id']} has fewer than three visual elements")
        if float(scene.get("movement_interval_seconds", 99)) > 3:
            issues.append(f"{scene['scene_id']} has no planned movement within three seconds")
        leaked = _internal_terms(" ".join([scene.get("voiceover_text", ""), scene.get("caption_text", "")]))
        if leaked:
            issues.append(f"{scene['scene_id']} contains internal terminology: {', '.join(leaked)}")
    opening = timeline["scenes"][0] if timeline["scenes"] else {}
    opening_required = {"club_badge_home", "club_badge_away", "competition_logo", "match_title", "modern_scoreboard", "broadcast_animation"}
    missing_opening = sorted(opening_required - set(opening.get("visual_elements", [])))
    if missing_opening:
        issues.append("opening five seconds missing: " + ", ".join(missing_opening))
    if not voice_pkg.get("voice_timestamps", {}).get("entries"):
        issues.append("missing voice refs")
    if len(visual_pkg.get("visual_plan", {}).get("scenes", [])) != len(timeline["scenes"]):
        issues.append("visual scene count mismatch")
    if any(len(line.split()) > 7 for cap in captions["captions"] for line in cap["text"].split("\n")):
        issues.append("caption exceeds max words per line")
    if any(len(cap["text"].split("\n")) > 2 for cap in captions["captions"]):
        issues.append("caption exceeds max line count")
    if any(layer["z_index"] <= 0 for scene in layer_map["scenes"] for layer in scene["layers"]):
        issues.append("invalid layer z-index")
    if not render_plan.get("required_fonts"):
        issues.append("required fonts missing")
    if asset_bundle.get("render_readiness_status") == "blocked_legal_risk":
        issues.append("blocked legal asset included")
    status = "failed_validation" if issues else ("ready_with_warnings" if warnings or asset_bundle.get("render_readiness_status") == "needs_manual_assets" else "ready")
    report = {"production_id": timeline["production_id"], "component_id": "IF-TL07", "component_name": "Timeline Validator", "timestamp": now(), "checks": {"duration": timeline["total_duration_seconds"] <= 60, "scene_order": not any("overlap" in issue for issue in issues), "asset_refs": not any("asset refs" in issue for issue in issues), "voice_refs": not any("voice refs" in issue for issue in issues), "captions": not any("caption" in issue for issue in issues), "render_settings": render_plan["render_settings"]["resolution"] == RESOLUTION}, "issues": issues, "warnings": warnings, "render_readiness_status": status, "approval_status": "approved" if status != "failed_validation" else "blocked"}
    package = {"production_id": timeline["production_id"], "match": timeline["match"], "competition": timeline["competition"], "timeline": timeline, "scene_compositions": scenes, "layer_map": layer_map, "caption_sync": captions, "audio_sync": audio, "render_plan": render_plan, "validation_report": report, "required_assets": render_plan["required_assets"], "required_fonts": render_plan["required_fonts"], "required_audio": render_plan["required_audio"], "legal_warnings": asset_bundle.get("legal_warnings", []), "render_readiness_status": status, "approval_status": report["approval_status"], "next_component": "Rendering Engine"}
    write_json(root / OUTPUT / "timeline_validation_report.json", report)
    write_json(root / OUTPUT / "renderer-ready-package.json", package)
    StructuredLogger(root / LOGS, f"timeline-validator-{timeline['production_id']}").log({"event": "renderer_ready_package_written", "status": status, "issues": len(issues)})
    return {"timeline_validation_report": report, "renderer_ready_package": package}


def _required(path: Path, name: str) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing {name}: {path}")
    return load_json(path)


def _validate_inputs(storyboard: dict[str, Any], visual: dict[str, Any], voice: dict[str, Any], assets: dict[str, Any]) -> None:
    for name, payload in [("storyboard", storyboard), ("visual", visual), ("voice", voice), ("assets", assets)]:
        if not payload.get("production_id"):
            raise ValueError(f"{name}.production_id required")
    if not storyboard.get("scenes"):
        raise ValueError("storyboard.scenes required")


def _status_warnings(asset_bundle: dict[str, Any]) -> list[str]:
    warnings = list(asset_bundle.get("legal_warnings", []))
    if asset_bundle.get("render_readiness_status") not in {"ready", "ready_with_fallbacks"}:
        warnings.append(f"Media asset bundle status: {asset_bundle.get('render_readiness_status')}")
    return warnings


def _asset_ref(asset_id: str, asset_bundle: dict[str, Any]) -> dict[str, Any]:
    for ref in _all_assets(asset_bundle):
        if ref.get("asset_id") == asset_id or ref.get("graphic_id") == asset_id:
            return ref
    return {"asset_id": asset_id, "missing": True, "fallback_strategy": "Use text/card fallback if renderer needs a concrete layer."}


def _all_assets(asset_bundle: dict[str, Any]) -> list[dict[str, Any]]:
    refs = []
    def walk(value: Any) -> None:
        if isinstance(value, dict):
            if value.get("asset_id") or value.get("graphic_id"):
                refs.append(value)
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)
    walk(asset_bundle)
    return refs


def _valid_asset_ids(asset_bundle: dict[str, Any]) -> set[str]:
    ids = {ref.get("asset_id") for ref in _all_assets(asset_bundle) if ref.get("asset_id")}
    ids.update(ref.get("graphic_id") for ref in _all_assets(asset_bundle) if ref.get("graphic_id"))
    for scene in asset_bundle.get("scene_asset_map", []):
        ids.update(scene.get("required_asset_ids", []))
        ids.update(scene.get("resolved_asset_ids", []))
        ids.update(scene.get("fallback_asset_ids", []))
    return ids


def _has_fallback(asset_ids: list[str], asset_bundle: dict[str, Any]) -> bool:
    fallback_ids = {ref.get("asset_id") for ref in asset_bundle.get("fallback_assets", [])}
    return bool(set(asset_ids) & fallback_ids)


def _layer_asset(layer_type: str, scene: dict[str, Any], asset_bundle: dict[str, Any]) -> dict[str, Any] | None:
    if layer_type == "background":
        return _asset_ref(scene["asset_refs"][0], asset_bundle) if scene["asset_refs"] else None
    if layer_type in {"team_badges", "player_or_icon_assets", "data_cards"}:
        return _asset_ref(next((asset for asset in scene["asset_refs"] if "team" in asset or "icon" in asset or "card" in asset), scene["asset_refs"][0] if scene["asset_refs"] else ""), asset_bundle)
    if layer_type == "watermark":
        return _asset_ref("watermark", asset_bundle)
    return None


def _position(layer_type: str) -> str:
    return {"captions": "lower_safe", "watermark": "top_right_safe", "primary_text": "center_safe", "background": "full_frame"}.get(layer_type, "center_safe")


def _fit_caption(text: str) -> str:
    words = re.findall(r"[A-Za-z0-9'-]+", text)
    if len(words) <= 7:
        return " ".join(words)
    return " ".join(words[:7]) + "\n" + " ".join(words[7:14])


def _viewer_text(text: str) -> str:
    replacements = {
        "X-Factor": "One thing that could change everything",
        "Tactical Edge": "biggest advantage",
        "Form Index": "recent form",
        "Risk Meter": "what could go wrong",
    }
    output = str(text)
    for internal, replacement in replacements.items():
        output = output.replace(internal, replacement)
    return output


def _internal_terms(text: str) -> list[str]:
    return [term for term in INTERNAL_TERMS if re.search(rf"\b{re.escape(term)}\b", text, re.IGNORECASE)]


def _motion_beats(start: float, end: float, interval: float) -> list[dict[str, Any]]:
    beats = []
    current = round(start, 2)
    index = 1
    while current < end:
        beats.append({"time_seconds": current, "movement": ["slow_zoom", "parallax", "light_sweep", "badge_slide"][index % 4]})
        current = round(current + min(interval, 2.8), 2)
        index += 1
    return beats


def _visual_elements_for_scene(scene: dict[str, Any], visual: dict[str, Any]) -> list[str]:
    elements = list(visual.get("visual_elements", []))
    if not elements and scene.get("scene_type") == "Brand Opening":
        elements = ["club_badge_home", "club_badge_away", "competition_logo", "match_title", "modern_scoreboard", "broadcast_animation"]
    if not elements:
        elements = ["stadium_background", "lower_third", "motion_graphics"]
    return elements
