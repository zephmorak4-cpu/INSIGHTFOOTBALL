# Storyboard Generator

Sprint 4 component 1. Converts `final-script-package.json` and `voiceover_final.txt` into `storyboard_draft.json`.

It preserves the final script exactly, creates scene timing, captions, on-screen text, visual treatment notes, and required asset references. It does not create assets or render video.

```powershell
$env:PYTHONPATH='editorial-brain\storyboard-generator\src'
python -m storyboard_generator.cli --config editorial-brain\storyboard-generator\config\storyboard-generator.config.json --script-package editorial-brain\output\final-script-package.json --voiceover editorial-brain\output\voiceover_final.txt
```

