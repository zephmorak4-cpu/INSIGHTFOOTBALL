# Voice Director

Reads `final-script-package.json` and creates `voice_plan.json`.

The module sets voice style, emotion, pace, pauses, emphasis words, and breathing points. It does not edit the approved script and does not generate audio.

Sample:

```powershell
python -m voice_director.cli --config editorial-brain/production/voice-director/config/voice-director.config.json --script-package editorial-brain/output/final-script-package.json
```
