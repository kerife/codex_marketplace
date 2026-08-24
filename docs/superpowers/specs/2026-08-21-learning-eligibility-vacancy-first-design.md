# Learning Eligibility and Vacancy-First Decision

## Status

Approved in chat as an architectural increment. This specification is the
binding product, provenance, privacy, and rendering contract for the
implementation plan. The user-facing objective is to prevent weak market
evidence from producing premature learning recommendations and to surface one
private, reversible next action aimed at first-interview preparation.

## Problem and required outcome

The current semantic-provenance v2 path proves that a learning decision cites
the exact candidate claims, evidence, requirements, vacancies, market signals,
and provider option that its source arrays name. It does not prove that the
market signal is recurrent enough to justify learning, nor that the candidate
has an explicit proof, knowledge, experience, or terminology gap.

The canonical complete fixture demonstrates the product defect: Terraform is
present in one of five vacancies and is a `candidate_reported_match`, yet four
learning decisions are produced, including two `do_now` decisions. The
renderer describes the input as repeated or recurrent evidence. A single
vacancy and a supported candidate relation are not evidence of a learning gap.

The new outcome must establish this closed chain:

```text
user-selected public vacancy + user-selected public market signal
  -> exact active-vacancy recurrence
  -> exact candidate support relation
  -> explicit candidate-confirmed gap assessment
  -> one eligibility state
  -> exactly one safe next action
  -> zero or one learning decision
```

The system must not select a vacancy automatically, infer a gap from prose,
turn an evidence-coverage score into hiring probability, or present several
contradictory actions as equally urgent.

## Scope

This increment adds:

1. `candidate-gap-response-v1`, an immutable, identity-free source record of
   the user's closed public selection and relation response;
2. `candidate-gap-assessment-v1`, a projection that resolves that response
   against exact validated source snapshots;
3. `career-next-action-eligibility-v1`, a recomputable decision gate bound to
   the validated research, dossier, alignment, market, and gap-assessment
   sources;
4. `career-learning-decision-v3`, a zero-or-one-decision generation that is
   derived from the eligibility artifact rather than caller-selected semantics;
5. one localized “This week's decision” / “Decisión de esta semana” card in
   the existing executive dossier `Decide now` region; and
6. deterministic Superdesign, accessibility, privacy, writer/CLI, installed
   cache, and release evidence for the new composition.

This increment does not:

- generate or submit an application;
- edit LinkedIn, a CV, or any public profile;
- send a message, connection request, or recruiter outreach;
- enroll in or purchase learning;
- score interview or hiring probability;
- choose the target vacancy or market signal for the user;
- generate the contents of a full vacancy-tailoring packet; or
- change the meaning of historical v1 or v2 artifacts.

The private vacancy packet named by the fallback is the next deliverable, not
an implicit external action. Its contents will be specified in a later cycle.

## Versioning and compatibility

- Add the four new schemas and their builders/validators without modifying the
  meaning of existing schema versions.
- `career-learning-decision-v1` and `career-learning-decision-v2` remain
  readable historical inputs. Their builders and fixtures stay available for
  compatibility tests.
- New canonical generation uses `career-learning-decision-v3`.
- The v3 renderer path requires its response, assessment, and eligibility
  sources. Mixed, crossed, partial, or stale groups fail before any new UI is
  rendered.
- Every historical v1 and v2 composition remains byte-identical. Only the new
  v3 composition receives new rendered snapshots.
- The protected legacy no-market ES/EN snapshots remain byte-identical.
- The plugin manifest, static inventories, active installed cache, and release
  attestation must include the new artifacts before v3 is claimed available.

## Candidate gap response v1

`candidate-gap-response-v1` is the independent source of user intent. It is
persisted before assessment and is never reconstructed from assessment,
eligibility, or learning output. It contains exactly:

- `schema_version = candidate-gap-response-v1`;
- `locale`, common `as_of_date`, `source_research_snapshot`,
  `source_market_snapshot`, and nullable `source_provider_research_snapshot`;
- `response_state` (`unavailable`, `selection_required`, `partial`, or
  `complete`);
- `selected_vacancy_ordinal`, `selected_signal`, `relation`, and
  `selected_provider_ordinal`, with nullability below;
- `privacy_boundary = identity_free_closed_candidate_response_only`;
- `draft_only = true`; and
- `no_external_action = true`.

The response uses only public ordinals: `V1`–`V5` for a vacancy and `L1`–`Ln`
for a provider option. It never accepts a private vacancy or provider ID. The
closed relation enum is the assessment relation enum defined below; there is no
free-form response field.

| Response state | Vacancy/signal | Relation | Provider ordinal/source snapshot |
| --- | --- | --- | --- |
| `unavailable` | both null | null | ordinal null; snapshot null |
| `selection_required` | both null | null | ordinal null; snapshot null |
| `partial` | both non-null | `unknown` | ordinal null; snapshot null |
| `complete`, non-knowledge relation | both non-null | confirmed non-unknown | ordinal null; snapshot null |
| `complete`, `knowledge_gap` without provider selection | both non-null | `knowledge_gap` | ordinal null; snapshot null or non-null according to whether provider research was supplied |
| `complete`, `knowledge_gap` with provider selection | both non-null | `knowledge_gap` | ordinal non-null and snapshot non-null |

