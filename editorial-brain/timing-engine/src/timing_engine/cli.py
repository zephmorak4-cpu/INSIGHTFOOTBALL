"""Timing Engine CLI."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import load_config
from .service import TimingEngineService


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Timing Engine")
    parser.add_argument("--config", required=True)
    parser.add_argument("--scene-list", required=True)
    parser.add_argument("--voiceover", required=True)
    args = parser.parse_args()
    result = TimingEngineService(load_config(Path(args.config))).run_from_files(Path(args.scene_list), Path(args.voiceover))
    print(json.dumps({k: v for k, v in result.items() if k not in {"timeline", "final_package"}}, indent=2))
    return 0 if result.get("success") else 1


if __name__ == "__main__":
    raise SystemExit(main())

