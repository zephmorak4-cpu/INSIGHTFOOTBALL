"""Storyboard Generator service."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .adapter import build_storyboard
from .config import StoryboardGeneratorConfig
from .errors import ValidationError
from .json_utils import load_json_file, load_text_file, write_json_file
from .logging_utils import StructuredLogger
from .prompt_loader import PromptLoader
from .validation import StoryboardValidator


class StoryboardGeneratorService:
    def __init__(self, config: StoryboardGeneratorConfig):
        self.config = config
        self.prompt_loader = PromptLoader(config.prompt_path)
        self.validator = StoryboardValidator(config.script_package_schema, config.output_schema)

    def run_from_files(self, script_package_path: Path, voiceover_path: Path) -> dict[str, Any]:
        return self.run(load_json_file(script_package_path), load_text_file(voiceover_path))

    def run(self, package: dict[str, Any], voiceover: str) -> dict[str, Any]:
        package = dict(package)
        if "final_voiceover" not in package and "full_voiceover" in package:
            package["final_voiceover"] = package["full_voiceover"]
        production_id = package.get("production_id", "unknown-production")
        logger = StructuredLogger(self.config.log_directory, f"storyboard-generator-{production_id}")
        try:
            self.validator.validate_inputs(package, voiceover)
            self.prompt_loader.load()
            storyboard = build_storyboard(package, voiceover, self.config)
            self.validator.validate_output(storyboard, package)
        except ValidationError as exc:
            logger.log({"event": "storyboard_generation_failed", "issues": exc.issues})
            return self._error(production_id, exc.issues)
        output_path = self.config.output_directory / "storyboard_draft.json"
        write_json_file(output_path, storyboard)
        logger.log({"event": "storyboard_draft_written", "output_path": str(output_path), "scene_count": storyboard["scene_count"]})
        return {"success": True, "storyboard": storyboard, "storyboard_path": str(output_path)}

    @staticmethod
    def _error(production_id: str, issues: list[str]) -> dict[str, Any]:
        return {"success": False, "agent_id": "IF-A06", "agent_name": "Storyboard Generator", "production_id": production_id, "error": {"code": "STORYBOARD_GENERATION_FAILED", "issues": issues}, "approval_status": "blocked", "next_component": None}
