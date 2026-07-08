# INSIGHT FOOTBALL Production Blueprint v1.0

## 1. Project Overview

### What INSIGHT FOOTBALL is

INSIGHT FOOTBALL is a football intelligence media system that produces one short, evidence-supported match preview every day.

The brand does not try to predict football like a betting page. It finds the most interesting story before kickoff, explains it in simple language, backs it with a few useful facts, and invites fans to decide whether they agree.

Brand promise:

> Before the first whistle... here's the insight.

Core philosophy:

> INSIGHT FOOTBALL does not create football predictions. INSIGHT FOOTBALL discovers the most interesting football story before kickoff, explains it in simple language, supports it with evidence, and lets the audience decide whether they agree.

Tone rule:

> Never sound like an analyst. Sound like a friend who happens to know football really well.

Golden rule:

> If a 16-year-old football fan would not naturally say it in a conversation, do not let the AI say it.

### What INSIGHT FOOTBALL is not

INSIGHT FOOTBALL is not:

- A betting tips channel.
- A football news repost page.
- A generic highlights page.
- A tactical lecture.
- A prediction machine.
- A channel that promises guaranteed results.
- A system built around expensive AI video generation as the main method.
- A NotebookLM workflow.

### MVP definition

The MVP produces:

- One match preview per day.
- 60 seconds maximum.
- Faceless video.
- Data-supported storytelling.
- Simple spoken language.
- Template-based vertical video.
- Output for YouTube Shorts, Facebook Reels, and Telegram.
- A complete production package containing script, scenes, visuals, captions, metadata, and quality control.

The MVP should use manual or semi-manual data input first. Automation should be added only after the story format works.

---

## 2. Core Content Formula

### Exact 60-second structure

| Time | Segment | Purpose |
|---|---|---|
| 0-3 seconds | Brand opening | Establish the brand and promise. |
| 3-10 seconds | Surprising fact or hidden match angle | Stop the scroll with a real reason to care. |
| 10-18 seconds | Central question | Give the viewer a simple problem to follow. |
| 18-42 seconds | Story explanation | Explain the match angle in normal football language. |
| 42-55 seconds | Evidence and dashboard visuals | Show the proof without turning the video into a stats lecture. |
| 55-60 seconds | Answer and debate invitation | Give a soft conclusion and invite comments. |

### Required opening

Voiceover:

```text
Before the first whistle... here's the insight.
```

### Segment rules

0-3 seconds:

- Always use the brand opening.
- Keep the visual sharp and quick.
- Show INSIGHT FOOTBALL branding and the match fixture.

3-10 seconds:

- Reveal one surprising fact directly.
- Do not call it "wild card" in narration.
- Avoid slow setup.

10-18 seconds:

- Ask one central question.
- The question should be easy for fans to argue about.

18-42 seconds:

- Tell one story.
- Use simple football language.
- Avoid trying to explain every possible angle.

42-55 seconds:

- Show evidence and dashboard visuals.
- Visual labels can be branded.
- Voiceover should explain the meaning naturally.

55-60 seconds:

- Give a careful, non-guaranteed answer.
- Invite debate.

Example ending:

```text
Do you agree, or are we missing something? Tell us below.
```

### Why this structure works for retention

The first 3 seconds create brand memory. The next 7 seconds create curiosity. The central question gives viewers a reason to stay because they want the answer. The middle section keeps attention by telling one clear story, not dumping information. The dashboard appears late enough to support the story instead of overwhelming the viewer. The final question converts passive viewing into comments.

---

## 3. AI Agent System

### Agent table

| Agent | Purpose | Primary output | JSON required |
|---|---|---|---|
| Match Selector | Choose the best match to cover today. | Selected match and reason. | Yes |
| Story Hunter | Find the strongest pre-kickoff story angle. | Story angle, surprising fact, central question. | Yes |
| Evidence Filter | Keep only the facts that support the story. | 3 to 5 evidence points and warnings. | Yes |
| Insight Scoring Agent | Create a simple visual dashboard. | Probabilities, form, edge, uncertainty, X-factor. | Yes |
| Scriptwriter | Write the final 60-second voiceover. | Script, duration, hook, question, CTA. | Yes |
| Storyboard Agent | Turn the script into scenes. | Timestamped scene plan. | Yes |
| Visual Director | Turn scenes into template instructions. | Layout, motion, assets, render rules. | Yes |
| Quality Control Agent | Decide whether the package is publishable. | Pass/fail with scores and fixes. | Yes |

---

## 4. Input and Output Format for Each Agent

### Shared validation principles

Every agent must:

- Return valid JSON only.
- Include every required field.
- Use plain English.
- Avoid betting certainty.
- Preserve the selected match context.
- Flag weak data instead of pretending it is strong.

Every agent fails if:

- Required fields are missing.
- The output is not valid JSON.
- It invents hard facts without a sample or uncertainty label.
- It produces content that sounds like guaranteed betting advice.

### Agent 1: Match Selector

Role:

Choose the best match to cover for the day.

Objective:

Select one match with the strongest mix of audience interest, importance, story potential, and data availability.

Input schema:

```json
{
  "type": "object",
  "required": ["date", "fixtures"],
  "properties": {
    "date": { "type": "string", "format": "date" },
    "fixtures": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["home_team", "away_team", "competition", "kickoff_time"],
        "properties": {
          "home_team": { "type": "string" },
          "away_team": { "type": "string" },
          "competition": { "type": "string" },
          "kickoff_time": { "type": "string" },
          "team_popularity": { "type": "number", "minimum": 0, "maximum": 10 },
          "match_importance": { "type": "number", "minimum": 0, "maximum": 10 },
          "rivalry_level": { "type": "number", "minimum": 0, "maximum": 10 },
          "available_data_score": { "type": "number", "minimum": 0, "maximum": 10 },
          "expected_audience_interest": { "type": "number", "minimum": 0, "maximum": 10 }
        }
      }
    }
  }
}
```

Output schema:

```json
{
  "type": "object",
  "required": ["selected_match", "selected_reason", "selection_score", "runner_up_matches"],
  "properties": {
    "selected_match": {
      "type": "object",
      "required": ["home_team", "away_team", "competition", "kickoff_time"],
      "properties": {
        "home_team": { "type": "string" },
        "away_team": { "type": "string" },
        "competition": { "type": "string" },
        "kickoff_time": { "type": "string" }
      }
    },
    "selected_reason": { "type": "string" },
    "selection_score": { "type": "number", "minimum": 0, "maximum": 100 },
    "runner_up_matches": { "type": "array" },
    "data_gaps": { "type": "array", "items": { "type": "string" } }
  }
}
```

Required fields:

- selected_match
- selected_reason
- selection_score
- runner_up_matches

Optional fields:

- data_gaps

Validation rules:

- Select exactly one match.
- Give a specific reason.
- Do not select a match only because it is popular if story data is weak.

