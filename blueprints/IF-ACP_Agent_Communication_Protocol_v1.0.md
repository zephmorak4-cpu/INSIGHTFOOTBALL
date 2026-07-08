# INSIGHT FOOTBALL Agent Communication Protocol

Protocol name: IF-ACP  
Version: 1.0  
Status: Official internal communication standard  
Purpose: define how autonomous AI workers communicate inside the INSIGHT FOOTBALL newsroom.

This document is not implementation code. It is the communication standard for the INSIGHT FOOTBALL production system.

---

## 1. Protocol Principles

INSIGHT FOOTBALL agents do not chat freely with each other. They pass structured newsroom messages.

Every agent must:

- Receive only the information it needs.
- Return valid JSON.
- Preserve locked decisions from previous agents.
- Flag uncertainty clearly.
- Refuse to continue when mandatory fields are missing.
- Avoid betting-tip language.
- Keep the brand tone simple, friendly, curious, and human.

The protocol protects the production chain from four common failures:

- Agents changing decisions they are not allowed to change.
- Weak data turning into confident claims.
- Betting-market data becoming the main story.
- Robotic or technical language entering the final video.

---

## 2. Agent Registry

| Agent ID | Agent Name | Primary Mission |
|---|---|---|
| IF-A01 | Match Selector | Choose the best match to cover. |
| IF-A02 | Story Hunter | Discover the strongest pre-kickoff story. |
| IF-A03 | Evidence Filter | Select only evidence that supports the story. |
| IF-A04 | Insight Scoring Agent | Build the simple match dashboard. |
| IF-A05 | Scriptwriter | Write the final 60-second voiceover. |
| IF-A06 | Storyboard Agent | Convert script into timestamped scenes. |
| IF-A07 | Visual Director | Convert scenes into render-ready visual instructions. |
| IF-A08 | Quality Control Agent | Approve, reject, or send back the package. |

---

## 3. Standard Message Format

Every message between agents must use this envelope.

```json
{
  "message_id": "if-acp-msg-0001",
  "agent_id": "IF-A01",
  "agent_name": "Match Selector",
  "timestamp": "2026-07-06T10:00:00+01:00",
  "production_id": "if-2026-07-06-liverpool-arsenal",
  "input_version": "v1",
  "output_version": "v1",
  "confidence": {
    "score": 0,
    "reason": ""
  },
  "warnings": [],
  "errors": [],
  "locked_fields": [],
  "editable_fields": [],
  "next_agent": "IF-A02",
  "approval_status": "pending",
  "payload": {}
}
```

### Required envelope fields

- message_id
- agent_id
- agent_name
- timestamp
- production_id
- input_version
- output_version
- confidence
- warnings
- errors
- locked_fields
- editable_fields
- next_agent
- approval_status
- payload

### Approval status values

```text
pending
approved
needs_revision
rejected
blocked
human_review_required
```

### Confidence object

```json
{
  "score": 85,
  "reason": "Strong recent form data and clear story relevance."
}
```

Confidence must be a whole number from 0 to 100.

---

## 4. Versioning Standard

Every agent output must support:

- v1
- v2
- v3
- history
- rollback support

### Version object

```json
{
  "current_version": "v2",
  "history": [
    {
      "version": "v1",
      "timestamp": "2026-07-06T10:00:00+01:00",
      "agent_id": "IF-A02",
      "summary": "Initial story angle created.",
      "status": "replaced"
    },
    {
      "version": "v2",
      "timestamp": "2026-07-06T10:08:00+01:00",
      "agent_id": "IF-A02",
      "summary": "Story angle revised after weak evidence warning.",
      "status": "active"
    }
  ],
  "rollback_available": true,
  "rollback_target": "v1"
}
```

### Version rules

- v1 is the first valid agent output.
- v2 is created when an output is revised after validation, QC, or human feedback.
- v3 is the maximum normal revision before human review is required.
- After v3, the agent must set `approval_status` to `human_review_required`.
- History must never be deleted.
- Rollback must restore the previous payload and locked-field state.

---

## 5. Quality Gates

An agent cannot continue unless mandatory fields exist.

### Gate statuses

```text
pass
fail
warning
human_review_required
```

### Universal quality gate

Every agent must check:

- Required input fields exist.
- Input is for one match only.
- Production ID is present.
- Previous locked fields are preserved.
- Confidence score is present.
- Warnings and errors are explicit.
- Output is valid JSON.

If any mandatory field is missing, the agent must stop and return:

```json
{
  "approval_status": "blocked",
  "errors": ["Missing required field: selected_match"],
  "next_agent": "previous_agent"
}
```

---

## 6. Confidence Rules

Confidence is not how strongly the agent likes its own answer. It is how reliable the output is based on the quality of available data and clarity of the task.

| Score | Meaning | Action |
|---|---|---|
| 90-100 | Very strong | Continue. |
| 80-89 | Strong | Continue. |
| 70-79 | Usable but watch carefully | Continue with warning. |
| 60-69 | Weak | Send back to previous agent or request human review. |
| 0-59 | Not production-ready | Reject or block. |

### Confidence examples

```json
{
  "score": 95,
  "reason": "Strong evidence from form, injuries, and home/away performance."
}
```

```json
{
  "score": 66,
  "reason": "The match is popular, but available data does not support a compelling story yet."
}
```

### Escalation rule

If confidence is below 70:

- Do not continue to the next agent automatically.
- Send the package back to the previous agent if the issue can be fixed there.
- Request human review if the issue is editorial, factual, legal, or brand-sensitive.

---

## 7. Rejection Rules

