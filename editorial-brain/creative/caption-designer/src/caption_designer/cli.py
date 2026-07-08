from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import load_config
from .service import CaptionDesignerService


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Caption Designer")
    parser.add_argument("--config", required=True)
    parser.add_argument("--visual-plan", required=True)
    args = parser.parse_args()
    result = CaptionDesignerService(load_config(Path(args.config))).run_from_file(Path(args.visual_plan))
    print(json.dumps({k: v for k, v in result.items() if k != "caption_plan"}, indent=2))
    return 0 if result.get("success") else 1


if __name__ == "__main__":
    raise SystemExit(main())