Example input:

```json
{
  "date": "2026-07-06",
  "fixtures": [
    {
      "home_team": "Liverpool",
      "away_team": "Arsenal",
      "competition": "Premier League",
      "kickoff_time": "20:00",
      "team_popularity": 10,
      "match_importance": 9,
      "rivalry_level": 8,
      "available_data_score": 9,
      "expected_audience_interest": 10
    }
  ]
}
```

Example output:

```json
{
  "selected_match": {
    "home_team": "Liverpool",
    "away_team": "Arsenal",
    "competition": "Premier League",
    "kickoff_time": "20:00"
  },
  "selected_reason": "This match has major audience interest, strong table relevance, and enough recent form data to build a clear pre-kickoff story.",
  "selection_score": 94,
  "runner_up_matches": [],
  "data_gaps": []
}
```

### Agent 2: Story Hunter

Role:

Find the most interesting story before kickoff.

Objective:

Discover the strongest story angle. Do not write the script.

Input schema:

```json
{
  "type": "object",
  "required": ["selected_match"],
  "properties": {
    "selected_match": { "type": "object" },
    "team_form": { "type": "object" },
    "injuries": { "type": "array" },
    "head_to_head": { "type": "object" },
    "home_away_performance": { "type": "object" },
    "odds": { "type": "object" },
    "recent_news": { "type": "array" },
    "team_style_notes": { "type": "object" }
  }
}
```

Output schema:

```json
{
  "type": "object",
  "required": ["main_story_angle", "surprising_fact", "central_question", "why_this_angle_matters", "why_fans_should_care"],
  "properties": {
    "main_story_angle": { "type": "string" },
    "surprising_fact": { "type": "string" },
    "central_question": { "type": "string" },
    "why_this_angle_matters": { "type": "string" },
    "why_fans_should_care": { "type": "string" },
    "rejected_angles": { "type": "array", "items": { "type": "string" } },
    "data_warnings": { "type": "array", "items": { "type": "string" } }
  }
}
```

Validation rules:

- Must produce one main story angle only.
- Central question must be conversational.
- Must not write the final script.

Failure conditions:

- Produces multiple competing main angles.
- Uses technical phrasing as the main question.
- Makes unsupported claims.

Example output:

```json
{
  "main_story_angle": "Liverpool may have the edge because they are starting games faster, but Arsenal have the quality to punish one loose spell.",
  "surprising_fact": "Liverpool have scored first in most of their recent home matches, while Arsenal have needed longer to settle away from home.",
  "central_question": "Can Arsenal survive Liverpool's fast start?",
  "why_this_angle_matters": "The first 20 minutes could shape the whole match.",
  "why_fans_should_care": "Both fanbases will have strong opinions about whether Arsenal can handle the pressure.",
  "rejected_angles": ["Generic title race angle", "Basic head-to-head angle"],
  "data_warnings": ["Use verified recent match data before publishing."]
}
```

### Agent 3: Evidence Filter

Role:

Collect only the facts needed to support the story.

Objective:

Reduce raw data to 3 to 5 evidence points that make the story easier to believe.

Input schema:

```json
{
  "type": "object",
  "required": ["main_story_angle", "raw_statistics"],
  "properties": {
    "main_story_angle": { "type": "string" },
    "raw_statistics": { "type": "object" },
    "team_form": { "type": "object" },
    "head_to_head": { "type": "object" },
    "injuries": { "type": "array" },
    "odds": { "type": "object" },
    "xg": { "type": "object" },
    "goals_scored_conceded": { "type": "object" },
    "home_away_data": { "type": "object" }
  }
}
```

Output schema:

```json
{
  "type": "object",
  "required": ["evidence_points", "evidence_strength_rating", "weak_data_warnings", "recommended_visual_evidence"],
  "properties": {
    "evidence_points": {
      "type": "array",
      "minItems": 3,
      "maxItems": 5,
      "items": {
        "type": "object",
        "required": ["point", "why_it_matters", "source_type", "confidence"],
        "properties": {
          "point": { "type": "string" },
          "why_it_matters": { "type": "string" },
          "source_type": { "type": "string" },
          "confidence": { "type": "string", "enum": ["low", "medium", "high"] }
        }
      }
    },
    "evidence_strength_rating": { "type": "number", "minimum": 0, "maximum": 10 },
    "weak_data_warnings": { "type": "array", "items": { "type": "string" } },
    "recommended_visual_evidence": { "type": "array", "items": { "type": "string" } }
  }
}
```

Validation rules:

- Return 3 to 5 evidence points.
- Remove irrelevant statistics.
- Each evidence point must explain why it matters.

Failure conditions:

- More than 5 evidence points.
- Raw numbers with no explanation.
- Evidence does not support the story angle.

### Agent 4: Insight Scoring Agent

Role:

Generate the simplified match dashboard.

Objective:

Create a consistent, explainable dashboard for visuals. The dashboard supports the story; it is not the story.

Input schema:

```json
{
  "type": "object",
  "required": ["selected_match", "evidence_points"],
  "properties": {
    "selected_match": { "type": "object" },
    "evidence_points": { "type": "array" },
    "team_form": { "type": "object" },
    "home_away_data": { "type": "object" },
    "injuries": { "type": "array" },
    "odds": { "type": "object" },
    "model_notes": { "type": "string" }
  }
}
```

