"""Small JSON Schema validator for Insight Engine schemas."""

from __future__ import annotations

from typing import Any


class SchemaValidator:
    """Validates the subset of JSON Schema used by the Sprint 1 modules."""

    def validate(self, data: Any, schema: dict[str, Any]) -> list[str]:
        issues: list[str] = []
        self._validate_node(data, schema, "$", issues)
        return issues

    def _validate_node(self, data: Any, schema: dict[str, Any], path: str, issues: list[str]) -> None:
        expected_type = schema.get("type")
        if expected_type and not self._matches_type(data, expected_type):
            issues.append(f"{path}: expected {expected_type}, got {type(data).__name__}")
            return
        if "enum" in schema and data not in schema["enum"]:
            issues.append(f"{path}: value {data!r} not in enum {schema['enum']!r}")
        if isinstance(data, dict):
            for required in schema.get("required", []):
                if required not in data:
                    issues.append(f"{path}: missing required field {required}")
            for key, child_schema in schema.get("properties", {}).items():
                if key in data:
                    self._validate_node(data[key], child_schema, f"{path}.{key}", issues)
        if isinstance(data, list):
            if "minItems" in schema and len(data) < int(schema["minItems"]):
                issues.append(f"{path}: expected at least {schema['minItems']} items")
            if "maxItems" in schema and len(data) > int(schema["maxItems"]):
                issues.append(f"{path}: expected at most {schema['maxItems']} items")
            if isinstance(schema.get("items"), dict):
                for index, item in enumerate(data):
                    self._validate_node(item, schema["items"], f"{path}[{index}]", issues)
        if isinstance(data, (int, float)) and not isinstance(data, bool):
            if "minimum" in schema and data < schema["minimum"]:
                issues.append(f"{path}: expected >= {schema['minimum']}")
            if "maximum" in schema and data > schema["maximum"]:
                issues.append(f"{path}: expected <= {schema['maximum']}")
        if isinstance(data, str) and "minLength" in schema and len(data) < int(schema["minLength"]):
            issues.append(f"{path}: expected string length >= {schema['minLength']}")

    @staticmethod
    def _matches_type(data: Any, expected_type: str) -> bool:
        if expected_type == "object":
            return isinstance(data, dict)
        if expected_type == "array":
            return isinstance(data, list)
        if expected_type == "string":
            return isinstance(data, str)
        if expected_type == "integer":
            return isinstance(data, int) and not isinstance(data, bool)
        if expected_type == "number":
            return isinstance(data, (int, float)) and not isinstance(data, bool)
        if expected_type == "boolean":
            return isinstance(data, bool)
        return True
