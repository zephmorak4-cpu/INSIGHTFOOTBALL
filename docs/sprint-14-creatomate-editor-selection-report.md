# Sprint 14 Report: Creatomate Rendering + Editor Match Selection

Date: 2026-07-09

## Implemented

- Added Editor Match Selection support.
- Editor-selected matches override automatic Match Selector recommendations.
- Automatic selection remains available only when no editor selection is provided.
- Added Creatomate Template Registry with opening, match intro, question, evidence, tactical, comparison, dashboard, CTA, and closing templates.
- Upgraded Creatomate renderer payloads to use dynamic variables.
- Added silent audio mode for CapCut narration/audio overlay.
- Updated Telegram approval copy for production, match, selected-by, audio mode, render mode, readiness, score, story, question, video status, and Creatomate status.
- Added sample leakage checks for Creatomate payloads.

## Sample Run

Editor selection:

```text
France vs Morocco
Competition: International Friendly
Selected by: Human editor
Audio mode: silent
Render mode: creatomate
Creatomate status: dry_run_complete
```

Dry-run result:

```text
Daily run: passed
Creatomate payload: created
Template scenes: 10
Sample leakage: no Liverpool/Arsenal in Creatomate payload
```

## Creatomate Payload Summary

Required global variables are populated dynamically:

```text
brand_logo
corner_logo
home_team
away_team
competition
home_badge
away_badge
competition_logo
match_title
central_question
surprising_fact
main_insight
primary_evidence
secondary_evidence
viewer_takeaway
cta_text
tagline
```

## Telegram Approval Sample

```text
INSIGHT FOOTBALL APPROVAL REQUEST

Production: if-2026-07-09-france-morocco
Match: France vs Morocco
Competition: International Friendly
Selected by: Human editor
Audio mode: silent, ready for CapCut voice/audio overlay
Render mode: creatomate
Readiness: needs_human_review
Score: 86

Story: France may have the edge if they turn the first 20 minutes into pressure, but Morocco have enough quality to punish one mistake.
Question: Can Morocco survive France's fast start?
Video status: completed
Creatomate status: dry_run_complete

Approval gate:
Review video, approve, then publish.
```

## Tests

```text
Ran 405 tests
OK
```

## Remaining Manual Setup

- Provide a real `EDITOR_SELECTION_PATH` file for each editor-controlled daily run, or leave it unset to use automatic recommendation mode.
- Replace the temporary single Creatomate template ID with separate template IDs when each production template is created in Creatomate.
- Telegram user/chat must start the bot before approval messages can be delivered to that chat.
