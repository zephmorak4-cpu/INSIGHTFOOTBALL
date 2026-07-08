"""Business and schema validation for Evidence Filter."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .errors import ValidationError
from .json_utils import load_json_file
from .schema_validator import SchemaValidator


FORBIDDEN_BETTING_TERMS = ["banker", "lock", "guaranteed", "safe bet", "sure bet", "betting tip"]
IRRELEVANT_STAT_TERMS = ["corners", "possession", "pass accuracy"]


class EvidenceFilterValidator:
    def __init__(
        self,
        daily_input_schema_path: Path,
        match_selection_schema_path: Path,
        story_hunter_schema_path: Path,
        output_schema_path: Path,
        minimum_confidence: int,
    ):
        self.daily_input_schema = load_json_file(daily_input_schema_path)
        self.match_selection_schema = load_json_file(match_selection_schema_path)
        self.story_hunter_schema = load_json_file(story_hunter_schema_path)
        self.output_schema = load_json_file(output_schema_path)
        self.minimum_confidence = minimum_confidence
        self.schema_validator = SchemaValidator()

    def validate_inputs(self, daily_input: dict[str, Any], match_selection: dict[str, Any], story_hunter: dict[str, Any]) -> None:
        issues = []
        issues.extend(self.schema_validator.validate(daily_input, self.daily_input_schema))
        issues.extend(self.schema_validator.validate(match_selection, self.match_selection_schema))
        issues.extend(self.schema_validator.validate(story_hunter, self.story_hunter_schema))
        if match_selection.get("approval_status") != "approved":
            issues.append("$.match_selection.approval_status: must be approved")
        if story_hunter.get("approval_status") != "approved":
            issues.append("$.story_hunter.approval_status: must be approved")
        if story_hunter.get("selected_match") != match_selection.get("selected_match"):
            issues.append("$.story_hunter.selected_match: must match Match Selector selected_match")
        if issues:
            raise ValidationError("Evidence Filter input validation failed", issues)

    def validate_output(self, output: dict[str, Any], story_hunter: dict[str, Any]) -> None:
        issues = self.schema_validator.validate(output, self.output_schema)
        issues.extend(self._validate_business_rules(output, story_hunter))
        if issues:
            raise ValidationError("Evidence Filter output validation failed", issues)

    def _validate_business_rules(self, output: dict[str, Any], story_hunter: dict[str, Any]) -> list[str]:
        issues: list[str] = []
        if output.get("agent_id") != "IF-A03":
            issues.append("$.agent_id: must be IF-A03")
        if output.get("next_agent") != "IF-A04":
            issues.append("$.next_agent: must be IF-A04")
        if output.get("approval_status") != "approved":
            issues.append("$.approval_status: must be approved for downstream handoff")

        for field in ["story_angle", "central_question"]:
            if output.get(field) != story_hunter.get(field):
                issues.append(f"$.{field}: must preserve approved Story Hunter field")
        locked = output.get("locked_fields", {})
        for field in ["story_angle", "central_question", "surprising_fact"]:
            if locked.get(field) != story_hunter.get(field):
                issues.append(f"$.locked_fields.{field}: must preserve approved Story Hunter field")

        primary = output.get("primary_evidence", [])
        secondary = output.get("secondary_evidence", [])
        if len(primary) < 2:
            issues.append("$.primary_evidence: at least two direct evidence points are required")
        if not output.get("evidence_summary"):
            issues.append("$.evidence_summary: required")

        all_claims = []
        for section in [primary, secondary, output.get("contradictory_evidence", [])]:
            for item in section:
                claim = str(item.get("claim", "")).strip().lower()
                if claim in all_claims:
                    issues.append(f"duplicated evidence: {claim}")
                all_claims.append(claim)
                for term in FORBIDDEN_BETTING_TERMS:
                    if term in claim:
                        issues.append(f"forbidden betting language: '{term}'")

        for item in output.get("supporting_statistics", []):
            raw = str(item.get("raw_stat", "")).lower()
            used = item.get("used")
            if used is True and any(term in raw for term in IRRELEVANT_STAT_TERMS):
                issues.append(f"unrelated statistic used as evidence: {raw}")
            if not item.get("simple_translation"):
                issues.append("$.supporting_statistics: every stat needs simple_translation")

        evidence_confidence = output.get("evidence_confidence")
        if not isinstance(evidence_confidence, int):
            issues.append("$.evidence_confidence: must be an integer")
        elif evidence_confidence < self.minimum_confidence:
            issues.append(f"$.evidence_confidence: must be >= {self.minimum_confidence}")

        quality = output.get("evidence_quality", {})
        if quality:
            average_quality = sum(int(quality.get(key, 0)) for key in ["story_support", "clarity", "relevance", "data_reliability"]) / 4
            if isinstance(evidence_confidence, int) and evidence_confidence > int(average_quality * 10) + 15:
                issues.append("$.evidence_confidence: too high for evidence quality scores")

        return issues