The response validator validates closed shape, scalar grammar, public ordinal
bounds, common date/locale, and source snapshots against independently supplied
research, market dossier, and optional provider research. It does not claim to
recompute the user's intent. Provider research is supplied if and only if the
provider snapshot is non-null. Any later validator receives this response as a
separate argument and verifies its snapshot before consuming the selection.

## Candidate gap assessment v1

### Purpose

`candidate-gap-assessment-v1` resolves the separately persisted response's
explicit vacancy, market signal, optional provider, and gap-relation choices
into an identity-free closed assessment. The response—not this projection—is
the independent source of user intent. Neither is produced by classifying
free-form prose. The candidate-reported status is evidence of the assessment,
not verified proof of skill level or employability.

### Top-level contract

The artifact contains exactly:

- `schema_version = candidate-gap-assessment-v1`;
- `locale` (`es` or `en`);
- `as_of_date` (`YYYY-MM-DD`);
- `state` (`selection_required`, `complete`, `partial`, or `unavailable`);
- `source_research_snapshot`;
- `source_dossier_snapshot`;
- `source_market_snapshot`;
- `source_gap_response_snapshot`;
- `source_provider_research_snapshot`, nullable;
- `selected_vacancy_id`, `selected_signal`, and
  `selected_provider_option_id`, each nullable under the state rules below;
- zero or one `assessments`;
- `privacy_boundary = identity_free_closed_candidate_assessment_only`;
- `draft_only = true`; and
- `no_external_action = true`.

Each assessment contains exactly:

- `signal`, using the semantic-provenance v2 normalized signal grammar;
- `relation`, one of `supported`, `proof_gap`, `knowledge_gap`,
  `practice_gap`, `professional_experience_gap`, `terminology_gap`, or
  `unknown`;
- `confirmation_state`, either `candidate_confirmed` or `not_assessed`; and
- `assessment_date`, equal to the artifact date when candidate-confirmed and
  `null` otherwise.

`unknown` requires `not_assessed` and a null date. Every other relation requires
`candidate_confirmed` and the common artifact date. The assessment signal must
equal `selected_signal` and an exact normalized `requested_technology_term`.
No assessment contains prose, identity, internal claim/evidence IDs, URLs,
provider data, or employment outcome claims.

State invariants are exact:

- `unavailable`: research is unavailable; all three selected fields are null,
  the provider snapshot is null, and `assessments` is empty;
- `selection_required`: research is available; all three selected fields are
  null, the provider snapshot is null, and `assessments` is empty;
- `partial`: selected vacancy and signal are non-null, provider is null, and
  there is exactly one `unknown` / `not_assessed` assessment; the provider
  snapshot is null;
- `complete`: selected vacancy and signal are non-null and exactly one
  candidate-confirmed non-unknown assessment exists. The provider snapshot is
  null for non-knowledge relations. For `knowledge_gap`, it is non-null if and
  only if provider research was independently supplied; selected provider is
  non-null if and only if the response has a public provider ordinal, in which
  case the option must be active, official, and cover the exact signal.

Selected vacancy and signal must be an exact valid pair in the bound research.
Selected provider is never inferred from ordering and is forbidden for every
relation other than `knowledge_gap`.

### Builder and validator

The builder accepts validated research, executive dossier, market dossier, the
separately validated candidate gap response, and optional provider research. It resolves
the response's public `Vn` and optional `Ln` ordinals against deterministic
source ordering and emits the corresponding private references only inside the
assessment. It normalizes no aliases: the supplied signal must already equal a
normalized requested technology term. It generates confirmation metadata and
every source snapshot. The builder never accepts a second selection parameter
and never infers intent.

The trusted validator receives the artifact plus candidate gap response,
research, executive dossier, market dossier, and optional provider research. It validates the
independent response first, then recomputes the valid vacancy/signal pair,
allowed requested-signal set, selected provider relation, snapshots, state, and
complete expected assessment projection from that response. It never derives
the response from the assessment. It rejects added, missing, duplicated,
reordered, malformed, crossed, cyclic, or exception-raising input with fixed
diagnostics that do not echo source data.

## Career next-action eligibility v1

### Inputs

`build_career_next_action_eligibility_v1` accepts:

- validated target-vacancy research v1;
- validated executive career dossier v2;
- validated career market learning dossier v2;
- validated candidate gap response v1;
- validated candidate gap assessment v1; and
- optional validated provider research v1.

The builder recomputes candidate-market alignment v2 and every source snapshot.
It never accepts caller-authored recurrence, support state, candidate relation,
eligibility state, action, display copy, or public ordinal.

The selection fields come only from the validated assessment source. Vacancy
matches `^V-[0-9]{3}$`, signal matches the normalized signal grammar, and
provider option matches `^LP-[0-9]{3}$`. The eligibility builder does not
accept a second selection parameter that could override the user's source.

### Output

The artifact contains exactly:

- `schema_version = career-next-action-eligibility-v1`;
- `locale` and the common `as_of_date`;
- `state`;
- `source_research_snapshot`;
- `source_dossier_snapshot`;
- `source_alignment_snapshot`;
- `source_market_snapshot`;
- `source_gap_response_snapshot`;
- `source_gap_assessment_snapshot`;
- `source_provider_research_snapshot`, non-null if and only if provider research
  is supplied under the exact grouping rule below;
