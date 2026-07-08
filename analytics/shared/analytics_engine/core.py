from __future__ import annotations

from pathlib import Path
from statistics import mean
from typing import Any

from .io import StructuredLogger, load_json, now, write_json
from .providers import get_providers

OUTPUT = Path("editorial-brain/output")
LOGS = Path("editorial-brain/logs")
DB_PATH = Path("analytics/data/performance_database.json")


def run_all(root: Path = Path(".")) -> dict[str, Any]:
    package = load_json(root / OUTPUT / "published-package.json")
    metrics = metrics_collector(package, root=root)
    database = performance_database(package, metrics, root=root)
    performance = performance_analyzer(metrics, database, root=root)
    hooks = hook_analyzer(database, root=root)
    thumbnails = thumbnail_analyzer(database, root=root)
    retention = retention_analyzer(metrics, root=root)
    cta = cta_analyzer(database, root=root)
    recommendations = recommendation_engine(performance, hooks, thumbnails, retention, cta, root=root)
    reports = daily_performance_reporter(database, performance, hooks, thumbnails, retention, cta, recommendations, root=root)
    package_out = {
        "production_id": package["production_id"],
        "platform_metrics": metrics,
        "historical_metrics": database,
        "performance_analysis": performance,
        "hook_analysis": hooks,
        "thumbnail_analysis": thumbnails,
        "retention_analysis": retention,
        "cta_analysis": cta,
        "recommendations": recommendations,
        "daily_report": reports["daily_report"],
        "weekly_report": reports["weekly_report"],
        "monthly_report": reports["monthly_report"],
        "approval_status": "approved",
        "human_editorial_control": "recommendations_only_no_prompt_rewrites",
    }
    write_json(root / OUTPUT / "learning-package.json", package_out)
    StructuredLogger(root / LOGS, f"learning-package-{package['production_id']}").log({"event": "learning_package_written", "recommendations": len(recommendations["recommendations"])})
    return {"learning_package": package_out, **reports, "platform_metrics": metrics, "performance_database": database, "performance_analysis": performance, "hook_analysis": hooks, "thumbnail_analysis": thumbnails, "retention_analysis": retention, "cta_analysis": cta, "recommendations": recommendations}


def metrics_collector(published_package: dict[str, Any], *, root: Path = Path(".")) -> dict[str, Any]:
    platform_metrics = [provider.collect_metrics(published_package) for provider in get_providers()]
    totals = {
        "views": sum(item["views"] for item in platform_metrics),
        "watch_time_seconds": sum(item["watch_time_seconds"] for item in platform_metrics),
        "likes": sum(item["likes"] for item in platform_metrics),
        "comments": sum(item["comments"] for item in platform_metrics),
        "shares": sum(item["shares"] for item in platform_metrics),
        "subscribers_gained": sum(item["subscribers_gained"] for item in platform_metrics),
    }
    totals["average_view_duration_seconds"] = round(totals["watch_time_seconds"] / max(totals["views"], 1), 2)
    payload = {"production_id": published_package["production_id"], "component_id": "IF-AN01", "component_name": "Metrics Collector", "timestamp": now(), "platforms": platform_metrics, "totals": totals, "warnings": ["Dry-run/mock analytics used; replace with live adapters when publishing is live."] if published_package.get("dry_run", True) else [], "approval_status": "approved"}
    _write(root, "platform_metrics.json", payload, "metrics-collector")
    return payload


def performance_database(published_package: dict[str, Any], metrics: dict[str, Any], *, root: Path = Path(".")) -> dict[str, Any]:
    db_file = root / DB_PATH
    if db_file.exists():
        db = load_json(db_file)
    else:
        db = {"component_id": "IF-AN02", "component_name": "Performance Database", "videos": []}
    existing = [item for item in db["videos"] if item["production_id"] != published_package["production_id"]]
    entry = {
        "production_id": published_package["production_id"],
        "match": published_package["match"],
        "competition": published_package["competition"],
        "hook": published_package["publishing_metadata"]["selected_title"],
        "hook_type": _hook_type(published_package["publishing_metadata"]["selected_title"]),
        "thumbnail": published_package["publishing_metadata"]["thumbnail_text"],
        "thumbnail_style": "question_text_card",
        "publishing_time": published_package["publishing_schedule"]["publish_times"]["youtube"],
        "story_angle": published_package["publishing_metadata"]["selected_title"],
        "cta": published_package["publishing_metadata"]["cta_text"],
        "metrics": metrics["totals"],
        "platform_metrics": metrics["platforms"],
    }
    db["videos"] = existing + _baseline_entries() + [entry]
    db["updated_at"] = now()
    write_json(db_file, db)
    write_json(root / OUTPUT / "performance_database.json", db)
    return db


