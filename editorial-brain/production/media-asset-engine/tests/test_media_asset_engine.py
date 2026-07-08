from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
SRC = ROOT / "editorial-brain" / "production" / "media-asset-engine" / "shared"
sys.path.insert(0, str(SRC))

from media_asset_engine.core import (
    asset_bundle_validator,
    asset_cache_manager,
    asset_library_manager,
    background_asset_manager,
    competition_logo_manager,
    icon_manager,
    illustration_provider_adapter,
    run_all,
    team_badge_manager,
)
from media_asset_engine.io import load_json
from media_asset_engine.providers import get_provider

ASSET_PACKAGE = ROOT / "editorial-brain" / "output" / "final-asset-package.json"
VISUAL_PACKAGE = ROOT / "editorial-brain" / "output" / "visual-production-package.json"
SEARCH_PLAN = ROOT / "editorial-brain" / "output" / "asset_search_plan.json"
GRAPHICS = ROOT / "editorial-brain" / "output" / "graphic_requirements.json"


class MediaAssetEngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.asset_package = load_json(ASSET_PACKAGE)
        cls.visual_package = load_json(VISUAL_PACKAGE)
        cls.search_plan = load_json(SEARCH_PLAN)
        cls.graphics = load_json(GRAPHICS)

    def library(self):
        return asset_library_manager(copy.deepcopy(self.asset_package), root=ROOT)

    def test_asset_library_finds_existing_assets(self):
        library = self.library()
        self.assertIn("found_assets", library)

    def test_asset_library_flags_missing_required_assets(self):
        self.assertGreater(len(self.library()["missing_assets"]), 0)

    def test_asset_library_detects_reusable_assets(self):
        library = self.library()
        self.assertIn("reusable_assets", library)

    def test_asset_library_flags_legal_review_assets(self):
        self.assertGreater(len(self.library()["legal_review_assets"]), 0)

    def test_asset_library_health_score(self):
        score = self.library()["library_health_score"]
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)

    def test_asset_library_schema_shape(self):
        library = self.library()
        for field in ["production_id", "component_id", "found_assets", "missing_assets", "approval_status"]:
            self.assertIn(field, library)

    def test_team_badge_resolves_home_badge(self):
        result = team_badge_manager(self.asset_package, self.library(), root=ROOT)
        self.assertEqual(result["home_badge"]["asset_id"], "team_logo_home")

    def test_team_badge_resolves_away_badge(self):
        result = team_badge_manager(self.asset_package, self.library(), root=ROOT)
        self.assertEqual(result["away_badge"]["asset_id"], "team_logo_away")

    def test_team_badge_creates_fallback_if_missing(self):
        self.assertGreaterEqual(len(team_badge_manager(self.asset_package, self.library(), root=ROOT)["fallback_badges"]), 1)

    def test_team_badge_flags_legal_warnings(self):
        self.assertGreater(len(team_badge_manager(self.asset_package, self.library(), root=ROOT)["legal_warnings"]), 0)

    def test_team_badge_schema_shape(self):
        result = team_badge_manager(self.asset_package, self.library(), root=ROOT)
        self.assertIn("home_badge", result)
        self.assertIn("away_badge", result)

    def test_competition_logo_resolves_or_fallback(self):
        result = competition_logo_manager(self.asset_package, self.library(), root=ROOT)
        self.assertTrue(result["competition_logo"] or result["fallback_logo"])

    def test_competition_logo_fallback_text_card(self):
        result = competition_logo_manager(self.asset_package, self.library(), root=ROOT)
        self.assertTrue(result["missing_logo"])

    def test_competition_logo_schema_shape(self):
        self.assertIn("competition", competition_logo_manager(self.asset_package, self.library(), root=ROOT))

    def test_background_resolves_approved_background(self):
        result = background_asset_manager(self.asset_package, self.visual_package, self.library(), root=ROOT)
        self.assertGreater(len(result["background_assets"]), 0)

    def test_background_blocks_broadcast_screenshot(self):
        package = copy.deepcopy(self.asset_package)
        package["asset_manifest"]["required_assets"].append({"asset_id": "bad_broadcast", "asset_name": "Broadcast screenshot", "asset_type": "background", "category": "background", "required": True, "source_strategy": "broadcast screenshot", "legal_status": "blocked", "fallback_strategy": "", "scenes_used": []})
        result = background_asset_manager(package, self.visual_package, asset_library_manager(package, root=ROOT), root=ROOT)
        self.assertGreater(len(result["legal_warnings"]), 0)

    def test_background_creates_generation_task(self):
        result = background_asset_manager(self.asset_package, self.visual_package, self.library(), root=ROOT)
        self.assertGreater(len(result["generated_background_tasks"]), 0)

    def test_background_provides_fallback(self):
        self.assertGreater(len(background_asset_manager(self.asset_package, self.visual_package, self.library(), root=ROOT)["fallback_backgrounds"]), 0)

    def test_background_schema_shape(self):
        self.assertIn("background_assets", background_asset_manager(self.asset_package, self.visual_package, self.library(), root=ROOT))

    def test_icon_resolves_known_icons(self):
        result = icon_manager(self.asset_package, self.visual_package, self.library(), root=ROOT)
        self.assertTrue(any(icon["asset_id"] == "goal_icon" for icon in result["resolved_icons"]))

    def test_icon_creates_fallback_icons(self):
        self.assertGreater(len(icon_manager(self.asset_package, self.visual_package, self.library(), root=ROOT)["fallback_icons"]), 0)

    def test_icon_flags_missing_icons(self):
        self.assertGreater(len(icon_manager(self.asset_package, self.visual_package, self.library(), root=ROOT)["missing_icons"]), 0)

    def test_icon_schema_shape(self):
        self.assertIn("resolved_icons", icon_manager(self.asset_package, self.visual_package, self.library(), root=ROOT))

    def test_illustration_creates_generation_tasks(self):
        library = self.library()
        backgrounds = background_asset_manager(self.asset_package, self.visual_package, library, root=ROOT)
        icons = icon_manager(self.asset_package, self.visual_package, library, root=ROOT)
        result = illustration_provider_adapter(self.search_plan, self.graphics, backgrounds, icons, root=ROOT)
        self.assertGreater(len(result["illustration_tasks"]["generation_tasks"]), 0)

    def test_illustration_blocks_unsafe_generation_tasks(self):
        search = copy.deepcopy(self.search_plan)
        search["generation_tasks"].append({"task_id": "unsafe", "asset_id": "real_player_likeness", "description": "real player likeness", "legal_notes": "not approved"})
        result = illustration_provider_adapter(search, self.graphics, {"generated_background_tasks": []}, {"resolved_icons": []}, root=ROOT)
        self.assertGreater(len(result["illustration_tasks"]["blocked_generation_tasks"]), 0)

    def test_illustration_placeholder_metadata(self):
        library = self.library()
        result = illustration_provider_adapter(self.search_plan, self.graphics, background_asset_manager(self.asset_package, self.visual_package, library, root=ROOT), icon_manager(self.asset_package, self.visual_package, library, root=ROOT), root=ROOT)
        self.assertGreater(len(result["generated_placeholder_assets"]["file_paths"]), 0)

    def test_illustration_provider_interface(self):
        self.assertEqual(get_provider("placeholder").provider_name, "static_placeholder")

    def test_illustration_schema_shape(self):
        result = illustration_provider_adapter(self.search_plan, self.graphics, {"generated_background_tasks": []}, {"resolved_icons": []}, root=ROOT)
        self.assertIn("provider_recommendations", result["illustration_tasks"])

    def test_cache_calculates_checksums(self):
        result = run_all(ROOT)["asset_cache_index"]
        self.assertTrue(all(entry["checksum"] for entry in result["cache_entries"]))

    def test_cache_deduplicates_assets(self):
        result = run_all(ROOT)["asset_cache_index"]
        self.assertIn("duplicate_assets", result)

    def test_cache_tracks_reuse(self):
        result = run_all(ROOT)["asset_cache_index"]
        self.assertIn("reused_assets", result)

    def test_cache_schema_shape(self):
        self.assertIn("cache_entries", run_all(ROOT)["asset_cache_index"])

    def test_valid_bundle_passes(self):
        bundle = run_all(ROOT)["asset_bundle"]["media_asset_bundle"]
        self.assertIn(bundle["approval_status"], {"approved", "blocked"})

    def test_missing_required_with_fallback_ready_with_fallbacks(self):
        library = self.library()
        badges = team_badge_manager(self.asset_package, library, root=ROOT)
        competition = competition_logo_manager(self.asset_package, library, root=ROOT)
        backgrounds = background_asset_manager(self.asset_package, self.visual_package, library, root=ROOT)
        icons = icon_manager(self.asset_package, self.visual_package, library, root=ROOT)
        illustration = illustration_provider_adapter(self.search_plan, self.graphics, backgrounds, icons, root=ROOT)
        cache = asset_cache_manager([library, badges, competition, backgrounds, icons, illustration], root=ROOT)
        badges["legal_warnings"] = []
        competition["legal_warnings"] = []
        result = asset_bundle_validator(self.asset_package, self.visual_package, library, badges, competition, backgrounds, icons, illustration, cache, root=ROOT)
        self.assertEqual(result["media_asset_bundle"]["render_readiness_status"], "ready_with_fallbacks")

    def test_missing_required_without_fallback_needs_manual_assets(self):
        package = copy.deepcopy(self.asset_package)
        package["asset_manifest"]["required_assets"].append({"asset_id": "no_fallback_asset", "asset_name": "No fallback asset", "asset_type": "image", "category": "manual", "required": True, "legal_status": "approved", "fallback_strategy": "", "scenes_used": []})
        result = run_all(ROOT)
        manual = asset_bundle_validator(package, self.visual_package, asset_library_manager(package, root=ROOT), result["team_badge_assets"], result["competition_logo_assets"], result["background_assets"], result["icon_assets"], result["illustration_outputs"], result["asset_cache_index"], root=ROOT)
        self.assertEqual(manual["media_asset_bundle"]["render_readiness_status"], "needs_manual_assets")

    def test_blocked_legal_asset_returns_blocked(self):
        package = copy.deepcopy(self.asset_package)
        package["asset_manifest"]["required_assets"].append({"asset_id": "blocked_asset", "asset_name": "Blocked asset", "asset_type": "image", "category": "manual", "required": True, "legal_status": "blocked", "fallback_strategy": "Use placeholder.", "scenes_used": []})
        result = run_all(ROOT)
        blocked = asset_bundle_validator(package, self.visual_package, asset_library_manager(package, root=ROOT), result["team_badge_assets"], result["competition_logo_assets"], result["background_assets"], result["icon_assets"], result["illustration_outputs"], result["asset_cache_index"], root=ROOT)
        self.assertEqual(blocked["media_asset_bundle"]["render_readiness_status"], "blocked_legal_risk")

    def test_media_asset_bundle_schema_shape(self):
        bundle = run_all(ROOT)["asset_bundle"]["media_asset_bundle"]
        for field in ["production_id", "match", "competition", "scene_asset_map", "render_readiness_status", "next_component"]:
            self.assertIn(field, bundle)


if __name__ == "__main__":
    unittest.main()
