# Scene Planner

Sprint 4 component 2. Refines `storyboard_draft.json` into `scene_list.json`, mapping scenes to approved templates and checking that CTA and dashboard scenes exist.

```powershell
$env:PYTHONPATH='editorial-brain\scene-planner\src'
python -m scene_planner.cli --config editorial-brain\scene-planner\config\scene-planner.config.json --storyboard editorial-brain\output\storyboard_draft.json --script-package editorial-brain\output\final-script-package.json
```

