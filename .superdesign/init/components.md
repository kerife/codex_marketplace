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
- Description: long-form private career dossier shell rendered with scoped inline CSS and optional inline behavior.

The exact HTML templates and CSS implementation are included in `layouts.md` and `theme.md` below.
