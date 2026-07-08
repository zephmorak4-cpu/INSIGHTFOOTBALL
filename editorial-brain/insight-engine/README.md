# Insight Engine Module

Agent: `IF-A04`  
Prompt: `IF-PROMPT-04-INSIGHT-ENGINE@v1.0`  
Scope: transform approved evidence into a balanced editorial conclusion.

This module is production code for Sprint 1. It does not run Scriptwriter, Storyboard, rendering, publishing, or the full pipeline.

## Responsibilities

- Load Daily Input JSON.
- Load approved Match Selector output.
- Load approved Story Hunter output.
- Load approved Evidence Filter output.
- Preserve locked story fields.
- Explain what the evidence means.
- Produce a match edge without probabilities.
- Explain uncertainty honestly.
- Identify one tactical implication.
- Identify one X-factor.
- Produce a memorable takeaway.
- Validate output.
- Retry once on validation failure.
- Log structured events.

## Sample Execution

Set `PYTHONPATH`:

```text
$env:PYTHONPATH='editorial-brain/insight-engine/src'
```

Run:

```text
C:\Users\HP\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m insight_engine.cli --provider deterministic --config editorial-brain/insight-engine/config/insight-engine.config.json --daily-input editorial-brain/examples/liverpool-arsenal-daily-input.json --match-selection editorial-brain/output/match-selection-liverpool-arsenal.json --story-hunter editorial-brain/output/story-hunter-liverpool-arsenal.json --evidence-filter editorial-brain/output/evidence-filter-liverpool-arsenal.json --output editorial-brain/output/insight-engine-liverpool-arsenal.json
```

## Match Edge Rules

Allowed values:

- Home Edge
- Away Edge
- Balanced
- Slight Home Edge
- Slight Away Edge

Probabilities are not allowed.

## Locked Fields

The Insight Engine must preserve:

- story_angle
- central_question
- surprising_fact

It may explain them, but it cannot rewrite them.
