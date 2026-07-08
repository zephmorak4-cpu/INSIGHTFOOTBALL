# INSIGHT FOOTBALL Agent Run Sheet

Use this as the quick copy-paste order for one daily production run.

## 1. Match Selector

Prompt file:

```text
prompts/match_selector.txt
```

Paste in:

```text
date
fixtures_json
```

Save output as:

```text
agent_outputs.match_selector
```

## 2. Story Hunter

Prompt file:

```text
prompts/story_hunter.txt
```

Paste in:

```text
selected_match_json
team_form_json
injuries_json
head_to_head_json
home_away_json
odds_json
recent_news_json
team_style_notes_json
```

Save output as:

```text
agent_outputs.story_hunter
```

## 3. Evidence Filter

Prompt file:

```text
prompts/evidence_filter.txt
```

Paste in:

```text
main_story_angle
raw_statistics_json
team_form_json
head_to_head_json
injuries_json
odds_json
xg_json
goals_json
home_away_json
```

Save output as:

```text
agent_outputs.evidence_filter
```

## 4. Insight Scoring Agent

Prompt file:

```text
prompts/insight_scoring_agent.txt
```

Paste in:

```text
selected_match_json
evidence_points_json
team_form_json
home_away_json
injuries_json
odds_json
model_notes
```

Save output as:

```text
agent_outputs.insight_scoring
```

## 5. Scriptwriter

Prompt file:

```text
prompts/scriptwriter.txt
```

Paste in:

```text
selected_match_json
main_story_angle
central_question
evidence_points_json
insight_dashboard_json
brand_tone_rules_json
```

Save output as:

```text
agent_outputs.scriptwriter
```

## 6. Storyboard Agent

Prompt file:

```text
prompts/storyboard_agent.txt
```

Paste in:

```text
final_script
dashboard_data_json
brand_visual_rules_json
```

Save output as:

```text
agent_outputs.storyboard
```

## 7. Visual Director

Prompt file:

```text
prompts/visual_director.txt
```

Paste in:

```text
storyboard_json
available_assets_json
team_names_json
team_logos_json
brand_colors_json
dashboard_data_json
```

Save output as:

```text
agent_outputs.visual_director
```

## 8. Quality Control Agent

Prompt file:

```text
prompts/quality_control_agent.txt
```

Paste in:

```text
script_json
storyboard_json
evidence_json
dashboard_json
brand_rules_json
```

Save output as:

```text
agent_outputs.quality_control
```

## Final Assembly

Combine approved outputs into:

```text
daily_packages/YYYY-MM-DD_home-team_away-team.json
```

Final status options:

```text
draft
needs_review
approved
rendered
published
failed
```

Use `approved` only after QC passes.
