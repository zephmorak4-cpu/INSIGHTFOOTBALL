"""Hook Optimizer CLI."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import load_config
from .json_utils import load_json_file
from .llm import RuleBasedHookOptimizerClient
from .service import HookOptimizerService


def main() -> int:
    parser = argparse.ArgumentParser(description="Run INSIGHT FOOTBALL Hook Optimizer")
    parser.add_argument("--config", required=True)
    parser.add_argument("--script", required=True)
    parser.add_argument("--brief", required=True)
    args = parser.parse_args()
    config = load_config(Path(args.config))
    script = load_json_file(Path(args.script))
    brief = load_json_file(Path(args.brief))
    result = HookOptimizerService(config, RuleBasedHookOptimizerClient(script, brief, config)).run(script, brief)
    print(json.dumps({k: v for k, v in result.items() if k not in {"optimization", "optimized_script"}}, indent=2))
    return 0 if result.get("success") else 1


if __name__ == "__main__":
    raise SystemExit(main())