Agents must reject inputs when continuing would damage quality.

### Standard rejection format

```json
{
  "approval_status": "rejected",
  "confidence": {
    "score": 48,
    "reason": "No compelling pre-kickoff story could be found."
  },
  "errors": ["No clear central question.", "Available evidence is weak."],
  "recovery_strategy": "Return to Match Selector and choose a different match."
}
```

### Example rejection

Story Hunter rejects match because:

- No compelling story.
- No surprising fact.
- No fan-relevant question.
- Available data is too thin.

Recovery:

- Return to Match Selector.
- Choose runner-up match.
- Add more data.
- Request human editor decision.

---

## 8. Agent Contracts

## IF-A01: Match Selector

### Mission

Choose the best match to cover for the day.

### Responsibilities

- Review daily fixtures.
- Score audience interest, competition importance, rivalry level, and data availability.
- Select exactly one match.
- Explain why the match was selected.
- Flag weak data or runner-up options.

### Allowed inputs

- Daily fixtures.
- Competition names.
- Kickoff times.
- Country.
- Team popularity.
- Match importance.
- Rivalry level.
- Data availability.
- Expected audience interest.

### Forbidden inputs

- Final script.
- Storyboard.
- Visual direction.
- Betting advice.
- Predicted guaranteed outcome.
- Personal preference without data.

### Required outputs

- selected_match
- selected_reason
- selection_score
- runner_up_matches
- data_gaps
- confidence
- human_review_flags

### Output JSON schema

```json
{
  "type": "object",
  "required": [
    "selected_match",
    "selected_reason",
    "selection_score",
    "runner_up_matches",
    "data_gaps",
    "confidence",
    "human_review_flags"
  ],
  "properties": {
    "selected_match": {
      "type": "object",
      "required": ["home_team", "away_team", "competition", "kickoff_time"],
      "properties": {
        "home_team": { "type": "string" },
        "away_team": { "type": "string" },
        "competition": { "type": "string" },
        "kickoff_time": { "type": "string" },
        "country": { "type": "string" }
      }
    },
    "selected_reason": { "type": "string" },
    "selection_score": { "type": "integer", "minimum": 0, "maximum": 100 },
    "runner_up_matches": { "type": "array" },
    "data_gaps": { "type": "array" },
    "confidence": { "type": "object" },
    "human_review_flags": { "type": "array" }
  }
}
```

### Validation rules

- Must select one match only.
- Selection score must be 0 to 100.
- Must explain why this match is better than alternatives.

### Failure conditions

- No fixtures available.
- Multiple matches selected.
- Selection based only on team popularity.
- Confidence below 70.

### Recovery strategy

- Request more fixture data.
- Choose runner-up match.
- Ask human producer to pick the match.

### Confidence score

High confidence requires:

- Strong match importance.
- Strong audience interest.
- Sufficient data availability.

### Human review flags

- Multiple matches have similar selection score.
- Selected match has weak data.
- Match is low-interest but strategically important.

---

## IF-A02: Story Hunter

### Mission

Find the strongest pre-kickoff story angle.

### Responsibilities

- Discover one main story.
- Create one central question.
- Identify one surprising fact.
- Explain why fans should care.
- Reject weak or generic angles.

### Allowed inputs

- selected_match.
- selected_reason.
- team form.
- injuries.
- suspensions.
- head-to-head.
- home/away performance.
- tactical notes.
- recent news.
- odds as optional context only.

### Forbidden inputs

- Final script.
- Visual storyboard.
- Render instructions.
- Requests to predict a guaranteed outcome.
- Betting market as the main story.

### Required outputs

- main_story_angle
- central_question
- surprising_fact
- why_this_angle_matters
- why_fans_should_care
- rejected_angles
- data_warnings
- confidence
- human_review_flags

### Output JSON schema

```json
{
  "type": "object",
  "required": [
    "main_story_angle",
    "central_question",
    "surprising_fact",
    "why_this_angle_matters",
    "why_fans_should_care",
    "rejected_angles",
    "data_warnings",
    "confidence",
    "human_review_flags"
  ],
  "properties": {
    "main_story_angle": { "type": "string" },
    "central_question": { "type": "string" },
    "surprising_fact": { "type": "string" },
    "why_this_angle_matters": { "type": "string" },
    "why_fans_should_care": { "type": "string" },
    "rejected_angles": { "type": "array" },
    "data_warnings": { "type": "array" },
    "confidence": { "type": "object" },
    "human_review_flags": { "type": "array" }
  }
}
```

### Validation rules

- Must produce one main story only.
- Central question must be conversational.
- Surprising fact must support the story.
- Must not write the final script.

### Failure conditions

- No compelling story.
- Central question is vague.
- Surprising fact is weak.
- Story sounds like betting advice.
- Confidence below 70.

### Recovery strategy

- Request more data from daily input.
- Ask Match Selector for runner-up match.
- Generate alternative angles for human review.

### Confidence score

High confidence requires:

- Strong story relevance.
- Clear central question.
- Evidence exists to support the angle.

### Human review flags

- Story depends on unverified news.
- Story is controversial.
- Story is too similar to recent videos.

---

## IF-A03: Evidence Filter

### Mission

Select only the evidence needed to support the story.

### Responsibilities

- Keep 3 to 5 evidence points.
- Remove irrelevant statistics.
- Flag weak data.
- Recommend visual evidence.
- Preserve the story angle and central question.

### Allowed inputs

- main_story_angle.
- central_question.
- surprising_fact.
- raw statistics.
- form.
- injuries.
- head-to-head.
- home/away data.
- xG if available.
- odds as optional supporting context.

