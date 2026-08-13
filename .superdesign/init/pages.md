# Page and artifact dependency trees

## Executive career dossier

- `plugins/professional-growth-coach/scripts/render_executive_career_dossier.py`
  - `plugins/professional-growth-coach/assets/executive-career-dossier-v1.html`
  - `plugins/professional-growth-coach/assets/executive-career-dossier-v1.css`
  - `plugins/professional-growth-coach/schemas/executive-career-dossier-v1.schema.json`

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
