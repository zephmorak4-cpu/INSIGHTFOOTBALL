"""Canonical Editorial Package assembly."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def assemble_editorial_package(
    *,
    daily_input: dict[str, Any],
    match_selection: dict[str, Any],
    story_hunter: dict[str, Any],
    evidence_filter: dict[str, Any],
    insight_engine: dict[str, Any],
    execution_metadata: dict[str, Any],
) -> dict[str, Any]:
    selected_match = match_selection["selected_match"]
    confidence_scores = {
        "match_selector": match_selection["confidence"]["score"],
        "story_hunter": story_hunter["story_confidence"],
        "evidence_filter": evidence_filter["evidence_confidence"],
        "insight_engine": insight_engine["confidence"]["score"],
    }
    confidence_scores["overall"] = round(sum(confidence_scores.values()) / len(confidence_scores), 2)

    warnings = []
    for output in [match_selection, story_hunter, evidence_filter, insight_engine]:
        warnings.extend(output.get("warnings", []))
        warnings.extend(output.get("data_gaps", []))

    return {
        "metadata": {
            "production_id": match_selection["production_id"],
            "date": daily_input["production_metadata"]["date"],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "package_version": "v1",
            "source": "editorial-orchestrator",
        },
        "match": selected_match,
        "competition": selected_match["competition"],
        "story_angle": story_hunter["story_angle"],
        "central_question": story_hunter["central_question"],
        "surprising_fact": story_hunter["surprising_fact"],
        "primary_evidence": evidence_filter["primary_evidence"],
        "secondary_evidence": evidence_filter["secondary_evidence"],
        "contradictory_evidence": evidence_filter["contradictory_evidence"],
        "insight_summary": insight_engine["insight_summary"],
        "match_edge": insight_engine["match_edge"],
        "key_advantage": insight_engine["key_advantage"],
        "tactical_explanation": insight_engine["tactical_explanation"],
        "uncertainty_summary": insight_engine["uncertainty_summary"],
        "x_factor": insight_engine["x_factor"],
        "viewer_takeaway": insight_engine["viewer_takeaway"],
        "confidence_scores": confidence_scores,
        "locked_fields": {
            "selected_match": selected_match,
            "selection_source": match_selection.get("selection_source", "automatic_recommendation"),
            "story_angle": story_hunter["story_angle"],
            "central_question": story_hunter["central_question"],
            "surprising_fact": story_hunter["surprising_fact"],
        },
        "warnings": sorted(set(warnings)),
        "editorial_notes": insight_engine.get("editorial_notes", []),
        "execution_metadata": execution_metadata,
        "agent_outputs": {
            "match_selector": match_selection,
            "story_hunter": story_hunter,
            "evidence_filter": evidence_filter,
            "insight_engine": insight_engine,
        },
        "status": "approved",
    }
