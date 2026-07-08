"""Scriptwriter service."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from time import perf_counter
from pathlib import Path
from typing import Any

from .config import ScriptwriterConfig
from .errors import LLMError, ValidationError
from .json_utils import load_json_file, parse_json_object, write_json_file, write_text_file
from .llm import LLMClient
from .logging_utils import StructuredLogger
from .prompt_loader import PromptLoader
from .validation import ScriptwriterValidator


class ScriptwriterService:
    def __init__(self, config: ScriptwriterConfig, llm_client: LLMClient):
        self.config = config
        self.llm_client = llm_client
        self.validator = ScriptwriterValidator(
            config.input_schema,
            config.output_schema,
            config.min_words,
            config.max_words,
            config.target_duration_seconds,
        )
        self.prompt_loader = PromptLoader(config.prompt_path)

    def run_from_file(self, brief_path: Path) -> dict[str, Any]:
        return self.run(load_json_file(brief_path))

    def run(self, brief: dict[str, Any]) -> dict[str, Any]:
        production_id = brief.get("production_id", "unknown-production")
        logger = StructuredLogger(self.config.log_directory, f"scriptwriter-{production_id}")
        try:
            self.validator.validate_input(brief)
            base_prompt = self._build_prompt(brief)
        except ValidationError as exc:
            return self._error(production_id, "SCRIPTWRITER_INPUT_INVALID", exc.issues, 0)
        attempts_allowed = self.config.max_retries + 1
        last_issues: list[str] = []
        for attempt in range(1, attempts_allowed + 1):
            start = perf_counter()
            try:
                raw = self.llm_client.generate(base_prompt if attempt == 1 else self._retry_prompt(base_prompt, last_issues), temperature=self.config.temperature, max_tokens=self.config.max_tokens)
                output = parse_json_object(raw)
                self.validator.validate_output(output, brief)
                script_path = self.config.output_directory / f"script-output-{production_id}.json"
                voiceover_path = self.config.output_directory / f"voiceover-{production_id}.txt"
                write_json_file(script_path, output)
                write_text_file(voiceover_path, output["full_voiceover"])
                logger.log({"event": "scriptwriter_completed", "attempt": attempt, "duration_ms": int((perf_counter() - start) * 1000), "script_path": str(script_path), "voiceover_path": str(voiceover_path)})
                return {"success": True, "script": output, "script_path": str(script_path), "voiceover_path": str(voiceover_path)}
            except (LLMError, ValueError, json.JSONDecodeError, ValidationError) as exc:
                last_issues = getattr(exc, "issues", [str(exc)])
                logger.log({"event": "scriptwriter_attempt_failed", "attempt": attempt, "issues": last_issues})
        return self._error(production_id, "SCRIPTWRITER_VALIDATION_FAILED", last_issues, attempts_allowed)

    def _build_prompt(self, brief: dict[str, Any]) -> str:
        return self.prompt_loader.load() + "\n\nProduction Brief JSON:\n" + json.dumps(brief, ensure_ascii=True) + "\n\nReturn only script_output.json."

    @staticmethod
    def _retry_prompt(prompt: str, issues: list[str]) -> str:
        return prompt + "\n\nFix these validation issues and return JSON only:\n" + json.dumps(issues, ensure_ascii=True)

    @staticmethod
    def _error(production_id: str, code: str, issues: list[str], attempts: int) -> dict[str, Any]:
        return {
            "success": False,
            "agent_id": "IF-A05",
            "agent_name": "Scriptwriter",
            "production_id": production_id,
            "error": {"code": code, "message": "Scriptwriter failed", "issues": issues, "attempts": attempts},
            "approval_status": "blocked",
            "next_agent": None,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

