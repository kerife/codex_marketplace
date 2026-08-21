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

- Sources: `schemas/career-market-learning-dossier-v1.schema.json`, `schemas/career-learning-decision-v1.schema.json`, and their build/validation scripts.
- Description: optional offline evidence and proof-to-cost decision sections composed inside v2. They are not standalone pages, routes, or network-backed widgets; unavailable market evidence produces no learning recommendation.

The exact HTML templates and CSS implementation are included in `layouts.md` and `theme.md` below.
