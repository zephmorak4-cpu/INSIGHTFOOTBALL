# INSIGHT FOOTBALL Sprint 1 — Editorial Brain Implementation

Status: Sprint 1 build guide  
Scope: Editorial Brain only  
Agents included: Match Selector, Story Hunter, Evidence Filter, Insight Engine  
Agents excluded: Scriptwriter, Storyboard, Visual Director, Quality Control  

This guide defines how to build the first working INSIGHT FOOTBALL Editorial Brain. It does not redesign the system. It uses the existing Production Blueprint, Daily Input Specification, IF-ACP, Visual Production System, and Prompt Library.

---

## 1. Sprint Goal

Input:

```text
Daily Input JSON
```

Pipeline:

```text
Match Selector
-> Story Hunter
-> Evidence Filter
-> Insight Engine
```

Output:

```text
Editorial Production Package
```

Sprint 1 proves that the first four agents can work together, preserve locked fields, validate outputs, and produce a consistent editorial package.

No rendering. No publishing. No n8n. No Creatomate. No YouTube, Facebook, or Telegram integration.

---

## 2. Folder Structure

Created scaffold:

```text
editorial-brain/
  match-selector/
  story-hunter/
  evidence-filter/
  insight-engine/
  shared/
  tests/
  examples/
  config/
  output/
  schemas/
  logs/
```

Recommended file responsibilities:

```text
editorial-brain/
  README.md
  match-selector/
    agent.md
  story-hunter/
    agent.md
  evidence-filter/
    agent.md
  insight-engine/
    agent.md
  shared/
    agent-message-envelope.schema.json
    validation-rules.md
    locked-fields.md
  schemas/
    editorial-production-package.schema.json
  config/
    editorial-brain.config.json
  examples/
    liverpool-arsenal-daily-input.json
    liverpool-arsenal-sample-run.md
  output/
    .gitkeep
  logs/
    .gitkeep
  tests/
    test-plan.md
```

---

## 3. Build Order

### Task 1: Define Sprint 1 data contracts

Complexity: Medium  
Dependencies: IF-ACP, Prompt Library, Daily Input Specification

Build:

- Agent message envelope.
- Agent output contracts.
- Editorial Production Package schema.
- Locked-field list.
- Validation policy.

Done when:

- Every agent has required fields.
- Final package schema is stable.
- Locked fields are explicit.

### Task 2: Implement Daily Input loader

Complexity: Low  
Dependencies: Daily Input JSON

Build:

- Load one Daily Input JSON file.
- Verify required sections exist.
- Normalize team names and production metadata.
- Reject multi-match input.

Done when:

- Invalid daily input stops before Agent 1.

### Task 3: Implement Agent Runner

Complexity: Medium  
Dependencies: prompts, schemas, model config

Build orchestration:

```text
Load Daily Input
-> Run Match Selector
-> Validate Match Selector output
-> Run Story Hunter
-> Validate Story Hunter output
-> Run Evidence Filter
-> Validate Evidence Filter output
-> Run Insight Engine
-> Validate Insight Engine output
-> Assemble Editorial Package
```

Done when:

- Pipeline stops on validation failure.
- Each stage logs start, end, duration, confidence, warnings, errors, approval, and next agent.

### Task 4: Implement Validation Layer

Complexity: High  
Dependencies: schemas and IF-ACP

Build validators for:

- Required fields.
- JSON schema.
- Confidence score.
- Quality gates.
- Locked fields.
- Human review flags.

Done when:

- Invalid data cannot reach the next agent.

### Task 5: Implement Editorial Package assembler

Complexity: Medium  
Dependencies: all four agent outputs

Build:

- Combine approved outputs.
- Preserve locked fields.
- Add confidence scores.
- Add editorial notes.
- Add quality metrics.
- Add metadata and version.

Done when:

- Final JSON validates against schema.

### Task 6: Build tests

Complexity: Medium  
Dependencies: sample input and sample outputs

Build:

- Unit tests.
- Pipeline tests.
- Validation tests.
- Failure tests.
- Edge case tests.
- Recovery tests.

Done when:

- Happy path passes.
- Common failures stop the pipeline.
- Locked-field mutation is caught.

---

## 4. Agent Runner Design

The Agent Runner is a simple orchestration layer.

### Runner responsibilities

- Load config.
- Load Daily Input.
- Load prompt versions.
- Execute agents in fixed order.
- Validate each output.
- Enforce locked fields.
- Stop on failure.
- Write logs.
- Write final Editorial Production Package.

