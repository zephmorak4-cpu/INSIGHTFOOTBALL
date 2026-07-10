# Legacy Multi-Agent System Archive

The previous INSIGHT FOOTBALL production pipeline remains in the repository for reference, tests, and rollback.

Production no longer calls the multi-agent modules directly. The disabled legacy path includes:

- Match Selector
- Story Hunter
- Evidence Filter
- Insight Engine
- Editorial Orchestrator
- Editorial Validator
- Production Brief Generator
- Hook Optimizer
- CTA Generator
- Asset Planner
- Search Planner
- Graphic Planner
- learning and analytics production chain
- automatic match recommendation
- sample story fallbacks

The active production entrypoint is now:

```text
python scripts/render_daily_entrypoint.py
```

That entrypoint delegates to:

```text
python -m simple_mvp.run_production
```

Do not reconnect legacy modules to production unless the simple MVP is explicitly retired.
