"""Business and schema validation for Story Hunter."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .errors import ValidationError
from .json_utils import load_json_file
from .schema_validator import SchemaValidator


GENERIC_ANGLES = [
    "match preview",
    "both teams want to win",
    "exciting game",
    "good form",
    "needs points",
]
FORBIDDEN_BETTING_TERMS = ["banker", "lock", "guaranteed", "safe bet", "sure bet", "betting tip"]
TECHNICAL_TERMS = ["xg differential", "transition efficiency", "ppda", "field tilt", "expected threat"]


class StoryHunterValidator:
    def __init__(
        self,
        daily_input_schema_path: Path,
        match_selection_schema_path: Path,
        output_schema_path: Path,
        minimum_confidence: int,
    ):
        self.daily_input_schema = load_json_file(daily_input_schema_path)
        self.match_selection_schema = load_json_file(match_selection_schema_path)
        self.output_schema = load_json_file(output_schema_path)
        self.minimum_confidence = minimum_confidence
        self.schema_validator = SchemaValidator()

    def validate_inputs(self, daily_input: dict[str, Any], match_selection: dict[str, Any]) -> None:
        issues = []
        issues.extend(self.schema_validator.validate(daily_input, self.daily_input_schema))
        issues.extend(self.schema_validator.validate(match_selection, self.match_selection_schema))
        if match_selection.get("approval_status") != "approved":
            issues.append("$.match_selection.approval_status: must be approved")
        if issues:
            raise ValidationError("Story Hunter input validation failed", issues)

    def validate_output(self, output: dict[str, Any], match_selection: dict[str, Any]) -> None:
        issues = self.schema_validator.validate(output, self.output_schema)
        issues.extend(self._validate_business_rules(output, match_selection))
        if issues:
            raise ValidationError("Story Hunter output validation failed", issues)

    def _validate_business_rules(self, output: dict[str, Any], match_selection: dict[str, Any]) -> list[str]:
        issues: list[str] = []
        if output.get("agent_id") != "IF-A02":
            issues.append("$.agent_id: must be IF-A02")
        if output.get("next_agent") != "IF-A03":
            issues.append("$.next_agent: must be IF-A03")
        if output.get("approval_status") != "approved":
            issues.append("$.approval_status: must be approved for downstream handoff")

        if output.get("selected_match") != match_selection.get("selected_match"):
            issues.append("$.selected_match: must match approved Match Selector output")

        story_angle = str(output.get("story_angle", "")).strip()
        central_question = str(output.get("central_question", "")).strip()
        surprising_fact = str(output.get("surprising_fact", "")).strip()
        combined = " ".join([story_angle, central_question, surprising_fact]).lower()

        if len(story_angle.split()) < 8:
            issues.append("$.story_angle: too short to be a clear story angle")
        if not central_question.endswith("?"):
            issues.append("$.central_question: must be a question")
        if len(central_question.split()) < 5:
            issues.append("$.central_question: boring or too short")
        if len(surprising_fact.split()) < 8:
            issues.append("$.surprising_fact: too weak or too short")

        for phrase in GENERIC_ANGLES:
            if phrase in story_angle.lower() or phrase in central_question.lower():
                issues.append(f"story is too generic: contains '{phrase}'")
        for term in FORBIDDEN_BETTING_TERMS:
            if term in combined:
                issues.append(f"forbidden betting language: '{term}'")
        for term in TECHNICAL_TERMS:
            if term in combined:
                issues.append(f"language is too technical: '{term}'")

        if "sample" not in surprising_fact.lower() and "verified" not in " ".join(output.get("warnings", [])).lower():
            # The MVP examples often use sample data. Real facts must either be verified upstream or flagged.
            issues.append("$.surprising_fact: unsupported fact must be marked sample or verified")

        story_confidence = output.get("story_confidence")
        if not isinstance(story_confidence, int):
            issues.append("$.story_confidence: must be an integer")
        elif story_confidence < self.minimum_confidence:
            issues.append(f"$.story_confidence: must be >= {self.minimum_confidence}")

        locked = output.get("locked_fields", {})
        for field in ["story_angle", "central_question", "surprising_fact"]:
            if locked.get(field) != output.get(field):
                issues.append(f"$.locked_fields.{field}: must match top-level {field}")

        return issues
