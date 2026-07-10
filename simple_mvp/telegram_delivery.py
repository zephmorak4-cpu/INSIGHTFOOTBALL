from __future__ import annotations

import json
import mimetypes
import os
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from .errors import MVPError
from .io_utils import OUTPUT, RENDERS, write_json


def write_narration_script(selection: dict[str, Any], content: dict[str, Any]) -> Path:
    script = str(content["full_script"]).strip()
    words = len(script.split())
    path = RENDERS / selection["production_id"] / "narration_script.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    scene_notes = "\n".join(f"- {scene.get('template_key')}: {scene.get('duration')}s - {scene.get('text')}" for scene in content.get("visual_scenes", []))
    path.write_text(f"INSIGHT FOOTBALL NARRATION SCRIPT\n\n{script}\n\nWord count: {words}\nEstimated narration duration: {round(words / 2.55)} seconds\n\nScene timing notes:\n{scene_notes}\n", encoding="utf-8")
    return path


def deliver(selection: dict[str, Any], content: dict[str, Any], render: dict[str, Any]) -> dict[str, Any]:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_APPROVAL_CHAT_ID") or os.environ.get("TELEGRAM_CHANNEL_ID", "")
    if not token or not chat_id:
        raise MVPError("TELEGRAM_CONFIG_REQUIRED", "Telegram token and approval chat ID are required.")
    video = Path(render["final_video_path"])
    if not video.exists() or video.suffix.lower() != ".mp4":
        raise MVPError("TELEGRAM_VIDEO_MISSING", "Telegram delivery requires a real MP4.")
    script_path = write_narration_script(selection, content)
    video_response = _send_file(token, chat_id, "sendVideo", "video", video, _video_caption(selection), {"supports_streaming": "true"})
    script_response = _send_text(token, chat_id, script_path.read_text(encoding="utf-8"))
    summary_response = _send_text(token, chat_id, _summary(selection, content, render))
    report = {
        "sent": True,
        "video_sent": True,
        "script_sent": True,
        "summary_sent": True,
        "video_message_id": _message_id(video_response),
        "script_message_id": _message_id(script_response),
        "summary_message_id": _message_id(summary_response),
        "script_path": str(script_path),
    }
    write_json(OUTPUT / "telegram_delivery_report.json", report)
    return report


def _video_caption(selection: dict[str, Any]) -> str:
    return "\n".join(["INSIGHT FOOTBALL PRODUCTION PREVIEW", "", f"Match: {selection['match']}", f"Competition: {selection['competition']}", f"Production: {selection['production_id']}", "Render: Creatomate complete", "Audio mode: silent, ready for CapCut", "", "Review the video, then check the full script below."])[:1024]


def _summary(selection: dict[str, Any], content: dict[str, Any], render: dict[str, Any]) -> str:
    return "\n".join(["INSIGHT FOOTBALL MVP SUMMARY", "", f"Match: {selection['match']}", f"Competition: {selection['competition']}", f"Central question: {content['central_question']}", f"Story: {content['main_story']}", f"Video duration: {render.get('duration_seconds', 'unknown')}", f"Render status: {render['render_status']}", "CapCut audio mode: silent_capcut"])


def _send_text(token: str, chat_id: str, text: str) -> dict[str, Any]:
    request = urllib.request.Request(f"https://api.telegram.org/bot{token}/sendMessage", data=urllib.parse.urlencode({"chat_id": chat_id, "text": text}).encode("utf-8"), method="POST")
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8", errors="replace"))


def _send_file(token: str, chat_id: str, method: str, field: str, path: Path, caption: str, extra: dict[str, str] | None = None) -> dict[str, Any]:
    boundary = "----InsightFootballMVP"
    fields = {"chat_id": chat_id, "caption": caption}
    fields.update(extra or {})
    chunks: list[bytes] = []
    for name, value in fields.items():
        chunks.extend([f"--{boundary}\r\n".encode(), f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode(), str(value).encode(), b"\r\n"])
    chunks.extend([f"--{boundary}\r\n".encode(), f'Content-Disposition: form-data; name="{field}"; filename="{path.name}"\r\n'.encode(), f"Content-Type: {mimetypes.guess_type(path.name)[0] or 'application/octet-stream'}\r\n\r\n".encode(), path.read_bytes(), b"\r\n", f"--{boundary}--\r\n".encode()])
    request = urllib.request.Request(f"https://api.telegram.org/bot{token}/{method}", data=b"".join(chunks), headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}, method="POST")
    with urllib.request.urlopen(request, timeout=120) as response:
        return json.loads(response.read().decode("utf-8", errors="replace"))


def _message_id(response: dict[str, Any]) -> int | None:
    result = response.get("result")
    return result.get("message_id") if isinstance(result, dict) else None
