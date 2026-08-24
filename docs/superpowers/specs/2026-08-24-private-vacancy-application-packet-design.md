# Private Vacancy Application Packet — Design Specification

**Date:** 2026-08-24
**Status:** Approved; implementation authority
**Scope:** `professional-growth-coach` plugin, private/offline artifacts only

## 1. Decision summary

Add two closed, versioned private contracts:

1. `candidate-fact-matrix-v1`, an identity-free, evidence-state-aware source of candidate facts.
2. `private-vacancy-application-packet-v1`, a deterministic vacancy-bound draft packet with one readiness decision.

The existing `career-next-action-eligibility-v1` artifact remains the sole authority for the target vacancy and for whether packet preparation is the next safe action. The packet does not accept a second target-vacancy parameter.

The packet's three readiness states are:

- `revise_first`
- `ready_for_manual_authorization`
- `stop`

`ready_for_manual_authorization` means only that a private, evidence-bound draft is ready for human review before a future, separate, exact authorization request. It never means ready to apply, eligible for employment, or authorized to upload, message, publish, or submit.

## 2. Problem and desired outcome

Three existing eligibility states can recommend `prepare_private_vacancy_packet`, but the plugin has no typed artifact for that action. The user can see what to do next but cannot obtain a bounded, auditable packet that distinguishes supported claims from revisions and hard stops.

The increment will produce one private JSON artifact and one private HTML rendering that:

- bind to the vacancy already selected by validated eligibility;
- map exact vacancy signals to evidence-backed candidate facts;
- draft only deterministic, source-derived language;
- show one primary readiness decision;
- expose missing, unsupported, conflicting, or confidential evidence;
- prepare, but never perform, a future career action.

## 3. Non-goals

This increment will not:

- apply to a vacancy, upload a file, edit a profile, send a message, contact a recruiter, purchase, enroll, or publish;
- infer hiring probability, fit percentage, seniority, compensation, or application eligibility;
- search the market or select a different vacancy;
- infer aliases or semantic equivalence from free-form prose;
- rewrite arbitrary user prose and claim that a validator proved its meaning;
- include candidate identity, contact details, private analytics, credentials, URLs, raw HTML, or source snapshots in public output;
- change historical v1/v2 renderer bytes or the existing 39 accepted / 9 rejected installed-smoke semantics.

## 4. Authority and data flow

```text
validated source group
  ├── career-next-action-eligibility-v1  (sole vacancy/trigger authority)
  ├── target-vacancy-research-v1         (exact normalized vacancy signals)
  └── candidate-fact-matrix-v1           (identity-free candidate evidence)
                    │
                    ▼
private-vacancy-application-packet-v1
  ├── deterministic claim matrix
  ├── one readiness decision
  ├── private drafts and handoff
  └── no external-action authorization
                    │
                    ▼
private JSON + offline HTML
```

The packet builder captures one closed composite source group once, validates and freezes that capture, recomputes every derived relation from it, and renders only the resulting closed projection. The group contains exactly:

```text
eligibility_group
candidate_fact_group
```

`eligibility_group` contains the eligibility artifact plus the six independent inputs required by its existing validator: `research`, `executive_dossier`, `market_dossier`, `gap_response`, `gap_assessment`, and nullable `provider_research`. `candidate_fact_group` contains the fact-matrix artifact plus its exact closed builder input. The target vacancy research is `eligibility_group.research`; it is not accepted again under a second key. Crossed dates, crossed snapshots, or mismatched source groups fail closed. The builder performs no live-currentness check and makes no claim that a vacancy remains open after the supplied `as_of_date`.

## 5. Candidate fact matrix contract

### 5.1 Top-level fields

`candidate-fact-matrix-v1` contains exactly:

```text
schema_version
locale
case_scope
signal_vocabulary
sources
facts
source_snapshot
```

Rules:

- `schema_version = "candidate-fact-matrix-v1"`.
- `locale` is `es` or `en`.
- `case_scope = "single_candidate"`; no candidate identifier is emitted.
- `signal_vocabulary = "candidate-claim-signal-v1"`.
- all objects are closed (`additionalProperties: false`).
- arrays are bounded, non-empty where specified, and use unique stable IDs.
- strings are trimmed, length-bounded, control-character-free, and must not contain URLs or HTML.

### 5.2 Sources

Each `sources[]` row contains exactly:

```text
source_id
source_type
evidence_state
captured_at
```

- `source_id`: `FS-001` through `FS-020`, contiguous in source order.
- `source_type`: `cv | professional_profile | portfolio | interview_notes | candidate_statement | verified_record`.
- `evidence_state`: `verified | candidate_reported | inferred | unknown`.
- `captured_at`: common ISO-8601 UTC timestamp for the captured group.

The artifact stores no source path, filename, URL, account, organization-private identifier, or raw document body.

Source type constrains the maximum evidence state. Only `verified_record` may
carry `evidence_state=verified`. `cv`, `professional_profile`, `portfolio`,
`interview_notes`, and `candidate_statement` may carry only
`candidate_reported | inferred | unknown`. This is a structural ceiling, not
proof that every verified record is sufficient; downstream relation, conflict,
and confidentiality gates still apply.

### 5.3 Facts

Each `facts[]` row contains exactly:

