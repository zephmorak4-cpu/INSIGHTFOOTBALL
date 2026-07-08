from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

from .io import StructuredLogger, load_json, now, write_json
from .providers import get_provider


SUPPORTED_FORMATS = {".svg", ".png", ".jpg", ".jpeg", ".json"}
OUTPUT = Path("editorial-brain/output")
LOGS = Path("editorial-brain/logs")
LIBRARY_ROOT = Path("editorial-brain/assets")
PLACEHOLDER_ROOT = LIBRARY_ROOT / "generated" / "sprint8"


def run_all(root: Path = Path(".")) -> dict[str, Any]:
    asset_package = load_json(root / OUTPUT / "final-asset-package.json")
    visual_package = load_json(root / OUTPUT / "visual-production-package.json")
    search_plan = load_json(root / OUTPUT / "asset_search_plan.json")
    graphics = load_json(root / OUTPUT / "graphic_requirements.json")
    library = asset_library_manager(asset_package, root=root)
    badges = team_badge_manager(asset_package, library, root=root)
    competition = competition_logo_manager(asset_package, library, root=root)
    backgrounds = background_asset_manager(asset_package, visual_package, library, root=root)
    icons = icon_manager(asset_package, visual_package, library, root=root)
    illustration = illustration_provider_adapter(search_plan, graphics, backgrounds, icons, root=root)
    cache = asset_cache_manager([library, badges, competition, backgrounds, icons, illustration], root=root)
    bundle = asset_bundle_validator(asset_package, visual_package, library, badges, competition, backgrounds, icons, illustration, cache, root=root)
    return {
        "asset_library_status": library,
        "team_badge_assets": badges,
        "competition_logo_assets": competition,
        "background_assets": backgrounds,
        "icon_assets": icons,
        "illustration_outputs": illustration,
        "asset_cache_index": cache,
        "asset_bundle": bundle,
    }


def asset_library_manager(asset_package: dict[str, Any], *, root: Path = Path(".")) -> dict[str, Any]:
    production_id = asset_package["production_id"]
    logger = StructuredLogger(root / LOGS, f"asset-library-manager-{production_id}")
    required = _required_assets(asset_package)
    files = _scan_files(root / LIBRARY_ROOT)
    found, missing, reusable, legal_review, blocked = [], [], [], [], []
    for asset in required:
        match = _find_file(asset, files)
        if match:
            found_asset = _asset_ref(asset, match)
            found.append(found_asset)
            if found_asset["reusable"]:
                reusable.append(found_asset)
        else:
            missing.append(_requirement_ref(asset))
        if asset.get("legal_status") == "needs_review":
            legal_review.append(_requirement_ref(asset))
        if asset.get("legal_status") == "blocked":
            blocked.append(_requirement_ref(asset))
    score = round((len(found) / max(len(required), 1)) * 100)
    status = {
        "production_id": production_id,
        "component_id": "IF-MAE01",
        "component_name": "Asset Library Manager",
        "timestamp": now(),
        "source_asset_package": production_id,
        "found_assets": found,
        "missing_assets": missing,
        "reusable_assets": reusable,
        "legal_review_assets": legal_review,
        "blocked_assets": blocked,
        "library_health_score": score,
        "warnings": [f"{len(missing)} required assets missing from local library."] if missing else [],
        "approval_status": "blocked" if blocked else "approved",
        "next_component": "Team Badge Manager",
    }
    write_json(root / OUTPUT / "asset_library_status.json", status)
    logger.log({"event": "asset_library_status_written", "missing_assets": len(missing), "health": score})
    return status


