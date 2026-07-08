"""Scene Planner CLI."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import load_config
from .service import ScenePlannerService


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Scene Planner")
    parser.add_argument("--config", required=True)
    parser.add_argument("--storyboard", required=True)
    parser.add_argument("--script-package", required=True)
    args = parser.parse_args()
    result = ScenePlannerService(load_config(Path(args.config))).run_from_files(Path(args.storyboard), Path(args.script_package))
    print(json.dumps({k: v for k, v in result.items() if k != "scene_list"}, indent=2))
    return 0 if result.get("success") else 1


if __name__ == "__main__":
    raise SystemExit(main())

