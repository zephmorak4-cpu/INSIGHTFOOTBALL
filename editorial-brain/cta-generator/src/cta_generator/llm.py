"""LLM interface and deterministic CTA adapter."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Protocol

from .metrics import count_words, estimate_duration_seconds


class LLMClient(Protocol):
    def generate(self, prompt: str, *, temperature: float, max_tokens: int) -> str:
        """Generate JSON text."""


class RuleBasedCtaGeneratorClient:
    def __init__(self, script: dict[str, Any], brief: dict[str, Any], config: Any):
        self.script = script
        self.brief = brief
        self.config = config

    def generate(self, prompt: str, *, temperature: float, max_tokens: int) -> str:
        options = [
            "Can Arsenal survive the first 20 minutes, or will Liverpool take control early? Tell us below.",
            "Do you agree, or are we missing something?",
            "Who has the edge before kickoff? Drop your call below.",
        ]
        original = self.script.get("cta", "")
        selected = options[0]
        final_voiceover = self.script["full_voiceover"].replace(original, selected, 1) if original else f"{self.script['full_voiceover']} {selected}"
        output = {
            "production_id": self.brief["production_id"],
            "component_id": self.config.component_id,
            "component_name": self.config.component_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "original_cta": original,
            "cta_options": options,
            "selected_cta": selected,
            "selection_reason": "The selected CTA invites football debate without sounding desperate or generic.",
            "final_voiceover": final_voiceover,
            "final_word_count": count_words(final_voiceover),
            "final_estimated_duration_seconds": estimate_duration_seconds(final_voiceover),
            "approval_status": "approved",
        }
        return json.dumps(output)

