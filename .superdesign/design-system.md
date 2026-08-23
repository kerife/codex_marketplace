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

The composed market region is source-aware, generation-strict, and all-or-none.
Version 1 requires its derived market dossier, normalized research, and supplied
identity-free alignment; optional learning must also be version 1. Version 2
requires its market dossier and normalized research, recomputes alignment, and
accepts independently validated provider research only with a version 2 learning
decision. Mixed, crossed, and incomplete groups fail before any market UI
renders. Legacy dossier renders with no optional market inputs keep the existing
generic placeholder. A validated unavailable bundle instead shows its bounded
limitation and one localized safe next step, without exposing snapshots, URLs,
referrers, internal vacancy/employer/evidence/requirement IDs, raw requirement
paraphrases, or inferred eligibility; it makes no external action.

Complete and limited market summaries expose one localized, validated research
date before the learning boundary so the client can judge evidence freshness;
unavailable and legacy no-market states expose no date marker.
Limited market summaries additionally expose the visible sample limitation
before the learning state and as the region description; complete, unavailable,
and legacy no-market states do not claim that limitation.

When a read-only section inspection is pending, Decide now names the visible
priorities that the inspection may inform before asking the single localized
authorization question. If no priority targets that section, it states that the
inspection completes visible coverage and that reprioritization requires a
separate review. With no pending inspection, no impact block or authorization
question is rendered.

The learning decision boundary appears before the cards, and every learning
card references the shared boundary with `aria-describedby`. The localized,
visible boundary remains printable and does not predict an interview, offer,
salary, or return on investment.

LearningSignalRoute is a compact group inside each validated version 2 learning
card. It renders one row per source signal with only the validated public term
label, localized support state, public vacancy ordinals, and exact recurrence;
the card adds the source-recomputed decision basis and localized decision label.
It exposes no internal IDs, snapshots, URLs, source prose, or raw enums. Group
and row labels resolve through unique ARIA references, while the inherited card
and proof styles preserve the same mobile, print, dark, and forced-colors
contracts. Version 1 cards, unavailable market evidence, and legacy no-market
output keep their prior behavior.

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

## Vacancy-first weekly decision v3

Career-learning-decision v3 adds one full-width WeeklyDecision card immediately
after the condensed market card in Decide now. It is the sole primary weekly
imperative; the existing read-only inspection authorization stays visibly
secondary and remains a separate permission question. The later learning panel
appears only for the one eligibility-authorized decision and is not relocated.

The renderer captures dossier, market, research, optional provider, response,
assessment, eligibility, and learning together in one bounded snapshot before
schema access. Partial, mixed, stale, and crossed groups fail before CSS or
template reads. Version 1, version 2, unavailable-market, and legacy no-market
bytes retain their historical composition.

WeeklyDecision exposes only a public Vn plus title/employer, selected signal,
exact recurrence, closed localized evidence copy, one action, private
deliverable, done-when, and the visible no-outcome/no-external-action boundary.
Only `selection_required` adds exactly two internal navigation links, to the
vacancy key and signal matrix; the card has no external links or controls.
Provider-selection state renders the complete non-ranked L1–Ln list. The card
uses stable labelled/described relationships, one-column mobile wrapping,
atomic print rules, dark tokens, forced system colors, and reduced-motion-safe
static content. visual QA not run; deterministic DOM/CSS contract only.