### Forbidden inputs

- New story angle unless requested by rejection.
- Final voiceover.
- Visual layout decisions.
- Betting market as main evidence.

### Required outputs

- evidence_points
- evidence_strength_rating
- weak_data_warnings
- recommended_visual_evidence
- confidence
- human_review_flags

### Output JSON schema

```json
{
  "type": "object",
  "required": [
    "evidence_points",
    "evidence_strength_rating",
    "weak_data_warnings",
    "recommended_visual_evidence",
    "confidence",
    "human_review_flags"
  ],
  "properties": {
    "evidence_points": {
      "type": "array",
      "minItems": 3,
      "maxItems": 5
    },
    "evidence_strength_rating": {
      "type": "integer",
      "minimum": 0,
      "maximum": 10
    },
    "weak_data_warnings": { "type": "array" },
    "recommended_visual_evidence": { "type": "array" },
    "confidence": { "type": "object" },
    "human_review_flags": { "type": "array" }
  }
}
```

### Validation rules

- Must return 3 to 5 evidence points.
- Evidence must support locked story angle.
- Must explain why each point matters.

### Failure conditions

- Fewer than 3 useful evidence points.
- Evidence contradicts the story.
- Evidence is mostly odds-based.
- Confidence below 70.

### Recovery strategy

- Request more data.
- Ask Story Hunter to revise story.
- Flag human review if story is strong but evidence is thin.

### Confidence score

High confidence requires:

- Multiple independent evidence points.
- Low reliance on unverified news.
- Clear visual evidence options.

### Human review flags

- Weak data warning.
- Important claim needs source verification.
- Evidence supports a different story than the locked angle.

---

## IF-A04: Insight Scoring Agent

### Mission

Build a simple, explainable dashboard for visuals.

### Responsibilities

- Create home/draw/away probabilities.
- Summarize form.
- Identify tactical advantage.
- Set uncertainty level.
- Identify X-factor.
- Write plain English dashboard summary.

### Allowed inputs

- selected_match.
- story_angle.
- evidence_points.
- form.
- home/away data.
- injuries.
- odds as optional calibration only.

### Forbidden inputs

- Instructions to guarantee outcome.
- Scriptwriting decisions.
- Visual animation instructions.
- Complex black-box scoring.

### Required outputs

- home_win_probability
- draw_probability
- away_win_probability
- form_summary
- tactical_advantage
- uncertainty_level
- x_factor
- surprising_detail
- plain_english_summary
- confidence
- human_review_flags

### Output JSON schema

```json
{
  "type": "object",
  "required": [
    "home_win_probability",
    "draw_probability",
    "away_win_probability",
    "form_summary",
    "tactical_advantage",
    "uncertainty_level",
    "x_factor",
    "surprising_detail",
    "plain_english_summary",
    "confidence",
    "human_review_flags"
  ],
  "properties": {
    "home_win_probability": { "type": "integer", "minimum": 0, "maximum": 100 },
    "draw_probability": { "type": "integer", "minimum": 0, "maximum": 100 },
    "away_win_probability": { "type": "integer", "minimum": 0, "maximum": 100 },
    "form_summary": { "type": "string" },
    "tactical_advantage": { "type": "string" },
    "uncertainty_level": { "type": "string", "enum": ["low", "medium", "high"] },
    "x_factor": { "type": "string" },
    "surprising_detail": { "type": "string" },
    "plain_english_summary": { "type": "string" },
    "confidence": { "type": "object" },
    "human_review_flags": { "type": "array" }
  }
}
```

### Validation rules

- Probabilities must total 100.
- Use whole numbers only.
- Must not present probabilities as guarantees.

### Failure conditions

- Probabilities do not total 100.
- Dashboard contradicts evidence.
- Dashboard is too technical.
- Confidence below 70.

### Recovery strategy

- Recalculate from evidence.
- Lower confidence and request review.
- Send back to Evidence Filter if evidence is too weak.

### Confidence score

High confidence requires:

- Evidence supports edge.
- Probabilities are explainable.
- Uncertainty is acknowledged.

### Human review flags

- Dashboard may look like betting prediction.
- Score is heavily influenced by odds.
- X-factor depends on unconfirmed squad news.

---

## IF-A05: Scriptwriter

### Mission

Write the final 60-second script.

### Responsibilities

- Use the brand opening.
- Reveal the surprising fact.
- Ask the central question.
- Explain one story clearly.
- Mention evidence naturally.
- End with a debate invitation.

### Allowed inputs

- selected_match.
- story_angle.
- central_question.
- surprising_fact.
- evidence_points.
- insight_dashboard.
- brand tone rules.

### Forbidden inputs

- Raw data dump not filtered by Evidence Filter.
- Requests to guarantee outcome.
- Heavy tactical jargon.
- Betting-tip framing.
- Visual layout decisions.

### Required outputs

- final_voiceover_script
- estimated_duration_seconds
- word_count
- hook
- central_question
- closing_engagement_question
- compliance_warning
- confidence
- human_review_flags

### Output JSON schema

```json
{
  "type": "object",
  "required": [
    "final_voiceover_script",
    "estimated_duration_seconds",
    "word_count",
    "hook",
    "central_question",
    "closing_engagement_question",
    "compliance_warning",
    "confidence",
    "human_review_flags"
  ],
  "properties": {
    "final_voiceover_script": { "type": "string" },
    "estimated_duration_seconds": { "type": "integer", "maximum": 60 },
    "word_count": { "type": "integer", "maximum": 150 },
    "hook": { "type": "string" },
    "central_question": { "type": "string" },
    "closing_engagement_question": { "type": "string" },
    "compliance_warning": { "type": "string" },
    "confidence": { "type": "object" },
    "human_review_flags": { "type": "array" }
  }
}
```

