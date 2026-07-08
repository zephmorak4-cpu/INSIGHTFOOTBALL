from __future__ import annotations

import argparse
import json
from pathlib import Path

from media_asset_engine.core import asset_cache_manager
from media_asset_engine.io import load_json


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Asset Cache Manager")
    parser.add_argument("--inputs", nargs="+", required=True)
    args = parser.parse_args()
    result = asset_cache_manager([load_json(Path(path)) for path in args.inputs])
    print(json.dumps({"success": True, "output": "editorial-brain/output/asset_cache_index.json", "entries": len(result["cache_entries"])}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
