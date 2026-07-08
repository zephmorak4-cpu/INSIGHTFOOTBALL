# Visual Director

Sprint 6 component 1. Reads `final-storyboard-package.json` and `final-asset-package.json`, then writes `visual_plan.json`.

It defines scene templates, layouts, backgrounds, foreground assets, logo placement, dashboard usage, visual hierarchy, and safe-area notes. It does not generate images or render video.

```powershell
$env:PYTHONPATH='editorial-brain\creative\visual-director\src'
python -m visual_director.cli --config editorial-brain\creative\visual-director\config\visual-director.config.json --storyboard-package editorial-brain\output\final-storyboard-package.json --asset-package editorial-brain\output\final-asset-package.json
```

