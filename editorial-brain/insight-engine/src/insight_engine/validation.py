"""Business and schema validation for Insight Engine."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .errors import ValidationError
from .json_utils import load_json_file
from .llm import calculate_confidence
from .schema_validator import SchemaValidator


ALLOWED_MATCH_EDGES = {"Home Edge", "Away Edge", "Balanced", "Slight Home Edge", "Slight Away Edge"}
FORBIDDEN_BETTING_TERMS = ["banker", "lock", "guaranteed", "safe bet", "sure bet", "betting tip", "must win"]
TECHNICAL_TERMS = ["xg differential", "ppda", "field tilt", "expected threat", "transition efficiency"]
UNSUPPORTED_RISK_TERMS = ["injury", "suspension", "weather", "red card"]


class InsightEngineValidator:
    def __init__(
        self,
        daily_input_schema_path: Path,
        match_selection_schema_path: Path,
        story_hunter_schema_path: Path,
        evidence_filter_schema_path: Path,
        output_schema_path: Path,
        minimum_confidence: int,
    ):
        self.daily_input_schema = load_json_file(daily_input_schema_path)
        self.match_selection_schema = load_json_file(match_selection_schema_path)
        self.story_hunter_schema = load_json_file(story_hunter_schema_path)
        self.evidence_filter_schema = load_json_file(evidence_filter_schema_path)
        self.output_schema = load_json_file(output_schema_path)
        self.minimum_confidence = minimum_confidence
        self.schema_validator = SchemaValidator()

    def validate_inputs(
        self,
        daily_input: dict[str, Any],
        match_selection: dict[str, Any],
        story_hunter: dict[str, Any],
        evidence_filter: dict[str, Any],
    ) -> None:
        issues = []
        issues.extend(self.schema_validator.validate(daily_input, self.daily_input_schema))
        issues.extend(self.schema_validator.validate(match_selection, self.match_selection_schema))
        issues.extend(self.schema_validator.validate(story_hunter, self.story_hunter_schema))
        issues.extend(self.schema_validator.validate(evidence_filter, self.evidence_filter_schema))
        if match_selection.get("approval_status") != "approved":
            issues.append("$.match_selection.approval_status: must be approved")
        if story_hunter.get("approval_status") != "approved":
            issues.append("$.story_hunter.approval_status: must be approved")
        if evidence_filter.get("approval_status") != "approved":
            issues.append("$.evidence_filter.approval_status: must be approved")
        if evidence_filter.get("story_angle") != story_hunter.get("story_angle"):
            issues.append("$.evidence_filter.story_angle: must match Story Hunter story_angle")
        if evidence_filter.get("central_question") != story_hunter.get("central_question"):
            issues.append("$.evidence_filter.central_question: must match Story Hunter central_question")
        if issues:
            raise ValidationError("Insight Engine input validation failed", issues)

    def validate_output(self, output: dict[str, Any], story_hunter: dict[str, Any], evidence_filter: dict[str, Any]) -> None:
        issues = self.schema_validator.validate(output, self.output_schema)
        issues.extend(self._validate_business_rules(output, story_hunter, evidence_filter))
        if issues:
            raise ValidationError("Insight Engine output validation failed", issues)

    def _validate_business_rules(self, output: dict[str, Any], story_hunter: dict[str, Any], evidence_filter: dict[str, Any]) -> list[str]:
        issues: list[str] = []
        if output.get("agent_id") != "IF-A04":
            issues.append("$.agent_id: must be IF-A04")
        if output.get("next_agent") != "IF-A05":
            issues.append("$.next_agent: must be IF-A05")
        if output.get("approval_status") != "approved":
            issues.append("$.approval_status: must be approved for downstream handoff")

        if output.get("match_edge") not in ALLOWED_MATCH_EDGES:
            issues.append("$.match_edge: invalid or missing match edge")
        if _contains_probability(output.get("match_edge", "")):
            issues.append("$.match_edge: probabilities are not allowed")

        tactical = str(output.get("tactical_explanation", "")).strip()
        if not tactical:
            issues.append("$.tactical_explanation: required")
        if _sentence_count(tactical) > 3:
            issues.append("$.tactical_explanation: maximum 3 sentences")

        if not str(output.get("x_factor", "")).strip():
            issues.append("$.x_factor: required")
        if not str(output.get("uncertainty_summary", "")).strip():
            issues.append("$.uncertainty_summary: required")

        for field in ["story_angle", "central_question"]:
            if output.get(field) != story_hunter.get(field):
                issues.append(f"$.{field}: must preserve approved Story Hunter field")
        locked = output.get("locked_fields", {})
        for field in ["story_angle", "central_question", "surprising_fact"]:
            if locked.get(field) != story_hunter.get(field):
                issues.append(f"$.locked_fields.{field}: must preserve approved Story Hunter field")

        combined = " ".join(
            str(output.get(field, ""))
            for field in [
                "insight_summary",
                "match_edge",
                "key_advantage",
                "tactical_explanation",
                "uncertainty_summary",
                "x_factor",
                "surprising_takeaway",
                "viewer_takeaway",
            ]
        ).lower()
        for term in FORBIDDEN_BETTING_TERMS:
            if term in combined:
                issues.append(f"forbidden betting language: '{term}'")
        for term in TECHNICAL_TERMS:
            if term in combined:
                issues.append(f"unexplained jargon: '{term}'")

        source_text = " ".join([
            str(story_hunter),
            str(evidence_filter),
        ]).lower()
        for term in UNSUPPORTED_RISK_TERMS:
            if term in combined and term not in source_text:
                issues.append(f"unsupported claim introduced: '{term}'")

        confidence = output.get("confidence", {}).get("score")
        if not isinstance(confidence, int):
            issues.append("$.confidence.score: must be an integer")
        elif confidence < self.minimum_confidence:
            issues.append(f"$.confidence.score: must be >= {self.minimum_confidence}")
        expected_confidence = calculate_confidence(
            int(evidence_filter.get("evidence_confidence", 0)),
            evidence_filter.get("evidence_quality", {}),
        )
        if isinstance(confidence, int) and abs(confidence - expected_confidence) > 10:
            issues.append("$.confidence.score: does not match evidence-based confidence calculation")

        return issues


def _sentence_count(text: str) -> int:
    return len([part for part in re.split(r"[.!?]+", text) if part.strip()])


def _contains_probability(text: str) -> bool:
    return bool(re.search(r"\b\d{1,3}\s*%", str(text)))
