# INSIGHT FOOTBALL Package Assembly Checklist

Use this checklist before a daily package is marked `approved`.

## Required Files

- Daily input JSON exists.
- Final production package JSON exists.
- Agent outputs were saved or copied into the final package.
- Any sample data has been replaced or clearly marked.

## Required Package Fields

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

## Match Check

- One match only.
- Home team is correct.
- Away team is correct.
- Competition is correct.
- Kickoff time is correct.
- Venue is included if available.

## Story Check

- One clear story angle.
- One clear central question.
- One surprising fact.
- Fans would naturally care about the question.
- The story is not generic.

## Evidence Check

- 3 to 5 evidence points.
- Every evidence point supports the story.
- Weak data is flagged.
- No unverified claim is presented as fact.
- No unnecessary stats are included.

## Dashboard Check

- Home win probability is present.
- Draw probability is present.
- Away win probability is present.
- Probabilities total 100.
- Form summary is simple.
- Tactical advantage is simple.
- Uncertainty level is low, medium, or high.
- X-factor is clear.

## Script Check

- Starts with: "Before the first whistle... here's the insight."
- Under 150 words.
- Estimated duration is 60 seconds or less.
- Sounds conversational.
- Avoids heavy jargon.
- Does not promise certainty.
- Does not sound like betting advice.
- Ends with a debate question.

## Storyboard Check

- Scenes are numbered.
- Timestamps are present.
- No scene runs beyond 60 seconds.
- Visuals change every 3 to 5 seconds.
- Captions are short.
- Every scene supports the story.

## Visual Direction Check

- 9:16 vertical format.
- Captions always visible.
- Club logos are clear.
- Dashboard is clean.
- No clutter.
- No unsafe copyrighted footage.
- Player cutouts are legally safe if used.

## Publishing Metadata Check

- YouTube title exists.
- Facebook caption exists.
- Telegram caption exists.
- Hashtags exist.
- Metadata does not sound like betting tips.

## Quality Control Check

- pass_or_fail is `pass`.
- retention_score is 7 or higher.
- clarity_score is 8 or higher.
- story_score is 7 or higher.
- evidence_score is 7 or higher.
- required_fixes is empty.

## Approval Decision

Set status to:

```text
approved
```

Only when every major check passes.

Set status to:

```text
needs_review
```

If the package is close but needs human changes.

Set status to:

```text
failed
```

If the story is weak, the script sounds robotic, the content sounds like betting advice, or the video cannot fit under 60 seconds.