### Validation rules

- Under 150 words.
- Under 60 seconds.
- Must include brand opening.
- Must include central question.
- Must not change locked central question without explicit revision approval.

### Failure conditions

- Too long.
- Robotic tone.
- Betting-tip language.
- Too many stats.
- No engagement ending.
- Confidence below 70.

### Recovery strategy

- Rewrite script shorter.
- Simplify language.
- Send back to Story Hunter if story is unclear.
- Send back to Evidence Filter if evidence cannot be explained simply.

### Confidence score

High confidence requires:

- Strong hook.
- Simple language.
- Clear story.
- Script fits 60 seconds.

### Human review flags

- Script may sound too technical.
- Hook is weaker than story.
- Central question changed.
- Compliance warning is not empty.

---

## IF-A06: Storyboard Agent

### Mission

Convert the script into a scene-by-scene production plan.

### Responsibilities

- Create timestamped scenes.
- Change visuals every 3 to 5 seconds.
- Add on-screen text.
- Add caption text.
- Identify assets needed.
- Preserve the approved script.

### Allowed inputs

- final_voiceover_script.
- dashboard data.
- visual rules.
- asset availability notes.

### Forbidden inputs

- New story angle.
- New evidence claims.
- Script rewrites unless requested.
- Copyrighted asset assumptions.

### Required outputs

- scenes
- scene_number
- timestamp_start
- timestamp_end
- voiceover_line
- visual_description
- on_screen_text
- animation_instruction
- asset_needed
- caption_text
- confidence
- human_review_flags

### Output JSON schema

```json
{
  "type": "object",
  "required": ["scenes", "confidence", "human_review_flags"],
  "properties": {
    "scenes": {
      "type": "array",
      "items": {
        "type": "object",
        "required": [
          "scene_number",
          "timestamp_start",
          "timestamp_end",
          "voiceover_line",
          "visual_description",
          "on_screen_text",
          "animation_instruction",
          "asset_needed",
          "caption_text"
        ]
      }
    },
    "confidence": { "type": "object" },
    "human_review_flags": { "type": "array" }
  }
}
```

### Validation rules

- No scene may exceed 5 seconds without a visual change.
- Total duration must be 60 seconds or less.
- Captions must be short.

### Failure conditions

- Scene timing exceeds script duration.
- Visuals do not support story.
- Captions are too long.
- Confidence below 70.

### Recovery strategy

- Split long scenes.
- Reduce on-screen text.
- Send back to Scriptwriter if script cannot be storyboarded under 60 seconds.

### Confidence score

High confidence requires:

- Clean scene pacing.
- Clear visual support.
- No asset uncertainty.

### Human review flags

- Asset rights unclear.
- Visual plan may be cluttered.
- Captions need manual shortening.

---

## IF-A07: Visual Director

### Mission

Convert the storyboard into render-ready template instructions.

### Responsibilities

- Define layout.
- Define camera movement.
- Define typography.
- Define caption placement.
- Define dashboard design.
- List assets.
- Define render instructions.

### Allowed inputs

- storyboard.
- available assets.
- team names.
- team logos.
- brand colors.
- dashboard data.

### Forbidden inputs

- New facts.
- New story angle.
- Script rewrites.
- Unlicensed asset assumptions.

### Required outputs

- layout_instructions
- camera_movement
- typography_rules
- caption_placement
- dashboard_design
- animation_rules
- asset_list
- render_instructions
- confidence
- human_review_flags

### Output JSON schema

```json
{
  "type": "object",
  "required": [
    "layout_instructions",
    "camera_movement",
    "typography_rules",
    "caption_placement",
    "dashboard_design",
    "animation_rules",
    "asset_list",
    "render_instructions",
    "confidence",
    "human_review_flags"
  ],
  "properties": {
    "layout_instructions": { "type": "array" },
    "camera_movement": { "type": "array" },
    "typography_rules": { "type": "array" },
    "caption_placement": { "type": "string" },
    "dashboard_design": { "type": "array" },
    "animation_rules": { "type": "array" },
    "asset_list": { "type": "array" },
    "render_instructions": { "type": "array" },
    "confidence": { "type": "object" },
    "human_review_flags": { "type": "array" }
  }
}
```

### Validation rules

- Must use vertical 9:16.
- Captions must stay visible.
- Every asset must be listed.
- No unsafe footage.

### Failure conditions

- Required assets unavailable.
- Visuals are too cluttered.
- Instructions cannot be rendered by a template system.
- Confidence below 70.

### Recovery strategy

- Replace unsafe assets.
- Simplify layout.
- Send back to Storyboard Agent if scenes require impossible visuals.

### Confidence score

High confidence requires:

- Assets available.
- Layout is simple.
- Render instructions are clear.

### Human review flags

- Logo rights unclear.
- Player image rights unclear.
- Template renderer limitations.

---

## IF-A08: Quality Control Agent

### Mission

Approve, reject, or send back the production package.

### Responsibilities

- Check script.
- Check storyboard.
- Check evidence.
- Check dashboard.
- Check brand rules.
- Fail unsafe or weak packages.
- Recommend fixes.

### Allowed inputs

- full production package.
- script.
- storyboard.
- evidence.
- dashboard.
- visual direction.
- brand rules.

### Forbidden inputs

- New facts not present in package.
- Requests to approve despite mandatory failure.
- Requests to ignore legal or brand risk.

