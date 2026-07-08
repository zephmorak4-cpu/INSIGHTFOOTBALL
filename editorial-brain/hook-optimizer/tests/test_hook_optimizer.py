from __future__ import annotations

import json
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPT_SRC = ROOT / "editorial-brain" / "scriptwriter" / "src"
SRC = ROOT / "editorial-brain" / "hook-optimizer" / "src"
sys.path.insert(0, str(SCRIPT_SRC))
sys.path.insert(0, str(SRC))

from hook_optimizer.config import load_config
from hook_optimizer.llm import RuleBasedHookOptimizerClient
from hook_optimizer.service import HookOptimizerService
from scriptwriter.config import load_config as load_script_config
from scriptwriter.json_utils import load_json_file
from scriptwriter.llm import RuleBasedScriptwriterClient


CONFIG_PATH = ROOT / "editorial-brain" / "hook-optimizer" / "config" / "hook-optimizer.config.json"
SCRIPT_CONFIG_PATH = ROOT / "editorial-brain" / "scriptwriter" / "config" / "scriptwriter.config.json"
BRIEF_PATH = ROOT / "editorial-brain" / "output" / "production-brief-if-2026-07-06-liverpool-arsenal.json"


class StaticClient:
    def __init__(self, payload: dict):
        self.payload = payload

    def generate(self, prompt: str, *, temperature: float, max_tokens: int) -> str:
        return json.dumps(self.payload)


def sample_inputs():
    brief = load_json_file(BRIEF_PATH)
    script_config = load_script_config(SCRIPT_CONFIG_PATH)
    script = json.loads(RuleBasedScriptwriterClient(brief, script_config).generate("", temperature=0, max_tokens=0))
    return script, brief


class HookOptimizerTests(unittest.TestCase):
    def run_service(self, script, brief, client=None):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        config = replace(load_config(CONFIG_PATH), output_directory=Path(temp_dir.name) / "output", log_directory=Path(temp_dir.name) / "logs")
        client = client or RuleBasedHookOptimizerClient(script, brief, config)
        return HookOptimizerService(config, client).run(script, brief)

    def test_produces_3_hook_options(self):
        script, brief = sample_inputs()
        result = self.run_service(script, brief)
        self.assertEqual(len(result["optimization"]["hook_options"]), 3)

    def test_selects_one_hook(self):
        script, brief = sample_inputs()
        result = self.run_service(script, brief)
        self.assertIn(result["optimization"]["selected_hook"], result["optimization"]["hook_options"])

    def test_does_not_change_surprising_fact(self):
        script, brief = sample_inputs()
        result = self.run_service(script, brief)
        self.assertIn(brief["surprising_fact"], result["optimized_script"]["hook"])

    def test_does_not_change_central_question(self):
        script, brief = sample_inputs()
        result = self.run_service(script, brief)
        self.assertEqual(result["optimized_script"]["central_question"], brief["central_question"])

    def test_rejects_clickbait(self):
        script, brief = sample_inputs()
        bad = {
            "production_id": brief["production_id"],
            "component_id": "S3-C02",
            "component_name": "Hook Optimizer",
            "timestamp": "now",
            "original_hook": script["hook"],
            "hook_options": ["You won't believe this shocking outcome.", brief["surprising_fact"], brief["surprising_fact"]],
            "selected_hook": brief["surprising_fact"],
            "selection_reason": "test",
            "rejected_hooks": [],
            "locked_fields_preserved": True,
            "warnings": [],
            "approval_status": "approved",
        }
        result = self.run_service(script, brief, StaticClient(bad))
        self.assertFalse(result["success"])
        self.assertTrue(any("clickbait" in issue for issue in result["error"]["issues"]))

    def test_rejects_betting_language(self):
        script, brief = sample_inputs()
        bad = {
            "production_id": brief["production_id"],
            "component_id": "S3-C02",
            "component_name": "Hook Optimizer",
            "timestamp": "now",
            "original_hook": script["hook"],
            "hook_options": [brief["surprising_fact"] + " Guaranteed.", brief["surprising_fact"], brief["surprising_fact"]],
            "selected_hook": brief["surprising_fact"],
            "selection_reason": "test",
            "rejected_hooks": [],
            "locked_fields_preserved": True,
            "warnings": [],
            "approval_status": "approved",
        }
        result = self.run_service(script, brief, StaticClient(bad))
        self.assertFalse(result["success"])
        self.assertTrue(any("betting" in issue for issue in result["error"]["issues"]))


if __name__ == "__main__":
    unittest.main()

