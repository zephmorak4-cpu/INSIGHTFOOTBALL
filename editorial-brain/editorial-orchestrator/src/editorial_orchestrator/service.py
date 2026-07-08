"""Editorial Orchestrator service."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any

from .config import OrchestratorConfig
from .errors import ValidationError
from .json_utils import load_json_file, write_json_file
from .logging_utils import ExecutionLogger
from .module_loader import ensure_editorial_module_paths
from .package_assembler import assemble_editorial_package
from .validation import OrchestratorValidator


class EditorialOrchestrator:
    """Executes the four Editorial Brain modules and assembles one package."""

    def __init__(self, config: OrchestratorConfig, workspace_root: Path | None = None):
        self.config = config
        self.workspace_root = workspace_root or Path.cwd()
        ensure_editorial_module_paths(self.workspace_root)
        self.validator = OrchestratorValidator(config.package_schema_path, config.minimum_confidence)

    def run_from_file(self, daily_input_path: Path) -> dict[str, Any]:
        return self.run(load_json_file(daily_input_path))

    def run(self, daily_input: dict[str, Any]) -> dict[str, Any]:
        production_id = daily_input.get("production_metadata", {}).get("production_id", "unknown-production")
        logger = ExecutionLogger(self.config.log_directory, production_id)
        pipeline_start = perf_counter()
        stage_reports: list[dict[str, Any]] = []

        try:
            match_selection = self._run_stage("match_selector", daily_input, None, None, None, logger, stage_reports)
            self.validator.validate_stage_output(match_selection, "IF-A01", ("confidence", "score"))

            story_hunter = self._run_stage("story_hunter", daily_input, match_selection, None, None, logger, stage_reports)
            self.validator.validate_stage_output(story_hunter, "IF-A02", ("story_confidence",))

            evidence_filter = self._run_stage("evidence_filter", daily_input, match_selection, story_hunter, None, logger, stage_reports)
            self.validator.validate_stage_output(evidence_filter, "IF-A03", ("evidence_confidence",))

            insight_engine = self._run_stage("insight_engine", daily_input, match_selection, story_hunter, evidence_filter, logger, stage_reports)
            self.validator.validate_stage_output(insight_engine, "IF-A04", ("confidence", "score"))

            self.validator.validate_locked_fields(
                story_hunter=story_hunter,
                evidence_filter=evidence_filter,
                insight_engine=insight_engine,
            )

            execution_metadata = {
                "started_at": stage_reports[0]["start_time"] if stage_reports else datetime.now(timezone.utc).isoformat(),
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "duration_ms": int((perf_counter() - pipeline_start) * 1000),
                "stages": stage_reports,
            }
            package = assemble_editorial_package(
                daily_input=daily_input,
                match_selection=match_selection,
                story_hunter=story_hunter,
                evidence_filter=evidence_filter,
                insight_engine=insight_engine,
                execution_metadata=execution_metadata,
            )
            self.validator.validate_package(package)

            package_path = self.config.output_directory / f"editorial-package-{production_id}.json"
            report = self._build_report(production_id, "success", stage_reports, package_path, None, pipeline_start)
            report_path = self.config.output_directory / f"execution-report-{production_id}.json"
            write_json_file(package_path, package)
            write_json_file(report_path, report)
            logger.log({"event": "orchestrator_complete", "status": "success", "package_path": str(package_path), "report_path": str(report_path)})
            return {"success": True, "package_path": str(package_path), "report_path": str(report_path), "package": package, "report": report}
        except ValidationError as exc:
            report = self._build_report(production_id, "failed", stage_reports, None, exc.issues, pipeline_start)
            report_path = self.config.output_directory / f"execution-report-{production_id}.json"
            write_json_file(report_path, report)
            logger.log({"event": "orchestrator_failed", "status": "failed", "issues": exc.issues, "report_path": str(report_path)})
            return {
                "success": False,
                "error": {
                    "code": "EDITORIAL_ORCHESTRATOR_FAILED",
                    "message": str(exc),
                    "issues": exc.issues,
                },
                "report_path": str(report_path),
                "report": report,
            }

    def _run_stage(
        self,
        stage_name: str,
        daily_input: dict[str, Any],
        match_selection: dict[str, Any] | None,
        story_hunter: dict[str, Any] | None,
        evidence_filter: dict[str, Any] | None,
        logger: ExecutionLogger,
        stage_reports: list[dict[str, Any]],
    ) -> dict[str, Any]:
        start = perf_counter()
        start_time = datetime.now(timezone.utc).isoformat()
        output = self._execute_stage(stage_name, daily_input, match_selection, story_hunter, evidence_filter)
        duration_ms = int((perf_counter() - start) * 1000)
        report = {
            "stage": stage_name,
            "agent_id": output.get("agent_id"),
            "start_time": start_time,
            "end_time": datetime.now(timezone.utc).isoformat(),
            "duration_ms": duration_ms,
            "confidence": _stage_confidence(output),
            "warnings": _stage_warnings(output),
            "errors": output.get("error", {}).get("issues", []),
            "approval_status": output.get("approval_status"),
            "next_agent": output.get("next_agent"),
        }
        stage_reports.append(report)
        logger.log({"event": "stage_complete", **report})
        return output

    def _execute_stage(
        self,
        stage_name: str,
        daily_input: dict[str, Any],
        match_selection: dict[str, Any] | None,
        story_hunter: dict[str, Any] | None,
        evidence_filter: dict[str, Any] | None,
    ) -> dict[str, Any]:
        if stage_name == "match_selector":
            from match_selector.config import load_config as load_ms_config
            from match_selector.llm import RuleBasedMatchSelectorClient
            from match_selector.service import MatchSelectorService

            module_config = load_ms_config(self.config.match_selector_config_path)
            return MatchSelectorService(module_config, RuleBasedMatchSelectorClient(daily_input)).run(daily_input)
        if stage_name == "story_hunter":
            from story_hunter.config import load_config as load_sh_config
            from story_hunter.llm import RuleBasedStoryHunterClient
            from story_hunter.service import StoryHunterService

            module_config = load_sh_config(self.config.story_hunter_config_path)
            return StoryHunterService(module_config, RuleBasedStoryHunterClient(daily_input, match_selection)).run(daily_input, match_selection)
        if stage_name == "evidence_filter":
            from evidence_filter.config import load_config as load_ef_config
            from evidence_filter.llm import RuleBasedEvidenceFilterClient
            from evidence_filter.service import EvidenceFilterService

            module_config = load_ef_config(self.config.evidence_filter_config_path)
            return EvidenceFilterService(module_config, RuleBasedEvidenceFilterClient(daily_input, match_selection, story_hunter)).run(daily_input, match_selection, story_hunter)
        if stage_name == "insight_engine":
            from insight_engine.config import load_config as load_ie_config
            from insight_engine.llm import RuleBasedInsightEngineClient
            from insight_engine.service import InsightEngineService

            module_config = load_ie_config(self.config.insight_engine_config_path)
            return InsightEngineService(module_config, RuleBasedInsightEngineClient(daily_input, match_selection, story_hunter, evidence_filter)).run(daily_input, match_selection, story_hunter, evidence_filter)
        raise ValidationError("Unknown stage", [stage_name])

    def _build_report(self, production_id: str, status: str, stages: list[dict[str, Any]], package_path: Path | None, issues: list[str] | None, pipeline_start: float) -> dict[str, Any]:
        return {
            "production_id": production_id,
            "status": status,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "duration_ms": int((perf_counter() - pipeline_start) * 1000),
            "stage_count": len(stages),
            "stages": stages,
            "package_path": str(package_path) if package_path else None,
            "issues": issues or [],
        }


def _stage_confidence(output: dict[str, Any]):
    if "confidence" in output and isinstance(output["confidence"], dict):
        return output["confidence"].get("score")
    return output.get("story_confidence") or output.get("evidence_confidence")


def _stage_warnings(output: dict[str, Any]) -> list[str]:
    warnings = []
    warnings.extend(output.get("warnings", []))
    warnings.extend(output.get("data_gaps", []))
    return warnings
