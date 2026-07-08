from __future__ import annotations

import json
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
VALIDATOR_SRC = ROOT / "editorial-brain" / "editorial-validator" / "src"
SRC = ROOT / "editorial-brain" / "production-brief-generator" / "src"
sys.path.insert(0, str(VALIDATOR_SRC))
sys.path.insert(0, str(SRC))

from editorial_validator.config import load_config as load_validator_config
from editorial_validator.service import EditorialValidatorService
from production_brief_generator.config import load_config
from production_brief_generator.service import ProductionBriefGeneratorService


CONFIG_PATH = ROOT / "editorial-brain" / "production-brief-generator" / "config" / "production-brief-generator.config.json"
VALIDATOR_CONFIG_PATH = ROOT / "editorial-brain" / "editorial-validator" / "config" / "editorial-validator.config.json"
PACKAGE_PATH = ROOT / "editorial-brain" / "output" / "editorial-package-if-2026-07-06-liverpool-arsenal.json"


def load_package() -> dict:
    package = json.loads(PACKAGE_PATH.read_text(encoding="utf-8"))
    package["warnings"] = []
    return package


def approved_package(temp: Path) -> dict:
    validator_config = load_validator_config(VALIDATOR_CONFIG_PATH)
    validator_config = replace(validator_config, output_directory=temp / "validator-output", log_directory=temp / "logs")
    result = EditorialValidatorService(validator_config).run(load_package())
    return result["validated_package"]


def load_test_config():
    config = load_config(CONFIG_PATH)
    temp_dir = tempfile.TemporaryDirectory()
    temp = Path(temp_dir.name)
    return replace(config, output_directory=temp / "output", log_directory=temp / "logs"), temp_dir, temp


class ProductionBriefGeneratorTests(unittest.TestCase):
    def test_approved_package_produces_valid_brief(self):
        config, temp_dir, temp = load_test_config()
        self.addCleanup(temp_dir.cleanup)
        result = ProductionBriefGeneratorService(config).run(approved_package(temp))
        self.assertTrue(result["success"])
        self.assertEqual(result["brief"]["next_agent"], "IF-A05")
        self.assertTrue(Path(result["brief_path"]).exists())

    def test_rejected_package_cannot_produce_brief(self):
        config, temp_dir, temp = load_test_config()
        self.addCleanup(temp_dir.cleanup)
        package = approved_package(temp)
        package["approval_status"] = "rejected"
        result = ProductionBriefGeneratorService(config).run(package)
        self.assertFalse(result["success"])

    def test_missing_required_fields_fails(self):
        config, temp_dir, temp = load_test_config()
        self.addCleanup(temp_dir.cleanup)
        package = approved_package(temp)
        package.pop("central_question")
        result = ProductionBriefGeneratorService(config).run(package)
        self.assertFalse(result["success"])

    def test_locked_fields_preserved(self):
        config, temp_dir, temp = load_test_config()
        self.addCleanup(temp_dir.cleanup)
        package = approved_package(temp)
        result = ProductionBriefGeneratorService(config).run(package)
        self.assertEqual(result["brief"]["locked_fields"], package["locked_fields"])

    def test_forbidden_phrases_included(self):
        config, temp_dir, temp = load_test_config()
        self.addCleanup(temp_dir.cleanup)
        result = ProductionBriefGeneratorService(config).run(approved_package(temp))
        self.assertIn("guaranteed", result["brief"]["forbidden_phrases"])
        self.assertIn("bet of the day", result["brief"]["forbidden_phrases"])

    def test_brand_opening_included(self):
        config, temp_dir, temp = load_test_config()
        self.addCleanup(temp_dir.cleanup)
        result = ProductionBriefGeneratorService(config).run(approved_package(temp))
        self.assertEqual(result["brief"]["brand_opening"], "Before the first whistle... here's the insight.")

    def test_cta_direction_included(self):
        config, temp_dir, temp = load_test_config()
        self.addCleanup(temp_dir.cleanup)
        result = ProductionBriefGeneratorService(config).run(approved_package(temp))
        self.assertIn("Ask viewers", result["brief"]["cta_direction"])

    def test_brief_schema_validates(self):
        config, temp_dir, temp = load_test_config()
        self.addCleanup(temp_dir.cleanup)
        result = ProductionBriefGeneratorService(config).run(approved_package(temp))
        self.assertTrue(result["success"])
        self.assertGreaterEqual(len(result["brief"]["evidence_to_use"]), 1)


if __name__ == "__main__":
    unittest.main()