- `selected_vacancy_id`, `selected_signal`, and
  `selected_provider_option_id`; the first two are both null only when
  selection is required or market evidence is unavailable, and the provider
  field is non-null if and only if state/action are
  `eligible`/`research_provider_option` with the exact explicitly selected
  eligible option;
- `public_vacancy_ordinal`, null under the same conditions;
- `recurrence` as the exact `k/N` market fraction or null under the state
  matrix below;
- `candidate_support_state`, nullable under the state matrix below;
- `candidate_relation`, nullable under the state matrix below;
- `recommended_next_action`;
- `decision_basis_code`;
- `eligible_provider_choices`, empty except for
  `provider_selection_required`, where it is the complete deterministic list
  of `public_provider_ordinal`, `option_name`, and `provider_or_owner` rows;
- localized deterministic `private_deliverable` and `done_when` copy;
- `privacy_boundary = identity_free_structured_eligibility_only`;
- `draft_only = true`;
- `no_external_action = true`; and
- `outcome_boundary = not_an_interview_offer_salary_or_hiring_prediction`.

The closed states are:

- `selection_required`;
- `insufficient_recurrence`;
- `insufficient_gap_evidence`;
- `provider_selection_required`;
- `provider_evidence_required`;
- `learning_not_applicable`;
- `eligible`;
- `unavailable`.

The closed actions are:

- `select_target_vacancy_and_signal`;
- `confirm_gap_relation`;
- `select_provider_option`;
- `prepare_private_vacancy_packet`;
- `build_bounded_proof`;
- `run_validation_lab`;
- `research_provider_option`;
- `run_role_search_experiment`; and
- `no_learning_yet`.

Field nullability is normative:

| State | Selection IDs | Public ordinal | Recurrence/support/relation |
| --- | --- | --- | --- |
| `unavailable` | all null | null | all null |
| `selection_required` | vacancy/signal/provider all null | null | all null |
| every other state | vacancy and signal non-null; provider only when explicitly selected | non-null | all non-null |

The renderer omits vacancy, signal, recurrence, and evidence rows when their
fields are null. `selection_required` renders only the fixed selection question,
action, deliverable, done-when, and boundary rows. `unavailable` renders no
weekly-decision card.

For `selection_required`, the localized help states the ordered decision before
its existing internal navigation: choose one public `Vn` in the vacancy key,
then choose a signal in the signal matrix for that same active vacancy. It
retains exactly the localized vacancy-key link followed by the localized
signal-matrix link.

Its exact normalized visible copy is:

- ES: `Primero, elige una vacante Vn en la clave de vacantes. Después, para esa misma vacante activa, elige una señal en la matriz de señales.`
- EN: `First, choose a vacancy Vn in the vacancy key. Then choose a signal in the signal matrix for that same active vacancy.`

Provider grouping is exact. The provider input is present if and only if
`source_provider_research_snapshot` is non-null. It is forbidden for
unavailable, selection-required, partial, and every confirmed non-knowledge
relation. For `knowledge_gap`, it may be absent; absence or zero exact eligible
options yields `provider_evidence_required`. A non-null selected provider ID is
allowed only for `eligible + research_provider_option`, when the response
contains an explicit public provider ordinal and eligibility resolves and binds
that exact option. Learning v3 consumes only this eligibility-bound option and
accepts no provider selection argument.

The knowledge-gap lifecycle therefore requires fresh source records: no
provider source yields `provider_evidence_required`; a new response bound to a
provider source with eligible choices but no `Ln` yields
`provider_selection_required`; and a later new response with an explicit valid
`Ln` can yield `eligible`. No derived artifact is edited in place.

The eligibility projection is exhaustive:

| Condition/state | Recurrence, support, relation | Provider projection | `decision_basis_code` | Action | Learning rows |
| --- | --- | --- | --- | --- | --- |
| `unavailable` | all null | ID null; choices empty | `market_unavailable` | `no_learning_yet` | 0 |
| `selection_required` | all null | ID null; choices empty | `selection_missing` | `select_target_vacancy_and_signal` | 0 |
| `insufficient_recurrence` | exact non-null values | ID null; choices empty | `recurrence_below_two` | `prepare_private_vacancy_packet` | 0 |
| `insufficient_gap_evidence` + `unknown` | exact recurrence/support; relation `unknown` | ID null; choices empty | `gap_unknown` | `confirm_gap_relation` | 0 |
| `insufficient_gap_evidence` + `supported` | exact recurrence/support; relation `supported` | ID null; choices empty | `candidate_supported` | `prepare_private_vacancy_packet` | 0 |
| `provider_selection_required` | exact recurrence/support; relation `knowledge_gap` | ID null; every exact eligible public choice | `provider_choice_missing` | `select_provider_option` | 0 |
| `provider_evidence_required` | exact recurrence/support; relation `knowledge_gap` | ID null; choices empty | `provider_evidence_missing` | `no_learning_yet` | 0 |
| `learning_not_applicable` | exact recurrence/support; relation `professional_experience_gap` | ID null; choices empty | `professional_experience_required` | `prepare_private_vacancy_packet` | 0 |
| `eligible` + `proof_gap` | exact recurrence/support/relation | ID null; choices empty | `proof_gap_recurrent` | `build_bounded_proof` | 1 |
| `eligible` + `practice_gap` | exact recurrence/support/relation | ID null; choices empty | `practice_gap_recurrent` | `run_validation_lab` | 1 |
| `eligible` + `terminology_gap` | exact recurrence/support/relation | ID null; choices empty | `terminology_gap_recurrent` | `run_role_search_experiment` | 1 |
| `eligible` + `knowledge_gap` | exact recurrence/support/relation | exact selected ID; choices empty | `knowledge_gap_recurrent_provider_selected` | `research_provider_option` | 1 |

