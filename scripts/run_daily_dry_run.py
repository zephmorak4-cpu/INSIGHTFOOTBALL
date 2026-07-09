from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from production_editor_guard import guard_production_editor_selection, structured_error, write_blocked_report


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "editorial-brain" / "output"


def run_step(name: str, command: list[str], pythonpath: list[Path]) -> dict[str, object]:
    env = os.environ.copy()
    existing = env.get("PYTHONPATH")
    parts = [str(path) for path in pythonpath]
    if existing:
        parts.append(existing)
    env["PYTHONPATH"] = os.pathsep.join(parts)

    started = datetime.now(timezone.utc)
    process = subprocess.run(command, cwd=ROOT, env=env, text=True, capture_output=True)
    finished = datetime.now(timezone.utc)
    return {
        "name": name,
        "command": command,
        "started_at": started.isoformat(),
        "finished_at": finished.isoformat(),
        "return_code": process.returncode,
        "stdout": process.stdout.strip(),
        "stderr": process.stderr.strip(),
        "success": process.returncode == 0,
    }


def load_json(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def apply_editor_selection_if_present(daily_input_path: str) -> str:
    editor_path = os.environ.get("EDITOR_SELECTION_PATH")
    if not editor_path:
        return daily_input_path
    module_path = ROOT / "editorial-brain" / "editor-match-selector" / "src"
    if str(module_path) not in sys.path:
        sys.path.insert(0, str(module_path))
    from editor_match_selector import apply_editor_selection, load_editor_selection

    daily_input = load_json(ROOT / daily_input_path)
    updated = apply_editor_selection(daily_input, load_editor_selection(Path(editor_path)))
    output = OUTPUT / "editor-selected-daily-input.json"
    OUTPUT.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(updated, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    return str(output.relative_to(ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(description="Run INSIGHT FOOTBALL daily dry-run production flow.")
    parser.add_argument(
        "--daily-input",
        default="editorial-brain/examples/liverpool-arsenal-daily-input.json",
        help="Daily Input JSON used by the editorial orchestrator.",
    )
    args = parser.parse_args()
    if os.environ.get("INSIGHT_FOOTBALL_ENV", "").lower() == "production":
        try:
            guard_production_editor_selection()
        except RuntimeError as exc:
            error = structured_error(exc)
            write_blocked_report(error)
            print(json.dumps(error, indent=2))
            return 1
    args.daily_input = apply_editor_selection_if_present(args.daily_input)
    if os.environ.get("INSIGHT_FOOTBALL_ENV", "").lower() == "production":
        normalized_input = args.daily_input.replace("\\", "/")
        if "examples/" in normalized_input and os.environ.get("INSIGHT_FOOTBALL_ALLOW_SAMPLE_DAILY_INPUT", "").lower() != "true":
            print(json.dumps({"success": False, "error": "Production runs cannot use example Daily Input files."}, indent=2))
            return 1

    python = sys.executable
    render_command = [
        python,
        "-m",
        "render_validator.cli",
        "--renderer-profile",
        os.environ.get("INSIGHT_FOOTBALL_RENDERER_PROFILE", "placeholder"),
    ]
    if os.environ.get("INSIGHT_FOOTBALL_DRY_RUN", "true").lower() == "false":
        render_command.append("--live")

    step_plan = [
        (
            "editorial_orchestrator",
            [
                python,
                "-m",
                "editorial_orchestrator.cli",
                "--config",
                "editorial-brain/editorial-orchestrator/config/editorial-orchestrator.config.json",
                "--daily-input",
                args.daily_input,
            ],
            [ROOT / "editorial-brain" / "editorial-orchestrator" / "src"],
        ),
        (
            "rendering_engine",
            render_command,
            [
                ROOT / "editorial-brain" / "production" / "rendering-engine" / "shared",
                ROOT / "editorial-brain" / "production" / "rendering-engine" / "render-validator" / "src",
            ],
        ),
        (
            "publish_readiness_gate",
            [python, "-m", "publish_readiness_gate.cli"],
            [
                ROOT / "editorial-brain" / "production" / "final-quality-control" / "shared",
                ROOT / "editorial-brain" / "production" / "final-quality-control" / "publish-readiness-gate" / "src",
            ],
        ),
        (
            "publishing_dry_run",
            [python, "-m", "publishing_report_generator.cli"],
            [
                ROOT / "distribution" / "publishing-engine" / "shared",
                ROOT / "distribution" / "publishing-engine" / "publishing-report-generator" / "src",
            ],
        ),
        (
            "analytics_learning",
            [python, "-m", "daily_performance_reporter.cli"],
            [
                ROOT / "analytics" / "shared",
                ROOT / "analytics" / "daily-performance-reporter" / "src",
            ],
        ),
    ]
    steps = []
    for name, command, pythonpath in step_plan:
        step = run_step(name, command, pythonpath)
        steps.append(step)
        if not step["success"]:
            break

    success = all(step["success"] for step in steps)
    publish_readiness = load_json(OUTPUT / "publish_readiness_report.json")
    publishing_report = load_json(OUTPUT / "publishing_report.json")
    learning_package = load_json(OUTPUT / "learning-package.json")

    report = {
        "run_type": "daily_dry_run",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "daily_input": args.daily_input,
        "success": success,
        "approval_required": True,
        "live_publishing_performed": False,
        "steps": steps,
        "publish_readiness": {
            "final_status": publish_readiness.get("final_status"),
            "overall_score": publish_readiness.get("overall_score"),
            "human_review_required": publish_readiness.get("human_review_required"),
            "warnings": publish_readiness.get("warnings", []),
        },
        "publishing": {
            "final_status": publishing_report.get("final_status"),
            "dry_run": publishing_report.get("dry_run", True),
            "warnings": publishing_report.get("warnings", []),
        },
        "learning": {
            "approval_status": learning_package.get("approval_status"),
            "recommendation_count": len(learning_package.get("recommendations", {}).get("recommendations", []))
            if learning_package
            else 0,
        },
        "next_gate": "Telegram human approval before production publishing.",
    }

    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "daily-run-report.json").write_text(json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    print(json.dumps({"success": success, "output": "editorial-brain/output/daily-run-report.json"}, indent=2))
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
