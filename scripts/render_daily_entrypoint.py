from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]


def run(command: list[str]) -> int:
    process = subprocess.run(command, cwd=ROOT)
    return process.returncode


def main() -> int:
    daily_input = os.environ.get("DAILY_INPUT_PATH", "editorial-brain/examples/liverpool-arsenal-daily-input.json")
    run_tests = os.environ.get("INSIGHT_FOOTBALL_RUN_TESTS_ON_RENDER", "true").lower() == "true"
    production = os.environ.get("INSIGHT_FOOTBALL_ENV", "").lower() == "production"
    sample_allowed = os.environ.get("INSIGHT_FOOTBALL_ALLOW_SAMPLE_DAILY_INPUT", "").lower() == "true"

    if run_tests:
        tests_status = run([sys.executable, "scripts/run_tests.py"])
        if tests_status != 0:
            return tests_status

    if production and "examples" in daily_input.replace("\\", "/") and not sample_allowed:
        live_path = "editorial-brain/output/live-daily-input.json"
        today = datetime.now(ZoneInfo("Africa/Lagos")).date().isoformat()
        live_status = run([sys.executable, "scripts/live_daily_input_builder.py", "--date", today, "--output", live_path])
        if live_status != 0:
            return live_status
        daily_input = live_path

    production_status = run([sys.executable, "scripts/run_daily_dry_run.py", "--daily-input", daily_input])
    if production_status != 0:
        return production_status

    run_url = os.environ.get("RENDER_RUN_URL", "")
    return run([sys.executable, "scripts/send_telegram_approval.py", "--run-url", run_url])


if __name__ == "__main__":
    raise SystemExit(main())