### Execution order

```json
[
  "IF-A01",
  "IF-A02",
  "IF-A03",
  "IF-A04"
]
```

### Pipeline behavior

Match Selector output must validate before Story Hunter starts.

Story Hunter output must validate before Evidence Filter starts.

Evidence Filter output must validate before Insight Engine starts.

Insight Engine output must validate before final package assembly.

### Stop conditions

Stop immediately if:

- JSON is invalid.
- Required fields are missing.
- Confidence is below threshold.
- Locked fields changed.
- Approval status is rejected or blocked.
- Human review is mandatory and policy says stop.

---

## 5. Validation Layer

### Universal validation rules

Every agent output must include:

- agent_id
- agent_name
- prompt_id
- prompt_version
- production_id
- confidence
- human_review_flags
- approval_status
- next_agent

### Confidence validation

Default threshold:

```text
70
```

Rules:

- 90-100: Continue.
- 80-89: Continue.
- 70-79: Continue with warning.
- 60-69: Stop and return to previous agent.
- 0-59: Reject or require human review.

### Locked-field validation

Locked fields by stage:

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

- insight_dashboard
- uncertainty_level
- match_edge

Validation must compare downstream outputs against locked upstream values.

### Quality gates

Match Selector gate:

- One match only.
- Selection reason exists.
- Story potential considered.
- Confidence >= 70.

Story Hunter gate:

- One story angle.
- One central question.
- One surprising fact.
- No betting framing.
- Confidence >= 70.

Evidence Filter gate:

- 3 to 5 evidence points.
- Evidence supports locked story.
- Weak data flagged.
- Confidence >= 70.

Insight Engine gate:

- Match edge is explainable.
- Probabilities total 100 if used.
- Uncertainty is included.
- No invented statistics.
- Confidence >= 70.

---

## 6. Editorial Production Package Schema

The final Sprint 1 output is the Editorial Production Package.

Required top-level fields:

- metadata
- version
- match
- competition
- story_angle
- central_question
- surprising_fact
- evidence
- insight_dashboard
- confidence_scores
- quality_metrics
- editorial_notes
- quality_notes
- locked_fields
- agent_outputs
- status

Schema summary:

```json
{
  "metadata": {
    "production_id": "",
    "date": "",
    "created_at": "",
    "input_version": "v1",
    "output_version": "v1"
  },
  "version": {
    "current_version": "v1",
    "history": [],
    "rollback_available": false
  },
  "match": {
    "home_team": "",
    "away_team": "",
    "kickoff_time": "",
    "country": ""
  },
  "competition": "",
  "story_angle": "",
  "central_question": "",
  "surprising_fact": "",
  "evidence": {
    "evidence_points": [],
    "evidence_strength_rating": 0,
    "weak_data_warnings": []
  },
  "insight_dashboard": {
    "match_edge": {},
    "form_summary": "",
    "tactical_explanation": "",
    "uncertainty_explanation": "",
    "uncertainty_level": "",
    "x_factor": "",
    "surprising_detail": "",
    "plain_english_summary": ""
  },
  "confidence_scores": {
    "match_selector": 0,
    "story_hunter": 0,
    "evidence_filter": 0,
    "insight_engine": 0,
    "overall_confidence": 0
  },
  "quality_metrics": {
    "story_score": 0,
    "clarity_score": 0,
    "evidence_score": 0,
    "editorial_score": 0,
    "overall_pass_fail": "FAIL"
  },
  "editorial_notes": [],
  "quality_notes": [],
  "locked_fields": {},
  "agent_outputs": {},
  "status": "draft"
}
```

---

## 7. Logging Standard

Every stage should log:

- stage_id
- agent_id
- agent_name
- start_time
- end_time
- duration_ms
- confidence
- warnings
- errors
- approval_status
- next_agent

Example:

```json
{
  "stage_id": "stage-02-story-hunter",
  "agent_id": "IF-A02",
  "agent_name": "Story Hunter",
  "start_time": "2026-07-06T10:05:00+01:00",
  "end_time": "2026-07-06T10:05:12+01:00",
  "duration_ms": 12000,
  "confidence": 86,
  "warnings": ["FACT_CHECK_REQUIRED"],
  "errors": [],
  "approval_status": "approved",
  "next_agent": "IF-A03"
}
```

---

## 8. Configuration

Sprint 1 configuration must cover:

