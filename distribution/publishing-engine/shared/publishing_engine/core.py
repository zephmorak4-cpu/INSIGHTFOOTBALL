from __future__ import annotations

import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .io import StructuredLogger, load_json, now, write_json

OUTPUT = Path("editorial-brain/output")
LOGS = Path("editorial-brain/logs")
FORBIDDEN = ["guaranteed", "sure odds", "cannot lose", "100% correct", "banker", "wager", "tipster"]
DEFAULT_HASHTAGS = ["#InsightFootball", "#FootballAnalysis", "#PremierLeague", "#Liverpool", "#Arsenal", "#MatchPreview", "#FootballShorts"]


def run_all(root: Path = Path("."), *, dry_run: bool = True, live: bool = False) -> dict[str, Any]:
    package = load_json(root / OUTPUT / "publish-ready-package.json")
    metadata = generate_metadata(package, root=root)
    yt = youtube_payload(package, metadata, dry_run=dry_run and not live, root=root)
    fb = facebook_payload(package, metadata, dry_run=dry_run and not live, root=root)
    tg = telegram_payload(package, metadata, dry_run=dry_run and not live, root=root)
    schedule = publishing_schedule(package, root=root)
    validation = publishing_validator(package, metadata, [yt, fb, tg], dry_run=dry_run and not live, root=root)
    status = publishing_status(package, [yt, fb, tg], schedule, validation, root=root)
    report = publish_report(package, metadata, schedule, status, root=root)
    return {"publishing_metadata": metadata, "youtube_publish_payload": yt, "facebook_publish_payload": fb, "telegram_publish_payload": tg, "publishing_schedule": schedule, "publishing_validation_report": validation, "publishing_status": status, **report}


def generate_metadata(package: dict[str, Any], *, root: Path = Path(".")) -> dict[str, Any]:
    match = package["match"]
    question = package.get("telegram_seed") or package.get("title_seed", "").split(":")[-1].strip()
    title_options = [
        question,
        "The First 20 Minutes Could Decide This Match",
        f"{match['home_team']} vs {match['away_team']}: The Insight Before Kickoff",
    ]
    selected = _safe_title(next(title for title in title_options if title))
    forbidden = _forbidden_hits(" ".join(title_options) + " " + package.get("description_seed", ""))
    hashtags = DEFAULT_HASHTAGS[:]
    metadata = {
        "production_id": package["production_id"],
        "component_id": "IF-PUB01",
        "component_name": "Publishing Metadata Generator",
        "timestamp": now(),
        "match": match,
        "competition": package["competition"],
        "video_type": "short_form_match_preview",
        "title_options": title_options,
        "selected_title": selected,
        "youtube_description": f"{package['description_seed']}\n\n{package['caption_seed']}\n\n{' '.join(hashtags)}",
        "facebook_caption": f"{selected}\n\n{package['caption_seed']}\n\n{' '.join(hashtags[:6])}",
        "telegram_post": f"{selected}\n\n{package['telegram_seed']}\n\n{package['caption_seed']}",
        "hashtags": hashtags,
        "thumbnail_text": selected[:64],
        "pinned_comment_suggestion": package["caption_seed"],
        "cta_text": package["caption_seed"],
        "forbidden_language_check": {"passed": not forbidden, "matches": forbidden},
        "warnings": ["Publish-ready package requires human review."] if package.get("approval_status") == "needs_human_review" else [],
        "approval_status": "approved" if not forbidden else "blocked",
        "next_component": "YouTube Publisher Adapter",
    }
    write_json(root / OUTPUT / "publishing_metadata.json", metadata)
    _log(root, "publishing-metadata-generator", metadata)
    return metadata


def youtube_payload(package: dict[str, Any], metadata: dict[str, Any], *, dry_run: bool = True, root: Path = Path(".")) -> dict[str, Any]:
    required = ["YOUTUBE_CLIENT_ID", "YOUTUBE_CLIENT_SECRET", "YOUTUBE_REFRESH_TOKEN", "YOUTUBE_CHANNEL_ID"]
    credential_status = _credentials(required, dry_run)
    payload = {
        "production_id": package["production_id"], "platform": "youtube", "video_path": package["final_video_path"], "title": metadata["selected_title"],
        "description": metadata["youtube_description"], "tags": [tag.lstrip("#") for tag in metadata["hashtags"]], "category": "Sports",
        "privacy_status": "private", "made_for_kids": False, "scheduled_publish_time": None, "thumbnail_path": package["thumbnail_path"],
        "dry_run": dry_run, "credential_status": credential_status, "upload_status": "dry_run_ready" if dry_run else ("ready" if credential_status["valid"] else "blocked"),
        "warnings": credential_status["warnings"], "approval_status": "approved" if credential_status["valid"] or dry_run else "blocked",
    }
    write_json(root / OUTPUT / "youtube_publish_payload.json", payload)
    return payload


