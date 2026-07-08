"""Minimal schema validator."""

from __future__ import annotations

from typing import Any


class SchemaValidator:
    def validate(self, data: dict[str, Any], schema: dict[str, Any]) -> list[str]:
        issues: list[str] = []
        for field in schema.get("required", []):
            if field not in data:
                issues.append(f"$.{field}: required")
        for key, child_schema in schema.get("properties", {}).items():
            if key in data and child_schema.get("type") and not _ok(data[key], child_schema["type"]):
                issues.append(f"$.{key}: expected {child_schema['type']}")
        return issues


def _ok(value: Any, expected: str) -> bool:
    return {
        "object": isinstance(value, dict),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "number": isinstance(value, (int, float)) and not isinstance(value, bool),
        "boolean": isinstance(value, bool),
    }.get(expected, True)

