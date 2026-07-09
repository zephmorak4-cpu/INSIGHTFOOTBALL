from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import textwrap
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from .io import StructuredLogger, load_json, now, write_json

OUTPUT = Path("editorial-brain/output")
LOGS = Path("editorial-brain/logs")
RENDERS = Path("renders")
SUPPORTED_RENDERERS = ["creatomate", "remotion", "ffmpeg", "placeholder"]
BASE_RENDER_SIZE = (1080, 1920)
DEFAULT_OUTPUT_SIZE = (720, 1280)
BRAND_MOTION_STANDARD = {
    "standard_id": "IF-BMS-1.0",
    "version": "1.0",
    "persistent_logo": {
        "required": True,
        "position": "top-left",
        "fallback_position": "top-right",
        "size_percent_frame_width": {"min": 5, "max": 8},
        "opacity_percent": {"min": 85, "max": 90},
        "respect_title_safe_margins": True,
        "avoid_subtitles_dashboards_and_statistics": True,
        "continuous_animation_allowed": False,
        "distort_stretch_rotate_recolor_crop_allowed": False,
    },
    "opening_sting": {
        "required": True,
        "duration_seconds": 1.5,
        "sequence": [
            "dark_stadium_background",
            "stadium_floodlights_illuminate",
            "red_motion_streak",
            "center_logo_fade_scale",
            "metallic_light_sweep",
            "subtle_camera_push",
        ],
        "audio": ["deep_cinematic_impact", "short_whoosh", "low_crowd_ambience"],
    },
    "transition_sting": {
        "required": True,
        "duration_seconds": 0.3,
        "between_sections": ["hook_to_analysis", "analysis_to_tactical_view", "tactical_view_to_wild_card", "wild_card_to_conclusion"],
        "animation": ["red_diagonal_swipe", "brief_logo_flash", "motion_blur", "dashboard_wipe"],
        "audio": ["short_branded_swoosh"],
    },
    "end_card": {
        "required": True,
        "duration_seconds": 4.0,
        "scene": ["dark_stadium_background", "slow_camera_push", "stadium_floodlights", "soft_smoke", "floating_particles", "centered_logo", "metallic_light_reflection"],
        "tagline": "KNOW MORE. SEE MORE. WIN MORE.",
        "cta": "Subscribe for Daily Football Intelligence",
        "icons": ["youtube", "telegram"],
        "finish": "fade_to_black",
        "audio": ["sonic_logo", "stadium_crowd_ambience", "soft_cinematic_finish"],
    },
    "graphics": {
        "panel_rules": ["logo", "red_accent_line", "dark_navy_background", "white_typography", "rounded_broadcast_panels"],
        "lower_thirds": ["small_logo", "dark_navy_background", "red_accent_strip", "white_typography", "rounded_corners"],
        "thumbnail": {"logo_required": True, "position": "top-left", "consistent_size_and_spacing": True},
    },
    "colors": {"deep_navy": "#0B132B", "sports_blue": "#0D47A1", "espn_red": "#E10600", "clean_white": "#F5F5F5", "charcoal": "#1A1A1A"},
    "typography": {"primary": ["Bebas Neue", "Anton"], "secondary": "Montserrat"},
}


