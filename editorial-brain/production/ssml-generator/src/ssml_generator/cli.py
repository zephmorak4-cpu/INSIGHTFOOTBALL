from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import load_config
from .service import SSMLGeneratorService


def main() -> int:
    parser = argparse.ArgumentParser(description="Run SSML Generator")
    parser.add_argument("--config", required=True)
    parser.add_argument("--script-package", required=True)
    parser.add_argument("--voice-plan", required=True)
    parser.add_argument("--pronunciation-dictionary", required=True)
    args = parser.parse_args()
    result = SSMLGeneratorService(load_config(Path(args.config))).run_from_files(Path(args.script_package), Path(args.voice_plan), Path(args.pronunciation_dictionary))
    print(json.dumps({k: v for k, v in result.items() if k != "ssml"}, indent=2))
    return 0 if result.get("success") else 1


if __name__ == "__main__":
    raise SystemExit(main())
