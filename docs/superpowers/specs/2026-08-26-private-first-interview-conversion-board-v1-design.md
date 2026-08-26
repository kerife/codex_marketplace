# Private First-Interview Conversion Board v1

## Status

Approved architectural design for the next plugin increment. The artifact is
private, offline, source-bound, draft-only, and never an authorization to
message, connect, apply, publish, or schedule.

## Goal

Turn the existing textual `first_interview_7_day_plan` contract into one
reusable private JSON/HTML decision board without duplicating or weakening the
existing recruiter and interview-preparation routes.

## Scope and non-goals

In scope:

- A versioned `private-first-interview-conversion-board-v1` schema, identity,
  deterministic builder, validator, private writer, renderer, HTML, and CSS.
- A source-bound projection of one validated recruiter-outreach/first-interview
  group into a customer-readable ES/EN board.
- Exact cardinalities: one decision summary, seven plan days, four decision
  branches, and seven daily review templates.
- Static and security tests, fixtures, package inventory, privacy checks,
  Superdesign references, and installed-release evidence.

Out of scope:

- LinkedIn or Chrome access, recruiter discovery, messaging, connection,
  application, calendar, upload, purchase, enrollment, or any other external
  action.
- Raw recruiter replies, candidate identity, contact details, private vacancy
  identifiers, source URLs, or source snapshots in the rendered artifact.
- Numeric interview probability, fit score, causal lift, ranking, salary,
  eligibility, availability, or guaranteed outcome.
- Changing the existing textual networking contract or ordinary
  `prepare-role-interviews`, recruiter-triage, or packet-routing behavior.

## Architecture

The board is a projection layer over an existing validated source group. The
caller supplies no final board rows. A builder accepts one complete, same-group
validated composition containing the recruiter outreach lab, its quality gate,
and the seven-day first-interview plan. It recomputes the public projection,
freezes it into a private proof object, and returns that opaque object only
after schema, source, privacy, and safety validation.

The validator re-computes the projection from the frozen source group and
compares canonical JSON before any asset or output path is read. The renderer
accepts only the exact validator-issued proof-object class. The writer uses the
existing descriptor-anchored private-output pattern and creates mode-600 HTML
atomically with no partial output on failure.

## Source contract and projection

The input must contain the existing contract rows from
`skills/optimize-professional-profile/references/networking-and-content.md`:

- one `recruiter_outreach_lab` and its selected target/quality context;
- one `linkedin_outreach_quality_gate` and its three quality checks;
- one `first_interview_7_day_plan`;
- one `first_interview_weekly_coach_plan`;
- four `first_interview_decision_ladder` rows;
- seven `interview_plan_day` rows;
- seven `first_interview_daily_review_log` rows.

The builder emits these public sections:

1. `decision`: localized objective, current state, next safe private action,
   one descriptive signal, and the visible no-outcome boundary.
2. `sequence`: closed stages `current_state`, `private_preparation`,
   `human_review`, and `authorization_gate`; this is explanatory text, not a
   control or workflow executor.
3. `proof_cards`: at most three validated public proof signals, each with a
   vacancy signal label, supported evidence summary, and caveat. Internal IDs
   and source prose are removed.
4. `risk_checks`: the closed risk topics `production`, `compensation`,
   `eligibility`, `availability`, and `confidentiality`; each has a trigger
   question, safe response boundary, confirmation need, and forbidden claim.
5. `rehearsal`: one traceable private question, purpose, response structure,
   and wait-for-response boundary. Pre-response score remains `unknown`.
6. `week`: exactly seven projected days with private action, evidence/asset
   boundary, review checkpoint, observable signal, fallback, and stop rule.
7. `decision_ladder`: exactly four branches in order `advance`, `clarify`,
   `pause`, `stop`, with trigger, evidence requirement, next safe action,
   blocked action, measurement label, review question, and script boundary.
8. `daily_reviews`: exactly seven templates keyed by day 1 through 7, with
   observed signal, signal quality, decision, evidence log, next safe action,
   metric label, confounder note, and coach question.
9. `approval_boundary`: fixed private-review wording and prohibited actions.

The `stop` state emits the decision and boundary only. It must suppress proof
cards, rehearsal detail, detailed week actions, and tracking detail. `ready`,
`clarify`, and `pause` retain the corresponding private review surfaces but
never authorize execution.

## Closed states and safety rules

The source decision is fail-closed:

- `ready` requires confirmed stage and role context, supported facts, and no
  unresolved critical constraint; it still means manual private review only.
