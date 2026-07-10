from __future__ import annotations

from app.content.script_writer import script_issues


def validate_outputs(report: str, insight: dict[str, object], probabilities: dict[str, object], script: str, sheet: str) -> dict[str, object]:
    issues: list[str] = []
    if not report or "Sources Used" not in report:
        issues.append("report missing sources")
    if not insight.get("central_insight") or len(insight.get("supporting_evidence", [])) < 2:
        issues.append("insight lacks support")
    if sum(int(probabilities[key]) for key in ["team_a_win", "draw", "team_b_win"]) != 100:
        issues.append("probabilities do not total 100")
    issues.extend(script_issues(script))
    if "Moment" not in sheet or "CapCut" not in sheet:
        issues.append("director sheet incomplete")
    status = "PASS" if not issues else "NEEDS_REVIEW" if len(issues) <= 2 else "FAIL"
    return {"status": status, "issues": issues}