- Model selection.
- Temperature.
- Max tokens.
- Retry policy.
- Timeout.
- Validation policy.
- Prompt versions.
- Execution order.

Recommended defaults:

```json
{
  "model_selection": {
    "default_provider": "openai",
    "default_model": "gpt-4.1",
    "fallback_model": "claude-sonnet"
  },
  "generation": {
    "temperature": 0.3,
    "max_tokens": 2500
  },
  "retry_policy": {
    "max_retries": 1,
    "retry_on_invalid_json": true,
    "retry_on_missing_required_fields": true,
    "retry_on_low_confidence": false
  },
  "timeout": {
    "agent_timeout_seconds": 60,
    "pipeline_timeout_seconds": 300
  },
  "validation_policy": {
    "minimum_confidence": 70,
    "stop_on_human_review_required": true,
    "stop_on_locked_field_change": true,
    "require_valid_json": true
  },
  "prompt_versions": {
    "IF-A01": "IF-PROMPT-01-MATCH-SELECTOR@v1.0",
    "IF-A02": "IF-PROMPT-02-STORY-HUNTER@v1.0",
    "IF-A03": "IF-PROMPT-03-EVIDENCE-FILTER@v1.0",
    "IF-A04": "IF-PROMPT-04-INSIGHT-ENGINE@v1.0"
  },
  "execution_order": ["IF-A01", "IF-A02", "IF-A03", "IF-A04"]
}
```

---

## 9. Error Recovery

### If Match Selector fails

Possible causes:

- No fixtures.
- Multiple matches selected.
- Confidence below 70.
- Missing selected_match.

Action:

- Stop pipeline.
- Request corrected Daily Input or human match selection.

### If Story Hunter fails

Possible causes:

- No compelling story.
- Weak central question.
- Surprising fact missing.
- Story sounds like betting advice.

Action:

- Stop pipeline.
- Return to Match Selector if the match is weak.
- Request more match context if data is thin.
- Allow Story Hunter v2 if the match is strong but angle is weak.

### If Evidence Filter confidence drops below 70

Possible causes:

- Fewer than 3 evidence points.
- Evidence does not support story.
- Evidence depends on unverified claims.
- Odds are doing too much work.

Action:

- Stop pipeline.
- Return to Story Hunter if story is unsupported.
- Request additional data if story is good but evidence is thin.
- Set status to `needs_review`.

### If Insight Engine cannot explain the story

Possible causes:

- Evidence is too weak.
- Story is too abstract.
- Dashboard would require invented stats.
- Match edge cannot be explained simply.

Action:

- Stop pipeline.
- Return to Evidence Filter for stronger evidence.
- Return to Story Hunter if story is not explainable.
- Require human editor if dashboard is optional but story is strong.

---

## 10. Quality Metrics

Every run must produce:

- Story Score.
- Clarity Score.
- Evidence Score.
- Editorial Score.
- Confidence.
- Overall Pass/Fail.

### Scoring rules

Story Score:

- 0-4: Weak or generic story.
- 5-6: Usable but not compelling.
- 7-8: Strong and clear.
- 9-10: Excellent, surprising, fan-relevant.

Clarity Score:

- Measures whether a general fan can understand the angle.

Evidence Score:

- Measures whether the facts support the story.

Editorial Score:

- Measures overall usefulness for a 60-second preview.

Overall Pass/Fail:

```text
PASS if all scores are 7+ and all agent confidence scores are 70+.
FAIL if any mandatory gate fails.
NEEDS_REVIEW if scores pass but human flags exist.
```

---

## 11. Testing Framework

### Unit tests

Test each agent output validator:

- Required fields present.
- Valid confidence score.
- Valid approval status.
- Valid next agent.
- Valid locked fields.

### Pipeline tests

Test happy path:

```text
Daily Input
-> Match Selector
-> Story Hunter
-> Evidence Filter
-> Insight Engine
-> Editorial Package
```

Expected result:

- Final package status is `approved` or `needs_review`.
- No locked fields changed.

### Validation tests

Test invalid cases:

- Missing selected_match.
- Missing central_question.
- Evidence points fewer than 3.
- Probabilities do not total 100.
- Confidence missing.
- Invalid JSON.

### Failure tests

Test pipeline stops when:

- Story Hunter confidence is 62.
- Evidence Filter changes central question.
- Insight Engine invents unsupported data.
- Human review flag is mandatory.

### Edge cases

Test:

- Low-profile match with strong story.
- Popular match with weak story.
- Balanced evidence with no clear edge.
- Injury-based story with unverified injury.
- Missing betting market.

### Recovery tests

Test:

- Story Hunter v2 after weak angle.
- Evidence Filter requests additional data.
- Insight Engine sends back unsupported dashboard.
- Human review required status.

---

## 12. Sample Run: Liverpool vs Arsenal

This example uses illustrative sample data only.

### Input

```json
{
  "production_metadata": {
    "date": "2026-07-06",
    "production_id": "if-2026-07-06-liverpool-arsenal",
    "language": "English",
    "status": "draft"
  },
  "fixtures": [
    {
      "home_team": "Liverpool",
      "away_team": "Arsenal",
      "competition": "Premier League",
      "kickoff_time": "20:00",
      "country": "England",
      "audience_interest": 10,
      "importance": 9,
      "rivalry": 8,
      "available_data": 9,
      "story_potential": 9
    }
  ],
  "match_context": {
    "recent_form": {
      "liverpool": "Sample: strong home starts",
      "arsenal": "Sample: slower away starts"
    },
    "tactical_notes": {
      "battle": "Liverpool early pressure vs Arsenal buildup"
    },
    "statistics": {
      "liverpool": "Sample: strong first-half output",
      "arsenal": "Sample: stronger after settling"
    }
  }
}
```

### Match Selector output

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

### Story Hunter output

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

### Evidence Filter output

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

### Insight Engine output

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

### Final Editorial Package

```json
{
  "metadata": {
    "production_id": "if-2026-07-06-liverpool-arsenal",
    "date": "2026-07-06",
    "input_version": "v1",
    "output_version": "v1"
  },
  "match": {
    "home_team": "Liverpool",
    "away_team": "Arsenal",
    "kickoff_time": "20:00",
    "country": "England"
  },
  "competition": "Premier League",
  "story_angle": "Liverpool may have the edge if they turn the first 20 minutes into chaos, but Arsenal have enough quality to punish one mistake.",
  "central_question": "Can Arsenal survive Liverpool's fast start?",
  "surprising_fact": "Sample data: Liverpool have started quickly in recent home matches, while Arsenal have sometimes needed longer to settle away.",
  "evidence": {
    "evidence_points": [
      "Liverpool have started recent home games quickly.",
      "Arsenal have sometimes needed longer to settle away.",
      "Arsenal still create enough chances to punish mistakes."
    ],
    "evidence_strength_rating": 7,
    "weak_data_warnings": ["Verify sample claims before publishing."]
  },
  "insight_dashboard": {
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
    "plain_english_summary": "Everything points to Liverpool having the early edge, but Arsenal can still make this uncomfortable."
  },
  "confidence_scores": {
    "match_selector": 94,
    "story_hunter": 86,
    "evidence_filter": 78,
    "insight_engine": 80,
    "overall_confidence": 84.5
  },
  "quality_metrics": {
    "story_score": 8.5,
    "clarity_score": 9,
    "evidence_score": 7,
    "editorial_score": 8,
    "overall_pass_fail": "NEEDS_REVIEW"
  },
  "editorial_notes": ["Story is strong and simple."],
  "quality_notes": ["Sample data must be verified before scripting."],
  "locked_fields": {
    "selected_match": "Liverpool vs Arsenal",
    "story_angle": "Liverpool may have the edge if they turn the first 20 minutes into chaos, but Arsenal have enough quality to punish one mistake.",
    "central_question": "Can Arsenal survive Liverpool's fast start?",
    "surprising_fact": "Sample data: Liverpool have started quickly in recent home matches, while Arsenal have sometimes needed longer to settle away."
  },
  "status": "needs_review"
}
```

---

## 13. Success Criteria

Sprint 1 is complete only if:

- Four agents execute in sequence.
- Data remains consistent.
- Locked fields are respected.
- Validation passes.
- Editorial Package is produced.
- Story remains unchanged after Story Hunter.
- Output follows Prompt Library.
- JSON schemas validate.
- Low confidence stops the pipeline.
- Human review flags are preserved.
- Logs are produced for every stage.

---

## 14. Sprint 1 Definition of Done

Sprint 1 is done when a developer can run one Liverpool vs Arsenal daily input through:

```text
Daily Input JSON
-> Match Selector
-> Story Hunter
-> Evidence Filter
-> Insight Engine
-> Editorial Production Package JSON
```

And receive a valid, consistent editorial package ready for Sprint 2 scripting.