class RendererInterface(ABC):
    renderer_profile: str

    @abstractmethod
    def validate_package(self, package: dict[str, Any], *, dry_run: bool = True) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def build_render_payload(self, package: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def submit_render(self, payload: dict[str, Any], *, dry_run: bool = True) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def check_status(self, job_id: str) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def download_artifacts(self, job_id: str, artifact_root: Path) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def cancel_render(self, job_id: str) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def estimate_cost(self, package: dict[str, Any]) -> float:
        raise NotImplementedError

    @abstractmethod
    def estimate_duration(self, package: dict[str, Any]) -> float:
        raise NotImplementedError


class CreatomateAdapter(RendererInterface):
    renderer_profile = "creatomate"

    def validate_package(self, package: dict[str, Any], *, dry_run: bool = True) -> dict[str, Any]:
        if not dry_run and not os.environ.get("CREATOMATE_API_KEY"):
            return {"success": False, "error": "CREATOMATE_API_KEY is required outside dry_run mode."}
        return {"success": True, "dry_run": dry_run, "warnings": [] if os.environ.get("CREATOMATE_API_KEY") else ["Missing API key; dry_run payload only."]}

    def build_render_payload(self, package: dict[str, Any]) -> dict[str, Any]:
        payload = {
            "renderer": self.renderer_profile,
            "dry_run": True,
            "template_id": os.environ.get("CREATOMATE_TEMPLATE_ID", "mock-template"),
            "output_format": "mp4",
            "brand_motion_standard": BRAND_MOTION_STANDARD,
            "modifications": [
                {"scene_id": scene["scene_id"], "template_id": scene["template_id"], "duration": scene["duration_seconds"], "text": scene["caption_text"], "assets": scene["asset_refs"]}
                for scene in package["timeline"]["scenes"]
            ],
            "captions": package["caption_sync"]["captions"],
            "audio": package["required_audio"],
        }
        write_json(OUTPUT / "creatomate_render_payload.json", payload)
        return payload

    def submit_render(self, payload: dict[str, Any], *, dry_run: bool = True) -> dict[str, Any]:
        return {"success": True, "external_job_id": "creatomate-dry-run", "status": "completed" if dry_run else "queued", "dry_run": dry_run}

    def check_status(self, job_id: str) -> dict[str, Any]:
        return {"job_id": job_id, "status": "completed", "progress": 100}

    def download_artifacts(self, job_id: str, artifact_root: Path) -> dict[str, Any]:
        return _write_placeholder_artifacts(artifact_root, self.renderer_profile, "Creatomate dry-run does not download media artifacts.")

    def cancel_render(self, job_id: str) -> dict[str, Any]:
        return {"job_id": job_id, "status": "cancelled"}

    def estimate_cost(self, package: dict[str, Any]) -> float:
        return round(package["timeline"]["total_duration_seconds"] * 0.002, 4)

    def estimate_duration(self, package: dict[str, Any]) -> float:
        return float(package["timeline"]["total_duration_seconds"])


class RemotionAdapter(CreatomateAdapter):
    renderer_profile = "remotion"

    def build_render_payload(self, package: dict[str, Any]) -> dict[str, Any]:
        payload = {"renderer": self.renderer_profile, "status": "not_implemented", "composition_id": "InsightFootballVertical", "brand_motion_standard": BRAND_MOTION_STANDARD, "props": {"production_id": package["production_id"], "scene_count": len(package["timeline"]["scenes"])}, "reason": "Remotion adapter contract exists; rendering implementation is reserved for a future sprint."}
        write_json(OUTPUT / "remotion_render_payload.json", payload)
        return payload

    def submit_render(self, payload: dict[str, Any], *, dry_run: bool = True) -> dict[str, Any]:
        return {"success": True, "status": "not_implemented", "dry_run": dry_run, "message": payload["reason"]}


class PlaceholderAdapter(CreatomateAdapter):
    renderer_profile = "placeholder"

    def build_render_payload(self, package: dict[str, Any]) -> dict[str, Any]:
        payload = {"renderer": self.renderer_profile, "mode": "structured_placeholder", "production_id": package["production_id"], "scene_count": len(package["timeline"]["scenes"]), "duration": package["timeline"]["total_duration_seconds"], "brand_motion_standard": BRAND_MOTION_STANDARD, "reason": "Placeholder renderer documents render intent without producing video frames."}
        write_json(OUTPUT / "render_payload.json", payload)
        return payload

    def submit_render(self, payload: dict[str, Any], *, dry_run: bool = True) -> dict[str, Any]:
        return {"success": True, "external_job_id": "placeholder-local", "status": "completed", "dry_run": dry_run}

    def download_artifacts(self, job_id: str, artifact_root: Path) -> dict[str, Any]:
        return _write_placeholder_artifacts(artifact_root, self.renderer_profile, "Placeholder renderer selected; no video encoding attempted.")

    def estimate_cost(self, package: dict[str, Any]) -> float:
        return 0.0


class FFmpegAdapter(PlaceholderAdapter):
    renderer_profile = "ffmpeg"

    def validate_package(self, package: dict[str, Any], *, dry_run: bool = True) -> dict[str, Any]:
        ffmpeg_path = _ffmpeg_path()
        return {"success": bool(ffmpeg_path), "ffmpeg_path": ffmpeg_path, "error": None if ffmpeg_path else "FFmpeg executable not found. Set FFMPEG_BINARY_PATH or install ffmpeg on PATH.", "dry_run": dry_run}

    def build_render_payload(self, package: dict[str, Any]) -> dict[str, Any]:
        segments = _build_branded_segments(package)
        payload = {
            "renderer": self.renderer_profile,
            "ffmpeg_path": _ffmpeg_path(),
            "output_resolution": f"{DEFAULT_OUTPUT_SIZE[0]}x{DEFAULT_OUTPUT_SIZE[1]}",
            "fps": 30,
            "output_format": "mp4",
            "brand_motion_standard": BRAND_MOTION_STANDARD,
            "segments": segments,
            "scene_text": [scene["caption_text"] for scene in package["timeline"]["scenes"]],
            "fallback_render_enabled": False,
        }
        self._last_package = package
        self._last_payload = payload
        write_json(OUTPUT / "ffmpeg_render_payload.json", payload)
        return payload

    def submit_render(self, payload: dict[str, Any], *, dry_run: bool = True) -> dict[str, Any]:
        if not payload.get("ffmpeg_path"):
            return {"success": False, "status": "failed", "error": "FFmpeg executable not found. Real MP4 rendering requires ffmpeg.", "dry_run": dry_run}
        return {"success": True, "status": "completed", "external_job_id": "ffmpeg-local", "dry_run": dry_run}

    def download_artifacts(self, job_id: str, artifact_root: Path) -> dict[str, Any]:
        payload = getattr(self, "_last_payload", None)
        package = getattr(self, "_last_package", None)
        ffmpeg_path = _ffmpeg_path()
        if not payload or not package:
            raise RuntimeError("FFmpeg render payload missing; build_render_payload must run before download_artifacts.")
        if not ffmpeg_path:
            raise RuntimeError("FFmpeg executable not found. Cannot generate final_video.mp4.")
        return _render_ffmpeg_artifacts(package, payload, artifact_root, ffmpeg_path)


def get_renderer(profile: str) -> RendererInterface:
    renderers = {"creatomate": CreatomateAdapter(), "remotion": RemotionAdapter(), "ffmpeg": FFmpegAdapter(), "placeholder": PlaceholderAdapter()}
    if profile not in renderers:
        raise ValueError(f"Unsupported renderer profile: {profile}")
    return renderers[profile]


class RenderJobBuilder:
    def build(self, package: dict[str, Any], renderer: RendererInterface, payload: dict[str, Any], *, dry_run: bool = True) -> dict[str, Any]:
        production_id = package["production_id"]
        job = {"production_id": production_id, "job_id": f"render-{production_id}", "timestamp": now(), "renderer_profile": renderer.renderer_profile, "input_package": "renderer-ready-package.json", "render_payload": payload, "brand_motion_standard": payload.get("brand_motion_standard", BRAND_MOTION_STANDARD), "output_settings": package["render_plan"]["output_settings"], "required_assets": package["required_assets"], "required_audio": package["required_audio"], "required_fonts": package["required_fonts"], "estimated_duration_seconds": renderer.estimate_duration(package), "estimated_cost": renderer.estimate_cost(package), "dry_run": dry_run, "status": "queued", "warnings": package.get("validation_report", {}).get("warnings", []), "approval_status": "approved"}
        write_json(OUTPUT / "render_job.json", job)
        return job


class RenderQueueManager:
    def queue(self, job: dict[str, Any]) -> dict[str, Any]:
        return self._status(job, "queued", 0)

    def update(self, job: dict[str, Any], status: str, *, errors: list[str] | None = None, artifact_refs: dict[str, Any] | None = None) -> dict[str, Any]:
        progress = {"queued": 0, "validating": 20, "rendering": 60, "completed": 100, "failed": 100, "cancelled": 100}.get(status, 0)
        return self._status(job, status, progress, errors=errors or [], artifact_refs=artifact_refs or {})

    def _status(self, job: dict[str, Any], status: str, progress: int, *, errors: list[str] | None = None, artifact_refs: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = {"job_id": job["job_id"], "production_id": job["production_id"], "renderer_profile": job["renderer_profile"], "status": status, "progress": progress, "started_at": job["timestamp"], "completed_at": now() if status in {"completed", "failed", "cancelled"} else None, "duration_seconds": job["estimated_duration_seconds"] if status == "completed" else 0, "errors": errors or [], "warnings": job.get("warnings", []), "artifact_refs": artifact_refs or {}}
        write_json(OUTPUT / "render_status.json", payload)
        return payload


def artifact_manager(package: dict[str, Any], job: dict[str, Any], renderer: RendererInterface, payload: dict[str, Any], root: Path = Path(".")) -> dict[str, Any]:
    artifact_root = root / RENDERS / package["production_id"]
    artifact_root.mkdir(parents=True, exist_ok=True)
    logs_path = artifact_root / "logs"
    logs_path.mkdir(exist_ok=True)
    write_json(artifact_root / "render_job.json", job)
    write_json(artifact_root / "render_payload.json", payload)
    artifacts = renderer.download_artifacts(job["job_id"], artifact_root)
    final_video = artifacts["final_video_path"]
    thumbnail = artifacts["thumbnail_path"]
    output = {"production_id": package["production_id"], "job_id": job["job_id"], "artifact_root": str(artifact_root), "final_video_path": final_video, "thumbnail_path": thumbnail, "payload_path": str(artifact_root / "render_payload.json"), "logs_path": str(logs_path), "file_sizes": _file_sizes([final_video, thumbnail, str(artifact_root / "render_payload.json")]), "checksums": _checksums([final_video, thumbnail, str(artifact_root / "render_payload.json")]), "missing_artifacts": [path for path in [final_video, thumbnail] if not Path(path).exists()], "approval_status": "approved"}
    write_json(OUTPUT / "render_artifacts.json", output)
    write_json(artifact_root / "render_artifacts.json", output)
    return output


def render_validator(package: dict[str, Any], job: dict[str, Any], status: dict[str, Any], artifacts: dict[str, Any], *, allow_placeholder: bool = True) -> dict[str, Any]:
    final_path = Path(artifacts["final_video_path"])
    thumb_path = Path(artifacts["thumbnail_path"])
    placeholder = final_path.suffix == ".json"
    issues, warnings = [], list(job.get("warnings", []))
    if not final_path.exists():
        issues.append("video artifact missing")
    if placeholder and allow_placeholder:
        warnings.append("Structured placeholder video artifact used; no MP4 generated.")
    elif placeholder:
        issues.append("placeholder artifact not allowed")
    if package["timeline"]["total_duration_seconds"] > 60:
        issues.append("duration exceeds 60 seconds")
    if package["timeline"].get("aspect_ratio") != "9:16":
        issues.append("wrong aspect ratio")
    if package["timeline"].get("resolution") != "1080x1920":
        issues.append("wrong resolution")
    if package["timeline"].get("fps") != 30:
        issues.append("wrong fps")
    if not thumb_path.exists():
        warnings.append("Thumbnail placeholder missing.")
    if status["status"] not in {"completed", "failed"}:
        issues.append("render job status not terminal")
    if package.get("render_readiness_status") == "failed_validation":
        issues.append("renderer-ready package failed validation")
    brand_report = _brand_motion_checks(job)
    issues.extend(brand_report["issues"])
    report = {"production_id": package["production_id"], "component_id": "IF-RE08", "component_name": "Render Validator", "timestamp": now(), "checks": {"video_exists_or_placeholder": final_path.exists() and (not placeholder or allow_placeholder), "duration": package["timeline"]["total_duration_seconds"] <= 60, "aspect_ratio": package["timeline"].get("aspect_ratio") == "9:16", "resolution": package["timeline"].get("resolution") == "1080x1920", "fps": package["timeline"].get("fps") == 30, "audio_documented": bool(package.get("required_audio")), "captions_documented": bool(package.get("caption_sync", {}).get("captions")), "thumbnail_exists": thumb_path.exists(), "job_terminal": status["status"] in {"completed", "failed"}, "legal": package.get("render_readiness_status") != "failed_validation", "brand_motion_standard": brand_report["passed"]}, "brand_motion_report": brand_report, "issues": issues, "warnings": warnings, "placeholder_mode": placeholder, "approval_status": "approved" if not issues else "blocked"}
    write_json(OUTPUT / "render_validation_report.json", report)
    return report


def run_all(root: Path = Path("."), renderer_profile: str = "placeholder", *, dry_run: bool = True) -> dict[str, Any]:
    package = load_json(root / OUTPUT / "renderer-ready-package.json")
    renderer = get_renderer(renderer_profile)
    validation = renderer.validate_package(package, dry_run=dry_run)
    payload = renderer.build_render_payload(package)
    write_json(root / OUTPUT / "render_payload.json", payload)
    job = RenderJobBuilder().build(package, renderer, payload, dry_run=dry_run)
    queue = RenderQueueManager()
    queue.queue(job)
    submit = renderer.submit_render(payload, dry_run=dry_run)
    status_name = "completed" if submit.get("success") else "failed"
    artifacts = artifact_manager(package, job, renderer, payload, root)
    status = queue.update(job, status_name, errors=[] if submit.get("success") else [submit.get("error", "render failed")], artifact_refs=artifacts)
    report = render_validator(package, job, status, artifacts)
    complete = {"production_id": package["production_id"], "match": package["match"], "competition": package["competition"], "source_renderer_ready_package": package["production_id"], "renderer_profile": renderer_profile, "brand_motion_standard": BRAND_MOTION_STANDARD, "render_job": job, "render_status": status, "render_artifacts": artifacts, "render_validation_report": report, "final_video_path": artifacts["final_video_path"], "thumbnail_path": artifacts["thumbnail_path"], "duration_seconds": package["timeline"]["total_duration_seconds"], "file_size": artifacts["file_sizes"].get(artifacts["final_video_path"], 0), "checksums": artifacts["checksums"], "warnings": report["warnings"] + validation.get("warnings", []), "human_review_flags": ["Review placeholder render before publishing."] if report["placeholder_mode"] else [], "approval_status": report["approval_status"], "next_component": "Final Quality Control"}
    write_json(root / OUTPUT / "render-complete-package.json", complete)
    StructuredLogger(root / LOGS, f"rendering-engine-{package['production_id']}").log({"event": "render_complete_package_written", "renderer": renderer_profile, "approval_status": complete["approval_status"]})
    return {"render_job": job, "render_status": status, "render_artifacts": artifacts, "render_validation_report": report, "render_complete_package": complete}


def _write_placeholder_artifacts(root: Path, renderer: str, reason: str) -> dict[str, Any]:
    root.mkdir(parents=True, exist_ok=True)
    video = root / "final_video.placeholder.json"
    thumb = root / "thumbnail_frame.placeholder.json"
    write_json(video, {"artifact_type": "structured_video_placeholder", "renderer": renderer, "reason": reason, "created_at": now(), "expected_final_name": "final_video.mp4"})
    write_json(thumb, {"artifact_type": "structured_thumbnail_placeholder", "renderer": renderer, "reason": reason, "created_at": now(), "expected_final_name": "thumbnail_frame.png"})
    return {"final_video_path": str(video), "thumbnail_path": str(thumb), "placeholder": True, "reason": reason}


def _ffmpeg_path() -> str | None:
    configured = os.environ.get("FFMPEG_BINARY_PATH")
    if configured and Path(configured).exists():
        return configured
    executable = shutil.which("ffmpeg")
    if executable:
        return executable
    try:
        import imageio_ffmpeg
    except ImportError:
        return None
    bundled = imageio_ffmpeg.get_ffmpeg_exe()
    return bundled if bundled and Path(bundled).exists() else None


def _build_branded_segments(package: dict[str, Any]) -> list[dict[str, Any]]:
    transition_points = {"hook_to_analysis", "analysis_to_tactical_view", "tactical_view_to_wild_card", "wild_card_to_conclusion"}
    scenes = [scene for scene in package["timeline"]["scenes"] if scene.get("scene_type") not in {"Brand Opening", "End Card", "Outro"}]
    if not scenes:
        scenes = package["timeline"]["scenes"]
    transition_count = min(4, max(0, len(scenes) - 1))
    reserved = BRAND_MOTION_STANDARD["opening_sting"]["duration_seconds"] + BRAND_MOTION_STANDARD["end_card"]["duration_seconds"] + transition_count * BRAND_MOTION_STANDARD["transition_sting"]["duration_seconds"]
    content_budget = max(1.0, float(package["timeline"]["total_duration_seconds"]) - reserved)
    source_total = sum(float(scene.get("duration_seconds", 1.0)) for scene in scenes) or 1.0
    segments: list[dict[str, Any]] = [{"kind": "opening_sting", "duration_seconds": 1.5, "title": "INSIGHT FOOTBALL", "subtitle": BRAND_MOTION_STANDARD["end_card"]["tagline"]}]
    for index, scene in enumerate(scenes):
        scaled = round(content_budget * float(scene.get("duration_seconds", 1.0)) / source_total, 2)
        segments.append({
            "kind": "content_scene",
            "duration_seconds": max(1.0, scaled),
            "scene_id": scene.get("scene_id"),
            "scene_type": scene.get("scene_type", "Analysis"),
            "title": scene.get("scene_type", "INSIGHT"),
            "body": scene.get("caption_text") or scene.get("voiceover_text", ""),
            "voiceover_text": scene.get("voiceover_text", ""),
            "brand_panel": True,
            "lower_third": True,
            "persistent_logo": True,
        })
        if index < transition_count:
            transition_name = list(transition_points)[index] if index < len(transition_points) else "section_transition"
            segments.append({"kind": "transition_sting", "duration_seconds": 0.3, "transition": transition_name, "persistent_logo": True})
    segments.append({"kind": "end_card", "duration_seconds": 4.0, "title": "INSIGHT FOOTBALL", "tagline": BRAND_MOTION_STANDARD["end_card"]["tagline"], "cta": BRAND_MOTION_STANDARD["end_card"]["cta"]})
    return segments


def _render_ffmpeg_artifacts(package: dict[str, Any], payload: dict[str, Any], artifact_root: Path, ffmpeg_path: str) -> dict[str, Any]:
    artifact_root.mkdir(parents=True, exist_ok=True)
    frames_dir = artifact_root / "frames"
    frames_dir.mkdir(exist_ok=True)
    frame_entries = []
    for index, segment in enumerate(payload["segments"]):
        frame_path = frames_dir / f"segment_{index:03d}_{segment['kind']}.png"
        _draw_segment_frame(package, segment, frame_path)
        frame_entries.append({"path": frame_path, "duration": float(segment["duration_seconds"])})
    video_path = artifact_root / "final_video.mp4"
    thumbnail_path = artifact_root / "thumbnail_frame.png"
    concat_path = frames_dir / "concat.txt"
    _write_concat_file(concat_path, frame_entries)
    _run_ffmpeg_encode(ffmpeg_path, concat_path, video_path)
    shutil.copyfile(frame_entries[1]["path"] if len(frame_entries) > 2 else frame_entries[0]["path"], thumbnail_path)
    manifest = {
        "artifact_type": "real_mp4_render",
        "renderer": "ffmpeg",
        "created_at": now(),
        "production_id": package["production_id"],
        "duration_seconds": round(sum(entry["duration"] for entry in frame_entries), 2),
        "resolution": f"{DEFAULT_OUTPUT_SIZE[0]}x{DEFAULT_OUTPUT_SIZE[1]}",
        "fps": payload["fps"],
        "brand_motion_standard": payload["brand_motion_standard"]["standard_id"],
        "segments": payload["segments"],
    }
    write_json(artifact_root / "render_manifest.json", manifest)
    return {"final_video_path": str(video_path), "thumbnail_path": str(thumbnail_path), "manifest_path": str(artifact_root / "render_manifest.json"), "placeholder": False, "reason": "FFmpeg generated a real MP4 render."}


def _draw_segment_frame(package: dict[str, Any], segment: dict[str, Any], path: Path) -> None:
    width, height = BASE_RENDER_SIZE
    colors = BRAND_MOTION_STANDARD["colors"]
    image = Image.new("RGB", (width, height), colors["deep_navy"])
    draw = ImageDraw.Draw(image)
    _draw_stadium_background(draw, width, height, segment["kind"])
    if segment["kind"] == "opening_sting":
        _draw_center_logo(draw, width, height, scale=1.55)
        _draw_match_scoreboard(draw, package, y=250)
        _draw_text_center(draw, segment["subtitle"], y=1200, size=42, fill=colors["clean_white"], max_width=880)
        _draw_red_streak(draw, width, height, y=1040)
    elif segment["kind"] == "transition_sting":
        _draw_transition(draw, width, height)
    elif segment["kind"] == "end_card":
        _draw_center_logo(draw, width, height, scale=1.25)
        _draw_text_center(draw, "KNOW MORE.\nSEE MORE.\nWIN MORE.", y=1080, size=58, fill=colors["clean_white"], max_width=880)
        _draw_text_center(draw, segment["cta"], y=1360, size=36, fill=colors["clean_white"], max_width=900)
        _draw_social_icons(draw, width, height)
    else:
        _draw_corner_logo(draw)
        _draw_live_score_bar(draw, package)
        _draw_ticker(draw, segment)
        _draw_brand_panel(draw, segment, package)
        _draw_lower_third(draw, segment)
    output_width, output_height = DEFAULT_OUTPUT_SIZE
    if (width, height) != (output_width, output_height):
        image = image.resize((output_width, output_height), Image.Resampling.LANCZOS)
    image.save(path)


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default()


def _draw_stadium_background(draw: ImageDraw.ImageDraw, width: int, height: int, kind: str) -> None:
    colors = BRAND_MOTION_STANDARD["colors"]
    for y in range(0, height, 8):
        ratio = y / height
        blue = int(43 + 45 * (1 - ratio))
        draw.rectangle([0, y, width, y + 8], fill=(3, 12, blue))
    for x in range(-80, width + 120, 180):
        draw.polygon([(x, 0), (x + 90, 0), (width // 2, 760)], fill=(25, 42, 70))
    draw.rectangle([0, 1380, width, height], fill=(6, 12, 22))
    for x in range(90, width, 150):
        draw.ellipse([x - 12, 120, x + 12, 144], fill=(245, 245, 245))
        draw.line([x, 145, width // 2, 760], fill=(45, 60, 88), width=2)
    if kind in {"opening_sting", "end_card"}:
        for x in range(0, width, 80):
            draw.point((x + 20, 540 + (x % 9) * 14), fill=colors["clean_white"])


def _draw_center_logo(draw: ImageDraw.ImageDraw, width: int, height: int, *, scale: float) -> None:
    colors = BRAND_MOTION_STANDARD["colors"]
    font_if = _font(int(180 * scale))
    font_name = _font(int(76 * scale))
    x = width // 2 - int(250 * scale)
    y = height // 2 - int(190 * scale)
    draw.text((x, y), "I", font=font_if, fill=colors["clean_white"])
    draw.text((x + int(112 * scale), y), "F", font=font_if, fill=colors["espn_red"])
    draw.ellipse([x + int(8 * scale), y + int(160 * scale), x + int(92 * scale), y + int(244 * scale)], outline=colors["clean_white"], width=max(4, int(5 * scale)))
    draw.arc([x - int(18 * scale), y + int(142 * scale), x + int(185 * scale), y + int(280 * scale)], 15, 165, fill=colors["espn_red"], width=max(5, int(8 * scale)))
    draw.text((x + int(270 * scale), y + int(70 * scale)), "INSIGHT", font=font_name, fill=colors["clean_white"])
    draw.text((x + int(270 * scale), y + int(150 * scale)), "FOOTBALL", font=font_name, fill=colors["espn_red"])


def _draw_match_scoreboard(draw: ImageDraw.ImageDraw, package: dict[str, Any], *, y: int) -> None:
    colors = BRAND_MOTION_STANDARD["colors"]
    match = package.get("match", {})
    home = match.get("home_team", "HOME")
    away = match.get("away_team", "AWAY")
    competition = package.get("competition", "Competition")
    draw.rounded_rectangle([90, y, 990, y + 210], radius=24, fill=(7, 14, 28), outline=(245, 245, 245), width=3)
    draw.rectangle([90, y, 990, y + 14], fill=colors["espn_red"])
    _draw_badge(draw, 160, y + 64, home)
    _draw_badge(draw, 850, y + 64, away)
    draw.text((300, y + 54), f"{home}  v  {away}", font=_font(48), fill=colors["clean_white"])
    draw.text((300, y + 118), competition, font=_font(30), fill=(210, 220, 235))
    draw.text((440, y + 160), "MATCH PREVIEW", font=_font(28), fill=colors["espn_red"])


def _draw_badge(draw: ImageDraw.ImageDraw, x: int, y: int, name: str) -> None:
    colors = BRAND_MOTION_STANDARD["colors"]
    initials = "".join(part[:1] for part in str(name).split()[:2]).upper() or "FC"
    draw.ellipse([x - 46, y - 46, x + 46, y + 46], fill=(11, 24, 48), outline=colors["espn_red"], width=5)
    draw.text((x - 24, y - 24), initials[:2], font=_font(34), fill=colors["clean_white"])


def _draw_live_score_bar(draw: ImageDraw.ImageDraw, package: dict[str, Any]) -> None:
    colors = BRAND_MOTION_STANDARD["colors"]
    match = package.get("match", {})
    draw.rounded_rectangle([210, 48, 1032, 138], radius=14, fill=(7, 14, 28), outline=(34, 58, 86), width=2)
    draw.rectangle([210, 48, 230, 138], fill=colors["espn_red"])
    draw.text((250, 70), f"{match.get('home_team', 'HOME')} v {match.get('away_team', 'AWAY')}", font=_font(34), fill=colors["clean_white"])
    draw.text((790, 74), package.get("competition", "Competition"), font=_font(26), fill=(210, 220, 235))


def _draw_ticker(draw: ImageDraw.ImageDraw, segment: dict[str, Any]) -> None:
    colors = BRAND_MOTION_STANDARD["colors"]
    draw.rectangle([0, 1818, 1080, 1884], fill=(7, 14, 28))
    draw.rectangle([0, 1818, 115, 1884], fill=colors["espn_red"])
    draw.text((28, 1834), "IF", font=_font(32), fill=colors["clean_white"])
    label = str(segment.get("scene_type", "Match intelligence")).upper()
    draw.text((140, 1834), label[:55], font=_font(28), fill=colors["clean_white"])


def _draw_corner_logo(draw: ImageDraw.ImageDraw) -> None:
    colors = BRAND_MOTION_STANDARD["colors"]
    draw.rounded_rectangle([48, 48, 188, 138], radius=16, fill=(7, 14, 28), outline=(245, 245, 245), width=2)
    draw.text((65, 54), "I", font=_font(64), fill=colors["clean_white"])
    draw.text((105, 54), "F", font=_font(64), fill=colors["espn_red"])
    draw.ellipse([69, 104, 99, 134], outline=colors["clean_white"], width=3)


def _draw_brand_panel(draw: ImageDraw.ImageDraw, segment: dict[str, Any], package: dict[str, Any]) -> None:
    colors = BRAND_MOTION_STANDARD["colors"]
    draw.rounded_rectangle([72, 280, 1008, 1330], radius=28, fill=(8, 19, 43), outline=(28, 52, 82), width=4)
    draw.rectangle([72, 280, 94, 1330], fill=colors["espn_red"])
    scene_type = str(segment.get("scene_type", "ANALYSIS")).upper()
    match = package.get("match", {})
    title = f"{match.get('home_team', 'HOME')} vs {match.get('away_team', 'AWAY')}"
    draw.text((124, 330), scene_type, font=_font(48), fill=colors["espn_red"])
    draw.text((124, 405), title, font=_font(58), fill=colors["clean_white"])
    _draw_text_box(draw, segment.get("body", ""), x=124, y=540, max_width=820, line_height=72, size=58)
    draw.line([124, 1160, 956, 1160], fill=colors["espn_red"], width=5)
    draw.text((124, 1200), "DATA-DRIVEN FOOTBALL INTELLIGENCE", font=_font(34), fill=(210, 220, 235))


def _draw_lower_third(draw: ImageDraw.ImageDraw, segment: dict[str, Any]) -> None:
    colors = BRAND_MOTION_STANDARD["colors"]
    draw.rounded_rectangle([72, 1490, 1008, 1638], radius=20, fill=(7, 14, 28), outline=(34, 58, 86), width=3)
    draw.rectangle([72, 1490, 96, 1638], fill=colors["espn_red"])
    draw.text((124, 1515), "INSIGHT FOOTBALL", font=_font(32), fill=colors["clean_white"])
    draw.text((124, 1562), str(segment.get("scene_type", "Analysis")), font=_font(44), fill=colors["espn_red"])


def _draw_transition(draw: ImageDraw.ImageDraw, width: int, height: int) -> None:
    colors = BRAND_MOTION_STANDARD["colors"]
    draw.polygon([(-120, 0), (340, 0), (width + 120, height), (650, height)], fill=colors["espn_red"])
    draw.polygon([(260, 0), (450, 0), (width + 120, height), (930, height)], fill=(245, 245, 245))
    _draw_center_logo(draw, width, height, scale=0.8)


def _draw_red_streak(draw: ImageDraw.ImageDraw, width: int, height: int, *, y: int) -> None:
    colors = BRAND_MOTION_STANDARD["colors"]
    draw.polygon([(0, y), (width, y - 95), (width, y - 30), (0, y + 65)], fill=colors["espn_red"])


def _draw_social_icons(draw: ImageDraw.ImageDraw, width: int, height: int) -> None:
    colors = BRAND_MOTION_STANDARD["colors"]
    y = 1530
    draw.rounded_rectangle([width // 2 - 160, y, width // 2 - 40, y + 92], radius=20, fill=colors["espn_red"])
    draw.polygon([(width // 2 - 112, y + 24), (width // 2 - 112, y + 68), (width // 2 - 72, y + 46)], fill=colors["clean_white"])
    draw.ellipse([width // 2 + 40, y, width // 2 + 160, y + 92], fill=(0, 136, 204))
    draw.polygon([(width // 2 + 70, y + 48), (width // 2 + 138, y + 20), (width // 2 + 115, y + 72)], fill=colors["clean_white"])


def _draw_text_center(draw: ImageDraw.ImageDraw, text: str, *, y: int, size: int, fill: str, max_width: int) -> None:
    lines = []
    for raw_line in text.splitlines():
        lines.extend(textwrap.wrap(raw_line, width=max(8, max_width // max(size // 2, 1))) or [""])
    font = _font(size)
    total_height = len(lines) * int(size * 1.25)
    current_y = y - total_height // 2
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        draw.text(((1080 - (bbox[2] - bbox[0])) // 2, current_y), line, font=font, fill=fill)
        current_y += int(size * 1.25)


def _draw_text_box(draw: ImageDraw.ImageDraw, text: str, *, x: int, y: int, max_width: int, line_height: int, size: int) -> None:
    colors = BRAND_MOTION_STANDARD["colors"]
    font = _font(size)
    lines = textwrap.wrap(str(text), width=max(10, max_width // max(size // 2, 1)))[:7]
    for index, line in enumerate(lines):
        draw.text((x, y + index * line_height), line, font=font, fill=colors["clean_white"])


def _write_concat_file(path: Path, frame_entries: list[dict[str, Any]]) -> None:
    lines = []
    base_dir = path.parent
    for entry in frame_entries:
        frame_path = Path(entry["path"])
        frame = os.path.relpath(frame_path, base_dir).replace("\\", "/").replace("'", "'\\''")
        lines.append(f"file '{frame}'")
        lines.append(f"duration {entry['duration']:.2f}")
    if frame_entries:
        frame_path = Path(frame_entries[-1]["path"])
        frame = os.path.relpath(frame_path, base_dir).replace("\\", "/").replace("'", "'\\''")
        lines.append(f"file '{frame}'")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _run_ffmpeg_encode(ffmpeg_path: str, concat_path: Path, video_path: Path) -> None:
    output_width, output_height = DEFAULT_OUTPUT_SIZE
    command = [
        ffmpeg_path,
        "-y",
        "-threads",
        "1",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(concat_path),
        "-vf",
        f"scale={output_width}:{output_height},format=yuv420p",
        "-c:v",
        "libx264",
        "-preset",
        "ultrafast",
        "-crf",
        "28",
        "-r",
        "30",
        "-movflags",
        "+faststart",
        str(video_path),
    ]
    result = subprocess.run(command, text=True, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg render failed: {result.stderr[-1000:]}")


def _brand_motion_checks(job: dict[str, Any]) -> dict[str, Any]:
    standard = job["brand_motion_standard"] if "brand_motion_standard" in job else job.get("render_payload", {}).get("brand_motion_standard", {})
    checks = {
        "persistent_corner_logo": bool(standard.get("persistent_logo", {}).get("required")) and standard.get("persistent_logo", {}).get("position") in {"top-left", "top-right"},
        "opening_sting": standard.get("opening_sting", {}).get("required") is True and standard.get("opening_sting", {}).get("duration_seconds") == 1.5,
        "transition_sting": standard.get("transition_sting", {}).get("required") is True and standard.get("transition_sting", {}).get("duration_seconds") == 0.3,
        "end_card": standard.get("end_card", {}).get("required") is True and standard.get("end_card", {}).get("duration_seconds") == 4.0,
        "thumbnail_logo": standard.get("graphics", {}).get("thumbnail", {}).get("logo_required") is True,
    }
    issues = [f"brand motion missing: {name}" for name, passed in checks.items() if not passed]
    return {"standard_id": standard.get("standard_id"), "checks": checks, "issues": issues, "passed": not issues}


def _file_sizes(paths: list[str]) -> dict[str, int]:
    return {path: Path(path).stat().st_size for path in paths if Path(path).exists()}


def _checksums(paths: list[str]) -> dict[str, str]:
    checksums = {}
    for path in paths:
        p = Path(path)
        if p.exists():
            h = hashlib.sha256()
            h.update(p.read_bytes())
            checksums[path] = h.hexdigest()
    return checksums
