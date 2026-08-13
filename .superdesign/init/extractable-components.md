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
- Category: layout
- Description: long-form scorecard and decision dossier.
- Extractable props: validated dossier sections and locale.
- Hardcoded: print, reduced-motion, contrast, and no-external-resource policies.
