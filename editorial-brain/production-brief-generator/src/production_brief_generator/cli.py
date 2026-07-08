"""CLI runner for Production Brief Generator."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import load_config
from .service import ProductionBriefGeneratorService


def main() -> int:
    parser = argparse.ArgumentParser(description="Run INSIGHT FOOTBALL Production Brief Generator")
    parser.add_argument("--config", required=True)
    parser.add_argument("--validated-package", required=True)
    args = parser.parse_args()
    result = ProductionBriefGeneratorService(load_config(Path(args.config))).run_from_file(Path(args.validated_package))
    print(json.dumps({k: v for k, v in result.items() if k != "brief"}, indent=2, ensure_ascii=True))
    return 0 if result.get("success") else 1


if __name__ == "__main__":
    raise SystemExit(main())
