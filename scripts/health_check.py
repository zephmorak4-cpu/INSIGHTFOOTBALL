from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config.settings import load_settings
from app.telegram.handlers import command_response


def main() -> int:
    print(command_response("/health", load_settings()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
