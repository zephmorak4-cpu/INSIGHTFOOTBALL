from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .ai_editor import create_content_package
from .asset_resolver import resolve_assets
from .creatomate_renderer import render_video
from .errors import MVPError
from .io_utils import OUTPUT, ROOT, read_json, write_json
from .match_data_fetcher import fetch_match_data
from .qc import run_qc
from .telegram_delivery import deliver, write_narration_script


REQUIRED_INPUT = ["production_id", "match", "home_team", "away_team", "competition", "stage", "kickoff_time", "selected_by", "audio_mode"]


def load_manual_input(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise MVPError("MANUAL_MATCH_INPUT_MISSING", f"Manual match input not found: {path}")
    payload = read_json(path)
    missing = [key for key in REQUIRED_INPUT if not payload.get(key)]
    if missing:
        raise MVPError("MANUAL_MATCH_INPUT_INVALID", "manual_match_input.json is missing required fields.", {"missing": missing})
    if payload["selected_by"] != "human_editor":
        raise MVPError("HUMAN_SELECTION_REQUIRED", "No automatic match selection is allowed in Simple MVP.")
    if payload["audio_mode"] != "silent_capcut":
        raise MVPError("SILENT_CAPCUT_REQUIRED", "Simple MVP requires audio_mode=silent_capcut.")
    return payload


def run(input_path: Path) -> dict[str, Any]:
    selection = load_manual_input(input_path)
    match_data = fetch_match_data(selection)
    write_json(OUTPUT / "match_data.json", match_data)
    content = create_content_package(selection, match_data)
    write_json(OUTPUT / "content_package.json", content)
    assets = resolve_assets(selection)
    write_json(OUTPUT / "resolved_assets.json", assets)
    render = render_video(selection, content, assets)
    write_json(OUTPUT / "render_result.json", render)
    script_path = write_narration_script(selection, content)
    telegram = deliver(selection, content, render)
    qc = run_qc(selection, content, assets, render, telegram)
    report = {"success": qc["status"] == "PASS", "selection": selection, "sources": match_data["sources"], "content_package": str(OUTPUT / "content_package.json"), "narration_script": str(script_path), "render": render, "telegram": telegram, "qc": qc}
    write_json(OUTPUT / "mvp_production_report.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the simple INSIGHT FOOTBALL MVP production flow.")
    parser.add_argument("--input", default="simple_mvp/manual_match_input.json")
    args = parser.parse_args()
    try:
        report = run((ROOT / args.input).resolve() if not Path(args.input).is_absolute() else Path(args.input))
    except MVPError as exc:
        payload = exc.to_dict()
        write_json(OUTPUT / "mvp_production_report.json", payload)
        print(json.dumps(payload, indent=2))
        return 1
    except Exception as exc:
        payload = {"success": False, "error": {"code": "MVP_UNEXPECTED_ERROR", "message": str(exc)}}
        write_json(OUTPUT / "mvp_production_report.json", payload)
        print(json.dumps(payload, indent=2))
        return 1
    print(json.dumps(report, indent=2))
    return 0 if report["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