Output schema:

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
    "plain_english_summary"
  ],
  "properties": {
    "home_win_probability": { "type": "number", "minimum": 0, "maximum": 100 },
    "draw_probability": { "type": "number", "minimum": 0, "maximum": 100 },
    "away_win_probability": { "type": "number", "minimum": 0, "maximum": 100 },
    "form_summary": { "type": "string" },
    "tactical_advantage": { "type": "string" },
    "uncertainty_level": { "type": "string", "enum": ["low", "medium", "high"] },
    "x_factor": { "type": "string" },
    "surprising_detail": { "type": "string" },
    "plain_english_summary": { "type": "string" }
  }
}
```

Validation rules:

- Probabilities must total 100.
- Avoid fake precision. Use whole numbers.
- Explain the edge in plain English.

Failure conditions:

- Probabilities do not total 100.
- Output claims certainty.
- Dashboard is too technical for a casual viewer.

### Agent 5: Scriptwriter

Role:

Write the final 60-second voiceover.

Objective:

Turn the story angle, evidence, and dashboard into a short, conversational script.

Input schema:

```json
{
  "type": "object",
  "required": ["selected_match", "main_story_angle", "central_question", "evidence_points", "insight_dashboard", "brand_tone_rules"],
  "properties": {
    "selected_match": { "type": "object" },
    "main_story_angle": { "type": "string" },
    "central_question": { "type": "string" },
    "evidence_points": { "type": "array" },
    "insight_dashboard": { "type": "object" },
    "brand_tone_rules": { "type": "array", "items": { "type": "string" } }
  }
}
```

Output schema:

```json
{
  "type": "object",
  "required": ["final_voiceover_script", "estimated_duration_seconds", "word_count", "hook", "central_question", "closing_engagement_question", "compliance_warning"],
  "properties": {
    "final_voiceover_script": { "type": "string" },
    "estimated_duration_seconds": { "type": "number", "maximum": 60 },
    "word_count": { "type": "number", "maximum": 150 },
    "hook": { "type": "string" },
    "central_question": { "type": "string" },
    "closing_engagement_question": { "type": "string" },
    "compliance_warning": { "type": "string" }
  }
}
```

Validation rules:

- Under 150 words.
- Under 60 seconds.
- Must include the brand opening.
- Must include one central question.
- Must end with a debate invitation.

Failure conditions:

- Sounds like betting advice.
- Says "this will happen."
- Uses heavy jargon.
- Reads every metric mechanically.
- Says "today's Wild Card."

### Agent 6: Storyboard Agent

Role:

Convert the script into a scene-by-scene production plan.

Objective:

Create visuals that change every 3 to 5 seconds and support the story.

Input schema:

```json
{
  "type": "object",
  "required": ["final_script", "dashboard_data", "brand_visual_rules"],
  "properties": {
    "final_script": { "type": "string" },
    "dashboard_data": { "type": "object" },
    "brand_visual_rules": { "type": "object" }
  }
}
```

Output schema:

```json
{
  "type": "object",
  "required": ["scenes"],
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
        ],
        "properties": {
          "scene_number": { "type": "integer" },
          "timestamp_start": { "type": "number" },
          "timestamp_end": { "type": "number" },
          "voiceover_line": { "type": "string" },
          "visual_description": { "type": "string" },
          "on_screen_text": { "type": "string" },
          "animation_instruction": { "type": "string" },
          "asset_needed": { "type": "array", "items": { "type": "string" } },
          "caption_text": { "type": "string" }
        }
      }
    }
  }
}
```

Validation rules:

- Visuals change every 3 to 5 seconds.
- Total duration must be 60 seconds or less.
- Captions must be short.

Failure conditions:

- Scene longer than 5 seconds without visual change.
- On-screen text duplicates full voiceover.
- Scene does not support the story.

### Agent 7: Visual Director

Role:

Turn storyboard scenes into video template instructions.

Objective:

Create render-ready guidance for Creatomate, Shotstack, Remotion, Canva automation, or another template renderer.

Input schema:

```json
{
  "type": "object",
  "required": ["storyboard", "available_assets", "team_names", "brand_colors", "dashboard_data"],
  "properties": {
    "storyboard": { "type": "object" },
    "available_assets": { "type": "array" },
    "team_names": { "type": "array" },
    "team_logos": { "type": "array" },
    "brand_colors": { "type": "object" },
    "dashboard_data": { "type": "object" }
  }
}
```

Output schema:

```json
{
  "type": "object",
  "required": ["layout_instructions", "camera_movement", "typography_rules", "caption_placement", "dashboard_design", "animation_rules", "asset_list", "render_instructions"],
  "properties": {
    "layout_instructions": { "type": "array", "items": { "type": "string" } },
    "camera_movement": { "type": "array", "items": { "type": "string" } },
    "typography_rules": { "type": "array", "items": { "type": "string" } },
    "caption_placement": { "type": "string" },
    "dashboard_design": { "type": "array", "items": { "type": "string" } },
    "animation_rules": { "type": "array", "items": { "type": "string" } },
    "asset_list": { "type": "array", "items": { "type": "string" } },
    "render_instructions": { "type": "array", "items": { "type": "string" } }
  }
}
```

Validation rules:

- Must fit vertical 9:16.
- Must include captions.
- Must avoid copyrighted broadcast footage unless licensed.

Failure conditions:

- Too much screen clutter.
- No clear logo or match title.
- Visual plan needs assets that are not available or legally safe.

### Agent 8: Quality Control Agent

Role:

Check whether the production package is good enough to publish.

Objective:

Fail weak packages before rendering or publishing.

Input schema:

```json
{
  "type": "object",
  "required": ["script", "storyboard", "evidence", "dashboard", "brand_rules"],
  "properties": {
    "script": { "type": "object" },
    "storyboard": { "type": "object" },
    "evidence": { "type": "object" },
    "dashboard": { "type": "object" },
    "brand_rules": { "type": "array" }
  }
}
```

Output schema:

```json
{
  "type": "object",
  "required": ["pass_or_fail", "reason", "issues_found", "required_fixes", "retention_score", "clarity_score", "story_score", "evidence_score", "final_recommendation"],
  "properties": {
    "pass_or_fail": { "type": "string", "enum": ["pass", "fail"] },
    "reason": { "type": "string" },
    "issues_found": { "type": "array", "items": { "type": "string" } },
    "required_fixes": { "type": "array", "items": { "type": "string" } },
    "retention_score": { "type": "number", "minimum": 0, "maximum": 10 },
    "clarity_score": { "type": "number", "minimum": 0, "maximum": 10 },
    "story_score": { "type": "number", "minimum": 0, "maximum": 10 },
    "evidence_score": { "type": "number", "minimum": 0, "maximum": 10 },
    "final_recommendation": { "type": "string" }
  }
}
```

Must fail if:

- Opening is boring.
- Script sounds robotic.
- There is no clear central question.
- Surprising fact is weak.
- Script is too technical.
- Video is longer than 60 seconds.
- Content sounds like guaranteed betting advice.
- Too many statistics are mentioned without explanation.
- Ending does not invite engagement.

---

## 5. Prompt Templates for Each Agent

### Agent 1 prompt: Match Selector

```text
SYSTEM ROLE:
You are the Match Selector for INSIGHT FOOTBALL, a football intelligence media brand.

TASK:
Choose the single best match to cover today. Do not write a script. Select the match with the strongest mix of audience interest, match importance, story potential, and available data.

INPUT VARIABLES:
date: {{date}}
fixtures: {{fixtures_json}}

OUTPUT REQUIREMENTS:
Return valid JSON only with:
- selected_match
- selected_reason
- selection_score
- runner_up_matches
- data_gaps

TONE RULES:
Be practical, specific, and concise.

RESTRICTIONS:
Do not choose more than one match.
Do not select a match only because the teams are famous.
Do not invent unavailable data.
Do not mention betting tips.

JSON OUTPUT INSTRUCTION:
Return only valid JSON. No markdown. No explanation outside JSON.
```

### Agent 2 prompt: Story Hunter

```text
SYSTEM ROLE:
You are the Story Hunter for INSIGHT FOOTBALL.

TASK:
Find the strongest pre-kickoff story angle for the selected match. Do not write the script. Your job is to discover the most interesting story fans will care about before kickoff.

