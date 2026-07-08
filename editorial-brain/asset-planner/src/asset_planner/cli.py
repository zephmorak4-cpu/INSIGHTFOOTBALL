"""Asset Planner CLI."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import load_config
from .service import AssetPlannerService


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Asset Planner")
    parser.add_argument("--config", required=True)
    parser.add_argument("--storyboard-package", required=True)
    args = parser.parse_args()
    result = AssetPlannerService(load_config(Path(args.config))).run_from_file(Path(args.storyboard_package))
    print(json.dumps({k: v for k, v in result.items() if k != "asset_manifest"}, indent=2))
    return 0 if result.get("success") else 1


if __name__ == "__main__":
    raise SystemExit(main())