### Required outputs

- pass_or_fail
- reason
- issues_found
- required_fixes
- retention_score
- clarity_score
- story_score
- evidence_score
- final_recommendation
- confidence
- human_review_flags

### Output JSON schema

```json
{
  "type": "object",
  "required": [
    "pass_or_fail",
    "reason",
    "issues_found",
    "required_fixes",
    "retention_score",
    "clarity_score",
    "story_score",
    "evidence_score",
    "final_recommendation",
    "confidence",
    "human_review_flags"
  ],
  "properties": {
    "pass_or_fail": { "type": "string", "enum": ["pass", "fail"] },
    "reason": { "type": "string" },
    "issues_found": { "type": "array" },
    "required_fixes": { "type": "array" },
    "retention_score": { "type": "number", "minimum": 0, "maximum": 10 },
    "clarity_score": { "type": "number", "minimum": 0, "maximum": 10 },
    "story_score": { "type": "number", "minimum": 0, "maximum": 10 },
    "evidence_score": { "type": "number", "minimum": 0, "maximum": 10 },
    "final_recommendation": { "type": "string" },
    "confidence": { "type": "object" },
    "human_review_flags": { "type": "array" }
  }
}
```

### Validation rules

- Must fail if any mandatory fail condition exists.
- Must give required fixes when failed.
- Must not approve over-60-second videos.

### Failure conditions

- Boring opening.
- Robotic script.
- No central question.
- Weak surprising fact.
- Too technical.
- Longer than 60 seconds.
- Betting-tip language.
- Too many unexplained stats.
- No engagement ending.

### Recovery strategy

- Send back to the responsible agent.
- Request human review for legal, editorial, or brand-sensitive issues.
- Reject if package cannot be fixed within three revisions.

### Confidence score

High confidence requires:

- Clear pass/fail evidence.
- Strong brand fit.
- No unresolved warnings.

### Human review flags

- Legal asset concern.
- Factual uncertainty.
- Tone uncertainty.
- Weak but publishable story.

---

## 9. Agent-to-Agent Communication Rules

This section defines every approved connection in the production chain.

## IF-A01 Match Selector -> IF-A02 Story Hunter

### Information transferred

- selected_match
- selected_reason
- selection_score
- runner_up_matches
- data_gaps
- production_metadata
- daily_input_reference

### Must never be transferred

- Final script.
- Suggested guaranteed outcome.
- Betting pick.
- Visual plan.

### May be modified by Story Hunter

- Story angle.
- Central question.
- Surprising fact.
- Fan relevance.

### Becomes locked

- selected_match
- competition
- kickoff_time
- production_id

Locked fields can only change if:

- Match Selector issues a revised output version.
- Human producer approves match replacement.

---

## IF-A02 Story Hunter -> IF-A03 Evidence Filter

### Information transferred

- selected_match
- main_story_angle
- central_question
- surprising_fact
- why_this_angle_matters
- why_fans_should_care
- data_warnings

### Must never be transferred

- Full final script.
- Visual instructions.
- Pressure to prove a weak story.
- Betting-market framing as the core narrative.

### May be modified by Evidence Filter

- Evidence strength.
- Data warnings.
- Recommended visual evidence.
- Request for revised story if evidence is weak.

### Evidence Filter is not allowed to change

- selected_match
- main_story_angle
- central_question
- surprising_fact

### Becomes locked

- main_story_angle
- central_question
- surprising_fact

Locked story fields can only change if:

- Evidence Filter rejects evidence support.
- Story Hunter creates v2.
- Human review approves the change.

---

## IF-A03 Evidence Filter -> IF-A04 Insight Scoring Agent

### Information transferred

- selected_match
- main_story_angle
- central_question
- evidence_points
- evidence_strength_rating
- weak_data_warnings
- recommended_visual_evidence

### Must never be transferred

- Unfiltered raw stats as final evidence.
- Unsupported claims.
- Request to force the dashboard toward a desired result.

### May be modified by Insight Scoring Agent

- Probability edge.
- Form summary.
- Tactical advantage wording.
- Uncertainty level.
- X-factor.
- Plain English dashboard summary.

### Insight Scoring Agent is not allowed to change

- selected_match
- main_story_angle
- central_question
- evidence_points content

### Becomes locked

- evidence_points
- evidence_strength_rating

Evidence can only change if:

- Dashboard cannot be explained from evidence.
- QC finds unsupported evidence.
- Evidence Filter creates v2.

---

## IF-A04 Insight Scoring Agent -> IF-A05 Scriptwriter

### Information transferred

- selected_match
- main_story_angle
- central_question
- surprising_fact
- evidence_points
- insight_dashboard
- plain_english_summary
- uncertainty_level
- human_review_flags

### Must never be transferred

- Instruction to promise outcome.
- Instruction to read every metric.
- Betting-tip framing.
- Complex scoring calculations not needed for narration.

### May be modified by Scriptwriter

- Spoken wording.
- Hook phrasing.
- Evidence phrasing.
- Closing engagement question.

### Scriptwriter is not allowed to change

- selected_match
- central_question unless approved
- dashboard probabilities
- evidence facts
- uncertainty level

### Becomes locked

- insight_dashboard
- uncertainty_level
- evidence_points

Dashboard can only change if:

- Scriptwriter cannot explain it naturally.
- QC flags it as misleading.
- Insight Scoring Agent creates v2.

---

## IF-A05 Scriptwriter -> IF-A06 Storyboard Agent

### Information transferred

- final_voiceover_script
- estimated_duration_seconds
- word_count
- hook
- central_question
- closing_engagement_question
- insight_dashboard
- evidence_points

