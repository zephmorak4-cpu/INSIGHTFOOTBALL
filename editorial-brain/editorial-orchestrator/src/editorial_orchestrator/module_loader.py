"""Imports the four Editorial Brain modules without changing their packages."""

from __future__ import annotations

import sys
from pathlib import Path


def ensure_editorial_module_paths(workspace_root: Path) -> None:
    paths = [
        workspace_root / "editorial-brain" / "match-selector" / "src",
        workspace_root / "editorial-brain" / "story-hunter" / "src",
        workspace_root / "editorial-brain" / "evidence-filter" / "src",
        workspace_root / "editorial-brain" / "insight-engine" / "src",
    ]
    for path in reversed(paths):
        value = str(path)
        if value not in sys.path:
            sys.path.insert(0, value)
