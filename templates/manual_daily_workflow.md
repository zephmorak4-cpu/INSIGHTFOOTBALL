# INSIGHT FOOTBALL Manual Daily Workflow v1.0

Use this workflow to produce one daily 60-second match preview before full automation is built.

The purpose of this phase is simple:

```text
Prove the daily production format before automating everything.
```

## Daily Output

Each production run should create one completed JSON package in:

```text
daily_packages/
```

Recommended filename format:

```text
YYYY-MM-DD_home-team_away-team.json
```

Example:

```text
2026-07-06_liverpool_arsenal.json
```

## Files Used

Start here:

```text
templates/daily_input.md
```

Use `templates/daily_input_template.json` only when an automation tool needs JSON input.

Prompts:

```text
prompts/match_selector.txt
prompts/story_hunter.txt
prompts/evidence_filter.txt
prompts/insight_scoring_agent.txt
prompts/scriptwriter.txt
prompts/storyboard_agent.txt
prompts/visual_director.txt
prompts/quality_control_agent.txt
```

Validation target:

```text
schemas/InsightFootballProductionPackage.schema.json
```

Sample reference:

```text
daily_packages/sample_liverpool_arsenal.json
```

## Step 1: Fill the Daily Input Template

Copy:

```text
templates/daily_input.md
```

Save the copy as:

```text
daily_packages/YYYY-MM-DD_home-team_away-team_daily_input.md
```

Fill in:

- Date.
- Fixtures.
- Competition.
- Kickoff time.
- Team popularity score.
- Match importance score.
- Rivalry level.
- Available data score.
- Expected audience interest.

Then add context for likely selected matches:

- Recent form.
- Injuries.
- Head-to-head.
- Home and away performance.
- Odds if available.
- Recent news.
- Team style notes.
- Raw statistics.
- Goals scored and conceded.
- xG if available.

Do not worry about perfect data in the MVP. Use enough verified information to support a simple story.

## Step 2: Run Agent 1, Match Selector

Open:

```text
prompts/match_selector.txt
```

Replace:

```text
{{date}}
{{fixtures_json}}
```

With data from the daily input file.

Expected output:

```json
{
  "selected_match": {},
  "selected_reason": "",
  "selection_score": 0,
  "runner_up_matches": [],
  "data_gaps": []
}
```

Human review:

- Is the match interesting enough for fans?
- Is there enough data to tell a story?
- Is the match relevant to your audience?

If the answer is no, manually choose another match and continue.

## Step 3: Run Agent 2, Story Hunter

Open:

```text
prompts/story_hunter.txt
```

Replace the variables with:

- selected_match from Agent 1.
- team_form.
- injuries.
- head_to_head.
- home_away_performance.
- odds.
- recent_news.
- team_style_notes.

Expected output:

```json
{
  "main_story_angle": "",
  "surprising_fact": "",
  "central_question": "",
  "why_this_angle_matters": "",
  "why_fans_should_care": "",
  "rejected_angles": [],
  "data_warnings": []
}
```

Human review:

- Is there one clear story?
- Is the surprising fact actually interesting?
- Would football fans argue about the central question?
- Does it avoid sounding like betting advice?

If the story feels weak, ask the agent for 3 alternative story angles, then choose one manually.

## Step 4: Run Agent 3, Evidence Filter

Open:

```text
prompts/evidence_filter.txt
```

Replace the variables with:

- main_story_angle from Agent 2.
- raw_statistics.
- team_form.
- head_to_head.
- injuries.
- odds.
- xg.
- goals_scored_conceded.
- home_away_data.

Expected output:

```json
{
  "evidence_points": [],
  "evidence_strength_rating": 0,
  "weak_data_warnings": [],
  "recommended_visual_evidence": []
}
```

Human review:

- Keep only 3 to 5 evidence points.
- Remove any stat that does not support the story.
- Mark weak data clearly.
- Do not publish sample or unverified data as fact.

## Step 5: Run Agent 4, Insight Scoring Agent

Open:

```text
prompts/insight_scoring_agent.txt
```

Replace the variables with:

- selected_match.
- evidence_points from Agent 3.
- team_form.
- home_away_data.
- injuries.
- odds.
- model_notes if needed.

Expected output:

```json
{
  "home_win_probability": 0,
  "draw_probability": 0,
  "away_win_probability": 0,
  "form_summary": "",
  "tactical_advantage": "",
  "uncertainty_level": "medium",
  "x_factor": "",
  "surprising_detail": "",
  "plain_english_summary": ""
}
```

Human review:

- Probabilities must total 100.
- Scores must feel explainable.
- The dashboard must support the story, not replace it.
- Remove fake precision.

