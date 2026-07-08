"""Prompt loading from the frozen Prompt Library."""

from __future__ import annotations

from pathlib import Path

from .errors import PromptLoadError


class PromptLoader:
    """Loads the Evidence Filter prompt section from the official Prompt Library."""

    START = "## 7. Agent 3: Evidence Filter"
    END = "## 8. Agent 4: Insight Engine"

    def __init__(self, prompt_library_path: Path):
        self.prompt_library_path = prompt_library_path

    def load_evidence_filter_prompt(self) -> str:
        try:
            text = self.prompt_library_path.read_text(encoding="utf-8")
        except OSError as exc:
            raise PromptLoadError(f"Could not read prompt library: {self.prompt_library_path}") from exc

        start = text.find(self.START)
        end = text.find(self.END)
        if start == -1 or end == -1 or end <= start:
            raise PromptLoadError("Could not locate Evidence Filter prompt section in Prompt Library")
        return text[start:end].strip()

    @staticmethod
    def render(prompt: str, variables: dict[str, str]) -> str:
        rendered = prompt
        for key, value in variables.items():
            rendered = rendered.replace("{{" + key + "}}", value)
        return rendered