- `clarify` means role scope, evidence, eligibility, availability,
  compensation, or another critical constraint is missing.
- `pause` means no useful signal, weak target context, or an unapproved wait
  window.
- `stop` means decline, closed role, unsupported/confidential claims, missing
  authorization, or generic-outreach drift.

Every emitted artifact includes the fixed booleans:

```text
draft_only=true
external_actions_authorized=false
no_message_action=true
no_calendar_action=true
raw_event_retained=false
raw_reply_retained=false
raw_answer_retained=false
local_save_mode=disabled
candidate_review_required=true
```

No source-controlled text is rendered without escaping. The public projection
may include only closed labels, bounded localized copy, and validated fact
summaries. PII, secrets, HTML, control characters, URLs, paths, prompt-
injection text, internal IDs, snapshot digests, and raw recruiter/candidate
prose are rejected or omitted before the proof object exists.

## Visual product

The board uses the existing `practice_triage` token family and the saved
Superdesign editorial direction. The reading order is:

1. private/draft header and public vacancy label/date only;
2. one primary decision card with current state, next safe action, and boundary;
3. a four-stage static sequence;
4. proof cards (maximum three);
5. risk-check matrix;
6. private rehearsal card;
7. seven-day timeline and daily review templates;
8. repeated approval boundary and footer.

The HTML has one `h1`, a skip link, focusable `main#main-content`, unique
section headings, definition lists/ordered lists, and no forms, buttons,
scripts, external links, or network resources. Text and symbols convey state;
color is never the only signal. CSS must preserve mobile stacking at 640px,
print atomicity, dark mode, forced colors, reduced motion, and a repeated
private boundary in print. Empirical browser, print-preview, and
assistive-technology QA are not part of this release unless a valid visual
runtime becomes available.

## Interfaces

The implementation follows the existing plugin naming conventions:

- `build_private_first_interview_conversion_board_v1(source_group: object) -> ValidatedPrivateFirstInterviewConversionBoard`
- `validate_private_first_interview_conversion_board_v1(source_group: object) -> ValidatedPrivateFirstInterviewConversionBoard`
- `write_private_first_interview_conversion_board_v1(validated_board: object, output: Path, *, force: bool = False) -> WriteReceipt`
- `render_private_first_interview_conversion_board_v1(validated_board: object) -> str`

The validator-issued class is the only accepted renderer input. Public helper
functions may return bounded diagnostics but never echo source values.

## Error handling and file boundaries

Validation fails before template/CSS reads for incomplete, crossed, stale,
mutated, duplicate, oversized, cyclic, unsafe, or caller-authored inputs. The
asset loader must read only regular package-local files through its existing
`O_NOFOLLOW`/descriptor boundary. The writer creates a private parent, uses an
exclusive temporary file, flushes and fsyncs, atomically replaces the target,
and rejects symlink/non-regular targets. Invalid input leaves no output file.

## Testing and release gates

Tests must cover:

- ES and EN accepted fixtures with exact 1/7/4/7 cardinalities;
- source crossing, stale/mutated snapshots, duplicate or extra rows, caller
  supplied final rows, invalid states, and missing dependencies;
- PII, secrets, URLs, HTML, control characters, prompt injection, send,
  calendar, fit, probability, guarantee, salary, eligibility, and availability
  language rejection with generic bounded errors;
- validator-issued object identity, renderer no-echo, deterministic bytes,
  stop suppression, writer mode 600, symlink rejection, and no partial output;
- semantic HTML, CSP/noindex/no-referrer, token allowlist, responsive/print/
  dark/forced/reduced hooks, and Superdesign reference parity;
- package static checks, repository privacy, source/cache parity, installed
  semantic smokes, attestation binding, and historical artifact compatibility.

The release must not claim browser or assistive-technology QA without direct
runtime evidence.

## Documentation updates

Update the plugin README and routing guidance with the explicit private board
branch, add the artifact to `.superdesign/design-system.md`, `layouts.md`,
`pages.md`, `components.md`, `theme.md`, and any extractable-component index,
and record the release in the installed smoke attestation. Existing textual
contracts remain the source-of-truth and must continue to pass unchanged.

## Acceptance decision

This design is accepted when the builder/validator/renderer/writer and tests
prove the source-bound, private, offline, non-interactive, fail-closed behavior
above, and the exact release is pushed to `origin/main`, installed in Codex,
and verified by source/cache parity and installed smokes.
