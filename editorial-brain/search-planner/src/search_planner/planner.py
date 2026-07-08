"""Search planning."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def build_search_plan(manifest: dict[str, Any], config: Any) -> dict[str, Any]:
    tasks = []
    manual = []
    generation = []
    blocked = []
    fallback = []
    legal = []
    for asset in manifest.get("required_assets", []) + manifest.get("optional_assets", []):
        should_plan_generated = "generated illustration" in asset.get("source_strategy", "")
        if asset["asset_id"] not in manifest.get("missing_assets", []) and asset["legal_status"] == "approved" and not should_plan_generated:
            continue
        task = _task(asset)
        if task["task_type"] == "blocked":
            blocked.append(task)
        elif task["task_type"] == "manual_upload":
            manual.append(task)
        elif task["task_type"] in {"generated_illustration", "template_graphic"}:
            generation.append(task)
        else:
            tasks.append(task)
        if asset["legal_status"] == "needs_review":
            legal.append({**task, "task_id": f"legal-{asset['asset_id']}", "task_type": "legal_review", "description": f"Confirm rights for {asset['asset_name']}", "required_before_render": True})
        fallback.append({**task, "task_id": f"fallback-{asset['asset_id']}", "task_type": "fallback", "description": asset["fallback_strategy"], "required_before_render": False})
    return {
        "production_id": manifest["production_id"],
        "component_id": config.component_id,
        "component_name": config.component_name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source_asset_manifest": manifest["production_id"],
        "search_tasks": tasks,
        "manual_tasks": manual,
        "generation_tasks": generation,
        "blocked_assets": blocked,
        "fallback_tasks": fallback,
        "legal_review_tasks": legal,
        "approval_status": "approved",
        "next_component": config.next_component,
    }


def _task(asset: dict[str, Any]) -> dict[str, Any]:
    strategy = asset["source_strategy"]
    if "broadcast" in strategy:
        task_type = "blocked"
        approved = "blocked"
    elif "manual upload" in strategy:
        task_type = "manual_upload"
        approved = "manual_upload"
    elif "generated illustration" in strategy:
        task_type = "generated_illustration"
        approved = "generated_illustration"
    elif "template graphic" in strategy or "custom" in strategy:
        task_type = "template_graphic"
        approved = "internal_template"
    else:
        task_type = "internal_library"
        approved = "approved_internal_or_rights_checked_source"
    return {
        "task_id": f"task-{asset['asset_id']}",
        "asset_id": asset["asset_id"],
        "task_type": task_type,
        "description": f"Confirm or prepare {asset['asset_name']}",
        "suggested_query": f"{asset['asset_name']} approved asset",
        "approved_source_type": approved,
        "legal_notes": f"Legal status: {asset['legal_status']}. {asset['fallback_strategy']}",
        "priority": asset["priority"],
        "fallback_option": asset["fallback_strategy"],
        "required_before_render": asset["required"],
    }
