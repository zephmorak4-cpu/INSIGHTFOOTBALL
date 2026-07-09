"""LLM interfaces and adapters for Match Selector."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
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


class RuleBasedMatchSelectorClient:
    """Deterministic local adapter for tests and sample runs."""

    def __init__(self, daily_input: dict):
        self.daily_input = daily_input

    def generate(self, prompt: str, *, temperature: float, max_tokens: int) -> str:
        fixtures = self.daily_input.get("fixtures", [])
        if not fixtures:
            return json.dumps({"error": "No fixtures available"})

        editor_selection = self.daily_input.get("editor_selection")
        ranked = sorted(fixtures, key=self._score_fixture, reverse=True)
        if isinstance(editor_selection, dict):
            ranked = sorted(ranked, key=lambda item: 0 if item.get("selection_source") == "human_editor" else 1)
        selected = ranked[0]
        score = self._score_fixture(selected)
        runner_up_matches = [
            {
                "home_team": item.get("home_team", ""),
                "away_team": item.get("away_team", ""),
                "competition": item.get("competition", ""),
                "selection_score": self._score_fixture(item),
            }
            for item in ranked[1:3]
        ]
        data_gaps = self._data_gaps(selected)
        confidence_score = max(0, min(100, int(round(score - (len(data_gaps) * 4)))))
        production_id = self.daily_input.get("production_metadata", {}).get("production_id", "")

        output = {
            "agent_id": "IF-A01",
            "agent_name": "Match Selector",
            "prompt_id": "IF-PROMPT-01-MATCH-SELECTOR",
            "prompt_version": "v1.0",
            "production_id": production_id,
            "selected_match": {
                "home_team": selected.get("home_team", ""),
                "away_team": selected.get("away_team", ""),
                "competition": selected.get("competition", ""),
                "kickoff_time": selected.get("kickoff_time", ""),
                "country": selected.get("country", ""),
            },
            "selected_reason": self._selection_reason(selected),
            "selection_source": selected.get("selection_source", "automatic_recommendation"),
            "selection_score": int(round(score)),
            "audience_interest_score": int(selected.get("audience_interest", 0)),
            "importance_score": int(selected.get("importance", 0)),
            "rivalry_score": int(selected.get("rivalry", 0)),
            "data_availability_score": int(selected.get("available_data", 0)),
            "story_potential_score": int(selected.get("story_potential", 0)),
            "runner_up_matches": runner_up_matches,
            "rejected_matches": [],
            "data_gaps": data_gaps,
            "confidence": {
                "score": confidence_score,
                "reason": "Selection is based on audience interest, importance, rivalry, data availability, and story potential.",
            },
            "human_review_flags": ["LOW_CONFIDENCE"] if confidence_score < 70 else [],
            "approval_status": "approved" if confidence_score >= 70 else "needs_revision",
            "next_agent": "IF-A02",
        }
        return json.dumps(output)

    @staticmethod
    def _score_fixture(fixture: dict) -> float:
        return (
            float(fixture.get("audience_interest", 0)) * 2.0
            + float(fixture.get("importance", 0)) * 2.0
            + float(fixture.get("rivalry", 0)) * 1.2
            + float(fixture.get("available_data", 0)) * 2.2
            + float(fixture.get("story_potential", 0)) * 2.6
        )

    @staticmethod
    def _data_gaps(fixture: dict) -> list[str]:
        gaps = []
        for field in ["home_team", "away_team", "competition", "kickoff_time", "country"]:
            if not fixture.get(field):
                gaps.append(f"Missing {field}")
        if float(fixture.get("available_data", 0)) < 7:
            gaps.append("Available data score is below recommended threshold")
        if float(fixture.get("story_potential", 0)) < 7:
            gaps.append("Story potential score is below recommended threshold")
        return gaps

    @staticmethod
    def _selection_reason(fixture: dict) -> str:
        return (
            f"{fixture.get('home_team', 'Home team')} vs {fixture.get('away_team', 'Away team')} "
            "has the strongest mix of audience interest, match importance, available data, and story potential."
        )
