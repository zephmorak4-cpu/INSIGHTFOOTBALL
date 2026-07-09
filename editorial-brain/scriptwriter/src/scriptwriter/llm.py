"""LLM interfaces and deterministic local adapter for Scriptwriter."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Protocol


class LLMClient(Protocol):
    def generate(self, prompt: str, *, temperature: float, max_tokens: int) -> str:
        """Generate a text response from a prompt."""


class RuleBasedScriptwriterClient:
    """Deterministic adapter for tests and sample execution."""

    def __init__(self, brief: dict[str, Any], config: Any):
        self.brief = brief
        self.config = config

    def generate(self, prompt: str, *, temperature: float, max_tokens: int) -> str:
        brief = self.brief
        brand = brief["brand_opening"]
        question = brief["central_question"]
        fact = brief["surprising_fact"]
        evidence = brief.get("evidence_to_use", [])
        contradiction = brief.get("contradiction_to_handle", [])
        hook = fact
        main_body = (
            f"So the real question is: {question} "
            f"{brief['match']['home_team']} usually start aggressively, pressing high and forcing rushed decisions. "
            f"{brief['match']['away_team']} have enough quality to play through it, but a messy opening can drag them from their plan. "
            f"The evidence is simple: {evidence[0] if evidence else brief['key_advantage']} "
            f"The balance matters too: {contradiction[0] if contradiction else brief['x_factor']} "
            f"That makes it a {brief['match_edge'].lower()}, not a prediction."
        )
        conclusion = (
            f"{brief['viewer_takeaway']} "
            f"Watch {brief['x_factor'].rstrip('.').lower()}."
        )
        cta = "Can Arsenal survive the first 20 minutes, or will Liverpool take control early? Tell us below."
        voiceover = f"{brand} {hook} {main_body} {conclusion} {cta}"
        output = {
            "production_id": brief["production_id"],
            "agent_id": self.config.agent_id,
            "agent_name": self.config.agent_name,
            "prompt_id": self.config.prompt_id,
            "prompt_version": self.config.prompt_version,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "input_brief_id": brief["brief_id"],
            "match": brief["match"],
            "competition": brief["competition"],
            "script_version": "v1",
            "word_count": count_words(voiceover),
            "estimated_duration_seconds": estimate_duration_seconds(voiceover),
            "brand_opening": brand,
            "hook": hook,
            "central_question": question,
            "main_body": main_body,
            "conclusion": conclusion,
            "cta": cta,
            "full_voiceover": voiceover,
            "final_voiceover": voiceover,
            "claims_used": [fact, *evidence, *contradiction, brief["match_edge"], brief["key_advantage"], brief["x_factor"]],
            "claims_rejected": brief.get("evidence_to_avoid", []),
            "locked_fields": brief["locked_fields"],
            "warnings": [],
            "human_review_flags": [],
            "approval_status": "approved",
            "next_agent": self.config.next_agent,
        }
        return json.dumps(output)


def count_words(text: str) -> int:
    return len([word for word in str(text).replace("...", " ").split() if word.strip()])


def estimate_duration_seconds(text: str) -> int:
    return max(1, round(count_words(text) / 2.6))