### Must never be transferred

- Permission to rewrite the story.
- Permission to add new evidence.
- Permission to extend beyond 60 seconds.

### May be modified by Storyboard Agent

- Scene breaks.
- On-screen text.
- Caption compression.
- Visual descriptions.
- Asset needs.

### Storyboard Agent is not allowed to change

- final_voiceover_script
- central_question
- evidence facts
- dashboard values

### Becomes locked

- final_voiceover_script
- word_count
- estimated_duration_seconds

Script can only change if:

- Storyboard Agent cannot fit it into 60 seconds.
- QC flags tone, length, or clarity.
- Scriptwriter creates v2.

---

## IF-A06 Storyboard Agent -> IF-A07 Visual Director

### Information transferred

- storyboard scenes
- timestamps
- voiceover lines
- on_screen_text
- caption_text
- animation_instruction
- asset_needed
- dashboard data

### Must never be transferred

- New claims not in the script.
- Asset assumptions without rights status.
- New script lines.

### May be modified by Visual Director

- Layout instructions.
- Camera movement.
- Typography rules.
- Caption placement.
- Dashboard design.
- Animation rules.
- Render instructions.

### Visual Director is not allowed to change

- scene meaning
- voiceover lines
- facts
- central question
- dashboard values

### Becomes locked

- scene order
- scene timestamps
- caption meaning

Storyboard can only change if:

- Visual Director cannot render the scene safely.
- Assets are unavailable.
- QC flags visual clutter.
- Storyboard Agent creates v2.

---

## IF-A07 Visual Director -> IF-A08 Quality Control Agent

### Information transferred

- complete visual direction
- storyboard
- final script
- evidence
- dashboard
- asset list
- render instructions
- human_review_flags

### Must never be transferred

- Unlicensed asset approval.
- Unsupported factual claims.
- Approval pressure.

### May be modified by Quality Control Agent

- Approval status.
- Required fixes.
- Final recommendation.
- Return destination.

### Quality Control Agent is not allowed to change directly

- Script.
- Story angle.
- Evidence points.
- Dashboard values.
- Visual instructions.

QC can only request changes from responsible agents.

### Becomes locked

If passed:

- production package v1
- approved script
- approved storyboard
- approved visual direction
- approved QC result

If failed:

- failed reasons
- required fixes
- return agent

---

## IF-A08 Quality Control Agent -> Previous Agent

QC may send work back to any prior agent.

### Return to Match Selector when

- Match is weak.
- No compelling story exists.
- Audience interest is too low.

### Return to Story Hunter when

- Story is unclear.
- Central question is weak.
- Surprising fact is weak.

### Return to Evidence Filter when

- Evidence does not support story.
- Too many stats.
- Weak data is not flagged.

### Return to Insight Scoring Agent when

- Dashboard is misleading.
- Probabilities do not total 100.
- Scores feel like betting advice.

### Return to Scriptwriter when

- Script is robotic.
- Script is too long.
- Script sounds technical.
- Ending does not invite engagement.

### Return to Storyboard Agent when

- Visuals do not change every 3 to 5 seconds.
- Captions are too long.
- Scenes do not support script.

### Return to Visual Director when

- Layout is cluttered.
- Asset rights are unclear.
- Render instructions are incomplete.

---

## 10. Locked Field Standard

Locked fields are decisions that downstream agents must preserve.

| Field | Locked By | Can Be Changed By |
|---|---|---|
| production_id | Production setup | Human producer only |
| selected_match | Match Selector | Match Selector v2 or human producer |
| competition | Match Selector | Match Selector v2 or human producer |
| kickoff_time | Match Selector | Match Selector v2 or human producer |
| main_story_angle | Story Hunter | Story Hunter v2 after evidence/QC rejection |
| central_question | Story Hunter | Story Hunter v2 or human producer |
| surprising_fact | Story Hunter | Story Hunter v2 after evidence/QC rejection |
| evidence_points | Evidence Filter | Evidence Filter v2 |
| insight_dashboard | Insight Scoring Agent | Insight Scoring Agent v2 |
| final_voiceover_script | Scriptwriter | Scriptwriter v2 |
| storyboard | Storyboard Agent | Storyboard Agent v2 |
| visual_direction | Visual Director | Visual Director v2 |
| quality_control_result | Quality Control Agent | Quality Control Agent v2 after revision |

---

## 11. Human Review Flags

Every agent must output `human_review_flags`, even if empty.

### Standard flags

```text
FACT_CHECK_REQUIRED
LOW_CONFIDENCE
WEAK_STORY
WEAK_EVIDENCE
BETTING_TONE_RISK
LEGAL_ASSET_RISK
SCRIPT_TOO_TECHNICAL
VISUAL_CLUTTER_RISK
PUBLISHING_RISK
HUMAN_EDITOR_DECISION
```

### Human review is mandatory when

- Confidence is below 70.
- Any legal asset issue exists.
- Any unverified injury or suspension is central to the story.
- Betting odds are the main support for the story.
- QC fails twice.
- The same agent reaches v3.

---

## 12. Recovery Strategies

### Missing required input

Action:

- Stop.
- Set approval_status to `blocked`.
- Return required fields.

### Low confidence

Action:

- If 60-69, return to previous agent with warning.
- If below 60, reject and request human review.

### Weak story

Action:

- Story Hunter creates up to three alternatives.
- Human producer chooses.
- If no angle works, return to Match Selector.

### Weak evidence

Action:

- Evidence Filter requests more data.
- Story Hunter revises story if needed.
- Human producer approves if evidence is acceptable but not strong.

