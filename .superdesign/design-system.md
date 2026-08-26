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

## Private vacancy application packet

The approved packet is implemented as a compact 920px editorial shell using
the existing paper, white surface, ink, forest, coral, line, system-sans, and
Georgia token family. It does not inherit the dossier grid, example facts, or
wide shell. The source assets are
`plugins/professional-growth-coach/assets/private-vacancy-application-packet-v1.html`
and `.css`; the renderer is
`plugins/professional-growth-coach/scripts/render_private_vacancy_application_packet_v1.py`.

The reading order is fixed: private/draft header; one readiness decision;
public vacancy context; requirement/evidence cards; unsupported items; private
drafts; claim review; first-interview handoff; proposed tracking; approval
boundary; footer. Stop replaces drafts, claim review, and detailed handoff and
tracking with one bounded suppression section. The document exposes one `h1`,
an explicitly labelled focusable main landmark, labelled sections/articles,
definition lists, semantic lists, and one captioned claim table with scoped
headers and stable local row IDs.

Only the same-package opaque validated snapshot can reach rendering. Visible
dynamic content is limited to closed localized templates and catalog labels,
validated packet projections, and escaped public vacancy title, organization,
and date. Internal IDs, snapshots, digests, paths, URLs, raw enums, source
prose, signal bindings, forms, buttons, scripts, and external assets are not
rendered. The HTML carries CSP, noindex, and no-referrer metadata; CSS includes
dark, forced-colors, reduced-motion, 640px mobile, print atomicity, and a
repeated print privacy/authorization boundary. Browser visual QA, printed-page
QA, and assistive-technology QA were not run; evidence is limited to static and
deterministic renderer tests.

## Learning proof sprint

The learning-proof-sprint-v1 surface reuses the practice/triage green-coral
token family as a five-day private timeline. Its first reading unit is the
static `Start here` / `Empieza aquí` card: action, timebox, review gate,
progress, and private reuse destination appear before the detailed timeline.
Closed contract values are localized into human copy at render time; unknown
values remain escaped fallback text. The surface stays offline, draft-only,
non-interactive, and preserves mobile, print, dark, forced-colors, and reduced-
motion behavior. Browser, print, and assistive-technology QA were not run.

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
vacancy key and signal matrix. Its localized help first directs the customer to
choose one public Vn, then a signal belonging to that same active vacancy; the
card has no external links or controls.

The exact normalized selection help is:

- ES: `Primero, elige una vacante Vn en la clave de vacantes. Después, para esa misma vacante activa, elige una señal en la matriz de señales.`
- EN: `First, choose a vacancy Vn in the vacancy key. Then choose a signal in the signal matrix for that same active vacancy.`

Provider-selection state renders the complete non-ranked L1–Ln list. The card
uses stable labelled/described relationships, one-column mobile wrapping,
atomic print rules, dark tokens, forced system colors, and reduced-motion-safe
static content. For `insufficient_gap_evidence` with the `unknown` relation and
the `confirm_gap_relation` action only, a non-interactive unordered relation
group follows the evidence statement and precedes the existing action. Its
localized heading is the group's stable accessible label; it is not added to
the card description. visual QA not run; deterministic DOM/CSS contract only.

## Private first-interview conversion board

`PrivateFirstInterviewConversionBoard` is a decision-first, offline product
surface for the explicit private branch after recruiter triage and before
manual interview preparation. The 920px editorial shell uses the shared
`practice_triage` palette and places current state, next safe action, and the
no-outcome boundary above the sequence. It then composes at most three proof
cards, five risk topics, one rehearsal, seven days, four decision branches,
and seven review templates; `stop` suppresses detail and tracking.

The artifact is identity-free, draft-only, source-bound, and has no controls,
network resources, or external action. Static parity covers responsive 640px,
print, dark, forced-colors, and reduced-motion hooks. visual QA not run;
deterministic DOM/CSS contract only.