def team_badge_manager(asset_package: dict[str, Any], library: dict[str, Any], *, root: Path = Path(".")) -> dict[str, Any]:
    match = asset_package["match"]
    home = _resolve_or_fallback("team_logo_home", f"{match['home_team']} badge fallback", library, root)
    away = _resolve_or_fallback("team_logo_away", f"{match['away_team']} badge fallback", library, root)
    missing = [badge for badge in [home, away] if badge.get("fallback")]
    legal = [f"{item['asset_name']} requires rights confirmation." for item in _legal_review(library) if item["asset_id"] in {"team_logo_home", "team_logo_away", "team_logos"}]
    output = {
        "production_id": asset_package["production_id"],
        "component_id": "IF-MAE02",
        "component_name": "Team Badge Manager",
        "timestamp": now(),
        "home_team": match["home_team"],
        "away_team": match["away_team"],
        "home_badge": home,
        "away_badge": away,
        "missing_badges": [item["asset_id"] for item in missing],
        "fallback_badges": missing,
        "legal_warnings": legal,
        "approval_status": "approved",
        "next_component": "Competition Logo Manager",
    }
    write_json(root / OUTPUT / "team_badge_assets.json", output)
    StructuredLogger(root / LOGS, f"team-badge-manager-{asset_package['production_id']}").log({"event": "team_badge_assets_written", "fallbacks": len(missing)})
    return output


def competition_logo_manager(asset_package: dict[str, Any], library: dict[str, Any], *, root: Path = Path(".")) -> dict[str, Any]:
    resolved = _resolve_or_fallback("competition_logo", f"{asset_package['competition']} text logo fallback", library, root)
    output = {
        "production_id": asset_package["production_id"],
        "component_id": "IF-MAE03",
        "component_name": "Competition Logo Manager",
        "timestamp": now(),
        "competition": asset_package["competition"],
        "competition_logo": None if resolved.get("fallback") else resolved,
        "fallback_logo": resolved if resolved.get("fallback") else None,
        "missing_logo": bool(resolved.get("fallback")),
        "legal_warnings": [f"{asset_package['competition']} logo requires rights confirmation."] if any(item["asset_id"] == "competition_logo" for item in _legal_review(library)) else [],
        "approval_status": "approved",
        "next_component": "Background Asset Manager",
    }
    write_json(root / OUTPUT / "competition_logo_assets.json", output)
    StructuredLogger(root / LOGS, f"competition-logo-manager-{asset_package['production_id']}").log({"event": "competition_logo_assets_written", "fallback": output["missing_logo"]})
    return output


def background_asset_manager(asset_package: dict[str, Any], visual_package: dict[str, Any], library: dict[str, Any], *, root: Path = Path(".")) -> dict[str, Any]:
    requirements = [asset for asset in _required_assets(asset_package) if asset.get("asset_type") in {"background", "pitch", "image"} or "background" in asset.get("asset_id", "")]
    assets, tasks, fallbacks, warnings = [], [], [], []
    for asset in requirements:
        if _blocked_background(asset):
            warnings.append(f"{asset['asset_id']} blocked because it resembles broadcast footage or random stadium photography.")
            continue
        resolved = _resolve_or_fallback(asset["asset_id"], f"{asset['asset_name']} fallback background", library, root)
        if resolved.get("fallback"):
            task = _generation_task(asset, "background", "Create a clean football intelligence background; avoid broadcast footage.")
            tasks.append(task)
            fallbacks.append(resolved)
        assets.append(resolved)
    output = {
        "production_id": asset_package["production_id"],
        "component_id": "IF-MAE04",
        "component_name": "Background Asset Manager",
        "timestamp": now(),
        "background_assets": assets,
        "generated_background_tasks": tasks,
        "fallback_backgrounds": fallbacks,
        "legal_warnings": warnings,
        "approval_status": "approved",
        "next_component": "Icon Manager",
    }
    write_json(root / OUTPUT / "background_assets.json", output)
    StructuredLogger(root / LOGS, f"background-asset-manager-{asset_package['production_id']}").log({"event": "background_assets_written", "fallbacks": len(fallbacks)})
    return output


