"""CTA Generator validation."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .errors import ValidationError
from .json_utils import load_json_file
from .metrics import count_words, estimate_duration_seconds
from .schema_validator import SchemaValidator


GENERIC_CTA = ["like and subscribe", "follow us for more amazing content", "smash that like button"]
BETTING_CTA = ["click the link to win", "free money", "risk-free", "guaranteed", "bet of the day"]


class CtaGeneratorValidator:
    def __init__(self, script_schema: Path, brief_schema: Path, cta_schema: Path, final_package_schema: Path, max_options: int, max_seconds: int):
        self.script_schema = load_json_file(script_schema)
        self.brief_schema = load_json_file(brief_schema)
        self.cta_schema = load_json_file(cta_schema)
        self.final_package_schema = load_json_file(final_package_schema)
        self.max_options = max_options
        self.max_seconds = max_seconds
        self.schema_validator = SchemaValidator()

    def validate_inputs(self, script: dict[str, Any], brief: dict[str, Any]) -> None:
        issues = []
        issues.extend(self.schema_validator.validate(script, self.script_schema))
        issues.extend(self.schema_validator.validate(brief, self.brief_schema))
        if script.get("production_id") != brief.get("production_id"):
            issues.append("$.production_id: script and brief must match")
        if issues:
            raise ValidationError("CTA input validation failed", issues)

    def validate_cta(self, cta: dict[str, Any]) -> None:
        issues = self.schema_validator.validate(cta, self.cta_schema)
        options = cta.get("cta_options", [])
        if len(options) != self.max_options:
            issues.append(f"$.cta_options: must contain {self.max_options} options")
        if cta.get("selected_cta") not in options:
            issues.append("$.selected_cta: must be one of cta_options")
        for option in options:
            lower = str(option).lower()
            for phrase in GENERIC_CTA:
                if phrase in lower:
                    issues.append(f"generic CTA rejected: {phrase}")
            for phrase in BETTING_CTA:
                if _contains_phrase(lower, phrase):
                    issues.append(f"betting CTA rejected: {phrase}")
        if count_words(cta.get("final_voiceover", "")) != cta.get("final_word_count"):
            issues.append("$.final_word_count: must match final voiceover")
        if estimate_duration_seconds(cta.get("final_voiceover", "")) != cta.get("final_estimated_duration_seconds"):
            issues.append("$.final_estimated_duration_seconds: must match final voiceover")
        if cta.get("final_estimated_duration_seconds", 999) > self.max_seconds:
            issues.append("$.final_estimated_duration_seconds: must be <= 60")
        if issues:
            raise ValidationError("CTA output validation failed", sorted(set(issues)))

    def validate_final_package(self, package: dict[str, Any]) -> None:
        issues = self.schema_validator.validate(package, self.final_package_schema)
        if package.get("next_agent") != "IF-A06":
            issues.append("$.next_agent: must be IF-A06")
        if package.get("estimated_duration_seconds", 999) > self.max_seconds:
            issues.append("$.estimated_duration_seconds: must be <= 60")
        if issues:
            raise ValidationError("Final script package validation failed", issues)


def _contains_phrase(text: str, phrase: str) -> bool:
    return re.search(rf"\b{re.escape(phrase)}\b", text) is not None