INPUT VARIABLES:
selected_match: {{selected_match_json}}
team_form: {{team_form_json}}
injuries: {{injuries_json}}
head_to_head: {{head_to_head_json}}
home_away_performance: {{home_away_json}}
odds: {{odds_json}}
recent_news: {{recent_news_json}}
team_style_notes: {{team_style_notes_json}}

OUTPUT REQUIREMENTS:
Return valid JSON with:
- main_story_angle
- surprising_fact
- central_question
- why_this_angle_matters
- why_fans_should_care
- rejected_angles
- data_warnings

TONE RULES:
Use simple football language. Sound like a friend who knows football well.

RESTRICTIONS:
Do not write the final script.
Do not use heavy tactical jargon.
Do not call the angle a "wild card."
Do not promise what will happen.
Do not create betting advice.

JSON OUTPUT INSTRUCTION:
Return only valid JSON. No markdown. No explanation outside JSON.
```

### Agent 3 prompt: Evidence Filter

```text
SYSTEM ROLE:
You are the Evidence Filter for INSIGHT FOOTBALL.

TASK:
Select only the facts that support the main story angle. Remove irrelevant stats. Keep the evidence useful for a 60-second video.

INPUT VARIABLES:
main_story_angle: {{main_story_angle}}
raw_statistics: {{raw_statistics_json}}
team_form: {{team_form_json}}
head_to_head: {{head_to_head_json}}
injuries: {{injuries_json}}
odds: {{odds_json}}
xg: {{xg_json}}
goals_scored_conceded: {{goals_json}}
home_away_data: {{home_away_json}}

OUTPUT REQUIREMENTS:
Return valid JSON with:
- evidence_points: 3 to 5 items
- evidence_strength_rating
- weak_data_warnings
- recommended_visual_evidence

Each evidence point must include:
- point
- why_it_matters
- source_type
- confidence

TONE RULES:
Plain English. Explain why the fact matters.

RESTRICTIONS:
Do not include more than 5 evidence points.
Do not include stats that do not support the story.
Do not invent facts.
Flag weak or unreliable data.

JSON OUTPUT INSTRUCTION:
Return only valid JSON. No markdown. No explanation outside JSON.
```

### Agent 4 prompt: Insight Scoring Agent

```text
SYSTEM ROLE:
You are the Insight Scoring Agent for INSIGHT FOOTBALL.

TASK:
Create a simple visual dashboard for the selected match. The dashboard must be explainable, consistent, and suitable for a short video.

INPUT VARIABLES:
selected_match: {{selected_match_json}}
evidence_points: {{evidence_points_json}}
team_form: {{team_form_json}}
home_away_data: {{home_away_json}}
injuries: {{injuries_json}}
odds: {{odds_json}}
model_notes: {{model_notes}}

OUTPUT REQUIREMENTS:
Return valid JSON with:
- home_win_probability
- draw_probability
- away_win_probability
- form_summary
- tactical_advantage
- uncertainty_level
- x_factor
- surprising_detail
- plain_english_summary

TONE RULES:
Simple and clear. The scores are for visuals, not for gambling.

RESTRICTIONS:
Probabilities must total 100.
Use whole numbers.
Do not claim certainty.
Do not overcomplicate the dashboard.

JSON OUTPUT INSTRUCTION:
Return only valid JSON. No markdown. No explanation outside JSON.
```

### Agent 5 prompt: Scriptwriter

```text
SYSTEM ROLE:
You are the Scriptwriter for INSIGHT FOOTBALL.

TASK:
Write a final voiceover script for a vertical football preview video. It must be 60 seconds or less and under 150 words.

INPUT VARIABLES:
selected_match: {{selected_match_json}}
main_story_angle: {{main_story_angle}}
central_question: {{central_question}}
evidence_points: {{evidence_points_json}}
insight_dashboard: {{insight_dashboard_json}}
brand_tone_rules: {{brand_tone_rules_json}}

OUTPUT REQUIREMENTS:
Return valid JSON with:
- final_voiceover_script
- estimated_duration_seconds
- word_count
- hook
- central_question
- closing_engagement_question
- compliance_warning

TONE RULES:
Never sound like an analyst. Sound like a friend who happens to know football really well.
If a 16-year-old football fan would not naturally say it in conversation, do not use it.

RESTRICTIONS:
Start with: "Before the first whistle... here's the insight."
Do not sound like a betting page.
Do not promise guaranteed outcomes.
Do not say "this will happen."
Do not say "today's Wild Card."
Do not read every metric mechanically.
Use phrases like "everything points to", "this could matter", "the edge goes to", and "football can still surprise us" where natural.

JSON OUTPUT INSTRUCTION:
Return only valid JSON. No markdown. No explanation outside JSON.
```

### Agent 6 prompt: Storyboard Agent

```text
SYSTEM ROLE:
You are the Storyboard Agent for INSIGHT FOOTBALL.

TASK:
Convert the final script into a scene-by-scene production plan for a 9:16 video. Visuals must change every 3 to 5 seconds.

INPUT VARIABLES:
final_script: {{final_script}}
dashboard_data: {{dashboard_data_json}}
brand_visual_rules: {{brand_visual_rules_json}}

OUTPUT REQUIREMENTS:
Return valid JSON with a scenes array. Each scene must include:
- scene_number
- timestamp_start
- timestamp_end
- voiceover_line
- visual_description
- on_screen_text
- animation_instruction
- asset_needed
- caption_text

TONE RULES:
Visuals should feel like a clean football intelligence dashboard.

RESTRICTIONS:
Total duration must be 60 seconds or less.
No scene should stay visually static for more than 5 seconds.
Do not overload the screen with text.
Captions must be short.

JSON OUTPUT INSTRUCTION:
Return only valid JSON. No markdown. No explanation outside JSON.
```

### Agent 7 prompt: Visual Director

```text
SYSTEM ROLE:
You are the Visual Director for INSIGHT FOOTBALL.

TASK:
Turn the storyboard into template-ready video instructions for automated rendering.

INPUT VARIABLES:
storyboard: {{storyboard_json}}
available_assets: {{available_assets_json}}
team_names: {{team_names_json}}
team_logos: {{team_logos_json}}
brand_colors: {{brand_colors_json}}
dashboard_data: {{dashboard_data_json}}

OUTPUT REQUIREMENTS:
Return valid JSON with:
- layout_instructions
- camera_movement
- typography_rules
- caption_placement
- dashboard_design
- animation_rules
- asset_list
- render_instructions

TONE RULES:
Clean, bold, modern football intelligence dashboard.

RESTRICTIONS:
Vertical 9:16 only.
No clutter.
No copyrighted broadcast footage unless licensed.
Use player cutouts only from approved legal assets.
Every visual must support the story.

JSON OUTPUT INSTRUCTION:
Return only valid JSON. No markdown. No explanation outside JSON.
```

### Agent 8 prompt: Quality Control Agent

```text
SYSTEM ROLE:
You are the Quality Control Agent for INSIGHT FOOTBALL.

