# Render Deployment Runbook

INSIGHT FOOTBALL can run on Render as a scheduled cron job.

## Service

The Render Blueprint is defined in:

```text
render.yaml
```

FFmpeg is installed on Render through:

```text
Aptfile
```

It creates:

```text
insight-football-daily-production
```

Service type:

```text
cron
```

Schedule:

```text
0 9 * * *
```

That is **09:00 UTC**, which is **10:00 Africa/Lagos**.

## Runtime Behavior

The Render cron job runs:

```text
python scripts/render_daily_entrypoint.py
```

The entrypoint:

1. Runs the full regression suite.
2. Runs the daily dry-run production flow.
3. Refreshes the render package using `INSIGHT_FOOTBALL_RENDERER_PROFILE`.
4. Generates the approval package.
5. Sends a Telegram approval request when Telegram secrets are configured.
6. Attaches the real `final_video.mp4` when one exists.
7. Performs no live publishing.

## Required Render Environment Variables

Set these directly in Render, not in Git:

```text
TELEGRAM_BOT_TOKEN
TELEGRAM_APPROVAL_CHAT_ID
```

Optional but recommended:

```text
FFMPEG_BINARY_PATH
OPENAI_API_KEY
APP_FOOTBALL_API_KEY
NEWS_API_KEY
GNEWS_API_KEY
CREATOMATE_API_KEY
CREATOMATE_TEMPLATE_ID
```

Runtime controls:

```text
INSIGHT_FOOTBALL_ENV=production
INSIGHT_FOOTBALL_DRY_RUN=true
INSIGHT_FOOTBALL_REQUIRE_HUMAN_APPROVAL=true
INSIGHT_FOOTBALL_RUN_TESTS_ON_RENDER=true
INSIGHT_FOOTBALL_RENDERER_PROFILE=ffmpeg
DAILY_INPUT_PATH=editorial-brain/examples/liverpool-arsenal-daily-input.json
```

`FFMPEG_BINARY_PATH` is required when `ffmpeg` is not available on the Render PATH. The real MP4 renderer fails loudly instead of falling back to a placeholder video.

## GitHub Secrets For Render Deploys

If you want GitHub Actions to trigger a Render deploy manually, create a Render deploy hook for the cron job and add it to GitHub as:

```text
RENDER_DEPLOY_HOOK_URL
```

Then run:

```text
Render Deploy
```

from GitHub Actions.

## Approval Gate

Telegram receives the approval request, but production publishing is still blocked until a human manually runs:

```text
Approved Production Publish
```

with:

```text
approval_statement=APPROVED
```

Do not set `live_publish=true` until the render output is a real `.mp4` and all review warnings are cleared.

## Live Telegram Publishing After Approval

The manual GitHub workflow:

```text
Approved Production Publish
```

publishes Telegram only. This avoids blocking Telegram release on missing YouTube or Facebook credentials.

For a live Telegram publish, configure:

```text
TELEGRAM_BOT_TOKEN
TELEGRAM_CHANNEL_ID
```

Then run the workflow with:

```text
approval_statement=APPROVED
live_publish=true
```

The workflow sets:

```text
HUMAN_APPROVAL_CONFIRMED=true
```

The publisher will reject placeholder renders and only send a real `.mp4`.
