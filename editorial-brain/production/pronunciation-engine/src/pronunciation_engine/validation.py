from __future__ import annotations

from typing import Any


class PronunciationEngineValidator:
    def validate_inputs(self, script_package: dict[str, Any], voice_plan: dict[str, Any]) -> list[str]:
        issues = []
        if not script_package.get("final_voiceover"):
            issues.append("$.final_voiceover: required")
        if not voice_plan.get("sections"):
            issues.append("$.voice_plan.sections: required")
        if script_package.get("production_id") != voice_plan.get("production_id"):
            issues.append("$.production_id: script and voice plan must match")
        return issues

    def validate_output(self, dictionary: dict[str, Any]) -> list[str]:
        issues = []
        if not dictionary.get("items"):
            issues.append("$.items: pronunciation entries required")
        terms = [item.get("term", "").lower() for item in dictionary.get("items", [])]
        for required in ["liverpool", "arsenal", "premier league"]:
            if required not in terms:
                issues.append(f"$.items: missing required football term {required}")
        for item in dictionary.get("items", []):
            for field in ["term", "phonetic", "language", "notes"]:
                if not item.get(field):
                    issues.append(f"{item.get('term', '<unknown>')}.{field}: required")
        return issues
