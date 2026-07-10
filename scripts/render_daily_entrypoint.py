from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    """Production entrypoint for the Simple MVP.

    The legacy multi-agent production chain is intentionally disabled. Production now runs only
    a human-selected match through `simple_mvp.run_production`.
    """
    manual_input = os.environ.get("MANUAL_MATCH_INPUT_PATH", "simple_mvp/manual_match_input.json")
    return subprocess.run([sys.executable, "-m", "simple_mvp.run_production", "--input", manual_input], cwd=ROOT).returncode


if __name__ == "__main__":
    raise SystemExit(main())