The localized state statement is the exact row in the normative copy table
whose condition matches this table. `private_deliverable` and `done_when` are
the exact localized action-table cells. No additional state, basis code,
nullable combination, provider choice projection, or learning cardinality is
valid.

### Exact decision table

Rules are evaluated in this order:

1. Market evidence unavailable produces `unavailable` + `no_learning_yet` and
   no selection fields. The eligibility result is not rendered as a second
   action card; the existing unavailable-market safe step remains the single
   visible next action.
2. A selection-required assessment produces `selection_required` +
   `select_target_vacancy_and_signal`. The renderer asks the user to choose one
   public vacancy ordinal and one public signal from that vacancy; it does not
   rank or preselect either value.
3. A supplied vacancy or signal that does not exist, is inactive, is not part
   of the selected vacancy, or crosses a snapshot fails closed. It is not a
   user-facing eligibility state.
4. Recurrence in fewer than two distinct active vacancies produces
   `insufficient_recurrence` + `prepare_private_vacancy_packet`, regardless of
   candidate relation or provider research.
5. A missing assessment or `unknown` relation produces
   `insufficient_gap_evidence` + `confirm_gap_relation`.
6. `supported` produces `insufficient_gap_evidence` +
   `prepare_private_vacancy_packet`; evidence of support is not evidence of a
   gap.
7. With recurrence of at least two active vacancies:
   - `proof_gap` produces `eligible` + `build_bounded_proof`;
   - `practice_gap` produces `eligible` + `run_validation_lab`;
   - `professional_experience_gap` produces `learning_not_applicable` +
     `prepare_private_vacancy_packet`; deterministic copy states that a lab,
     course, or certification cannot substitute for professional or production
     experience;
   - `terminology_gap` produces `eligible` + `run_role_search_experiment`;
   - `knowledge_gap` with one or more active, official, independently validated
     options that explicitly cover the exact signal, but no explicit provider
     selection, produces `provider_selection_required` +
     `select_provider_option`. The renderer exposes every eligible option as a
     stable, non-ranked public choice; it never chooses one;
   - `knowledge_gap` plus an explicitly selected eligible provider option
     produces `eligible` + `research_provider_option`;
   - `knowledge_gap` without any eligible option produces
     `provider_evidence_required` + `no_learning_yet`.

Selecting a provider option for any non-knowledge relation, selecting an
unknown/inactive/non-covering option, or supplying a provider selection before
vacancy and signal selection fails closed. The system never selects a provider
on the user's behalf.

There is exactly one output action. The decision table never uses alignment
percentage, evidence coverage percentage, qualitative band, employer identity,
title similarity, free-form text, or provider marketing prose.

### Public ordinal

`public_vacancy_ordinal` is recomputed from the sorted vacancy order in the
validated market dossier, using `V1` through `V5`. The internal
`selected_vacancy_id` is never rendered. This preserves the semantic-provenance
v2 public-order correction.

### Validator

The trusted validator receives the artifact and every independent source used
by the builder. It rebuilds the complete artifact and compares exact canonical
content. Unknown keys, source mutation, snapshot drift, cross-version inputs,
wrong dates/locales, reordered arrays, forged actions, and exceptional object
behavior produce bounded generic diagnostics without source echo or traceback.

## Career learning decision v3

### Constructor authority

`build_career_learning_decision_v3` accepts the validated source group plus the
validated eligibility artifact. It does not accept decision requests.

The eligibility action is the sole decision authority:

- `build_bounded_proof`, `run_validation_lab`,
  `research_provider_option`, and `run_role_search_experiment` project exactly
  one decision row;
- every other action projects zero decision rows.

The builder revalidates and recomputes eligibility before projection. It does
not trust a caller-authored eligibility artifact, provider option, gap type,
decision code, source union, or visible copy.

### Output

The top-level v3 artifact has
`schema_version = career-learning-decision-v3`, retains the v2 privacy,
no-action, outcome, common date, and source snapshot fields, and adds
`source_gap_response_snapshot`,
`source_gap_assessment_snapshot`, and
`source_next_action_eligibility_snapshot`. Its `decisions` array has zero or
one item. All three snapshots must match the separately supplied source
artifacts; none is inferred from another derived artifact.

The decision row retains the safe v2 public projection fields but its semantic
code and exact source unions come from the eligibility builder. The mapping is:

- `build_bounded_proof` -> proof / portfolio project / `do_now`;
- `run_validation_lab` -> practice / lab / `do_now`;
- `research_provider_option` -> knowledge / course or certification /
  `research_first` using only the explicitly selected provider option after it
  is revalidated against the independently validated source;
- `run_role_search_experiment` -> terminology / role search /
  `research_first`.

