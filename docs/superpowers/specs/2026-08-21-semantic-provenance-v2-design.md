# Semantic Provenance v2 for Market and Learning Decisions

## Status

Approved in chat for architectural implementation. This specification is the
binding contract for the implementation plan. It replaces free-form semantic
association with deterministic, snapshot-bound provenance while keeping every
v1 artifact readable as historical data.

## Problem and required outcome

The v1 market path proves that an evidence ID exists and has a compatible
state, but it does not prove that the evidence supports the named market
signal. A caller can therefore bind a generic headline record to
`observability` and obtain a verified match. The v1 learning path separately
checks that evidence and vacancy IDs exist, so a decision can claim that an
unrelated topic recurs in the market while citing valid but unrelated IDs.

The v2 outcome must establish two recomputable branches that join at a market
signal and continue into a bounded decision:

```text
requested technology term -> dossier claim -> dossier evidence
                            \-> normalized market signal
research signal -> vacancy requirement -> vacancy
provider research option -> covered market signal
all validated branches -> bounded learning decision
```

No component may infer this chain from prose, keywords, substrings, synonyms,
stemming, embeddings, or an LLM. Every relationship must come from closed
structured fields and be checked against independently snapshotted sources.

## Versioning and compatibility

- Add `candidate-market-alignment-v2`,
  `career-market-learning-dossier-v2`, and
  `career-learning-decision-v2` schemas, plus the independent
  `career-learning-provider-research-v1` source schema.
- Retain every v1 schema, validator, fixture, and renderer path for historical
  read-only compatibility. Do not silently change the meaning of a v1
  artifact.
- New builders and release fixtures emit v2. A v1 artifact is never upgraded
  in place; migration rebuilds it from its original research and executive
  dossier sources.
- The v1 no-market renderer snapshots remain byte-identical.
- The plugin manifest, static inventories, installed package, and release
  attestation must include the new schemas and tests before v2 is claimed as
  available.

## Deterministic signal normalization

The only permitted mapping from a dossier technology term to a research
signal is:

1. require a string and apply Unicode NFKC;
2. trim leading and trailing whitespace;
3. apply `casefold()`;
4. replace each non-empty run of ASCII whitespace or `-` with `_`;
5. require the complete result to match `^[a-z][a-z0-9_]{1,63}$`.

No other punctuation is rewritten. Slashes, dots, plus signs, partial terms,
aliases, synonyms, and substring matches do not bind. Collisions after
normalization fail closed with a generic diagnostic rather than selecting one
term.

## Candidate market alignment v2

### Source and API

`derive_candidate_market_alignment_v2(research, executive_dossier)` is the
only production constructor. Market builders and validators call it directly;
they do not accept a caller-authored alignment as authority.

The top-level fields are:

- `schema_version = candidate-market-alignment-v2`
- `research_snapshot`
- `executive_dossier_snapshot`
- `signal_bindings`
- `privacy_boundary = identity_free_structured_provenance_only`

Each signal binding contains exactly:

- `signal`
- `support_state`
- `claim_ids`
- `evidence_ids`
- `requirement_ids`
- `vacancy_ids`

All arrays are unique and lexicographically sorted. Bindings are sorted by
signal.

### Research-side derivation

Signals are the exact set of `requirements[].signal` values in validated
target-vacancy research. For each signal:

- `requirement_ids` is the exact set of requirements carrying that signal;
- `vacancy_ids` is the exact set of vacancies containing those requirements.

These market-side arrays remain populated even when candidate support is
unknown.

### Candidate-side derivation

For each research signal, find an exact normalized match in
`requested_technology_terms`. Follow that term's `claim_ids` to closed dossier
claims, then take the exact union of their `evidence_ids` and resolve those
records in `dossier.evidence`.

The only states derivable from the current upstream contract are:

- `verified_match`: every linked claim and evidence record is `verified`;
- `candidate_reported_match`: the complete chain contains at least one
  `candidate_reported` record and no `inferred` or `unknown` record;
- `unknown`: no exact term exists, the chain is incomplete, or any linked
  claim/evidence is `inferred` or `unknown`.

For `unknown`, `claim_ids` and `evidence_ids` are empty. The v2 builder never
emits `adjacent_evidence` or `explicit_gap`; those states require a future
closed relation enum upstream and must not be inferred from prose.

The current complete-five fixture therefore preserves only Terraform as
`candidate_reported_match`; Python, Kubernetes, Observability, and Linux
become `unknown`. The resulting lower alignment score is intentional and
must be fixed in golden tests.

## Career market learning dossier v2

The v2 market builder accepts only validated research and executive dossier
sources. It derives alignment v2 internally and emits:

- `schema_version = career-market-learning-dossier-v2`;
- the existing dated search summary, vacancy cards, recurrence rows, matrix,
  methodology, privacy, and action boundaries;
