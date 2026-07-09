from __future__ import annotations

import json
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "editorial-brain" / "match-selector" / "src"
sys.path.insert(0, str(SRC))

from match_selector.config import load_config
from match_selector.llm import RuleBasedMatchSelectorClient
from match_selector.prompt_loader import PromptLoader
from match_selector.service import MatchSelectorService
from match_selector.validation import MatchSelectorValidator


CONFIG_PATH = ROOT / "editorial-brain" / "match-selector" / "config" / "match-selector.config.json"
INPUT_PATH = ROOT / "editorial-brain" / "examples" / "liverpool-arsenal-daily-input.json"


class StaticLLMClient:
    def __init__(self, responses: list[str]):
        self.responses = responses
        self.calls = 0

    def generate(self, prompt: str, *, temperature: float, max_tokens: int) -> str:
        response = self.responses[min(self.calls, len(self.responses) - 1)]
        self.calls += 1
        return response


def load_sample_input() -> dict:
    return json.loads(INPUT_PATH.read_text(encoding="utf-8"))


def load_test_config():
    config = load_config(CONFIG_PATH)
    temp_dir = tempfile.TemporaryDirectory()
    return replace(config, log_directory=Path(temp_dir.name)), temp_dir


class MatchSelectorModuleTests(unittest.TestCase):
    def test_prompt_loader_reads_frozen_prompt_library_section(self):
        config, temp_dir = load_test_config()
        self.addCleanup(temp_dir.cleanup)
        prompt = PromptLoader(config.prompt_library_path).load_match_selector_prompt()
        self.assertIn("IF-PROMPT-01-MATCH-SELECTOR", prompt)
        self.assertIn("Match Selector", prompt)
        self.assertNotIn("## 6. Agent 2: Story Hunter", prompt)

    def test_deterministic_client_returns_valid_match_selection(self):
        config, temp_dir = load_test_config()
        self.addCleanup(temp_dir.cleanup)
        daily_input = load_sample_input()
        service = MatchSelectorService(config, RuleBasedMatchSelectorClient(daily_input))

        result = service.run(daily_input)

        self.assertEqual(result["agent_id"], "IF-A01")
        self.assertEqual(result["next_agent"], "IF-A02")
        self.assertEqual(result["selected_match"]["home_team"], "Liverpool")
        self.assertEqual(result["selected_match"]["away_team"], "Arsenal")
        self.assertGreaterEqual(result["confidence"]["score"], 70)

    def test_invalid_daily_input_returns_structured_error(self):
        config, temp_dir = load_test_config()
        self.addCleanup(temp_dir.cleanup)
        invalid_input = {"production_metadata": {"date": "2026-07-06", "production_id": "bad"}}
        service = MatchSelectorService(config, StaticLLMClient([]))

        result = service.run(invalid_input)

        self.assertFalse(result["success"])
        self.assertEqual(result["approval_status"], "blocked")
        self.assertIn("Daily input validation failed", result["error"]["message"])

    def test_retry_once_after_invalid_json_then_succeeds(self):
        config, temp_dir = load_test_config()
        self.addCleanup(temp_dir.cleanup)
        daily_input = load_sample_input()
        valid_response = RuleBasedMatchSelectorClient(daily_input).generate("", temperature=0.3, max_tokens=2500)
        client = StaticLLMClient(["not json", valid_response])
        service = MatchSelectorService(config, client)

        result = service.run(daily_input)

        self.assertEqual(client.calls, 2)
        self.assertEqual(result["agent_id"], "IF-A01")
        self.assertEqual(result["approval_status"], "approved")

    def test_retry_failure_returns_structured_error(self):
        config, temp_dir = load_test_config()
        self.addCleanup(temp_dir.cleanup)
        daily_input = load_sample_input()
        client = StaticLLMClient(["not json", "still not json"])
        service = MatchSelectorService(config, client)

        result = service.run(daily_input)

        self.assertFalse(result["success"])
        self.assertEqual(result["error"]["code"], "MATCH_SELECTOR_VALIDATION_FAILED")
        self.assertEqual(result["error"]["attempts"], 2)

    def test_validator_rejects_match_not_present_in_daily_input(self):
        config, temp_dir = load_test_config()
        self.addCleanup(temp_dir.cleanup)
        daily_input = load_sample_input()
        output = json.loads(RuleBasedMatchSelectorClient(daily_input).generate("", temperature=0.3, max_tokens=2500))
        output["selected_match"]["home_team"] = "Chelsea"
        validator = MatchSelectorValidator(
            config.input_schema_path,
            config.output_schema_path,
            config.minimum_confidence,
        )

        with self.assertRaises(Exception) as context:
            validator.validate_output(output, daily_input)
        self.assertIn("selected match must exist", str(context.exception.issues))

    def test_production_rejects_non_today_fixture(self):
        config, temp_dir = load_test_config()
        self.addCleanup(temp_dir.cleanup)
        daily_input = load_sample_input()
        daily_input["production_metadata"]["date"] = "2026-07-09"
        validator = MatchSelectorValidator(config.input_schema_path, config.output_schema_path, config.minimum_confidence)
        with patch.dict("os.environ", {"INSIGHT_FOOTBALL_ENV": "production"}, clear=False), self.assertRaises(Exception) as context:
            validator.validate_daily_input(daily_input)
        self.assertIn("production fixtures must be for 2026-07-09", str(context.exception.issues))


if __name__ == "__main__":
    unittest.main()
