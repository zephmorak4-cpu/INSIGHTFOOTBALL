# Editorial Brain Sprint 1 Test Plan

## Unit Tests

- Match Selector output has one selected match.
- Story Hunter output has one story angle, one central question, and one surprising fact.
- Evidence Filter output has 3 to 5 evidence points.
- Insight Engine probabilities total 100 when probabilities are present.
- Every agent output includes confidence.
- Every agent output includes human_review_flags.

## Pipeline Tests

- Valid Liverpool vs Arsenal input reaches final package.
- Agent execution order is IF-A01, IF-A02, IF-A03, IF-A04.
- Final package validates against editorial-production-package schema.

## Validation Tests

- Missing production_id stops pipeline.
- Missing selected_match stops pipeline.
- Missing central_question stops pipeline.
- Evidence with fewer than 3 points stops pipeline.
- Confidence below 70 stops pipeline.
- Locked-field mutation stops pipeline.

## Failure Tests

- Story Hunter returns weak story and confidence 62.
- Evidence Filter changes central question.
- Insight Engine uses unsupported invented statistic.
- Insight Engine probabilities total 105.
- Agent returns invalid JSON.

## Edge Cases

- Popular match with weak story.
- Low-profile match with strong story.
- Balanced evidence with no clear edge.
- Injury-based story with unverified injury.
- Missing betting market.

## Recovery Tests

- Story Hunter v2 after weak angle.
- Evidence Filter requests additional data.
- Insight Engine sends back unsupported dashboard.
- Human review required status is preserved.
