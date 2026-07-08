"""Validation layer for the Editorial Orchestrator."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .errors import ValidationError
from .json_utils import load_json_file
from .schema_validator import SchemaValidator


class OrchestratorValidator:
    def __init__(self, package_schema_path: Path, minimum_confidence: int):
        self.package_schema = load_json_file(package_schema_path)
        self.minimum_confidence = minimum_confidence
        self.schema_validator = SchemaValidator()

    def validate_stage_output(self, output: dict[str, Any], expected_agent_id: str, confidence_path: tuple[str, ...]) -> None:
        issues: list[str] = []
        if output.get("success") is False:
            issues.append(f"{expected_agent_id}: module returned structured error")
            issues.extend(output.get("error", {}).get("issues", []))
        if output.get("agent_id") != expected_agent_id:
            issues.append(f"{expected_agent_id}: unexpected agent_id {output.get('agent_id')}")
        if output.get("approval_status") != "approved":
            issues.append(f"{expected_agent_id}: approval_status must be approved")
        confidence = _get_nested(output, confidence_path)
        if not isinstance(confidence, int):
            issues.append(f"{expected_agent_id}: confidence missing or invalid")
        elif confidence < self.minimum_confidence:
            issues.append(f"{expected_agent_id}: confidence {confidence} below {self.minimum_confidence}")
        if issues:
            raise ValidationError(f"{expected_agent_id} validation failed", issues)

    def validate_locked_fields(
        self,
        *,
        story_hunter: dict[str, Any],
        evidence_filter: dict[str, Any],
        insight_engine: dict[str, Any],
    ) -> None:
        issues: list[str] = []
        for field in ["story_angle", "central_question", "surprising_fact"]:
            expected = story_hunter.get(field)
            if evidence_filter.get("locked_fields", {}).get(field) != expected:
                issues.append(f"Evidence Filter changed locked field: {field}")
            if insight_engine.get("locked_fields", {}).get(field) != expected:
                issues.append(f"Insight Engine changed locked field: {field}")
        if evidence_filter.get("story_angle") != story_hunter.get("story_angle"):
            issues.append("Evidence Filter story_angle does not match Story Hunter")
        if insight_engine.get("story_angle") != story_hunter.get("story_angle"):
            issues.append("Insight Engine story_angle does not match Story Hunter")
        if issues:
            raise ValidationError("Locked field validation failed", issues)

    def validate_package(self, package: dict[str, Any]) -> None:
        issues = self.schema_validator.validate(package, self.package_schema)
        if package.get("locked_fields", {}).get("story_angle") != package.get("story_angle"):
            issues.append("Package locked story_angle mismatch")
        if package.get("locked_fields", {}).get("central_question") != package.get("central_question"):
            issues.append("Package locked central_question mismatch")
        if package.get("locked_fields", {}).get("surprising_fact") != package.get("surprising_fact"):
            issues.append("Package locked surprising_fact mismatch")
        if issues:
            raise ValidationError("Editorial Package validation failed", issues)


def _get_nested(data: dict[str, Any], path: tuple[str, ...]):
    current: Any = data
    for item in path:
        if not isinstance(current, dict):
            return None
        current = current.get(item)
    return current
