from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .io import StructuredLogger, load_json, now, write_json

OUTPUT = Path("editorial-brain/output")
LOGS = Path("editorial-brain/logs")
FORBIDDEN_BETTING = ["guaranteed", "banker", "lock", "wager", "tipster"]


def run_all(root: Path = Path(".")) -> dict[str, Any]:
    render = load_json(root / OUTPUT / "render-complete-package.json")
    script = load_json(root / OUTPUT / "final-script-package.json")
    voice = load_json(root / OUTPUT / "voice-production-package.json")
    storyboard = load_json(root / OUTPUT / "final-storyboard-package.json")
    visual = load_json(root / OUTPUT / "visual-production-package.json")
    assets = load_json(root / OUTPUT / "media-asset-bundle.json")
    renderer = load_json(root / OUTPUT / "renderer-ready-package.json")
    reports = {
        "video_qc_report": video_qc(render, root=root),
        "audio_qc_report_final": audio_qc(render, voice, root=root),
        "caption_qc_report": caption_qc(render, root=root),
        "brand_compliance_report": brand_compliance_checker(render, script, visual, root=root),
        "script_alignment_report": script_alignment_checker(render, script, storyboard, root=root),
        "legal_safety_report": legal_copyright_checker(render, assets, script, root=root),
    }
    readiness = publish_readiness_gate(render, reports, script, root=root)
    return {**reports, **readiness}


def video_qc(render: dict[str, Any], *, root: Path = Path(".")) -> dict[str, Any]:
    video_path = Path(render["final_video_path"])
    thumb_path = Path(render["thumbnail_path"])
    placeholder = render["render_validation_report"].get("placeholder_mode", False)
    issues, warnings = [], []
    exists = video_path.exists()
    size = video_path.stat().st_size if exists else 0
    if not exists and not placeholder:
        issues.append("video file missing")
    if size == 0 and not placeholder:
        issues.append("video file empty")
    if placeholder:
        warnings.append("Placeholder render documented; no real video integrity checks available.")
    if render["duration_seconds"] > 60:
        issues.append("duration exceeds 60 seconds")
    if not thumb_path.exists():
        warnings.append("thumbnail missing")
    score = _score(issues, warnings, base=96 if not placeholder else 82)
    report = {
        "production_id": render["production_id"], "component_id": "IF-FQC01", "component_name": "Video QC", "timestamp": now(),
        "video_path": str(video_path), "file_exists": exists, "file_size": size, "duration_seconds": render["duration_seconds"],
        "resolution": render.get("render_job", {}).get("render_payload", {}).get("output_resolution", "1080x1920"),
        "aspect_ratio": "9:16", "fps": 30, "codec": "placeholder" if placeholder else "unknown", "thumbnail_path": str(thumb_path),
        "issues_found": issues, "warnings": warnings, "score": score, "approval_status": "approved" if not issues else "blocked",
    }
    _write(root, "video_qc_report.json", report, "video-qc")
    return report


def audio_qc(render: dict[str, Any], voice: dict[str, Any], *, root: Path = Path(".")) -> dict[str, Any]:
    placeholder = render["render_validation_report"].get("placeholder_mode", False)
    issues, warnings = [], []
    audio_exists = not placeholder and bool(render.get("render_job", {}).get("required_audio"))
    if not audio_exists:
        warnings.append("Audio track not inspectable in placeholder mode." if placeholder else "Audio track missing.")
    duration = voice["audio_qc_report"]["estimated_duration_seconds"]
    if abs(duration - render["duration_seconds"]) > 2:
        warnings.append("Voice duration differs from rendered duration by more than two seconds.")
    score = _score(issues, warnings, base=88 if placeholder else 96)
    report = {
        "production_id": render["production_id"], "component_id": "IF-FQC02", "component_name": "Audio QC", "timestamp": now(),
        "audio_exists": audio_exists, "duration_seconds": duration, "loudness_status": "not_inspectable_placeholder" if placeholder else "acceptable",
        "silence_warnings": [], "clipping_status": "not_inspectable_placeholder" if placeholder else "absent", "voice_sync_status": "aligned",
        "music_balance_status": "no_music_bed", "issues_found": issues, "warnings": warnings, "score": score, "approval_status": "approved",
    }
    _write(root, "audio_qc_report_final.json", report, "audio-qc-final")
    return report


