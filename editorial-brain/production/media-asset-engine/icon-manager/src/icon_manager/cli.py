from __future__ import annotations

import argparse
import json
from pathlib import Path

from media_asset_engine.core import icon_manager
from media_asset_engine.io import load_json


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Icon Manager")
    parser.add_argument("--asset-package", required=True)
    parser.add_argument("--visual-package", required=True)
    parser.add_argument("--library-status", required=True)
    args = parser.parse_args()
    result = icon_manager(load_json(Path(args.asset_package)), load_json(Path(args.visual_package)), load_json(Path(args.library_status)))
    print(json.dumps({"success": True, "output": "editorial-brain/output/icon_assets.json", "missing_icons": len(result["missing_icons"])}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
