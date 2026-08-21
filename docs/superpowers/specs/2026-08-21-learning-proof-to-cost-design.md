# Proof-to-Cost Learning Card Projection

## Status

Approved as a bounded renderer increment. It consumes the already validated
`career-learning-decision-v1` bundle and changes no persisted schema, builder,
v1 output, or no-market bytes.

## Outcome

Learning cards must let a client compare the proposed proof, the effort/cost
uncertainty, and the bounded signal it could create before deciding whether to
buy a course or certification. The card should explain the coach's basis and,
for official provider rows, expose the source date and explicit unknowns.

## Presentation contract

Each evaluated decision card adds localized, escaped fields:

- `Base de la decisión / Decision basis` — why the option follows from the
  repeated market signal.
- `Costo y tiempo / Cost and time` — the existing `cost_time_band` wording,
  including unknowns rather than inventing values.
- `Señal esperada / Expected signal` — the existing bounded hypothesis; never a
  hiring, interview, salary, or offer prediction.
- `Fuente oficial / Official source` — only for course/certification rows with
  validated `provider_source`; show `source_date` and `unknowns`, not raw IDs or
  external links. If no provider source exists, render nothing.

Keep the existing decision, alternative, risk, and next-review fields. The
order is decision basis → cost/time → expected signal → source metadata →
existing alternative/risk/decision/gate so the proof-to-cost comparison is
visible before the action boundary.

## Compatibility and privacy

- No schema or builder changes.
- Reuse the validated frozen bundle; render only escaped strings already
  accepted by the learning validator.
- Do not add links, buttons, forms, purchase/apply instructions, or outcome
  claims. Preserve the existing v1 and no-market byte snapshots.
- Preserve mobile, print, dark, forced-colors, and reduced-motion CSS contracts.

## Verification

Add ES/EN tests for course, certification, portfolio, and no-learning rows;
assert all new fields appear only in evaluated market output, provider metadata
is conditional, and no raw URLs/IDs or external controls are introduced. Run
the v2, market-learning, v1, parity, privacy, static, and locked release gates
on both supported Python runtimes.
