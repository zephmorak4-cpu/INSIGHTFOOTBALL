"""LLM interfaces and deterministic adapter for Insight Engine."""

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
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
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


class RuleBasedInsightEngineClient:
    """Deterministic local adapter for tests and sample runs."""

    def __init__(self, daily_input: dict, match_selection: dict, story_hunter: dict, evidence_filter: dict):
        self.daily_input = daily_input
        self.match_selection = match_selection
        self.story_hunter = story_hunter
        self.evidence_filter = evidence_filter

    def generate(self, prompt: str, *, temperature: float, max_tokens: int) -> str:
        story_angle = self.story_hunter.get("story_angle", "")
        central_question = self.story_hunter.get("central_question", "")
        surprising_fact = self.story_hunter.get("surprising_fact", "")
        selected_match = self.story_hunter.get("selected_match", {})
        home = selected_match.get("home_team", "Home team")
        away = selected_match.get("away_team", "Away team")
        evidence_confidence = int(self.evidence_filter.get("evidence_confidence", 0))
        quality = self.evidence_filter.get("evidence_quality", {})
        confidence_score = calculate_confidence(evidence_confidence, quality)

        output = {
            "production_id": self.story_hunter.get("production_id", ""),
            "agent_id": "IF-A04",
            "agent_name": "Insight Engine",
            "prompt_id": "IF-PROMPT-04-INSIGHT-ENGINE",
            "prompt_version": "v1.0",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "story_angle": story_angle,
            "central_question": central_question,
            "insight_summary": (
                f"{home}'s strongest advantage is how aggressively they begin matches, "
                f"but {away} have shown they can recover after difficult starts."
            ),
            "match_edge": "Slight Home Edge",
            "key_advantage": "Early pressure.",
            "tactical_explanation": (
                f"{home} are likely to press high from kickoff. "
                f"If {away} break that press consistently, the match becomes much more balanced."
            ),
            "uncertainty_summary": (
                f"An unexpected {away} lineup or an early {home} mistake could completely change the pattern."
            ),
            "x_factor": f"{away}'s ability to escape {home}'s first press.",
            "surprising_takeaway": "The first twenty minutes may decide more than the final score.",
            "viewer_takeaway": "Watch the opening phase closely; it may tell you how the rest of the game will unfold.",
            "editorial_notes": [
                "Insight is based on approved evidence from the Evidence Filter.",
                "Keep the conclusion framed as an edge, not a prediction."
            ],
            "confidence": {
                "score": confidence_score,
                "reason": "Confidence is based on evidence confidence and evidence quality scores."
            },
            "warnings": self.evidence_filter.get("warnings", []),
            "human_review_flags": self.evidence_filter.get("human_review_flags", []),
            "locked_fields": {
                "story_angle": story_angle,
                "central_question": central_question,
                "surprising_fact": surprising_fact
            },
            "approval_status": "approved" if confidence_score >= 70 else "needs_revision",
            "next_agent": "IF-A05"
        }
        return json.dumps(output)


def calculate_confidence(evidence_confidence: int, quality: dict) -> int:
    if not quality:
        return max(0, min(100, evidence_confidence))
    quality_average = sum(
        int(quality.get(key, 0))
        for key in ["story_support", "clarity", "relevance", "data_reliability"]
    ) / 4
    return max(0, min(100, int(round((evidence_confidence * 0.55) + (quality_average * 10 * 0.45)))))