- `source_alignment_snapshot`, computed from the canonical alignment v2;
- matrix rows whose `claim_ids` and `evidence_ids` exactly match the derived
  binding; their cells remain exact projections of requirements and vacancies.

The trusted validator recomputes the alignment and complete expected market
dossier from the research and executive-dossier sources. It rejects stale
snapshots and any
added, removed, reordered, or substituted claim, evidence, requirement, or
vacancy reference. It never reconstructs an alignment from the market output
being validated.

Unavailable research produces an empty, snapshot-bound v2 market artifact and
does not synthesize candidate support.

## Career learning provider research v1

Course and certification relevance cannot be established from the learning
decision itself. Provider research is therefore a separate validated source,
not embedded caller-authored metadata.

The source artifact contains exactly:

- `schema_version = career-learning-provider-research-v1`;
- `locale`, `as_of_date`, and `state` (`complete`, `limited`, or
  `unavailable`);
- zero to twenty `options`;
- `privacy_boundary = public_provider_metadata_only`;
- `no_external_action = true`.

Each option contains exactly `option_id`, `option_type`, `provider`, `option`,
`source_title`, `source_date`, `access_date`, `source_state`, `url`,
`geography`, `availability`, `current_cost`, `currency`, `tax`, `duration`,
`prerequisite`, `renewal`, `maintenance`, `unknowns`, `covered_signals`, and
`coverage_basis`. `option_id` matches `^LP-[0-9]{3}$`; `option_type` is
`course` or `certification`; the URL is official HTTPS; source/access dates
cannot exceed the artifact date; source state is `active`, `unknown`, or
`unavailable`; bounded prose passes the shared public-provider privacy guard.
`covered_signals` is lexicographically sorted and `coverage_basis` is one
closed value:

- `exact_technology_title`;
- `explicit_curriculum`;
- `explicit_exam_objective`.

`covered_signals` records an explicit conclusion of the provider-research
step. It uses the same normalized signal keys as market v2; it is never
inferred later from the provider name, option title, URL, or prose. An option
without explicit official coverage has an empty array and may not justify a
signal-bound learning decision. The artifact has its own canonical
`snap-provider-sha256-<64 lowercase hex>` snapshot, and learning
builders/validators receive it as an independent argument.

The initial golden provider source contains the active HashiCorp Terraform
option bound to `terraform`. The unrelated Argo option is not bound to
Terraform and cannot be selected for that decision.

## Career learning decision v2

### Structured input and output

Each evaluated decision contains these internal provenance fields:

- `source_signals`: one to five unique, lexicographically sorted normalized
  signals;
- `claim_ids`: the exact union for those signals;
- `source_evidence_ids`: the exact evidence union for those signals;
- `requirement_ids`: the exact requirement union for those signals;
- `vacancy_ids`: the exact vacancy union for those signals;
- `decision_code`: a closed enum selecting all learning semantics;
- `provider_option_id`: an internal provider-research reference or `null`;
- `target_role_families`: the exact unique, sorted role-family union of the
  referenced vacancies.

The builder input for each row contains exactly `decision_rank`,
`decision_code`, `source_signals`, and `provider_option_id`. It computes every
other decision field. Callers cannot provide or override provenance arrays,
gap/option/decision enums, display names, rationales, alternatives, risk copy,
cost copy, signal boundaries, or action gates.

The v2 output row contains exactly the four input fields plus `claim_ids`,
`source_evidence_ids`, `requirement_ids`, `vacancy_ids`,
`target_role_families`, `gap_type`, `option_type`, `decision`, `option_name`,
`provider_or_owner`, `signal_routes`, `cost_time_band`,
`expected_signal_boundary`, `portfolio_or_no_learning_alternative`,
`overbuying_risk`, `decision_basis`, `next_action_gate`, `outcome_boundary`,
`draft_only`, and `no_external_action`. `signal_routes` stores the exact
per-signal relationships consumed by validator and renderer and contains no
source prose or URLs.

The normative decision-code table is:

| `decision_code` | `gap_type` | `option_type` | `decision` | Provider |
| --- | --- | --- | --- | --- |
| `build_bounded_proof` | `proof` | `portfolio_project` | `do_now` | forbidden |
| `run_validation_lab` | `experience` | `lab` | `do_now` | forbidden |
| `research_provider_option` | `knowledge` | source option type | `research_first` | required |
| `defer_learning_purchase` | `low_return` | `no_learning_yet` | `defer` | forbidden |
| `run_role_search_experiment` | `terminology` | `role_search` | `research_first` | forbidden |

For `research_provider_option`, the referenced option must be active and its
`covered_signals` must equal `source_signals`. Its visible name is copied only
after the provider artifact passes the shared identity, URL, raw-control,
length, Unicode, and privacy guards; it is HTML escaped at the renderer. Any
other provider reference or mismatch fails closed. For non-provider codes,
`option_name` and `provider_or_owner` come from localized fixed templates.