## Private first-interview provenance boundary v2

The v2 board is a sanitized, proof-only extension of the frozen v1 board. The
decision remains the first reading unit. Exactly one `board-trust-strip` follows
it before the sequence: it labels synthetic test input or composition-only
provenance, states that original text is not stored, and preserves the manual
review requirement. It deliberately renders no digest, provenance/source ID,
raw source prose, URL, control, or external action. `stop` retains the decision,
trust strip, and approval boundary while omitting all preparation detail.

The 920px practice-triage surface preserves the skip link, focusable labelled
main landmark, semantic section labels, `minmax()` review layout, one-column
mobile reset, intermediate-width layout, print atomicity, dark mode,
forced-colors treatment for both trust and approval boundaries, and
reduced-motion handling. Browser visual QA, printed-page QA, and
assistive-technology QA are not run or claimed; evidence is deterministic
DOM/CSS testing only.

The header also exposes the artifact's `as_of_date` once as a localized
“Reference date”/“Fecha de referencia” beside the state, using a semantic ISO
`time` value. It describes the evidence cutoff only; it must not be labelled as
“updated”, “current”, or “valid through”, and it never exposes provenance IDs,
digests, or source text. The date remains visible for `stop`, mobile, print,
dark, and forced-colors presentations.

The practice handoff keeps the board static and proof-first. A ready board
uses the coral practice checkpoint treatment and a later-request cue; clarify
uses a forest-soft checkpoint that asks for the missing fact; pause uses a
paper checkpoint that signals manual review; stop omits the checkpoint and all
preparation detail. State modifiers are carried in a non-executable data
attribute so CSS can distinguish them without exposing raw enums as copy.
Print, dark, forced-colors, reduced-motion, and offline contracts remain
unchanged. Visual/browser/assistive-technology QA is not run or claimed.

The answer-feedback continuation closes the loop without adding a form or a
control: the reading order is question, next step, answer structure, feedback,
decision, evidence boundary, then the compact practice-origin receipt. One
localized categorical signal is shown, with the score remaining unknown; raw
answer text, internal identifiers, and snapshot metadata never enter the
document. The origin receipt is deliberately secondary to the action and
review, while the same print, dark, forced-colors, reduced-motion, and offline
boundaries remain in force. Visual/browser/assistive-technology QA is not run
or claimed.
The session also exposes a three-step semantic progress track
(`prepare`, `answer`, `review`) with one `aria-current="step"`. A second
attempt adds a localized final-attempt notice, and its terminal feedback card
closes the cycle without inviting a third rehearsal.
In forced-colors mode, the current progress step keeps a system `Highlight`
outline so its location remains visible without relying on color differences.
The practice skip link uses the same system `Highlight` outline on focus, while
its `Canvas`/`CanvasText` surface remains visible before focus moves to `main`.
The chat summary mirrors that closure with a short terminal message while
keeping answer text and provenance metadata out of the summary.
Independent sessions keep the next-step instruction aligned with the closed
question kind; `missing_detail` asks for one bounded clarification instead of
the generic context/action/result sequence. Sourced sessions continue to point
back to the private originating conversation.
Ready boards and awaiting sessions use a compact re-entry capsule for the one
private next action; it remains static, localized, and absent from blocked or
terminal states. The ready capsule presents the bounded context/action/result
shape as a three-step visual recipe; it is guidance only and never collects or
stores a response.
The visual layer renders closed risk, quality, score, authorization, and
prohibited-action enums as localized human labels; unsupported values stay out
of the UI through a generic fail-closed diagnostic.
Long boards use a restrained localized section-navigation strip for scanning;
it disappears in print and preserves the static, private boundary.
The strip links every detailed section and targets headings prepared for
keyboard and assistive-technology navigation, with
touch-sized links that wrap cleanly on narrow screens. The selected heading
gets a visible `:target` outline for orientation; because the artifact is
static and script-free, the fragment link does not claim automatic focus
transfer.
