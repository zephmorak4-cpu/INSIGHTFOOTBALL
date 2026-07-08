"""Small JSON schema validator for Sprint 3 schemas."""

from __future__ import annotations

from typing import Any


class SchemaValidator:
    def validate(self, data: dict[str, Any], schema: dict[str, Any]) -> list[str]:
        return self._validate_object(data, schema, "$")

    def _validate_object(self, data: Any, schema: dict[str, Any], path: str) -> list[str]:
        issues: list[str] = []
        expected = schema.get("type")
        if expected and not _type_ok(data, expected):
            return [f"{path}: expected {expected}"]
        if not isinstance(data, dict):
            return issues
        for field in schema.get("required", []):
            if field not in data:
                issues.append(f"{path}.{field}: required")
        for key, child_schema in schema.get("properties", {}).items():
            if key not in data:
                continue
            child = data[key]
            child_path = f"{path}.{key}"
            child_type = child_schema.get("type")
            if child_type and not _type_ok(child, child_type):
                issues.append(f"{child_path}: expected {child_type}")
                continue
            if "enum" in child_schema and child not in child_schema["enum"]:
                issues.append(f"{child_path}: expected one of {child_schema['enum']}")
            if child_schema.get("type") == "object":
                issues.extend(self._validate_object(child, child_schema, child_path))
            if child_schema.get("type") == "array" and not isinstance(child, list):
                issues.append(f"{child_path}: expected array")
        return issues


def _type_ok(value: Any, expected: str) -> bool:
    checks = {
        "object": isinstance(value, dict),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "number": isinstance(value, (int, float)) and not isinstance(value, bool),
        "boolean": isinstance(value, bool),
    }
    return checks.get(expected, True)

