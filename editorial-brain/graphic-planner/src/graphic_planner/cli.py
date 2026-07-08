from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import load_config
from .service import GraphicPlannerService


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Graphic Planner")
    parser.add_argument("--config", required=True)
    parser.add_argument("--storyboard-package", required=True)
    parser.add_argument("--asset-manifest", required=True)
    parser.add_argument("--asset-search-plan", required=True)
    args = parser.parse_args()
    result = GraphicPlannerService(load_config(Path(args.config))).run_from_files(Path(args.storyboard_package), Path(args.asset_manifest), Path(args.asset_search_plan))
    print(json.dumps({k: v for k, v in result.items() if k not in {"graphic_requirements", "final_asset_package"}}, indent=2))
    return 0 if result.get("success") else 1


if __name__ == "__main__":
    raise SystemExit(main())

