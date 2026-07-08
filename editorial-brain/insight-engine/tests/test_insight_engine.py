from __future__ import annotations

import json
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "editorial-brain" / "insight-engine" / "src"
sys.path.insert(0, str(SRC))

from insight_engine.config import load_config
from insight_engine.llm import RuleBasedInsightEngineClient, calculate_confidence
from insight_engine.prompt_loader import PromptLoader
from insight_engine.service import InsightEngineService
from insight_engine.validation import InsightEngineValidator


CONFIG_PATH = ROOT / "editorial-brain" / "insight-engine" / "config" / "insight-engine.config.json"
DAILY_INPUT_PATH = ROOT / "editorial-brain" / "examples" / "liverpool-arsenal-daily-input.json"
MATCH_SELECTION_PATH = ROOT / "editorial-brain" / "output" / "match-selection-liverpool-arsenal.json"
STORY_HUNTER_PATH = ROOT / "editorial-brain" / "output" / "story-hunter-liverpool-arsenal.json"
EVIDENCE_FILTER_PATH = ROOT / "editorial-brain" / "output" / "evidence-filter-liverpool-arsenal.json"


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


def valid_output(daily_input: dict, match_selection: dict, story_hunter: dict, evidence_filter: dict) -> dict:
    raw = RuleBasedInsightEngineClient(daily_input, match_selection, story_hunter, evidence_filter).generate(
        "",
        temperature=0.2,
        max_tokens=2500,
    )
    return json.loads(raw)


