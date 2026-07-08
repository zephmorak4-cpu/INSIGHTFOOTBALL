from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import load_config
from .service import DashboardComposerService


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Dashboard Composer")
    parser.add_argument("--config", required=True)
    parser.add_argument("--storyboard-package", required=True)
    parser.add_argument("--visual-plan", required=True)
    parser.add_argument("--camera-plan", required=True)
    parser.add_argument("--motion-plan", required=True)
    parser.add_argument("--caption-plan", required=True)
    args = parser.parse_args()
    result = DashboardComposerService(load_config(Path(args.config))).run_from_files(Path(args.storyboard_package), Path(args.visual_plan), Path(args.camera_plan), Path(args.motion_plan), Path(args.caption_plan))
    print(json.dumps({k: v for k, v in result.items() if k not in {"dashboard_plan", "visual_production_package"}}, indent=2))
    return 0 if result.get("success") else 1


if __name__ == "__main__":
    raise SystemExit(main())

