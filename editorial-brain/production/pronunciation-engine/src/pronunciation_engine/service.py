from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import PronunciationEngineConfig
from .json_utils import load_json_file, write_json_file
from .logging_utils import StructuredLogger
from .validation import PronunciationEngineValidator


KNOWN_TERMS = {
    "Liverpool": ("LIV-er-pool", "club"),
    "Arsenal": ("AR-suh-nuhl", "club"),
    "Premier League": ("PREM-ee-er leeg", "competition"),
    "England": ("ING-glund", "country"),
    "Anfield": ("AN-feeld", "stadium"),
    "Arne Slot": ("AR-nuh slot", "manager"),
    "Mikel Arteta": ("mee-KEL ar-TET-uh", "manager"),
    "x-factor": ("EKS fak-ter", "football phrase"),
    "xG": ("EKS jee", "abbreviation"),
    "VAR": ("vee-ay-AR", "abbreviation"),
    "CTA": ("see-tee-AY", "production abbreviation"),
}


class PronunciationEngineService:
    def __init__(self, config: PronunciationEngineConfig):
        self.config = config
        self.validator = PronunciationEngineValidator()

    def run_from_files(self, script_package_path: Path, voice_plan_path: Path) -> dict[str, Any]:
        return self.run(load_json_file(script_package_path), load_json_file(voice_plan_path))

    def run(self, script_package: dict[str, Any], voice_plan: dict[str, Any]) -> dict[str, Any]:
        production_id = script_package.get("production_id", "unknown-production")
        logger = StructuredLogger(self.config.log_directory, f"pronunciation-engine-{production_id}")
        issues = self.validator.validate_inputs(script_package, voice_plan)
        dictionary = _build_dictionary(script_package, voice_plan, self.config)
        issues.extend(self.validator.validate_output(dictionary))
        if issues:
            logger.log({"event": "pronunciation_failed", "issues": issues})
            return {"success": False, "error": {"code": "PRONUNCIATION_FAILED", "issues": issues}, "pronunciation_dictionary": dictionary}
        path = self.config.output_directory / "pronunciation_dictionary.json"
        write_json_file(path, dictionary)
        logger.log({"event": "pronunciation_dictionary_written", "output_path": str(path), "terms": len(dictionary["items"])})
        return {"success": True, "pronunciation_dictionary": dictionary, "pronunciation_dictionary_path": str(path)}


def _build_dictionary(script: dict[str, Any], voice_plan: dict[str, Any], config: PronunciationEngineConfig) -> dict[str, Any]:
    text = " ".join([script.get("final_voiceover", ""), str(script.get("match", {})), str(script.get("locked_fields", {}))])
    terms = set()
    match = script.get("match", {})
    for value in [match.get("home_team"), match.get("away_team"), match.get("competition"), match.get("country")]:
        if value:
            terms.add(str(value))
    for known in KNOWN_TERMS:
        if re.search(rf"\b{re.escape(known)}\b", text, flags=re.IGNORECASE):
            terms.add(known)
    items = []
    for term in sorted(terms, key=str.lower):
        phonetic, note = KNOWN_TERMS.get(term, _fallback(term))
        items.append({"term": term, "phonetic": phonetic, "language": "en-GB", "notes": note})
    return {
        "production_id": script["production_id"],
        "component_id": config.component_id,
        "component_name": config.component_name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source_voice_plan": voice_plan.get("production_id", ""),
        "phonetic_standard": config.phonetic_standard,
        "supported_languages": config.supported_languages,
        "items": items,
        "warnings": [],
        "approval_status": "approved",
        "next_component": config.next_component,
    }


def _fallback(term: str) -> tuple[str, str]:
    phonetic = "-".join(part.upper() if len(part) <= 3 else part for part in term.split())
    return phonetic, "fallback phonetic spelling; review recommended"
