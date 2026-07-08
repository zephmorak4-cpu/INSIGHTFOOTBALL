"""Asset manifest construction."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


ASSET_LIBRARY = {
    "brand_logo": ("INSIGHT FOOTBALL logo", "logo", "brand", True, "svg/png", "internal approved brand kit", "approved"),
    "wordmark": ("INSIGHT FOOTBALL wordmark", "logo", "brand", True, "svg/png", "internal approved brand kit", "approved"),
    "watermark": ("INSIGHT FOOTBALL watermark", "logo", "brand", True, "png", "internal approved brand kit", "approved"),
    "intro_frame": ("Intro frame", "template", "brand", True, "png/json", "template graphic", "approved"),
    "outro_frame": ("Outro frame", "template", "brand", True, "png/json", "template graphic", "approved"),
    "team_logos": ("Liverpool and Arsenal badges", "logo", "match", True, "svg/png", "approved team badge source", "needs_review"),
    "team_logo_home": ("Liverpool badge", "logo", "match", True, "svg/png", "approved team badge source", "needs_review"),
    "team_logo_away": ("Arsenal badge", "logo", "match", True, "svg/png", "approved team badge source", "needs_review"),
    "competition_logo": ("Premier League logo", "logo", "match", True, "svg/png", "approved competition source", "needs_review"),
    "background_graphic": ("Clean match background", "background", "brand", True, "png", "custom graphic", "approved"),
    "data_card": ("Surprising detail card", "card", "dashboard", True, "json/png", "template graphic", "approved"),
    "pitch_graphic": ("Pitch background", "pitch", "football", True, "svg/png", "custom pitch diagram", "approved"),
    "tactical_arrows": ("Tactical arrows", "icon", "football", True, "svg", "custom vector", "approved"),
    "pressing_icon": ("Pressing icon", "icon", "football", True, "svg", "custom icon", "approved"),
    "goal_icon": ("Goal icon", "icon", "football", True, "svg", "custom icon", "approved"),
    "comment_icon": ("Comment icon", "icon", "football", True, "svg", "custom icon", "approved"),
    "dashboard_panel": ("Insight dashboard panel", "card", "dashboard", True, "json/png", "template graphic", "approved"),
    "player_image": ("Player cutout", "photo", "optional", False, "png", "manual upload only", "needs_review"),
    "stadium_image": ("Stadium-style background", "illustration", "optional", False, "png", "generated illustration", "approved"),
}


def build_manifest(storyboard: dict[str, Any], config: Any) -> dict[str, Any]:
    scene_asset_map = []
    assets_seen: dict[str, set[str]] = {}
    for scene in storyboard.get("scenes", []):
        scene_assets = list(dict.fromkeys(scene.get("required_assets", [])))
        scene_asset_map.append({"scene_id": scene["scene_id"], "scene_type": scene["scene_type"], "asset_ids": scene_assets})
        for asset_id in scene_assets:
            assets_seen.setdefault(asset_id, set()).add(scene["scene_id"])
    for asset_id in ["wordmark", "watermark", "intro_frame", "outro_frame", "team_logo_away", "competition_logo", "tactical_arrows", "pressing_icon", "goal_icon", "stadium_image"]:
        assets_seen.setdefault(asset_id, set())
    assets = [_asset(asset_id, sorted(scenes), config) for asset_id, scenes in sorted(assets_seen.items())]
    missing = [asset["asset_id"] for asset in assets if asset["legal_status"] == "needs_review" or asset["source_strategy"] in {"manual upload only", "approved team badge source", "approved competition source"}]
    legal_warnings = [
        "Do not use copyrighted broadcast footage.",
        "Do not use unlicensed player photos unless manually approved.",
        "Use approved sources for club badges and competition marks.",
        "Avoid unsafe scraped images and unclear source ownership.",
    ]
    return {
        "production_id": storyboard["production_id"],
        "component_id": config.component_id,
        "component_name": config.component_name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source_storyboard_package": storyboard["production_id"],
        "match": storyboard["match"],
        "competition": storyboard["competition"],
        "required_assets": [asset for asset in assets if asset["required"]],
        "optional_assets": [asset for asset in assets if not asset["required"]],
        "reusable_assets": [asset for asset in assets if asset["category"] in {"brand", "football", "dashboard"}],
        "scene_asset_map": scene_asset_map,
        "missing_assets": missing,
        "legal_warnings": legal_warnings,
        "asset_priority": {"high": [a["asset_id"] for a in assets if a["priority"] == "high"], "medium": [a["asset_id"] for a in assets if a["priority"] == "medium"], "low": [a["asset_id"] for a in assets if a["priority"] == "low"]},
        "approval_status": "approved",
        "next_component": config.next_component,
    }


def _asset(asset_id: str, scenes: list[str], config: Any) -> dict[str, Any]:
    name, asset_type, category, required, fmt, source, legal = ASSET_LIBRARY.get(asset_id, (asset_id.replace("_", " ").title(), "graphic", "football", True, "svg/png", "custom graphic", "approved"))
    priority = "high" if required and category in {"brand", "match", "dashboard", "football"} else "medium" if required else "low"
    return {
        "asset_id": asset_id,
        "asset_name": name,
        "asset_type": asset_type,
        "category": category,
        "required": required,
        "scenes_used": scenes,
        "purpose": f"Support {', '.join(scenes) if scenes else 'the video package'}",
        "recommended_format": fmt,
        "recommended_dimensions": config.default_dimensions.get(asset_type, config.default_dimensions["default"]),
        "source_strategy": source,
        "legal_status": legal,
        "fallback_strategy": _fallback(asset_type, category),
        "priority": priority,
    }


def _fallback(asset_type: str, category: str) -> str:
    if asset_type == "photo":
        return "Replace with generated illustration or pitch graphic."
    if category == "match":
        return "Use text initials in approved template until badge is confirmed."
    return "Use custom vector/template graphic from internal library."
