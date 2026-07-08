from __future__ import annotations

import json
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPT_SRC = ROOT / "editorial-brain" / "scriptwriter" / "src"
HOOK_SRC = ROOT / "editorial-brain" / "hook-optimizer" / "src"
SRC = ROOT / "editorial-brain" / "cta-generator" / "src"
sys.path.insert(0, str(SCRIPT_SRC))
sys.path.insert(0, str(HOOK_SRC))
sys.path.insert(0, str(SRC))

from cta_generator.config import load_config
from cta_generator.llm import RuleBasedCtaGeneratorClient
from cta_generator.service import CtaGeneratorService
from hook_optimizer.config import load_config as load_hook_config
from hook_optimizer.llm import RuleBasedHookOptimizerClient
from hook_optimizer.service import HookOptimizerService
from scriptwriter.config import load_config as load_script_config
from scriptwriter.json_utils import load_json_file
from scriptwriter.llm import RuleBasedScriptwriterClient


CONFIG_PATH = ROOT / "editorial-brain" / "cta-generator" / "config" / "cta-generator.config.json"
HOOK_CONFIG_PATH = ROOT / "editorial-brain" / "hook-optimizer" / "config" / "hook-optimizer.config.json"
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
    temp_dir = tempfile.TemporaryDirectory()
    hook_config = replace(load_hook_config(HOOK_CONFIG_PATH), output_directory=Path(temp_dir.name) / "out", log_directory=Path(temp_dir.name) / "logs")
    optimized = HookOptimizerService(hook_config, RuleBasedHookOptimizerClient(script, brief, hook_config)).run(script, brief)["optimized_script"]
    temp_dir.cleanup()
    return optimized, brief


class CtaGeneratorTests(unittest.TestCase):
    def run_service(self, script, brief, client=None):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        config = replace(load_config(CONFIG_PATH), output_directory=Path(temp_dir.name) / "output", log_directory=Path(temp_dir.name) / "logs")
        client = client or RuleBasedCtaGeneratorClient(script, brief, config)
        return CtaGeneratorService(config, client).run(script, brief)

    def test_produces_cta_options(self):
        script, brief = sample_inputs()
        result = self.run_service(script, brief)
        self.assertEqual(len(result["cta"]["cta_options"]), 3)

    def test_selects_one_cta(self):
        script, brief = sample_inputs()
        result = self.run_service(script, brief)
        self.assertIn(result["cta"]["selected_cta"], result["cta"]["cta_options"])

    def test_rejects_generic_like_and_subscribe(self):
        script, brief = sample_inputs()
        bad = RuleBasedCtaGeneratorClient(script, brief, replace(load_config(CONFIG_PATH), output_directory=Path("."), log_directory=Path("."))).generate("", temperature=0, max_tokens=0)
        payload = json.loads(bad)
        payload["cta_options"][0] = "Like and subscribe."
        payload["selected_cta"] = payload["cta_options"][1]
        result = self.run_service(script, brief, StaticClient(payload))
        self.assertFalse(result["success"])
        self.assertTrue(any("generic CTA" in issue for issue in result["error"]["issues"]))

    def test_rejects_betting_cta(self):
        script, brief = sample_inputs()
        bad = RuleBasedCtaGeneratorClient(script, brief, replace(load_config(CONFIG_PATH), output_directory=Path("."), log_directory=Path("."))).generate("", temperature=0, max_tokens=0)
        payload = json.loads(bad)
        payload["cta_options"][0] = "Click the link to win free money."
        payload["selected_cta"] = payload["cta_options"][1]
        result = self.run_service(script, brief, StaticClient(payload))
        self.assertFalse(result["success"])
        self.assertTrue(any("betting CTA" in issue for issue in result["error"]["issues"]))

    def test_final_voiceover_remains_under_60_seconds(self):
        script, brief = sample_inputs()
        result = self.run_service(script, brief)
        self.assertLessEqual(result["cta"]["final_estimated_duration_seconds"], 60)

    def test_final_package_validates(self):
        script, brief = sample_inputs()
        result = self.run_service(script, brief)
        self.assertTrue(result["success"])
        self.assertEqual(result["final_package"]["next_agent"], "IF-A06")


if __name__ == "__main__":
    unittest.main()

