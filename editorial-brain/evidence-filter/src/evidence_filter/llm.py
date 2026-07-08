"""LLM interfaces and deterministic adapter for Evidence Filter."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol

from .errors import LLMError


class LLMClient(Protocol):
    def generate(self, prompt: str, *, temperature: float, max_tokens: int) -> str:
        """Generate a text response from a prompt."""


@dataclass
class OpenAICompatibleHTTPClient:
    """Minimal OpenAI-compatible chat completions client using the standard library."""

    endpoint: str
    model: str
    api_key_env: str
    timeout_seconds: int

    def generate(self, prompt: str, *, temperature: float, max_tokens: int) -> str:
        api_key = os.environ.get(self.api_key_env)
        if not api_key:
            raise LLMError(f"Missing API key environment variable: {self.api_key_env}")

        payload = {
            "model": self.model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        request = urllib.request.Request(
            self.endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                body = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise LLMError(f"LLM request failed: {exc}") from exc

        try:
            return body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMError("LLM response did not match OpenAI-compatible format") from exc


class RuleBasedEvidenceFilterClient:
    """Deterministic local adapter for tests and sample runs."""

    def __init__(self, daily_input: dict, match_selection: dict, story_hunter: dict):
        self.daily_input = daily_input
        self.match_selection = match_selection
        self.story_hunter = story_hunter

    def generate(self, prompt: str, *, temperature: float, max_tokens: int) -> str:
        production_id = self.story_hunter.get("production_id", "")
        story_angle = self.story_hunter.get("story_angle", "")
        central_question = self.story_hunter.get("central_question", "")
        surprising_fact = self.story_hunter.get("surprising_fact", "")
        approved_story = {
            "story_angle": story_angle,
            "central_question": central_question,
            "surprising_fact": surprising_fact,
        }
        selected_match = self.story_hunter.get("selected_match", {})
        home = selected_match.get("home_team", "Home team")
        away = selected_match.get("away_team", "Away team")
        context = self.daily_input.get("match_context", {})

        primary = [
            {
                "claim": f"Sample data: {home} have scored early in four of their last five home games.",
                "simple_translation": f"{home} usually make opponents uncomfortable early at home.",
                "why_it_supports_story": "It directly supports the question about surviving the fast start.",
                "source_type": "recent home form",
                "confidence": "medium"
            },
            {
                "claim": f"Sample data: {away} conceded first in three of their last six away matches.",
                "simple_translation": f"{away} have had a few away games where they needed to recover.",
                "why_it_supports_story": "It supports the idea that the opening spell could be a real test.",
                "source_type": "away form",
                "confidence": "medium"
            }
        ]
        secondary = [
            {
                "claim": f"Sample data: {away} have recovered points after conceding first multiple times this season.",
                "simple_translation": f"{away} can survive difficult starts and still find a way back.",
                "why_it_supports_story": "It keeps the evidence balanced and avoids making the story sound certain.",
                "source_type": "match recovery pattern",
                "confidence": "medium"
            }
        ]
        contradictory = [
            {
                "claim": f"Sample data: {away} have recently improved defensively away from home.",
                "simple_translation": f"{away} may be better prepared for pressure than older form suggests.",
                "why_it_matters": "It weakens any simple claim that the fast start automatically decides the match.",
                "confidence": "medium"
            }
        ]

        output = {
            "production_id": production_id,
            "agent_id": "IF-A03",
            "agent_name": "Evidence Filter",
            "prompt_id": "IF-PROMPT-03-EVIDENCE-FILTER",
            "prompt_version": "v1.0",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "story_angle": story_angle,
            "central_question": central_question,
            "approved_story": approved_story,
            "evidence_summary": (
                f"{home}'s early pressure is real, but {away} have shown they can survive difficult starts."
            ),
            "primary_evidence": primary,
            "secondary_evidence": secondary,
            "supporting_statistics": [
                {
                    "raw_stat": f"Sample: {home} early goals in 4 of last 5 home games",
                    "simple_translation": f"{home} have been dangerous early at home.",
                    "used": True
                },
                {
                    "raw_stat": "Sample: corners average 6.2",
                    "simple_translation": "Rejected because corners do not directly answer the central question.",
                    "used": False
                }
            ],
            "supporting_context": self._supporting_context(context),
            "contradictory_evidence": contradictory,
            "missing_information": [
                "Verify first-half scoring data before publishing.",
                "Verify Arsenal away defensive trend before publishing."
            ],
            "evidence_quality": {
                "story_support": 8,
                "clarity": 9,
                "relevance": 8,
                "data_reliability": 7
            },
            "evidence_confidence": 78,
            "warnings": ["FACT_CHECK_REQUIRED: sample evidence must be verified before publishing."],
            "human_review_flags": ["FACT_CHECK_REQUIRED"],
            "locked_fields": {
                "story_angle": story_angle,
                "central_question": central_question,
                "surprising_fact": surprising_fact
            },
            "approval_status": "approved",
            "next_agent": "IF-A04"
        }
        return json.dumps(output)

    @staticmethod
    def _supporting_context(context: dict) -> list[str]:
        notes = []
        tactical = context.get("tactical_notes", {}).get("battle")
        if tactical:
            notes.append(f"Tactical context: {tactical}")
        recent = context.get("recent_form", {})
        for team, note in recent.items():
            notes.append(f"Recent form context for {team}: {note}")
        return notes or ["No additional supporting context provided."]
