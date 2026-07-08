# Story Hunter Module

Agent: `IF-A02`  
Prompt: `IF-PROMPT-02-STORY-HUNTER@v1.0`  
Scope: find the strongest pre-kickoff story angle.

This module is production code for Sprint 1. It does not run Evidence Filter, Insight Engine, Scriptwriter, or the full pipeline.

## Responsibilities

- Load Daily Input JSON.
- Load approved Match Selection JSON.
- Load the frozen Story Hunter prompt from the Prompt Library.
- Call an injectable LLM client.
- Validate response against JSON schema.
- Enforce Story Hunter business rules.
- Retry once on validation failure.
- Return a structured error if retry fails.
- Write structured JSON logs.

## Inputs

1. Daily Input JSON.
2. Approved Match Selection JSON from Module 1.

## Output

Validated Story Hunter JSON containing:

- story_angle
- central_question
- surprising_fact
- why_this_matters
- why_fans_should_care
- supporting_context
- rejected_angles
- story_confidence
- locked_fields
- approval_status
- next_agent

## Sample Execution

Set `PYTHONPATH`:

```text
$env:PYTHONPATH='editorial-brain/story-hunter/src'
```

Run with the deterministic adapter:

```text
C:\Users\HP\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m story_hunter.cli --provider deterministic --config editorial-brain/story-hunter/config/story-hunter.config.json --daily-input editorial-brain/examples/liverpool-arsenal-daily-input.json --match-selection editorial-brain/output/match-selection-liverpool-arsenal.json --output editorial-brain/output/story-hunter-liverpool-arsenal.json
```

## Validation

The module fails if:

- There is no clear story angle.
- The central question is boring.
- The surprising fact is weak.
- The angle is too generic.
- The language sounds too technical.
- The output sounds like betting advice.
- It only repeats obvious facts.
- It invents unsupported facts.
- Confidence is below 70.

## Locked Fields

After approval, these fields are locked:

- story_angle
- central_question
- surprising_fact

Downstream agents may support or challenge them, but they cannot silently rewrite them.
