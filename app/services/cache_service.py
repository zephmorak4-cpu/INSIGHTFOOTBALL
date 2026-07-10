from __future__ import annotations

from pathlib import Path


class CacheService:
    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