TASK:
Decide whether the production package is good enough to publish. Be strict. Fail weak packages.

INPUT VARIABLES:
script: {{script_json}}
storyboard: {{storyboard_json}}
evidence: {{evidence_json}}
dashboard: {{dashboard_json}}
brand_rules: {{brand_rules_json}}

OUTPUT REQUIREMENTS:
Return valid JSON with:
- pass_or_fail
- reason
- issues_found
- required_fixes
- retention_score
- clarity_score
- story_score
- evidence_score
- final_recommendation

PASS/FAIL RULES:
Fail if the opening is boring.
Fail if the script sounds robotic.
Fail if there is no clear central question.
Fail if the surprising fact is weak.
Fail if the script is too technical.
Fail if the video is longer than 60 seconds.
Fail if the content sounds like guaranteed betting advice.
Fail if too many statistics are mentioned without explanation.
Fail if the ending does not invite engagement.

JSON OUTPUT INSTRUCTION:
Return only valid JSON. No markdown. No explanation outside JSON.
```

---

## 6. Production Package Schema

Master schema name:

```text
InsightFootballProductionPackage
```

Schema:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "InsightFootballProductionPackage",
  "type": "object",
  "required": [
    "package_id",
    "date",
    "match",
    "competition",
    "selected_reason",
    "story_angle",
    "surprising_fact",
    "central_question",
    "evidence_points",
    "insight_dashboard",
    "final_script",
    "storyboard",
    "visual_direction",
    "captions",
    "publishing_metadata",
    "quality_control",
    "status"
  ],
  "properties": {
    "package_id": { "type": "string" },
    "date": { "type": "string", "format": "date" },
    "match": {
      "type": "object",
      "required": ["home_team", "away_team", "kickoff_time"],
      "properties": {
        "home_team": { "type": "string" },
        "away_team": { "type": "string" },
        "kickoff_time": { "type": "string" },
        "venue": { "type": "string" }
      }
    },
    "competition": { "type": "string" },
    "selected_reason": { "type": "string" },
    "story_angle": { "type": "string" },
    "surprising_fact": { "type": "string" },
    "central_question": { "type": "string" },
    "evidence_points": {
      "type": "array",
      "minItems": 3,
      "maxItems": 5
    },
    "insight_dashboard": {
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
        "plain_english_summary"
      ]
    },
    "final_script": {
      "type": "object",
      "required": ["voiceover", "word_count", "estimated_duration_seconds"]
    },
    "storyboard": {
      "type": "array",
      "items": { "type": "object" }
    },
    "visual_direction": { "type": "object" },
    "captions": {
      "type": "array",
      "items": { "type": "object" }
    },
    "publishing_metadata": {
      "type": "object",
      "properties": {
        "youtube_title": { "type": "string" },
        "facebook_caption": { "type": "string" },
        "telegram_caption": { "type": "string" },
        "hashtags": { "type": "array", "items": { "type": "string" } }
      }
    },
    "quality_control": { "type": "object" },
    "status": {
      "type": "string",
      "enum": ["draft", "needs_review", "approved", "rendered", "published", "failed"]
    }
  }
}
```

### Example production package

This is illustrative sample data only. It must be replaced with verified live data before publishing.

