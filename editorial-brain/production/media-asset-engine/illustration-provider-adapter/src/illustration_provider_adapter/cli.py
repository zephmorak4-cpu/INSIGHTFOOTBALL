from __future__ import annotations

import argparse
import json
from pathlib import Path

from media_asset_engine.core import illustration_provider_adapter
from media_asset_engine.io import load_json


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Illustration Provider Adapter")
    parser.add_argument("--search-plan", required=True)
    parser.add_argument("--graphic-requirements", required=True)
    parser.add_argument("--background-assets", required=True)
    parser.add_argument("--icon-assets", required=True)
    args = parser.parse_args()
    result = illustration_provider_adapter(load_json(Path(args.search_plan)), load_json(Path(args.graphic_requirements)), load_json(Path(args.background_assets)), load_json(Path(args.icon_assets)))
    print(json.dumps({"success": True, "outputs": ["editorial-brain/output/illustration_tasks.json", "editorial-brain/output/generated_placeholder_assets.json"], "tasks": len(result["illustration_tasks"]["generation_tasks"])}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
