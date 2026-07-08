# Voice Provider Abstraction

Defines the Sprint 7 provider contract without generating audio.

Required methods:

- `generate_voice()`
- `list_voices()`
- `validate_ssml()`
- `estimate_duration()`

Supported compatibility adapters: Google Cloud TTS, Azure Speech, ElevenLabs, OpenAI TTS, Cartesia, and PlayHT.