Provider ordering is deterministic only for display. It never selects or ranks
an option. Enrollment or purchase remains outside the artifact and requires
exact later authorization.

Every v3 decision has exact source unions:

- `source_signals` is the one selected normalized signal;
- `vacancy_ids` is the sorted set of distinct active vacancies containing an
  exact requirement for that signal;
- `requirement_ids` is the sorted set of those exact matching requirements;
- `claim_ids` and `source_evidence_ids` are the sorted exact alignment-route
  unions for the selected signal and contain no unrelated claim or evidence;
- `target_role_families` is the sorted exact union from those vacancies;
- `signal_routes` contains one row whose public vacancy ordinals correspond
  exactly to `vacancy_ids` in validated market order and whose recurrence is
  the same `k/N` as eligibility; and
- `provider_option_id` is non-null only for `research_provider_option` and must
  equal the option already bound by eligibility.

The gap response, assessment, and eligibility snapshots provide the provenance
for relation and action; there is no caller-supplied gap/evidence union. Any
missing, extra, reordered, unrelated, or crossed source member fails closed.
Provider coverage and visible copy are recomputed exactly. No caller prose is
accepted.

## Executive dossier composition

### Input grouping

The existing renderer gains one new coherent optional generation:

```text
market dossier v2
+ research
+ candidate gap response v1
+ candidate gap assessment v1
+ next-action eligibility v1
+ learning decision v3
+ provider research only when supplied or required
```

For v3, the response, assessment, eligibility, and learning artifacts are
all-or-none.
The existing v1 and v2 composition rules remain unchanged. A v3 artifact cannot
be paired with v1 market/alignment or v2 learning. Missing, extra, malformed, or
crossed inputs fail before partial market, decision, or learning HTML is
returned or written.

### “This week's decision” card

The v3 composition adds one full-width card inside `Decide now`, after the
current market summary and before the detailed learning section. It appears for
selection-required, insufficient, provider-required, learning-not-applicable,
and eligible states. It is omitted for unavailable market evidence and legacy
no-market input so the existing unavailable-market safe step remains the only
visible next action.

The card contains, in this order:

1. localized heading “Decisión de esta semana” / “This week's decision”;
2. the user-selected public vacancy ordinal and public title/employer, or one
   selection question when `selection_required`;
3. the selected public signal and exact recurrence `k/N` when available;
4. for `provider_selection_required` only, the complete eligible provider list
   as stable public `L1`–`Ln` choices, each with option name and
   provider/owner, in deterministic lexical order that is explicitly not a
   ranking;
5. a localized relation/evidence statement;
6. exactly one localized next-action label;
7. the deterministic private deliverable;
8. deterministic `done_when`; and
9. a visible, printable boundary stating that the artifact does not predict an
   interview, offer, salary, or hiring outcome and performs no external action.

The card never renders internal vacancy, requirement, claim, evidence,
provider-option, or snapshot IDs; source/referrer/provider URLs; raw source
prose; candidate identity; contact data; private analytics; caller-authored
copy; or raw enum names.

When state is `unavailable`, the existing unavailable-market safe step remains
authoritative and no weekly-decision card is rendered. When state is
`selection_required`, there is no button, form, auto-selection, ranking, or
external link. Selection occurs through a later explicit user response and a
fresh artifact build.

For `provider_selection_required`, the public choice list is recomputed from
the independently validated provider source and exact selected signal. It is
sorted by normalized option name and then provider/owner solely for stable
display, assigned `L1` through `Ln`, and labeled explicitly as non-ranked. Each
visible and accessible choice name contains its public ordinal, option name,
and provider/owner. It contains no provider-option ID, URL, price claim, or
marketing prose. A later explicit `L1`–`Ln` response is mapped locally to the
corresponding internal option reference only when a fresh assessment is built
from the persisted response source; the renderer never mutates or completes
the existing artifact.

### Normative localized copy

State/evidence statements are fixed templates:

| State/condition | Español | English |
| --- | --- | --- |
| `selection_required` | `Elige una pareja válida de vacante y señal (V1–Vn) para decidir el siguiente paso; no se preselecciona ninguna.` | `Choose one valid vacancy-and-signal pair (V1–Vn) to decide the next step; none is preselected.` |
| `insufficient_recurrence` | `La señal aparece en {recurrence}; no alcanza el umbral de dos vacantes activas.` | `The signal appears in {recurrence}; it does not meet the two-active-vacancy threshold.` |
| `insufficient_gap_evidence` + `unknown` | `La relación de brecha todavía no está confirmada.` | `The gap relation is not confirmed yet.` |
| `insufficient_gap_evidence` + `supported` | `La señal está respaldada; ese respaldo no demuestra una brecha.` | `The signal is supported; that support does not establish a gap.` |
| `provider_selection_required` | `Hay recurrencia y una brecha de conocimiento confirmada; falta elegir una opción oficial verificada.` | `Recurrence and a confirmed knowledge gap exist; one verified official option still needs to be selected.` |
| `provider_evidence_required` | `Hay recurrencia y una brecha de conocimiento confirmada, pero no hay una opción oficial verificada para esta señal.` | `Recurrence and a confirmed knowledge gap exist, but no verified official option covers this signal.` |
| `learning_not_applicable` | `La brecha requiere experiencia profesional o de producción; un laboratorio, curso o certificación no la sustituye.` | `The gap requires professional or production experience; a lab, course, or certification cannot substitute for it.` |
| `eligible` | `La señal aparece en {recurrence} y la relación {relation_label} fue confirmada por la persona candidata.` | `The signal appears in {recurrence}, and the {relation_label} relation was candidate-confirmed.` |

