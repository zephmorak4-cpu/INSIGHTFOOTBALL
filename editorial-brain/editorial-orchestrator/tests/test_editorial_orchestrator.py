from __future__ import annotations

import json
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "editorial-brain" / "editorial-orchestrator" / "src"
sys.path.insert(0, str(SRC))

from editorial_orchestrator.config import load_config
from editorial_orchestrator.package_assembler import assemble_editorial_package
from editorial_orchestrator.service import EditorialOrchestrator
from editorial_orchestrator.validation import OrchestratorValidator


CONFIG_PATH = ROOT / "editorial-brain" / "editorial-orchestrator" / "config" / "editorial-orchestrator.config.json"
DAILY_INPUT_PATH = ROOT / "editorial-brain" / "examples" / "liverpool-arsenal-daily-input.json"
MATCH_SELECTION_PATH = ROOT / "editorial-brain" / "output" / "match-selection-liverpool-arsenal.json"
STORY_HUNTER_PATH = ROOT / "editorial-brain" / "output" / "story-hunter-liverpool-arsenal.json"
EVIDENCE_FILTER_PATH = ROOT / "editorial-brain" / "output" / "evidence-filter-liverpool-arsenal.json"
INSIGHT_ENGINE_PATH = ROOT / "editorial-brain" / "output" / "insight-engine-liverpool-arsenal.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_test_config():
    config = load_config(CONFIG_PATH)
    temp_dir = tempfile.TemporaryDirectory()
    temp_path = Path(temp_dir.name)
    return replace(config, output_directory=temp_path / "output", log_directory=temp_path / "logs"), temp_dir


class EditorialOrchestratorTests(unittest.TestCase):
    def test_assembles_valid_canonical_package(self):
        config, temp_dir = load_test_config()
        self.addCleanup(temp_dir.cleanup)
        daily_input = load_json(DAILY_INPUT_PATH)
        match_selection = load_json(MATCH_SELECTION_PATH)
        story_hunter = load_json(STORY_HUNTER_PATH)
        evidence_filter = load_json(EVIDENCE_FILTER_PATH)
        insight_engine = load_json(INSIGHT_ENGINE_PATH)
        package = assemble_editorial_package(
            daily_input=daily_input,
            match_selection=match_selection,
            story_hunter=story_hunter,
            evidence_filter=evidence_filter,
            insight_engine=insight_engine,
            execution_metadata={
                "started_at": "2026-07-06T00:00:00+00:00",
                "completed_at": "2026-07-06T00:00:01+00:00",
                "duration_ms": 1000,
                "stages": [],
            },
        )

        OrchestratorValidator(config.package_schema_path, config.minimum_confidence).validate_package(package)
        self.assertEqual(package["match_edge"], "Slight Home Edge")
        self.assertEqual(package["confidence_scores"]["overall"], 83.5)

    def test_locked_field_change_fails(self):
        config, temp_dir = load_test_config()
        self.addCleanup(temp_dir.cleanup)
        story_hunter = load_json(STORY_HUNTER_PATH)
        evidence_filter = load_json(EVIDENCE_FILTER_PATH)
        insight_engine = load_json(INSIGHT_ENGINE_PATH)
        evidence_filter["locked_fields"]["central_question"] = "Changed?"

        with self.assertRaises(Exception) as context:
            OrchestratorValidator(config.package_schema_path, config.minimum_confidence).validate_locked_fields(
                story_hunter=story_hunter,
                evidence_filter=evidence_filter,
                insight_engine=insight_engine,
            )
        self.assertIn("Evidence Filter changed locked field", str(context.exception.issues))

    def test_full_liverpool_arsenal_integration_run(self):
        config, temp_dir = load_test_config()
        self.addCleanup(temp_dir.cleanup)
        daily_input = load_json(DAILY_INPUT_PATH)
        result = EditorialOrchestrator(config, workspace_root=ROOT).run(daily_input)

        self.assertTrue(result["success"])
        package_path = Path(result["package_path"])
        report_path = Path(result["report_path"])
        self.assertTrue(package_path.exists())
        self.assertTrue(report_path.exists())

        package = load_json(package_path)
        report = load_json(report_path)
        self.assertEqual(package["metadata"]["production_id"], "if-2026-07-06-liverpool-arsenal")
        self.assertEqual(package["central_question"], "Can Arsenal survive Liverpool's fast start?")
        self.assertEqual(package["match_edge"], "Slight Home Edge")
        self.assertEqual(len(report["stages"]), 4)
        self.assertEqual(report["status"], "success")


if __name__ == "__main__":
    unittest.main()
