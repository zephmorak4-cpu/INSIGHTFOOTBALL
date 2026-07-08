"""Small JSON Schema validator."""

from __future__ import annotations

from typing import Any


class SchemaValidator:
    def validate(self, data: Any, schema: dict[str, Any]) -> list[str]:
        issues: list[str] = []
        self._node(data, schema, "$", issues)
        return issues

    def _node(self, data: Any, schema: dict[str, Any], path: str, issues: list[str]) -> None:
        typ = schema.get("type")
        if typ and not self._type_ok(data, typ):
            issues.append(f"{path}: expected {typ}, got {type(data).__name__}")
            return
        if "enum" in schema and data not in schema["enum"]:
            issues.append(f"{path}: value {data!r} not in enum {schema['enum']!r}")
        if isinstance(data, dict):
            for key in schema.get("required", []):
                if key not in data:
                    issues.append(f"{path}: missing required field {key}")
            for key, child in schema.get("properties", {}).items():
                if key in data:
                    self._node(data[key], child, f"{path}.{key}", issues)
        if isinstance(data, list):
            if "minItems" in schema and len(data) < int(schema["minItems"]):
                issues.append(f"{path}: expected at least {schema['minItems']} items")
        if isinstance(data, str) and "minLength" in schema and len(data) < int(schema["minLength"]):
            issues.append(f"{path}: expected string length >= {schema['minLength']}")

    @staticmethod
    def _type_ok(data: Any, typ: str) -> bool:
        return (
            (typ == "object" and isinstance(data, dict))
            or (typ == "array" and isinstance(data, list))
            or (typ == "string" and isinstance(data, str))
            or (typ == "integer" and isinstance(data, int) and not isinstance(data, bool))
            or (typ == "number" and isinstance(data, (int, float)) and not isinstance(data, bool))
            or (typ == "boolean" and isinstance(data, bool))
        )
