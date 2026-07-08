"""Hook Optimizer validation."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .errors import ValidationError
from .json_utils import load_json_file
from .schema_validator import SchemaValidator


BETTING = ["guaranteed", "sure win", "banker", "lock", "bet of the day", "risk-free", "100 percent"]
CLICKBAIT = ["you won't believe", "shocking outcome", "revealed", "crazy", "unbelievable"]


class HookOptimizerValidator:
    def __init__(self, script_schema: Path, brief_schema: Path, optimization_schema: Path, optimized_script_schema: Path, max_options: int):
        self.script_schema = load_json_file(script_schema)
        self.brief_schema = load_json_file(brief_schema)
        self.optimization_schema = load_json_file(optimization_schema)
        self.optimized_script_schema = load_json_file(optimized_script_schema)
        self.max_options = max_options
        self.schema_validator = SchemaValidator()

    def validate_inputs(self, script: dict[str, Any], brief: dict[str, Any]) -> None:
        issues = []
        issues.extend(self.schema_validator.validate(script, self.script_schema))
        issues.extend(self.schema_validator.validate(brief, self.brief_schema))
        if script.get("production_id") != brief.get("production_id"):
            issues.append("$.production_id: script and brief must match")
        if script.get("central_question") != brief.get("central_question"):
            issues.append("$.central_question: script must preserve brief question")
        if issues:
            raise ValidationError("Hook Optimizer input validation failed", issues)

    def validate_optimization(self, optimization: dict[str, Any], script: dict[str, Any], brief: dict[str, Any]) -> None:
        issues = self.schema_validator.validate(optimization, self.optimization_schema)
        options = optimization.get("hook_options", [])
        if len(options) != self.max_options:
            issues.append(f"$.hook_options: must contain {self.max_options} options")
        if optimization.get("selected_hook") not in options:
            issues.append("$.selected_hook: must be one of hook_options")
        for hook in options:
            lower = str(hook).lower()
            if brief.get("surprising_fact") not in hook:
                issues.append("$.hook_options: each hook must preserve surprising fact")
            for phrase in CLICKBAIT:
                if phrase in lower:
                    issues.append(f"clickbait hook rejected: {phrase}")
            for phrase in BETTING:
                if _contains_phrase(lower, phrase):
                    issues.append(f"betting language rejected: {phrase}")
        if not optimization.get("locked_fields_preserved"):
            issues.append("$.locked_fields_preserved: must be true")
        if issues:
            raise ValidationError("Hook Optimizer output validation failed", sorted(set(issues)))

    def validate_optimized_script(self, optimized: dict[str, Any], script: dict[str, Any], brief: dict[str, Any], selected_hook: str) -> None:
        issues = self.schema_validator.validate(optimized, self.optimized_script_schema)
        if optimized.get("hook") != selected_hook:
            issues.append("$.hook: must use selected hook")
        if optimized.get("central_question") != brief.get("central_question"):
            issues.append("$.central_question: must not change")
        if brief.get("surprising_fact") not in optimized.get("hook", ""):
            issues.append("$.hook: must preserve surprising fact")
        if optimized.get("locked_fields") != script.get("locked_fields"):
            issues.append("$.locked_fields: must be preserved")
        if issues:
            raise ValidationError("Optimized script validation failed", issues)


def _contains_phrase(text: str, phrase: str) -> bool:
    return re.search(rf"\b{re.escape(phrase)}\b", text) is not None

