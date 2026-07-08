# Evidence Filter Module

Agent: `IF-A03`  
Prompt: `IF-PROMPT-03-EVIDENCE-FILTER@v1.0`  
Scope: support the approved story with the strongest evidence only.

This module is production code for Sprint 1. It does not run Insight Engine or the full pipeline.

## Responsibilities

- Load Daily Input JSON.
- Load approved Match Selector output.
- Load approved Story Hunter output.
- Preserve locked Story Hunter fields.
- Load the frozen Evidence Filter prompt from the Prompt Library.
- Call an injectable LLM client.
- Validate response against JSON schema.
- Reject unrelated, duplicated, weak, contradictory-hidden, unsupported, speculative, or betting-style evidence.
- Translate statistics into simple football language.
- Retry once on validation failure.
- Return structured errors.
- Write structured JSON logs.

## Inputs

1. Daily Input JSON.
2. Approved Match Selection JSON.
3. Approved Story Hunter JSON.

## Output

Validated Evidence Filter JSON containing:

- evidence_summary
- primary_evidence
- secondary_evidence
- supporting_statistics
- supporting_context
- contradictory_evidence
- missing_information
- evidence_quality
- evidence_confidence
- locked_fields
- approval_status
- next_agent

## Sample Execution

Set `PYTHONPATH`:

```text
$env:PYTHONPATH='editorial-brain/evidence-filter/src'
```

Run:

```text
C:\Users\HP\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m evidence_filter.cli --provider deterministic --config editorial-brain/evidence-filter/config/evidence-filter.config.json --daily-input editorial-brain/examples/liverpool-arsenal-daily-input.json --match-selection editorial-brain/output/match-selection-liverpool-arsenal.json --story-hunter editorial-brain/output/story-hunter-liverpool-arsenal.json --output editorial-brain/output/evidence-filter-liverpool-arsenal.json
```

## Locked Fields

The Evidence Filter must not modify:

- story_angle
- central_question
- surprising_fact

These remain locked after Story Hunter approval.