## Step 6: Run Agent 5, Scriptwriter

Open:

```text
prompts/scriptwriter.txt
```

Replace the variables with:

- selected_match.
- main_story_angle.
- central_question.
- evidence_points.
- insight_dashboard.
- brand_tone_rules.

Expected output:

```json
{
  "final_voiceover_script": "",
  "estimated_duration_seconds": 0,
  "word_count": 0,
  "hook": "",
  "central_question": "",
  "closing_engagement_question": "",
  "compliance_warning": ""
}
```

Human review:

- Read the script out loud.
- If it sounds like a formal analyst, rewrite it.
- If it sounds like betting tips, rewrite it.
- If the opening is weak, rewrite it.
- If the script is over 150 words, shorten it.
- If it does not invite debate at the end, fix it.

Target:

```text
95 to 130 words
45 to 58 seconds
```

## Step 7: Run Agent 6, Storyboard Agent

Open:

```text
prompts/storyboard_agent.txt
```

Replace the variables with:

- final_script.
- dashboard_data.
- brand_visual_rules.

Expected output:

```json
{
  "scenes": []
}
```

Human review:

- Does every scene support the story?
- Do visuals change every 3 to 5 seconds?
- Are captions short?
- Is the total duration 60 seconds or less?

## Step 8: Run Agent 7, Visual Director

Open:

```text
prompts/visual_director.txt
```

Replace the variables with:

- storyboard.
- available_assets.
- team_names.
- team_logos.
- brand_colors.
- dashboard_data.

Expected output:

```json
{
  "layout_instructions": [],
  "camera_movement": [],
  "typography_rules": [],
  "caption_placement": "",
  "dashboard_design": [],
  "animation_rules": [],
  "asset_list": [],
  "render_instructions": []
}
```

Human review:

- Are all assets available?
- Are logos clear?
- Are player images legally safe?
- Is there any copyrighted broadcast footage? Remove it unless licensed.
- Can the video be rendered using a template?

## Step 9: Run Agent 8, Quality Control Agent

Open:

```text
prompts/quality_control_agent.txt
```

Replace the variables with:

- script.
- storyboard.
- evidence.
- dashboard.
- brand_rules.

Expected output:

```json
{
  "pass_or_fail": "pass",
  "reason": "",
  "issues_found": [],
  "required_fixes": [],
  "retention_score": 0,
  "clarity_score": 0,
  "story_score": 0,
  "evidence_score": 0,
  "final_recommendation": ""
}
```

Human review:

- If QC fails, fix the listed issues before rendering.
- Do not override QC if the issue is betting certainty, weak story, no central question, or duration above 60 seconds.

Minimum approval scores:

```text
retention_score: 7+
clarity_score: 8+
story_score: 7+
evidence_score: 7+
```

## Step 10: Assemble the Production Package

Create a final JSON file in:

```text
daily_packages/
```

Use this filename format:

```text
YYYY-MM-DD_home-team_away-team.json
```

The final package must match:

```text
schemas/InsightFootballProductionPackage.schema.json
```

Required top-level fields:

- package_id
- date
- match
- competition
- selected_reason
- story_angle
- surprising_fact
- central_question
- evidence_points
- insight_dashboard
- final_script
- storyboard
- visual_direction
- captions
- publishing_metadata
- quality_control
- status

Set status to:

```text
approved
```

Only when QC passes and human review is complete.

## Step 11: Prepare for Render

Before rendering, confirm:

- Voiceover is final.
- Captions are short.
- Visual scenes are clear.
- Assets are available.
- Brand colors are set.
- Logos are available.
- No illegal footage is used.
- Total duration is 60 seconds or less.

## Step 12: Prepare Publishing Metadata

Create platform-specific metadata:

YouTube Shorts:

- Short title.
- Main question in title or first line.
- 3 to 5 hashtags.

Facebook Reels:

- Conversational caption.
- Invite comments.
- Avoid too many hashtags.

Telegram:

- Short caption.
- Match name.
- Central question.
- Link to video if published elsewhere.

## Daily Human Checklist

Approve the package only if:

- The match is clear.
- The opening is strong.
- The story has one clear question.
- The surprising fact is interesting.
- The script sounds natural.
- The evidence supports the story.
- The video does not sound like gambling advice.
- The ending invites debate.
- The visuals can be made with templates.
- The package is 60 seconds or less.

## MVP Rule

Do not chase full automation until this manual workflow produces 10 strong daily packages.

For the first 10 videos, focus on:

- Hook strength.
- Story clarity.
- Script tone.
- Comments from viewers.
- Completion rate.

After 10 videos, automate the most repetitive parts first.
