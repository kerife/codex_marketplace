# Extractable components

## PrivateReceiptShell

- Source: `plugins/professional-growth-coach/assets/private-recruiter-conversion-outcome-v1.html`, `plugins/professional-growth-coach/assets/private-recruiter-followthrough-checkpoint-v1.html`
- Category: layout
- Description: compact receipt shell with skip link, title, fact grid, and continuity footer.
- Extractable props: `title`, `kicker`, `facts`, `employmentBoundary`, `locale`.
- Hardcoded: offline meta policy, card geometry, print rules, and accessibility landmarks.

## TriageReceipt

- Source: `plugins/professional-growth-coach/assets/private-recruiter-reply-triage-v1.html`
- Category: layout
- Description: decision-oriented recruiter triage artifact.
- Extractable props: `decision`, `evidence`, `handoff`, `boundary`, `locale`.
- Hardcoded: privacy-safe structure and no-action boundary.

## PracticeSession

- Source: `plugins/professional-growth-coach/assets/recruiter-practice-session-v1.html`
- Category: layout
- Description: preparation artifact for a bounded recruiter conversation.
- Extractable props: `prompt`, `rehearsal`, `evidence`, `nextAction`, `locale`.
- Hardcoded: private/offline presentation and manual re-entry rule.

## ExecutiveDossier

- Source: `plugins/professional-growth-coach/assets/executive-career-dossier-v1.html`
- Category: layout/composed v1-v2 surface
- Description: long-form scorecard and decision dossier. The v2 renderer composes market evidence, three CoachPriorityCard/DecisionTrace surfaces, and optional proof-to-cost LearningDecision cards into the same offline shell.
- Extractable props: validated dossier sections, optional validated market and learning bundles, and locale.
- Hardcoded: print, reduced-motion, contrast, and no-external-resource policies.

## DecisionTrace

- Source: `plugins/professional-growth-coach/scripts/render_executive_career_dossier_v2.py`
- Category: composed v2 subcomponent
- Description: four-step, market-only trace from priority to evidence, private template, and read-only inspection status. It is derived at render time and is not persisted as a separate schema or route.
- Extractable props: validated priority, dossier evidence, market group, and locale.
- Hardcoded: no raw evidence IDs, no external controls, one authorization question in the Decide ahora / Decide now summary.

## LearningDecision

- Source: `plugins/professional-growth-coach/schemas/career-learning-decision-v2.schema.json`, `plugins/professional-growth-coach/scripts/build_career_learning_decision_v2.py`, `plugins/professional-growth-coach/scripts/project_career_learning_decision_v2.py`, `plugins/professional-growth-coach/scripts/validate_career_learning_provider_research.py`, and `plugins/professional-growth-coach/scripts/render_executive_career_dossier_v2.py`; the v1 builder remains a supported compatibility source.
- Category: composed v2 subcomponent
- Description: optional ranked proof-and-cost cards. Each card contains a LearningSignalRoute plus localized option/owner, cost/time, expected boundary, lower-cost alternative, overbuying risk, decision, and next-action gate.
- Extractable props: validated and source-recomputed learning decision bundle plus locale; unavailable or zero-market inputs render no learning panel.
- Hardcoded: render only projected public fields; never render provider URLs, source/internal IDs, snapshots, raw source prose, or an external-action control.

## WeeklyDecision

- Source: `plugins/professional-growth-coach/scripts/render_executive_career_dossier_v2.py` and `plugins/professional-growth-coach/assets/career-learning-eligibility-v1.css`.
- Category: composed v3 subcomponent.
- Description: one full-width, non-interactive weekly decision after the condensed market summary. It presents a public vacancy/signal, exact evidence statement, one action, one deliverable, one done-when, and the fixed outcome/no-action boundary.
- Extractable props: validated eligibility public projection, validated public market vacancies, and locale; provider-selection state includes the complete non-ranked L1–Ln choice list.
- Hardcoded: unavailable renders no card; no forms, buttons, links, internal IDs, snapshots, URLs, source prose, raw enums, or caller-authored recommendation text.