```json
{
  "package_id": "if-2026-07-06-liverpool-arsenal",
  "date": "2026-07-06",
  "match": {
    "home_team": "Liverpool",
    "away_team": "Arsenal",
    "kickoff_time": "20:00",
    "venue": "Anfield"
  },
  "competition": "Premier League",
  "selected_reason": "High audience interest, strong rivalry feel, clear data availability, and a strong pre-kickoff story around Liverpool's fast starts.",
  "story_angle": "Liverpool may have the edge if they turn the first 20 minutes into chaos, but Arsenal have enough quality to punish one mistake.",
  "surprising_fact": "Sample data: Liverpool have scored first in most of their recent home matches, while Arsenal have often grown into away games slowly.",
  "central_question": "Can Arsenal survive Liverpool's fast start?",
  "evidence_points": [
    {
      "point": "Sample data: Liverpool have started recent home games quickly.",
      "why_it_matters": "It supports the idea that Arsenal's first job is surviving the opening pressure.",
      "source_type": "team form",
      "confidence": "medium"
    },
    {
      "point": "Sample data: Arsenal have conceded more early chances away from home than at home.",
      "why_it_matters": "It makes the opening phase feel important.",
      "source_type": "home away data",
      "confidence": "medium"
    },
    {
      "point": "Sample data: Arsenal's attack still creates enough chances to change the game late.",
      "why_it_matters": "It stops the story from becoming a one-sided prediction.",
      "source_type": "chance creation",
      "confidence": "medium"
    }
  ],
  "insight_dashboard": {
    "home_win_probability": 43,
    "draw_probability": 27,
    "away_win_probability": 30,
    "form_summary": "Liverpool edge the recent home form, Arsenal remain dangerous away.",
    "tactical_advantage": "Liverpool's early pressure against Arsenal's slower away starts.",
    "uncertainty_level": "medium",
    "x_factor": "Arsenal's first pass through midfield under pressure.",
    "surprising_detail": "The first 20 minutes may matter more than the final scoreline suggests.",
    "plain_english_summary": "Everything points to Liverpool having the early edge, but Arsenal have enough quality to turn one loose moment into a goal."
  },
  "final_script": {
    "voiceover": "Before the first whistle... here's the insight. Liverpool's biggest weapon in this one might not be a player. It might be the first 20 minutes. Sample data shows they have been starting fast at home, while Arsenal have sometimes needed time to settle away. So the question is simple: can Arsenal survive Liverpool's fast start? If they do, this game could open up for them. But if Liverpool win the early pressure, the edge goes to the home side. The dashboard gives Liverpool a small edge, not a guarantee, because football can still surprise us. Do you agree, or are we missing something? Tell us below.",
    "word_count": 107,
    "estimated_duration_seconds": 52
  },
  "storyboard": [
    {
      "scene_number": 1,
      "timestamp_start": 0,
      "timestamp_end": 3,
      "voiceover_line": "Before the first whistle... here's the insight.",
      "visual_description": "Brand lockup over dark pitch texture with both club crests.",
      "on_screen_text": "Before the first whistle",
      "animation_instruction": "Slow zoom in.",
      "asset_needed": ["brand logo", "pitch background", "club crests"],
      "caption_text": "Here's the insight."
    },
    {
      "scene_number": 2,
      "timestamp_start": 3,
      "timestamp_end": 8,
      "voiceover_line": "Liverpool's biggest weapon in this one might not be a player.",
      "visual_description": "Liverpool crest expands with first 20 minutes timer graphic.",
      "on_screen_text": "The first 20 minutes",
      "animation_instruction": "Quick punch-in.",
      "asset_needed": ["Liverpool crest", "timer icon"],
      "caption_text": "It might be time."
    },
    {
      "scene_number": 3,
      "timestamp_start": 8,
      "timestamp_end": 14,
      "voiceover_line": "It might be the first 20 minutes.",
      "visual_description": "Animated match clock and pressure arrows toward Arsenal half.",
      "on_screen_text": "Fast start?",
      "animation_instruction": "Pressure arrows slide forward.",
      "asset_needed": ["pitch diagram", "arrow icons"],
      "caption_text": "Fast start?"
    },
    {
      "scene_number": 4,
      "timestamp_start": 14,
      "timestamp_end": 20,
      "voiceover_line": "So the question is simple: can Arsenal survive Liverpool's fast start?",
      "visual_description": "Split screen: Liverpool pressure bar vs Arsenal survival bar.",
      "on_screen_text": "Can Arsenal survive it?",
      "animation_instruction": "Horizontal comparison movement.",
      "asset_needed": ["club crests", "bar graphics"],
      "caption_text": "Can Arsenal survive?"
    },
    {
      "scene_number": 5,
      "timestamp_start": 20,
      "timestamp_end": 32,
      "voiceover_line": "If they do, this game could open up for them.",
      "visual_description": "Arsenal transition path appears through midfield.",
      "on_screen_text": "One clean escape changes it",
      "animation_instruction": "Ball path draws across pitch.",
      "asset_needed": ["pitch diagram", "ball icon"],
      "caption_text": "One escape changes it."
    },
    {
      "scene_number": 6,
      "timestamp_start": 32,
      "timestamp_end": 45,
      "voiceover_line": "But if Liverpool win the early pressure, the edge goes to the home side.",
      "visual_description": "Dashboard cards show form, tactical advantage, and X-factor.",
      "on_screen_text": "Small edge: Liverpool",
      "animation_instruction": "Cards slide in one by one.",
      "asset_needed": ["dashboard template"],
      "caption_text": "Small edge: Liverpool."
    },
    {
      "scene_number": 7,
      "timestamp_start": 45,
      "timestamp_end": 55,
      "voiceover_line": "The dashboard gives Liverpool a small edge, not a guarantee, because football can still surprise us.",
      "visual_description": "Animated probability bars: 43, 27, 30.",
      "on_screen_text": "Edge, not guarantee",
      "animation_instruction": "Probability bars fill from zero.",
      "asset_needed": ["probability bars"],
      "caption_text": "Edge, not guarantee."
    },
    {
      "scene_number": 8,
      "timestamp_start": 55,
      "timestamp_end": 60,
      "voiceover_line": "Do you agree, or are we missing something? Tell us below.",
      "visual_description": "Both crests return with comment prompt.",
      "on_screen_text": "Do you agree?",
      "animation_instruction": "Subtle pulse on comment icon.",
      "asset_needed": ["club crests", "comment icon"],
      "caption_text": "Tell us below."
    }
  ],
  "visual_direction": {
    "layout_instructions": [
      "Use 1080x1920 vertical canvas.",
      "Keep club crests large and readable.",
      "Keep captions in the lower safe zone."
    ],
    "camera_movement": [
      "Slow zoom for opening.",
      "Quick punch-in on the surprising fact.",
      "Horizontal slide for team comparison.",
      "Animated bars for dashboard."
    ],
    "typography_rules": [
      "Bold condensed headline font.",
      "Maximum 7 caption words per line.",
      "Use high contrast text."
    ],
    "caption_placement": "Lower third, above platform UI safe area.",
    "dashboard_design": [
      "Show probabilities as simple bars.",
      "Show tactical advantage as one sentence.",
      "Show X-factor as one short label."
    ],
    "animation_rules": [
      "No excessive effects.",
      "Every movement must support attention or meaning."
    ],
    "asset_list": ["brand logo", "club crests", "pitch diagram", "dashboard cards", "icons"],
    "render_instructions": [
      "Export MP4 H.264.",
      "1080x1920.",
      "30 fps.",
      "Keep duration at 60 seconds or less."
    ]
  },
  "captions": [
    { "start": 0, "end": 3, "text": "Here's the insight." },
    { "start": 3, "end": 8, "text": "It might be time." },
    { "start": 14, "end": 20, "text": "Can Arsenal survive?" }
  ],
  "publishing_metadata": {
    "youtube_title": "Liverpool vs Arsenal: Before the first whistle",
    "facebook_caption": "Can Arsenal survive Liverpool's fast start?",
    "telegram_caption": "Before the first whistle: Liverpool vs Arsenal insight.",
    "hashtags": ["#InsightFootball", "#Liverpool", "#Arsenal", "#FootballShorts"]
  },
  "quality_control": {
    "pass_or_fail": "pass",
    "reason": "Clear story, strong central question, simple language, non-guaranteed conclusion.",
    "issues_found": [],
    "required_fixes": [],
    "retention_score": 8.5,
    "clarity_score": 9,
    "story_score": 8.5,
    "evidence_score": 7.5,
    "final_recommendation": "Approved for render after replacing sample data with verified live data."
  },
  "status": "approved"
}
```

---

## 7. Data Flow

Text diagram:

```text
Raw Fixtures
-> Match Selector
-> Selected Match
-> Story Hunter
-> Story Angle + Central Question
-> Evidence Filter
-> Evidence Points
-> Insight Scoring Agent
-> Dashboard
-> Scriptwriter
-> Voiceover Script
-> Storyboard Agent
-> Scene Plan
-> Visual Director
-> Render Instructions
-> Quality Control
-> Final Production Package
-> Video Renderer
-> Publishing
```

### Stage-by-stage flow

Raw Fixtures:

- Receives fixture list, kickoff times, competitions, and basic popularity signals.
- Produces structured fixture input.

Match Selector:

- Receives all fixtures.
- Produces one selected match and selection reason.

Story Hunter:

- Receives selected match, form, injuries, head-to-head, home/away data, odds if available, news, and style notes.
- Produces story angle, surprising fact, central question, and fan relevance.

Evidence Filter:

- Receives story angle and raw statistics.
- Produces 3 to 5 evidence points and recommended visuals.

Insight Scoring Agent:

- Receives evidence and simplified match data.
- Produces dashboard fields and plain English summary.

Scriptwriter:

- Receives selected match, story, question, evidence, dashboard, and tone rules.
- Produces final voiceover script under 150 words.

Storyboard Agent:

- Receives final script and dashboard.
- Produces timestamped scenes with visual descriptions, captions, and assets.

Visual Director:

- Receives storyboard and available assets.
- Produces template instructions for rendering.

Quality Control:

- Receives the script, storyboard, evidence, dashboard, and brand rules.
- Produces pass/fail, scores, issues, and required fixes.

Final Production Package:

- Combines all approved outputs into one JSON object.

Video Renderer:

- Receives render instructions, assets, captions, and voiceover.
- Produces a vertical MP4.

Publishing:

