# Editorial Brain Validation Rules

Every agent output must pass validation before the next agent runs.

## Universal Required Fields

- agent_id
- agent_name
- prompt_id
- prompt_version
- production_id
- confidence
- human_review_flags
- approval_status
- next_agent

## Confidence Threshold

Minimum confidence:

```text
70
```

If confidence is below 70, stop the pipeline.

## Locked Fields

After Match Selector:

- selected_match
- competition
- kickoff_time
- production_id

After Story Hunter:

- story_angle
- central_question
- surprising_fact

After Evidence Filter:

- evidence_points
- evidence_strength_rating

After Insight Engine:

- match_edge
- uncertainty_level
- insight_dashboard

## Mandatory Stops

Stop if:

- JSON is invalid.
- Required fields are missing.
- Locked fields are changed.
- Confidence is below 70.
- approval_status is rejected or blocked.
- Human review is required and policy requires stopping.