The `{relation_label}` token is also closed and localized:

| Relation | Español | English |
| --- | --- | --- |
| `proof_gap` | `brecha de evidencia práctica` | `proof gap` |
| `practice_gap` | `brecha de práctica` | `practice gap` |
| `terminology_gap` | `brecha de terminología` | `terminology gap` |
| `knowledge_gap` | `brecha de conocimiento` | `knowledge gap` |

Action labels, deliverables, and done-when copy are also fixed:

| Action | ES: label / deliverable / done when | EN: label / deliverable / done when |
| --- | --- | --- |
| `select_target_vacancy_and_signal` | `Elige vacante y señal` / `Una pareja pública Vn + señal elegida por ti.` / `La vacante y la señal pertenecen a la misma vacante activa.` | `Choose vacancy and signal` / `One public Vn + signal pair chosen by you.` / `The vacancy and signal belong to the same active vacancy.` |
| `confirm_gap_relation` | `Confirma la relación de brecha` / `Una respuesta estructurada, sin prosa libre, para la señal elegida.` / `La relación queda confirmada o marcada como desconocida.` | `Confirm the gap relation` / `One structured response without free-form prose for the selected signal.` / `The relation is confirmed or marked unknown.` |
| `prepare_private_vacancy_packet` | `Prepara primero el paquete privado de vacante` / `Un borrador privado y verificable para la vacante elegida; no se envía.` / `Cada afirmación está respaldada o marcada para confirmar u omitir.` | `Prepare the private vacancy packet first` / `One private, verifiable draft for the selected vacancy; it is not sent.` / `Every claim is supported or marked to confirm or omit.` |
| `build_bounded_proof` | `Construye una prueba acotada` / `Una prueba privada e inspeccionable de la señal elegida.` / `La prueba muestra alcance, acción y resultado sin afirmar producción no demostrada.` | `Build one bounded proof` / `One private, inspectable proof for the selected signal.` / `The proof shows scope, action, and result without claiming unsupported production work.` |
| `run_validation_lab` | `Ejecuta un laboratorio de práctica` / `Un laboratorio privado y acotado para practicar la señal.` / `El resultado es inspeccionable y no se presenta como experiencia profesional.` | `Run one practice lab` / `One private, bounded lab for practicing the signal.` / `The result is inspectable and is not presented as professional experience.` |
| `select_provider_option` | `Elige una opción oficial para investigar` / `Una opción pública elegida explícitamente; no es una recomendación de compra.` / `La opción activa cubre la señal exacta y su fuente oficial está fechada.` | `Choose one official option to research` / `One explicitly selected public option; this is not a purchase recommendation.` / `The active option covers the exact signal and has a dated official source.` |
| `research_provider_option` | `Investiga la opción elegida` / `Una revisión privada de costo, tiempo, requisitos y desconocidos.` / `Costo, tiempo, requisitos y mantenimiento están confirmados o marcados como desconocidos.` | `Research the selected option` / `One private review of cost, time, prerequisites, and unknowns.` / `Cost, time, prerequisites, and maintenance are confirmed or marked unknown.` |
| `run_role_search_experiment` | `Prueba una búsqueda acotada de roles` / `Una búsqueda privada con la terminología elegida; no se postula.` / `La consulta devuelve evidencia fechada o queda registrada como no disponible.` | `Run one bounded role-search experiment` / `One private search using the selected terminology; no application is submitted.` / `The query returns dated evidence or is recorded as unavailable.` |
| `no_learning_yet` | `No compres aprendizaje todavía` / `Una nota privada de la evidencia de proveedor que falta.` / `Existe una fuente oficial vigente o la decisión permanece aplazada.` | `Do not buy learning yet` / `One private note of the missing provider evidence.` / `A current official source exists or the decision remains deferred.` |

The common visible boundary is exact:

- ES: `Límite: esta decisión usa evidencia documentada; no predice entrevista, oferta, salario ni contratación y no ejecuta ninguna acción externa.`
- EN: `Boundary: this decision uses documented evidence; it predicts neither an interview, offer, salary, nor hiring outcome and performs no external action.`

The visible vacancy name and its accessible name both include the public ordinal,
title, and employer. ARIA may not replace or hide the visible ordinal.

### Learning panel

The detailed learning panel renders only when v3 contains its single decision.
It reuses the existing proof-and-cost and LearningSignalRoute visual contracts.
When v3 has zero decisions, no empty learning grid is rendered. The weekly
decision card remains the visible explanation of why learning is deferred for
non-unavailable states. For `unavailable`, only the existing localized
unavailable-market safe step explains the next action.

## Superdesign workflow

The target is an existing rendered executive dossier. The repository init is
complete but no trusted `.superdesign/resume.json` exists for this target.
After this written spec is approved:

1. collect and validate the cold target context under the existing Superdesign
   SOP;
2. show the complete repo-relative context-file list before upload;
3. create one faithful reproduction of the current complete-market v2 dossier;
4. create one replacement direction that adds the full-width weekly-decision
   card while preserving the design system and all existing market/learning
   content;
