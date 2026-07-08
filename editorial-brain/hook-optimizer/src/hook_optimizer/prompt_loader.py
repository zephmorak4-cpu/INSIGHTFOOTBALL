"""Prompt loading."""

from pathlib import Path


class PromptLoader:
    def __init__(self, prompt_path: Path):
        self.prompt_path = prompt_path

    def load(self) -> str:
        return self.prompt_path.read_text(encoding="utf-8")

