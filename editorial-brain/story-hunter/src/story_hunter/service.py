"""Story Hunter service."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from time import perf_counter
from typing import Any

from .config import StoryHunterConfig
from .errors import LLMError, PromptLoadError, ValidationError
from .json_utils import load_json_file, parse_json_object
from .llm import LLMClient
from .logging_utils import StructuredLogger
from .prompt_loader import PromptLoader
from .validation import StoryHunterValidator


class StoryHunterService:
    """Runs the Story Hunter agent for approved Match Selection and Daily Input."""

    def __init__(
        self,
        config: StoryHunterConfig,
        llm_client: LLMClient,
        validator: StoryHunterValidator | None = None,
        logger: StructuredLogger | None = None,
    ):
        self.config = config
        self.llm_client = llm_client
        self.validator = validator or StoryHunterValidator(
            config.daily_input_schema_path,
            config.match_selection_schema_path,
            config.output_schema_path,
            config.minimum_confidence,
        )
        self.logger = logger or StructuredLogger(config.log_directory)
        self.prompt_loader = PromptLoader(config.prompt_library_path)

    def run_from_files(self, daily_input_path, match_selection_path) -> dict[str, Any]:
        daily_input = load_json_file(daily_input_path)
        match_selection = load_json_file(match_selection_path)
        return self.run(daily_input, match_selection)

    def run(self, daily_input: dict[str, Any], match_selection: dict[str, Any]) -> dict[str, Any]:
        production_id = match_selection.get(
            "production_id",
            daily_input.get("production_metadata", {}).get("production_id", ""),
        )
        try:
            self.validator.validate_inputs(daily_input, match_selection)
            base_prompt = self._build_prompt(daily_input, match_selection)
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
                self.validator.validate_output(parsed, match_selection)
                duration_ms = int((perf_counter() - start) * 1000)
                self._log_attempt(
                    production_id,
                    attempt,
                    start_time,
                    duration_ms,
                    parsed,
                    warnings=parsed.get("warnings", []),
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
            code="STORY_HUNTER_VALIDATION_FAILED",
            message="Story Hunter failed after retry",
            issues=last_issues,
            retryable=False,
            attempts=attempts_allowed,
        )

    def _build_prompt(self, daily_input: dict[str, Any], match_selection: dict[str, Any]) -> str:
        prompt = self.prompt_loader.load_story_hunter_prompt()
        context = daily_input.get("match_context", {})
        variables = {
            "selected_match_json": json.dumps(match_selection.get("selected_match", {}), ensure_ascii=True),
            "match_context_json": json.dumps(context, ensure_ascii=True),
            "recent_form_json": json.dumps(context.get("recent_form", {}), ensure_ascii=True),
            "squad_availability_json": json.dumps(context.get("squad_availability", {}), ensure_ascii=True),
            "tactical_notes_json": json.dumps(context.get("tactical_notes", {}), ensure_ascii=True),
            "head_to_head_json": json.dumps(context.get("head_to_head", {}), ensure_ascii=True),
            "statistics_json": json.dumps(context.get("statistics", {}), ensure_ascii=True),
            "news_json": json.dumps(context.get("news", {}), ensure_ascii=True),
            "betting_market_json": json.dumps(context.get("betting_market_optional", {}), ensure_ascii=True),
            "audience_notes_json": json.dumps(daily_input.get("audience_notes", {}), ensure_ascii=True),
        }
        rendered = PromptLoader.render(prompt, variables)
        return (
            rendered
            + "\n\nApproved Match Selection JSON:\n"
            + json.dumps(match_selection, ensure_ascii=True)
            + "\n\nReturn only the Story Hunter JSON object."
        )

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
                "stage_id": "stage-02-story-hunter",
                "agent_id": "IF-A02",
                "agent_name": "Story Hunter",
                "production_id": production_id,
                "attempt": attempt,
                "start_time": start_time,
                "end_time": datetime.now(timezone.utc).isoformat(),
                "duration_ms": duration_ms,
                "confidence": output.get("story_confidence"),
                "warnings": warnings,
                "errors": errors,
                "approval_status": output.get("approval_status", "failed" if errors else "approved"),
                "next_agent": output.get("next_agent", "IF-A03"),
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
            "agent_id": "IF-A02",
            "agent_name": "Story Hunter",
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
