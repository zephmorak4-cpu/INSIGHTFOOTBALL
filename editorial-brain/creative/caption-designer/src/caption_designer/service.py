from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import CaptionDesignerConfig
from .json_utils import load_json_file, write_json_file
from .logging_utils import StructuredLogger
from .validation import CaptionDesignerValidator


KEY_WORDS = ["Liverpool", "Arsenal", "edge", "pressure", "x-factor", "survive", "first"]


class CaptionDesignerService:
    def __init__(self, config: CaptionDesignerConfig):
        self.config = config
        self.validator = CaptionDesignerValidator(config.max_words_per_line, config.max_lines)

    def run_from_file(self, visual_plan_path: Path) -> dict[str, Any]:
        return self.run(load_json_file(visual_plan_path))

    def run(self, visual_plan: dict[str, Any]) -> dict[str, Any]:
        production_id = visual_plan.get("production_id", "unknown-production")
        logger = StructuredLogger(self.config.log_directory, f"caption-designer-{production_id}")
        issues = self.validator.validate_input(visual_plan)
        scenes = []
        for scene in visual_plan.get("scenes", []):
            caption = _summarize(scene.get("primary_text") or scene.get("secondary_text") or scene["scene_type"], self.config.max_words_per_line, self.config.max_lines)
            lines = caption.split("\n")
            if len(lines) > self.config.max_lines or any(len(line.split()) > self.config.max_words_per_line for line in lines):
                issues.append(f"{scene['scene_id']}: caption line length invalid")
            scenes.append({
                "scene_id": scene["scene_id"],
                "caption": caption,
                "caption_position": "lower_third_safe",
                "font_size": 54 if scene["scene_type"] in {"Central Question", "Final Question / CTA"} else 46,
                "font_weight": "bold" if scene["scene_type"] in {"Central Question", "Insight Dashboard"} else "semibold",
                "highlight_words": [word for word in KEY_WORDS if word.lower() in caption.lower()],
                "background_style": "dark_translucent_strip",
                "timing": {"start_offset": 0.2, "end_offset": -0.2},
                "safe_area_notes": "Lower third, inside center 80%, never over team badge or dashboard values.",
            })
        plan = {
            "production_id": visual_plan.get("production_id", ""),
            "component_id": self.config.component_id,
            "component_name": self.config.component_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source_visual_plan": visual_plan.get("production_id", ""),
            "scenes": scenes,
            "warnings": [],
            "approval_status": "approved" if not issues else "blocked",
            "next_component": self.config.next_component,
        }
        issues.extend(self.validator.validate_output(plan))
        if issues:
            logger.log({"event": "caption_design_failed", "issues": issues})
            return {"success": False, "error": {"code": "CAPTION_DESIGN_FAILED", "issues": issues}, "caption_plan": plan}
        path = self.config.output_directory / "caption_plan.json"
        write_json_file(path, plan)
        logger.log({"event": "caption_plan_written", "output_path": str(path)})
        return {"success": True, "caption_plan": plan, "caption_plan_path": str(path)}


def _summarize(text: str, max_words: int, max_lines: int) -> str:
    words = str(text).replace("...", "").split()
    words = words[: max_words * max_lines]
    lines = [" ".join(words[i:i + max_words]) for i in range(0, len(words), max_words)]
    return "\n".join(lines[:max_lines])