def icon_manager(asset_package: dict[str, Any], visual_package: dict[str, Any], library: dict[str, Any], *, root: Path = Path(".")) -> dict[str, Any]:
    required = [asset for asset in _required_assets(asset_package) if asset.get("asset_type") == "icon" or asset.get("asset_id", "").endswith("_icon")]
    required_ids = {asset["asset_id"] for asset in required}
    required_ids.update({"press_icon", "warning_icon", "uncertainty_icon", "tactical_arrow", "x_factor_icon", "dashboard_icon"})
    resolved, missing, fallbacks = [], [], []
    for asset_id in sorted(required_ids):
        asset = _asset_by_id(asset_package, asset_id) or {"asset_id": asset_id, "asset_name": asset_id.replace("_", " ").title(), "asset_type": "icon", "category": "football", "scenes_used": [], "legal_status": "approved"}
        item = _resolve_or_fallback(asset_id, f"{asset['asset_name']} fallback icon", library, root)
        resolved.append(item)
        if item.get("fallback"):
            missing.append(asset_id)
            fallbacks.append(item)
    output = {
        "production_id": asset_package["production_id"],
        "component_id": "IF-MAE05",
        "component_name": "Icon Manager",
        "timestamp": now(),
        "resolved_icons": resolved,
        "missing_icons": missing,
        "fallback_icons": fallbacks,
        "icon_style_notes": "Use simple approved SVG/PNG icons, white-on-dark dashboard style, no third-party packs without review.",
        "approval_status": "approved",
        "next_component": "Illustration Provider Adapter",
    }
    write_json(root / OUTPUT / "icon_assets.json", output)
    StructuredLogger(root / LOGS, f"icon-manager-{asset_package['production_id']}").log({"event": "icon_assets_written", "fallbacks": len(fallbacks)})
    return output


def illustration_provider_adapter(search_plan: dict[str, Any], graphics: dict[str, Any], backgrounds: dict[str, Any], icons: dict[str, Any], *, root: Path = Path("."), provider_name: str = "placeholder") -> dict[str, Any]:
    provider = get_provider(provider_name)
    production_id = search_plan["production_id"]
    tasks = []
    for task in search_plan.get("generation_tasks", []) + backgrounds.get("generated_background_tasks", []):
        asset_id = task["asset_id"]
        tasks.append({
            "task_id": f"generate-{asset_id}",
            "asset_id": asset_id,
            "asset_type": task.get("asset_type", task.get("task_type", "illustration")),
            "prompt": task.get("description", "Create an INSIGHT FOOTBALL placeholder illustration."),
            "negative_prompt": "No player likeness, no broadcast screenshot, no copyrighted match footage, no betting aesthetic.",
            "style_notes": "Clean football intelligence dashboard, premium dark sports interface, safe abstract shapes.",
            "dimensions": "1080x1920",
            "scenes_used": task.get("scenes_used", []),
            "provider": provider.provider_name,
            "legal_notes": task.get("legal_notes", "Approved placeholder workflow."),
            "priority": task.get("priority", "medium"),
        })
    blocked = [task for task in tasks if _unsafe_generation(task)]
    safe_tasks = [task for task in tasks if task not in blocked]
    generated = [provider.create_placeholder(task, root / PLACEHOLDER_ROOT).__dict__ for task in safe_tasks]
    output = {
        "illustration_tasks": {
            "production_id": production_id,
            "component_id": "IF-MAE06",
            "component_name": "Illustration Provider Adapter",
            "timestamp": now(),
            "generation_tasks": safe_tasks,
            "provider_recommendations": ["placeholder", "local_svg_generator", "openai_image_generation", "google_image_generation", "stability", "midjourney_manual_workflow"],
            "blocked_generation_tasks": blocked,
            "manual_review_tasks": [task for task in safe_tasks if "player" in task["asset_id"]],
            "approval_status": "approved" if not blocked else "blocked",
        },
        "generated_placeholder_assets": {
            "production_id": production_id,
            "generated_assets": generated,
            "placeholder_assets": [item["file_path"] for item in generated],
            "file_paths": [item["file_path"] for item in generated],
            "metadata": {"provider": provider.provider_name, "style_profile": "INSIGHT FOOTBALL clean dashboard placeholders"},
            "approval_status": "approved",
        },
    }
    write_json(root / OUTPUT / "illustration_tasks.json", output["illustration_tasks"])
    write_json(root / OUTPUT / "generated_placeholder_assets.json", output["generated_placeholder_assets"])
    StructuredLogger(root / LOGS, f"illustration-provider-adapter-{production_id}").log({"event": "illustration_outputs_written", "tasks": len(safe_tasks)})
    return output


