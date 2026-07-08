# Match Selector Module

Agent: `IF-A01`  
Prompt: `IF-PROMPT-01-MATCH-SELECTOR@v1.0`  
Scope: select one match from Daily Input JSON.

This module is production code for Sprint 1. It does not run Story Hunter, Evidence Filter, Insight Engine, or the full pipeline.

## Responsibilities

- Load Daily Input JSON.
- Load the frozen Match Selector prompt from the Prompt Library.
- Call an injectable LLM client.
- Validate the response against JSON schema.
- Enforce Match Selector business rules.
- Retry once on validation failure.
- Return a structured error if retry fails.
- Write structured JSON logs.

## Folder Structure

```text
match-selector/
  config/
  schemas/
  src/match_selector/
  tests/
  README.md
```

## Sample Execution

Use the deterministic local adapter:

```text
C:\Users\HP\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m match_selector.cli --provider deterministic --config editorial-brain/match-selector/config/match-selector.config.json --input editorial-brain/examples/liverpool-arsenal-daily-input.json --output editorial-brain/output/match-selection-liverpool-arsenal.json
```

Set `PYTHONPATH` first when running directly from the repository:

```text
$env:PYTHONPATH='editorial-brain/match-selector/src'
```

## LLM Providers

The module includes:

- `OpenAICompatibleHTTPClient` for real OpenAI-compatible chat completions.
- `RuleBasedMatchSelectorClient` for deterministic local tests and sample execution.

To use a real provider, change:

```json
"provider": "openai"
```

And set:

```text
OPENAI_API_KEY
```

## Output

Successful output is a validated Match Selection JSON object.

Failed output is a structured error:

```json
{
  "success": false,
  "agent_id": "IF-A01",
  "agent_name": "Match Selector",
  "error": {
    "code": "MATCH_SELECTOR_VALIDATION_FAILED",
    "message": "Match Selector failed after retry",
    "issues": [],
    "retryable": false,
    "attempts": 2
  },
  "approval_status": "blocked",
  "next_agent": null
}
```

## Validation

The module validates:

- Daily Input schema.
- Match Selection schema.
- Required fields.
- Confidence score.
- Selected match exists in input fixtures.
- Forbidden betting language.
- Story potential threshold.
- Data availability threshold.

Minimum confidence:

```text
70
```