def facebook_payload(package: dict[str, Any], metadata: dict[str, Any], *, dry_run: bool = True, root: Path = Path(".")) -> dict[str, Any]:
    credential_status = _credentials(["FACEBOOK_PAGE_ID", "FACEBOOK_PAGE_ACCESS_TOKEN"], dry_run)
    payload = {
        "production_id": package["production_id"], "platform": "facebook", "video_path": package["final_video_path"], "caption": metadata["facebook_caption"],
        "title": metadata["selected_title"], "description": metadata["youtube_description"], "scheduled_publish_time": None, "dry_run": dry_run,
        "credential_status": credential_status, "upload_status": "dry_run_ready" if dry_run else ("ready" if credential_status["valid"] else "blocked"),
        "warnings": credential_status["warnings"], "approval_status": "approved" if credential_status["valid"] or dry_run else "blocked",
    }
    write_json(root / OUTPUT / "facebook_publish_payload.json", payload)
    return payload


def telegram_payload(package: dict[str, Any], metadata: dict[str, Any], *, dry_run: bool = True, root: Path = Path(".")) -> dict[str, Any]:
    credential_status = _credentials(["TELEGRAM_BOT_TOKEN", "TELEGRAM_CHANNEL_ID"], dry_run)
    payload = {
        "production_id": package["production_id"], "platform": "telegram", "video_path": package["final_video_path"], "message_text": metadata["telegram_post"],
        "caption": metadata["telegram_post"], "dry_run": dry_run, "credential_status": credential_status,
        "send_status": "dry_run_ready" if dry_run else ("ready" if credential_status["valid"] else "blocked"),
        "warnings": credential_status["warnings"], "approval_status": "approved" if credential_status["valid"] or dry_run else "blocked",
    }
    write_json(root / OUTPUT / "telegram_publish_payload.json", payload)
    return payload


def publishing_schedule(package: dict[str, Any], *, root: Path = Path("."), mode: str = "publish_now") -> dict[str, Any]:
    timestamp = now()
    publish_at = datetime.now(timezone.utc) if mode == "publish_now" else datetime.now(timezone.utc) + timedelta(hours=1)
    schedule = {
        "production_id": package["production_id"], "component_id": "IF-PUB05", "component_name": "Publishing Scheduler", "timestamp": timestamp,
        "timezone": "Africa/Lagos", "schedule_mode": mode, "platforms": ["youtube", "facebook", "telegram"],
        "publish_times": {platform: publish_at.isoformat() for platform in ["youtube", "facebook", "telegram"]},
        "platform_order": ["youtube", "facebook", "telegram"], "retry_policy": {"max_retries": 1, "retry_delay_seconds": 60},
        "warnings": [], "approval_status": "approved",
    }
    write_json(root / OUTPUT / "publishing_schedule.json", schedule)
    return schedule


def publishing_validator(package: dict[str, Any], metadata: dict[str, Any], payloads: list[dict[str, Any]], *, dry_run: bool = True, root: Path = Path(".")) -> dict[str, Any]:
    blocking, warnings = [], []
    if package.get("approval_status") == "rejected":
        blocking.append("publish-ready package rejected by QC")
    if not Path(package["final_video_path"]).exists():
        blocking.append("video path missing")
    if package.get("approval_status") == "needs_human_review":
        warnings.append("package requires human review before live publishing")
    if not metadata.get("forbidden_language_check", {}).get("passed", False):
        blocking.append("forbidden language in metadata")
    for payload in payloads:
        if not dry_run and not payload["credential_status"]["valid"]:
            blocking.append(f"{payload['platform']} credentials missing for live mode")
        if payload.get("approval_status") == "blocked":
            blocking.append(f"{payload['platform']} payload blocked")
    legal_warnings = package.get("legal_warnings", [])
    warnings.extend(legal_warnings)
    report = {
        "production_id": package["production_id"], "component_id": "IF-PUB07", "component_name": "Publishing Validator", "timestamp": now(),
        "package_status": package.get("approval_status"), "video_status": "exists_or_placeholder", "metadata_status": "approved" if not _forbidden_hits(str(metadata)) else "blocked",
        "credential_status": "dry_run_allowed" if dry_run else ("valid" if not any(not p["credential_status"]["valid"] for p in payloads) else "missing"),
        "legal_status": "warnings_present" if legal_warnings else "clear", "platform_payload_status": "approved" if all(p["approval_status"] == "approved" for p in payloads) else "blocked",
        "blocking_issues": sorted(set(blocking)), "warnings": warnings, "approval_status": "approved" if not blocking else "blocked",
    }
    write_json(root / OUTPUT / "publishing_validation_report.json", report)
    return report