def asset_cache_manager(outputs: list[dict[str, Any]], *, root: Path = Path(".")) -> dict[str, Any]:
    production_id = _first_production_id(outputs)
    refs = _collect_asset_refs(outputs)
    entries, seen, duplicates, reused, new = [], {}, [], [], []
    for ref in refs:
        path = ref.get("local_path") or ref.get("file_path")
        checksum = _checksum_path(Path(path)) if path else ref.get("checksum") or _checksum_text(ref.get("asset_id", ref.get("asset_name", "asset")))
        entry = {"asset_id": ref.get("asset_id", Path(path).stem if path else "unknown"), "local_path": path, "checksum": checksum, "legal_status": ref.get("legal_status", "approved_placeholder"), "source": ref.get("source", "sprint8"), "reusable": bool(ref.get("reusable", True))}
        if checksum in seen:
            duplicates.append({"checksum": checksum, "asset_ids": [seen[checksum], entry["asset_id"]]})
            reused.append(entry)
        else:
            seen[checksum] = entry["asset_id"]
            new.append(entry)
        entries.append(entry)
    output = {
        "production_id": production_id,
        "component_id": "IF-MAE07",
        "component_name": "Asset Cache Manager",
        "timestamp": now(),
        "cache_entries": entries,
        "duplicate_assets": duplicates,
        "reused_assets": reused,
        "new_assets": new,
        "cache_health_score": 100 if entries else 70,
        "warnings": [] if entries else ["No cacheable assets found."],
        "approval_status": "approved",
        "next_component": "Asset Bundle Validator",
    }
    write_json(root / OUTPUT / "asset_cache_index.json", output)
    StructuredLogger(root / LOGS, f"asset-cache-manager-{production_id}").log({"event": "asset_cache_index_written", "entries": len(entries)})
    return output


def asset_bundle_validator(asset_package: dict[str, Any], visual_package: dict[str, Any], library: dict[str, Any], badges: dict[str, Any], competition: dict[str, Any], backgrounds: dict[str, Any], icons: dict[str, Any], illustration: dict[str, Any], cache: dict[str, Any], *, root: Path = Path(".")) -> dict[str, Any]:
    required = _required_assets(asset_package)
    fallback_assets = _fallbacks(badges, competition, backgrounds, icons)
    missing_without_fallback = [asset for asset in required if _is_missing(asset["asset_id"], library) and not asset.get("fallback_strategy")]
    legal_warnings = badges.get("legal_warnings", []) + competition.get("legal_warnings", []) + backgrounds.get("legal_warnings", [])
    blocked = library.get("blocked_assets", []) + illustration["illustration_tasks"].get("blocked_generation_tasks", [])
    scene_map = _scene_asset_map(visual_package, fallback_assets, library)
    placeholder_paths = illustration["generated_placeholder_assets"].get("file_paths", [])
    path_issues = [path for path in placeholder_paths if not Path(path).exists()]
    status = _readiness(blocked, missing_without_fallback, legal_warnings, fallback_assets, path_issues)
    report = {
        "production_id": asset_package["production_id"],
        "component_id": "IF-MAE08",
        "component_name": "Asset Bundle Validator",
        "timestamp": now(),
        "checks": {
            "required_assets_have_fallbacks": not missing_without_fallback,
            "blocked_assets_excluded": not blocked,
            "legal_warnings_surfaced": True,
            "cache_checksums_exist": all(entry.get("checksum") for entry in cache.get("cache_entries", [])),
            "placeholder_paths_exist": not path_issues,
            "scene_asset_mapping_complete": bool(scene_map),
        },
        "render_readiness_status": status,
        "warnings": legal_warnings + ([f"Missing placeholder paths: {path_issues}"] if path_issues else []),
        "approval_status": "approved" if status in {"ready", "ready_with_fallbacks", "needs_manual_assets"} else "blocked",
    }
    bundle = {
        "production_id": asset_package["production_id"],
        "match": asset_package["match"],
        "competition": asset_package["competition"],
        "source_asset_package": asset_package["production_id"],
        "source_visual_package": visual_package["production_id"],
        "brand_assets": [asset for asset in required if asset.get("category") == "brand"],
        "team_badges": {"home_badge": badges["home_badge"], "away_badge": badges["away_badge"]},
        "competition_assets": competition,
        "background_assets": backgrounds.get("background_assets", []),
        "icon_assets": icons.get("resolved_icons", []),
        "illustration_assets": illustration["illustration_tasks"].get("generation_tasks", []),
        "placeholder_assets": illustration["generated_placeholder_assets"].get("placeholder_assets", []),
        "graphic_assets": _graphics_from_package(asset_package),
        "scene_asset_map": scene_map,
        "asset_cache_index": cache,
        "legal_warnings": legal_warnings,
        "missing_assets": library.get("missing_assets", []),
        "fallback_assets": fallback_assets,
        "manual_review_tasks": illustration["illustration_tasks"].get("manual_review_tasks", []) + library.get("legal_review_assets", []),
        "render_readiness_status": status,
        "approval_status": report["approval_status"],
        "next_component": "Timeline Builder",
    }
    write_json(root / OUTPUT / "asset_bundle_validation_report.json", report)
    write_json(root / OUTPUT / "media-asset-bundle.json", bundle)
    StructuredLogger(root / LOGS, f"asset-bundle-validator-{asset_package['production_id']}").log({"event": "media_asset_bundle_written", "status": status})
    return {"asset_bundle_validation_report": report, "media_asset_bundle": bundle}


