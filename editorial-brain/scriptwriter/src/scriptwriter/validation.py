"""Scriptwriter validation."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .errors import ValidationError
from .json_utils import load_json_file
from .llm import count_words, estimate_duration_seconds
from .schema_validator import SchemaValidator


BETTING_LANGUAGE = ["guaranteed", "sure win", "banker", "lock", "bet of the day", "risk-free", "100 percent", "definitely will win", "must win bet", "free money"]
ROBOTIC_LANGUAGE = ["based on the data provided", "the model indicates", "statistical analysis suggests", "the home side possesses", "expected goals differential"]
UNSUPPORTED_TERMS = ["red card", "injury", "suspension", "weather"]
INTERNAL_TERMS = ["Form Index", "Risk Meter", "Tactical Edge", "X-Factor", "Evidence Filter", "Insight Engine", "Story Hunter", "Editorial Brain"]


class ScriptwriterValidator:
    def __init__(self, input_schema: Path, output_schema: Path, min_words: int, max_words: int, max_seconds: int):
        self.input_schema = load_json_file(input_schema)
        self.output_schema = load_json_file(output_schema)
        self.min_words = min_words
        self.max_words = max_words
        self.max_seconds = max_seconds
        self.schema_validator = SchemaValidator()

    def validate_input(self, brief: dict[str, Any]) -> None:
        issues = self.schema_validator.validate(brief, self.input_schema)
        if not brief.get("central_question"):
            issues.append("$.central_question: required")
        if brief.get("next_agent") != "IF-A05":
            issues.append("$.next_agent: production brief must target IF-A05")
        if issues:
            raise ValidationError("Scriptwriter input validation failed", issues)

    def validate_output(self, output: dict[str, Any], brief: dict[str, Any]) -> None:
        issues = self.schema_validator.validate(output, self.output_schema)
        voiceover = str(output.get("full_voiceover", ""))
        lower = voiceover.lower()
        expected_opening = brief.get("brand_opening", "")
        words = count_words(voiceover)
        seconds = estimate_duration_seconds(voiceover)
        if not voiceover.startswith(expected_opening):
            issues.append("$.full_voiceover: must start with required brand opening")
        if words < self.min_words:
            issues.append(f"$.word_count: must be >= {self.min_words}")
        if words > self.max_words:
            issues.append(f"$.word_count: must be <= {self.max_words}")
        if seconds > self.max_seconds:
            issues.append(f"$.estimated_duration_seconds: must be <= {self.max_seconds}")
        if output.get("word_count") != words:
            issues.append("$.word_count: must match full_voiceover")
        if output.get("estimated_duration_seconds") != seconds:
            issues.append("$.estimated_duration_seconds: must match full_voiceover")
        if output.get("final_voiceover") and output.get("final_voiceover") != voiceover:
            issues.append("$.final_voiceover: must match full_voiceover")
        if brief.get("central_question") not in voiceover:
            issues.append("$.full_voiceover: central question must be included")
        if brief.get("surprising_fact") not in voiceover:
            issues.append("$.full_voiceover: surprising fact must be included")
        if output.get("cta") and output["cta"] not in voiceover:
            issues.append("$.full_voiceover: CTA must be included")
        for term in BETTING_LANGUAGE:
            if _contains_phrase(lower, term):
                issues.append(f"forbidden betting language: {term}")
        for phrase in ROBOTIC_LANGUAGE:
            if phrase in lower:
                issues.append(f"robotic language: {phrase}")
        for term in INTERNAL_TERMS:
            if _contains_phrase(lower, term.lower()):
                issues.append(f"internal terminology leaked: {term}")
        source = " ".join([str(brief), str(output.get("claims_used", []))]).lower()
        for term in UNSUPPORTED_TERMS:
            if term in lower and term not in source:
                issues.append(f"unsupported claim introduced: {term}")
        locked = output.get("locked_fields", {})
        for field in ["central_question", "surprising_fact", "story_angle"]:
            if locked.get(field) != brief.get("locked_fields", {}).get(field):
                issues.append(f"$.locked_fields.{field}: must preserve production brief locked field")
        if output.get("central_question") != brief.get("central_question"):
            issues.append("$.central_question: must preserve production brief central question")
        if output.get("approval_status") != "approved":
            issues.append("$.approval_status: must be approved")
        if output.get("next_agent") != "IF-A06":
            issues.append("$.next_agent: must be IF-A06")
        if issues:
            raise ValidationError("Scriptwriter output validation failed", sorted(set(issues)))


def _contains_phrase(text: str, phrase: str) -> bool:
    return re.search(rf"\b{re.escape(phrase)}\b", text) is not None
