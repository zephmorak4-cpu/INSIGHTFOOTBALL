from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "distribution" / "publishing-engine" / "shared"
sys.path.insert(0, str(SRC))

from publishing_engine.core import (
    facebook_payload,
    generate_metadata,
    publish_report,
    publishing_schedule,
    publishing_status,
    publishing_validator,
    run_all,
    telegram_payload,
    youtube_payload,
)
from publishing_engine.io import load_json

PACKAGE = ROOT / "editorial-brain" / "output" / "publish-ready-package.json"


class PublishingEngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.package = load_json(PACKAGE)

    def metadata(self):
        return generate_metadata(copy.deepcopy(self.package), root=ROOT)

    def payloads(self, dry_run=True):
        metadata = self.metadata()
        return [
            youtube_payload(self.package, metadata, dry_run=dry_run, root=ROOT),
            facebook_payload(self.package, metadata, dry_run=dry_run, root=ROOT),
            telegram_payload(self.package, metadata, dry_run=dry_run, root=ROOT),
        ]

    def test_generates_title_options(self):
        self.assertGreaterEqual(len(self.metadata()["title_options"]), 3)

    def test_selects_title(self):
        self.assertTrue(self.metadata()["selected_title"])

    def test_generates_youtube_description(self):
        self.assertIn("#InsightFootball", self.metadata()["youtube_description"])

    def test_generates_facebook_caption(self):
        self.assertTrue(self.metadata()["facebook_caption"])

    def test_generates_telegram_post(self):
        self.assertTrue(self.metadata()["telegram_post"])

    def test_rejects_betting_language(self):
        package = copy.deepcopy(self.package)
        package["description_seed"] = "Guaranteed Liverpool win"
        self.assertEqual(generate_metadata(package, root=ROOT)["approval_status"], "blocked")

    def test_rejects_clickbait_certainty(self):
        package = copy.deepcopy(self.package)
        package["description_seed"] = "100% correct prediction"
        self.assertFalse(generate_metadata(package, root=ROOT)["forbidden_language_check"]["passed"])

    def test_metadata_schema_shape(self):
        self.assertIn("hashtags", self.metadata())

    def test_youtube_dry_run_without_credentials(self):
        with patch.dict("os.environ", {}, clear=True):
            self.assertEqual(youtube_payload(self.package, self.metadata(), dry_run=True, root=ROOT)["approval_status"], "approved")

    def test_youtube_live_fails_without_credentials(self):
        with patch.dict("os.environ", {}, clear=True):
            self.assertEqual(youtube_payload(self.package, self.metadata(), dry_run=False, root=ROOT)["approval_status"], "blocked")

    def test_youtube_payload_video_path(self):
        self.assertIn("video_path", youtube_payload(self.package, self.metadata(), root=ROOT))

    def test_youtube_payload_title_description(self):
        payload = youtube_payload(self.package, self.metadata(), root=ROOT)
        self.assertTrue(payload["title"])
        self.assertTrue(payload["description"])

    def test_youtube_schema_shape(self):
        self.assertEqual(youtube_payload(self.package, self.metadata(), root=ROOT)["platform"], "youtube")

    def test_facebook_dry_run_without_credentials(self):
        with patch.dict("os.environ", {}, clear=True):
            self.assertEqual(facebook_payload(self.package, self.metadata(), dry_run=True, root=ROOT)["approval_status"], "approved")

    def test_facebook_live_fails_without_credentials(self):
        with patch.dict("os.environ", {}, clear=True):
            self.assertEqual(facebook_payload(self.package, self.metadata(), dry_run=False, root=ROOT)["approval_status"], "blocked")

    def test_facebook_payload_caption(self):
        self.assertTrue(facebook_payload(self.package, self.metadata(), root=ROOT)["caption"])

    def test_facebook_schema_shape(self):
        self.assertEqual(facebook_payload(self.package, self.metadata(), root=ROOT)["platform"], "facebook")

    def test_telegram_dry_run_without_credentials(self):
        with patch.dict("os.environ", {}, clear=True):
            self.assertEqual(telegram_payload(self.package, self.metadata(), dry_run=True, root=ROOT)["approval_status"], "approved")

    def test_telegram_live_fails_without_credentials(self):
        with patch.dict("os.environ", {}, clear=True):
            self.assertEqual(telegram_payload(self.package, self.metadata(), dry_run=False, root=ROOT)["approval_status"], "blocked")

    def test_telegram_payload_message(self):
        self.assertTrue(telegram_payload(self.package, self.metadata(), root=ROOT)["message_text"])

    def test_telegram_schema_shape(self):
        self.assertEqual(telegram_payload(self.package, self.metadata(), root=ROOT)["platform"], "telegram")

    def test_publish_now_schedule(self):
        self.assertEqual(publishing_schedule(self.package, root=ROOT)["schedule_mode"], "publish_now")

    def test_scheduled_publish(self):
        self.assertEqual(publishing_schedule(self.package, root=ROOT, mode="scheduled")["schedule_mode"], "scheduled")

    def test_timezone_included(self):
        self.assertEqual(publishing_schedule(self.package, root=ROOT)["timezone"], "Africa/Lagos")

    def test_schedule_schema_shape(self):
        self.assertIn("publish_times", publishing_schedule(self.package, root=ROOT))

    def test_queue_jobs(self):
        schedule = publishing_schedule(self.package, root=ROOT)
        validation = publishing_validator(self.package, self.metadata(), self.payloads(), root=ROOT)
        self.assertEqual(len(publishing_status(self.package, self.payloads(), schedule, validation, root=ROOT)["jobs"]), 3)

    def test_queue_dry_run_complete(self):
        schedule = publishing_schedule(self.package, root=ROOT)
        validation = publishing_validator(self.package, self.metadata(), self.payloads(), root=ROOT)
        self.assertEqual(publishing_status(self.package, self.payloads(), schedule, validation, root=ROOT)["overall_status"], "dry_run_complete")

    def test_queue_failed_job(self):
        schedule = publishing_schedule(self.package, root=ROOT)
        validation = {"approval_status": "blocked", "warnings": []}
        self.assertEqual(publishing_status(self.package, self.payloads(), schedule, validation, root=ROOT)["overall_status"], "failed")

    def test_queue_cancelled_schema_status(self):
        schedule = publishing_schedule(self.package, root=ROOT)
        validation = publishing_validator(self.package, self.metadata(), self.payloads(), root=ROOT)
        self.assertIn("overall_status", publishing_status(self.package, self.payloads(), schedule, validation, root=ROOT))

    def test_status_schema_shape(self):
        schedule = publishing_schedule(self.package, root=ROOT)
        validation = publishing_validator(self.package, self.metadata(), self.payloads(), root=ROOT)
        self.assertIn("queue_id", publishing_status(self.package, self.payloads(), schedule, validation, root=ROOT))

    def test_validator_approved_package_passes_dry_run(self):
        report = publishing_validator(self.package, self.metadata(), self.payloads(), dry_run=True, root=ROOT)
        self.assertEqual(report["approval_status"], "approved")

    def test_validator_rejected_qc_fails(self):
        package = copy.deepcopy(self.package)
        package["approval_status"] = "rejected"
        report = publishing_validator(package, self.metadata(), self.payloads(), root=ROOT)
        self.assertEqual(report["approval_status"], "blocked")

    def test_validator_dry_run_without_credentials_passes(self):
        with patch.dict("os.environ", {}, clear=True):
            self.assertEqual(publishing_validator(self.package, self.metadata(), self.payloads(), dry_run=True, root=ROOT)["approval_status"], "approved")

    def test_validator_live_without_credentials_fails(self):
        payloads = self.payloads(dry_run=False)
        self.assertEqual(publishing_validator(self.package, self.metadata(), payloads, dry_run=False, root=ROOT)["approval_status"], "blocked")

    def test_validator_forbidden_language_fails(self):
        metadata = self.metadata()
        metadata["selected_title"] = "Guaranteed Liverpool Win"
        metadata["forbidden_language_check"] = {"passed": False, "matches": ["guaranteed"]}
        self.assertEqual(publishing_validator(self.package, metadata, self.payloads(), root=ROOT)["approval_status"], "blocked")

    def test_validator_legal_blocking_fails(self):
        package = copy.deepcopy(self.package)
        package["approval_status"] = "rejected"
        self.assertEqual(publishing_validator(package, self.metadata(), self.payloads(), root=ROOT)["approval_status"], "blocked")

    def test_report_dry_run_complete(self):
        result = run_all(ROOT)
        self.assertEqual(result["publishing_report"]["final_status"], "dry_run_complete")

    def test_report_published(self):
        status = {"jobs": [{"platform": "youtube", "status": "published", "dry_run": False}], "errors": [], "warnings": []}
        self.assertEqual(publish_report(self.package, self.metadata(), publishing_schedule(self.package, root=ROOT), status, root=ROOT)["publishing_report"]["final_status"], "published")

    def test_report_partial_failure(self):
        status = {"jobs": [{"platform": "youtube", "status": "published", "dry_run": False}, {"platform": "facebook", "status": "failed", "dry_run": False}], "errors": ["x"], "warnings": []}
        self.assertEqual(publish_report(self.package, self.metadata(), publishing_schedule(self.package, root=ROOT), status, root=ROOT)["publishing_report"]["final_status"], "partially_published")

    def test_published_package_schema_shape(self):
        self.assertEqual(run_all(ROOT)["published_package"]["next_component"], "Analytics Engine")


if __name__ == "__main__":
    unittest.main()
