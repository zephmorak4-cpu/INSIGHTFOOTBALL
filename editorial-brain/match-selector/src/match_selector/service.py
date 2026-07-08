"""Match Selector service."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any

from .config import MatchSelectorConfig
from .errors import LLMError, PromptLoadError, ValidationError
from .json_utils import load_json_file, parse_json_object
from .llm import LLMClient
from .logging_utils import StructuredLogger
from .prompt_loader import PromptLoader
from .validation import MatchSelectorValidator


class MatchSelectorService:
    """Runs the Match Selector agent for one Daily Input JSON file."""

    def __init__(
        self,
        config: MatchSelectorConfig,
        llm_client: LLMClient,
        validator: MatchSelectorValidator | None = None,
        logger: StructuredLogger | None = None,
    ):
        self.config = config
        self.llm_client = llm_client
        self.validator = validator or MatchSelectorValidator(
            config.input_schema_path,
            config.output_schema_path,
            config.minimum_confidence,
        )
        self.logger = logger or StructuredLogger(config.log_directory)
        self.prompt_loader = PromptLoader(config.prompt_library_path)

    def run_from_file(self, daily_input_path: Path) -> dict[str, Any]:
        daily_input = load_json_file(daily_input_path)
        return self.run(daily_input)

    def run(self, daily_input: dict[str, Any]) -> dict[str, Any]:
        production_id = daily_input.get("production_metadata", {}).get("production_id", "")
        try:
            self.validator.validate_daily_input(daily_input)
            base_prompt = self._build_prompt(daily_input)
        except (ValidationError, PromptLoadError) as exc:
            return self._structured_error(
                production_id=production_id,
                code=exc.__class__.__name__,
                message=str(exc),
                issues=getattr(exc, "issues", [str(exc)]),
                retryable=False,
                attempts=0,
            )

        last_issues: list[str] = []
        attempts_allowed = self.config.max_retries + 1
        for attempt in range(1, attempts_allowed + 1):
            prompt = base_prompt if attempt == 1 else self._retry_prompt(base_prompt, last_issues)
            start = perf_counter()
            start_time = datetime.now(timezone.utc).isoformat()
            try:
                raw_response = self.llm_client.generate(
                    prompt,
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens,
                )
                parsed = parse_json_object(raw_response)
                self.validator.validate_output(parsed, daily_input)
                duration_ms = int((perf_counter() - start) * 1000)
                self._log_attempt(
                    production_id,
                    attempt,
                    start_time,
                    duration_ms,
                    parsed,
                    warnings=parsed.get("data_gaps", []),
                    errors=[],
                )
                return parsed
            except (LLMError, ValueError, json.JSONDecodeError, ValidationError) as exc:
                duration_ms = int((perf_counter() - start) * 1000)
                last_issues = getattr(exc, "issues", [str(exc)])
                self._log_attempt(
                    production_id,
                    attempt,
                    start_time,
                    duration_ms,
                    {},
                    warnings=[],
                    errors=last_issues,
                )

        return self._structured_error(
            production_id=production_id,
            code="MATCH_SELECTOR_VALIDATION_FAILED",
            message="Match Selector failed after retry",
            issues=last_issues,
            retryable=False,
            attempts=attempts_allowed,
        )

    def _build_prompt(self, daily_input: dict[str, Any]) -> str:
        prompt = self.prompt_loader.load_match_selector_prompt()
        metadata = daily_input.get("production_metadata", {})
        variables = {
            "production_metadata_json": json.dumps(metadata, ensure_ascii=True),
            "fixtures_json": json.dumps(daily_input.get("fixtures", []), ensure_ascii=True),
            "audience_notes_json": json.dumps(daily_input.get("audience_notes", {}), ensure_ascii=True),
            "priority_competitions_json": json.dumps(daily_input.get("priority_competitions", []), ensure_ascii=True),
            "data_availability_notes_json": json.dumps(daily_input.get("data_availability_notes", {}), ensure_ascii=True),
        }
        rendered = PromptLoader.render(prompt, variables)
        return rendered + "\n\nReturn only the Match Selector JSON object."

    @staticmethod
    def _retry_prompt(base_prompt: str, issues: list[str]) -> str:
        return (
            base_prompt
            + "\n\nYour previous response failed validation. Fix these issues and return valid JSON only:\n"
            + json.dumps(issues, ensure_ascii=True)
        )

    def _log_attempt(
        self,
        production_id: str,
        attempt: int,
        start_time: str,
        duration_ms: int,
        output: dict[str, Any],
        warnings: list[str],
        errors: list[str],
    ) -> None:
        self.logger.log(
            {
                "stage_id": "stage-01-match-selector",
                "agent_id": "IF-A01",
                "agent_name": "Match Selector",
                "production_id": production_id,
                "attempt": attempt,
                "start_time": start_time,
                "end_time": datetime.now(timezone.utc).isoformat(),
                "duration_ms": duration_ms,
                "confidence": output.get("confidence", {}).get("score"),
                "warnings": warnings,
                "errors": errors,
                "approval_status": output.get("approval_status", "failed" if errors else "approved"),
                "next_agent": output.get("next_agent", "IF-A02"),
            }
        )

    @staticmethod
    def _structured_error(
        *,
        production_id: str,
        code: str,
        message: str,
        issues: list[str],
        retryable: bool,
        attempts: int,
    ) -> dict[str, Any]:
        return {
            "success": False,
            "agent_id": "IF-A01",
            "agent_name": "Match Selector",
            "production_id": production_id,
            "error": {
                "code": code,
                "message": message,
                "issues": issues,
                "retryable": retryable,
                "attempts": attempts,
            },
            "approval_status": "blocked",
            "next_agent": None,
        }
