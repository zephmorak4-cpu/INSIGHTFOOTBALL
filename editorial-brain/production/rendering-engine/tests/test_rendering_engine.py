from __future__ import annotations

import copy
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[4]
SRC = ROOT / "editorial-brain" / "production" / "rendering-engine" / "shared"
sys.path.insert(0, str(SRC))

from rendering_engine.core import (
    BRAND_MOTION_STANDARD,
    CreatomateAdapter,
    FFmpegAdapter,
    RemotionAdapter,
    RenderJobBuilder,
    RenderQueueManager,
    artifact_manager,
    get_renderer,
    render_validator,
    run_all,
)
from rendering_engine.io import load_json

PACKAGE = ROOT / "editorial-brain" / "output" / "renderer-ready-package.json"


class RenderingEngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.package = load_json(PACKAGE)

    def test_supported_renderers_registered(self):
        self.assertEqual(get_renderer("placeholder").renderer_profile, "placeholder")
        self.assertEqual(get_renderer("creatomate").renderer_profile, "creatomate")
        self.assertEqual(get_renderer("remotion").renderer_profile, "remotion")
        self.assertEqual(get_renderer("ffmpeg").renderer_profile, "ffmpeg")

    def test_unsupported_renderer_fails(self):
        with self.assertRaises(ValueError):
            get_renderer("unknown")

    def test_required_methods_exist(self):
        renderer = get_renderer("placeholder")
        for method in ["validate_package", "build_render_payload", "submit_render", "check_status", "download_artifacts", "cancel_render", "estimate_cost", "estimate_duration"]:
            self.assertTrue(callable(getattr(renderer, method)))

    def test_dry_run_mode_works(self):
        renderer = CreatomateAdapter()
        self.assertTrue(renderer.validate_package(self.package, dry_run=True)["success"])

    def test_creatomate_builds_payload_dry_run(self):
        payload = CreatomateAdapter().build_render_payload(self.package)
        self.assertEqual(payload["renderer"], "creatomate")
        self.assertGreater(len(payload["modifications"]), 0)

    def test_brand_motion_standard_is_embedded(self):
        payload = CreatomateAdapter().build_render_payload(self.package)
        self.assertEqual(payload["brand_motion_standard"]["standard_id"], "IF-BMS-1.0")
        self.assertTrue(BRAND_MOTION_STANDARD["persistent_logo"]["required"])

    def test_creatomate_missing_api_key_does_not_fail_dry_run(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertTrue(CreatomateAdapter().validate_package(self.package, dry_run=True)["success"])

    def test_creatomate_missing_api_key_fails_live(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertFalse(CreatomateAdapter().validate_package(self.package, dry_run=False)["success"])

    def test_creatomate_scene_mapping(self):
        payload = CreatomateAdapter().build_render_payload(self.package)
        self.assertEqual(len(payload["modifications"]), len(self.package["timeline"]["scenes"]))

    def test_creatomate_asset_mapping(self):
        payload = CreatomateAdapter().build_render_payload(self.package)
        self.assertTrue(all("assets" in scene for scene in payload["modifications"]))

    def test_creatomate_caption_mapping(self):
        payload = CreatomateAdapter().build_render_payload(self.package)
        self.assertEqual(len(payload["captions"]), len(self.package["caption_sync"]["captions"]))

    def test_remotion_stub_interface(self):
        self.assertEqual(RemotionAdapter().renderer_profile, "remotion")

    def test_remotion_not_implemented_response(self):
        payload = RemotionAdapter().build_render_payload(self.package)
        self.assertEqual(payload["status"], "not_implemented")

    def test_ffmpeg_creates_placeholder_when_incomplete(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(RuntimeError):
                FFmpegAdapter().download_artifacts("job", Path(temp))

    def test_ffmpeg_failure_when_unavailable(self):
        with patch("shutil.which", return_value=None), patch("imageio_ffmpeg.get_ffmpeg_exe", return_value="missing-ffmpeg"):
            payload = FFmpegAdapter().build_render_payload(self.package)
            result = FFmpegAdapter().submit_render(payload)
            self.assertFalse(result["success"])

    def test_ffmpeg_output_path(self):
        payload = FFmpegAdapter().build_render_payload(self.package)
        self.assertEqual(payload["output_format"], "mp4")
        self.assertGreater(len(payload["segments"]), 0)
        self.assertEqual(payload["segments"][0]["kind"], "opening_sting")

    def test_ffmpeg_real_artifact_contract(self):
        with tempfile.TemporaryDirectory() as temp:
            renderer = FFmpegAdapter()
            payload = renderer.build_render_payload(self.package)

            def fake_encode(ffmpeg_path, concat_path, video_path):
                Path(video_path).write_bytes(b"fake mp4")

            with patch("rendering_engine.core._ffmpeg_path", return_value="ffmpeg"), patch("rendering_engine.core._run_ffmpeg_encode", side_effect=fake_encode):
                artifacts = renderer.download_artifacts("job", Path(temp))
            self.assertTrue(Path(artifacts["final_video_path"]).exists())
            self.assertTrue(Path(artifacts["thumbnail_path"]).exists())
            self.assertFalse(artifacts["placeholder"])

    def test_ffmpeg_does_not_silently_fail(self):
        with patch("shutil.which", return_value=None):
            result = FFmpegAdapter().submit_render({"ffmpeg_path": None})
            self.assertIn("error", result)

    def test_render_job_created(self):
        renderer = get_renderer("placeholder")
        job = RenderJobBuilder().build(self.package, renderer, renderer.build_render_payload(self.package))
        self.assertEqual(job["status"], "queued")

    def test_job_includes_renderer_profile(self):
        renderer = get_renderer("placeholder")
        self.assertEqual(RenderJobBuilder().build(self.package, renderer, renderer.build_render_payload(self.package))["renderer_profile"], "placeholder")

    def test_job_includes_render_settings(self):
        renderer = get_renderer("placeholder")
        self.assertIn("output_settings", RenderJobBuilder().build(self.package, renderer, renderer.build_render_payload(self.package)))

    def test_job_includes_brand_motion_standard(self):
        renderer = get_renderer("placeholder")
        job = RenderJobBuilder().build(self.package, renderer, renderer.build_render_payload(self.package))
        self.assertEqual(job["brand_motion_standard"]["standard_id"], "IF-BMS-1.0")

    def test_job_estimates_duration(self):
        renderer = get_renderer("placeholder")
        self.assertEqual(RenderJobBuilder().build(self.package, renderer, renderer.build_render_payload(self.package))["estimated_duration_seconds"], 60.0)

    def test_job_estimates_cost(self):
        renderer = get_renderer("placeholder")
        self.assertEqual(RenderJobBuilder().build(self.package, renderer, renderer.build_render_payload(self.package))["estimated_cost"], 0.0)

    def test_job_schema_shape(self):
        renderer = get_renderer("placeholder")
        job = RenderJobBuilder().build(self.package, renderer, renderer.build_render_payload(self.package))
        self.assertIn("job_id", job)

    def test_queue_job(self):
        renderer = get_renderer("placeholder")
        job = RenderJobBuilder().build(self.package, renderer, renderer.build_render_payload(self.package))
        self.assertEqual(RenderQueueManager().queue(job)["status"], "queued")

    def test_queue_updates_status(self):
        renderer = get_renderer("placeholder")
        job = RenderJobBuilder().build(self.package, renderer, renderer.build_render_payload(self.package))
        self.assertEqual(RenderQueueManager().update(job, "rendering")["progress"], 60)

    def test_queue_completed(self):
        renderer = get_renderer("placeholder")
        job = RenderJobBuilder().build(self.package, renderer, renderer.build_render_payload(self.package))
        self.assertEqual(RenderQueueManager().update(job, "completed")["status"], "completed")

    def test_queue_failed(self):
        renderer = get_renderer("placeholder")
        job = RenderJobBuilder().build(self.package, renderer, renderer.build_render_payload(self.package))
        self.assertEqual(RenderQueueManager().update(job, "failed", errors=["x"])["errors"], ["x"])

    def test_queue_cancelled(self):
        renderer = get_renderer("placeholder")
        job = RenderJobBuilder().build(self.package, renderer, renderer.build_render_payload(self.package))
        self.assertEqual(RenderQueueManager().update(job, "cancelled")["status"], "cancelled")

    def test_artifact_folder_created(self):
        with tempfile.TemporaryDirectory() as temp:
            renderer = get_renderer("placeholder")
            job = RenderJobBuilder().build(self.package, renderer, renderer.build_render_payload(self.package))
            artifacts = artifact_manager(self.package, job, renderer, {}, Path(temp))
            self.assertTrue(Path(artifacts["artifact_root"]).exists())

    def test_artifact_stores_payloads(self):
        with tempfile.TemporaryDirectory() as temp:
            renderer = get_renderer("placeholder")
            payload = renderer.build_render_payload(self.package)
            job = RenderJobBuilder().build(self.package, renderer, payload)
            artifacts = artifact_manager(self.package, job, renderer, payload, Path(temp))
            self.assertTrue(Path(artifacts["payload_path"]).exists())

    def test_artifact_checksums(self):
        with tempfile.TemporaryDirectory() as temp:
            renderer = get_renderer("placeholder")
            payload = renderer.build_render_payload(self.package)
            job = RenderJobBuilder().build(self.package, renderer, payload)
            artifacts = artifact_manager(self.package, job, renderer, payload, Path(temp))
            self.assertTrue(artifacts["checksums"])

    def test_artifact_flags_missing(self):
        with tempfile.TemporaryDirectory() as temp:
            renderer = get_renderer("placeholder")
            job = RenderJobBuilder().build(self.package, renderer, renderer.build_render_payload(self.package))
            artifacts = artifact_manager(self.package, job, renderer, {}, Path(temp))
            self.assertEqual(artifacts["missing_artifacts"], [])

    def test_artifact_schema_shape(self):
        with tempfile.TemporaryDirectory() as temp:
            renderer = get_renderer("placeholder")
            job = RenderJobBuilder().build(self.package, renderer, renderer.build_render_payload(self.package))
            artifacts = artifact_manager(self.package, job, renderer, {}, Path(temp))
            self.assertIn("final_video_path", artifacts)

    def validator_inputs(self):
        renderer = get_renderer("placeholder")
        payload = renderer.build_render_payload(self.package)
        job = RenderJobBuilder().build(self.package, renderer, payload)
        artifacts = artifact_manager(self.package, job, renderer, payload, ROOT)
        status = RenderQueueManager().update(job, "completed", artifact_refs=artifacts)
        return job, status, artifacts

    def test_valid_artifact_passes(self):
        job, status, artifacts = self.validator_inputs()
        self.assertEqual(render_validator(self.package, job, status, artifacts)["approval_status"], "approved")

    def test_brand_motion_missing_fails_validation(self):
        job, status, artifacts = self.validator_inputs()
        job["brand_motion_standard"] = {}
        report = render_validator(self.package, job, status, artifacts)
        self.assertEqual(report["approval_status"], "blocked")
        self.assertFalse(report["checks"]["brand_motion_standard"])

    def test_missing_video_placeholder_accepted(self):
        job, status, artifacts = self.validator_inputs()
        self.assertTrue(render_validator(self.package, job, status, artifacts, allow_placeholder=True)["checks"]["video_exists_or_placeholder"])

    def test_duration_above_60_fails(self):
        package = copy.deepcopy(self.package)
        package["timeline"]["total_duration_seconds"] = 61
        job, status, artifacts = self.validator_inputs()
        self.assertEqual(render_validator(package, job, status, artifacts)["approval_status"], "blocked")

    def test_wrong_aspect_ratio_fails(self):
        package = copy.deepcopy(self.package)
        package["timeline"]["aspect_ratio"] = "16:9"
        job, status, artifacts = self.validator_inputs()
        self.assertEqual(render_validator(package, job, status, artifacts)["approval_status"], "blocked")

    def test_missing_thumbnail_warns(self):
        job, status, artifacts = self.validator_inputs()
        Path(artifacts["thumbnail_path"]).unlink()
        self.assertTrue(render_validator(self.package, job, status, artifacts)["warnings"])

    def test_blocked_legal_asset_fails(self):
        package = copy.deepcopy(self.package)
        package["render_readiness_status"] = "failed_validation"
        job, status, artifacts = self.validator_inputs()
        self.assertEqual(render_validator(package, job, status, artifacts)["approval_status"], "blocked")

    def test_final_package_created(self):
        self.assertIn("render_complete_package", run_all(ROOT))

    def test_final_package_approval_status(self):
        self.assertEqual(run_all(ROOT)["render_complete_package"]["approval_status"], "approved")

    def test_placeholder_mode_documented(self):
        self.assertTrue(run_all(ROOT)["render_complete_package"]["render_validation_report"]["placeholder_mode"])

    def test_final_package_includes_brand_motion_standard(self):
        package = run_all(ROOT)["render_complete_package"]
        self.assertEqual(package["brand_motion_standard"]["standard_id"], "IF-BMS-1.0")

    def test_next_component(self):
        self.assertEqual(run_all(ROOT)["render_complete_package"]["next_component"], "Final Quality Control")

    def test_final_schema_shape(self):
        package = run_all(ROOT)["render_complete_package"]
        self.assertIn("render_artifacts", package)
        self.assertIn("render_validation_report", package)


if __name__ == "__main__":
    unittest.main()
