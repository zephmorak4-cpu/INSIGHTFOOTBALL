from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python scripts/inspect_run.py RUN_ID")
        return 1
    run_dir = ROOT / "data" / "runs" / sys.argv[1]
    if not run_dir.exists():
        print("Run not found.")
        return 1
    for name in ["request.json", "fixture.json", "validation.json", "probabilities.json", "final_output.json", "errors.log"]:
        path = run_dir / name
        if path.exists():
            print(f"\n== {name} ==")
            print(path.read_text(encoding="utf-8")[:2000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
