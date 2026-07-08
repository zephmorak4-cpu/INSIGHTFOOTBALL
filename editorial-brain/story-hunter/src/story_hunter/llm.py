"""LLM interfaces and adapters for Story Hunter."""

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


class RuleBasedStoryHunterClient:
    """Deterministic local adapter for tests and sample runs."""

    def __init__(self, daily_input: dict, match_selection: dict):
        self.daily_input = daily_input
        self.match_selection = match_selection

    def generate(self, prompt: str, *, temperature: float, max_tokens: int) -> str:
        selected_match = self.match_selection.get("selected_match", {})
        home = selected_match.get("home_team", "Home team")
        away = selected_match.get("away_team", "Away team")
        context = self.daily_input.get("match_context", {})
        recent_form = context.get("recent_form", {})
        tactical_notes = context.get("tactical_notes", {})
        statistics = context.get("statistics", {})
        production_id = self.match_selection.get(
            "production_id",
            self.daily_input.get("production_metadata", {}).get("production_id", ""),
        )

        early_pressure_story = self._has_early_pressure_context(home, away, recent_form, tactical_notes, statistics)
        if early_pressure_story:
            story_angle = (
                f"{home} may have the edge if they turn the first 20 minutes into pressure, "
                f"but {away} have enough quality to punish one mistake."
            )
            central_question = f"Can {away} survive {home}'s fast start?"
            surprising_fact = (
                f"Sample data: {home} have started quickly in recent home matches, "
                f"while {away} have sometimes needed longer to settle away."
            )
            supporting_context = [
                f"{home} recent form note: {recent_form.get(home.lower(), recent_form.get(home, 'strong home starts'))}",
                f"{away} recent form note: {recent_form.get(away.lower(), recent_form.get(away, 'slower away starts'))}",
                f"Tactical note: {tactical_notes.get('battle', 'early pressure vs buildup')}",
            ]
            confidence = 86
            rejected_angles = ["Generic match preview", "Basic head-to-head angle"]
            warnings = ["FACT_CHECK_REQUIRED: sample claims must be verified before publishing."]
        else:
            story_angle = f"{home} vs {away} may come down to which team controls the first big momentum swing."
            central_question = f"Who handles the first big moment better?"
            surprising_fact = "Available context does not provide a strong verified surprising fact."
            supporting_context = ["Daily input has limited story-specific context."]
            confidence = 62
            rejected_angles = ["Generic match preview"]
            warnings = ["LOW_CONFIDENCE", "WEAK_STORY"]

        output = {
            "production_id": production_id,
            "agent_id": "IF-A02",
            "agent_name": "Story Hunter",
            "prompt_id": "IF-PROMPT-02-STORY-HUNTER",
            "prompt_version": "v1.0",
            "input_version": "v1",
            "output_version": "v1",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "selected_match": selected_match,
            "story_angle": story_angle,
            "central_question": central_question,
            "surprising_fact": surprising_fact,
            "why_this_matters": "The opening spell could decide whether the away team plays calmly or spends the match reacting.",
            "why_fans_should_care": "Both fanbases will have strong opinions about whether the away team can handle that early pressure.",
            "supporting_context": supporting_context,
            "rejected_angles": rejected_angles,
            "story_confidence": confidence,
            "warnings": warnings,
            "human_review_flags": ["FACT_CHECK_REQUIRED"] if confidence >= 70 else ["LOW_CONFIDENCE", "HUMAN_EDITOR_DECISION"],
            "locked_fields": {
                "story_angle": story_angle,
                "central_question": central_question,
                "surprising_fact": surprising_fact,
            },
            "approval_status": "approved" if confidence >= 70 else "needs_revision",
            "next_agent": "IF-A03",
        }
        return json.dumps(output)

    @staticmethod
    def _has_early_pressure_context(home: str, away: str, recent_form: dict, tactical_notes: dict, statistics: dict) -> bool:
        combined = json.dumps(
            {
                "home": recent_form.get(home.lower(), recent_form.get(home, "")),
                "away": recent_form.get(away.lower(), recent_form.get(away, "")),
                "tactical": tactical_notes,
                "statistics": statistics,
            }
        ).lower()
        return any(term in combined for term in ["early", "fast", "first-half", "first half", "pressure", "starts"])
