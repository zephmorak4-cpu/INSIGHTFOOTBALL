from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import load_config
from .service import VoiceDirectorService


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Voice Director")
    parser.add_argument("--config", required=True)
    parser.add_argument("--script-package", required=True)
    args = parser.parse_args()
    result = VoiceDirectorService(load_config(Path(args.config))).run_from_file(Path(args.script_package))
    print(json.dumps({k: v for k, v in result.items() if k != "voice_plan"}, indent=2))
    return 0 if result.get("success") else 1


if __name__ == "__main__":
    raise SystemExit(main())
