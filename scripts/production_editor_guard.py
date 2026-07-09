from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "editorial-brain" / "output"
BLOCKED_SELECTED_BY = {"automatic", "automatic_recommendation", "system", "match_selector"}
EDITOR_SELECTION_REQUIRED = {
    "code": "EDITOR_SELECTION_REQUIRED",
    "message": "No editor-selected match was provided. Production cannot continue. Please choose the match manually.",
}
PRODUCTION_REQUIRES_HUMAN = {
    "code": "PRODUCTION_REQUIRES_HUMAN_EDITOR_SELECTION",
    "message": "Production requires selected_by to be human_editor.",
}


def production_mode() -> bool:
    return os.environ.get("INSIGHT_FOOTBALL_ENV", "").lower() == "production"


def require_editor_selection_path() -> Path:
    path = os.environ.get("EDITOR_SELECTION_PATH", "").strip()
    if not path:
        raise RuntimeError(json.dumps(EDITOR_SELECTION_REQUIRED))
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = ROOT / candidate
    if not candidate.exists():
        raise RuntimeError(json.dumps(EDITOR_SELECTION_REQUIRED))
    return candidate


def load_valid_editor_selection(path: Path | None = None) -> dict[str, Any]:
    module_path = ROOT / "editorial-brain" / "editor-match-selector" / "src"
    if str(module_path) not in sys.path:
        sys.path.insert(0, str(module_path))
    from editor_match_selector import load_editor_selection

    selection_path = path or require_editor_selection_path()
    try:
        selection = load_editor_selection(selection_path)
    except ValueError as exc:
        message = str(exc)
        if "PRODUCTION_REQUIRES_HUMAN_EDITOR_SELECTION" in message:
            raise RuntimeError(json.dumps(PRODUCTION_REQUIRES_HUMAN)) from exc
        raise RuntimeError(json.dumps({"code": "EDITOR_SELECTION_INVALID", "message": message})) from exc
    if selection.get("selected_by") in BLOCKED_SELECTED_BY:
        raise RuntimeError(json.dumps(PRODUCTION_REQUIRES_HUMAN))
    if selection.get("selected_by") != "human_editor":
        raise RuntimeError(json.dumps(PRODUCTION_REQUIRES_HUMAN))
    return selection


def guard_production_editor_selection() -> dict[str, Any] | None:
    if not production_mode():
        return None
    return load_valid_editor_selection()


def structured_error(exc: RuntimeError) -> dict[str, Any]:
    try:
        payload = json.loads(str(exc))
    except json.JSONDecodeError:
        payload = {"code": "EDITOR_SELECTION_INVALID", "message": str(exc)}
    return {"success": False, "error": payload}


def write_blocked_report(error: dict[str, Any]) -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    report = {
        "run_type": "daily_dry_run",
        "success": False,
        "approval_required": True,
        "live_publishing_performed": False,
        "error": error["error"],
        "steps": [],
        "next_gate": "Editor must provide editor_selection.json before production can run.",
    }
    (OUTPUT / "daily-run-report.json").write_text(json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
