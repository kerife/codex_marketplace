# Professional Growth Coach design system

## Purpose

Office-safe, evidence-first career review surfaces. The interface should make
the decision, safe next action, and boundary visible before secondary context.
It must remain useful when printed, viewed without external assets, or opened
with reduced motion and forced colors.

## Visual language

- Warm paper background with ink text and restrained forest/coral accents.
- Compact receipts use a centered shell, generous gutters, and one fact column
  through 640px; the second column begins at 641px.
- Cards and decision panels stay atomic in print and avoid relying on color
  alone for meaning.
- Focus indicators are explicit, high-contrast, and preserved in forced colors.

## Interaction and content rules

- Every surface has one skip link and one focusable `main#main-content` target.
- Safe next steps and employment boundaries are visible, printable, and never
  replaced by an external navigation dependency.
- Copy is evidence-safe: no private identifiers, local user paths, or secrets
  appear in diagnostics or public examples.
- No external fonts, scripts, or icon services are required by shipped assets.

## Fidelity contract

The shipped HTML/CSS assets under `plugins/professional-growth-coach/assets/`
are the source of truth. `.superdesign/init/layouts.md` and
`.superdesign/init/theme.md` mirror those files byte-for-byte where marked;
parity tests must fail if either artifact drifts.

The composed market region is source-aware and all-or-none: its derived market
dossier, normalized research, and identity-free alignment must validate
together before any market UI renders. Legacy dossier renders with no optional
market inputs keep the existing generic placeholder. A validated unavailable
bundle instead shows its bounded limitation without exposing snapshots, URLs,
referrers, internal vacancy/employer/evidence/requirement IDs, raw requirement
paraphrases, or inferred eligibility.

Vacancy alignment uses one native `progress` per vacancy, labelled by the
vacancy heading, its visible `N de 100` / `N out of 100` score, evidence
coverage percentage, and localized qualitative band. Coverage and band are
descriptive evidence metadata, never a hiring probability. Recurrence
uses a second native progress family labelled by the visible signal and exact
`k/N` fraction; this always describes the validated sample only. The semantic
matrix keeps a caption, scoped row/column headers, stable header relationships,
short V1–VN headers with visually hidden full labels, and a complete adjacent
key. Every state combines a visible symbol and text. At 680px and below, the
table remains in the DOM while rows stack; vacancy cells use short V1–VN
`data-label` values while the adjacent key and semantic headers retain full
employer/title labels, avoiding repeated long names in the mobile scan. The
header is visually clipped, never removed. Print restores the table/header-group
display model and keeps the full vacancy key with the table.
Dark, grayscale, high-contrast, and forced-colors modes preserve the same text
and symbols without color-only meaning. The four-stage gap route remains a
non-interactive evidence workflow and recommends no course or certification
while `learning_state=not_evaluated`.
