from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import load_config
from .service import VisualDirectorService


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Visual Director")
    parser.add_argument("--config", required=True)
    parser.add_argument("--storyboard-package", required=True)
    parser.add_argument("--asset-package", required=True)
    args = parser.parse_args()
    result = VisualDirectorService(load_config(Path(args.config))).run_from_files(Path(args.storyboard_package), Path(args.asset_package))
    print(json.dumps({k: v for k, v in result.items() if k != "visual_plan"}, indent=2))
    return 0 if result.get("success") else 1


if __name__ == "__main__":
    raise SystemExit(main())