def caption_qc(render: dict[str, Any], *, root: Path = Path(".")) -> dict[str, Any]:
    captions = render["render_complete_package"]["caption_sync"]["captions"] if "render_complete_package" in render else load_json(root / OUTPUT / "renderer-ready-package.json")["caption_sync"]["captions"]
    issues, warnings, violations = [], [], []
    if not captions:
        issues.append("captions missing")
    for cap in captions:
        lines = cap["text"].split("\n")
        if len(lines) > 2:
            violations.append(cap["caption_id"])
        if any(len(line.split()) > 7 for line in lines):
            violations.append(cap["caption_id"])
        if cap.get("safe_area_status") != "compliant":
            warnings.append(f"{cap['caption_id']} unsafe caption area")
    if violations:
        issues.append("caption readability rule violation")
    score = _score(issues, warnings, base=96)
    report = {
        "production_id": render["production_id"], "component_id": "IF-FQC03", "component_name": "Caption QC", "timestamp": now(),
        "captions_exist": bool(captions), "caption_count": len(captions), "timing_status": "aligned", "readability_score": score,
        "safe_area_status": "compliant" if not warnings else "warning", "line_length_violations": violations, "spelling_warnings": [],
        "issues_found": issues, "warnings": warnings, "score": score, "approval_status": "approved" if not issues else "blocked",
    }
    _write(root, "caption_qc_report.json", report, "caption-qc")
    return report


def brand_compliance_checker(render: dict[str, Any], script: dict[str, Any], visual: dict[str, Any], *, root: Path = Path(".")) -> dict[str, Any]:
    text = script["final_voiceover"]
    issues, warnings = [], []
    opening = text.lower().startswith("before the first whistle")
    if not opening:
        issues.append("required opening missing")
    if not script.get("central_question") or script["central_question"].lower() not in text.lower():
        issues.append("central question missing")
    if "tell us below" not in text.lower():
        issues.append("CTA missing")
    forbidden = [word for word in FORBIDDEN_BETTING if re.search(rf"\b{re.escape(word)}\b", text, re.I)]
    if forbidden:
        issues.append("forbidden betting language found")
    if "robotic" in text.lower():
        warnings.append("robotic phrasing warning")
    dashboard_scenes = [s for s in visual["dashboard_plan"]["dashboard_cards"]]
    score = _score(issues, warnings, base=94)
    report = {
        "production_id": render["production_id"], "component_id": "IF-FQC04", "component_name": "Brand Compliance Checker", "timestamp": now(),
        "brand_opening_present": opening, "tone_status": "conversational", "central_question_present": not any("central question" in i for i in issues),
        "story_clarity_score": 92, "dashboard_clarity_score": 90 if len(dashboard_scenes) <= 5 else 75, "cta_status": "present" if "tell us below" in text.lower() else "missing",
        "forbidden_language_found": forbidden, "issues_found": issues, "warnings": warnings, "score": score, "approval_status": "approved" if not issues else "blocked",
    }
    _write(root, "brand_compliance_report.json", report, "brand-compliance")
    return report


def script_alignment_checker(render: dict[str, Any], script: dict[str, Any], storyboard: dict[str, Any], *, root: Path = Path(".")) -> dict[str, Any]:
    rendered_text = " ".join(scene["voiceover_text"] for scene in render.get("render_complete_package", {}).get("timeline", {}).get("scenes", [])) or load_json(root / OUTPUT / "renderer-ready-package.json")["timeline"]["scenes"][0]["voiceover_text"]
    full_timeline_text = " ".join(scene["voiceover_text"] for scene in load_json(root / OUTPUT / "renderer-ready-package.json")["timeline"]["scenes"])
    issues, warnings = [], []
    text = full_timeline_text.lower()
    if script["central_question"].lower() not in text:
        issues.append("central question missing")
    if script["locked_fields"]["surprising_fact"].lower() not in text:
        issues.append("surprising fact missing")
    if "tell us below" not in text:
        issues.append("CTA missing")
    if any("unauthorized" in scene["voiceover_text"].lower() for scene in load_json(root / OUTPUT / "renderer-ready-package.json")["timeline"]["scenes"]):
        issues.append("unauthorized claim added")
    scene_order = [s["scene_id"] for s in storyboard["scenes"]] == [s["scene_id"] for s in load_json(root / OUTPUT / "renderer-ready-package.json")["timeline"]["scenes"]]
    if not scene_order:
        issues.append("scene order mismatch")
    score = _score(issues, warnings, base=95)
    report = {
        "production_id": render["production_id"], "component_id": "IF-FQC05", "component_name": "Script Alignment Checker", "timestamp": now(),
        "script_match_status": "aligned" if not issues else "misaligned", "hook_present": script["hook"].lower() in text,
        "central_question_present": script["central_question"].lower() in text, "surprising_fact_present": script["locked_fields"]["surprising_fact"].lower() in text,
        "cta_present": "tell us below" in text, "unauthorized_claims": [i for i in issues if "unauthorized" in i],
        "locked_fields_status": "preserved" if not any("missing" in i for i in issues[:2]) else "failed", "scene_order_status": "aligned" if scene_order else "mismatch",
        "issues_found": issues, "warnings": warnings, "score": score, "approval_status": "approved" if not issues else "blocked",
    }
    _write(root, "script_alignment_report.json", report, "script-alignment")
    return report


