from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
SRC = ROOT / "editorial-brain" / "production" / "timeline-builder" / "shared"
sys.path.insert(0, str(SRC))

from timeline_builder_engine.core import (
    audio_synchronizer,
    caption_synchronizer,
    layer_composer,
    render_plan_generator,
    run_all,
    scene_composer,
    timeline_builder,
    timeline_validator,
)
from timeline_builder_engine.io import load_json

OUT = ROOT / "editorial-brain" / "output"


class TimelineBuilderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.storyboard = load_json(OUT / "final-storyboard-package.json")
        cls.visual = load_json(OUT / "visual-production-package.json")
        cls.voice = load_json(OUT / "voice-production-package.json")
        cls.assets = load_json(OUT / "media-asset-bundle.json")

    def build(self):
        return timeline_builder(copy.deepcopy(self.storyboard), copy.deepcopy(self.visual), copy.deepcopy(self.voice), copy.deepcopy(self.assets), root=ROOT)

    def composed(self):
        timeline = self.build()
        scenes = scene_composer(timeline, self.storyboard, self.visual, self.assets, root=ROOT)
        layers = layer_composer(timeline, scenes, self.assets, root=ROOT)
        captions = caption_synchronizer(timeline, layers, root=ROOT)
        audio = audio_synchronizer(timeline, self.voice, root=ROOT)
        render = render_plan_generator(timeline, layers, captions, audio, self.assets, root=ROOT)
        return timeline, scenes, layers, captions, audio, render

    def test_valid_inputs_create_timeline(self):
        self.assertEqual(self.build()["component_id"], "IF-TL01")

    def test_missing_storyboard_package_fails(self):
        with self.assertRaises(ValueError):
            timeline_builder({}, self.visual, self.voice, self.assets, root=ROOT)

    def test_missing_visual_package_fails(self):
        with self.assertRaises(ValueError):
            timeline_builder(self.storyboard, {}, self.voice, self.assets, root=ROOT)

    def test_missing_voice_package_fails(self):
        with self.assertRaises(ValueError):
            timeline_builder(self.storyboard, self.visual, {}, self.assets, root=ROOT)

    def test_missing_asset_bundle_fails(self):
        with self.assertRaises(ValueError):
            timeline_builder(self.storyboard, self.visual, self.voice, {}, root=ROOT)

    def test_total_duration_under_60(self):
        self.assertLessEqual(self.build()["total_duration_seconds"], 60)

    def test_scenes_ordered_correctly(self):
        starts = [scene["start_time_seconds"] for scene in self.build()["scenes"]]
        self.assertEqual(starts, sorted(starts))

    def test_timeline_schema_shape(self):
        timeline = self.build()
        for field in ["production_id", "component_id", "scenes", "fps", "aspect_ratio", "resolution"]:
            self.assertIn(field, timeline)

    def test_scene_compositions_created(self):
        timeline = self.build()
        scenes = scene_composer(timeline, self.storyboard, self.visual, self.assets, root=ROOT)
        self.assertEqual(len(scenes["scenes"]), len(timeline["scenes"]))

    def test_scene_maps_templates(self):
        timeline = self.build()
        scenes = scene_composer(timeline, self.storyboard, self.visual, self.assets, root=ROOT)
        self.assertTrue(all(scene["template_id"] for scene in scenes["scenes"]))

    def test_scene_applies_fallback_templates(self):
        storyboard = copy.deepcopy(self.storyboard)
        visual = copy.deepcopy(self.visual)
        visual["visual_plan"]["scenes"][0].pop("template_id")
        timeline = timeline_builder(storyboard, visual, self.voice, self.assets, root=ROOT)
        self.assertTrue(timeline["scenes"][0]["template_id"])

    def test_scene_includes_visual_asset_audio_refs(self):
        timeline = self.build()
        scene = scene_composer(timeline, self.storyboard, self.visual, self.assets, root=ROOT)["scenes"][0]
        self.assertIn("foreground", scene)
        self.assertIn("audio_segment_ref", scene)

    def test_scene_schema_shape(self):
        self.assertIn("component_id", scene_composer(self.build(), self.storyboard, self.visual, self.assets, root=ROOT))

    def test_layer_order(self):
        _, _, layers, _, _, _ = self.composed()
        order = [layer["layer_type"] for layer in layers["scenes"][0]["layers"]]
        self.assertEqual(order[0], "background")
        self.assertEqual(order[-1], "transitions")

    def test_layer_z_index(self):
        _, _, layers, _, _, _ = self.composed()
        self.assertEqual([layer["z_index"] for layer in layers["scenes"][0]["layers"]], list(range(1, 11)))

    def test_captions_above_visuals(self):
        _, _, layers, _, _, _ = self.composed()
        by_type = {layer["layer_type"]: layer["z_index"] for layer in layers["scenes"][0]["layers"]}
        self.assertGreater(by_type["captions"], by_type["primary_text"])

    def test_includes_watermark(self):
        _, _, layers, _, _, _ = self.composed()
        self.assertEqual(layers["watermark_layer"], "watermark")

    def test_safe_area_compliance(self):
        _, _, layers, _, _, _ = self.composed()
        self.assertTrue(all(layer["safe_area_compliant"] for scene in layers["scenes"] for layer in scene["layers"]))

    def test_layer_map_schema_shape(self):
        _, _, layers, _, _, _ = self.composed()
        self.assertIn("caption_layer", layers)

    def test_captions_align_to_scene_timing(self):
        timeline, _, layers, captions, _, _ = self.composed()
        self.assertEqual(captions["captions"][0]["start_time_seconds"], timeline["scenes"][0]["start_time_seconds"])

    def test_caption_max_words_per_line(self):
        _, _, _, captions, _, _ = self.composed()
        self.assertTrue(all(len(line.split()) <= 7 for cap in captions["captions"] for line in cap["text"].split("\n")))

    def test_caption_max_two_lines(self):
        _, _, _, captions, _, _ = self.composed()
        self.assertTrue(all(len(cap["text"].split("\n")) <= 2 for cap in captions["captions"]))

    def test_captions_avoid_unsafe_areas(self):
        _, _, _, captions, _, _ = self.composed()
        self.assertTrue(all(cap["safe_area_status"] == "compliant" for cap in captions["captions"]))

    def test_readability_score_generated(self):
        _, _, _, captions, _, _ = self.composed()
        self.assertTrue(all(cap["readability_score"] > 0 for cap in captions["captions"]))

    def test_caption_schema_shape(self):
        _, _, _, captions, _, _ = self.composed()
        self.assertIn("captions", captions)

    def test_audio_timing_aligns(self):
        _, _, _, _, audio, _ = self.composed()
        self.assertEqual(audio["sync_status"], "aligned")

    def test_sync_offset_calculated(self):
        _, _, _, _, audio, _ = self.composed()
        self.assertIn("sync_offset", audio["scene_audio_map"][0])

    def test_missing_voice_timestamps_fail(self):
        timeline = self.build()
        voice = copy.deepcopy(self.voice)
        voice["voice_timestamps"]["entries"] = []
        with self.assertRaises(ValueError):
            audio_synchronizer(timeline, voice, root=ROOT)

    def test_audio_warnings_work(self):
        _, _, _, _, audio, _ = self.composed()
        self.assertIn("warnings", audio)

    def test_audio_schema_shape(self):
        _, _, _, _, audio, _ = self.composed()
        self.assertIn("scene_audio_map", audio)

    def test_render_plan_provider_agnostic(self):
        _, _, _, _, _, render = self.composed()
        self.assertEqual(render["renderer_profile"]["default"], "provider_agnostic")

    def test_render_plan_settings(self):
        _, _, _, _, _, render = self.composed()
        self.assertEqual(render["render_settings"]["resolution"], "1080x1920")
        self.assertEqual(render["render_settings"]["fps"], 30)

    def test_render_plan_not_hardcoded_creatomate(self):
        _, _, _, _, _, render = self.composed()
        self.assertNotEqual(render["renderer_profile"]["default"], "Creatomate")

    def test_render_plan_supports_multiple_profiles(self):
        _, _, _, _, _, render = self.composed()
        self.assertGreaterEqual(len(render["renderer_profile"]["supported_renderers"]), 5)

    def test_render_plan_schema_shape(self):
        _, _, _, _, _, render = self.composed()
        self.assertIn("required_fonts", render)

    def test_valid_timeline_passes(self):
        result = run_all(ROOT)["renderer_ready_package"]
        self.assertIn(result["render_readiness_status"], {"ready", "ready_with_warnings"})

    def test_overlapping_scenes_fail(self):
        timeline, scenes, layers, captions, audio, render = self.composed()
        timeline["scenes"][1]["start_time_seconds"] = 0
        result = timeline_validator(timeline, scenes, layers, captions, audio, render, self.voice, self.visual, self.assets, root=ROOT)
        self.assertEqual(result["renderer_ready_package"]["render_readiness_status"], "failed_validation")

    def test_duration_over_60_fails(self):
        timeline, scenes, layers, captions, audio, render = self.composed()
        timeline["total_duration_seconds"] = 61
        result = timeline_validator(timeline, scenes, layers, captions, audio, render, self.voice, self.visual, self.assets, root=ROOT)
        self.assertEqual(result["renderer_ready_package"]["render_readiness_status"], "failed_validation")

    def test_missing_asset_refs_fail(self):
        timeline, scenes, layers, captions, audio, render = self.composed()
        timeline["scenes"][0]["asset_refs"].append("missing_forever")
        result = timeline_validator(timeline, scenes, layers, captions, audio, render, self.voice, self.visual, self.assets, root=ROOT)
        self.assertEqual(result["renderer_ready_package"]["render_readiness_status"], "failed_validation")

    def test_missing_voice_refs_fail(self):
        timeline, scenes, layers, captions, audio, render = self.composed()
        voice = copy.deepcopy(self.voice)
        voice["voice_timestamps"]["entries"] = []
        result = timeline_validator(timeline, scenes, layers, captions, audio, render, voice, self.visual, self.assets, root=ROOT)
        self.assertEqual(result["renderer_ready_package"]["render_readiness_status"], "failed_validation")

    def test_blocked_legal_assets_fail(self):
        timeline, scenes, layers, captions, audio, render = self.composed()
        assets = copy.deepcopy(self.assets)
        assets["render_readiness_status"] = "blocked_legal_risk"
        result = timeline_validator(timeline, scenes, layers, captions, audio, render, self.voice, self.visual, assets, root=ROOT)
        self.assertEqual(result["renderer_ready_package"]["render_readiness_status"], "failed_validation")

    def test_renderer_ready_package_schema_shape(self):
        package = run_all(ROOT)["renderer_ready_package"]
        for field in ["timeline", "scene_compositions", "layer_map", "caption_sync", "audio_sync", "render_plan", "validation_report"]:
            self.assertIn(field, package)


if __name__ == "__main__":
    unittest.main()
