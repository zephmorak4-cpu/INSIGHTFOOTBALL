"""Editorial Validator service."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import re
from typing import Any

from .config import EditorialValidatorConfig
from .json_utils import load_json_file, write_json_file
from .logging_utils import ComponentLogger
from .schema_validator import SchemaValidator


BETTING_TERMS = ["guaranteed", "sure win", "banker", "lock", "bet of the day", "risk-free", "100 percent", "definitely"]
GENERIC_STORY_TERMS = ["match preview", "both teams want to win", "exciting game", "good form", "needs points"]
UNSUPPORTED_TERMS = ["injury", "weather", "red card", "suspension"]


class EditorialValidatorService:
    def __init__(self, config: EditorialValidatorConfig):
        self.config = config
        self.schema_validator = SchemaValidator()
        self.input_schema = load_json_file(config.input_schema)
        self.output_schema = load_json_file(config.output_schema)
        self.validated_package_schema = load_json_file(config.validated_package_schema)

    def run_from_file(self, package_path: Path) -> dict[str, Any]:
        return self.run(load_json_file(package_path))

    def run(self, package: dict[str, Any]) -> dict[str, Any]:
        production_id = package.get("metadata", {}).get("production_id", "unknown-production")
        logger = ComponentLogger(self.config.log_directory, production_id)
        logger.log({"event": "validation_started", "production_id": production_id})
        report = self._validate(package)
        report_issues = self.schema_validator.validate(report, self.output_schema)
        if report_issues:
            report["validation_status"] = "failed"
            report["approval_status"] = "rejected"
            report["issues_found"].extend(report_issues)
            report["required_fixes"].append("Fix validation report schema.")
        report_path = self.config.output_directory / f"validation-report-{production_id}.json"
        write_json_file(report_path, report)
        logger.log({"event": "validation_report_written", "status": report["validation_status"], "report_path": str(report_path)})

        if report["approval_status"] == "approved":
            validated = dict(package)
            validated["validation_metadata"] = {
                "validator_id": self.config.component_id,
                "validator_name": self.config.component_name,
                "timestamp": report["timestamp"],
                "report_path": str(report_path),
            }
            validated["approval_status"] = "approved"
            validated["validator_notes"] = report["warnings"]
            validated["publishability_score"] = report["overall_score"]
            issues = self.schema_validator.validate(validated, self.validated_package_schema)
            if issues:
                report["validation_status"] = "failed"
                report["approval_status"] = "rejected"
                report["issues_found"].extend(issues)
                write_json_file(report_path, report)
                return {"success": False, "report": report, "report_path": str(report_path)}
            validated_path = self.config.output_directory / f"validated-editorial-package-{production_id}.json"
            write_json_file(validated_path, validated)
            logger.log({"event": "validated_package_written", "validated_package_path": str(validated_path)})
            return {"success": True, "validated_package": validated, "validated_package_path": str(validated_path), "report": report, "report_path": str(report_path)}

        return {"success": False, "report": report, "report_path": str(report_path)}

    def _validate(self, package: dict[str, Any]) -> dict[str, Any]:
        production_id = package.get("metadata", {}).get("production_id", "")
        issues = self.schema_validator.validate(package, self.input_schema)
        required_fixes: list[str] = []
        warnings: list[str] = []
        human_flags: list[str] = []

        story = package.get("story_angle", "")
        question = package.get("central_question", "")
        fact = package.get("surprising_fact", "")
        editorial_text = " ".join(
            str(package.get(field, ""))
            for field in [
                "story_angle",
                "central_question",
                "surprising_fact",
                "insight_summary",
                "match_edge",
                "key_advantage",
                "tactical_explanation",
                "uncertainty_summary",
                "x_factor",
                "viewer_takeaway",
                "editorial_notes",
            ]
        ).lower()
        combined = editorial_text
        source_text = str(package.get("agent_outputs", {})).lower()

        if not question:
            issues.append("central_question is missing")
            required_fixes.append("Add one clear central question.")
        if any(term in story.lower() for term in GENERIC_STORY_TERMS):
            issues.append("story_angle is generic")
            required_fixes.append("Return to Story Hunter for a sharper story angle.")
        if len(fact.split()) < 8:
            issues.append("surprising_fact is weak")
            required_fixes.append("Strengthen or verify the surprising fact.")
        if not package.get("primary_evidence"):
            issues.append("primary evidence is missing")
            required_fixes.append("Return to Evidence Filter.")
        if not package.get("contradictory_evidence"):
            issues.append("contradictory evidence is missing")
            required_fixes.append("Surface relevant contradiction or explain none found.")
        if "%" in str(package.get("match_edge", "")):
            issues.append("match_edge uses probabilities")
            required_fixes.append("Use edge labels only.")
        for term in BETTING_TERMS:
            if _contains_phrase(combined, term):
                issues.append(f"betting language appears: {term}")
                required_fixes.append("Remove betting language.")
        for term in UNSUPPORTED_TERMS:
            if term in combined and term not in source_text:
                issues.append(f"unsupported claim appears: {term}")
                required_fixes.append("Remove unsupported claim or add source evidence.")

        locked = package.get("locked_fields", {})
        for field in ["story_angle", "central_question", "surprising_fact"]:
            if locked.get(field) != package.get(field):
                issues.append(f"locked field mismatch: {field}")
                required_fixes.append("Restore locked field from Editorial Brain output.")

        confidence = package.get("confidence_scores", {})
        low = {k: v for k, v in confidence.items() if isinstance(v, (int, float)) and k != "overall" and v < self.config.confidence_threshold}
        if low:
            issues.append(f"confidence below threshold: {low}")
            required_fixes.append("Return to the weak module output for revision.")

        story_score = _score_text(story, 20)
        evidence_score = 85 if package.get("primary_evidence") and package.get("contradictory_evidence") else 55
        clarity_score = 85 if len(question.split()) >= 5 and question.endswith("?") else 50
        insight_score = _score_text(package.get("insight_summary", ""), 18)
        brand_safety_score = 50 if any(_contains_phrase(combined, term) for term in BETTING_TERMS) else 90
        overall = round((story_score + evidence_score + clarity_score + insight_score + brand_safety_score) / 5, 2)

        if package.get("warnings"):
            warnings.extend(package["warnings"])
            human_flags.append("FACT_CHECK_REQUIRED")
        if issues:
            status = "failed"
            approval = "rejected"
            next_component = None
        elif overall < self.config.publishability_threshold:
            status = "needs_human_review"
            approval = "needs_human_review"
            human_flags.append("HUMAN_EDITOR_DECISION")
            next_component = None
        elif human_flags:
            status = "needs_human_review"
            approval = "needs_human_review"
            next_component = None
        else:
            status = "approved"
            approval = "approved"
            next_component = self.config.next_component

        return {
            "production_id": production_id,
            "validator_id": self.config.component_id,
            "validator_name": self.config.component_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "input_package_version": package.get("metadata", {}).get("package_version", "unknown"),
            "validation_status": status,
            "overall_score": overall,
            "story_score": story_score,
            "evidence_score": evidence_score,
            "clarity_score": clarity_score,
            "insight_score": insight_score,
            "brand_safety_score": brand_safety_score,
            "issues_found": sorted(set(issues)),
            "required_fixes": sorted(set(required_fixes)),
            "warnings": sorted(set(warnings)),
            "human_review_flags": sorted(set(human_flags)),
            "approval_status": approval,
            "next_component": next_component,
        }


def _score_text(text: str, min_words: int) -> int:
    words = len(str(text).split())
    if words >= min_words:
        return 85
    if words >= max(8, min_words // 2):
        return 72
    return 50


def _contains_phrase(text: str, phrase: str) -> bool:
    return re.search(rf"\b{re.escape(phrase)}\b", text) is not None
