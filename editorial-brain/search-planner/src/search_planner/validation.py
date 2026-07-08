from __future__ import annotations

from pathlib import Path
from typing import Any

from .errors import ValidationError
from .json_utils import load_json_file
from .schema_validator import SchemaValidator


class SearchPlannerValidator:
    def __init__(self, input_schema: Path, output_schema: Path, blocked_source_types: list[str]):
        self.input_schema = load_json_file(input_schema)
        self.output_schema = load_json_file(output_schema)
        self.blocked_source_types = blocked_source_types
        self.schema_validator = SchemaValidator()

    def validate_input(self, manifest: dict[str, Any]) -> None:
        issues = self.schema_validator.validate(manifest, self.input_schema)
        if not manifest.get("missing_assets"):
            issues.append("$.missing_assets: expected planning list, even if empty")
        if issues:
            raise ValidationError("Search Planner input validation failed", issues)

    def validate_output(self, plan: dict[str, Any], manifest: dict[str, Any]) -> None:
        issues = self.schema_validator.validate(plan, self.output_schema)
        if manifest.get("missing_assets") and not (plan.get("search_tasks") or plan.get("manual_tasks") or plan.get("generation_tasks") or plan.get("legal_review_tasks")):
            issues.append("missing assets must create tasks")
        for task in plan.get("blocked_assets", []):
            if task.get("approved_source_type") != "blocked":
                issues.append(f"{task.get('task_id')}: blocked asset cannot be approved")
        if manifest.get("legal_warnings") and not plan.get("legal_review_tasks"):
            issues.append("legal warnings must create legal review tasks")
        if not plan.get("fallback_tasks"):
            issues.append("fallback tasks required")
        if issues:
            raise ValidationError("Search Planner output validation failed", sorted(set(issues)))

