# INSIGHT FOOTBALL Editorial Brain

Sprint 1 scope:

```text
Daily Input JSON
-> Match Selector
-> Story Hunter
-> Evidence Filter
-> Insight Engine
-> Editorial Production Package
```

This folder is for the first working Editorial Brain only.

Not included:

- Scriptwriting.
- Storyboarding.
- Visual rendering.
- Publishing.
- n8n or Make.com workflows.
- YouTube, Facebook, or Telegram integrations.

See the full implementation guide:

```text
../blueprints/INSIGHT_FOOTBALL_Sprint_1_Editorial_Brain_Implementation.md
```

## Folder Purpose

```text
match-selector/    Agent 1 contract and future implementation.
story-hunter/      Agent 2 contract and future implementation.
evidence-filter/   Agent 3 contract and future implementation.
insight-engine/    Agent 4 contract and future implementation.
shared/            Shared schemas, validation rules, locked-field rules.
schemas/           Final Editorial Production Package schema.
config/            Sprint 1 model, retry, validation, and execution config.
examples/          Liverpool vs Arsenal sample input and run notes.
tests/             Testing strategy and future tests.
output/            Generated Editorial Production Packages.
logs/              Pipeline logs.
```

## Success Criteria

- Four agents execute in sequence.
- Validation stops bad data.
- Locked fields are preserved.
- Final package validates.
- Story angle remains unchanged after Story Hunter.
- Confidence and human review flags are preserved.
