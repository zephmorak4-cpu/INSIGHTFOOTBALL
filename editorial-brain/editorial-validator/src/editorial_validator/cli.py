"""CLI runner for Editorial Validator."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import load_config
from .service import EditorialValidatorService


def main() -> int:
    parser = argparse.ArgumentParser(description="Run INSIGHT FOOTBALL Editorial Validator")
    parser.add_argument("--config", required=True)
    parser.add_argument("--package", required=True)
    args = parser.parse_args()
    result = EditorialValidatorService(load_config(Path(args.config))).run_from_file(Path(args.package))
    print(json.dumps({k: v for k, v in result.items() if k != "validated_package"}, indent=2, ensure_ascii=True))
    return 0 if result.get("success") else 1


if __name__ == "__main__":
    raise SystemExit(main())
