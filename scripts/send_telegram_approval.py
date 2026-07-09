from __future__ import annotations

import argparse
import json
import mimetypes
import os
import urllib.parse
import urllib.request
import urllib.error
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "editorial-brain" / "output"


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
    video_status = "attached" if find_approval_video() else str(render.get("render_status", {}).get("status", "pending"))

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
        "INSIGHT FOOTBALL APPROVAL VIDEO",
        f"Production: {production_id}",
        f"Match: {match_name}",
        f"Readiness: {readiness.get('final_status', 'unknown')}",
        f"Score: {readiness.get('overall_score', 'unknown')}",
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
        if path.exists() and path.suffix.lower() == ".mp4":
            return path
    return None


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
        print(json.dumps({"sent": False, "reason": "dry_run_or_missing_telegram_secrets", "message": message, "video_attachment": str(video_path) if video_path else None}, indent=2))
        return 0

    try:
        if video_path:
            send_video(token, chat_id, video_path, compact_caption(args.run_url))
            send_message(token, chat_id, message)
            print(json.dumps({"sent": True, "chat_id": chat_id, "video_attached": True, "video_path": str(video_path)}, indent=2))
        else:
            send_message(token, chat_id, message)
            print(json.dumps({"sent": True, "chat_id": chat_id, "video_attached": False}, indent=2))
    except RuntimeError as exc:
        print(json.dumps({"sent": False, "reason": "telegram_api_error", "error": str(exc), "chat_id": chat_id, "video_attached": bool(video_path)}, indent=2))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