def publishing_status(package: dict[str, Any], payloads: list[dict[str, Any]], schedule: dict[str, Any], validation: dict[str, Any], *, root: Path = Path(".")) -> dict[str, Any]:
    jobs = []
    for payload in payloads:
        failed = validation["approval_status"] == "blocked" or payload["approval_status"] == "blocked"
        jobs.append({
            "job_id": f"publish-{package['production_id']}-{payload['platform']}", "platform": payload["platform"], "status": "failed" if failed else "dry_run_complete",
            "dry_run": payload["dry_run"], "scheduled_time": schedule["publish_times"][payload["platform"]], "started_at": now(), "completed_at": now(),
            "platform_response": {"dry_run": payload["dry_run"], "message": "No live upload performed."}, "error": "validation blocked" if failed else None,
        })
    overall = "failed" if any(job["status"] == "failed" for job in jobs) else "dry_run_complete"
    status = {"production_id": package["production_id"], "queue_id": f"queue-{package['production_id']}", "timestamp": now(), "jobs": jobs, "overall_status": overall, "errors": [j["error"] for j in jobs if j["error"]], "warnings": validation["warnings"], "approval_status": "approved" if overall != "failed" else "blocked"}
    write_json(root / OUTPUT / "publishing_status.json", status)
    return status


def publish_report(package: dict[str, Any], metadata: dict[str, Any], schedule: dict[str, Any], status: dict[str, Any], *, root: Path = Path(".")) -> dict[str, Any]:
    platforms = [job["platform"] for job in status["jobs"]]
    published = [job["platform"] for job in status["jobs"] if job["status"] == "published"]
    failed = [job["platform"] for job in status["jobs"] if job["status"] == "failed"]
    if failed and len(failed) == len(platforms):
        final_status = "failed"
    elif failed:
        final_status = "partially_published"
    elif published and len(published) == len(platforms):
        final_status = "published"
    else:
        final_status = status.get("overall_status", "dry_run_complete")
    report = {
        "production_id": package["production_id"], "component_id": "IF-PUB08", "component_name": "Publishing Report Generator", "timestamp": now(),
        "platforms_attempted": platforms, "platforms_published": published, "platforms_failed": failed, "dry_run": all(job["dry_run"] for job in status["jobs"]),
        "platform_results": status["jobs"], "errors": status["errors"], "warnings": status["warnings"], "final_status": final_status,
    }
    published_package = {
        "production_id": package["production_id"], "match": package["match"], "competition": package["competition"], "source_publish_ready_package": package["production_id"],
        "publishing_metadata": metadata, "publishing_schedule": schedule, "publishing_status": status, "publishing_report": report,
        "platform_urls": {}, "platform_ids": {}, "dry_run": report["dry_run"], "approval_status": final_status, "next_component": "Analytics Engine",
    }
    write_json(root / OUTPUT / "publishing_report.json", report)
    write_json(root / OUTPUT / "published-package.json", published_package)
    StructuredLogger(root / LOGS, f"publishing-report-{package['production_id']}").log({"event": "published_package_written", "final_status": final_status})
    return {"publishing_report": report, "published_package": published_package}


def _credentials(required: list[str], dry_run: bool) -> dict[str, Any]:
    missing = [name for name in required if not os.environ.get(name)]
    warnings = [f"Missing credentials for dry-run: {', '.join(missing)}"] if missing and dry_run else []
    return {"valid": not missing, "missing": missing, "mode": "dry_run" if dry_run else "live", "warnings": warnings}


def _forbidden_hits(text: str) -> list[str]:
    return [phrase for phrase in FORBIDDEN if re.search(re.escape(phrase), text, flags=re.IGNORECASE)]


def _safe_title(title: str) -> str:
    title = title.replace("’", "'").strip()
    return title[:95]


def _log(root: Path, name: str, payload: dict[str, Any]) -> None:
    StructuredLogger(root / LOGS, f"{name}-{payload['production_id']}").log({"event": f"{name}_written", "approval_status": payload.get("approval_status")})
