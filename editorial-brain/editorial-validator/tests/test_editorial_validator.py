from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "editorial-brain" / "editorial-validator" / "src"
sys.path.insert(0, str(SRC))

from editorial_validator.config import load_config
from editorial_validator.service import EditorialValidatorService


CONFIG_PATH = ROOT / "editorial-brain" / "editorial-validator" / "config" / "editorial-validator.config.json"
PACKAGE_PATH = ROOT / "editorial-brain" / "output" / "editorial-package-if-2026-07-06-liverpool-arsenal.json"


def load_package() -> dict:
    package = json.loads(PACKAGE_PATH.read_text(encoding="utf-8"))
    package["warnings"] = []
    return package


def load_test_config():
    config = load_config(CONFIG_PATH)
    temp_dir = tempfile.TemporaryDirectory()
    temp = Path(temp_dir.name)
    return replace(config, output_directory=temp / "output", log_directory=temp / "logs"), temp_dir


class EditorialValidatorTests(unittest.TestCase):
    def test_valid_editorial_package_passes_and_creates_validated_package(self):
        config, temp_dir = load_test_config()
        self.addCleanup(temp_dir.cleanup)
        result = EditorialValidatorService(config).run(load_package())
        self.assertTrue(result["success"])
        self.assertEqual(result["report"]["approval_status"], "approved")
        self.assertTrue(Path(result["validated_package_path"]).exists())

    def test_missing_central_question_fails(self):
        config, temp_dir = load_test_config()
        self.addCleanup(temp_dir.cleanup)
        package = load_package()
        package["central_question"] = ""
        result = EditorialValidatorService(config).run(package)
        self.assertFalse(result["success"])
        self.assertEqual(result["report"]["approval_status"], "rejected")
        self.assertIn("central_question is missing", result["report"]["issues_found"])

    def test_generic_story_angle_fails(self):
        config, temp_dir = load_test_config()
        self.addCleanup(temp_dir.cleanup)
        package = load_package()
        package["story_angle"] = "Liverpool vs Arsenal match preview."
        package["locked_fields"]["story_angle"] = package["story_angle"]
        result = EditorialValidatorService(config).run(package)
        self.assertFalse(result["success"])
        self.assertIn("story_angle is generic", result["report"]["issues_found"])

    def test_betting_language_fails(self):
        config, temp_dir = load_test_config()
        self.addCleanup(temp_dir.cleanup)
        package = load_package()
        package["viewer_takeaway"] = "This is a guaranteed safe bet."
        result = EditorialValidatorService(config).run(package)
        self.assertFalse(result["success"])
        self.assertTrue(any("betting language" in issue for issue in result["report"]["issues_found"]))

    def test_unsupported_claim_fails(self):
        config, temp_dir = load_test_config()
        self.addCleanup(temp_dir.cleanup)
        package = load_package()
        package["insight_summary"] = "A red card will decide the match."
        result = EditorialValidatorService(config).run(package)
        self.assertFalse(result["success"])
        self.assertTrue(any("unsupported claim" in issue for issue in result["report"]["issues_found"]))

    def test_low_confidence_fails(self):
        config, temp_dir = load_test_config()
        self.addCleanup(temp_dir.cleanup)
        package = load_package()
        package["confidence_scores"]["evidence_filter"] = 50
        result = EditorialValidatorService(config).run(package)
        self.assertFalse(result["success"])
        self.assertTrue(any("confidence below threshold" in issue for issue in result["report"]["issues_found"]))

    def test_locked_field_mismatch_fails(self):
        config, temp_dir = load_test_config()
        self.addCleanup(temp_dir.cleanup)
        package = load_package()
        package["locked_fields"]["central_question"] = "Changed?"
        result = EditorialValidatorService(config).run(package)
        self.assertFalse(result["success"])
        self.assertIn("locked field mismatch: central_question", result["report"]["issues_found"])

    def test_needs_human_review_when_warnings_present(self):
        config, temp_dir = load_test_config()
        self.addCleanup(temp_dir.cleanup)
        package = load_package()
        package["warnings"] = ["FACT_CHECK_REQUIRED"]
        result = EditorialValidatorService(config).run(package)
        self.assertFalse(result["success"])
        self.assertEqual(result["report"]["approval_status"], "needs_human_review")
        self.assertIn("FACT_CHECK_REQUIRED", result["report"]["human_review_flags"])

    def test_rejection_report_is_created(self):
        config, temp_dir = load_test_config()
        self.addCleanup(temp_dir.cleanup)
        package = load_package()
        package["central_question"] = ""
        result = EditorialValidatorService(config).run(package)
        self.assertTrue(Path(result["report_path"]).exists())
        self.assertNotIn("validated_package_path", result)


if __name__ == "__main__":
    unittest.main()
