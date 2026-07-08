# Camera Planner

Creates virtual camera instructions from `visual_plan.json`. It only uses approved camera moves and does not render video.

```powershell
$env:PYTHONPATH='editorial-brain\creative\camera-planner\src'
python -m camera_planner.cli --config editorial-brain\creative\camera-planner\config\camera-planner.config.json --visual-plan editorial-brain\output\visual_plan.json
```