```text
fact_id
fact_type
evidence_state
source_ids
signal_bindings
signal_relation
conflict_state
confidentiality
```

- `fact_id`: `F-001` through `F-100`, contiguous in deterministic source order.
- `fact_type`: `skill | experience | outcome | credential | portfolio_evidence | work_preference | constraint`.
- `evidence_state`: the weakest supporting state across `source_ids`.
- `source_ids`: 1–5 valid source IDs, ordered and unique.
- `signal_bindings`: 0–20 closed `{kind, signal}` rows, ordered by `kind` and then `signal`, unique by the complete pair. `kind` is `requirement | eligibility_gate`. Requirement signals use the exact finite `candidate-claim-signal-v1` catalog: `authentication | certificate_management | incident_response | key_rotation | kubernetes | linux | observability | python | terraform`. Eligibility-gate signals use the existing seven-token enum: `work_authorization | country_geography | work_arrangement | language | seniority | experience_floor | employment_arrangement`. The explicit kind prevents a vacancy requirement such as `language` from joining a gate constraint.
- `signal_relation`: `supports | contradicts | unknown`.
- `conflict_state`: `clear | conflicting | superseded`.
- `confidentiality`: `usable | review_required | forbidden`.

For `usable` and `review_required`, `signal_bindings` contains 1–20 entries. For `forbidden`, `signal_bindings` is exactly empty, `signal_relation=unknown`, and the fact can never enter a claim or draft. `signal_relation=contradicts` is allowed only for `fact_type=constraint`; it becomes a readiness blocker only with `evidence_state=verified`. A candidate-reported fact may be usable, but its downstream confidence cannot exceed `medium` and its evidence state is never upgraded.

### 5.4 Fact-matrix builder input and behavior

The builder accepts one closed private input containing exactly:

```text
locale
captured_at
sources
facts
```

Normative raw-input contract:

| Field | Type and bounds | Ordering and uniqueness |
|---|---|---|
| `locale` | enum `es | en` | scalar |
| `captured_at` | ISO-8601 UTC string, exactly `YYYY-MM-DDTHH:MM:SSZ` | scalar |
| `sources` | array, 1–20 rows | source order is authoritative; duplicate canonical rows reject |
| `sources[].source_type` | enum from §5.2 | closed row |
| `sources[].evidence_state` | enum from §5.2 | closed row |
| `facts` | array, 1–100 rows | fact order is authoritative; duplicate canonical rows reject |
| `facts[].fact_type` | enum from §5.3 | scalar |
| `facts[].source_ordinals` | array, 1–5 integers in `1..len(sources)` | ascending and unique |
| `facts[].signal_bindings` | array, 0–20 closed `{kind, signal}` rows from the §5.3 versioned catalog | `kind`, then `signal`; unique complete pairs; zero only for forbidden facts |
| `facts[].signal_relation` | enum from §5.3 | scalar |
| `facts[].conflict_state` | enum from §5.3 | scalar |
| `facts[].confidentiality` | enum from §5.3 | scalar |

Every source row has exactly `source_type` and `evidence_state`; every raw fact row has exactly the six listed fact keys. The raw builder input contains no narrative field: evidence notes remain in the private source documents and are never accepted, snapshotted, logged, or projected by this contract. `source_ordinals` becomes the ordered output `source_ids`. Output source rows preserve input order and receive contiguous `FS-001..FS-020`; output facts preserve input order and receive contiguous `F-001..F-100`.

Evidence ordering is explicit: `unknown < inferred < candidate_reported < verified`. Output `facts[].evidence_state` is the minimum state across the referenced sources.

The builder assigns all IDs, validates normalized signal tokens, computes weakest evidence state and rejects:

- duplicate or discontinuous IDs after reconstruction;
- unknown source references;
- forbidden facts with signal bindings or a non-unknown relation;
- a non-constraint fact with `signal_relation=contradicts`;
- identity/contact/private-analytics fields at any depth;
- any narrative or caller-authored derived-prose field, including the prior `fact_text` shape;
- any signal outside the exact versioned catalog, crossed signal kind, unordered pair, or duplicate binding;
- crossed locale or capture timestamps;
- mutable, exception-throwing, oversized, recursive, or duplicate-key inputs.

The builder and validator use the same immutable snapshot. Diagnostics are fixed, generic, and never echo source values.

### 5.5 Fact-matrix source snapshot

`source_snapshot` is one string matching `^snap-candidate-facts-sha256-[0-9a-f]{64}$`. It is the SHA-256 of the canonical closed builder input after snapshotting and before any IDs or derived fields are assigned. The validator receives that same captured source group, recomputes the digest, rebuilds the matrix, and compares the complete artifact.

## 6. Private vacancy application packet contract

### 6.1 Top-level fields

`private-vacancy-application-packet-v1` contains exactly:

```text
schema_version
locale
as_of_date
target_binding
readiness
requirement_evidence
unsupported_or_missing_claims
draft_materials
claim_review
first_interview_prep_handoff
tracking_proposal
approval_boundary
source_snapshot
```

Rules:

- `schema_version = "private-vacancy-application-packet-v1"`.
- `locale` equals all three validated sources and `as_of_date` equals the common eligibility/target-research date.
- all objects are closed and all arrays follow the normative bounds below.
- every visible string is localized and derived from closed copy tables, validated public vacancy title/organization/requirement metadata, or the closed candidate-signal catalog; no candidate-authored prose is projected.

