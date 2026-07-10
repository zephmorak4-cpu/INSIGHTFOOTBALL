from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "editorial-brain" / "output"
LOG_PATH = OUTPUT / "creatomate_webhook_log.jsonl"


def handle_creatomate_webhook(payload: dict[str, Any]) -> dict[str, Any]:
    render_id = str(payload.get("id") or payload.get("render_id") or "")
    status = str(payload.get("status") or payload.get("state") or "").lower()
    metadata = payload.get("metadata", {}) if isinstance(payload.get("metadata"), dict) else {}
    production_id = str(metadata.get("production_id") or payload.get("production_id") or "")
    output_url = str(payload.get("url") or payload.get("output_url") or payload.get("outputUrl") or "")
    if not render_id or not status or not production_id:
        result = {"success": False, "error": "INVALID_CREATOMATE_WEBHOOK_PAYLOAD", "render_id": render_id, "production_id": production_id}
        _write_event(payload, result)
        return result

    existing = _processed_ids()
    duplicate = render_id in existing
    result = {"success": True, "render_id": render_id, "production_id": production_id, "status": _normalize_status(status), "output_url": output_url, "duplicate": duplicate}
    _write_event(payload, result)
    return result


def _normalize_status(status: str) -> str:
    return {"done": "succeeded", "completed": "succeeded", "success": "succeeded", "processing": "rendering"}.get(status, status)


def _processed_ids() -> set[str]:
    if not LOG_PATH.exists():
        return set()
    ids = set()
    for line in LOG_PATH.read_text(encoding="utf-8").splitlines():
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        render_id = item.get("result", {}).get("render_id")
        if render_id:
            ids.add(str(render_id))
    return ids


def _write_event(payload: dict[str, Any], result: dict[str, Any]) -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    event = {"payload": payload, "result": result}
    (OUTPUT / "creatomate_webhook_event.json").write_text(json.dumps(event, indent=2), encoding="utf-8")
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")


if __name__ == "__main__":
    import sys

    data = json.loads(sys.stdin.read() or "{}")
    print(json.dumps(handle_creatomate_webhook(data), indent=2))
