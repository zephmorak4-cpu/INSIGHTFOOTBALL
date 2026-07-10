from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEST_ROOTS = ("tests",)


def discover_tests() -> list[str]:
    tests: list[str] = []
    for root_name in TEST_ROOTS:
        root = ROOT / root_name
        if root.exists():
            tests.extend(str(path.relative_to(ROOT)) for path in root.rglob("test_*.py"))
    return sorted(tests)


def main() -> int:
    tests = discover_tests()
    if not tests:
        print("No active MVP tests discovered.", file=sys.stderr)
        return 1
    print(f"Running {len(tests)} active MVP test files...")
    return subprocess.call([sys.executable, "-m", "unittest", *tests], cwd=ROOT)


if __name__ == "__main__":
    raise SystemExit(main())
