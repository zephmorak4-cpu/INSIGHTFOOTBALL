# Liverpool vs Arsenal Sample Run

This run uses illustrative sample data only.

## Input

See:

```text
editorial-brain/examples/liverpool-arsenal-daily-input.json
```

## Stage 1: Match Selector

Expected output:

```json
{
  "agent_id": "IF-A01",
  "selected_match": {
    "home_team": "Liverpool",
    "away_team": "Arsenal",
    "competition": "Premier League",
    "kickoff_time": "20:00",
    "country": "England"
  },
  "selected_reason": "This match has strong audience interest, clear importance, and enough data for a useful pre-kickoff story.",
  "selection_score": 92,
  "confidence": {
    "score": 94,
    "reason": "Strong match profile and data availability."
  },
  "approval_status": "approved",
  "next_agent": "IF-A02"
}
```

## Stage 2: Story Hunter

Expected output:

```json
{
  "agent_id": "IF-A02",
  "story_angle": "Liverpool may have the edge if they turn the first 20 minutes into chaos, but Arsenal have enough quality to punish one mistake.",
  "central_question": "Can Arsenal survive Liverpool's fast start?",
  "surprising_fact": "Sample data: Liverpool have started quickly in recent home matches, while Arsenal have sometimes needed longer to settle away.",
  "why_fans_should_care": "Both fanbases will argue about whether Arsenal can handle that early pressure.",
  "confidence": {
    "score": 86,
    "reason": "The angle is simple, visual, and fan-relevant."
  },
  "human_review_flags": ["FACT_CHECK_REQUIRED"],
  "approval_status": "approved",
  "next_agent": "IF-A03"
}
```

## Stage 3: Evidence Filter

Expected output:

```json
{
  "agent_id": "IF-A03",
  "locked_story_angle": "Liverpool may have the edge if they turn the first 20 minutes into chaos, but Arsenal have enough quality to punish one mistake.",
  "locked_central_question": "Can Arsenal survive Liverpool's fast start?",
  "evidence_points": [
    {
      "point": "Sample data: Liverpool have started recent home games quickly.",
      "why_it_matters": "It supports the idea that Arsenal's first job is surviving the opening spell.",
      "confidence": "medium"
    },
    {
      "point": "Sample data: Arsenal have sometimes needed longer to settle away.",
      "why_it_matters": "It makes the first 20 minutes feel important.",
      "confidence": "medium"
    },
    {
      "point": "Sample data: Arsenal still create enough chances to punish mistakes.",
      "why_it_matters": "It keeps the story balanced and avoids certainty.",
      "confidence": "medium"
    }
  ],
  "evidence_strength_rating": 7,
  "weak_data_warnings": ["Verify sample claims before publishing."],
  "confidence": {
    "score": 78,
    "reason": "Evidence supports the story but needs fact-checking."
  },
  "approval_status": "approved",
  "next_agent": "IF-A04"
}
```

## Stage 4: Insight Engine

Expected output:

```json
{
  "agent_id": "IF-A04",
  "match_edge": {
    "home_win_probability": 43,
    "draw_probability": 27,
    "away_win_probability": 30,
    "plain_label": "Small edge: Liverpool"
  },
  "form_summary": "Liverpool look stronger early at home, but Arsenal remain dangerous away.",
  "tactical_explanation": "Liverpool's early pressure could test Arsenal's first pass through midfield.",
  "uncertainty_explanation": "The edge is small because Arsenal have enough quality to punish one mistake.",
  "uncertainty_level": "medium",
  "x_factor": "Arsenal's first pass through midfield under pressure.",
  "surprising_detail": "The first 20 minutes may matter more than the final scoreline suggests.",
  "plain_english_summary": "Everything points to Liverpool having the early edge, but Arsenal can still make this uncomfortable.",
  "confidence": {
    "score": 80,
    "reason": "Dashboard is explainable from the evidence, with uncertainty clearly shown."
  },
  "approval_status": "approved",
  "next_agent": "package_assembler"
}
```

## Final Expected Status

```text
needs_review
```

Reason:

```text
Sample data must be replaced with verified data before Sprint 2 scripting.
```