def _required_assets(asset_package: dict[str, Any]) -> list[dict[str, Any]]:
    return list(asset_package.get("asset_manifest", {}).get("required_assets", []))


def _asset_by_id(asset_package: dict[str, Any], asset_id: str) -> dict[str, Any] | None:
    return next((asset for asset in _required_assets(asset_package) if asset.get("asset_id") == asset_id), None)


def _scan_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return [
        path
        for path in root.rglob("*")
        if path.is_file()
        and path.suffix.lower() in SUPPORTED_FORMATS
        and "sprint8" not in {part.lower() for part in path.parts}
    ]


def _find_file(asset: dict[str, Any], files: list[Path]) -> Path | None:
    terms = {asset.get("asset_id", "").lower(), _slug(asset.get("asset_name", "")), _slug(asset.get("category", ""))}
    for file in files:
        stem = file.stem.lower()
        if stem in terms or any(term and term in stem for term in terms):
            return file
    return None


def _asset_ref(asset: dict[str, Any], path: Path) -> dict[str, Any]:
    return {
        "asset_id": asset["asset_id"],
        "asset_name": asset["asset_name"],
        "asset_type": asset["asset_type"],
        "category": asset.get("category", ""),
        "local_path": str(path),
        "file_format": path.suffix.lower().lstrip("."),
        "dimensions": asset.get("recommended_dimensions", "unknown"),
        "legal_status": asset.get("legal_status", "needs_review"),
        "source": asset.get("source_strategy", "local_library"),
        "scenes_used": asset.get("scenes_used", []),
        "reusable": asset.get("category") in {"brand", "football", "dashboard", "match"},
        "checksum": _checksum_path(path),
    }


def _requirement_ref(asset: dict[str, Any]) -> dict[str, Any]:
    return {key: asset.get(key) for key in ["asset_id", "asset_name", "asset_type", "category", "required", "scenes_used", "legal_status", "fallback_strategy", "priority"]}


def _resolve_or_fallback(asset_id: str, label: str, library: dict[str, Any], root: Path) -> dict[str, Any]:
    found = next((asset for asset in library.get("found_assets", []) if asset.get("asset_id") == asset_id), None)
    if found:
        return found
    path = _write_placeholder(root, asset_id, label)
    return {"asset_id": asset_id, "asset_name": label, "asset_type": "fallback", "category": "fallback", "local_path": str(path), "file_format": "svg", "dimensions": "512x512", "legal_status": "approved_placeholder", "source": "deterministic_placeholder", "scenes_used": [], "reusable": True, "checksum": _checksum_path(path), "fallback": True}