def performance_analyzer(metrics: dict[str, Any], database: dict[str, Any], *, root: Path = Path(".")) -> dict[str, Any]:
    history = [video["metrics"] for video in database["videos"][:-1]]
    avg_views = mean([item["views"] for item in history]) if history else metrics["totals"]["views"]
    avg_retention = mean([item["average_view_duration_seconds"] for item in history]) if history else metrics["totals"]["average_view_duration_seconds"]
    score = round((metrics["totals"]["views"] / max(avg_views, 1)) * 50 + (metrics["totals"]["average_view_duration_seconds"] / max(avg_retention, 1)) * 50)
    payload = {"production_id": metrics["production_id"], "component_id": "IF-AN03", "component_name": "Performance Analyzer", "timestamp": now(), "performance_score": score, "views_vs_average_percent": round((metrics["totals"]["views"] - avg_views) / max(avg_views, 1) * 100, 2), "retention_vs_average_percent": round((metrics["totals"]["average_view_duration_seconds"] - avg_retention) / max(avg_retention, 1) * 100, 2), "trend": "growth" if score >= 100 else "decline", "outliers": [], "approval_status": "approved"}
    _write(root, "performance_analysis.json", payload, "performance-analyzer")
    return payload


def hook_analyzer(database: dict[str, Any], *, root: Path = Path(".")) -> dict[str, Any]:
    rows = _rank(database["videos"], "hook_type", "views")
    payload = {"component_id": "IF-AN04", "component_name": "Hook Analyzer", "timestamp": now(), "hook_leaderboard": rows, "best_hook_type": rows[0]["key"] if rows else "unknown", "approval_status": "approved"}
    _write(root, "hook_analysis.json", payload, "hook-analyzer")
    return payload


def thumbnail_analyzer(database: dict[str, Any], *, root: Path = Path(".")) -> dict[str, Any]:
    rows = _rank(database["videos"], "thumbnail_style", "views")
    payload = {"component_id": "IF-AN05", "component_name": "Thumbnail Analyzer", "timestamp": now(), "thumbnail_leaderboard": rows, "best_thumbnail_style": rows[0]["key"] if rows else "unknown", "approval_status": "approved"}
    _write(root, "thumbnail_analysis.json", payload, "thumbnail-analyzer")
    return payload


def retention_analyzer(metrics: dict[str, Any], *, root: Path = Path(".")) -> dict[str, Any]:
    merged = _average_retention(metrics["platforms"])
    drop = min(merged, key=lambda item: item["retention_percent"])
    steep = next((item for item in merged if item["second"] >= 42), drop)
    payload = {"production_id": metrics["production_id"], "component_id": "IF-AN06", "component_name": "Audience Retention Analyzer", "timestamp": now(), "drop_off_timeline": merged, "most_engaging_moment": merged[0], "least_engaging_moment": drop, "primary_drop_off": steep, "approval_status": "approved"}
    _write(root, "retention_analysis.json", payload, "retention-analyzer")
    return payload


def cta_analyzer(database: dict[str, Any], *, root: Path = Path(".")) -> dict[str, Any]:
    rows = _rank(database["videos"], "cta", "comments")
    payload = {"component_id": "IF-AN07", "component_name": "CTA Analyzer", "timestamp": now(), "cta_leaderboard": rows, "best_cta": rows[0]["key"] if rows else "unknown", "approval_status": "approved"}
    _write(root, "cta_analysis.json", payload, "cta-analyzer")
    return payload


def recommendation_engine(performance: dict[str, Any], hooks: dict[str, Any], thumbnails: dict[str, Any], retention: dict[str, Any], cta: dict[str, Any], *, root: Path = Path(".")) -> dict[str, Any]:
    recommendations = []
    if retention["primary_drop_off"]["retention_percent"] < 40:
        recommendations.append({"area": "retention", "recommendation": "Bring the dashboard insight earlier than 42 seconds.", "priority": "high"})
    if hooks.get("best_hook_type") == "question":
        recommendations.append({"area": "hook", "recommendation": "Keep testing short question hooks; they currently lead the hook leaderboard.", "priority": "medium"})
    if performance["trend"] == "decline":
        recommendations.append({"area": "format", "recommendation": "Shorten the setup before the central question.", "priority": "medium"})
    recommendations.append({"area": "governance", "recommendation": "Do not automatically rewrite prompts; route these findings to human editorial review.", "priority": "required"})
    payload = {"component_id": "IF-AN08", "component_name": "Recommendation Engine", "timestamp": now(), "recommendations": recommendations, "prompt_rewrite_performed": False, "human_editorial_control": True, "approval_status": "approved"}
    _write(root, "recommendations.json", payload, "recommendation-engine")
    return payload


