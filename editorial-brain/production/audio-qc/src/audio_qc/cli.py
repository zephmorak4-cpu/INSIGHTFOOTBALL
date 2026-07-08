from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import load_config
from .service import AudioQCService


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Audio Quality Control")
    parser.add_argument("--config", required=True)
    parser.add_argument("--voice-plan", required=True)
    parser.add_argument("--pronunciation-dictionary", required=True)
    parser.add_argument("--ssml", required=True)
    parser.add_argument("--ssml-metadata", required=True)
    parser.add_argument("--voice-timestamps", required=True)
    args = parser.parse_args()
    result = AudioQCService(load_config(Path(args.config))).run_from_files(Path(args.voice_plan), Path(args.pronunciation_dictionary), Path(args.ssml), Path(args.ssml_metadata), Path(args.voice_timestamps))
    print(json.dumps({k: v for k, v in result.items() if k != "voice_production_package"}, indent=2))
    return 0 if result.get("success") else 1


if __name__ == "__main__":
    raise SystemExit(main())