- Receives final MP4 and metadata.
- Publishes or queues to YouTube Shorts, Facebook Reels, and Telegram.

### Human review points for MVP testing

Human review should be inserted after:

- Match Selector: confirm the chosen match is worth covering.
- Story Hunter: confirm the angle is actually interesting.
- Scriptwriter: confirm the script sounds human.
- Quality Control: approve before render.
- First 30 published videos: manually review performance and comments.

---

## 8. Visual Template Rules

INSIGHT FOOTBALL should look like a clean football intelligence dashboard, not a generic slideshow.

Global rules:

- Vertical 9:16 format.
- 1080x1920 recommended.
- 60 seconds maximum.
- Visual change every 3 to 5 seconds.
- Captions always visible.
- Simple bold text.
- No clutter.
- Club logos shown clearly.
- Use player cutouts only when legally safe or from approved assets.
- Avoid copyrighted broadcast footage unless licensed.
- Use template-based motion graphics.
- Use animated bars, arrows, pitch diagrams, icons, and dashboard cards.
- Use clean background motion.
- Do not overload the screen with data.
- Every scene must support the story.

### Opening scene

- Brand logo.
- Match title.
- Both team crests.
- Dark pitch or clean football texture.
- Voiceover: "Before the first whistle... here's the insight."

### Match title scene

- Home team vs away team.
- Competition name.
- Kickoff time if relevant.
- Use large crests and compact text.

### Surprising fact scene

- One big statement.
- Quick punch-in.
- Use a timer, arrow, warning marker, or simple highlight shape.
- No paragraph text.

### Central question scene

- One question only.
- Use big readable text.
- Show both team crests or a split-screen comparison.

### Evidence scenes

- One evidence idea per scene.
- Use bars, arrows, pitch zones, or icons.
- Avoid more than one number per scene unless comparison is necessary.

### Dashboard scene

- Show probability bars.
- Show form summary.
- Show tactical advantage.
- Show uncertainty.
- Show X-factor.
- Keep labels visual; voiceover stays natural.

### Closing CTA scene

- Return to both crests.
- Show the debate question.
- Add comment icon.
- Keep it clean and easy to read.

---

## 9. Camera Movement Rules

Movement should help the viewer understand where to look.

| Movement | Use case | Rule |
|---|---|---|
| Slow zoom in | Opening and hooks | Creates focus without chaos. |
| Slide transition | Evidence scenes | Moves from one point to the next. |
| Quick punch-in | Surprising facts | Adds emphasis. |
| Horizontal movement | Team comparisons | Helps viewers feel the side-by-side contrast. |
| Animated probability bars | Dashboard | Makes numbers easier to understand. |
| Subtle pulse | CTA or key phrase | Use only for emphasis. |
| Subtle shake | Rare surprise moment | Use sparingly, never throughout a scene. |

Avoid:

- Excessive zooms.
- Random spins.
- Fast flashing.
- Effects that make text harder to read.
- Motion that does not support the story.

---

## 10. Caption Rules

Caption style:

- Short captions.
- Maximum 7 words per caption line.
- One or two lines maximum.
- Highlight only key phrases.
- Do not caption huge paragraphs.
- Use simple spoken English.
- Captions should match the voiceover but can be slightly compressed.
- Important words can appear as big on-screen text.
- Captions must stay inside platform safe areas.

Example:

Voiceover:

```text
Liverpool have been creating better chances every week.
```

Caption:

```text
Liverpool create better chances.
```

Caption formatting:

- Lower third placement.
- High contrast text.
- Key phrase highlight color.
- No tiny text.
- No full-screen blocks of subtitles.

---

## 11. Dashboard Rules

The dashboard is visual support, not the main story.

### Insight Score

Display:

- Home win probability.
- Draw probability.
- Away win probability.

Rules:

- Use whole numbers.
- Bars must total 100.
- Label as "edge" or "lean", not "prediction guarantee."

### Form comparison

Display:

- Short phrase for each team.
- Example: "Fast home starts" vs "Strong late control."

### Tactical advantage

Display:

- One sentence.
- Example: "Liverpool pressure vs Arsenal buildup."

### Match uncertainty

Display:

- Low, medium, or high.
- Explain with one short phrase.

### X-factor

Display:

- One player, absence, pattern, or moment.
- Example: "First pass through midfield."

### Surprising detail

Display:

- One detail fans can remember.
- Example: "The first 20 minutes could decide the mood."

Narration rule:

Do not mechanically read dashboard labels. Say it naturally:

```text
Everything we looked at gives Liverpool the edge, but Arsenal still have enough quality to punish one mistake.
```

---

## 12. Scripting Rules

### Rulebook

- Use simple football language.
- Start with a surprising fact after the brand opening.
- Ask one central question.
- Explain one idea clearly.
- Do not overload the viewer.
- Avoid technical jargon.
- Avoid betting certainty.
- Avoid robotic phrasing.
- Use curiosity.
- End with a debate question.
- Keep under 150 words.
- Keep under 60 seconds.
- Use short sentences.
- Let the evidence support the story quietly.

### Required language patterns

Use when natural:

- "everything points to..."
- "this could matter..."
- "the edge goes to..."
- "football can still surprise us..."
- "the question is simple..."

Avoid:

- "guaranteed"
- "lock"
- "banker"
- "must win bet"
- "this will happen"
- "expected goals differential"
- "transition efficiency"
- "today's Wild Card"

Bad example:

```text
The home side has a superior expected goals differential and transition efficiency.
```

Good example:

```text
Liverpool are creating better chances, and they are doing it earlier in games.
```

---

## 13. Match Story Angle Types

### 1. Can Team A survive Team B's early pressure?

When to use:

- One team starts quickly.
- The other team often settles slowly.
- Home crowd pressure is relevant.

Data that supports it:

- First-half goals.
- Shots in first 20 minutes.
- Home pressure data.
- Early concessions.

Example central question:

```text
Can Arsenal survive Liverpool's fast start?
```

Example opening line:

```text
Liverpool's biggest weapon here might be the first 20 minutes.
```

### 2. Is Team A being overrated?

When to use:

- Public hype is stronger than recent performance.
- Results look better than chance quality.

Data that supports it:

- Narrow wins.
- Weak underlying chance quality.
- Injuries.
- Easier recent fixtures.

Example central question:

```text
Are we giving Chelsea too much credit?
```

Example opening line:

```text
The table says one thing, but the performances say something else.
```

### 3. Is Team B more dangerous than people think?

When to use:

- Underdog has strong recent form.
- Favorite has a weakness the underdog can attack.

Data that supports it:

- Away scoring form.
- Counterattack goals.
- Recent chance creation.
- Favorite defensive absences.

Example central question:

```text
Are Spurs walking into a harder game than people expect?
```

Example opening line:

```text
This looks simple on paper, but it may not feel simple on the pitch.
```

### 4. Will one missing player change the match?

When to use:

