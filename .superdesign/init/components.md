# Shared UI components

This repository is a Python-rendered, offline HTML/CSS plugin rather than a JavaScript application. It has no React/Vue component library. The reusable visual units are server-rendered HTML fragments and CSS surfaces.

## PrivateReceiptShell

- Source templates: `plugins/professional-growth-coach/assets/private-recruiter-conversion-outcome-v1.html`, `plugins/professional-growth-coach/assets/private-recruiter-followthrough-checkpoint-v1.html`
- Description: compact, single-page decision receipt with skip link, title, facts, and continuity footer.
- Inputs: renderer-local labels and validated facts; no network data.

## TriageShell

- Source template: `plugins/professional-growth-coach/assets/private-recruiter-reply-triage-v1.html`
- Description: private recruiter reply triage receipt with decision, evidence, handoff, and boundary sections.

## PracticeSessionShell

- Source template: `plugins/professional-growth-coach/assets/recruiter-practice-session-v1.html`
- Description: private practice-session artifact with prompt, evidence, rehearsal, and next-action sections.

## ExecutiveDossierShell

- Source template: `plugins/professional-growth-coach/assets/executive-career-dossier-v1.html`
- Description: long-form private career dossier shell rendered with scoped inline CSS and optional inline behavior. The v2 renderer composes this same shell with the v2 CSS extension and validated market/learning sections.

## CoachPriorityCard and DecisionTrace

- Source: `plugins/professional-growth-coach/scripts/render_executive_career_dossier_v2.py` and `plugins/professional-growth-coach/assets/executive-career-dossier-v2.css`
- Description: three market-aware coaching priority cards. Each DecisionTrace presents priority, localized evidence state/paraphrase, a private blank template, and read-only inspection status; it never exposes evidence IDs or authorizes an external action.
- Inputs: validated v2 dossier plus a validated market group. The trace is omitted on the protected no-market path.

## MarketEvidence and LearningDecision

- Sources: `plugins/professional-growth-coach/schemas/career-market-learning-dossier-v2.schema.json`, `plugins/professional-growth-coach/schemas/career-learning-decision-v2.schema.json`, `plugins/professional-growth-coach/scripts/build_career_market_learning_dossier_v2.py`, `plugins/professional-growth-coach/scripts/build_career_learning_decision_v2.py`, `plugins/professional-growth-coach/scripts/project_career_learning_decision_v2.py`, `plugins/professional-growth-coach/scripts/validate_career_learning_provider_research.py`, and `plugins/professional-growth-coach/scripts/render_executive_career_dossier_v2.py`. The v1 schemas and builders remain supported by the same renderer compatibility boundary.
- Description: optional offline market evidence and ranked proof-and-cost decision cards composed inside the executive dossier. The v2 builder recomputes its market/alignment joins from validated sources, requires the provider research to share the normative source date, and projects the visible learning copy rather than accepting caller-authored recommendation prose.
- LearningSignalRoute: a compact per-signal proof route inside each LearningDecision showing only a validated public term label, localized support state, public vacancy ordinals, and recurrence. The surrounding card shows the localized option/owner, proof and cost, expected boundary, lower-cost alternative, overbuying risk, coach decision, and next-action gate.
- Privacy boundary: no source URLs, internal IDs, snapshots, or raw source prose are rendered. These components are not standalone pages, routes, or network-backed widgets; unavailable market evidence produces no learning recommendation.

The exact HTML templates and CSS implementation are included in `layouts.md` and `theme.md` below.

## WeeklyDecision

- Sources: `plugins/professional-growth-coach/schemas/career-next-action-eligibility-v1.schema.json`, `plugins/professional-growth-coach/schemas/career-learning-decision-v3.schema.json`, `plugins/professional-growth-coach/scripts/render_executive_career_dossier_v2.py`, and `plugins/professional-growth-coach/assets/career-learning-eligibility-v1.css`.
- Description: the sole primary weekly imperative inside Decide now, after the market summary and before the later detailed learning surface. The read-only inspection authorization remains a separate visibly secondary card. The `gap_unknown` variant adds a localized, non-interactive seven-relation unordered group after evidence and before that existing action.
- Inputs: one source-recomputed eligibility artifact plus validated public market projection; v3 response, assessment, eligibility, and learning are all-or-none.
- Privacy boundary: only public Vn/Ln ordinals and escaped public labels render. No internal ID, snapshot, URL, source prose, raw enum, control, or external link is exposed; the relation group is fixed localized copy rather than a response control.