def _write_placeholder(root: Path, asset_id: str, label: str) -> Path:
    path = root / PLACEHOLDER_ROOT / f"{asset_id}.svg"
    path.parent.mkdir(parents=True, exist_ok=True)
    text = label.replace("&", "&amp;").replace("<", "").replace(">", "")
    initials = "".join(part[0].upper() for part in re.findall(r"[A-Za-z]+", label)[:3]) or "IF"
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512"><rect width="512" height="512" rx="80" fill="#111827"/><circle cx="256" cy="208" r="120" fill="#16a34a" opacity="0.24"/><text x="256" y="230" text-anchor="middle" font-family="Arial" font-size="86" font-weight="700" fill="#f8fafc">{initials}</text><text x="256" y="340" text-anchor="middle" font-family="Arial" font-size="28" fill="#cbd5e1">{text[:28]}</text></svg>'
    path.write_text(svg, encoding="utf-8")
    return path


def _checksum_path(path: Path) -> str:
    if not path.exists():
        return _checksum_text(str(path))
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def _checksum_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def _legal_review(library: dict[str, Any]) -> list[dict[str, Any]]:
    return list(library.get("legal_review_assets", []))


def _blocked_background(asset: dict[str, Any]) -> bool:
    value = " ".join(str(asset.get(key, "")) for key in ["asset_id", "asset_name", "source_strategy"]).lower()
    return any(term in value for term in ["broadcast screenshot", "match footage", "random web stadium"])


def _generation_task(asset: dict[str, Any], asset_type: str, prompt: str) -> dict[str, Any]:
    return {"task_id": f"task-{asset['asset_id']}", "asset_id": asset["asset_id"], "asset_type": asset_type, "description": prompt, "scenes_used": asset.get("scenes_used", []), "priority": asset.get("priority", "medium"), "legal_notes": "Use internally generated or placeholder background only."}


def _unsafe_generation(task: dict[str, Any]) -> bool:
    text = " ".join(str(task.get(key, "")) for key in ["prompt", "negative_prompt", "asset_id"]).lower()
    return "real player likeness" in text and "approved" not in text


def _collect_asset_refs(outputs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    def walk(value: Any) -> None:
        if isinstance(value, dict):
            if value.get("local_path") or value.get("file_path"):
                refs.append(value)
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)
    for output in outputs:
        walk(output)
    return refs


def _first_production_id(outputs: list[dict[str, Any]]) -> str:
    for output in outputs:
        if isinstance(output, dict) and output.get("production_id"):
            return output["production_id"]
        if isinstance(output, dict):
            for value in output.values():
                if isinstance(value, dict) and value.get("production_id"):
                    return value["production_id"]
    return "unknown-production"


def _fallbacks(*outputs: dict[str, Any]) -> list[dict[str, Any]]:
    refs = []
    for output in outputs:
        refs.extend(_collect_asset_refs([output]))
    return [ref for ref in refs if ref.get("fallback")]


def _is_missing(asset_id: str, library: dict[str, Any]) -> bool:
    return any(asset.get("asset_id") == asset_id for asset in library.get("missing_assets", []))


def _scene_asset_map(visual_package: dict[str, Any], fallbacks: list[dict[str, Any]], library: dict[str, Any]) -> list[dict[str, Any]]:
    fallback_ids = {item["asset_id"] for item in fallbacks}
    found_ids = {item["asset_id"] for item in library.get("found_assets", [])}
    scenes = visual_package.get("visual_plan", {}).get("scenes", [])
    output = []
    for scene in scenes:
        ids = set(scene.get("foreground_assets", []) + scene.get("team_badges", []) + scene.get("graphic_assets", []))
        output.append({"scene_id": scene["scene_id"], "required_asset_ids": sorted(ids), "resolved_asset_ids": sorted(ids & (fallback_ids | found_ids)), "fallback_asset_ids": sorted(ids & fallback_ids)})
    return output


def _readiness(blocked: list[Any], missing_without_fallback: list[Any], legal_warnings: list[str], fallbacks: list[dict[str, Any]], path_issues: list[str]) -> str:
    if blocked or path_issues:
        return "blocked_legal_risk" if blocked else "failed_validation"
    if missing_without_fallback:
        return "needs_manual_assets"
    if legal_warnings:
        return "needs_manual_assets"
    if fallbacks:
        return "ready_with_fallbacks"
    return "ready"


def _graphics_from_package(asset_package: dict[str, Any]) -> list[dict[str, Any]]:
    return [asset for asset in _required_assets(asset_package) if asset.get("asset_type") in {"card", "template", "pitch"}]