- A key player is injured, suspended, or doubtful.
- The team relies heavily on that player's role.

Data that supports it:

- Win rate with and without player.
- Goals created.
- Defensive actions.
- Replacement quality.

Example central question:

```text
How much will City miss Rodri in this one?
```

Example opening line:

```text
The biggest story in this match might be the player who is not there.
```

### 5. Is the favourite actually vulnerable?

When to use:

- Favorite has name value but recent warning signs.
- Opponent has a clear route to cause problems.

Data that supports it:

- Defensive errors.
- Recent conceded chances.
- Fixture fatigue.
- Weakness against pace or set pieces.

Example central question:

```text
Is the favourite more vulnerable than the odds suggest?
```

Example opening line:

```text
The favourite has the bigger name, but not the cleaner story.
```

### 6. Could the underdog cause problems?

When to use:

- Underdog has a specific matchup advantage.
- Favorite struggles against compact teams or counters.

Data that supports it:

- Set-piece goals.
- Counterattack chances.
- Defensive shape.
- Favorite's recent slow starts.

Example central question:

```text
Can the underdog make this uncomfortable?
```

Example opening line:

```text
This is exactly the kind of game that can get awkward quickly.
```

### 7. Is this match closer than the odds suggest?

When to use:

- Market or public view heavily favors one side.
- Form and matchup data suggest a smaller gap.

Data that supports it:

- Recent form comparison.
- Chance creation.
- Injury balance.
- Home/away splits.

Example central question:

```text
Is this match closer than people think?
```

Example opening line:

```text
The gap on paper looks bigger than the gap on the pitch.
```

### 8. Can Team A stop one key player?

When to use:

- One player drives the opponent's attack.
- Opponent depends on that player for goals or creation.

Data that supports it:

- Goal involvement.
- Chances created.
- Touches in dangerous areas.
- Defensive matchup.

Example central question:

```text
Can United keep Saka quiet?
```

Example opening line:

```text
This match may come down to one side of the pitch.
```

### 9. Will the midfield battle decide everything?

When to use:

- Both teams need control in central areas.
- Press resistance, turnovers, or buildup are key.

Data that supports it:

- Possession losses.
- Pressing numbers.
- Passing under pressure.
- Ball recoveries.

Example central question:

```text
Who wins the middle before anyone wins the match?
```

Example opening line:

```text
Forget the score for a second. Watch the midfield first.
```

### 10. Is home advantage the biggest factor?

When to use:

- Home team performs much better at home.
- Away team has clear travel or away-form issues.

Data that supports it:

- Home record.
- Away record.
- Goals at home vs away.
- Crowd or venue factors.

Example central question:

```text
Is home advantage the real edge here?
```

Example opening line:

```text
The badge matters, but the stadium might matter more.
```

---

## 14. Quality Control Checklist

Approve only if every item is true:

- One clear match.
- One clear central question.
- First 5 seconds are strong.
- One surprising fact.
- Simple language.
- Story is easy to follow.
- Evidence supports the story.
- Video can be understood without deep football knowledge.
- Does not sound like gambling advice.
- Does not promise certainty.
- Ending invites comments.
- Visuals change every 3 to 5 seconds.
- Total duration is 60 seconds or less.
- Script is under 150 words unless deliberately approved.
- Captions are readable.
- On-screen text is not crowded.
- Dashboard supports the story instead of taking over.
- Sample or uncertain data is clearly marked internally before publishing.
- No unsafe copyrighted footage is required.

Quality scoring:

- Retention score: hook strength, pacing, visual changes.
- Clarity score: simple language and one clear idea.
- Story score: surprising fact, question, fan relevance.
- Evidence score: strength, relevance, and reliability of proof.

Minimum publish recommendation:

- Retention score: 7 or higher.
- Clarity score: 8 or higher.
- Story score: 7 or higher.
- Evidence score: 7 or higher.
- No mandatory fail condition triggered.

---

## 15. MVP Implementation Notes

Do not build a complex system first. The first goal is to prove that the content format works.

### Phase 1: Manual data input + AI production package

Build first:

- A manual fixture input form.
- A simple data input form for form, injuries, recent notes, and basic stats.
- LLM steps for each agent.
- Master production package JSON.
- Manual review after Story Hunter, Scriptwriter, and Quality Control.

Keep manual:

- Final match choice.
- Data verification.
- Asset selection.
- Publishing.

Why:

The MVP should test whether the insight format, tone, and retention structure work before investing in full automation.

### Phase 2: Automated fixture and stats collection

Automate:

- Daily fixture pull.
- Competition filtering.
- Basic team form.
- Home/away records.
- Recent goals scored/conceded.
- Injuries from trusted sources if available.

Keep manual:

- Final story angle approval.
- Data source spot checks.

Why:

Automation should reduce repetitive input while humans still protect story quality.

### Phase 3: Automated rendering

Use:

- Creatomate.
- Shotstack.
- Remotion.
- Canva template automation.
- Any renderer that supports vertical templates, dynamic text, images, captions, and animations.

Automate:

- Scene creation from storyboard.
- Caption placement.
- Dashboard card population.
- Export to MP4.

Keep manual:

- Template design review.
- Legal asset approval.

Why:

Rendering can be automated once the visual structure is stable.

### Phase 4: Automated publishing

Automate:

- Upload to YouTube Shorts.
- Upload or schedule Facebook Reels.
- Post to Telegram channel.
- Use platform-specific captions and hashtags.

Keep manual:

- Approval before publishing until quality is consistent.

Why:

Publishing automation should come after the content rarely needs correction.

### Phase 5: Analytics feedback loop

Track:

- 3-second retention.
- Average view duration.
- Completion rate.
- Replays.
- Comments.
- Shares.
- Saves.
- Click-through from Telegram if relevant.

Feed back into:

- Match selection weighting.
- Story angle scoring.
- Hook style.
- Caption style.
- Dashboard complexity.
- CTA wording.

### What should be automated first

Automate first:

- JSON package creation.
- Agent chaining.
- Script word count and duration checks.
- QC fail rules.
- Storyboard generation.

Automate later:

- Data collection from many sources.
- Full video rendering.
- Publishing.
- Performance-based model tuning.

Keep manual during testing:

- Data verification.
- Story approval.
- Final script approval.
- Asset legality.
- Publish approval.

---

## 16. Output Requirements Summary

The complete INSIGHT FOOTBALL production system should output:

- Selected match.
- Story angle.
- Surprising fact.
- Central question.
- Evidence points.
- Insight dashboard.
- Final voiceover.
- Storyboard.
- Visual direction.
- Captions.
- Publishing metadata.
- Quality control result.
- Status.

The system should be built around one principle:

```text
One match. One question. One insight. One clean story. Under 60 seconds.
```

The first version should optimize for repeatable quality, not maximum automation. Once the team can consistently produce strong manual or semi-automated packages, automation can take over the repetitive work.
