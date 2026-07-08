"""Hook Optimizer service."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .config import HookOptimizerConfig
from .errors import ValidationError
from .json_utils import load_json_file, parse_json_object, write_json_file
from .llm import LLMClient
from .logging_utils import StructuredLogger
from .prompt_loader import PromptLoader
from .validation import HookOptimizerValidator


class HookOptimizerService:
    def __init__(self, config: HookOptimizerConfig, llm_client: LLMClient):
        self.config = config
        self.llm_client = llm_client
        self.prompt_loader = PromptLoader(config.prompt_path)
        self.validator = HookOptimizerValidator(config.script_schema, config.brief_schema, config.optimization_schema, config.optimized_script_schema, config.max_hook_options)

    def run_from_files(self, script_path: Path, brief_path: Path) -> dict[str, Any]:
        return self.run(load_json_file(script_path), load_json_file(brief_path))

    def run(self, script: dict[str, Any], brief: dict[str, Any]) -> dict[str, Any]:
        production_id = brief.get("production_id", "unknown-production")
        logger = StructuredLogger(self.config.log_directory, f"hook-optimizer-{production_id}")
        try:
            self.validator.validate_inputs(script, brief)
            prompt = self.prompt_loader.load() + "\n\nScript:\n" + json.dumps(script, ensure_ascii=True) + "\n\nBrief:\n" + json.dumps(brief, ensure_ascii=True)
        except ValidationError as exc:
            return self._error(production_id, "HOOK_INPUT_INVALID", exc.issues)
        last_issues: list[str] = []
        for attempt in range(1, self.config.max_retries + 2):
            try:
                optimization = parse_json_object(self.llm_client.generate(prompt, temperature=self.config.temperature, max_tokens=self.config.max_tokens))
                self.validator.validate_optimization(optimization, script, brief)
                optimized = dict(script)
                old_hook = script["hook"]
                selected = optimization["selected_hook"]
                optimized["hook"] = selected
                optimized["full_voiceover"] = optimized["full_voiceover"].replace(old_hook, selected, 1)
                optimized["script_version"] = "v2-hook-optimized"
                self.validator.validate_optimized_script(optimized, script, brief, selected)
                optimization_path = self.config.output_directory / f"hook-optimization-{production_id}.json"
                optimized_path = self.config.output_directory / f"optimized-script-output-{production_id}.json"
                write_json_file(optimization_path, optimization)
                write_json_file(optimized_path, optimized)
                logger.log({"event": "hook_optimizer_completed", "attempt": attempt, "optimization_path": str(optimization_path), "optimized_script_path": str(optimized_path)})
                return {"success": True, "optimization": optimization, "optimized_script": optimized, "optimization_path": str(optimization_path), "optimized_script_path": str(optimized_path)}
            except (ValueError, json.JSONDecodeError, ValidationError) as exc:
                last_issues = getattr(exc, "issues", [str(exc)])
                logger.log({"event": "hook_optimizer_attempt_failed", "attempt": attempt, "issues": last_issues})
        return self._error(production_id, "HOOK_OPTIMIZATION_FAILED", last_issues)

    @staticmethod
    def _error(production_id: str, code: str, issues: list[str]) -> dict[str, Any]:
        return {"success": False, "component_id": "S3-C02", "component_name": "Hook Optimizer", "production_id": production_id, "error": {"code": code, "issues": issues}, "approval_status": "blocked"}

