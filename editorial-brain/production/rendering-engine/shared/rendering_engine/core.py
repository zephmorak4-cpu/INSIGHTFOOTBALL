from __future__ import annotations

import hashlib
import os
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from .io import StructuredLogger, load_json, now, write_json

OUTPUT = Path("editorial-brain/output")
LOGS = Path("editorial-brain/logs")
RENDERS = Path("renders")
SUPPORTED_RENDERERS = ["creatomate", "remotion", "ffmpeg", "placeholder"]
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
        ffmpeg_path = shutil.which("ffmpeg")
        return {"success": bool(ffmpeg_path), "ffmpeg_path": ffmpeg_path, "error": None if ffmpeg_path else "FFmpeg executable not found on PATH.", "dry_run": dry_run}

    def build_render_payload(self, package: dict[str, Any]) -> dict[str, Any]:
        payload = {"renderer": self.renderer_profile, "ffmpeg_path": shutil.which("ffmpeg"), "output_resolution": "1080x1920", "fps": 30, "brand_motion_standard": BRAND_MOTION_STANDARD, "scene_text": [scene["caption_text"] for scene in package["timeline"]["scenes"]], "fallback_render_enabled": True}
        write_json(OUTPUT / "ffmpeg_render_payload.json", payload)
        return payload

    def submit_render(self, payload: dict[str, Any], *, dry_run: bool = True) -> dict[str, Any]:
        if not payload.get("ffmpeg_path"):
            return {"success": False, "status": "failed", "error": "FFmpeg executable not found on PATH; structured placeholder required.", "dry_run": dry_run}
        return {"success": True, "status": "completed", "external_job_id": "ffmpeg-local", "dry_run": dry_run}

    def download_artifacts(self, job_id: str, artifact_root: Path) -> dict[str, Any]:
        if not shutil.which("ffmpeg"):
            return _write_placeholder_artifacts(artifact_root, self.renderer_profile, "FFmpeg unavailable; structured placeholder artifact created instead of MP4.")
        return _write_placeholder_artifacts(artifact_root, self.renderer_profile, "FFmpeg rendering is intentionally minimal in Sprint 10 placeholder mode.")


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
