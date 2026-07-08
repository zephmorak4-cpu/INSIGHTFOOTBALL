from __future__ import annotations

import json
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "editorial-brain" / "evidence-filter" / "src"
sys.path.insert(0, str(SRC))

from evidence_filter.config import load_config
from evidence_filter.llm import RuleBasedEvidenceFilterClient
from evidence_filter.prompt_loader import PromptLoader
from evidence_filter.service import EvidenceFilterService
from evidence_filter.validation import EvidenceFilterValidator


CONFIG_PATH = ROOT / "editorial-brain" / "evidence-filter" / "config" / "evidence-filter.config.json"
DAILY_INPUT_PATH = ROOT / "editorial-brain" / "examples" / "liverpool-arsenal-daily-input.json"
MATCH_SELECTION_PATH = ROOT / "editorial-brain" / "output" / "match-selection-liverpool-arsenal.json"
STORY_HUNTER_PATH = ROOT / "editorial-brain" / "output" / "story-hunter-liverpool-arsenal.json"


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


def valid_output(daily_input: dict, match_selection: dict, story_hunter: dict) -> dict:
    raw = RuleBasedEvidenceFilterClient(daily_input, match_selection, story_hunter).generate(
        "",
        temperature=0.2,
        max_tokens=2500,
    )
    return json.loads(raw)


