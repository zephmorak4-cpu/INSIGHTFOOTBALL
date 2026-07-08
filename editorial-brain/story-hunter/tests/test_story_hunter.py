from __future__ import annotations

import json
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "editorial-brain" / "story-hunter" / "src"
sys.path.insert(0, str(SRC))

from story_hunter.config import load_config
from story_hunter.llm import RuleBasedStoryHunterClient
from story_hunter.prompt_loader import PromptLoader
from story_hunter.service import StoryHunterService
from story_hunter.validation import StoryHunterValidator


CONFIG_PATH = ROOT / "editorial-brain" / "story-hunter" / "config" / "story-hunter.config.json"
DAILY_INPUT_PATH = ROOT / "editorial-brain" / "examples" / "liverpool-arsenal-daily-input.json"
MATCH_SELECTION_PATH = ROOT / "editorial-brain" / "output" / "match-selection-liverpool-arsenal.json"


class StaticLLMClient:
    def __init__(self, responses: list[str]):
        self.responses = responses
        self.calls = 0

    def generate(self, prompt: str, *, temperature: float, max_tokens: int) -> str:
        response = self.responses[min(self.calls, len(self.responses) - 1)]
        self.calls += 1
        return response


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_test_config():
    config = load_config(CONFIG_PATH)
    temp_dir = tempfile.TemporaryDirectory()
    return replace(config, log_directory=Path(temp_dir.name)), temp_dir


class StoryHunterModuleTests(unittest.TestCase):
    def test_prompt_loader_reads_frozen_prompt_library_section(self):
        config, temp_dir = load_test_config()
        self.addCleanup(temp_dir.cleanup)
        prompt = PromptLoader(config.prompt_library_path).load_story_hunter_prompt()
        self.assertIn("IF-PROMPT-02-STORY-HUNTER", prompt)
        self.assertIn("Story Hunter", prompt)
        self.assertNotIn("## 7. Agent 3: Evidence Filter", prompt)

    def test_deterministic_client_returns_valid_story_hunter_output(self):
        config, temp_dir = load_test_config()
        self.addCleanup(temp_dir.cleanup)
        daily_input = load_json(DAILY_INPUT_PATH)
        match_selection = load_json(MATCH_SELECTION_PATH)
        service = StoryHunterService(config, RuleBasedStoryHunterClient(daily_input, match_selection))

        result = service.run(daily_input, match_selection)

        self.assertEqual(result["agent_id"], "IF-A02")
        self.assertEqual(result["next_agent"], "IF-A03")
        self.assertEqual(result["approval_status"], "approved")
        self.assertEqual(result["selected_match"], match_selection["selected_match"])
        self.assertIn("Can Arsenal survive", result["central_question"])
        self.assertEqual(result["locked_fields"]["story_angle"], result["story_angle"])
        self.assertGreaterEqual(result["story_confidence"], 70)

    def test_rejects_unapproved_match_selection(self):
        config, temp_dir = load_test_config()
        self.addCleanup(temp_dir.cleanup)
        daily_input = load_json(DAILY_INPUT_PATH)
        match_selection = load_json(MATCH_SELECTION_PATH)
        match_selection["approval_status"] = "needs_revision"
        service = StoryHunterService(config, StaticLLMClient([]))

        result = service.run(daily_input, match_selection)

        self.assertFalse(result["success"])
        self.assertEqual(result["approval_status"], "blocked")
        self.assertIn("approval_status", str(result["error"]["issues"]))

    def test_retry_once_after_invalid_json_then_succeeds(self):
        config, temp_dir = load_test_config()
        self.addCleanup(temp_dir.cleanup)
        daily_input = load_json(DAILY_INPUT_PATH)
        match_selection = load_json(MATCH_SELECTION_PATH)
        valid_response = RuleBasedStoryHunterClient(daily_input, match_selection).generate("", temperature=0.3, max_tokens=2500)
        client = StaticLLMClient(["not json", valid_response])
        service = StoryHunterService(config, client)

        result = service.run(daily_input, match_selection)

        self.assertEqual(client.calls, 2)
        self.assertEqual(result["agent_id"], "IF-A02")
        self.assertEqual(result["approval_status"], "approved")

    def test_retry_failure_returns_structured_error(self):
        config, temp_dir = load_test_config()
        self.addCleanup(temp_dir.cleanup)
        daily_input = load_json(DAILY_INPUT_PATH)
        match_selection = load_json(MATCH_SELECTION_PATH)
        client = StaticLLMClient(["not json", "still not json"])
        service = StoryHunterService(config, client)

        result = service.run(daily_input, match_selection)

        self.assertFalse(result["success"])
        self.assertEqual(result["error"]["code"], "STORY_HUNTER_VALIDATION_FAILED")
        self.assertEqual(result["error"]["attempts"], 2)

    def test_validator_rejects_locked_field_mismatch(self):
        config, temp_dir = load_test_config()
        self.addCleanup(temp_dir.cleanup)
        daily_input = load_json(DAILY_INPUT_PATH)
        match_selection = load_json(MATCH_SELECTION_PATH)
        output = json.loads(RuleBasedStoryHunterClient(daily_input, match_selection).generate("", temperature=0.3, max_tokens=2500))
        output["locked_fields"]["central_question"] = "Can someone else change this?"
        validator = StoryHunterValidator(
            config.daily_input_schema_path,
            config.match_selection_schema_path,
            config.output_schema_path,
            config.minimum_confidence,
        )

        with self.assertRaises(Exception) as context:
            validator.validate_output(output, match_selection)
        self.assertIn("locked_fields.central_question", str(context.exception.issues))

    def test_validator_rejects_generic_story_angle(self):
        config, temp_dir = load_test_config()
        self.addCleanup(temp_dir.cleanup)
        daily_input = load_json(DAILY_INPUT_PATH)
        match_selection = load_json(MATCH_SELECTION_PATH)
        output = json.loads(RuleBasedStoryHunterClient(daily_input, match_selection).generate("", temperature=0.3, max_tokens=2500))
        output["story_angle"] = "Liverpool vs Arsenal match preview."
        output["locked_fields"]["story_angle"] = output["story_angle"]
        validator = StoryHunterValidator(
            config.daily_input_schema_path,
            config.match_selection_schema_path,
            config.output_schema_path,
            config.minimum_confidence,
        )

        with self.assertRaises(Exception) as context:
            validator.validate_output(output, match_selection)
        self.assertIn("too generic", str(context.exception.issues))


if __name__ == "__main__":
    unittest.main()
