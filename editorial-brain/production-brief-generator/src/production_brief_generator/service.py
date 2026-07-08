"""Production Brief Generator service."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import ProductionBriefConfig
from .json_utils import load_json_file, write_json_file
from .logging_utils import ComponentLogger
from .schema_validator import SchemaValidator


FORBIDDEN_PHRASES = [
    "guaranteed",
    "sure win",
    "banker",
    "lock",
    "bet of the day",
    "risk-free",
    "100 percent",
    "this will definitely happen"
]
REQUIRED_PHRASES = [
    "Before the first whistle... here's the insight.",
    "Do you agree, or are we missing something?"
]


class ProductionBriefGeneratorService:
    def __init__(self, config: ProductionBriefConfig):
        self.config = config
        self.schema_validator = SchemaValidator()
        self.input_schema = load_json_file(config.input_schema)
        self.output_schema = load_json_file(config.output_schema)

    def run_from_file(self, validated_package_path: Path) -> dict[str, Any]:
        return self.run(load_json_file(validated_package_path))

    def run(self, package: dict[str, Any]) -> dict[str, Any]:
        production_id = package.get("metadata", {}).get("production_id", "unknown-production")
        logger = ComponentLogger(self.config.log_directory, production_id)
        logger.log({"event": "brief_generation_started", "production_id": production_id})
        input_issues = self.schema_validator.validate(package, self.input_schema)
        if package.get("approval_status") != "approved":
            input_issues.append("validated editorial package must be approved")
        if input_issues:
            error = self._structured_error(production_id, input_issues)
            logger.log({"event": "brief_generation_failed", "issues": input_issues})
            return error

        brief = self._build_brief(package)
        issues = self.schema_validator.validate(brief, self.output_schema)
        if issues:
            error = self._structured_error(production_id, issues)
            logger.log({"event": "brief_schema_failed", "issues": issues})
            return error

        output_path = self.config.output_directory / f"production-brief-{production_id}.json"
        write_json_file(output_path, brief)
        logger.log({"event": "brief_written", "brief_path": str(output_path)})
        return {"success": True, "brief": brief, "brief_path": str(output_path)}

    def _build_brief(self, package: dict[str, Any]) -> dict[str, Any]:
        production_id = package["metadata"]["production_id"]
        evidence_to_use = [
            item.get("simple_translation") or item.get("claim")
            for item in package.get("primary_evidence", [])
        ]
        evidence_to_avoid = [
            "Do not mention rejected statistics unless they directly explain the story.",
            "Do not turn the match edge into a prediction.",
            "Do not read confidence scores in the voiceover."
        ]
        contradiction = [
            item.get("simple_translation") or item.get("claim")
            for item in package.get("contradictory_evidence", [])
        ]
        return {
            "production_id": production_id,
            "brief_id": f"brief-{production_id}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "match": package["match"],
            "competition": package["competition"],
            "video_type": "60-second match preview",
            "target_duration_seconds": self.config.target_duration_seconds,
            "target_platforms": self.config.target_platforms,
            "language": "English",
            "brand_opening": "Before the first whistle... here's the insight.",
            "central_question": package["central_question"],
            "hook_direction": _hook_direction(package),
            "surprising_fact": package["surprising_fact"],
            "story_angle": package["story_angle"],
            "main_insight": package["insight_summary"],
            "evidence_to_use": evidence_to_use,
            "evidence_to_avoid": evidence_to_avoid,
            "contradiction_to_handle": contradiction,
            "match_edge": package["match_edge"],
            "key_advantage": package["key_advantage"],
            "x_factor": package["x_factor"],
            "viewer_takeaway": package["viewer_takeaway"],
            "desired_emotion": "Curious, informed, ready to debate.",
            "tone_rules": [
                "Sound conversational.",
                "Sound like a knowledgeable football friend.",
                "Avoid heavy jargon.",
                "Avoid betting certainty.",
                "Avoid robotic language.",
                "Explain one idea clearly.",
                "End with a debate question."
            ],
            "forbidden_phrases": FORBIDDEN_PHRASES,
            "required_phrases": REQUIRED_PHRASES,
            "cta_direction": "Ask viewers whether Arsenal can survive the first 20 minutes.",
            "scriptwriter_notes": [
                "Do not write a prediction.",
                "Use the contradiction to keep the story balanced.",
                "Keep the dashboard language natural and simple."
            ],
            "locked_fields": package["locked_fields"],
            "next_agent": self.config.next_agent,
        }

    @staticmethod
    def _structured_error(production_id: str, issues: list[str]) -> dict[str, Any]:
        return {
            "success": False,
            "component_id": "S2-C02",
            "component_name": "Production Brief Generator",
            "production_id": production_id,
            "error": {
                "code": "PRODUCTION_BRIEF_GENERATION_FAILED",
                "message": "Production Brief could not be generated",
                "issues": issues,
            },
            "next_agent": None,
        }


def _hook_direction(package: dict[str, Any]) -> str:
    question = package.get("central_question", "")
    if "fast start" in question.lower() or "first" in package.get("surprising_fact", "").lower():
        return "Open with Liverpool's early scoring pattern."
    return "Open with the surprising fact, then ask the central question."
