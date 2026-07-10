from __future__ import annotations

import hashlib
import json
import mimetypes
import os
import shutil
import subprocess
import textwrap
import time
import urllib.error
import urllib.request
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from .io import StructuredLogger, load_json, now, write_json

OUTPUT = Path("editorial-brain/output")
LOGS = Path("editorial-brain/logs")
RENDERS = Path("renders")
SUPPORTED_RENDERERS = ["creatomate", "remotion", "ffmpeg", "placeholder"]
CREATOMATE_TEMPLATES_ENDPOINT = "https://api.creatomate.com/v1/templates"
CREATOMATE_RENDERS_ENDPOINT = "https://api.creatomate.com/v2/renders"
CREATOMATE_REQUIRED_TEMPLATE_ENVS = [
    "CREATOMATE_TEMPLATE_OPENING_STING",
    "CREATOMATE_TEMPLATE_MATCH_INTRO",
    "CREATOMATE_TEMPLATE_SURPRISING_FACT",
    "CREATOMATE_TEMPLATE_CENTRAL_QUESTION",
    "CREATOMATE_TEMPLATE_EVIDENCE_CARD",
    "CREATOMATE_TEMPLATE_TACTICAL_BOARD",
    "CREATOMATE_TEMPLATE_TEAM_COMPARISON",
    "CREATOMATE_TEMPLATE_DASHBOARD",
    "CREATOMATE_TEMPLATE_CTA",
    "CREATOMATE_TEMPLATE_CLOSING_STING",
]
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
GLOBAL_CREATOMATE_VARIABLES = [
    "brand_logo",
    "corner_logo",
    "home_team",
    "away_team",
    "competition",
    "home_badge",
    "away_badge",
    "competition_logo",
    "match_title",
    "central_question",
    "surprising_fact",
    "main_insight",
    "primary_evidence",
    "secondary_evidence",
    "viewer_takeaway",
    "cta_text",
    "tagline",
]
SAMPLE_TERMS = ["Liverpool", "Arsenal", "Anfield", "Emirates", "Salah", "Haaland", "Qarabag", "Vestri"]


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
        warnings: list[str] = []
        issues: list[str] = []
        if not dry_run and not _clean_env("CREATOMATE_API_KEY"):
            issues.append("CREATOMATE_API_KEY is required in Creatomate live mode.")
        registry = _creatomate_registry()
        missing_templates = _missing_live_template_ids(registry, require_all=True)
        if missing_templates and not dry_run:
            issues.append("Missing Creatomate template IDs: " + ", ".join(missing_templates))
        if missing_templates and dry_run:
            warnings.append("Missing template IDs; dry-run fallback IDs will be used.")
        return {"success": not issues, "dry_run": dry_run, "warnings": warnings, "issues": issues, "error": "; ".join(issues) if issues else None}

    def build_render_payload(self, package: dict[str, Any]) -> dict[str, Any]:
        variables = _creatomate_variables(package)
        registry = _creatomate_registry()
        scenes = _creatomate_scenes(package, registry, variables)
        payload = {
            "renderer": self.renderer_profile,
            "dry_run": os.environ.get("INSIGHT_FOOTBALL_DRY_RUN", "true").lower() != "false",
            "template_id": _template_id(registry["templates"][0], dry_run=True),
            "output_format": "mp4",
            "metadata": {"production_id": package["production_id"], "match": variables["match_title"], "competition": variables["competition"]},
            "render_audio_mode": os.environ.get("INSIGHT_FOOTBALL_RENDER_AUDIO_MODE", "silent"),
            "variables": variables,
            "brand_motion_standard": BRAND_MOTION_STANDARD,
            "template_registry_version": registry.get("version", "1.0"),
            "scenes": scenes,
            "modifications": _legacy_scene_modifications(package, variables),
            "creatomate_modifications": _creatomate_modifications(variables),
            "captions": _creatomate_captions(variables) if package.get("_editorial_context_applied") else package["caption_sync"]["captions"],
            "audio": _creatomate_audio(os.environ.get("INSIGHT_FOOTBALL_RENDER_AUDIO_MODE", "silent")),
            "required_global_variables": GLOBAL_CREATOMATE_VARIABLES,
            "validation": _validate_creatomate_payload(package, variables, scenes),
        }
        webhook_url = os.environ.get("CREATOMATE_WEBHOOK_URL", "").strip()
        if webhook_url:
            payload["webhook_url"] = webhook_url
        payload["validation"] = _validate_creatomate_payload(package, variables, scenes, payload=payload)
        write_json(OUTPUT / "creatomate_render_payload.json", payload)
        return payload

    def submit_render(self, payload: dict[str, Any], *, dry_run: bool = True) -> dict[str, Any]:
        if payload.get("validation", {}).get("issues"):
            return {"success": False, "status": "failed", "error": "; ".join(payload["validation"]["issues"]), "dry_run": dry_run}
        if dry_run:
            return {"success": True, "external_job_id": "creatomate-dry-run", "status": "dry_run", "dry_run": True, "creatomate_status": "dry_run_complete"}
        diagnostic = creatomate_connection_diagnostic()
        if diagnostic["approval_status"] != "approved":
            return {"success": False, "status": "failed", "error": "; ".join(diagnostic["blocking_issues"]), "dry_run": False, "creatomate_status": diagnostic["authentication_status"], "diagnostic": diagnostic}
        api_key = _clean_env("CREATOMATE_API_KEY")
        if not api_key:
            return {"success": False, "status": "failed", "error": "CREATOMATE_API_KEY is required in live mode.", "dry_run": False}
        render_body = {"template_id": payload["template_id"], "modifications": payload["creatomate_modifications"], "output_format": payload.get("output_format", "mp4"), "metadata": payload.get("metadata", {})}
        if payload.get("webhook_url"):
            render_body["webhook_url"] = payload["webhook_url"]
        write_json(OUTPUT / "creatomate_render_payload.json", render_body)
        request = urllib.request.Request(
            CREATOMATE_RENDERS_ENDPOINT,
            data=json.dumps(render_body).encode("utf-8"),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
            method="POST",
        )
        last_error: dict[str, Any] = {}
        for _ in range(2):
            try:
                with urllib.request.urlopen(request, timeout=30) as response:
                    body = json.loads(response.read().decode("utf-8"))
                job_id = _creatomate_job_id(body)
                write_json(OUTPUT / "creatomate_render_response.json", body)
                status = self._poll_until_terminal(job_id, api_key, body)
                if status.get("status") == "succeeded" and status.get("output_url"):
                    return {"success": True, "external_job_id": job_id, "status": "succeeded", "dry_run": False, "creatomate_status": "succeeded", "response": body, "status_response": status, "output_url": status["output_url"]}
                return {"success": False, "external_job_id": job_id, "status": status.get("status", "failed"), "dry_run": False, "creatomate_status": status.get("status", "failed"), "error": status.get("error", "Creatomate render did not produce a downloadable MP4."), "response": body, "status_response": status}
            except urllib.error.HTTPError as exc:
                last_error = _creatomate_http_error(exc, payload)
                if exc.code == 403:
                    write_json(OUTPUT / "creatomate_render_response.json", last_error)
                    return {"success": False, "status": "failed", "dry_run": False, "creatomate_status": "forbidden", "error": "CREATOMATE_ACCESS_FORBIDDEN", "failure": last_error}
                time.sleep(1)
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
                last_error = {"code": "CREATOMATE_SUBMISSION_FAILED", "error": str(exc), "endpoint": CREATOMATE_RENDERS_ENDPOINT}
                time.sleep(1)
        return {"success": False, "status": "failed", "error": "Creatomate render submission failed.", "dry_run": False, "failure": last_error}

    def check_status(self, job_id: str) -> dict[str, Any]:
        api_key = _clean_env("CREATOMATE_API_KEY")
        if not api_key:
            return {"job_id": job_id, "status": "failed", "error": "CREATOMATE_API_KEY missing"}
        return self._fetch_status(job_id, api_key)

    def download_artifacts(self, job_id: str, artifact_root: Path) -> dict[str, Any]:
        return _write_placeholder_artifacts(artifact_root, self.renderer_profile, "Creatomate dry-run stores payload only.")

    def download_creatomate_video(self, output_url: str, artifact_root: Path, response: dict[str, Any] | None = None) -> dict[str, Any]:
        artifact_root.mkdir(parents=True, exist_ok=True)
        video_path = artifact_root / "final_video.mp4"
        thumb_path = artifact_root / "thumbnail_frame.png"
        report = {"source_url": output_url, "target_path": str(video_path), "content_type": "", "file_size": 0, "checks": {}, "approval_status": "blocked"}
        request = urllib.request.Request(output_url, headers={"Accept": "video/mp4,*/*"})
        with urllib.request.urlopen(request, timeout=120) as response_obj:
            content_type = response_obj.headers.get("Content-Type", "")
            data = response_obj.read()
        video_path.write_bytes(data)
        if response is not None:
            write_json(artifact_root / "creatomate_render_response.json", response)
        report["content_type"] = content_type
        report["file_size"] = video_path.stat().st_size
        mime_type = mimetypes.guess_type(video_path.name)[0] or ""
        checks = {
            "exists": video_path.exists(),
            "size_gt_zero": video_path.stat().st_size > 0,
            "mime_mp4": "video/mp4" in content_type.lower() or mime_type == "video/mp4",
            "not_placeholder": "placeholder" not in video_path.name,
        }
        report["checks"] = checks
        report["approval_status"] = "approved" if all(checks.values()) else "blocked"
        write_json(artifact_root / "download_report.json", report)
        write_json(OUTPUT / "download_report.json", report)
        if not thumb_path.exists():
            write_json(thumb_path.with_suffix(".placeholder.json"), {"artifact_type": "thumbnail_placeholder", "reason": "Creatomate MP4 downloaded; thumbnail extraction unavailable."})
            thumb_path = thumb_path.with_suffix(".placeholder.json")
        return {"final_video_path": str(video_path), "thumbnail_path": str(thumb_path), "placeholder": False, "download_report": report, "reason": "Creatomate MP4 downloaded."}

    def _poll_until_terminal(self, job_id: str, api_key: str, initial_body: Any) -> dict[str, Any]:
        wait_seconds = float(os.environ.get("CREATOMATE_POLL_SECONDS", "1"))
        attempts = int(os.environ.get("CREATOMATE_POLL_ATTEMPTS", "6"))
        status = _creatomate_status_from_body(initial_body)
        if status.get("status") == "succeeded" and status.get("output_url"):
            return status
        for _ in range(attempts):
            status = self._fetch_status(job_id, api_key)
            if status.get("status") in {"succeeded", "failed", "cancelled"}:
                return status
            time.sleep(wait_seconds)
        return {**status, "status": status.get("status", "rendering"), "error": "Creatomate render did not finish before polling timeout."}

    def _fetch_status(self, job_id: str, api_key: str) -> dict[str, Any]:
        request = urllib.request.Request(f"{CREATOMATE_RENDERS_ENDPOINT}/{job_id}", headers={"Authorization": f"Bearer {api_key}", "Accept": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                body = json.loads(response.read().decode("utf-8"))
            status = _creatomate_status_from_body(body)
            write_json(OUTPUT / "render_status.json", {"job_id": job_id, **status})
            return status
        except urllib.error.HTTPError as exc:
            return {"job_id": job_id, "status": "failed", "error": _safe_excerpt(exc.read().decode("utf-8", errors="replace")), "http_status": exc.code}

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


def _clean_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return ""
    return value


def _safe_excerpt(text: str, limit: int = 500) -> str:
    api_key = os.environ.get("CREATOMATE_API_KEY", "")
    cleaned = text.replace(api_key, "[REDACTED]") if api_key else text
    return cleaned[:limit]


def _configured_template_ids() -> dict[str, str]:
    configured = {}
    fallback = os.environ.get("CREATOMATE_TEMPLATE_ID", "").strip()
    for env_name in CREATOMATE_REQUIRED_TEMPLATE_ENVS:
        value = os.environ.get(env_name, "").strip() or fallback
        if value:
            configured[env_name] = value
    return configured


def _template_ids_from_response(body: Any) -> set[str]:
    if isinstance(body, dict):
        items = body.get("templates") or body.get("data") or body.get("items") or body.get("response") or []
    else:
        items = body
    ids = set()
    if isinstance(items, list):
        for item in items:
            if isinstance(item, dict):
                for key in ["id", "template_id", "templateId"]:
                    if item.get(key):
                        ids.add(str(item[key]))
    return ids


def creatomate_connection_diagnostic() -> dict[str, Any]:
    api_key = _clean_env("CREATOMATE_API_KEY")
    configured_templates = _configured_template_ids()
    missing_envs = [env for env in CREATOMATE_REQUIRED_TEMPLATE_ENVS if env not in configured_templates]
    report: dict[str, Any] = {
        "api_key_present": bool(api_key),
        "authentication_status": "not_checked",
        "http_status": None,
        "project_access_status": "not_checked",
        "templates_found": [],
        "templates_missing": missing_envs,
        "response_body_safe_excerpt": "",
        "blocking_issues": [],
        "approval_status": "blocked",
    }
    if not api_key:
        report["authentication_status"] = "missing_api_key"
        report["blocking_issues"].append("CREATOMATE_API_KEY is missing, blank, or wrapped in quotes.")
        write_json(OUTPUT / "creatomate_connection_report.json", report)
        return report
    request = urllib.request.Request(CREATOMATE_TEMPLATES_ENDPOINT, headers={"Authorization": f"Bearer {api_key}", "Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body_text = response.read().decode("utf-8", errors="replace")
            status = response.status
    except urllib.error.HTTPError as exc:
        body_text = exc.read().decode("utf-8", errors="replace")
        status = exc.code
    except urllib.error.URLError as exc:
        body_text = str(exc)
        status = None
    report["http_status"] = status
    report["response_body_safe_excerpt"] = _safe_excerpt(body_text)
    if status != 200:
        report["authentication_status"] = "failed"
        report["project_access_status"] = "blocked"
        report["blocking_issues"].append(f"Creatomate template listing failed with HTTP status {status}.")
        write_json(OUTPUT / "creatomate_connection_report.json", report)
        return report
    try:
        body = json.loads(body_text)
    except json.JSONDecodeError:
        body = []
    accessible_ids = _template_ids_from_response(body)
    found, missing = [], list(missing_envs)
    for env_name, template_id in configured_templates.items():
        entry = {"env": env_name, "template_id": template_id}
        if template_id in accessible_ids:
            found.append(entry)
        else:
            missing.append(env_name)
    report["authentication_status"] = "authenticated"
    report["project_access_status"] = "accessible" if not missing else "template_mismatch"
    report["templates_found"] = found
    report["templates_missing"] = sorted(set(missing))
    if report["templates_missing"]:
        report["blocking_issues"].append("Configured Creatomate template IDs are missing from the API key's project.")
    report["approval_status"] = "approved" if not report["blocking_issues"] else "blocked"
    write_json(OUTPUT / "creatomate_connection_report.json", report)
    return report


def _creatomate_registry() -> dict[str, Any]:
    path = Path("editorial-brain/production/rendering-engine/creatomate-template-registry.json")
    if not path.exists():
        return {"version": "missing", "templates": []}
    return load_json(path)


def _missing_live_template_ids(registry: dict[str, Any], *, require_all: bool = False) -> list[str]:
    missing = []
    if require_all:
        for env_name in CREATOMATE_REQUIRED_TEMPLATE_ENVS:
            if not os.environ.get(env_name) and not os.environ.get("CREATOMATE_TEMPLATE_ID"):
                missing.append(env_name)
    for item in registry.get("templates", []):
        env_name = item.get("creatomate_template_id_env")
        if env_name and not os.environ.get(env_name) and not os.environ.get("CREATOMATE_TEMPLATE_ID") and env_name not in missing:
            missing.append(env_name)
    return missing


def _template_id(template: dict[str, Any], *, dry_run: bool) -> str:
    env_name = template.get("creatomate_template_id_env", "")
    configured = os.environ.get(env_name) or os.environ.get("CREATOMATE_TEMPLATE_ID")
    if configured:
        return configured
    if dry_run:
        return f"dry-run-{template.get('template_key', 'template')}"
    return ""


def _creatomate_variables(package: dict[str, Any]) -> dict[str, str]:
    match = package.get("match", {})
    home = str(match.get("home_team", "HOME"))
    away = str(match.get("away_team", "AWAY"))
    competition = str(package.get("competition") or match.get("competition", "Competition"))
    title = f"{home} vs {away}"
    return {
        "brand_logo": str(package.get("brand_logo", "{{BRAND_LOGO}}")),
        "corner_logo": str(package.get("corner_logo", "{{CORNER_LOGO}}")),
        "home_team": home,
        "away_team": away,
        "competition": competition,
        "home_badge": str(package.get("home_badge", f"{{{{{home.upper().replace(' ', '_')}_BADGE}}}}")),
        "away_badge": str(package.get("away_badge", f"{{{{{away.upper().replace(' ', '_')}_BADGE}}}}")),
        "competition_logo": str(package.get("competition_logo", "{{COMPETITION_LOGO}}")),
        "match_title": title,
        "kickoff_time": str(match.get("kickoff_time", "")),
        "story_angle": str(package.get("story_angle", "")),
        "central_question": str(package.get("central_question", "")),
        "surprising_fact": str(package.get("surprising_fact", "")),
        "main_insight": str(package.get("insight_summary", "")),
        "primary_evidence": _first_text(package.get("primary_evidence", [])),
        "secondary_evidence": _first_text(package.get("secondary_evidence", [])),
        "viewer_takeaway": str(package.get("viewer_takeaway", "")),
        "cta_text": str(package.get("cta_text") or package.get("central_question") or "Tell us what you think."),
        "tagline": "KNOW MORE. SEE MORE. WIN MORE.",
    }


def _first_text(items: Any) -> str:
    if isinstance(items, list) and items:
        first = items[0]
        if isinstance(first, dict):
            return str(first.get("simple_translation") or first.get("claim") or first)
        return str(first)
    return ""


def _creatomate_scenes(package: dict[str, Any], registry: dict[str, Any], variables: dict[str, str]) -> list[dict[str, Any]]:
    scenes = []
    for template in registry.get("templates", []):
        key = template["template_key"]
        scenes.append(
            {
                "template_key": key,
                "template_id": _template_id(template, dry_run=True),
                "duration_seconds": template["duration_seconds"],
                "variables": {name: variables.get(name, "") for name in template.get("required_variables", []) + template.get("optional_variables", [])},
                "animation_requirements": template.get("animation_requirements", []),
                "visual_elements": _visual_elements_for_template(key),
                "transition_sting_before": key not in {"opening_sting", "match_intro"},
                "persistent_corner_logo": key not in {"opening_sting", "closing_sting"},
                "logo_rules": {"preserve_aspect_ratio": True, "safe_margin_px": 48, "corner_opacity_percent": 88},
            }
        )
    return scenes


def _visual_elements_for_template(key: str) -> list[str]:
    mapping = {
        "opening_sting": ["brand_logo", "home_badge", "away_badge", "competition_logo", "stadium_background", "red_motion_streak"],
        "match_intro": ["home_badge", "away_badge", "vs_text", "competition_logo", "red_accent_line", "background_zoom"],
        "central_question": ["question_text", "home_badge", "away_badge", "particles", "corner_logo"],
        "evidence_card": ["stat_card", "keyword", "supporting_icon", "background_motion", "corner_logo"],
        "tactical_board": ["pitch_graphic", "animated_arrows", "player_markers", "camera_pan", "corner_logo"],
        "team_comparison": ["comparison_cards", "home_badge", "away_badge", "animated_bars", "corner_logo"],
        "insight_dashboard": ["dashboard_cards", "animated_bars", "highlight_card", "background_motion", "corner_logo"],
        "cta_card": ["cta_text", "comment_icon", "corner_logo", "red_accent_line"],
        "closing_sting": ["brand_logo", "tagline", "final_cta", "particles", "fade_to_black"],
    }
    return mapping.get(key, ["background", "text", "motion_element"])


def _creatomate_modifications(variables: dict[str, str]) -> dict[str, str]:
    return {f"{key}.text": value for key, value in variables.items()}


def _legacy_scene_modifications(package: dict[str, Any], variables: dict[str, str]) -> list[dict[str, Any]]:
    dynamic_text = [
        variables["match_title"],
        variables["central_question"],
        variables["surprising_fact"],
        variables["main_insight"],
        variables["viewer_takeaway"],
        variables["cta_text"],
    ]
    output = []
    for index, scene in enumerate(package["timeline"]["scenes"]):
        text = dynamic_text[index % len(dynamic_text)] if package.get("_editorial_context_applied") else scene.get("caption_text", "")
        output.append(
            {
                "scene_id": scene.get("scene_id"),
                "template_id": scene.get("template_id", "creatomate_dynamic_scene"),
                "duration": scene.get("duration_seconds", 4),
                "text": text,
                "assets": scene.get("asset_refs", []),
            }
        )
    return output


def _creatomate_captions(variables: dict[str, str]) -> list[dict[str, Any]]:
    lines = [
        variables["match_title"],
        variables["central_question"],
        variables["main_insight"],
        variables["viewer_takeaway"],
        variables["cta_text"],
    ]
    return [{"caption_id": f"creatomate-caption-{index:02d}", "text": text[:90], "safe_area_status": "compliant"} for index, text in enumerate(lines, start=1) if text]


def _creatomate_audio(mode: str) -> dict[str, Any]:
    return {
        "mode": mode,
        "status": "silent_placeholder" if mode == "silent" else "awaiting_voice_asset",
        "capcut_ready": mode == "silent",
        "notes": "Audio mode: silent, ready for CapCut voice/audio overlay" if mode == "silent" else "Audio asset required before live publishing.",
    }


def _validate_creatomate_payload(package: dict[str, Any], variables: dict[str, str], scenes: list[dict[str, Any]], payload: dict[str, Any] | None = None) -> dict[str, Any]:
    issues = []
    missing = [name for name in GLOBAL_CREATOMATE_VARIABLES if not str(variables.get(name, "")).strip()]
    if missing:
        issues.append("Missing Creatomate variables: " + ", ".join(missing))
    if not any(scene["template_key"] == "opening_sting" for scene in scenes):
        issues.append("opening_sting template missing")
    if not any(scene["template_key"] == "closing_sting" for scene in scenes):
        issues.append("closing_sting template missing")
    if any(len(scene.get("visual_elements", [])) < 3 for scene in scenes):
        issues.append("Every Creatomate scene must include at least three visual elements.")
    if any(not scene.get("animation_requirements") for scene in scenes):
        issues.append("Every Creatomate scene must include animation requirements.")
    selected = f"{variables.get('home_team')} {variables.get('away_team')}"
    text = json.dumps(payload if payload is not None else {"variables": variables, "scenes": scenes}, ensure_ascii=True)
    leaks = [term for term in SAMPLE_TERMS if term in text and term not in selected]
    if leaks:
        issues.append("Sample data leaked into Creatomate payload: " + ", ".join(sorted(set(leaks))))
    return {"passed": not issues, "issues": sorted(set(issues))}


def _creatomate_job_id(body: Any) -> str:
    if isinstance(body, list) and body and isinstance(body[0], dict):
        return str(body[0].get("id") or body[0].get("render_id") or "creatomate-render")
    if isinstance(body, dict):
        return str(body.get("id") or body.get("render_id") or "creatomate-render")
    return "creatomate-render"


def _creatomate_status_from_body(body: Any) -> dict[str, Any]:
    item = body[0] if isinstance(body, list) and body and isinstance(body[0], dict) else body
    if not isinstance(item, dict):
        return {"status": "failed", "error": "Unexpected Creatomate status response."}
    raw_status = str(item.get("status") or item.get("state") or "rendering").lower()
    status_map = {"done": "succeeded", "completed": "succeeded", "success": "succeeded", "rendered": "succeeded", "queued": "submitted", "pending": "submitted", "processing": "rendering"}
    status = status_map.get(raw_status, raw_status)
    output_url = item.get("url") or item.get("output_url") or item.get("outputUrl") or item.get("mp4_url")
    if not output_url and isinstance(item.get("output"), dict):
        output = item["output"]
        output_url = output.get("url") or output.get("mp4_url")
    return {"job_id": str(item.get("id") or item.get("render_id") or ""), "status": status, "output_url": output_url, "error": item.get("error") or item.get("message")}


def _creatomate_http_error(exc: urllib.error.HTTPError, payload: dict[str, Any]) -> dict[str, Any]:
    detail = exc.read().decode("utf-8", errors="replace")
    return {
        "code": "CREATOMATE_ACCESS_FORBIDDEN" if exc.code == 403 else "CREATOMATE_HTTP_ERROR",
        "probable_causes": [
            "invalid API key",
            "API key from a different Creatomate project",
            "template ID belongs to another project",
            "Authorization header missing or malformed",
            "request sent to the wrong Creatomate endpoint",
            "account/project access restriction",
        ] if exc.code == 403 else [],
        "http_status": exc.code,
        "safe_response_excerpt": _safe_excerpt(detail),
        "request_endpoint": CREATOMATE_RENDERS_ENDPOINT,
        "template_id": payload.get("template_id"),
        "production_id": payload.get("metadata", {}).get("production_id"),
        "timestamp": now(),
    }


def _write_failed_render_artifacts(root: Path, renderer: str, submit_result: dict[str, Any]) -> dict[str, Any]:
    root.mkdir(parents=True, exist_ok=True)
    failure = {
        "artifact_type": "render_failure",
        "renderer": renderer,
        "created_at": now(),
        "status": submit_result.get("creatomate_status") or submit_result.get("status", "failed"),
        "error": submit_result.get("error"),
        "failure": submit_result.get("failure") or submit_result.get("diagnostic") or {},
    }
    write_json(root / "render_status.json", failure)
    write_json(OUTPUT / "render_status.json", failure)
    return {"final_video_path": str(root / "final_video.mp4"), "thumbnail_path": str(root / "thumbnail_frame.png"), "placeholder": False, "approval_status": "blocked", "failure": failure, "reason": "Creatomate did not produce a real MP4."}


def _current_editorial_package(root: Path) -> dict[str, Any]:
    daily_path = root / OUTPUT / "daily-run-report.json"
    if daily_path.exists():
        daily = load_json(daily_path)
        for step in daily.get("steps", []):
            if step.get("name") != "editorial_orchestrator":
                continue
            try:
                stdout = json.loads(step.get("stdout", ""))
            except json.JSONDecodeError:
                continue
            package_path = stdout.get("package_path")
            if package_path:
                package = load_json(Path(package_path))
                if package:
                    return package
    candidates = sorted((root / OUTPUT).glob("editorial-package-*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    return load_json(candidates[0]) if candidates else {}


def _apply_editorial_context(package: dict[str, Any], editorial: dict[str, Any]) -> dict[str, Any]:
    if not editorial:
        return package
    updated = dict(package)
    metadata = editorial.get("metadata", {})
    updated["production_id"] = metadata.get("production_id", updated.get("production_id"))
    updated["match"] = editorial.get("match", updated.get("match"))
    updated["competition"] = editorial.get("competition", updated.get("competition"))
    for field in ["story_angle", "central_question", "surprising_fact", "insight_summary", "primary_evidence", "secondary_evidence", "viewer_takeaway"]:
        if field in editorial:
            updated[field] = editorial[field]
    if "locked_fields" in editorial:
        updated["locked_fields"] = editorial["locked_fields"]
    if "agent_outputs" in editorial:
        updated["agent_outputs"] = editorial["agent_outputs"]
    if isinstance(metadata, dict):
        updated["metadata"] = metadata
    updated["_editorial_context_applied"] = True
    return updated


def _package_human_selected(package: dict[str, Any]) -> bool:
    locked = package.get("locked_fields", {})
    if isinstance(locked, dict) and locked.get("selection_source") == "human_editor":
        return True
    agent_outputs = package.get("agent_outputs", {})
    if isinstance(agent_outputs, dict):
        match_selector = agent_outputs.get("match_selector", {})
        if isinstance(match_selector, dict) and match_selector.get("selection_source") == "human_editor":
            return True
    metadata = package.get("metadata", {})
    return isinstance(metadata, dict) and metadata.get("selected_by") == "human_editor"


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
        progress = {"queued": 0, "submitted": 25, "validating": 20, "rendering": 60, "completed": 100, "succeeded": 100, "failed": 100, "cancelled": 100}.get(status, 0)
        return self._status(job, status, progress, errors=errors or [], artifact_refs=artifact_refs or {})

    def _status(self, job: dict[str, Any], status: str, progress: int, *, errors: list[str] | None = None, artifact_refs: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = {"job_id": job["job_id"], "production_id": job["production_id"], "renderer_profile": job["renderer_profile"], "status": status, "progress": progress, "started_at": job["timestamp"], "completed_at": now() if status in {"completed", "succeeded", "failed", "cancelled"} else None, "duration_seconds": job["estimated_duration_seconds"] if status in {"completed", "succeeded"} else 0, "errors": errors or [], "warnings": job.get("warnings", []), "artifact_refs": artifact_refs or {}}
        write_json(OUTPUT / "render_status.json", payload)
        return payload


def artifact_manager(package: dict[str, Any], job: dict[str, Any], renderer: RendererInterface, payload: dict[str, Any], root: Path = Path("."), submit_result: dict[str, Any] | None = None) -> dict[str, Any]:
    artifact_root = root / RENDERS / package["production_id"]
    artifact_root.mkdir(parents=True, exist_ok=True)
    logs_path = artifact_root / "logs"
    logs_path.mkdir(exist_ok=True)
    write_json(artifact_root / "render_job.json", job)
    write_json(artifact_root / "render_payload.json", payload)
    submit_result = submit_result or {}
    if isinstance(renderer, CreatomateAdapter) and not job.get("dry_run"):
        if submit_result.get("success") and submit_result.get("output_url"):
            artifacts = renderer.download_creatomate_video(str(submit_result["output_url"]), artifact_root, submit_result.get("response"))
        else:
            artifacts = _write_failed_render_artifacts(artifact_root, renderer.renderer_profile, submit_result)
    else:
        artifacts = renderer.download_artifacts(job["job_id"], artifact_root)
    final_video = artifacts["final_video_path"]
    thumbnail = artifacts["thumbnail_path"]
    output = {"production_id": package["production_id"], "job_id": job["job_id"], "artifact_root": str(artifact_root), "final_video_path": final_video, "thumbnail_path": thumbnail, "payload_path": str(artifact_root / "render_payload.json"), "logs_path": str(logs_path), "file_sizes": _file_sizes([final_video, thumbnail, str(artifact_root / "render_payload.json")]), "checksums": _checksums([final_video, thumbnail, str(artifact_root / "render_payload.json")]), "missing_artifacts": [path for path in [final_video, thumbnail] if not final_video or not Path(path).exists()], "placeholder": bool(artifacts.get("placeholder")), "download_report": artifacts.get("download_report", {}), "approval_status": "approved" if artifacts.get("approval_status", "approved") == "approved" else "blocked"}
    write_json(OUTPUT / "render_artifacts.json", output)
    write_json(artifact_root / "render_artifacts.json", output)
    return output


def render_validator(package: dict[str, Any], job: dict[str, Any], status: dict[str, Any], artifacts: dict[str, Any], *, allow_placeholder: bool = True) -> dict[str, Any]:
    final_value = str(artifacts.get("final_video_path", ""))
    thumb_value = str(artifacts.get("thumbnail_path", ""))
    final_path = Path(final_value) if final_value else Path("__missing_final_video__")
    thumb_path = Path(thumb_value) if thumb_value else Path("__missing_thumbnail__")
    placeholder = final_path.suffix == ".json" or bool(artifacts.get("placeholder"))
    issues, warnings = [], list(job.get("warnings", []))
    if not final_path.exists():
        issues.append("video artifact missing")
    if job.get("renderer_profile") == "creatomate" and not job.get("dry_run") and placeholder:
        issues.append("live Creatomate render did not produce a real MP4")
    if placeholder and allow_placeholder:
        warnings.append("Structured placeholder video artifact used; no MP4 generated.")
    elif placeholder:
        issues.append("placeholder artifact not allowed")
    if final_path.exists() and final_path.suffix.lower() != ".mp4" and not placeholder:
        issues.append("final video is not an MP4")
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
    if status["status"] not in {"completed", "failed", "succeeded"}:
        issues.append("render job status not terminal")
    if package.get("render_readiness_status") == "failed_validation":
        issues.append("renderer-ready package failed validation")
    brand_report = _brand_motion_checks(job)
    issues.extend(brand_report["issues"])
    if job.get("renderer_profile") == "creatomate":
        creatomate_validation = job.get("render_payload", {}).get("validation", {})
        issues.extend(creatomate_validation.get("issues", []))
    report = {"production_id": package["production_id"], "component_id": "IF-RE08", "component_name": "Render Validator", "timestamp": now(), "checks": {"video_exists_or_placeholder": final_path.exists() and (not placeholder or allow_placeholder), "duration": package["timeline"]["total_duration_seconds"] <= 60, "aspect_ratio": package["timeline"].get("aspect_ratio") == "9:16", "resolution": package["timeline"].get("resolution") == "1080x1920", "fps": package["timeline"].get("fps") == 30, "audio_documented": bool(package.get("required_audio")), "captions_documented": bool(package.get("caption_sync", {}).get("captions")), "thumbnail_exists": thumb_path.exists(), "job_terminal": status["status"] in {"completed", "failed", "succeeded"}, "legal": package.get("render_readiness_status") != "failed_validation", "brand_motion_standard": brand_report["passed"]}, "brand_motion_report": brand_report, "issues": issues, "warnings": warnings, "placeholder_mode": placeholder, "approval_status": "approved" if not issues else "blocked"}
    write_json(OUTPUT / "render_validation_report.json", report)
    return report


def run_all(root: Path = Path("."), renderer_profile: str = "placeholder", *, dry_run: bool = True) -> dict[str, Any]:
    package = load_json(root / OUTPUT / "renderer-ready-package.json")
    package = _apply_editorial_context(package, _current_editorial_package(root))
    if os.environ.get("INSIGHT_FOOTBALL_ENV", "").lower() == "production" and not _package_human_selected(package):
        raise RuntimeError("PRODUCTION_REQUIRES_HUMAN_EDITOR_SELECTION")
    renderer = get_renderer(renderer_profile)
    validation = renderer.validate_package(package, dry_run=dry_run)
    payload = renderer.build_render_payload(package)
    write_json(root / OUTPUT / "render_payload.json", payload)
    job = RenderJobBuilder().build(package, renderer, payload, dry_run=dry_run)
    queue = RenderQueueManager()
    queue.queue(job)
    submit = renderer.submit_render(payload, dry_run=dry_run) if validation.get("success", True) else {"success": False, "status": "failed", "error": validation.get("error", "renderer validation failed"), "dry_run": dry_run}
    if submit.get("success") and submit.get("status") == "succeeded":
        status_name = "succeeded"
    elif submit.get("success") and dry_run:
        status_name = "completed"
    elif submit.get("success"):
        status_name = str(submit.get("status", "rendering"))
    else:
        status_name = "failed"
    artifacts = artifact_manager(package, job, renderer, payload, root, submit)
    status = queue.update(job, status_name, errors=[] if submit.get("success") else [submit.get("error", "render failed")], artifact_refs=artifacts)
    report = render_validator(package, job, status, artifacts)
    real_video_ready = report["approval_status"] == "approved" and not report["placeholder_mode"] and Path(artifacts["final_video_path"]).suffix.lower() == ".mp4"
    complete = {"production_id": package["production_id"], "match": package["match"], "competition": package["competition"], "source_renderer_ready_package": package["production_id"], "renderer_profile": renderer_profile, "render_audio_mode": os.environ.get("INSIGHT_FOOTBALL_RENDER_AUDIO_MODE", "silent"), "creatomate_status": submit.get("creatomate_status", status["status"]), "video_status": "ready_for_review" if real_video_ready else status["status"], "creatomate_render_id": submit.get("external_job_id"), "brand_motion_standard": BRAND_MOTION_STANDARD, "render_job": job, "render_status": status, "render_artifacts": artifacts, "render_validation_report": report, "final_video_path": artifacts["final_video_path"], "thumbnail_path": artifacts["thumbnail_path"], "duration_seconds": package["timeline"]["total_duration_seconds"], "file_size": artifacts["file_sizes"].get(artifacts["final_video_path"], 0), "checksums": artifacts["checksums"], "warnings": sorted(set(report["warnings"] + validation.get("warnings", []))), "human_review_flags": ["Review placeholder render before publishing."] if report["placeholder_mode"] else [], "approval_status": report["approval_status"], "next_component": "Final Quality Control"}
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
