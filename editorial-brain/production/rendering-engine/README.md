# Rendering Engine

Sprint 10 converts `renderer-ready-package.json` into render job/status/artifact packages.

## Real MP4 Renderer

The `ffmpeg` renderer generates a real 9:16 `final_video.mp4`.

It applies the mandatory INSIGHT FOOTBALL Brand Motion Standard:

- 1.5-second opening sting.
- Persistent corner logo.
- 0.3-second transition stings.
- Branded panels and lower thirds.
- 4-second end card.

Requirements:

```text
ffmpeg
```

or:

```text
FFMPEG_BINARY_PATH=/absolute/path/to/ffmpeg
```

If FFmpeg is missing, the adapter fails clearly instead of producing a fake MP4.

The placeholder renderer remains available for contract tests and dry documentation, but it is not a publishable video renderer.
