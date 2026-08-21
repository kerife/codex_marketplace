# Coach Decision Trace for Executive Career Dossiers

## Status

Approved for implementation as the next bounded product increment. The design
is derived from already validated dossier data; it does not introduce a new
persisted schema or a second provenance ledger.

## Problem and outcome

The current priority cards expose observation, rationale, prompt, and a private
template as separate fields. A client can see each fact, but cannot quickly
understand how the priority connects to its evidence, the next private draft,
and any read-only inspection consent. The increment adds a compact decision
trace inside each existing priority card:

1. **Prioridad** — rank and target section.
2. **Evidencia disponible** — localized state and a safe paraphrase of each
   validated evidence record.
3. **Plantilla privada** — the existing context/action/result blanks.
4. **Permiso de lectura** — the section inspection state and, only when
   pending, the existing exact authorization question.

The trace is a renderer projection only. It is not persisted, copied into the
market bundle, or sent to an external service.

## Scope and compatibility

- Render the trace only when a validated market dossier is composed. Preserve
  the byte-identical v2 no-market output and the v1 renderer/output.
- Reuse the existing priority, evidence, section-coverage, and authorization
  contracts. Do not add `decision_trace` to a schema, builder, handoff, or
  snapshot in this increment.
- Keep one authorization question at most. A pending question must remain
  read-only, current-session-only, and `carry_forward=false`; it must never
  imply permission to edit, publish, message, apply, or purchase.
- Declined, failed, absent, or unavailable inspection states must render a
  bounded status and no question. Do not infer eligibility, ownership, hiring
  outcomes, or missing evidence.
- If an evidence ID cannot resolve to the target section, fail closed with a
  generic diagnostic before writing HTML. Do not echo IDs, capture references,
  paths, URLs, emails, or raw private profile text.

## Presentation contract

Each priority card receives one labelled `section.decision-trace` with a
generated DOM id based only on rank. Its ordered list contains four stable
steps and no external controls:

- `decision-trace-priority-{rank}`: localized target-section label.
- `decision-trace-evidence-{rank}-{ordinal}`: localized evidence state and
  escaped, privacy-filtered paraphrase; never show the source ID.
- `decision-trace-template-{rank}`: the existing private field blanks.
- `decision-trace-inspection-{rank}`: inspected-present/absent,
  candidate-supplied, unavailable, declined, failed, or pending response.

The pending response must use localized status copy and a single internal link
to the existing Decide ahora authorization card; it must not repeat the literal
authorization question in every priority card. The exact question remains
unique in the authorization card and chat summary. Each card must include a
visible boundary that no external action is executed and that any later
external action needs separate authorization.

CSS must remain fluid at mobile widths, avoid positive fixed grid minima, keep
cards atomic for print, and provide equivalent Canvas/CanvasText/Highlight
colors for forced-colors, dark-mode parity, and reduced-motion behavior.

## Data flow and failure behavior

`render_dossier_html()` validates and projects the existing market group, then
derives an immutable trace per priority. The projection resolves evidence and
section coverage through existing helpers, applies the shared privacy/prose
guards to every visible paraphrase, and passes only escaped display strings to
the HTML builder. Invalid explicit market or trace inputs raise the existing
bounded dossier-validation error before any output file is opened. A missing
market group follows the protected legacy path unchanged.

## Verification contract

Add table-driven ES/EN tests for:

- all priorities showing four trace steps, concrete safe evidence states, the
  target-role label, and template fields;
- observed, candidate-reported, inferred, unavailable, declined, and failed
  evidence/inspection states;
- exactly one pending authorization question with the exact target section;
- unresolved/mismatched evidence IDs, malformed sections, raw IDs, URLs,
  identity/action/outcome prose, and external controls failing before output;
- no raw evidence IDs, capture references, paths, URLs, emails, or private text
  in rendered HTML; generated ARIA IDs remain unique and resolved;
- safe technical and non-predictive wording remaining valid;
- mobile, print, dark, forced-colors, and reduced-motion CSS contracts;
- v1 and no-market byte snapshots remaining unchanged.

Run current Python and CPython 3.11 focused suites, the full plugin suite,
static checks, repository privacy, locked release validation, and `git diff
--check` before cachebuster/install/push.

## Explicit non-goals

No new learning schema, no coach decision-trace persistence, no LinkedIn or
browser actions, no eligibility inference, no external links/forms/buttons,
and no claim that visual or assistive-technology QA occurred without a working
browser/canvas session.
