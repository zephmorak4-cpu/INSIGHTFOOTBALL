"""CTA Generator service."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .config import CtaGeneratorConfig
from .errors import ValidationError
from .json_utils import load_json_file, parse_json_object, write_json_file, write_text_file
from .llm import LLMClient
from .logging_utils import StructuredLogger
from .prompt_loader import PromptLoader
from .validation import CtaGeneratorValidator


class CtaGeneratorService:
    def __init__(self, config: CtaGeneratorConfig, llm_client: LLMClient):
        self.config = config
        self.llm_client = llm_client
        self.prompt_loader = PromptLoader(config.prompt_path)
        self.validator = CtaGeneratorValidator(config.script_schema, config.brief_schema, config.cta_schema, config.final_package_schema, config.max_cta_options, config.target_duration_seconds)

    def run_from_files(self, script_path: Path, brief_path: Path) -> dict[str, Any]:
        return self.run(load_json_file(script_path), load_json_file(brief_path))

    def run(self, script: dict[str, Any], brief: dict[str, Any]) -> dict[str, Any]:
        production_id = brief.get("production_id", "unknown-production")
        logger = StructuredLogger(self.config.log_directory, f"cta-generator-{production_id}")
        try:
            self.validator.validate_inputs(script, brief)
            prompt = self.prompt_loader.load() + "\n\nOptimized Script:\n" + json.dumps(script, ensure_ascii=True) + "\n\nBrief:\n" + json.dumps(brief, ensure_ascii=True)
        except ValidationError as exc:
            return self._error(production_id, "CTA_INPUT_INVALID", exc.issues)
        last_issues: list[str] = []
        for attempt in range(1, self.config.max_retries + 2):
            try:
                cta = parse_json_object(self.llm_client.generate(prompt, temperature=self.config.temperature, max_tokens=self.config.max_tokens))
                self.validator.validate_cta(cta)
                final_package = self._build_final_package(script, brief, cta)
                self.validator.validate_final_package(final_package)
                cta_path = self.config.output_directory / f"cta-output-{production_id}.json"
                final_script_path = self.config.output_directory / f"final-script-output-{production_id}.json"
                final_package_path = self.config.output_directory / "final-script-package.json"
                voiceover_path = self.config.output_directory / "voiceover_final.txt"
                write_json_file(cta_path, cta)
                write_json_file(final_script_path, {**script, "cta": cta["selected_cta"], "full_voiceover": cta["final_voiceover"], "final_voiceover": cta["final_voiceover"], "word_count": cta["final_word_count"], "estimated_duration_seconds": cta["final_estimated_duration_seconds"], "script_version": "v3-final"})
                write_json_file(final_package_path, final_package)
                write_text_file(voiceover_path, cta["final_voiceover"])
                logger.log({"event": "cta_generator_completed", "attempt": attempt, "final_package_path": str(final_package_path), "voiceover_path": str(voiceover_path)})
                return {"success": True, "cta": cta, "final_package": final_package, "cta_path": str(cta_path), "final_script_path": str(final_script_path), "final_package_path": str(final_package_path), "voiceover_path": str(voiceover_path)}
            except (ValueError, json.JSONDecodeError, ValidationError) as exc:
                last_issues = getattr(exc, "issues", [str(exc)])
                logger.log({"event": "cta_generator_attempt_failed", "attempt": attempt, "issues": last_issues})
        return self._error(production_id, "CTA_GENERATION_FAILED", last_issues)

    def _build_final_package(self, script: dict[str, Any], brief: dict[str, Any], cta: dict[str, Any]) -> dict[str, Any]:
        return {
            "production_id": brief["production_id"],
            "match": brief["match"],
            "competition": brief["competition"],
            "source_production_brief": brief["brief_id"],
            "full_voiceover": cta["final_voiceover"],
            "final_voiceover": cta["final_voiceover"],
            "word_count": cta["final_word_count"],
            "estimated_duration_seconds": cta["final_estimated_duration_seconds"],
            "hook": script["hook"],
            "central_question": script["central_question"],
            "main_body": script["main_body"],
            "conclusion": script["conclusion"],
            "cta": cta["selected_cta"],
            "claims_used": script["claims_used"],
            "claims_rejected": script["claims_rejected"],
            "locked_fields": script["locked_fields"],
            "script_quality_scores": {
                "clarity": 90,
                "football_language": 90,
                "story_focus": 88,
                "brand_safety": 95,
                "duration_fit": 95 if cta["final_estimated_duration_seconds"] <= self.config.target_duration_seconds else 50
            },
            "warnings": script.get("warnings", []),
            "human_review_flags": script.get("human_review_flags", []),
            "approval_status": "approved",
            "next_agent": self.config.next_agent,
        }

    @staticmethod
    def _error(production_id: str, code: str, issues: list[str]) -> dict[str, Any]:
        return {"success": False, "component_id": "S3-C03", "component_name": "CTA Generator", "production_id": production_id, "error": {"code": code, "issues": issues}, "approval_status": "blocked"}
