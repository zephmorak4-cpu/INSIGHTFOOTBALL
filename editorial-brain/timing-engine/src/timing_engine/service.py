"""Timing Engine service."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .config import TimingEngineConfig
from .errors import ValidationError
from .json_utils import load_json_file, load_text_file, write_json_file
from .logging_utils import StructuredLogger
from .timeline import build_final_package, build_timeline
from .validation import TimingEngineValidator


class TimingEngineService:
    def __init__(self, config: TimingEngineConfig):
        self.config = config
        self.validator = TimingEngineValidator(config.input_schema, config.timeline_schema, config.final_package_schema, config.max_duration_seconds)

    def run_from_files(self, scene_list_path: Path, voiceover_path: Path) -> dict[str, Any]:
        return self.run(load_json_file(scene_list_path), load_text_file(voiceover_path))

    def run(self, scene_list: dict[str, Any], voiceover: str) -> dict[str, Any]:
        production_id = scene_list.get("production_id", "unknown-production")
        logger = StructuredLogger(self.config.log_directory, f"timing-engine-{production_id}")
        try:
            self.validator.validate_input(scene_list, voiceover)
            timeline = build_timeline(scene_list, self.config)
            self.validator.validate_timeline(timeline)
            final_package = build_final_package(scene_list, timeline, voiceover, self.config)
            self.validator.validate_final_package(final_package)
        except ValidationError as exc:
            logger.log({"event": "timing_engine_failed", "issues": exc.issues})
            return {"success": False, "component_id": self.config.component_id, "component_name": self.config.component_name, "production_id": production_id, "error": {"code": "TIMING_ENGINE_FAILED", "issues": exc.issues}, "approval_status": "blocked"}
        timeline_path = self.config.output_directory / "timeline.json"
        package_path = self.config.output_directory / "final-storyboard-package.json"
        write_json_file(timeline_path, timeline)
        write_json_file(package_path, final_package)
        logger.log({"event": "timing_engine_completed", "timeline_path": str(timeline_path), "final_package_path": str(package_path)})
        return {"success": True, "timeline": timeline, "final_package": final_package, "timeline_path": str(timeline_path), "final_package_path": str(package_path)}

