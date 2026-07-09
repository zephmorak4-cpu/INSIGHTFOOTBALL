from __future__ import annotations

import json
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "editorial-brain" / "scriptwriter" / "src"
sys.path.insert(0, str(SRC))

from scriptwriter.config import load_config
from scriptwriter.json_utils import load_json_file
from scriptwriter.llm import RuleBasedScriptwriterClient
from scriptwriter.service import ScriptwriterService


CONFIG_PATH = ROOT / "editorial-brain" / "scriptwriter" / "config" / "scriptwriter.config.json"
BRIEF_PATH = ROOT / "editorial-brain" / "output" / "production-brief-if-2026-07-06-liverpool-arsenal.json"


def config_for(temp: Path):
    config = load_config(CONFIG_PATH)
    return replace(config, output_directory=temp / "output", log_directory=temp / "logs")


def load_brief() -> dict:
    return load_json_file(BRIEF_PATH)


class StaticClient:
    def __init__(self, payload: dict):
        self.payload = payload

    def generate(self, prompt: str, *, temperature: float, max_tokens: int) -> str:
        return json.dumps(self.payload)


def valid_script(config, brief):
    return json.loads(RuleBasedScriptwriterClient(brief, config).generate("", temperature=0, max_tokens=0))


class ScriptwriterTests(unittest.TestCase):
    def run_service(self, brief: dict, client=None):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        config = config_for(Path(temp_dir.name))
        client = client or RuleBasedScriptwriterClient(brief, config)
        return ScriptwriterService(config, client).run(brief), config

    def test_valid_production_brief_creates_valid_script(self):
        result, _ = self.run_service(load_brief())
        self.assertTrue(result["success"])
        self.assertTrue(Path(result["script_path"]).exists())

    def test_missing_central_question_fails(self):
        brief = load_brief()
        brief["central_question"] = ""
        result, _ = self.run_service(brief)
        self.assertFalse(result["success"])
        self.assertEqual(result["error"]["code"], "SCRIPTWRITER_INPUT_INVALID")

    def test_script_over_145_words_fails(self):
        brief = load_brief()
        _, config = self.run_service(brief)
        output = valid_script(config, brief)
        output["full_voiceover"] += " Extra words." * 20
        result, _ = self.run_service(brief, StaticClient(output))
        self.assertFalse(result["success"])
        self.assertTrue(any("<= 145" in issue for issue in result["error"]["issues"]))

    def test_script_under_120_words_fails(self):
        brief = load_brief()
        _, config = self.run_service(brief)
        output = valid_script(config, brief)
        output["full_voiceover"] = brief["brand_opening"] + " " + brief["surprising_fact"]
        result, _ = self.run_service(brief, StaticClient(output))
        self.assertFalse(result["success"])
        self.assertTrue(any(">= 120" in issue for issue in result["error"]["issues"]))

    def test_internal_terms_do_not_leak_to_voiceover(self):
        result, _ = self.run_service(load_brief())
        self.assertTrue(result["success"])
        voiceover = result["script"]["full_voiceover"]
        for term in ["X-Factor", "Tactical Edge", "Form Index", "Risk Meter"]:
            self.assertNotIn(term, voiceover)

    def test_missing_brand_opening_fails(self):
        brief = load_brief()
        _, config = self.run_service(brief)
        output = valid_script(config, brief)
        output["full_voiceover"] = output["full_voiceover"].replace(brief["brand_opening"], "Here is the insight.", 1)
        result, _ = self.run_service(brief, StaticClient(output))
        self.assertFalse(result["success"])
        self.assertTrue(any("brand opening" in issue for issue in result["error"]["issues"]))

    def test_betting_language_fails(self):
        brief = load_brief()
        _, config = self.run_service(brief)
        output = valid_script(config, brief)
        output["full_voiceover"] += " This is guaranteed."
        result, _ = self.run_service(brief, StaticClient(output))
        self.assertFalse(result["success"])
        self.assertTrue(any("betting" in issue for issue in result["error"]["issues"]))

    def test_robotic_language_fails(self):
        brief = load_brief()
        _, config = self.run_service(brief)
        output = valid_script(config, brief)
        output["full_voiceover"] += " Based on the data provided."
        result, _ = self.run_service(brief, StaticClient(output))
        self.assertFalse(result["success"])
        self.assertTrue(any("robotic" in issue for issue in result["error"]["issues"]))

    def test_unsupported_claim_fails(self):
        brief = load_brief()
        _, config = self.run_service(brief)
        output = valid_script(config, brief)
        output["full_voiceover"] += " A red card will decide it."
        result, _ = self.run_service(brief, StaticClient(output))
        self.assertFalse(result["success"])
        self.assertTrue(any("unsupported" in issue for issue in result["error"]["issues"]))

    def test_locked_fields_preserved(self):
        result, _ = self.run_service(load_brief())
        self.assertEqual(result["script"]["locked_fields"]["central_question"], load_brief()["locked_fields"]["central_question"])

    def test_liverpool_vs_arsenal_sample_succeeds(self):
        result, _ = self.run_service(load_brief())
        self.assertTrue(result["success"])
        self.assertLessEqual(result["script"]["estimated_duration_seconds"], 60)


if __name__ == "__main__":
    unittest.main()