class InsightEngineModuleTests(unittest.TestCase):
    def test_prompt_loader_reads_frozen_prompt_library_section(self):
        config, temp_dir = load_test_config()
        self.addCleanup(temp_dir.cleanup)
        prompt = PromptLoader(config.prompt_library_path).load_insight_engine_prompt()
        self.assertIn("IF-PROMPT-04-INSIGHT-ENGINE", prompt)
        self.assertIn("Insight Engine", prompt)
        self.assertNotIn("## 9. Agent 5: Scriptwriter", prompt)

    def test_liverpool_arsenal_sample_succeeds(self):
        config, temp_dir = load_test_config()
        self.addCleanup(temp_dir.cleanup)
        daily_input = load_json(DAILY_INPUT_PATH)
        match_selection = load_json(MATCH_SELECTION_PATH)
        story_hunter = load_json(STORY_HUNTER_PATH)
        evidence_filter = load_json(EVIDENCE_FILTER_PATH)
        service = InsightEngineService(
            config,
            RuleBasedInsightEngineClient(daily_input, match_selection, story_hunter, evidence_filter),
        )

        result = service.run(daily_input, match_selection, story_hunter, evidence_filter)

        self.assertEqual(result["agent_id"], "IF-A04")
        self.assertEqual(result["next_agent"], "IF-A05")
        self.assertEqual(result["approval_status"], "approved")
        self.assertEqual(result["story_angle"], story_hunter["story_angle"])
        self.assertEqual(result["central_question"], story_hunter["central_question"])
        self.assertEqual(result["match_edge"], "Slight Home Edge")
        self.assertGreaterEqual(result["confidence"]["score"], 70)
        self.assertIn("first", result["x_factor"].lower())

    def test_no_match_edge_fails(self):
        config, temp_dir = load_test_config()
        self.addCleanup(temp_dir.cleanup)
        daily_input = load_json(DAILY_INPUT_PATH)
        match_selection = load_json(MATCH_SELECTION_PATH)
        story_hunter = load_json(STORY_HUNTER_PATH)
        evidence_filter = load_json(EVIDENCE_FILTER_PATH)
        output = valid_output(daily_input, match_selection, story_hunter, evidence_filter)
        output["match_edge"] = ""
        validator = self._validator(config)

        with self.assertRaises(Exception) as context:
            validator.validate_output(output, story_hunter, evidence_filter)
        self.assertIn("match_edge", str(context.exception.issues))

    def test_no_tactical_explanation_fails(self):
        config, temp_dir = load_test_config()
        self.addCleanup(temp_dir.cleanup)
        daily_input, match_selection, story_hunter, evidence_filter = self._inputs()
        output = valid_output(daily_input, match_selection, story_hunter, evidence_filter)
        output["tactical_explanation"] = ""

        with self.assertRaises(Exception) as context:
            self._validator(config).validate_output(output, story_hunter, evidence_filter)
        self.assertIn("tactical_explanation", str(context.exception.issues))

    def test_no_x_factor_fails(self):
        config, temp_dir = load_test_config()
        self.addCleanup(temp_dir.cleanup)
        daily_input, match_selection, story_hunter, evidence_filter = self._inputs()
        output = valid_output(daily_input, match_selection, story_hunter, evidence_filter)
        output["x_factor"] = ""

        with self.assertRaises(Exception) as context:
            self._validator(config).validate_output(output, story_hunter, evidence_filter)
        self.assertIn("x_factor", str(context.exception.issues))

    def test_betting_language_rejected(self):
        config, temp_dir = load_test_config()
        self.addCleanup(temp_dir.cleanup)
        daily_input, match_selection, story_hunter, evidence_filter = self._inputs()
        output = valid_output(daily_input, match_selection, story_hunter, evidence_filter)
        output["viewer_takeaway"] = "This is a safe bet if Liverpool start quickly."

        with self.assertRaises(Exception) as context:
            self._validator(config).validate_output(output, story_hunter, evidence_filter)
        self.assertIn("forbidden betting language", str(context.exception.issues))

    def test_unsupported_claims_rejected(self):
        config, temp_dir = load_test_config()
        self.addCleanup(temp_dir.cleanup)
        daily_input, match_selection, story_hunter, evidence_filter = self._inputs()
        output = valid_output(daily_input, match_selection, story_hunter, evidence_filter)
        output["insight_summary"] = "A late injury will decide this match."

        with self.assertRaises(Exception) as context:
            self._validator(config).validate_output(output, story_hunter, evidence_filter)
        self.assertIn("unsupported claim", str(context.exception.issues))

    def test_locked_fields_preserved(self):
        config, temp_dir = load_test_config()
        self.addCleanup(temp_dir.cleanup)
        daily_input, match_selection, story_hunter, evidence_filter = self._inputs()
        output = valid_output(daily_input, match_selection, story_hunter, evidence_filter)
        output["locked_fields"]["central_question"] = "Changed?"

        with self.assertRaises(Exception) as context:
            self._validator(config).validate_output(output, story_hunter, evidence_filter)
        self.assertIn("locked_fields.central_question", str(context.exception.issues))

    def test_confidence_calculated_from_evidence(self):
        evidence_filter = load_json(EVIDENCE_FILTER_PATH)
        expected = calculate_confidence(
            evidence_filter["evidence_confidence"],
            evidence_filter["evidence_quality"],
        )
        self.assertEqual(expected, 79)

    def test_retry_once_after_invalid_json_then_succeeds(self):
        config, temp_dir = load_test_config()
        self.addCleanup(temp_dir.cleanup)
        daily_input, match_selection, story_hunter, evidence_filter = self._inputs()
        valid_response = json.dumps(valid_output(daily_input, match_selection, story_hunter, evidence_filter))
        client = StaticLLMClient(["not json", valid_response])
        service = InsightEngineService(config, client)

        result = service.run(daily_input, match_selection, story_hunter, evidence_filter)

        self.assertEqual(client.calls, 2)
        self.assertEqual(result["agent_id"], "IF-A04")
        self.assertEqual(result["approval_status"], "approved")

    def test_retry_failure_returns_structured_error(self):
        config, temp_dir = load_test_config()
        self.addCleanup(temp_dir.cleanup)
        daily_input, match_selection, story_hunter, evidence_filter = self._inputs()
        service = InsightEngineService(config, StaticLLMClient(["not json", "still not json"]))

        result = service.run(daily_input, match_selection, story_hunter, evidence_filter)

        self.assertFalse(result["success"])
        self.assertEqual(result["error"]["code"], "INSIGHT_ENGINE_VALIDATION_FAILED")
        self.assertEqual(result["error"]["attempts"], 2)

    @staticmethod
    def _inputs():
        return (
            load_json(DAILY_INPUT_PATH),
            load_json(MATCH_SELECTION_PATH),
            load_json(STORY_HUNTER_PATH),
            load_json(EVIDENCE_FILTER_PATH),
        )

    @staticmethod
    def _validator(config):
        return InsightEngineValidator(
            config.daily_input_schema_path,
            config.match_selection_schema_path,
            config.story_hunter_schema_path,
            config.evidence_filter_schema_path,
            config.output_schema_path,
            config.minimum_confidence,
        )


if __name__ == "__main__":
    unittest.main()
