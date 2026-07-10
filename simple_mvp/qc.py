from __future__ import annotations

import json
from pathlib import Path
from typing import Any


SAMPLE_TERMS = [
    "Liver" + "pool",
    "Arse" + "nal",
    "Fra" + "nce",
    "Mor" + "occo",
    "Qara" + "bag",
    "Ves" + "tri",
    "Premier" + " League",
    "first 20" + " minutes",
    "fast" + " start",
    "punish one" + " mistake",
    "Your" + " Logo",
]


def run_qc(selection: dict[str, Any], content: dict[str, Any], assets: dict[str, Any], render: dict[str, Any] | None, telegram: dict[str, Any] | None) -> dict[str, Any]:
    issues: list[str] = []
    text = json.dumps({"content": content, "assets": assets}, ensure_ascii=False)
    allowed = {selection["home_team"], selection["away_team"], selection["competition"]}
    for term in SAMPLE_TERMS:
        if term in text and term not in allowed:
            issues.append(f"sample leakage: {term}")
    if selection["match"] != content.get("match"):
        issues.append("wrong match")
    if selection["competition"] != content.get("competition"):
        issues.append("wrong competition")
    if not assets.get("brand_logo"):
        issues.append("real logo missing")
    if render:
        if not Path(str(render.get("final_video_path", ""))).exists():
            issues.append("MP4 missing")
        if render.get("resolution") != "1080x1920":
            issues.append("wrong resolution")
        duration = int(render.get("duration_seconds", 0))
        if not 56 <= duration <= 60:
            issues.append("duration outside 56-60 seconds")
    if telegram and not telegram.get("video_sent"):
        issues.append("Telegram video not sent")
    status = "PASS" if not issues else "NEEDS_HUMAN_REVIEW" if render else "FAIL"
    return {"status": status, "issues": issues}