### Script failure

Action:

- Scriptwriter creates v2.
- If v2 fails for tone, human editor reviews.
- If v3 fails, block production.

### Legal asset risk

Action:

- Visual Director replaces asset.
- QC must not pass until risk is resolved.

---

## 13. Complete Communication Flow Example: Liverpool vs Arsenal

This is illustrative sample data only.

### IF-A01 Match Selector output

```json
{
  "agent_id": "IF-A01",
  "agent_name": "Match Selector",
  "production_id": "if-2026-07-06-liverpool-arsenal",
  "output_version": "v1",
  "confidence": {
    "score": 94,
    "reason": "High audience interest, strong competition relevance, and enough data for a clear story."
  },
  "warnings": [],
  "errors": [],
  "next_agent": "IF-A02",
  "approval_status": "approved",
  "payload": {
    "selected_match": {
      "home_team": "Liverpool",
      "away_team": "Arsenal",
      "competition": "Premier League",
      "kickoff_time": "20:00",
      "country": "England"
    },
    "selected_reason": "This match has major audience interest and a strong pre-kickoff story potential.",
    "selection_score": 94,
    "runner_up_matches": [],
    "data_gaps": []
  }
}
```

Locked after this step:

- Liverpool vs Arsenal.
- Premier League.
- 20:00 kickoff.
- Production ID.

### IF-A02 Story Hunter output

```json
{
  "agent_id": "IF-A02",
  "agent_name": "Story Hunter",
  "production_id": "if-2026-07-06-liverpool-arsenal",
  "output_version": "v1",
  "confidence": {
    "score": 86,
    "reason": "The early-pressure angle is simple, fan-relevant, and supported by sample form notes."
  },
  "warnings": ["Sample data must be verified before publishing."],
  "errors": [],
  "next_agent": "IF-A03",
  "approval_status": "approved",
  "payload": {
    "main_story_angle": "Liverpool may have the edge if they turn the first 20 minutes into chaos, but Arsenal have enough quality to punish one mistake.",
    "central_question": "Can Arsenal survive Liverpool's fast start?",
    "surprising_fact": "Sample data: Liverpool have scored first in most recent home matches, while Arsenal have often needed longer to settle away.",
    "why_this_angle_matters": "The first 20 minutes could shape the whole match.",
    "why_fans_should_care": "Both fanbases will argue about whether Arsenal can handle the pressure."
  }
}
```

Locked after this step:

- Main story angle.
- Central question.
- Surprising fact.

### IF-A03 Evidence Filter output

```json
{
  "agent_id": "IF-A03",
  "agent_name": "Evidence Filter",
  "production_id": "if-2026-07-06-liverpool-arsenal",
  "output_version": "v1",
  "confidence": {
    "score": 78,
    "reason": "Evidence supports the angle, but sample data needs verification."
  },
  "warnings": ["FACT_CHECK_REQUIRED"],
  "errors": [],
  "next_agent": "IF-A04",
  "approval_status": "approved",
  "payload": {
    "evidence_points": [
      {
        "point": "Liverpool have started recent home games quickly.",
        "why_it_matters": "It supports the idea that Arsenal's first job is surviving early pressure.",
        "confidence": "medium"
      },
      {
        "point": "Arsenal have sometimes needed longer to settle away.",
        "why_it_matters": "It makes the opening phase important.",
        "confidence": "medium"
      },
      {
        "point": "Arsenal still create enough chances to change the game.",
        "why_it_matters": "It keeps the story balanced.",
        "confidence": "medium"
      }
    ],
    "evidence_strength_rating": 7,
    "weak_data_warnings": ["Verify all sample claims before publishing."],
    "recommended_visual_evidence": ["first 20 minutes timer", "pressure arrows", "probability bars"]
  }
}
```

Locked after this step:

- Evidence points.
- Evidence strength rating.

### IF-A04 Insight Scoring Agent output

```json
{
  "agent_id": "IF-A04",
  "agent_name": "Insight Scoring Agent",
  "production_id": "if-2026-07-06-liverpool-arsenal",
  "output_version": "v1",
  "confidence": {
    "score": 80,
    "reason": "Dashboard gives a small edge while preserving uncertainty."
  },
  "warnings": ["Do not present probabilities as guarantees."],
  "errors": [],
  "next_agent": "IF-A05",
  "approval_status": "approved",
  "payload": {
    "home_win_probability": 43,
    "draw_probability": 27,
    "away_win_probability": 30,
    "form_summary": "Liverpool edge the recent home form, Arsenal remain dangerous away.",
    "tactical_advantage": "Liverpool's early pressure against Arsenal's slower away starts.",
    "uncertainty_level": "medium",
    "x_factor": "Arsenal's first pass through midfield under pressure.",
    "surprising_detail": "The first 20 minutes may matter more than the final scoreline suggests.",
    "plain_english_summary": "Everything points to Liverpool having the early edge, but Arsenal have enough quality to turn one loose moment into a goal."
  }
}
```

Locked after this step:

- Dashboard.
- Probabilities.
- Uncertainty level.

### IF-A05 Scriptwriter output