class EvidenceFilterModuleTests(unittest.TestCase):
    def test_prompt_loader_reads_frozen_prompt_library_section(self):
        config, temp_dir = load_test_config()
        self.addCleanup(temp_dir.cleanup)
        prompt = PromptLoader(config.prompt_library_path).load_evidence_filter_prompt()
        self.assertIn("IF-PROMPT-03-EVIDENCE-FILTER", prompt)
        self.assertIn("Evidence Filter", prompt)
        self.assertNotIn("## 8. Agent 4: Insight Engine", prompt)

    def test_liverpool_arsenal_sample_succeeds(self):
        config, temp_dir = load_test_config()
        self.addCleanup(temp_dir.cleanup)
        daily_input = load_json(DAILY_INPUT_PATH)
        match_selection = load_json(MATCH_SELECTION_PATH)
        story_hunter = load_json(STORY_HUNTER_PATH)
        service = EvidenceFilterService(config, RuleBasedEvidenceFilterClient(daily_input, match_selection, story_hunter))

        result = service.run(daily_input, match_selection, story_hunter)

        self.assertEqual(result["agent_id"], "IF-A03")
        self.assertEqual(result["next_agent"], "IF-A04")
        self.assertEqual(result["approval_status"], "approved")
        self.assertEqual(result["story_angle"], story_hunter["story_angle"])
        self.assertEqual(result["central_question"], story_hunter["central_question"])
        self.assertGreaterEqual(result["evidence_confidence"], 70)
        self.assertGreaterEqual(len(result["primary_evidence"]), 2)
        self.assertGreaterEqual(len(result["contradictory_evidence"]), 1)
        self.assertGreaterEqual(len(result["missing_information"]), 1)

    def test_unrelated_statistics_rejected_when_marked_used(self):
        config, temp_dir = load_test_config()
        self.addCleanup(temp_dir.cleanup)
        daily_input = load_json(DAILY_INPUT_PATH)
        match_selection = load_json(MATCH_SELECTION_PATH)
        story_hunter = load_json(STORY_HUNTER_PATH)
        output = valid_output(daily_input, match_selection, story_hunter)
        output["supporting_statistics"][1]["used"] = True
        validator = EvidenceFilterValidator(
            config.daily_input_schema_path,
            config.match_selection_schema_path,
            config.story_hunter_schema_path,
            config.output_schema_path,
            config.minimum_confidence,
        )

        with self.assertRaises(Exception) as context:
            validator.validate_output(output, story_hunter)
        self.assertIn("unrelated statistic", str(context.exception.issues))

    def test_duplicated_evidence_rejected(self):
        config, temp_dir = load_test_config()
        self.addCleanup(temp_dir.cleanup)
        daily_input = load_json(DAILY_INPUT_PATH)
        match_selection = load_json(MATCH_SELECTION_PATH)
        story_hunter = load_json(STORY_HUNTER_PATH)
        output = valid_output(daily_input, match_selection, story_hunter)
        output["secondary_evidence"][0]["claim"] = output["primary_evidence"][0]["claim"]
        validator = EvidenceFilterValidator(
            config.daily_input_schema_path,
            config.match_selection_schema_path,
            config.story_hunter_schema_path,
            config.output_schema_path,
            config.minimum_confidence,
        )

        with self.assertRaises(Exception) as context:
            validator.validate_output(output, story_hunter)
        self.assertIn("duplicated evidence", str(context.exception.issues))

    def test_locked_fields_preserved(self):
        config, temp_dir = load_test_config()
        self.addCleanup(temp_dir.cleanup)
        daily_input = load_json(DAILY_INPUT_PATH)
        match_selection = load_json(MATCH_SELECTION_PATH)
        story_hunter = load_json(STORY_HUNTER_PATH)
        output = valid_output(daily_input, match_selection, story_hunter)
        output["locked_fields"]["surprising_fact"] = "Changed fact"
        validator = EvidenceFilterValidator(
            config.daily_input_schema_path,
            config.match_selection_schema_path,
            config.story_hunter_schema_path,
            config.output_schema_path,
            config.minimum_confidence,
        )

        with self.assertRaises(Exception) as context:
            validator.validate_output(output, story_hunter)
        self.assertIn("locked_fields.surprising_fact", str(context.exception.issues))

    def test_missing_evidence_flagged_by_schema_and_business_rules(self):
        config, temp_dir = load_test_config()
        self.addCleanup(temp_dir.cleanup)
        daily_input = load_json(DAILY_INPUT_PATH)
        match_selection = load_json(MATCH_SELECTION_PATH)
        story_hunter = load_json(STORY_HUNTER_PATH)
        output = valid_output(daily_input, match_selection, story_hunter)
        output["primary_evidence"] = output["primary_evidence"][:1]
        validator = EvidenceFilterValidator(
            config.daily_input_schema_path,
            config.match_selection_schema_path,
            config.story_hunter_schema_path,
            config.output_schema_path,
            config.minimum_confidence,
        )

        with self.assertRaises(Exception) as context:
            validator.validate_output(output, story_hunter)
        self.assertIn("primary_evidence", str(context.exception.issues))

    def test_retry_once_after_invalid_json_then_succeeds(self):
        config, temp_dir = load_test_config()
        self.addCleanup(temp_dir.cleanup)
        daily_input = load_json(DAILY_INPUT_PATH)
        match_selection = load_json(MATCH_SELECTION_PATH)
        story_hunter = load_json(STORY_HUNTER_PATH)
        valid_response = json.dumps(valid_output(daily_input, match_selection, story_hunter))
        client = StaticLLMClient(["not json", valid_response])
        service = EvidenceFilterService(config, client)

        result = service.run(daily_input, match_selection, story_hunter)

        self.assertEqual(client.calls, 2)
        self.assertEqual(result["agent_id"], "IF-A03")
        self.assertEqual(result["approval_status"], "approved")

    def test_retry_failure_returns_structured_error(self):
        config, temp_dir = load_test_config()
        self.addCleanup(temp_dir.cleanup)
        daily_input = load_json(DAILY_INPUT_PATH)
        match_selection = load_json(MATCH_SELECTION_PATH)
        story_hunter = load_json(STORY_HUNTER_PATH)
        client = StaticLLMClient(["not json", "still not json"])
        service = EvidenceFilterService(config, client)

        result = service.run(daily_input, match_selection, story_hunter)

        self.assertFalse(result["success"])
        self.assertEqual(result["error"]["code"], "EVIDENCE_FILTER_VALIDATION_FAILED")
        self.assertEqual(result["error"]["attempts"], 2)


if __name__ == "__main__":
    unittest.main()
