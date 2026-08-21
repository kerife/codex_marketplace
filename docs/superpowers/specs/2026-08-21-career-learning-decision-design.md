# Career Learning Decision Bundle

## Goal

Add an optional, evidence-bound learning/ROI decision surface to the private career-market dossier without changing the existing `career-market-learning-dossier-v1` contract or producing external actions.

## User-facing decision

The client should see a conversational panel titled `Qué estudiar —y qué no comprar aún—` only when a validated market sample contains at least one vacancy. The panel ranks three to five bounded choices: course, certification, portfolio project, lab, role-search action, or `no_learning_yet`. It explains the recurrent gap, the evidence supporting it, a cheaper proof alternative, and the review/authorization gate before any enrollment, purchase, exam, publication, or message.

## Compatibility boundary

- Existing market dossiers remain `learning_state=not_evaluated` with `learning_decisions=[]`.
- The new bundle is an optional `career-learning-decision-v1` artifact passed as an all-or-none renderer group alongside the validated dossier, research, alignment, and market dossier.
- N=0 or missing/invalid learning input renders no learning panel and no score, recurrence, demand, fit, or gap claim.
- Existing v1/no-market HTML bytes and existing market fixture projections remain unchanged.

## Data contract

The bundle is closed-schema and contains:

- `schema_version`, `locale`, `as_of_date`;
- `source_market_snapshot`, `source_dossier_snapshot`, and `source_research_snapshot`;
- `state`: `evaluated` or `unavailable`;
- `decisions`: exactly 3–5 rows when `evaluated`, otherwise an empty list;
- `privacy_boundary`, `no_external_action=true`, and the fixed `outcome_boundary` `not_an_interview_offer_salary_or_roi_prediction`.

Each decision row is ordered and contains `decision_rank`, `target_role`, `gap_type`, `option_type`, `option_name`, `provider_or_owner`, `source_gap_ids`, `vacancy_ids`, `market_evidence_state`, `cost_time_band`, `expected_signal_boundary`, `portfolio_or_no_learning_alternative`, `overbuying_risk`, `decision`, `decision_basis`, `next_action_gate`, `outcome_boundary`, `draft_only=true`, and `no_external_action=true`.

`gap_type` is one of `knowledge`, `proof`, `experience`, `terminology`, or `low_return`; `option_type` is one of `course`, `certification`, `portfolio_project`, `lab`, `role_search`, or `no_learning_yet`; `decision` is one of `do_now`, `defer`, `omit`, or `research_first`.

Course/certification rows must include one dated official provider source with URL, title, source state, geography/eligibility, availability, current cost/currency/tax, duration, prerequisite, renewal, maintenance, and explicit unknowns. No price, eligibility, or duration may be inferred.

## Rendering and privacy

- Render the panel after recurrent market signals and before gap-closure details.
- Add one internal link from `Decide ahora`; no external links are rendered as actions, and no forms/buttons are added.
- Keep copy coach-like, not a shopping list; mention why a project, lab, role search, or no-learning option may beat a course.
- Never render candidate identity, raw vacancy IDs, evidence IDs, private analytics, credentials, or unsupported claims.
- Preserve mobile, print, dark mode, forced-colors, contrast, reduced-motion, and a single coherent landmark/heading structure.

## Validation and failure behavior

- Validate all snapshots, row counts, ranks, references, source dates, unknown fields, and action boundaries before rendering.
- Reject malformed/cyclic input with bounded diagnostics and no echoed values or traceback.
- If the optional group is absent, preserve the current market render. If present but invalid, fail closed to the existing valid profile/market artifact and report the bounded unavailable state; never render partial learning rows.

## Verification

The increment is complete only after RED/GREEN tests for schema, validator, builder, renderer, privacy, no-market compatibility, N=0/N=1..5, mobile/print/dark/forced-colors contracts, package parity, full plugin discovery, full root discovery, installed cache parity, and remote `main` verification.