Normative packet bounds and IDs:

| Collection or value | Bound / pattern | Ordering |
|---|---|---|
| `requirement_evidence` | 1–30 rows; source `requirement_id` pattern `^V-[0-9]{3}-R-[0-9]{2}$` | selected-vacancy source order |
| `requirement_evidence[].fact_ids` | 0–100 fact IDs | every non-forbidden, non-superseded exact-signal match, unique in fact-matrix order |
| `unsupported_or_missing_claims` | 0–30 rows | requirement order |
| `draft_materials.cv_bullets` | 0–20 rows; IDs `^D-CV-[0-9]{3}$` | requirement then fact order |
| `draft_materials.recruiter_summary` | 0–5 rows; IDs `^D-RS-[0-9]{3}$` | requirement then fact order |
| `draft_materials.message_angle` | 0–5 rows; IDs `^D-MA-[0-9]{3}$` | requirement then fact order |
| `claim_review` | 0–60 rows; IDs `^C-[0-9]{3}$` | draft rows in surface order, then null-draft required rows in requirement order |
| readiness requirement IDs | 0–30 rows | vacancy order, unique |
| readiness gate tokens | 0–7 rows, existing eligibility-gate enum only | target gate order, unique |
| handoff requirement IDs | 0–30 rows | vacancy order, unique |
| handoff fact IDs | 0–100 rows | fact order, unique |
| prohibited actions | exact fixed list from §6.11 | listed order |

All ID references must resolve exactly once to the same captured group. Arrays that are empty by state use `maxItems: 0`; otherwise their stated bounds are enforced. Every scalar inherited from a source retains that source's schema bound.

Additional row bounds are normative: each draft has 1–5 `fact_ids` and 1–5 `requirement_ids`; each non-null claim-review row has the same bounds and must equal its draft's references; each null-draft claim-review row has 0–5 `fact_ids` and exactly one `requirement_id`. CV-bullet and message-angle text is 1–800 Unicode scalar values; recruiter-summary text is 1–3,200; all other localized headlines, rationales, review notes, and next steps are 1–500. Fixed locale template/separator copy contributes at most 200 characters per projected draft, so the maximum raw fact/signal inputs cannot overflow these surface bounds. `as_of_date` uses the existing `YYYY-MM-DD` contract. All booleans and enums are the exact constants or closed values stated in their sections.

### 6.2 Target binding

`target_binding` contains exactly:

```text
vacancy_id
vacancy_title
organization_label
eligibility_state
next_safe_action
```

It is recomputed from the eligibility artifact and its validated source group. `next_safe_action` must equal `prepare_private_vacancy_packet`. The builder accepts no caller-supplied vacancy selector and rejects any mismatch.

### 6.3 Requirement/evidence rows

Each `requirement_evidence[]` row contains exactly:

```text
requirement_id
signal
priority
fact_ids
coverage
confidence
```

- `requirement_id` is copied unchanged from the selected vacancy requirement; rows preserve validated source order.
- `signal` is an exact normalized vacancy signal.
- `priority`: `required | preferred | contextual`.
- `fact_ids` equals every non-forbidden, non-superseded exact-signal match, ordered uniquely by fact-matrix order.
- `coverage`: `supported | partial | missing | conflicting | review_required`.
- `confidence`: `high | medium | low | unknown`.

Matching is literal after the existing normalized-signal validation and requires `kind=requirement`. A selected-vacancy requirement outside `candidate-claim-signal-v1` has no admissible candidate binding and follows the existing `missing`/`revise_first` path without reflecting candidate input. The builder does not create aliases, use substring matching, or infer semantic entailment. Candidate-reported-only support caps confidence at `medium`; inferred-only support is `review_required` or weaker.

Priority is a closed mapping from the existing target-vacancy contract: `must_have -> required`, `preferred -> preferred`, and `responsibility_only -> contextual`. Supporting matches require `signal_relation=supports`; an exact `contradicts` match is represented as conflicting evidence, never as support.

Coverage and confidence use this total, ordered derivation:

1. `conflicting / unknown` when any exact matching fact is `conflict_state=conflicting`, any verified contradicting match exists, or both supporting and contradicting matches exist.
2. `supported / high` when one or more exact matches are usable, clear, `signal_relation=supports`, and verified, with no candidate-reported/inferred/unknown evidence state, review-required confidentiality, unknown relation, or contradicting match.
3. `supported / medium` when one or more exact matches are usable, clear, `signal_relation=supports`, and at least one is candidate-reported, with no inferred/unknown evidence state, review-required confidentiality, unknown relation, or contradicting match.
4. `partial / low` when usable clear support exists but any additional exact match has inferred/unknown evidence state, review-required confidentiality, or `signal_relation=unknown`, and no conflicting rule above applies.
5. `review_required / low` when exact matches exist but none is admissible support, and at least one has inferred/unknown evidence state, review-required confidentiality, `signal_relation=unknown`, or non-verified contradicting evidence.
6. `missing / unknown` when no non-forbidden exact match exists.

Superseded and forbidden facts never enter the derivation. A verified contradicting candidate constraint against a vacancy eligibility-gate token is handled by readiness `stop`; a requirement-token contradiction uses the table above.

