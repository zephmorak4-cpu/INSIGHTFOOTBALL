# CTA Generator

Sprint 3 component 3. The CTA Generator receives the optimized script and production brief, creates CTA options, selects the strongest engagement question, and writes:

- `cta-output-<production_id>.json`
- `final-script-output-<production_id>.json`
- `final-script-package.json`
- `voiceover_final.txt`

It rejects generic engagement prompts, betting CTAs, and scripts over 60 seconds.

```powershell
$env:PYTHONPATH='editorial-brain\cta-generator\src'
python -m cta_generator.cli --config editorial-brain\cta-generator\config\cta-generator.config.json --script editorial-brain\output\optimized-script-output-if-2026-07-06-liverpool-arsenal.json --brief editorial-brain\output\production-brief-if-2026-07-06-liverpool-arsenal.json
```

