"""Command-line runner for the Editorial Orchestrator."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import load_config
from .json_utils import load_json_file
from .service import EditorialOrchestrator


def main() -> int:
    parser = argparse.ArgumentParser(description="Run INSIGHT FOOTBALL Editorial Orchestrator")
    parser.add_argument("--daily-input", required=True, help="Path to Daily Input JSON")
    parser.add_argument("--config", required=True, help="Path to orchestrator config JSON")
    args = parser.parse_args()

    config = load_config(Path(args.config))
    daily_input = load_json_file(Path(args.daily_input))
    result = EditorialOrchestrator(config).run(daily_input)
    print(json.dumps({key: value for key, value in result.items() if key != "package"}, indent=2, ensure_ascii=True))
    return 0 if result.get("success") else 1


if __name__ == "__main__":
    raise SystemExit(main())