### 6.4 Unsupported or missing claims

Each `unsupported_or_missing_claims[]` row contains exactly:

```text
requirement_id
signal
reason
next_private_step
```

- `reason`: `missing_evidence | conflicting_evidence | review_required`.
- `next_private_step`: fixed localized copy such as verify a fact, remove a claim, or collect a private example.

No row repeats source prose, filenames, URLs, or private identifiers.

Reason mapping is total: `missing -> missing_evidence`, `conflicting -> conflicting_evidence`, and `partial | review_required -> review_required`. Supported requirements do not appear in this array.

### 6.5 Draft materials

`draft_materials` contains exactly:

```text
cv_bullets
recruiter_summary
message_angle
```

Each draft entry contains exactly:

```text
draft_id
text
fact_ids
requirement_ids
evidence_state
```

Draft copy is built only from fixed localized sentence templates keyed by `surface`, `fact_type`, and the matched catalog signal. The visible signal label comes from a closed ES/EN copy table; the builder never accepts or projects candidate-authored prose. These are bounded application scaffolds for private review, not model-expanded accomplishment claims.

Only facts with `confidentiality=usable`, `conflict_state=clear`, and `signal_relation=supports` may produce draft text. Candidate-reported facts remain labeled `candidate_reported`. Missing, inferred-only, conflicting, superseded, review-required, contradicting, or forbidden facts cannot become affirmative draft claims.

### 6.5.1 Deterministic draft projection

For one requirement, an admissible fact is an exact-signal match with `confidentiality=usable`, `conflict_state=clear`, `signal_relation=supports`, and `evidence_state` of `verified` or `candidate_reported`. Facts always retain fact-matrix order.

Projection occurs before ID assignment:

| Surface | Exact cardinality and selection | References and text source |
|---|---|---|
| `cv_bullets` | one row for each of the first 20 supported requirements in vacancy order | exactly the first admissible fact for that requirement; closed locale template keyed by `fact_type` and the matched catalog signal label |
| `recruiter_summary` | exactly one row when at least one required requirement is supported, otherwise zero | first five supported required requirements; first admissible fact for each, deduplicated in fact order; closed locale template and catalog labels in that same order |
| `message_angle` | exactly one row when any requirement is supported, otherwise zero | prefer the first supported requirement in vacancy order whose catalog signal equals the eligibility-selected signal; otherwise the first supported required requirement; otherwise the first supported requirement; reference its first admissible fact; closed locale template |

IDs are assigned only after the surface-specific cap and selection rules run. Each draft's `requirement_ids` and `fact_ids` are exactly the selected references above. Its `evidence_state` is the weakest referenced fact state under the §5.4 ordering.

### 6.6 Claim review

Each `claim_review[]` row contains exactly:

```text
claim_id
draft_id
fact_ids
requirement_ids
decision
confidence
review_note
```

- `draft_id`: a valid draft ID or `null`.
- `decision`: `use | revise | omit`.
- `confidence`: `high | medium | low | unknown`.
- `review_note`: fixed localized, bounded copy.

Every draft has exactly one claim-review row with a non-null `draft_id`. Every partial, conflicting, review-required, or missing required requirement has exactly one additional claim-review row with `draft_id=null`; these rows use closed localized review copy and do not pretend that draft prose exists. Null rows select the first five non-forbidden, non-superseded exact matches in fact order; a missing row has an empty `fact_ids` array.

Claim derivation is exact:

- verified-only draft -> `use / high`;
- any candidate-reported draft -> `use / medium`;
- partial or review-required null row -> `revise / low`;
- conflicting null row -> `revise / unknown`;
- missing null row -> `omit / unknown`.

This makes all three decisions reachable without generating an unsupported affirmative claim.

### 6.7 Readiness decision

`readiness` contains exactly:

```text
state
headline
rationale
blocking_requirement_ids
blocking_gate_tokens
revision_claim_ids
manual_review_required
external_action_authorized
```

Constants:

- `manual_review_required = true`.
- `external_action_authorized = false`.

Precedence is deterministic:

1. `stop` when a vacancy eligibility gate is contradicted by an exact-token, verified candidate constraint whose `conflict_state=clear` and which is not superseded.
2. `revise_first` when any required requirement is partial, missing, conflicting, review-required, or supported only by evidence that cannot form a claim; or any claim-review row is `revise`/`omit`.
3. `ready_for_manual_authorization` only when all required requirements are supported, at least one affirmative draft and its `use` claim exist, every emitted claim is `use`, no blocker exists, and all source bindings validate. An all-optional or otherwise empty packet is `revise_first`, never vacuously ready.

Unknown evidence never yields `stop` by itself. It yields `revise_first`. The headline and rationale come from closed ES/EN copy tables. `ready_for_manual_authorization` is a private-review readiness label only and confers no permission.

An eligibility artifact whose `recommended_next_action` is not `prepare_private_vacancy_packet` is invalid input and produces no packet; it is not converted into a `stop` artifact. Eligibility-gate contradiction is derived only by matching the closed target gate token to a non-superseded candidate constraint with `signal_relation=contradicts`, `evidence_state=verified`, and `conflict_state=clear`.