5. surface the canvas for review;
6. persist project, target, context files, fingerprints, baseline/active draft,
   and version in `.superdesign/resume.json`; and
7. implement only the approved canvas direction.

The generation prompt must use only the existing fonts, colors, spacing, card
geometry, and component styles. It may not add external assets, interactions,
gradients, fonts, imagery, or new brand marks. Static DOM/CSS checks do not
constitute browser, print-preview, or assistive-technology QA.

## Accessibility and responsive contract

- The weekly-decision card is a named `article` with one localized heading.
- The evidence statement and outcome/no-action boundary have stable IDs and are
  referenced through `aria-describedby` from the card.
- The selected vacancy ordinal is visible text; the full public title/employer
  remain the accessible name. No private ID enters any ARIA attribute.
- All IDs are unique and every `aria-labelledby`/`aria-describedby` reference
  resolves in ES and EN.
- At 680px and below the card remains one column and uses existing anywhere
  wrapping; no horizontal scroll or duplicated mobile label is introduced.
- The card is atomic in print through `break-inside` and
  `page-break-inside: avoid`.
- Light and dark text meet the existing contrast-token contract.
- Forced colors map text to `CanvasText`, surfaces to `Canvas`, and the accent
  border to `Highlight` or `CanvasText`; meaning never relies on color alone.
- Reduced-motion and no-script modes preserve the complete decision.

## Privacy, safety, and totality

- Every entry point first places the complete input group—research, dossier,
  market, provider when present, response, assessment, eligibility, and
  learning—inside one container and passes it once through the shared
  semantic-provenance v2 bounded plain-snapshot helper. The exact budgets are
  depth `32`, total nodes `10_000`, items per mapping/sequence `150`, and string
  length `4096`. Cycles, non-plain keys, unsupported objects, and budget excess
  fail with one fixed generic diagnostic.
- Validation, recomputation, projection, rendering, writing, and CLI handling
  consume only mappings/lists from that one frozen plain snapshot. They never
  reread, iterate, compare, stringify, copy, or deepcopy any original input
  after the boundary.
- This closes the mutable-input time-of-check/time-of-use class already used by
  the executive dossier and avoids repeating the recruiter-practice weakness
  identified during discovery.
- Copy/deepcopy, iteration, mapping access, string conversion, comparison, and
  Unicode normalization exceptions are caught and converted to fixed generic
  diagnostics with `raise ... from None`.
- Diagnostics, CLI stderr, renderer errors, and writer errors never include
  source values, local paths, URLs, IDs, candidate information, or tracebacks.
- Writers use the existing validate-before-write and atomic/no-partial-output
  pattern. A failed group leaves no HTML or partial JSON.
- The release repository privacy checker and private prose guards include every
  new schema, fixture, script, test, documentation example, and rendered field.
- External career actions remain `not_executed`; this increment performs no
  profile edit, publication, message, connection, application, upload,
  enrollment, purchase, or scheduling action.

## Deterministic TDD matrix

Tests are written and observed RED before production changes.

### Candidate response

- public `Vn` + exact signal + closed relation persist as one independent
  response source; no private vacancy/provider ID is accepted;
- `unavailable`, `selection_required`, `partial`, and `complete` enforce the
  exact nullability table;
- public `Ln` is accepted only for complete `knowledge_gap` with a matching
  independently supplied provider snapshot;
- missing/extra/prose fields, invalid ordinals, source drift, wrong locale/date,
  cycles, budget excess, and exception-raising values fail with one fixed
  no-echo diagnostic;
- mutating assessment or eligibility cannot alter or replace the independently
  supplied response, and crossed response snapshots fail closed.

### Candidate assessment

- unavailable response builds `unavailable` with null selections and no row;
- available selection-required response builds `selection_required` with null
  selections and no row;
- exact vacancy/signal pair + `proof_gap` builds `complete` with one
  candidate-confirmed row;
- exact pair + `unknown` builds `partial` with one `not_assessed` row and null
  assessment date;
- explicit knowledge-gap provider choice is bound to the provider snapshot;
- provider choice for another relation, an invalid vacancy/signal pair, or an
  ineligible provider fails closed;
- alias, unrequested signal, duplicate, wrong order, prose/extra field, crossed
  response/research/dossier/provider snapshot, invalid date/locale, non-string,
  cycle, and exception-raising input fail closed without echo;
- safe technical terms and both locales remain valid.

### Eligibility

- unavailable market -> `unavailable` + `no_learning_yet`, no weekly-decision
  card, and exactly the existing unavailable-market safe step;
- missing selection -> `selection_required` +
  `select_target_vacancy_and_signal`;
- selected signal absent from selected vacancy -> fail closed;
- `1/5 + candidate_reported_match + any relation` ->
  `insufficient_recurrence`, zero learning `do_now`, and
  `prepare_private_vacancy_packet`;
- `2/5 + unknown/not assessed` -> `insufficient_gap_evidence` +
  `confirm_gap_relation`;
- `2/5 + supported` -> `insufficient_gap_evidence` +
  `prepare_private_vacancy_packet`;
