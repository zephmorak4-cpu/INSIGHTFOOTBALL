# Timing Engine

Sprint 4 component 3. Validates `scene_list.json`, creates `timeline.json`, and assembles `final-storyboard-package.json`.

It validates scene order, total duration, CTA timing, dashboard timing, caption fit, and vertical video metadata. It does not render video or plan assets beyond listing required references.

```powershell
$env:PYTHONPATH='editorial-brain\timing-engine\src'
python -m timing_engine.cli --config editorial-brain\timing-engine\config\timing-engine.config.json --scene-list editorial-brain\output\scene_list.json --voiceover editorial-brain\output\voiceover_final.txt
```

