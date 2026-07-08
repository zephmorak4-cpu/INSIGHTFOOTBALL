from __future__ import annotations

import argparse
import json
from pathlib import Path

from media_asset_engine.core import asset_library_manager
from media_asset_engine.io import load_json


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Asset Library Manager")
    parser.add_argument("--asset-package", required=True)
    args = parser.parse_args()
    result = asset_library_manager(load_json(Path(args.asset_package)))
    print(json.dumps({"success": True, "output": "editorial-brain/output/asset_library_status.json", "approval_status": result["approval_status"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