`blocking_gate_tokens` records those exact gate enum values in target order. `blocking_requirement_ids` equals all required requirement IDs whose coverage is not `supported`, in vacancy order. Both arrays are ordered and unique; `blocking_gate_tokens` is non-empty for `stop` and empty otherwise. `blocking_requirement_ids` is empty for `ready_for_manual_authorization` and may coexist with a higher-precedence gate blocker in `stop`.

`revision_claim_ids` equals the ordered IDs of every `claim_review` row whose decision is `revise` or `omit`; it is empty for `ready_for_manual_authorization` and for the fully suppressed `stop` state.

### 6.8 Stop-state suppression

When `readiness.state=stop`:

- `draft_materials` arrays are empty;
- `claim_review` is empty;
- `first_interview_prep_handoff` is present only as a suppressed object;
- `tracking_proposal.record_state = "not_proposed"` and `event_kind = "none"`;
- the HTML renders one stop decision, bounded reasons, and no material that resembles an application draft.

### 6.9 Interview handoff

`first_interview_prep_handoff` contains exactly:

```text
state
interview_stage
vacancy_id
requirement_ids
fact_ids
next_private_step
```

- `state`: `available | suppressed`.
- `interview_stage = "unknown"` in every state because packet readiness is not evidence of a user-stated interview stage.
- it is available only for `ready_for_manual_authorization` and means only that manual re-entry into interview preparation is available; it carries IDs, not copied source prose.
- when available, `next_private_step` is fixed localized copy requesting the user-stated interview stage before routing to interview preparation.
- it does not schedule, send, or start interview preparation automatically.

`vacancy_id` always equals `target_binding.vacancy_id`. When available, `requirement_ids` contains every supported requirement in vacancy order and `fact_ids` contains their admissible supporting facts, ordered and deduplicated by fact-matrix order. When suppressed, both arrays are empty. `next_private_step` is selected solely by `locale` and `state`; no caller prose contributes.

### 6.10 Tracking proposal

`tracking_proposal` contains exactly:

```text
record_state
event_kind
vacancy_id
outcome_state
manual_reentry_required
auto_start
```

- non-stop: `record_state="proposed"`, `event_kind="application_packet_drafted"`, `outcome_state="draft_only"`;
- stop: `record_state="not_proposed"`, `event_kind="none"`, `outcome_state="not_started"`;
- always: `manual_reentry_required=true`, `auto_start=false`.
- always: `vacancy_id = target_binding.vacancy_id`.

This object is a proposed handoff only. It does not write to the outcomes tracker.

### 6.11 Approval boundary

`approval_boundary` contains exactly:

```text
artifact_state
allowed_next_step
prohibited_actions
authorization_required
```

- `artifact_state = "private_draft"`.
- `allowed_next_step = "manual_private_review"`.
- `prohibited_actions` is the fixed ordered list `external_edit, upload, export, share, submit, publish, message, connect, apply, schedule, calendar_create, purchase, enroll`.
- `authorization_required = true`.

### 6.12 Source snapshot

`source_snapshot` contains exact SHA-256 bindings for:

```text
eligibility
target_vacancy_research
candidate_fact_matrix
aggregate
```

- `eligibility`: `^snap-next-action-eligibility-v1-sha256-[0-9a-f]{64}$`.
- `target_vacancy_research`: `^snap-market-sha256-[0-9a-f]{64}$`.
- `candidate_fact_matrix`: `^snap-candidate-fact-matrix-v1-sha256-[0-9a-f]{64}$`.
- `aggregate`: `^snap-private-vacancy-packet-sources-v1-sha256-[0-9a-f]{64}$`.

Derivation is exact:

- `eligibility` is produced by the existing `snapshot_for_career_next_action_eligibility_v1` function.
- `target_vacancy_research` is produced by the existing canonical target-research snapshot function used for `source_research_snapshot`.
- `candidate_fact_matrix` is its stated prefix plus SHA-256 of canonical UTF-8 JSON for the validated matrix artifact (`sort_keys=true`, separators `,` and `:`, `ensure_ascii=false`). It is distinct from §5.5, which binds the raw fact-builder input.
- `aggregate` is its stated prefix plus SHA-256 of canonical UTF-8 JSON for the array `[eligibility_artifact, target_research_artifact, candidate_fact_matrix_artifact]` in exactly that order.

Validators recompute all four values and all derived rows. Crossed dates, crossed snapshots, tampered values, or caller-derived snapshots fail closed. “Crossed” means the artifacts do not share the locale/date/snapshot relations defined here; it does not mean elapsed wall-clock age or a live vacancy-status lookup.

Before packet projection, the existing eligibility validator runs against all seven values in `eligibility_group`; the fact-matrix validator likewise runs against both values in `candidate_fact_group`. The eligibility artifact's existing `source_research_snapshot` must equal the canonical research binding recomputed from `eligibility_group.research`, and its `selected_vacancy_id` must resolve to exactly one active vacancy. `vacancy_title` comes from that vacancy's `title`; `organization_label` comes from the exact `employer_id -> display_name` join. No display field is accepted from the caller.

## 7. Output behavior and diagnostics

The JSON writer is atomic:

1. validate and build in memory;
2. serialize canonical UTF-8 JSON;
3. write a mode-0600 temporary file in the destination directory;
4. fsync and replace the destination;
5. remove the temporary file on any failure.