All semantic output fields are generated from a single pure projection module
used by both builder and validator. It owns the ES/EN copy table for
`option_name`, `provider_or_owner`, `cost_time_band`,
`expected_signal_boundary`, `portfolio_or_no_learning_alternative`,
`overbuying_risk`, `decision_basis`, and `next_action_gate`. Unknown locale,
code, join input, or missing template fails closed. No existing free-text
decision field is accepted as v2 input. The v1 `target_role` and
`market_evidence_state` prose fields are replaced by structured
`target_role_families` and the per-signal route described below.

`decision_basis` is generated from `decision_code` plus a per-signal view
model. Each signal row contains its validated public term label, localized
support state, exact recurrence `k/N`, and public vacancy ordinals. Rows are
sorted by signal and never collapsed into one union that could attribute a
vacancy to the wrong signal.

### Normative localized projection copy

The public term labels come from the exact validated
`requested_technology_terms.term` records, not from raw signal keys. Labels
are privacy-checked, escaped, and joined deterministically: one label as-is;
two with ` y ` / ` and `; three to five with comma separators and final
` y ` / Oxford-comma `, and `. No other join form is accepted.

Non-provider option names are exact templates where `{signals}` is that
joined label:

| Code | ES | EN |
| --- | --- | --- |
| `build_bounded_proof` | `Prueba acotada de {signals}` | `Bounded {signals} proof` |
| `run_validation_lab` | `Laboratorio de validación de {signals}` | `{signals} validation lab` |
| `defer_learning_purchase` | `Aplazar compra de formación para {signals}` | `Defer learning purchase for {signals}` |
| `run_role_search_experiment` | `Experimento de búsqueda para {signals}` | `Role-search experiment for {signals}` |

`research_provider_option` uses the validated provider option label exactly.
Provider/owner is the validated provider label for that code and the
language-independent enum `candidate_owned` for every other code; the
renderer localizes the enum rather than exposing it raw.

Decision bases are exact fixed strings:

| Code | ES | EN |
| --- | --- | --- |
| `build_bounded_proof` | `Prioriza una prueba acotada antes de comprar formación; la ruta estructurada de evidencia es la base completa de esta decisión preliminar.` | `Prioritize one bounded proof before buying learning; the structured evidence route is the complete basis for this draft decision.` |
| `run_validation_lab` | `Usa un laboratorio acotado para comprobar la señal documentada; la ruta estructurada de evidencia es la base completa de esta decisión preliminar.` | `Use a bounded lab to test the documented signal; the structured evidence route is the complete basis for this draft decision.` |
| `research_provider_option` | `Investiga esta opción verificada de proveedor antes de comprar; su vínculo estructurado de señal no predice resultados laborales.` | `Research this verified provider option before buying; its structured signal binding does not predict employment outcomes.` |
| `defer_learning_purchase` | `Aplaza la compra hasta completar una prueba acotada; la ruta estructurada de evidencia no demuestra retorno de inversión.` | `Defer the purchase until one bounded proof is complete; the structured evidence route does not establish return on investment.` |
| `run_role_search_experiment` | `Prueba una búsqueda acotada de roles antes de elegir formación; la ruta estructurada de evidencia no demuestra elegibilidad ni contratación.` | `Run a bounded role search before choosing learning; the structured evidence route does not establish eligibility or hiring.` |

The remaining visible strings are shared fixed copy per locale: cost/time is
`No evaluado; requiere confirmación separada.` / `Not evaluated; separate
confirmation is required.`; the expected-signal boundary, proof alternative,
overbuying warning, and exact-authorization gate reuse the existing localized
privacy-safe concepts but live in this same closed table. Tests pin the full
ES/EN output object returned by the projection module so builder and validator
cannot drift.

### Cross-source invariants

For every decision:

1. every source signal exists in the recomputed alignment and market matrix;
2. `claim_ids` equals the exact claim union for those signals;
3. `source_evidence_ids` equals the exact evidence union for those signals;
4. `requirement_ids` equals the exact requirement union for those signals;
5. `vacancy_ids` equals the exact containing-vacancy union;
6. `target_role_families` equals the exact role-family union for those
   vacancies;
7. no source signal with `unknown` support may justify an evaluated learning
   decision;
8. provider decisions reference an independently validated option whose
   covered signals equal the decision signals;
9. locale, date, `source_research_snapshot`, `source_dossier_snapshot`,
   `source_alignment_snapshot`, `source_market_snapshot`, and
   `source_provider_research_snapshot`, plus privacy and no-action boundaries,
   match the validated sources.

