"""LLM interface and deterministic hook adapter."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Protocol


class LLMClient(Protocol):
    def generate(self, prompt: str, *, temperature: float, max_tokens: int) -> str:
        """Generate JSON text."""


class RuleBasedHookOptimizerClient:
    def __init__(self, script: dict[str, Any], brief: dict[str, Any], config: Any):
        self.script = script
        self.brief = brief
        self.config = config

    def generate(self, prompt: str, *, temperature: float, max_tokens: int) -> str:
        fact = self.brief["surprising_fact"]
        options = [
            fact,
            f"The first big answer may come before the match settles: {fact}",
            f"Watch the opening phase closely, because {fact}",
        ]
        output = {
            "production_id": self.brief["production_id"],
            "component_id": self.config.component_id,
            "component_name": self.config.component_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "original_hook": self.script["hook"],
            "hook_options": options,
            "selected_hook": options[0],
            "selection_reason": "The selected hook is specific, factual, simple, and avoids clickbait.",
            "rejected_hooks": options[1:],
            "locked_fields_preserved": True,
            "warnings": [],
            "approval_status": "approved",
        }
        return json.dumps(output)

