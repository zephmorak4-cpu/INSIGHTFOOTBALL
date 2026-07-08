from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import load_config
from .service import PronunciationEngineService


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Pronunciation Engine")
    parser.add_argument("--config", required=True)
    parser.add_argument("--script-package", required=True)
    parser.add_argument("--voice-plan", required=True)
    args = parser.parse_args()
    result = PronunciationEngineService(load_config(Path(args.config))).run_from_files(Path(args.script_package), Path(args.voice_plan))
    print(json.dumps({k: v for k, v in result.items() if k != "pronunciation_dictionary"}, indent=2))
    return 0 if result.get("success") else 1


if __name__ == "__main__":
    raise SystemExit(main())
