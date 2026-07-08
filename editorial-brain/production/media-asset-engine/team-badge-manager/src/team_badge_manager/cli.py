from __future__ import annotations

import argparse
import json
from pathlib import Path

from media_asset_engine.core import team_badge_manager
from media_asset_engine.io import load_json


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Team Badge Manager")
    parser.add_argument("--asset-package", required=True)
    parser.add_argument("--library-status", required=True)
    args = parser.parse_args()
    result = team_badge_manager(load_json(Path(args.asset_package)), load_json(Path(args.library_status)))
    print(json.dumps({"success": True, "output": "editorial-brain/output/team_badge_assets.json", "fallbacks": len(result["fallback_badges"])}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
