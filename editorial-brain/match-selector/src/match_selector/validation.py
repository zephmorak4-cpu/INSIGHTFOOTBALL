"""Business and schema validation for Match Selector."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from .errors import ValidationError
from .json_utils import load_json_file
from .schema_validator import SchemaValidator


FORBIDDEN_BETTING_TERMS = ["banker", "lock", "guaranteed", "safe bet", "sure bet"]


class MatchSelectorValidator:
    def __init__(self, input_schema_path: Path, output_schema_path: Path, minimum_confidence: int):
        self.input_schema = load_json_file(input_schema_path)
        self.output_schema = load_json_file(output_schema_path)
        self.minimum_confidence = minimum_confidence
        self.schema_validator = SchemaValidator()

    def validate_daily_input(self, daily_input: dict[str, Any]) -> None:
        issues = self.schema_validator.validate(daily_input, self.input_schema)
        fixtures = daily_input.get("fixtures", [])
        if len(fixtures) < 1:
            issues.append("$.fixtures: at least one fixture is required")
        if _production_mode():
            production_date = daily_input.get("production_metadata", {}).get("date", "")
            if not production_date:
                issues.append("$.production_metadata.date: required in production")
            for index, fixture in enumerate(fixtures):
                kickoff = str(fixture.get("kickoff_time", ""))
                if production_date and production_date not in kickoff:
                    issues.append(f"$.fixtures[{index}].kickoff_time: production fixtures must be for {production_date}")
        if issues:
            raise ValidationError("Daily input validation failed", issues)

    def validate_output(self, output: dict[str, Any], daily_input: dict[str, Any]) -> None:
        issues = self.schema_validator.validate(output, self.output_schema)
        issues.extend(self._validate_business_rules(output, daily_input))
        if issues:
            raise ValidationError("Match Selector output validation failed", issues)

    def _validate_business_rules(self, output: dict[str, Any], daily_input: dict[str, Any]) -> list[str]:
        issues: list[str] = []
        if output.get("agent_id") != "IF-A01":
            issues.append("$.agent_id: must be IF-A01")
        if output.get("next_agent") != "IF-A02":
            issues.append("$.next_agent: must be IF-A02")
        if output.get("approval_status") not in {"approved", "needs_revision", "rejected", "blocked", "human_review_required"}:
            issues.append("$.approval_status: invalid value")

        selected = output.get("selected_match", {})
        fixtures = daily_input.get("fixtures", [])
        if selected and not self._selected_match_exists(selected, fixtures):
            issues.append("$.selected_match: selected match must exist in Daily Input fixtures")
        if _production_mode():
            production_date = daily_input.get("production_metadata", {}).get("date", "")
            if production_date and selected and production_date not in str(selected.get("kickoff_time", "")):
                issues.append("$.selected_match.kickoff_time: selected match must be from today's live fixtures")

        confidence = output.get("confidence", {}).get("score")
        if not isinstance(confidence, int):
            issues.append("$.confidence.score: must be an integer")
        elif confidence < self.minimum_confidence:
            issues.append(f"$.confidence.score: must be >= {self.minimum_confidence}")

        calculated = calculate_confidence_floor(output)
        if isinstance(confidence, int) and confidence > calculated + 15:
            issues.append("$.confidence.score: reported confidence is too high for selection inputs")

        reason = str(output.get("selected_reason", "")).lower()
        for term in FORBIDDEN_BETTING_TERMS:
            if term in reason:
                issues.append(f"$.selected_reason: forbidden betting language '{term}'")

        if int(output.get("story_potential_score", 0)) < 5:
            issues.append("$.story_potential_score: selected match has weak story potential")
        if int(output.get("data_availability_score", 0)) < 5:
            issues.append("$.data_availability_score: selected match has weak data availability")

        return issues

    @staticmethod
    def _selected_match_exists(selected: dict[str, Any], fixtures: list[dict[str, Any]]) -> bool:
        for fixture in fixtures:
            if (
                fixture.get("home_team") == selected.get("home_team")
                and fixture.get("away_team") == selected.get("away_team")
                and fixture.get("competition") == selected.get("competition")
                and fixture.get("kickoff_time") == selected.get("kickoff_time")
            ):
                return True
        return False


def calculate_confidence_floor(output: dict[str, Any]) -> int:
    components = [
        int(output.get("audience_interest_score", 0)),
        int(output.get("importance_score", 0)),
        int(output.get("rivalry_score", 0)),
        int(output.get("data_availability_score", 0)),
        int(output.get("story_potential_score", 0)),
    ]
    weighted = (
        components[0] * 1.5
        + components[1] * 1.5
        + components[2] * 1.0
        + components[3] * 2.5
        + components[4] * 3.0
    )
    data_gap_penalty = len(output.get("data_gaps", [])) * 4
    return max(0, min(100, int(round(weighted - data_gap_penalty))))


def _production_mode() -> bool:
    return os.environ.get("INSIGHT_FOOTBALL_ENV", "").lower() == "production"
