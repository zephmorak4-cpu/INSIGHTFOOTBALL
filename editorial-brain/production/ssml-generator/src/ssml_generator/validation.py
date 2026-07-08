from __future__ import annotations

from typing import Any
from xml.etree import ElementTree


class SSMLGeneratorValidator:
    def validate_inputs(self, script_package: dict[str, Any], voice_plan: dict[str, Any], dictionary: dict[str, Any]) -> list[str]:
        issues = []
        if script_package.get("production_id") != voice_plan.get("production_id"):
            issues.append("$.production_id: script and voice plan must match")
        if script_package.get("production_id") != dictionary.get("production_id"):
            issues.append("$.production_id: script and pronunciation dictionary must match")
        if not dictionary.get("items"):
            issues.append("$.pronunciation_dictionary.items: required")
        return issues

    def validate_ssml(self, ssml: str) -> list[str]:
        try:
            root = ElementTree.fromstring(ssml)
        except ElementTree.ParseError as exc:
            return [f"voice.ssml: invalid XML: {exc}"]
        if root.tag != "speak":
            return ["voice.ssml: root element must be speak"]
        return []

    def validate_metadata(self, metadata: dict[str, Any]) -> list[str]:
        issues = []
        if metadata.get("sentence_count", 0) <= 0:
            issues.append("$.sentence_count: must be positive")
        if "break" not in metadata.get("supported_tags_used", []):
            issues.append("$.supported_tags_used: break tag required")
        return issues