The CLI writes no partial stdout or destination file on failure. Invalid source, schema, rendering, filesystem, timeout, duplicate-key, mutable-input, or ordinary exception boundaries return a fixed generic diagnostic and never echo source values, private paths, exception messages, IDs, or draft content.

Runtime value scanning occurs before projection and again on the closed artifact. The candidate fact input contains no prose field; its enum/token/ID fields are governed by their closed schema and finite signal catalog. Packet prose is generated only from closed copy tables and validated public vacancy metadata, then scanned for identity markers, email/phone/address-like contact data, URLs, HTML, raw private analytics, controls, and authentication-secret material. Authentication-secret material means any of:

- an assignment of a value to `password`, `passwd`, `api_key`, `access_key`, `refresh_token`, `bearer_token`, `client_secret`, or `private_key`, allowing case and space/hyphen/underscore variants;
- a `Bearer` value of eight or more token characters;
- a PEM private-key boundary;
- an opaque value of eight or more characters prefixed by `ghp_`, `gho_`, `ghu_`, `ghs_`, `ghr_`, `sk-`, `AKIA`, `xoxb-`, `xoxa-`, `xoxp-`, `xoxr-`, or `xoxs-`.

This rule does not reject professional qualifications or security terminology. Positive cases must preserve `authentication`, `certificate_management`, `key_rotation`, and professional certificate names; hostile cases must prove exact generic diagnostics, no value/path/exception echo, and no partial JSON, HTML, receipt, or destination file.

## 8. Private HTML product surface

The HTML is a compact offline review page, not an extension of the executive dossier dashboard. It uses no JavaScript, forms, buttons, external links, remote assets, upload/export/apply controls, or tracking pixels.

Visible hierarchy:

1. private/draft header;
2. one primary readiness decision;
3. packet context;
4. requirements and evidence;
5. unsupported or missing evidence;
6. draft CV bullets, recruiter summary, and message angle;
7. semantic claim-review table;
8. first-interview handoff;
9. proposed tracking event;
10. approval boundary;
11. footer.

Stop state suppresses sections 6–9 except the explicitly suppressed handoff/tracking summary required by the contract.

### 8.1 DOM and accessibility

- exactly one `<h1>`;
- stable IDs for the readiness title, each major section, and each claim row;
- `<main>` plus labelled `<section>`/`<article>` landmarks;
- definition lists for packet metadata and approval boundaries;
- semantic lists for requirements and drafts;
- one real table for claim review with `<caption>`, `<thead>`, scoped headers, and localized accessible names;
- visible focus styles even though the surface has no action controls;
- DOM order equals reading order;
- readiness state is never conveyed by color alone.

### 8.2 Security and presentation

- CSP: `default-src 'none'; style-src 'unsafe-inline'; img-src data:` only if a bundled data image is actually used;
- all dynamic text HTML-escaped;
- no source IDs, snapshots, paths, URLs, raw controls, or private metadata rendered;
- supports dark mode, forced-colors, reduced motion, and print;
- print retains private/draft and no-external-action boundaries on every page where practical through repeated header/footer CSS.

No browser, print-preview, or assistive-technology claim is made until empirical QA is run.

## 9. Superdesign generation contract

This is a new target, `vacancy-application-packet`, in the existing Superdesign project. The saved executive-dossier draft is not reused because its hierarchy is inappropriate for the compact private packet.

Before generation, share exactly these five repository files and no private data:

1. `.superdesign/design-system.md`
2. `plugins/professional-growth-coach/assets/private-recruiter-reply-triage-v1.html`
3. `plugins/professional-growth-coach/assets/private-recruiter-reply-triage-v1.css`
4. `plugins/professional-growth-coach/skills/optimize-career-assets/SKILL.md`
5. `plugins/professional-growth-coach/skills/optimize-career-assets/references/asset-workflow.md`

Generation prompt:

> Design one compact, premium, private/offline HTML review page for a vacancy-specific application packet. Preserve the repository's editorial executive style, restrained indigo/coral palette, dense evidence cards, dark-mode and print behavior, but do not reproduce the executive dossier dashboard. The page must show exactly one primary readiness decision (`revise_first`, `ready_for_manual_authorization`, or `stop`), followed by vacancy context, requirement/evidence coverage, missing or unsupported claims, deterministic private draft materials, a semantic claim-review table, a first-interview handoff, a proposed tracking event, and an explicit approval boundary. It must never look like an application form and must contain no buttons, forms, external links, upload/export/apply controls, JavaScript, candidate identity, source IDs, snapshots, URLs, or external-action authorization. Include ES and EN copy considerations, accessible landmarks and table semantics, forced-colors, reduced-motion, dark mode, and print. In `stop`, suppress all draft materials and secondary action detail. Return one self-contained visual proposal suitable for translation into the existing Python renderer and CSS asset.

Only one proposal is generated. The result is evaluated against the contract before any code is derived. Repository HTML/CSS remains authoritative; generated output is design evidence, not production code.

## 10. Renderer and CLI receipt

