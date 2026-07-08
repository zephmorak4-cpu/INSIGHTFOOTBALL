"""Small JSON Schema validator for Evidence Filter schemas."""

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
            properties = schema.get("properties", {})
            for key, child_schema in properties.items():
                if key in data:
                    self._validate_node(data[key], child_schema, f"{path}.{key}", issues)

        if isinstance(data, list):
            min_items = schema.get("minItems")
            max_items = schema.get("maxItems")
            if min_items is not None and len(data) < int(min_items):
                issues.append(f"{path}: expected at least {min_items} items")
            if max_items is not None and len(data) > int(max_items):
                issues.append(f"{path}: expected at most {max_items} items")
            item_schema = schema.get("items")
            if isinstance(item_schema, dict):
                for index, item in enumerate(data):
                    self._validate_node(item, item_schema, f"{path}[{index}]", issues)

        if isinstance(data, (int, float)) and not isinstance(data, bool):
            minimum = schema.get("minimum")
            maximum = schema.get("maximum")
            if minimum is not None and data < minimum:
                issues.append(f"{path}: expected >= {minimum}")
            if maximum is not None and data > maximum:
                issues.append(f"{path}: expected <= {maximum}")

        if isinstance(data, str):
            min_length = schema.get("minLength")
            if min_length is not None and len(data) < int(min_length):
                issues.append(f"{path}: expected string length >= {min_length}")

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
