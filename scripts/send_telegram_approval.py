from __future__ import annotations

import argparse
import json
import mimetypes
import os
import urllib.parse
import urllib.request
import urllib.error
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "editorial-brain" / "output"
TELEGRAM_MESSAGE_LIMIT = 3900


def load_json(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def current_editorial_package() -> dict[str, object]:
    daily = load_json(OUTPUT / "daily-run-report.json")
    for step in daily.get("steps", []):
        if not isinstance(step, dict) or step.get("name") != "editorial_orchestrator":
            continue
        try:
            payload = json.loads(str(step.get("stdout", "")))
        except json.JSONDecodeError:
            continue
        package_path = payload.get("package_path")
        if isinstance(package_path, str) and package_path:
            package = load_json(Path(package_path))
            if package:
                return package
    candidates = sorted(OUTPUT.glob("editorial-package-*.json"), key=lambda path: path.stat().st_mtime, reverse=True)
    return load_json(candidates[0]) if candidates else {}


def approval_package() -> dict[str, object]:
    editorial = current_editorial_package()
    if editorial:
        return editorial
    return load_json(OUTPUT / "publish-ready-package.json")


def package_production_id(package: dict[str, object]) -> str:
    metadata = package.get("metadata", {})
    if isinstance(metadata, dict) and metadata.get("production_id"):
        return str(metadata["production_id"])
    return str(package.get("production_id", "unknown-production"))


def build_message(run_url: str) -> str:
    daily = load_json(OUTPUT / "daily-run-report.json")
    readiness = load_json(OUTPUT / "publish_readiness_report.json")
    publishing = load_json(OUTPUT / "publishing_report.json")
    package = approval_package()
    render = load_json(OUTPUT / "render-complete-package.json")

    production_id = package_production_id(package) or str(readiness.get("production_id") or "unknown-production")
    match = package.get("match", {})
    match_name = f"{match.get('home_team', 'Home')} vs {match.get('away_team', 'Away')}"
    warnings = readiness.get("warnings") or publishing.get("warnings") or []
    editorial_warnings = package.get("warnings", [])
    if isinstance(editorial_warnings, list):
        warnings = list(editorial_warnings) + list(warnings)
    warnings = _clean_warnings(warnings, match)
    warning_text = "\n".join(f"- {warning}" for warning in warnings[:6]) if warnings else "- None"
    story_angle = package.get("story_angle") or package.get("insight_summary") or "See package for editorial angle."
    central_question = package.get("central_question", "See package for central question.")
    selected_by = "Human editor" if _selected_by_editor(package) else "Automatic recommendation"
    audio_mode = render.get("render_audio_mode", "silent")
    render_mode = render.get("renderer_profile", "unknown")
    creatomate_status = render.get("creatomate_status", "not_used")
    video_status = str(render.get("video_status") or ("ready_for_review" if find_approval_video() else render.get("render_status", {}).get("status", "pending")))

    return "\n".join(
        [
            "INSIGHT FOOTBALL APPROVAL REQUEST",
            "",
            f"Production: {production_id}",
            f"Match: {match_name}",
            f"Competition: {match.get('competition') or package.get('competition', 'unknown')}",
            f"Selected by: {selected_by}",
            f"Audio mode: {audio_mode}, ready for CapCut voice/audio overlay" if audio_mode == "silent" else f"Audio mode: {audio_mode}",
            f"Render mode: {render_mode}",
            f"Readiness: {readiness.get('final_status', 'unknown')}",
            f"Score: {readiness.get('overall_score', 'unknown')}",
            "",
            f"Story: {story_angle}",
            f"Question: {central_question}",
            f"Video status: {video_status}",
            f"Creatomate status: {creatomate_status}",
            "",
            "Warnings:",
            warning_text,
            "",
            "Approval gate:",
            "Review video, approve, then publish.",
            "",
            f"Run: {run_url}" if run_url else "Run: unavailable",
        ]
    )


def _selected_by_editor(package: dict[str, object]) -> bool:
    agent_outputs = package.get("agent_outputs", {})
    if isinstance(agent_outputs, dict):
        selection = agent_outputs.get("match_selector", {})
        if isinstance(selection, dict) and selection.get("selection_source") == "human_editor":
            return True
    locked = package.get("locked_fields", {})
    return isinstance(locked, dict) and locked.get("selection_source") == "human_editor"


def _clean_warnings(warnings: object, match: dict[str, object]) -> list[str]:
    if not isinstance(warnings, list):
        return []
    selected_text = f"{match.get('home_team', '')} {match.get('away_team', '')} {match.get('competition', '')}"
    stale_terms = ["Liverpool", "Arsenal", "Qarabag", "Vestri", "Premier League"]
    cleaned = []
    for warning in warnings:
        text = str(warning)
        if not text.strip():
            continue
        if "sample claim" in text.lower():
            continue
        if any(term in text for term in stale_terms) and not any(term in selected_text for term in stale_terms):
            continue
        if text not in cleaned:
            cleaned.append(text)
    return cleaned


def compact_caption(run_url: str) -> str:
    readiness = load_json(OUTPUT / "publish_readiness_report.json")
    package = approval_package()
    production_id = package_production_id(package) or str(readiness.get("production_id") or "unknown-production")
    match = package.get("match", {})
    match_name = f"{match.get('home_team', 'Home')} vs {match.get('away_team', 'Away')}"
    lines = [
        "INSIGHT FOOTBALL PRODUCTION PREVIEW",
        f"Production: {production_id}",
        f"Match: {match_name}",
        f"Competition: {match.get('competition') or package.get('competition', 'unknown')}",
        "Render: Creatomate complete",
        "Audio mode: silent, ready for CapCut",
        "",
        "Review the video, then check the full script below.",
    ]
    if run_url:
        lines.append(f"Run: {run_url}")
    return "\n".join(lines)[:1024]


def find_approval_video() -> Path | None:
    candidates: list[Path] = []
    package = load_json(OUTPUT / "publish-ready-package.json")
    render_artifacts = load_json(OUTPUT / "render_artifacts.json")
    render_complete = load_json(OUTPUT / "render-complete-package.json")
    for value in [
        package.get("final_video_path"),
        render_complete.get("final_video_path"),
        render_artifacts.get("final_video_path"),
    ]:
        if isinstance(value, str) and value:
            candidates.append(Path(value))
    for candidate in candidates:
        path = candidate if candidate.is_absolute() else ROOT / candidate
        if path.exists() and path.suffix.lower() == ".mp4" and path.stat().st_size > 0:
            return path
    return None


def render_ready_for_video() -> bool:
    render = load_json(OUTPUT / "render-complete-package.json")
    if render.get("video_status") != "ready_for_review":
        return False
    if render.get("creatomate_status") not in {"succeeded", "not_used"}:
        return False
    return find_approval_video() is not None


def build_failure_alert() -> str:
    package = approval_package()
    render = load_json(OUTPUT / "render-complete-package.json")
    connection = load_json(OUTPUT / "creatomate_connection_report.json")
    status = render.get("render_status", {}) if isinstance(render.get("render_status"), dict) else {}
    match = package.get("match", {}) if isinstance(package.get("match"), dict) else {}
    failure = status.get("errors", ["Render did not produce a validated MP4."])
    return "\n".join([
        "INSIGHT FOOTBALL RENDER FAILURE",
        "",
        f"Production: {package_production_id(package)}",
        f"Match: {match.get('home_team', 'Home')} vs {match.get('away_team', 'Away')}",
        f"Creatomate status: {render.get('creatomate_status', status.get('status', 'unknown'))}",
        f"HTTP status: {connection.get('http_status', 'unknown')}",
        f"Failure code: {failure[0] if failure else 'unknown'}",
        f"Safe response: {connection.get('response_body_safe_excerpt', '')}",
        "Required action: fix Creatomate API key/template project access, then rerun production.",
    ])


def narration_script() -> str:
    for path in [
        OUTPUT / "final-script-package.json",
        OUTPUT / "optimized-script-output.json",
        OUTPUT / "script-output.json",
    ]:
        data = load_json(path)
        if not data:
            continue
        for key in ["full_voiceover_script", "voiceover_script", "script", "narration_script"]:
            value = data.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        scenes = data.get("scenes")
        if isinstance(scenes, list):
            parts = [str(scene.get("voiceover") or scene.get("voiceover_text") or scene.get("script") or "").strip() for scene in scenes if isinstance(scene, dict)]
            text = "\n\n".join(part for part in parts if part)
            if text:
                return text
    package = approval_package()
    return str(package.get("insight_summary") or package.get("story_angle") or "Narration script unavailable. Use editorial package for manual narration.")


def script_message() -> str:
    package = approval_package()
    render = load_json(OUTPUT / "render-complete-package.json")
    script = narration_script()
    words = len(script.split())
    match = package.get("match", {}) if isinstance(package.get("match"), dict) else {}
    return "\n".join([
        "INSIGHT FOOTBALL NARRATION SCRIPT",
        "",
        f"Production: {package_production_id(package)}",
        f"Match: {match.get('home_team', 'Home')} vs {match.get('away_team', 'Away')}",
        f"Competition: {match.get('competition') or package.get('competition', 'unknown')}",
        f"Estimated duration: {render.get('duration_seconds', 'unknown')}",
        f"Word count: {words}",
        "",
        "SCRIPT",
        "",
        script,
        "",
        "CAPCUT NOTES",
        "",
        "- Add recorded narration using this script.",
        "- Keep voice natural and conversational.",
        "- Match pauses to the existing scene changes.",
        "- Keep music below the voice.",
        "- Export at 1080x1920.",
    ])


def production_summary() -> str:
    package = approval_package()
    render = load_json(OUTPUT / "render-complete-package.json")
    readiness = load_json(OUTPUT / "publish_readiness_report.json")
    match = package.get("match", {}) if isinstance(package.get("match"), dict) else {}
    warnings = _clean_warnings(list(package.get("warnings", [])) + list(readiness.get("warnings", [])), match)
    warning_text = "\n".join(f"- {warning}" for warning in warnings[:8]) if warnings else "- None"
    return "\n".join([
        "INSIGHT FOOTBALL FULL PRODUCTION PACKAGE",
        "",
        f"Production: {package_production_id(package)}",
        f"Match: {match.get('home_team', 'Home')} vs {match.get('away_team', 'Away')}",
        f"Competition: {match.get('competition') or package.get('competition', 'unknown')}",
        f"Central question: {package.get('central_question', 'unknown')}",
        f"Selected story: {package.get('story_angle', package.get('insight_summary', 'unknown'))}",
        f"Surprising fact: {package.get('surprising_fact', 'unknown')}",
        f"Video duration: {render.get('duration_seconds', 'unknown')}",
        f"Audio mode: {render.get('render_audio_mode', 'silent')}",
        f"Render provider: {render.get('renderer_profile', 'unknown')}",
        f"Creatomate render ID: {render.get('creatomate_render_id', 'unknown')}",
        f"Readiness: {readiness.get('final_status', 'unknown')}",
        f"Approval status: {render.get('approval_status', 'unknown')}",
        "",
        "Included:",
        "- Video preview",
        "- Narration script",
        "- Storyboard summary",
        "- Asset summary",
        "- Caption summary",
        "- QC report",
        "",
        "Warnings:",
        warning_text,
    ])


def split_messages(text: str) -> list[str]:
    if len(text) <= TELEGRAM_MESSAGE_LIMIT:
        return [text]
    chunks, current = [], ""
    for paragraph in text.split("\n\n"):
        candidate = paragraph if not current else current + "\n\n" + paragraph
        if len(candidate) > TELEGRAM_MESSAGE_LIMIT:
            if current:
                chunks.append(current)
            current = paragraph
        else:
            current = candidate
    if current:
        chunks.append(current)
    total = len(chunks)
    return [f"Part {index + 1}/{total}\n\n{chunk}" for index, chunk in enumerate(chunks)]


def create_production_package_zip() -> Path:
    package = approval_package()
    production_id = package_production_id(package)
    artifact_root = ROOT / "renders" / production_id
    artifact_root.mkdir(parents=True, exist_ok=True)
    script_path = artifact_root / "narration-script.txt"
    script_path.write_text(narration_script(), encoding="utf-8")
    readme_path = artifact_root / "README.txt"
    readme_path.write_text("INSIGHT FOOTBALL production package for editor approval.\n", encoding="utf-8")
    manifest = {"production_id": production_id, "created_at": "", "files": []}
    zip_path = artifact_root / f"production-package-{production_id}.zip"
    candidates = [
        find_approval_video(),
        script_path,
        OUTPUT / "final-script-package.json",
        OUTPUT / "final-storyboard-package.json",
        OUTPUT / "visual-production-package.json",
        OUTPUT / "media-asset-bundle.json",
        OUTPUT / "renderer-ready-package.json",
        OUTPUT / "render-complete-package.json",
        OUTPUT / "publish_readiness_report.json",
        readme_path,
    ]
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for candidate in candidates:
            if candidate and Path(candidate).exists():
                path = Path(candidate)
                archive.write(path, path.name)
                manifest["files"].append(path.name)
        archive.writestr("production_package_manifest.json", json.dumps(manifest, indent=2))
    (artifact_root / "production_package_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return zip_path


def send_message(token: str, chat_id: str, text: str) -> None:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    body = urllib.parse.urlencode({"chat_id": chat_id, "text": text, "disable_web_page_preview": "true"}).encode("utf-8")
    request = urllib.request.Request(url, data=body, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            response.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Telegram sendMessage failed: HTTP {exc.code} {detail}") from exc


def send_video(token: str, chat_id: str, video_path: Path, caption: str) -> None:
    url = f"https://api.telegram.org/bot{token}/sendVideo"
    fields = {"chat_id": chat_id, "caption": caption, "supports_streaming": "true"}
    body, content_type = _multipart_body(fields, "video", video_path)
    request = urllib.request.Request(url, data=body, method="POST", headers={"Content-Type": content_type})
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            response.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Telegram sendVideo failed: HTTP {exc.code} {detail}") from exc


def send_document(token: str, chat_id: str, document_path: Path, caption: str) -> None:
    url = f"https://api.telegram.org/bot{token}/sendDocument"
    body, content_type = _multipart_body({"chat_id": chat_id, "caption": caption[:1024]}, "document", document_path)
    request = urllib.request.Request(url, data=body, method="POST", headers={"Content-Type": content_type})
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            response.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Telegram sendDocument failed: HTTP {exc.code} {detail}") from exc


def _multipart_body(fields: dict[str, str], file_field: str, file_path: Path) -> tuple[bytes, str]:
    boundary = "----InsightFootballTelegramBoundary"
    chunks: list[bytes] = []
    for name, value in fields.items():
        chunks.extend([
            f"--{boundary}\r\n".encode("utf-8"),
            f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("utf-8"),
            str(value).encode("utf-8"),
            b"\r\n",
        ])
    mime_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
    chunks.extend([
        f"--{boundary}\r\n".encode("utf-8"),
        f'Content-Disposition: form-data; name="{file_field}"; filename="{file_path.name}"\r\n'.encode("utf-8"),
        f"Content-Type: {mime_type}\r\n\r\n".encode("utf-8"),
        file_path.read_bytes(),
        b"\r\n",
        f"--{boundary}--\r\n".encode("utf-8"),
    ])
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Send INSIGHT FOOTBALL approval request to Telegram.")
    parser.add_argument("--run-url", default=os.environ.get("GITHUB_RUN_URL", ""))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_APPROVAL_CHAT_ID") or os.environ.get("TELEGRAM_CHANNEL_ID", "")
    message = build_message(args.run_url)
    video_path = find_approval_video()
    package = approval_package()
    if not _selected_by_editor(package):
        print(json.dumps({"sent": False, "reason": "PRODUCTION_REQUIRES_HUMAN_EDITOR_SELECTION", "message": "Telegram approval blocked because selected_by is not human_editor."}, indent=2))
        return 1

    if args.dry_run or not token or not chat_id:
        preview_message = message if render_ready_for_video() else build_failure_alert()
        print(json.dumps({"sent": False, "reason": "dry_run_or_missing_telegram_secrets", "message": preview_message, "video_attachment": str(video_path) if video_path else None}, indent=2))
        return 0

    try:
        if not render_ready_for_video():
            alert = build_failure_alert()
            send_message(token, chat_id, alert)
            report = {"sent": True, "delivery_type": "render_failure_alert", "chat_id": chat_id, "video_attached": False, "reason": "no_validated_real_mp4"}
            (OUTPUT / "telegram_video_delivery_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
            print(json.dumps(report, indent=2))
            return 0

        assert video_path is not None
        send_video(token, chat_id, video_path, compact_caption(args.run_url))
        video_report = {"sent": True, "chat_id": chat_id, "video_attached": True, "video_path": str(video_path), "message_type": "sendVideo"}
        (OUTPUT / "telegram_video_delivery_report.json").write_text(json.dumps(video_report, indent=2), encoding="utf-8")

        script_parts = split_messages(script_message())
        for part in script_parts:
            send_message(token, chat_id, part)
        script_report = {"sent": True, "chat_id": chat_id, "parts": len(script_parts), "message_type": "sendMessage"}
        (OUTPUT / "telegram_script_delivery_report.json").write_text(json.dumps(script_report, indent=2), encoding="utf-8")

        send_message(token, chat_id, production_summary())
        zip_path = create_production_package_zip()
        send_document(token, chat_id, zip_path, "INSIGHT FOOTBALL production package ZIP")
        full_report = {"sent": True, "chat_id": chat_id, "video_attached": True, "script_sent": True, "zip_sent": True, "zip_path": str(zip_path)}
        (OUTPUT / "full-production-delivery-report.json").write_text(json.dumps(full_report, indent=2), encoding="utf-8")
        print(json.dumps(full_report, indent=2))
    except RuntimeError as exc:
        print(json.dumps({"sent": False, "reason": "telegram_api_error", "error": str(exc), "chat_id": chat_id, "video_attached": bool(video_path)}, indent=2))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
