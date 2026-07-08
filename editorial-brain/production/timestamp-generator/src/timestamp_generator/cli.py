from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import load_config
from .service import TimestampGeneratorService


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Timestamp Generator")
    parser.add_argument("--config", required=True)
    parser.add_argument("--voice-plan", required=True)
    parser.add_argument("--ssml-metadata", required=True)
    args = parser.parse_args()
    result = TimestampGeneratorService(load_config(Path(args.config))).run_from_files(Path(args.voice_plan), Path(args.ssml_metadata))
    print(json.dumps({k: v for k, v in result.items() if k != "voice_timestamps"}, indent=2))
    return 0 if result.get("success") else 1


if __name__ == "__main__":
    raise SystemExit(main())