```json
{
  "agent_id": "IF-A05",
  "agent_name": "Scriptwriter",
  "production_id": "if-2026-07-06-liverpool-arsenal",
  "output_version": "v1",
  "confidence": {
    "score": 88,
    "reason": "Script is short, conversational, and keeps the story clear."
  },
  "warnings": [],
  "errors": [],
  "next_agent": "IF-A06",
  "approval_status": "approved",
  "payload": {
    "final_voiceover_script": "Before the first whistle... here's the insight. Liverpool's biggest weapon in this one might not be a player. It might be the first 20 minutes. Sample data shows they have been starting fast at home, while Arsenal have sometimes needed time to settle away. So the question is simple: can Arsenal survive Liverpool's fast start? If they do, this game could open up for them. But if Liverpool win the early pressure, the edge goes to the home side. The dashboard gives Liverpool a small edge, not a guarantee, because football can still surprise us. Do you agree, or are we missing something? Tell us below.",
    "estimated_duration_seconds": 52,
    "word_count": 107,
    "hook": "Liverpool's biggest weapon in this one might not be a player.",
    "central_question": "Can Arsenal survive Liverpool's fast start?",
    "closing_engagement_question": "Do you agree, or are we missing something?",
    "compliance_warning": ""
  }
}
```

Locked after this step:

- Final script.
- Word count.
- Estimated duration.

### IF-A06 Storyboard Agent output

```json
{
  "agent_id": "IF-A06",
  "agent_name": "Storyboard Agent",
  "production_id": "if-2026-07-06-liverpool-arsenal",
  "output_version": "v1",
  "confidence": {
    "score": 84,
    "reason": "Scenes change frequently and support the script."
  },
  "warnings": [],
  "errors": [],
  "next_agent": "IF-A07",
  "approval_status": "approved",
  "payload": {
    "scene_count": 8,
    "duration_seconds": 60,
    "visual_change_interval": "3-5 seconds",
    "storyboard_summary": "Opening, surprising fact, central question, evidence, dashboard, CTA."
  }
}
```

Locked after this step:

- Scene order.
- Scene timing.
- Caption meaning.

### IF-A07 Visual Director output

```json
{
  "agent_id": "IF-A07",
  "agent_name": "Visual Director",
  "production_id": "if-2026-07-06-liverpool-arsenal",
  "output_version": "v1",
  "confidence": {
    "score": 82,
    "reason": "Template-based visuals are feasible if licensed crests and graphics are available."
  },
  "warnings": ["LEGAL_ASSET_RISK: verify logo and image rights."],
  "errors": [],
  "next_agent": "IF-A08",
  "approval_status": "human_review_required",
  "payload": {
    "layout": "Vertical 9:16 football intelligence dashboard.",
    "caption_placement": "Lower third safe zone.",
    "dashboard_design": "Simple probability bars, form card, tactical advantage card.",
    "asset_list": ["team crests", "pitch background", "timer icon", "arrows", "comment icon"],
    "render_instructions": ["Export MP4 H.264", "1080x1920", "30 fps", "60 seconds maximum"]
  }
}
```

Locked after this step:

- Visual direction, once asset rights are cleared.

### IF-A08 Quality Control output

```json
{
  "agent_id": "IF-A08",
  "agent_name": "Quality Control Agent",
  "production_id": "if-2026-07-06-liverpool-arsenal",
  "output_version": "v1",
  "confidence": {
    "score": 87,
    "reason": "Story, script, duration, and structure are strong, pending data and asset verification."
  },
  "warnings": ["FACT_CHECK_REQUIRED", "LEGAL_ASSET_RISK"],
  "errors": [],
  "next_agent": "human_producer",
  "approval_status": "human_review_required",
  "payload": {
    "pass_or_fail": "pass",
    "reason": "Approved creatively, but human review is required for sample data and asset rights.",
    "issues_found": ["Sample data must be verified.", "Logo and image rights must be confirmed."],
    "required_fixes": ["Replace sample data with verified data.", "Confirm asset rights before rendering."],
    "retention_score": 8.5,
    "clarity_score": 9,
    "story_score": 8.5,
    "evidence_score": 7.5,
    "final_recommendation": "Proceed after fact-check and asset clearance."
  }
}
```

---

## 14. Communication Diagram

```text
INSIGHT FOOTBALL NEWSROOM FLOW

Daily Input File
    |
    v
IF-A01 Match Selector
    | selected match locked
    v
IF-A02 Story Hunter
    | story angle + central question + surprising fact locked
    v
IF-A03 Evidence Filter
    | evidence points locked
    v
IF-A04 Insight Scoring Agent
    | dashboard locked
    v
IF-A05 Scriptwriter
    | final script locked
    v
IF-A06 Storyboard Agent
    | scene plan locked
    v
IF-A07 Visual Director
    | render instructions locked after asset review
    v
IF-A08 Quality Control Agent
    |
    +-- pass --> Human Producer Review --> Render --> Publish
    |
    +-- fail: weak match ---------> IF-A01 Match Selector
    |
    +-- fail: weak story ---------> IF-A02 Story Hunter
    |
    +-- fail: weak evidence ------> IF-A03 Evidence Filter
    |
    +-- fail: bad dashboard ------> IF-A04 Insight Scoring Agent
    |
    +-- fail: weak script --------> IF-A05 Scriptwriter
    |
    +-- fail: poor scenes --------> IF-A06 Storyboard Agent
    |
    +-- fail: visual issue -------> IF-A07 Visual Director
```

---

## 15. Official IF-ACP Rule

No agent owns the whole video.

Each agent owns one newsroom decision:

- Match Selector owns the match.
- Story Hunter owns the story.
- Evidence Filter owns the proof.
- Insight Scoring Agent owns the dashboard.
- Scriptwriter owns the voice.
- Storyboard Agent owns the sequence.
- Visual Director owns the visual execution.
- Quality Control owns approval.

Final standard:

```text
Every agent may improve its own layer.
No agent may quietly rewrite another agent's locked decision.
```