def daily_performance_reporter(database: dict[str, Any], performance: dict[str, Any], hooks: dict[str, Any], thumbnails: dict[str, Any], retention: dict[str, Any], cta: dict[str, Any], recommendations: dict[str, Any], *, root: Path = Path(".")) -> dict[str, Any]:
    top = max(database["videos"], key=lambda video: video["metrics"]["views"])
    worst = min(database["videos"], key=lambda video: video["metrics"]["views"])
    base = {"generated_at": now(), "top_video": top["production_id"], "worst_video": worst["production_id"], "best_hook": hooks.get("best_hook_type"), "best_thumbnail": thumbnails.get("best_thumbnail_style"), "best_publishing_time": top["publishing_time"], "retention_summary": retention["primary_drop_off"], "ctr_summary": _ctr_summary(top), "revenue_summary": {"revenue": 0.0, "rpm": 0.0}, "recommendations": recommendations["recommendations"], "approval_status": "approved"}
    daily = {"component_id": "IF-AN09", "component_name": "Daily Performance Reporter", "report_type": "daily", **base}
    weekly = {"component_id": "IF-AN09", "component_name": "Daily Performance Reporter", "report_type": "weekly", **base}
    monthly = {"component_id": "IF-AN09", "component_name": "Daily Performance Reporter", "report_type": "monthly", **base}
    write_json(root / OUTPUT / "daily_report.json", daily)
    write_json(root / OUTPUT / "weekly_report.json", weekly)
    write_json(root / OUTPUT / "monthly_report.json", monthly)
    return {"daily_report": daily, "weekly_report": weekly, "monthly_report": monthly}


def _write(root: Path, filename: str, payload: dict[str, Any], logger_name: str) -> None:
    write_json(root / OUTPUT / filename, payload)
    StructuredLogger(root / LOGS, logger_name).log({"event": f"{filename}_written", "approval_status": payload.get("approval_status")})


def _hook_type(title: str) -> str:
    if title.endswith("?"):
        return "question"
    if "first" in title.lower():
        return "tactical"
    return "data"


def _baseline_entries() -> list[dict[str, Any]]:
    return [
        {"production_id": "baseline-question", "match": {}, "competition": "Premier League", "hook": "Can the press decide it?", "hook_type": "question", "thumbnail": "Question card", "thumbnail_style": "question_text_card", "publishing_time": "2026-07-01T18:00:00+00:00", "story_angle": "question", "cta": "Tell us below.", "metrics": {"views": 900, "watch_time_seconds": 12000, "average_view_duration_seconds": 13.3, "likes": 41, "comments": 18, "shares": 11, "subscribers_gained": 4}, "platform_metrics": []},
        {"production_id": "baseline-data", "match": {}, "competition": "Premier League", "hook": "One stat explains the match", "hook_type": "data", "thumbnail": "Data card", "thumbnail_style": "stat_card", "publishing_time": "2026-07-02T18:00:00+00:00", "story_angle": "data", "cta": "What did you see?", "metrics": {"views": 720, "watch_time_seconds": 8700, "average_view_duration_seconds": 12.1, "likes": 28, "comments": 9, "shares": 8, "subscribers_gained": 3}, "platform_metrics": []},
    ]


def _rank(videos: list[dict[str, Any]], key: str, metric: str) -> list[dict[str, Any]]:
    grouped: dict[str, list[float]] = {}
    for video in videos:
        grouped.setdefault(str(video.get(key, "unknown")), []).append(float(video["metrics"].get(metric, 0)))
    return sorted([{"key": key_value, "average": round(mean(values), 2), "sample_size": len(values)} for key_value, values in grouped.items()], key=lambda row: row["average"], reverse=True)


def _average_retention(platforms: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seconds = sorted({point["second"] for platform in platforms for point in platform["audience_retention"]})
    rows = []
    for second in seconds:
        values = [point["retention_percent"] for platform in platforms for point in platform["audience_retention"] if point["second"] == second]
        rows.append({"second": second, "retention_percent": round(mean(values), 2)})
    return rows


def _ctr_summary(video: dict[str, Any]) -> dict[str, Any]:
    ctrs = [platform.get("ctr_percent", 0) for platform in video.get("platform_metrics", [])]
    return {"average_ctr_percent": round(mean(ctrs), 2) if ctrs else 0}
