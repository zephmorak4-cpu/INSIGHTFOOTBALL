# Render Deployment Runbook

INSIGHT FOOTBALL can run on Render as a scheduled cron job.

## Service

The Render Blueprint is defined in:

```text
render.yaml
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
3. Generates the approval package.
4. Sends a Telegram approval request when Telegram secrets are configured.
5. Performs no live publishing.

## Required Render Environment Variables

Set these directly in Render, not in Git:

```text
TELEGRAM_BOT_TOKEN
TELEGRAM_APPROVAL_CHAT_ID
```

Optional but recommended:

```text
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
DAILY_INPUT_PATH=editorial-brain/examples/liverpool-arsenal-daily-input.json
```

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

