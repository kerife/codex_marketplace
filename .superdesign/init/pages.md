# Page and artifact dependency trees

## Executive career dossier

- `plugins/professional-growth-coach/scripts/render_executive_career_dossier.py`
  - `plugins/professional-growth-coach/assets/executive-career-dossier-v1.html`
  - `plugins/professional-growth-coach/assets/executive-career-dossier-v1.css`
  - `plugins/professional-growth-coach/schemas/executive-career-dossier-v1.schema.json`
- `plugins/professional-growth-coach/scripts/render_executive_career_dossier_v2.py`
  - composes the v1 HTML shell with
    `plugins/professional-growth-coach/assets/executive-career-dossier-v2.css`
  - validates `plugins/professional-growth-coach/schemas/executive-career-dossier-v2.schema.json`
  - optionally composes validated market evidence and learning decisions from
    `career-market-learning-dossier-v1.schema.json` and
    `career-learning-decision-v1.schema.json`
  - alternatively composes the strict source-recomputed generation from
    `career-market-learning-dossier-v2.schema.json` and
    `career-learning-decision-v2.schema.json`; alignment is recomputed and
    provider research is accepted only with learning v2

The market and learning bundles are offline inputs to this dossier route, not
separate web pages. Their build/validation scripts are
`build_career_market_learning_dossier.py`, `validate_career_market_learning_dossier.py`,
`build_career_learning_decision.py`, and `validate_career_learning_decision.py`
for version 1, plus `build_career_market_learning_dossier_v2.py`,
`validate_career_market_learning_dossier_v2.py`,
`build_career_learning_decision_v2.py`,
`validate_career_learning_decision_v2.py`, and
`validate_career_learning_provider_research.py` for version 2.

## Recruiter reply triage

- `plugins/professional-growth-coach/scripts/render_private_recruiter_reply_triage.py`
  - `plugins/professional-growth-coach/assets/private-recruiter-reply-triage-v1.html`
  - `plugins/professional-growth-coach/assets/private-recruiter-reply-triage-v1.css`
  - `plugins/professional-growth-coach/scripts/private_prose_safety.py`

## Recruiter practice session

- `plugins/professional-growth-coach/scripts/render_recruiter_practice_session.py`
  - `plugins/professional-growth-coach/assets/recruiter-practice-session-v1.html`
  - `plugins/professional-growth-coach/assets/recruiter-practice-session-v1.css`
  - `plugins/professional-growth-coach/scripts/private_prose_safety.py`

## Compact conversion outcome

- `plugins/professional-growth-coach/scripts/render_private_recruiter_conversion_outcome.py`
  - `plugins/professional-growth-coach/assets/private-recruiter-conversion-outcome-v1.html`
  - `plugins/professional-growth-coach/assets/private-recruiter-conversion-outcome-v1.css`

## Compact follow-through checkpoint

- `plugins/professional-growth-coach/scripts/render_private_recruiter_followthrough_checkpoint.py`
  - `plugins/professional-growth-coach/assets/private-recruiter-followthrough-checkpoint-v1.html`
  - `plugins/professional-growth-coach/assets/private-recruiter-followthrough-checkpoint-v1.css`

Each tree ends at a self-contained HTML/CSS surface. The renderer is responsible for validated data-to-template binding; the artifact is the visual product.

## Private vacancy application packet

- `plugins/professional-growth-coach/scripts/render_private_vacancy_application_packet_v1.py`
  - accepts only `ValidatedPrivateVacancyPacket` from the same plugin package identity
  - reads `plugins/professional-growth-coach/assets/private-vacancy-application-packet-v1.html`
  - inlines `plugins/professional-growth-coach/assets/private-vacancy-application-packet-v1.css`
  - composes readiness, context, requirements/evidence, unsupported items, drafts, claim review, interview handoff, tracking proposal, approval boundary, and footer
  - replaces drafts/claim/handoff detail/tracking detail with one bounded suppression section for stop
  - atomically writes private mode-600 HTML through the existing packet writer boundary

The renderer contains no browser behavior or external resource path. Static structure and CSS modes are tested; browser visual, printed-page, and assistive-technology QA were not run.

## Executive career dossier v3 extension

- `plugins/professional-growth-coach/scripts/render_executive_career_dossier_v2.py`
  - validates `candidate-gap-response-v1.schema.json` and `candidate-gap-assessment-v1.schema.json`
  - recomputes `career-next-action-eligibility-v1.schema.json`
  - validates `career-learning-decision-v3.schema.json`
  - appends `plugins/professional-growth-coach/assets/career-learning-eligibility-v1.css` only for the coherent v3 WeeklyDecision composition

Response, assessment, eligibility, and learning v3 are one all-or-none offline
input group. Historical v1/v2 pages do not load the v3 stylesheet.