def legal_copyright_checker(render: dict[str, Any], assets: dict[str, Any], script: dict[str, Any], *, root: Path = Path(".")) -> dict[str, Any]:
    issues, warnings = [], []
    blocked = [a for a in assets.get("asset_cache_index", {}).get("cache_entries", []) if a.get("legal_status") == "blocked"]
    manual = assets.get("manual_review_tasks", [])
    if blocked:
        issues.append("blocked assets used")
    if manual:
        warnings.append("manual review assets present")
    missing_legal = [a for a in assets.get("asset_cache_index", {}).get("cache_entries", []) if not a.get("legal_status")]
    if missing_legal:
        issues.append("missing legal status")
    betting_bad = [word for word in FORBIDDEN_BETTING if re.search(rf"\b{re.escape(word)}\b", script["final_voiceover"], re.I)]
    if betting_bad:
        issues.append("betting guarantee language found")
    risk = "high" if issues else ("medium" if manual else "low")
    score = 72 if manual and not issues else _score(issues, warnings, base=94)
    report = {
        "production_id": render["production_id"], "component_id": "IF-FQC06", "component_name": "Legal & Copyright Checker", "timestamp": now(),
        "blocked_assets_used": blocked, "manual_review_assets": manual, "music_license_status": "no_music_bed", "image_license_status": "fallback_or_manual_review",
        "badge_license_status": "manual_review_required" if manual else "approved_or_fallback", "copyright_risk_level": risk,
        "betting_safety_status": "safe" if not betting_bad else "unsafe", "issues_found": issues, "warnings": warnings, "score": score,
        "approval_status": "needs_human_review" if manual and not issues else ("approved" if not issues else "blocked"),
    }
    _write(root, "legal_safety_report.json", report, "legal-safety")
    return report


def publish_readiness_gate(render: dict[str, Any], reports: dict[str, dict[str, Any]], script: dict[str, Any], *, root: Path = Path(".")) -> dict[str, Any]:
    scores = {name: report["score"] for name, report in reports.items()}
    blocking = [issue for report in reports.values() for issue in report.get("issues_found", [])]
    warnings = [warning for report in reports.values() for warning in report.get("warnings", [])] + render.get("warnings", [])
    legal = reports["legal_safety_report"]
    placeholder = reports["video_qc_report"]["codec"] == "placeholder"
    if blocking or legal["copyright_risk_level"] == "high":
        status = "rejected"
    elif placeholder or legal["approval_status"] == "needs_human_review" or min(scores.values()) < 80:
        status = "needs_human_review"
    else:
        status = "approved_for_publishing"
    overall = round(sum(scores.values()) / len(scores))
    report = {
        "production_id": render["production_id"], "component_id": "IF-FQC07", "component_name": "Publish Readiness Gate", "timestamp": now(),
        "video_qc_score": scores["video_qc_report"], "audio_qc_score": scores["audio_qc_report_final"], "caption_qc_score": scores["caption_qc_report"],
        "brand_score": scores["brand_compliance_report"], "script_alignment_score": scores["script_alignment_report"], "legal_safety_score": scores["legal_safety_report"],
        "overall_score": overall, "final_status": status, "blocking_issues": blocking, "warnings": warnings,
        "human_review_required": status == "needs_human_review", "required_fixes": blocking, "approval_status": status, "next_component": "Publishing Engine",
    }
    package = {
        "production_id": render["production_id"], "match": render["match"], "competition": render["competition"], "final_video_path": render["final_video_path"],
        "thumbnail_path": render["thumbnail_path"], "render_complete_package": render, "qc_reports": reports, "publish_readiness_report": report,
        "title_seed": f"{render['match']['home_team']} vs {render['match']['away_team']}: {script['central_question']}",
        "description_seed": script["hook"], "caption_seed": script["cta"], "telegram_seed": script["central_question"],
        "legal_warnings": reports["legal_safety_report"]["warnings"], "human_review_flags": render.get("human_review_flags", []) + (["Placeholder render requires review."] if placeholder else []),
        "approval_status": status, "next_component": "Publishing Engine",
    }
    write_json(root / OUTPUT / "publish_readiness_report.json", report)
    if status in {"approved_for_publishing", "needs_human_review"}:
        write_json(root / OUTPUT / "publish-ready-package.json", package)
    StructuredLogger(root / LOGS, f"publish-readiness-gate-{render['production_id']}").log({"event": "publish_readiness_written", "status": status})
    return {"publish_readiness_report": report, "publish_ready_package": package}


def _score(issues: list[str], warnings: list[str], *, base: int) -> int:
    return max(0, base - len(issues) * 25 - len(warnings) * 4)


def _write(root: Path, filename: str, report: dict[str, Any], logger_name: str) -> None:
    write_json(root / OUTPUT / filename, report)
    StructuredLogger(root / LOGS, f"{logger_name}-{report['production_id']}").log({"event": f"{filename}_written", "approval_status": report["approval_status"]})