The initial v2 golden decisions bind to Terraform and therefore to `C-002`,
`E-004`, `V-003-R-01`, and `V-003`. They comprise a bounded proof, a
validation lab, a provider-research option, and a defer-purchase alternative.
IDs are internal test expectations and must never appear in rendered HTML or
diagnostics.

### Version composition matrix

- market v1 accepts learning v1 or no learning bundle;
- market v2 accepts learning v2 or no learning bundle;
- unavailable market v2 accepts only unavailable learning v2 with no
  decisions;
- legacy no-market composition accepts no v2 bundle;
- every v1/v2 mixed pair, crossed snapshot, or provider snapshot omission is
  rejected before rendering.

## Candidate-facing projection

The renderer may consume learning v2 only after all validators pass. It must
not render `claim_ids`, evidence IDs, requirement IDs, vacancy IDs, snapshots,
source URLs, source paraphrases, raw enums, or arbitrary input prose.

The visible evidence route per learning decision contains one row per source
signal and only:

- the validated public technology-term label, after privacy validation and
  escaping (never the raw signal enum);
- localized support state;
- public vacancy ordinals `V1` through `VN` already defined by the adjacent
  vacancy key;
- recurrence `k/N`;
- localized deterministic `decision_basis` and decision label.

Provider option names are the only provider prose permitted in the route.
They must satisfy the provider-source guards above; provider descriptions,
source titles, URLs, unknowns, and eligibility/cost prose remain internal.

The existing proof-and-cost group, authorization boundary, privacy boundary,
print behavior, mobile behavior, dark mode, and forced-colors behavior remain
intact. The v1 renderer and unavailable/no-market states do not show this
projection.

Superdesign may be used to review hierarchy and density after the contract is
green. Repository artifacts, private dossiers, snapshots, or source fixtures
must not be uploaded to an external canvas. A deterministic local review is
the fallback when external artifact upload is not approved. No visual or
assistive-technology QA may be claimed without empirical evidence.

## Failure and diagnostic behavior

- Builders raise bounded generic `ValueError` or the existing typed dossier
  error before opening an output file.
- Validators return bounded generic diagnostics and never echo a signal,
  claim, evidence, requirement, vacancy, URL, path, provider value, or source
  prose.
- Malformed, cyclic, over-depth, oversized, non-string, Unicode edge, and
  stale-snapshot inputs remain total and fail closed.
- No failure path performs a network request or external action.

## TDD and acceptance contract

Tests must be written and observed failing before production edits. The
minimum RED matrix is:

1. reject `observability -> verified_match -> E-001`;
2. derive only Terraform as supported in the current fixture;
3. reject partial, synonymous, or punctuated term mappings;
4. reject added, removed, substituted, or reordered claim/evidence/
   requirement/vacancy references and stale alignment snapshots;
5. reject a Terraform decision carrying unrelated evidence or vacancies;
6. reject arbitrary Quantum option/basis prose, a Quantum provider option
   bound to Terraform, and any caller-provided semantic output field;
7. reject unknown, duplicate, or unsupported `source_signals` without echo;
8. accept the exact Terraform chain, the independently sourced Terraform
   provider option, and deterministic ES/EN per-signal rationale;
9. prove v1 historical validation and no-market byte snapshots remain
   unchanged;
10. prove no internal IDs, URLs, snapshots, or source prose reach HTML;
11. prove all v1/v2 composition combinations and reject mixed versions;
12. prove unique/resolved ARIA references and mobile, print, dark, and
    forced-colors contracts;
13. prove malformed/cyclic/oversized totality and source/cache parity.

Verification before release includes focused schema/builder/validator tests,
the full market and learning suites, renderer v2, package discovery, static
checks, repository privacy, the official locked release runner, `git diff
--check`, exact source/cache inventory and SHA parity, zero bytecode, and
installed smokes for both accepted and rejected provenance chains.

## Delivery sequence

1. Schemas and pure alignment derivation.
2. Market v2 builder, validator, fixtures, and golden arithmetic.
3. Independent provider research source contract and validator.
4. Learning v2 builder, validator, fixtures, and deterministic copy.
5. Safe renderer projection and Superdesign documentation parity.
6. Full review, cachebuster, install, installed smokes, attestation, and push
   to remote `main`.

Each task receives an independent implementation review; the combined diff
receives a final security and product review before release.

## Explicit non-goals

- No NLP, embeddings, synonym dictionary, or inferred semantic matching.
- No mutation of v1 semantics or in-place artifact upgrade.
- No raw evidence/claim prose in the learning projection.
- No provider-to-signal inference from provider prose; only the independently
  validated provider-research binding is authoritative.
- No LinkedIn inspection, recruiter outreach, application, profile edit,
  purchase, enrollment, publication, or other external action.
- No claim that structured provenance proves the real-world truth of an
  upstream claim; it proves an explicit, auditable chain between authorized
  source artifacts.