Full packet validation always requires the complete captured composite source
group. The packet validator returns an opaque immutable validated-packet
snapshot that carries the frozen artifact and cannot be constructed from an
artifact alone. The renderer consumes only that opaque snapshot and returns a
string; it exposes no artifact-only validation path. The JSON writer and HTML
renderer/writer accept the same opaque snapshot in the in-process packet
workflow, so JSON, HTML, and receipt derive from one composite capture.
Standalone CLI entry points capture the artifact and complete source group
together before obtaining the opaque snapshot. All paths reuse the
generic/no-echo/atomic boundary.

Successful CLI JSON receipt contains exactly:

```text
artifact_type
schema_version
locale
readiness_state
vacancy_id
output_path
private_draft
external_action_authorized
```

It never contains candidate facts, draft text, source IDs, snapshots, organization-private values, or URLs. `private_draft=true` and `external_action_authorized=false` are fixed.

Receipt values are closed: `artifact_type="private_vacancy_application_packet"`; `schema_version`, `locale`, `readiness_state`, and `vacancy_id` equal the corresponding validated packet values; `output_path` equals the writer's resolved destination path after the atomic replace. Any mismatch is a generic no-output failure.

### 10.1 Root routing and client delivery

The root `professional-growth-coach` skill and `references/routing.md` gain an explicit packet branch. Existing explicit recruiter-practice/reply-triage branches retain higher precedence. Otherwise, when the supplied composite group validates and eligibility recomputes to `recommended_next_action=prepare_private_vacancy_packet`, the root routes to `optimize-career-assets` and treats the validated JSON/HTML plus CLI receipt as execution proof. Missing composite inputs produce a bounded request for the missing private evidence; they do not fall through to an untyped packet.

The client delivery contains exactly these visible sections:

```text
private_packet_summary
readiness_decision
verified_local_artifact
approval_boundary
```

It ends with the localized sentence “No external action is performed.” The delivery contains no `candidate_id`, router contract, `module_execution_packet`, internal fact/source/snapshot IDs, raw source prose, or hidden authorization. The verified local artifact is a private local link; no upload or export occurs.

## 11. Privacy and package registration

Every new production, schema, asset, fixture, and test path is registered in exact package/static inventories. The repository privacy scanner receives closed recognizers only for canonical synthetic fixtures. A recognizer must:

- match an exact registered path and exact root shape;
- validate bounds and synthetic provenance;
- rebuild both artifacts from source inputs;
- compare exact canonical sibling outputs;
- scan the closed candidate fact projection, bounded public vacancy-research projection, and generated packet copy;
- fall back to the generic scanner for any unregistered, nested, mutated, or coordinately rebuilt near miss.

There is no broad ignore, suffix allowlist, or path-prefix exclusion.

## 12. Compatibility

- Existing eligibility, learning v1/v2/v3, dossier v1/v2/v3, recruiter-triage, and outcome contracts remain unchanged.
- Historical v1/v2/no-market HTML byte pins remain exact.
- Existing installed smoke remains 39 accepted / 9 rejected; packet cases are additive and separately enumerated.
- Existing textual application-claim evaluator behavior remains pinned.
- No existing public or private schema gains optional fields.

## 13. Acceptance matrix

The focused TDD suite must prove at least:

1. candidate fact matrix exact fields, bounds, stable IDs, evidence-state propagation, confidentiality, and identity-free output;
2. forbidden fact zero-binding conditional and no downstream use;
3. exact-signal matching with no alias, substring, or prose inference;
4. candidate-reported support retained and capped at medium confidence;
5. verified constraint contradiction yields `stop`;
6. unknown/partial/missing/conflicting/review-required required evidence yields `revise_first`;
7. complete usable evidence yields `ready_for_manual_authorization` with authorization still false;
8. all readiness states have exactly one primary decision and correct suppression;
9. deterministic ES/EN copy and ordering;
10. claim rows join exact draft, fact, and requirement IDs;
11. all six coverage/confidence derivation rows—including usable verified `signal_relation=unknown` with and without admissible support—and all three claim decisions are reachable and mutually exclusive;
12. gate blockers populate `blocking_gate_tokens`, while invalid eligibility authority produces no artifact;
13. crossed-date/crossed-snapshot/tampered groups reject, including mutations in every eligibility upstream source and the raw fact source group;
14. mutable, duplicate-key, recursive, oversized, exception-throwing, and hostile mappings fail closed;
15. builder and validator each capture their composite input group once;
16. JSON writer and CLI produce no partial output and generic/no-echo diagnostics;
17. the candidate fact input rejects every narrative or unknown field, while hostile identity/contact/authentication-secret/URL/HTML values in remaining packet sources fail generically with no echo or partial output and the closed signal catalog remains accepted;
18. root packet routing wins only at its defined precedence and emits the exact identity-free client delivery;
19. HTML has exact DOM/ARIA structure, no forbidden controls/content, and safe escaping;
20. dark/forced-colors/reduced-motion/print rules are statically present;
21. canonical synthetic fixtures rebuild byte-for-byte;
22. package/static/privacy inventories fail for missing, extra, linked, or non-regular paths;
23. existing v1/v2/no-market bytes and the historical 39/9 installed semantic matrix remain pinned;
24. installed exact-cache execution imports only from the verified private snapshot and emits the separate additive packet receipt described below.

## 14. Canonical fixtures

Use a small deterministic matrix, generated only by builders:

- ES `ready_for_manual_authorization`;
- EN `ready_for_manual_authorization`;
- ES `revise_first` from missing required evidence;
- EN `revise_first` from candidate-reported/review-required evidence;
- ES `stop` from a verified candidate constraint;
- EN `stop` from a verified candidate constraint.

