from __future__ import annotations

import json
import mimetypes
import os
import time
import urllib.request
from pathlib import Path
from typing import Any

from .errors import MVPError
from .io_utils import OUTPUT, RENDERS, now_iso, write_json


ENDPOINT = "https://api.creatomate.com/v2/renders"


def render_video(selection: dict[str, Any], content: dict[str, Any], assets: dict[str, Any]) -> dict[str, Any]:
    api_key = os.environ.get("CREATOMATE_API_KEY", "").strip()
    template_id = os.environ.get("CREATOMATE_MASTER_TEMPLATE_ID", "").strip()
    logo = os.environ.get("INSIGHT_FOOTBALL_LOGO_URL", "").strip()
    if not api_key:
        raise MVPError("CREATOMATE_API_KEY_REQUIRED", "CREATOMATE_API_KEY is required.")
    if not template_id:
        raise MVPError("CREATOMATE_MASTER_TEMPLATE_ID_REQUIRED", "CREATOMATE_MASTER_TEMPLATE_ID is required.")
    if not logo:
        raise MVPError("INSIGHT_FOOTBALL_LOGO_URL_REQUIRED", "INSIGHT_FOOTBALL_LOGO_URL is required for live MVP rendering.")

    payload = {"template_id": template_id, "modifications": _modifications(selection, content, assets), "output_format": "mp4", "metadata": json.dumps({"production_id": selection["production_id"]})}
    write_json(OUTPUT / "creatomate_render_payload.json", payload)
    response = _api_json("POST", ENDPOINT, api_key, payload)
    write_json(OUTPUT / "creatomate_render_response.json", response)
    render_id = _render_id(response)
    status = _poll(render_id, api_key)
    if status["status"] != "succeeded" or not status.get("output_url"):
        raise MVPError("CREATOMATE_RENDER_FAILED", "Creatomate render did not produce an MP4.", status)
    video_path = _download_mp4(selection["production_id"], str(status["output_url"]))
    return {"render_id": render_id, "render_status": "succeeded", "final_video_path": str(video_path), "duration_seconds": 60, "resolution": "1080x1920", "fetched_at": now_iso()}


def _modifications(selection: dict[str, Any], content: dict[str, Any], assets: dict[str, Any]) -> dict[str, str]:
    evidence = content.get("evidence_points", [])
    evidence_1 = evidence[0] if isinstance(evidence, list) and evidence else ""
    evidence_2 = evidence[1] if isinstance(evidence, list) and len(evidence) > 1 else ""
    return {
        "brand_logo": assets["brand_logo"],
        "home_team": selection["home_team"],
        "away_team": selection["away_team"],
        "home_badge": assets["home_badge"],
        "away_badge": assets["away_badge"],
        "competition": selection["competition"],
        "competition_logo": assets["competition_logo"],
        "central_question": content["central_question"],
        "hook": content["hook"],
        "evidence_1": str(evidence_1),
        "evidence_2": str(evidence_2),
        "conclusion": content["balanced_conclusion"],
        "cta": content["final_cta"],
        "tagline": "KNOW MORE. SEE MORE. WIN MORE.",
    }


def _api_json(method: str, url: str, api_key: str, body: dict[str, Any] | None = None) -> Any:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    headers = {"Authorization": f"Bearer {api_key}", "Accept": "application/json", "Content-Type": "application/json"}
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=45) as response:
        return json.loads(response.read().decode("utf-8", errors="replace"))


def _render_id(response: Any) -> str:
    item = response[0] if isinstance(response, list) and response else response
    render_id = item.get("id") if isinstance(item, dict) else None
    if not render_id:
        raise MVPError("CREATOMATE_RENDER_ID_MISSING", "Creatomate did not return a render ID.")
    return str(render_id)


def _poll(render_id: str, api_key: str) -> dict[str, Any]:
    attempts = int(os.environ.get("CREATOMATE_POLL_ATTEMPTS", "30"))
    seconds = int(os.environ.get("CREATOMATE_POLL_SECONDS", "5"))
    status = {"status": "submitted", "render_id": render_id}
    for _ in range(attempts):
        body = _api_json("GET", f"{ENDPOINT}/{render_id}", api_key)
        item = body[0] if isinstance(body, list) and body else body
        raw = str(item.get("status", "rendering")).lower()
        mapped = {"done": "succeeded", "completed": "succeeded", "planned": "rendering", "processing": "rendering"}.get(raw, raw)
        status = {"status": mapped, "render_id": render_id, "output_url": item.get("url") or item.get("output_url")}
        write_json(OUTPUT / "render_status.json", status)
        if mapped in {"succeeded", "failed", "cancelled"}:
            return status
        time.sleep(seconds)
    return status


def _download_mp4(production_id: str, url: str) -> Path:
    target = RENDERS / production_id / "final_video.mp4"
    target.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"Accept": "video/mp4,*/*"})
    with urllib.request.urlopen(request, timeout=120) as response:
        content_type = response.headers.get("Content-Type", "")
        data = response.read()
    target.write_bytes(data)
    report = {"target_path": str(target), "content_type": content_type, "file_size": target.stat().st_size, "mime_guess": mimetypes.guess_type(target.name)[0], "approval_status": "approved"}
    if target.stat().st_size <= 0 or ("video/mp4" not in content_type and report["mime_guess"] != "video/mp4"):
        report["approval_status"] = "blocked"
        write_json(OUTPUT / "download_report.json", report)
        raise MVPError("MP4_VALIDATION_FAILED", "Downloaded file is not a valid MP4.", report)
    write_json(OUTPUT / "download_report.json", report)
    write_json(target.parent / "download_report.json", report)
    return target