- `2/5 + proof_gap` -> one `build_bounded_proof`;
- `2/5 + practice_gap` -> one `run_validation_lab`;
- `2/5 + professional_experience_gap` ->
  `learning_not_applicable` + `prepare_private_vacancy_packet`, with explicit
  copy that learning cannot substitute for professional experience;
- `2/5 + terminology_gap` -> one `run_role_search_experiment`;
- `2/5 + knowledge_gap + explicit selected_provider_option_id + exact active
  provider coverage` -> one `research_provider_option`;
- knowledge gap without exact provider coverage ->
  `provider_evidence_required` + `no_learning_yet`;
- knowledge gap with eligible providers but no explicit provider selection ->
  `provider_selection_required` + `select_provider_option`, plus the complete
  stable non-ranked public `L1`–`Ln` option list;
- knowledge gap with an explicit eligible provider selection -> one
  `research_provider_option`;
- a certificate never substitutes for experience;
- score, coverage band, employer/title similarity, and source prose mutations do
  not alter the decision table;
- forged action/state/copy, crossed snapshots, stale sources, wrong public
  ordinal, malformed trees, and exceptional objects fail closed without echo.

### Learning v3

- ineligible states generate zero decisions;
- every eligible state generates exactly one decision with exact source unions;
- there is no caller decision request or caller prose parameter;
- provider selection is explicit, stable, and never inferred from ordering;
- public provider choices are complete, stably ordered, uniquely named in ES
  and EN, contain option/provider labels, and omit internal IDs and URLs;
- an explicit public `L1`–`Ln` response maps to the same bound internal option
  and requires a fresh assessment/eligibility build;
- unrelated provider options, unrelated signals, IDs, vacancies, and gap
  assessments cannot enter the decision;
- v1/v2 fixtures and validators remain readable and unchanged.

### Renderer and writer

- ES and EN render one weekly-decision card with localized visible copy;
- `selection_required`, insufficient recurrence, insufficient gap evidence,
  provider selection/evidence required, learning-not-applicable, and eligible
  states each show one action and the common boundary;
- unavailable shows no weekly-decision card and preserves exactly one existing
  localized unavailable-market safe step;
- detailed learning renders only for the one eligible v3 decision;
- no raw enum, internal ID, snapshot, URL, source prose, private value, form,
  button, or external link reaches the new region;
- all IDs are unique and references resolve;
- mobile, print, light, dark, forced-colors, and reduced-motion contracts are
  pinned;
- invalid or partial composition fails before output; writer and CLI leave no
  partial artifact;
- v1, v2, unavailable-market, and legacy no-market protected outputs retain
  their required behavior and byte snapshots.

## Documentation and skill routing

Update the professional-growth coach routing and recommend-career-learning
instructions so the order is explicit:

1. user selects one public target vacancy and signal;
2. recurrence and explicit candidate assessment are validated;
3. one weekly action is projected;
4. learning is considered only when the gate is eligible;
5. otherwise the candidate prepares private vacancy evidence or confirms the
   missing relation first.

Documentation must continue to say that market scores are evidence coverage,
never hiring probability. Superdesign `design-system.md`, `components.md`,
`extractable-components.md`, `pages.md`, `routes.md`, `layouts.md`, and
`theme.md` are updated only where the new product/DOM/CSS contract requires it;
byte-parity tests remain authoritative for mirrored shipped assets.

## Release gates

Before publication:

1. focused RED/GREEN matrices pass for all four new artifacts;
2. full market, semantic provenance, learning, renderer, writer/CLI, privacy,
   schema conformance, Superdesign parity, print, dark-mode, plugin structure,
   and package suites pass;
3. the canonical release-validation runner exits zero;
4. after source gates are green, create a dedicated cachebuster commit whose
   only product change is the manifest version; record that exact commit and
   `git rev-parse <cachebuster>:plugins/professional-growth-coach` tree;
5. use the already-authorized publication bridge to push through that
   cachebuster commit and align the canonical marketplace checkout, without
   discarding unrelated work. This first push is required because the public
   selector resolves the canonical checkout; installation cannot precede it;
6. install the exact public selector/version without deleting caches or config.
   Resolve the active cache directory only from the exact version/path reported
   by the successful plugin-list result, never from a `latest` alias or glob;
7. compare the cache to `git archive` of the recorded cachebuster plugin tree.
   Both inventories must have the same non-zero file count and the same sorted
   POSIX relative paths. Each file SHA-256 must match. The aggregate digest is
   SHA-256 over, for each sorted file, `path UTF-8 + NUL + lowercase file SHA-256
   hex + LF`; source and cache aggregate digests must match, and both sides must
   contain zero `.pyc`, `.pyo`, or `__pycache__` artifacts;
8. installed package tests, static checks, schema validators, and a semantic
   acceptance/rejection smoke matrix pass against imported cache modules;
9. create a second, attestation-only commit. The attestation records the
   cachebuster commit as `source_commit`, its exact plugin tree as
   `source_tree`, exact version/cache resolution, non-zero counts, per-file and
   aggregate hashes, accepted/rejected cases, repository-only scope, and the
   statement `visual QA not run` unless real browser evidence exists;
10. final release validation passes after the attestation commit; and
11. push the attestation commit as the final publication, verify remote HEAD,
    and align the primary checkout without discarding unrelated user work.

No release claim may rely only on source tests, static HTML inspection, a local
plugin list, or a successful installer exit code.
