# Editorial Orchestrator

The Editorial Orchestrator is not an AI agent.

It executes the completed Sprint 1 Editorial Brain modules in sequence:

```text
Daily Input
-> Match Selector
-> Story Hunter
-> Evidence Filter
-> Insight Engine
-> Canonical Editorial Package
```

It does not implement Scriptwriter, Storyboard, rendering, publishing, or any downstream system.

## Responsibilities

- Receive Daily Input JSON.
- Execute the four completed modules.
- Validate every stage.
- Stop immediately if a module fails.
- Preserve locked fields.
- Assemble one canonical Editorial Package.
- Write one execution log.
- Write one execution report.

## Sample Execution

Set `PYTHONPATH`:

```text
$env:PYTHONPATH='editorial-brain/editorial-orchestrator/src'
```

Run:

```text
C:\Users\HP\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m editorial_orchestrator.cli --config editorial-brain/editorial-orchestrator/config/editorial-orchestrator.config.json --daily-input editorial-brain/examples/liverpool-arsenal-daily-input.json
```

Expected outputs:

```text
editorial-brain/output/editorial-package-if-2026-07-06-liverpool-arsenal.json
editorial-brain/output/execution-report-if-2026-07-06-liverpool-arsenal.json
editorial-brain/logs/editorial-orchestrator-if-2026-07-06-liverpool-arsenal.log.jsonl
```

## Package Fails If

- Any required agent output is missing.
- JSON validation fails.
- Locked fields change.
- Confidence threshold is not met.
- Story consistency breaks.

## Canonical Package Includes

- Metadata
- Match
- Competition
- Story Angle
- Central Question
- Surprising Fact
- Primary Evidence
- Secondary Evidence
- Contradictory Evidence
- Insight Summary
- Match Edge
- Key Advantage
- Tactical Explanation
- Uncertainty Summary
- X-Factor
- Viewer Takeaway
- Confidence Scores
- Locked Fields
- Warnings
- Editorial Notes
- Execution Metadata