Each scenario directory stores one locale-matched `sources.json`, generated `candidate-fact-matrix.json`, and generated `application-packet.json`. Fixtures use synthetic role and organization labels and contain no candidate identity/contact values.

### 14.1 Installed packet matrix

The additive installed matrix uses these exact accepted case IDs:

```text
packet_ready_es
packet_ready_en
packet_revise_missing_es
packet_revise_review_en
packet_stop_constraint_es
packet_stop_constraint_en
```

It uses these exact rejected case IDs:

```text
packet_wrong_action
packet_crossed_research
packet_crossed_fact_source
packet_tampered_matrix
packet_tampered_packet
packet_alias_signal
packet_substring_signal
packet_caller_prose
packet_private_value
packet_confidential_claim
packet_hostile_mapping
packet_writer_cli_partial
```

Every case executes installed modules from the verified private snapshot. Rejected cases assert generic diagnostics, no echo, and no partial output where applicable.

## 15. Planned file boundaries

New production boundaries:

- candidate fact matrix schema, builder, validator, and canonical fixtures;
- private vacancy application packet schema, builder, validator, and canonical fixtures;
- packet renderer, atomic writer, CLI, HTML template, and CSS asset;
- focused contract/render/privacy tests.

Modified boundaries:

- `optimize-career-assets` routing and workflow references;
- root `skills/professional-growth-coach/SKILL.md` and `skills/professional-growth-coach/references/routing.md` for the exact packet trigger and delivery exception;
- plugin/package/static/privacy inventories and their tests;
- installed-smoke harness, release docs, and attestation parser/tests;
- Superdesign init/resume evidence only as required by the generation workflow.

No other renderer or product contract is refactored.

The new typed packet replaces the older prose-only `Application packet` field list in `optimize-career-assets/SKILL.md`, including its `candidate_id` field. The skill will point to this versioned, identity-free schema rather than maintain two competing packet contracts. This is a documentation migration, not an optional extension of the old shape.

## 16. Release sequence

1. Implement under TDD in task-sized commits and obtain independent spec/code review.
2. Run focused, package, privacy, static, source-discovery, and official release gates.
3. Treat the existing installed attestation as stale evidence until release.
4. Create one manifest-only cachebuster commit A after all source gates pass.
5. From the first plugin-tree change through exact A, the checked-in installed attestation is expected to be stale. Every source run must isolate by exact name the single `FullPluginIntegrationTests.test_checked_in_attestation_is_bound_to_immutable_git_archive_evidence` failure and require every other test green; any additional failure blocks progress. On B the complete official validator, including that named test, must return entirely green.
6. Push A to `origin/main`, fetch, and verify live remote SHA.
7. Align the clean public checkout safely, install the exact public selector, and resolve exactly one enabled version.
8. Compare immutable A archive to the exact cache: inventory, every SHA-256, aggregate digest, `diff -qr`, path/symlink/private-metadata/bytecode checks.
9. Run installed packet and historical semantic smokes from the verified private snapshot only.
10. Preserve every existing attestation field and value contract, including `installed_semantic_accepted_smokes=39/39` and `installed_semantic_rejected_smokes=9/9`. Add exactly six fields:
    - `installed_packet_accepted_smokes=6/6`
    - `installed_packet_rejected_smokes=12/12`
    - `installed_packet_accepted_case_ids` = the §14.1 accepted IDs joined by commas in listed order
    - `installed_packet_rejected_case_ids` = the §14.1 rejected IDs joined by commas in listed order
    - `installed_packet_artifact_provenance=validated_installed_builder_output_only`
    - `installed_packet_renderer_provenance=validated_installed_renderer_output_only`
    The two matrices are never merged into a misleading 45/21 total. The attestation parser requires exactly the prior complete field set plus these six keys and rejects missing, extra, duplicate, reordered-ID, stale, unresolved, or crossed values. Existing file-count, source/cache aggregate-digest, and `installed_import_boundary=verified_private_snapshot_only` fields continue to bind both matrices to the installed package.
11. Create attestation-only commit B containing that exact installed evidence.
12. Validate the real attestation file against independently derived Git commit/tree/archive/version/count/digest expectations, including unresolved/stale/duplicate/crossed negative controls.
13. Run the full official validator on B.
14. Push B to `origin/main`, fetch, verify remote/public/installed/parity again, and finish clean.

No release step broadens authorization to any career action.

## 17. Explicit rulings

- Eligibility owns vacancy selection; the packet has no second target selector.
- Readiness is private-review readiness, not application readiness or permission.
- The gate proves exact ID/signal/evidence linkage, not semantic entailment of arbitrary prose.
- Deterministic templates are required for all affirmative draft claims.
- `stop` is reserved for exact-token, verified blocked constraints; invalid packet authority fails with no output and uncertainty means revise.
- Candidate-reported evidence may support a medium-confidence claim but is never silently upgraded.
- One primary action surface is shown; secondary handoffs are descriptive and non-interactive.
- Superdesign receives only the five listed repository files and synthetic design requirements.
- Visual/print/AT verification is reported only if empirically executed.
- All §6.11 prohibited actions remain outside this increment.
