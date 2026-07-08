# Hook Optimizer

Sprint 3 component 2. The Hook Optimizer receives `script_output.json` and `production_brief.json`, creates three hook options, selects the strongest factual option, and writes:

- `hook-optimization-<production_id>.json`
- `optimized-script-output-<production_id>.json`

It does not change the central question, surprising fact, or locked fields.

```powershell
$env:PYTHONPATH='editorial-brain\hook-optimizer\src'
python -m hook_optimizer.cli --config editorial-brain\hook-optimizer\config\hook-optimizer.config.json --script editorial-brain\output\script-output-if-2026-07-06-liverpool-arsenal.json --brief editorial-brain\output\production-brief-if-2026-07-06-liverpool-arsenal.json
```

