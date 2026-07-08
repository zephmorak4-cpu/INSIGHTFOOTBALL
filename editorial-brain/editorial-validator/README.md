# Editorial Validator

Sprint 2 Component: `S2-C01`

The Editorial Validator is not an AI writer and does not change the story. It checks whether an Editorial Package from the Sprint 1 Editorial Orchestrator is strong enough to continue toward scriptwriting.

## Input

```text
editorial_package.json
```

## Outputs

```text
validation-report-<production_id>.json
validated-editorial-package-<production_id>.json
```

The validated package is only created when approval status is `approved`.

## CLI

```text
$env:PYTHONPATH='editorial-brain/editorial-validator/src'
C:\Users\HP\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m editorial_validator.cli --config editorial-brain/editorial-validator/config/editorial-validator.config.json --package editorial-brain/output/editorial-package-if-2026-07-06-liverpool-arsenal.json
```

## Fails If

- Central question is missing.
- Story angle is generic.
- Surprising fact is weak.
- Evidence is unrelated or missing.
- Locked fields changed.
- Betting language appears.
- Fake certainty appears.
- Unsupported statistics or claims appear.
- Confidence is below threshold.
