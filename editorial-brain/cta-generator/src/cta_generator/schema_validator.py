"""Small JSON schema validator."""

from __future__ import annotations

from typing import Any


class SchemaValidator:
    def validate(self, data: dict[str, Any], schema: dict[str, Any]) -> list[str]:
        issues: list[str] = []
        for field in schema.get("required", []):
            if field not in data:
                issues.append(f"$.{field}: required")
        for key, child_schema in schema.get("properties", {}).items():
            if key not in data:
                continue
            expected = child_schema.get("type")
            if expected and not _type_ok(data[key], expected):
                issues.append(f"$.{key}: expected {expected}")
            if "enum" in child_schema and data[key] not in child_schema["enum"]:
                issues.append(f"$.{key}: expected one of {child_schema['enum']}")
        return issues


def _type_ok(value: Any, expected: str) -> bool:
    return {
        "object": isinstance(value, dict),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "number": isinstance(value, (int, float)) and not isinstance(value, bool),
        "boolean": isinstance(value, bool),
    }.get(expected, True)

