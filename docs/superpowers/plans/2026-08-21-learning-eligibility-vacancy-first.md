# Learning Eligibility and Vacancy-First Decision Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Gate learning on an explicit public vacancy/signal choice, recurrence in at least two active vacancies, and a candidate-confirmed gap, then surface exactly one private weekly action and zero or one learning decision.

**Architecture:** Add an independently persisted closed response, a source-resolved assessment, a fully recomputed eligibility gate, and learning decision v3 in dependency order. Every new entrypoint snapshots the complete input group once before validation, every validator rebuilds derived output from independent sources, and the renderer adds a v3-only weekly-decision surface without changing historical v1/v2 bytes.

**Tech Stack:** Python 3.11 standard library, JSON Schema draft 2020-12, deterministic SHA-256 snapshots, `unittest`, HTML/CSS, Superdesign CLI, existing package/static/privacy/release harnesses.

**Spec:** `docs/superpowers/specs/2026-08-21-learning-eligibility-vacancy-first-design.md`

## Global Constraints

- Preserve every v1/v2 schema, builder, validator, fixture, renderer composition, and protected no-market byte snapshot unchanged.
- The response accepts public `V1`–`V5` and `L1`–`Ln` ordinals only; no caller may supply a private vacancy/provider ID or free-form semantic prose.
- The decision threshold is recurrence in at least two distinct active vacancies; scores, coverage bands, source prose, employer identity, and title similarity never affect eligibility.
- Exactly one next action is projected. Only `build_bounded_proof`, `run_validation_lab`, `research_provider_option`, and `run_role_search_experiment` produce one learning row; every other action produces zero.
- Provider selection is explicit. Stable lexical display order is not ranking and never selects an option.
- Use one bounded plain snapshot for the entire new input group with depth `32`, total nodes `10_000`, items per mapping/sequence `150`, and string length `4096`; never reread original inputs after the boundary.
- Builders raise fixed generic `ValueError`; validators return one bounded generic diagnostic; renderer/writer/CLI failures do not echo values, paths, URLs, IDs, or tracebacks and leave no partial output.
- Candidate-facing HTML contains no internal IDs, snapshots, URLs, source prose, private values, raw enums, forms, buttons, or external links.
- No LinkedIn/profile edit, connection, message, application, purchase, enrollment, upload beyond approved Superdesign context, or other external career action is executed.
- Superdesign uses the cold existing-UI SOP because init is complete and no trusted resume exists. Enumerate the exact context files before upload; obtain upload/canvas approval; persist `.superdesign/resume.json`; do not claim browser, print-preview, or assistive-technology QA unless empirically run.
- Tasks 1–6 form one executable product increment. Version/install/publish occurs only after their task reviews and a clean whole-branch review in Task 7.

## File Structure

- New `plugins/professional-growth-coach/scripts/semantic_provenance_snapshot.py`: sole bounded one-pass plain-snapshot helper for the complete new v3 input group; v2 bounded-tree checks delegate to its constants/helper without semantic change.
- New `build_candidate_gap_response_v1.py` / `validate_candidate_gap_response_v1.py`: public response source, snapshot, load, and exact source binding.
- New `build_candidate_gap_assessment_v1.py` / `validate_candidate_gap_assessment_v1.py`: public ordinal resolution into private source references.
- New `build_career_next_action_eligibility_v1.py` / `validate_career_next_action_eligibility_v1.py`: exact recurrence/relation/provider decision table and localized copy.
- New `build_career_learning_decision_v3.py` / `validate_career_learning_decision_v3.py`: zero/one projection driven only by validated eligibility.
- Four new closed schemas with matching names under `plugins/professional-growth-coach/schemas/`.
- `tests/test_learning_eligibility_v3.py`: focused response, assessment, eligibility, learning, totality, tampering, and deterministic fixture contracts.
- `tests/evals/with-skill/fixtures/`: canonical response/assessment/eligibility/learning-v3 source groups.
- Existing renderer/CSS/Superdesign/tests/static/privacy/release files: v3 composition, visual contract, packaging, and publication gates.

---

### Task 1: One-Pass Input Boundary and Candidate Gap Response v1

**Files:**
- Create: `plugins/professional-growth-coach/scripts/semantic_provenance_snapshot.py`
- Create: `plugins/professional-growth-coach/schemas/candidate-gap-response-v1.schema.json`
- Create: `plugins/professional-growth-coach/scripts/build_candidate_gap_response_v1.py`
- Create: `plugins/professional-growth-coach/scripts/validate_candidate_gap_response_v1.py`
- Create: `tests/test_learning_eligibility_v3.py`
- Modify: `plugins/professional-growth-coach/scripts/build_career_learning_decision_v2.py`
- Modify: `plugins/professional-growth-coach/tests/test_private_schema_conformance.py`
- Modify: `plugins/professional-growth-coach/tests/run_static_checks.py`
- Modify: `tests/test_full_plugin.py`

**Interfaces:**
- Consumes: `validate_research(value)`, `validate_schema_instance(market, load_schema("career-market-learning-dossier-v2.schema.json"))`, `snapshot_for_market_dossier(value)`, `snapshot_for_market_dossier_v2(value)`, and optional `validate_provider_research(value)` / `snapshot_for_provider_research(value)`. Because the approved response source does not receive the executive dossier, it does not call `validate_market_dossier_v2(value, research, dossier)`; instead it loads the named closed schema, validates market shape/state/date/locale, verifies the market artifact's research snapshot against the independently validated research, and binds the complete market artifact snapshot. Task 2 performs the full research+dossier+market semantic validation before resolving private IDs.
- Produces: `bounded_plain_snapshot(group: object) -> dict[str, object]`, `bounded_tree(value: object) -> bool`, `build_candidate_gap_response_v1(research: object, market_dossier: object, response: object | None, provider_research: object | None = None) -> dict[str, object]`, `validate_candidate_gap_response_v1(value: object, research: object, market_dossier: object, provider_research: object | None = None) -> list[str]`, `snapshot_for_candidate_gap_response_v1(value: Mapping[str, object]) -> str`, and `load_candidate_gap_response_v1(path: Path) -> dict[str, object]`.
- Internal contract: `_validate_candidate_gap_response_from_frozen(frozen_group: Mapping[str, object])` and `_project_candidate_gap_response_from_frozen(...)` never capture or inspect originals. Public entrypoints capture once; Tasks 2–5 may invoke only these internal frozen-group functions with their already captured built-ins.
- The response payload has only `selected_vacancy_ordinal`, `selected_signal`, `relation`, and `selected_provider_ordinal`; `None` becomes `unavailable` or `selection_required` from validated market state.

- [ ] **Step 1: Write the response, public-ordinal, and TOCTOU RED matrix**

Create the test module with the existing `load_sibling()` pattern and fixture roots. Add these exact behaviors before production exists:

```python
def test_response_persists_public_choice_without_private_ids(self):
    sources = recurrent_sources(locale="es")
    response = RESPONSE_BUILDER.build_candidate_gap_response_v1(
        sources.research,
        sources.market,
        {
            "selected_vacancy_ordinal": "V2",
            "selected_signal": "terraform",
            "relation": "proof_gap",
            "selected_provider_ordinal": None,
        },
    )
    self.assertEqual("candidate-gap-response-v1", response["schema_version"])
    self.assertEqual("complete", response["response_state"])
    self.assertEqual("V2", response["selected_vacancy_ordinal"])
    self.assertNotIn("V-003", json.dumps(response, sort_keys=True))
    self.assertEqual([], RESPONSE_VALIDATOR.validate_candidate_gap_response_v1(
        response, sources.research, sources.market
    ))

def test_response_rejects_private_ids_free_prose_and_crossed_ordinals(self):
    sources = recurrent_sources(locale="es")
    cases = (
        {"selected_vacancy_id": "V-003", "selected_signal": "terraform", "relation": "proof_gap", "selected_provider_ordinal": None},
        {"selected_vacancy_ordinal": "V1", "selected_signal": "terraform", "relation": "proof_gap", "selected_provider_ordinal": None, "reason": "I need this"},
        {"selected_vacancy_ordinal": "V3", "selected_signal": "terraform", "relation": "proof_gap", "selected_provider_ordinal": None},
    )
    for payload in cases:
        with self.subTest(payload=sorted(payload)):
            with self.assertRaisesRegex(ValueError, "candidate gap response is invalid"):
                RESPONSE_BUILDER.build_candidate_gap_response_v1(
                    sources.research, sources.market, payload
                )
```

Add table-driven cases for all four response states, all seven relations, invalid `V0/V6/L0`, aliases, non-string scalars, wrong date/locale, provider present iff snapshot non-null, non-knowledge provider selection, stale/crossed sources, cycles, depth 33, 10,001 nodes, 151-item collections, 4,097-character strings, lone surrogates, and exception-raising `Mapping`/`__deepcopy__`. Add a mutable mapping that returns safe values while copied and private sentinel values later; assert the sentinel is absent and validation uses only the captured snapshot.

- [ ] **Step 2: Run the focused test and record the expected RED**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest -q \
  tests.test_learning_eligibility_v3.CandidateGapResponseV1Tests
```

Expected: import failure for missing `build_candidate_gap_response_v1.py`; record the command, failure class, and count in the task report before production edits.

- [ ] **Step 3: Implement the shared one-pass snapshot helper**

Implement the exact constants and public entrypoint:

```python
MAX_DEPTH = 32
MAX_NODES = 10_000
MAX_ITEMS = 150
MAX_STRING = 4096

def bounded_plain_snapshot(group: object) -> dict[str, object]:
    try:
        budget = _Budget()
        captured = _plain_snapshot(group, depth=0, active=set(), budget=budget)
    except Exception:
        raise ValueError("semantic input group is invalid") from None
    if not isinstance(captured, dict):
        raise ValueError("semantic input group is invalid") from None
    return captured
```

`_plain_snapshot` accepts only mappings with string keys, lists/tuples, JSON scalar strings/integers/booleans/null, enforces budgets while traversing once, detects active-path cycles, and returns built-in dict/list/scalars. It never calls `str()` on unsupported values. Make v2 `_bounded_tree` delegate to `bounded_tree` from this module and prove existing v2 tests unchanged.

- [ ] **Step 4: Add the closed response schema and builder**

The schema must use `additionalProperties: false` at every object, exact state-dependent `oneOf` branches from the spec, signal regex `^[a-z][a-z0-9_]{1,63}$`, vacancy ordinal `^V[1-5]$`, provider ordinal `^L[1-9][0-9]*$`, snapshot prefixes, fixed privacy/no-action booleans, and the seven closed relation values.

Implement the public builder shape:

```python
def build_candidate_gap_response_v1(
    research: object,
    market_dossier: object,
    response: object | None,
    provider_research: object | None = None,
) -> dict[str, object]:
    frozen = bounded_plain_snapshot({
        "research": research,
        "market_dossier": market_dossier,
        "response": response,
        "provider_research": provider_research,
    })
    research_copy = frozen["research"]
    market_copy = frozen["market_dossier"]
    response_copy = frozen["response"]
    provider_copy = frozen["provider_research"]
    _validate_sources(research_copy, market_copy, provider_copy)
    return _project_response(research_copy, market_copy, response_copy, provider_copy)
```

Public `Vn` resolves only against current sorted market vacancies; public `Ln` resolves only against active exact-signal provider choices sorted by normalized option then provider. The response stores public values and source snapshots, never the resolved private IDs.

- [ ] **Step 5: Implement validation, snapshot, and bounded loading**

Validate schema and sources from one snapshot, recompute state/ordinal/provider legality without reconstructing user intent, and compare the fixed source/date fields. Return exactly `['candidate gap response does not match validated sources']` on any failure. Snapshot canonical sorted/separator-free UTF-8 JSON as the literal prefix `snap-gap-response-v1-sha256-` followed by a 64-character lowercase hexadecimal digest. Load through the existing bounded private JSON loader and raise `CandidateGapResponseLoadError('cannot load candidate gap response')` from no underlying cause.

- [ ] **Step 6: Run the complete prewritten matrix green and register package contracts**

Register schema/script/test paths in private schema conformance, `MARKET_DOSSIER_PACKAGE_PATHS` (or a new explicit v3 tuple), and `tests/test_full_plugin.py`. Run the exact Task 1 class again; do not weaken hostile objects or change expected generic diagnostics.

- [ ] **Step 7: Run Task 1 gates**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest -q \
  tests.test_learning_eligibility_v3.CandidateGapResponseV1Tests \
  tests.test_semantic_provenance_v2.CareerLearningDecisionV2Tests
PYTHONDONTWRITEBYTECODE=1 python3 -B \
  plugins/professional-growth-coach/tests/test_private_schema_conformance.py -q
PYTHONDONTWRITEBYTECODE=1 python3 -B plugins/professional-growth-coach/tests/run_static_checks.py
git diff --check
find plugins/professional-growth-coach -type f \( -name '*.pyc' -o -name '*.pyo' \) -print
find plugins/professional-growth-coach -type d -name __pycache__ -print
```

Expected: unittest/static exit 0; both `find` commands print nothing.

- [ ] **Step 8: Commit Task 1**

```bash
git add plugins/professional-growth-coach/scripts/semantic_provenance_snapshot.py \
  plugins/professional-growth-coach/schemas/candidate-gap-response-v1.schema.json \
  plugins/professional-growth-coach/scripts/build_candidate_gap_response_v1.py \
  plugins/professional-growth-coach/scripts/validate_candidate_gap_response_v1.py \
  plugins/professional-growth-coach/scripts/build_career_learning_decision_v2.py \
  plugins/professional-growth-coach/tests/test_private_schema_conformance.py \
  plugins/professional-growth-coach/tests/run_static_checks.py \
  tests/test_learning_eligibility_v3.py tests/test_full_plugin.py
git commit -m "feat: persist closed candidate gap responses"
```

---

### Task 2: Candidate Gap Assessment v1

**Files:**
- Create: `plugins/professional-growth-coach/schemas/candidate-gap-assessment-v1.schema.json`
- Create: `plugins/professional-growth-coach/scripts/build_candidate_gap_assessment_v1.py`
- Create: `plugins/professional-growth-coach/scripts/validate_candidate_gap_assessment_v1.py`
- Create: `tests/evals/with-skill/fixtures/candidate-gap-response-v1/selection-required-es.json`
- Create: `tests/evals/with-skill/fixtures/candidate-gap-response-v1/recurrent-proof-es.json`
- Create: `tests/evals/with-skill/fixtures/candidate-gap-response-v1/recurrent-knowledge-en.json`
- Create: `tests/evals/with-skill/fixtures/candidate-gap-response-v1/unavailable-es.json`
- Create: matching files under `tests/evals/with-skill/fixtures/candidate-gap-assessment-v1/`
- Modify: `tests/test_learning_eligibility_v3.py`
- Modify: `plugins/professional-growth-coach/tests/test_private_schema_conformance.py`
- Modify: `plugins/professional-growth-coach/tests/run_static_checks.py`
- Modify: `tests/test_full_plugin.py`

**Interfaces:**
- Consumes: validated research, dossier v2, market v2, response v1, and optional provider research.
- Produces: `build_candidate_gap_assessment_v1(research, executive_dossier, market_dossier, gap_response, provider_research=None)`, `validate_candidate_gap_assessment_v1(value, research, executive_dossier, market_dossier, gap_response, provider_research=None)`, `snapshot_for_candidate_gap_assessment_v1`, and `load_candidate_gap_assessment_v1`.
- Internal contract: `_project_candidate_gap_assessment_from_frozen(...)` and `_validate_candidate_gap_assessment_from_frozen(...)` consume one already captured built-in group and call Task 1's internal frozen-group validator, never its recapturing public entrypoint.
- Resolves `Vn`/`Ln` to private IDs inside the assessment only and binds `source_gap_response_snapshot`; no second selection argument exists.

- [ ] **Step 1: Write the complete assessment RED matrix**

```python
def test_assessment_resolves_public_v2_to_exact_private_vacancy(self):
    sources = recurrent_sources(locale="es")
    response = build_response(sources, relation="proof_gap")
    result = ASSESSMENT_BUILDER.build_candidate_gap_assessment_v1(
        sources.research, sources.dossier, sources.market, response
    )
    self.assertEqual("V-003", result["selected_vacancy_id"])
    self.assertEqual("terraform", result["selected_signal"])
    self.assertEqual("proof_gap", result["assessments"][0]["relation"])
    self.assertEqual(
        RESPONSE_VALIDATOR.snapshot_for_candidate_gap_response_v1(response),
        result["source_gap_response_snapshot"],
    )

def test_assessment_cannot_reconstruct_or_override_response(self):
    sources = recurrent_sources(locale="es")
    response = build_response(sources, relation="proof_gap")
    result = build_assessment(sources, response)
    altered = copy.deepcopy(result)
    altered["assessments"][0]["relation"] = "knowledge_gap"
    self.assertEqual(
        ["candidate gap assessment does not match validated sources"],
        ASSESSMENT_VALIDATOR.validate_candidate_gap_assessment_v1(
            altered, sources.research, sources.dossier, sources.market, response
        ),
    )
```

Add exact tests for unavailable/selection-required/partial/complete cardinality and dates, all relations, provider nullability, public `L1` resolving to `LP-001` for the ES provider source and `LP-003` for the existing EN provider source, crossed response/market/provider snapshots, wrong private IDs, extra/reordered rows, totality budgets, no-echo, and safe ES/EN technical labels.

- [ ] **Step 2: Run RED**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest -q \
  tests.test_learning_eligibility_v3.CandidateGapAssessmentV1Tests
```

Expected: missing assessment builder/validator import.

- [ ] **Step 3: Implement the closed schema and source-only projection**

Create the exact root/assessment fields and state branches from the spec. Implement:

```python
def build_candidate_gap_assessment_v1(
    research: object,
    executive_dossier: object,
    market_dossier: object,
    gap_response: object,
    provider_research: object | None = None,
) -> dict[str, object]:
    frozen = bounded_plain_snapshot({
        "research": research,
        "executive_dossier": executive_dossier,
        "market_dossier": market_dossier,
        "gap_response": gap_response,
        "provider_research": provider_research,
    })
    return _project_assessment(*_validated_group(frozen))
```

`_project_assessment` maps current public ordinals to exact private IDs, generates confirmation state/date, and copies no source prose. The validator validates the independent response, calls the same pure projection, and canonical-compares the complete supplied assessment.

- [ ] **Step 4: Generate canonical fixtures from builders**

Use one checked-in generator command in the task report (a `python3 -B -c` invocation importing by file path) to write sorted UTF-8 JSON plus trailing newline. `recurrent_sources()` changes the synthetic V-001 requirement signal from `python` to `terraform`, rebuilds market v2, and asserts recurrence `2/5`; the resulting tie sorts `V-001` as public `V1` and `V-003` as public `V2`, so both pairs are valid and the canonical proof response selects `V2` to preserve the exact `V-003` target. It never hand-edits derived fixtures.

- [ ] **Step 5: Register schema/fixtures and run Task 2 gates**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest -q \
  tests.test_learning_eligibility_v3.CandidateGapResponseV1Tests \
  tests.test_learning_eligibility_v3.CandidateGapAssessmentV1Tests \
  tests.test_semantic_provenance_v2
PYTHONDONTWRITEBYTECODE=1 python3 -B \
  plugins/professional-growth-coach/tests/test_private_schema_conformance.py -q
PYTHONDONTWRITEBYTECODE=1 python3 -B plugins/professional-growth-coach/tests/run_static_checks.py
git diff --check
```

- [ ] **Step 6: Commit Task 2**

```bash
git add plugins/professional-growth-coach/schemas/candidate-gap-assessment-v1.schema.json \
  plugins/professional-growth-coach/scripts/build_candidate_gap_assessment_v1.py \
  plugins/professional-growth-coach/scripts/validate_candidate_gap_assessment_v1.py \
  plugins/professional-growth-coach/tests/test_private_schema_conformance.py \
  plugins/professional-growth-coach/tests/run_static_checks.py \
  tests/evals/with-skill/fixtures/candidate-gap-response-v1 \
  tests/evals/with-skill/fixtures/candidate-gap-assessment-v1 \
  tests/test_learning_eligibility_v3.py tests/test_full_plugin.py
git commit -m "feat: resolve candidate gap assessments"
```

---

### Task 3: Career Next-Action Eligibility v1

**Files:**
- Create: `plugins/professional-growth-coach/schemas/career-next-action-eligibility-v1.schema.json`
- Create: `plugins/professional-growth-coach/scripts/build_career_next_action_eligibility_v1.py`
- Create: `plugins/professional-growth-coach/scripts/validate_career_next_action_eligibility_v1.py`
- Create: canonical fixtures under `tests/evals/with-skill/fixtures/career-next-action-eligibility-v1/`
- Modify: `tests/test_learning_eligibility_v3.py`
- Modify: `plugins/professional-growth-coach/tests/test_private_schema_conformance.py`
- Modify: `plugins/professional-growth-coach/tests/run_static_checks.py`
- Modify: `tests/test_full_plugin.py`

**Interfaces:**
- Consumes: research v1, dossier v2, market v2, gap response v1, gap assessment v1, and optional provider research v1. Recomputes candidate-market alignment v2.
- Produces: `build_career_next_action_eligibility_v1(...)`, `validate_career_next_action_eligibility_v1(...)`, `snapshot_for_career_next_action_eligibility_v1(...)`, `load_career_next_action_eligibility_v1(...)`, and immutable `ELIGIBILITY_RULES` / `COPY` mappings.
- Internal contract: `_project_eligibility_from_frozen(frozen_group: Mapping[str, object]) -> dict[str, object]` validates/recomputes from built-in captured values without recapturing. Public builder and validator each capture once and delegate to it; Task 4 may call it only with its own already captured group.
- `selected_provider_option_id` is non-null only for `eligible/research_provider_option`; `eligible_provider_choices` is non-empty only for `provider_selection_required`.

- [ ] **Step 1: Write the exhaustive decision-table RED matrix**

```python
def test_eligibility_table_projects_exactly_one_action(self):
    cases = (
        ("unavailable", "market_unavailable", "no_learning_yet", 0),
        ("selection_required", "selection_missing", "select_target_vacancy_and_signal", 0),
        ("insufficient_recurrence", "recurrence_below_two", "prepare_private_vacancy_packet", 0),
        ("gap_unknown", "gap_unknown", "confirm_gap_relation", 0),
        ("supported", "candidate_supported", "prepare_private_vacancy_packet", 0),
        ("provider_choice", "provider_choice_missing", "select_provider_option", 0),
        ("provider_evidence", "provider_evidence_missing", "no_learning_yet", 0),
        ("experience", "professional_experience_required", "prepare_private_vacancy_packet", 0),
        ("proof", "proof_gap_recurrent", "build_bounded_proof", 1),
        ("practice", "practice_gap_recurrent", "run_validation_lab", 1),
        ("terminology", "terminology_gap_recurrent", "run_role_search_experiment", 1),
        ("knowledge", "knowledge_gap_recurrent_provider_selected", "research_provider_option", 1),
    )
    for fixture_name, basis, action, learning_count in cases:
        with self.subTest(case=fixture_name):
            result = build_eligibility_case(fixture_name)
            self.assertEqual(basis, result["decision_basis_code"])
            self.assertEqual(action, result["recommended_next_action"])
            self.assertEqual(learning_count, int(action in LEARNING_ACTIONS))
```

Add assertions for exact nullability, recurrence/support/relation values, fixed ES/EN state/action/deliverable/done-when copy, `1/5` overriding every gap/provider state, two distinct active vacancies only, supported-not-gap behavior, experience-not-replaceable copy, provider absent/zero choices/choices/no selection/explicit L1 progression, complete non-ranked L1–Ln ordering, no LP IDs/URLs in public choices, selected provider bound only by eligibility, score/prose mutation invariance, snapshot tampering, arbitrary state/action/copy rejection, totality, and no-echo.

- [ ] **Step 2: Run RED**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest -q \
  tests.test_learning_eligibility_v3.CareerNextActionEligibilityV1Tests
```

Expected: missing eligibility builder/validator import.

- [ ] **Step 3: Implement the closed schema, exact rule table, and localized projection**

Define one immutable rule table with the 12 condition rows and one immutable ES/EN copy table copied verbatim from the spec. The builder signature is:

```python
def build_career_next_action_eligibility_v1(
    research: object,
    executive_dossier: object,
    market_dossier: object,
    gap_response: object,
    gap_assessment: object,
    provider_research: object | None = None,
) -> dict[str, object]:
    frozen = bounded_plain_snapshot({
        "research": research,
        "executive_dossier": executive_dossier,
        "market_dossier": market_dossier,
        "gap_response": gap_response,
        "gap_assessment": gap_assessment,
        "provider_research": provider_research,
    })
    validated = _validated_group(frozen)
    alignment = derive_candidate_market_alignment_v2(validated.research, validated.dossier)
    return _project_eligibility(validated, alignment)
```

Compute recurrence from distinct active exact-signal requirements, support from the exact alignment row, public ordinal from current market order, and choices from active official exact-signal provider rows only. Rule order is the spec order; no later rule may override insufficient recurrence.

- [ ] **Step 4: Implement complete recomputation validation and fixtures**

Validator snapshots the complete group once, validates response and assessment against their independent sources, invokes `_project_eligibility`, and compares canonical objects. Generate fixture rows for all 12 table conditions in both locales where copy differs; compact the fixture set by storing source inputs once per scenario directory, never by hand-authoring expected derived fields.

- [ ] **Step 5: Run Task 3 gates**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest -q \
  tests.test_learning_eligibility_v3 \
  tests.test_semantic_provenance_v2 \
  tests.test_career_market_learning_dossier
PYTHONDONTWRITEBYTECODE=1 python3 -B \
  plugins/professional-growth-coach/tests/test_private_schema_conformance.py -q
PYTHONDONTWRITEBYTECODE=1 python3 -B plugins/professional-growth-coach/tests/run_static_checks.py
PYTHONDONTWRITEBYTECODE=1 python3 -B scripts/check_repository_privacy.py
git diff --check
```

- [ ] **Step 6: Commit Task 3**

```bash
git add plugins/professional-growth-coach/schemas/career-next-action-eligibility-v1.schema.json \
  plugins/professional-growth-coach/scripts/build_career_next_action_eligibility_v1.py \
  plugins/professional-growth-coach/scripts/validate_career_next_action_eligibility_v1.py \
  plugins/professional-growth-coach/tests/test_private_schema_conformance.py \
  plugins/professional-growth-coach/tests/run_static_checks.py \
  tests/evals/with-skill/fixtures/career-next-action-eligibility-v1 \
  tests/test_learning_eligibility_v3.py tests/test_full_plugin.py
git commit -m "feat: gate learning with vacancy-first eligibility"
```

---

### Task 4: Career Learning Decision v3

**Files:**
- Create: `plugins/professional-growth-coach/schemas/career-learning-decision-v3.schema.json`
- Create: `plugins/professional-growth-coach/scripts/project_career_learning_decision_v3.py`
- Create: `plugins/professional-growth-coach/scripts/build_career_learning_decision_v3.py`
- Create: `plugins/professional-growth-coach/scripts/validate_career_learning_decision_v3.py`
- Create: fixtures under `tests/evals/with-skill/fixtures/career-learning-decision-v3/`
- Modify: `tests/test_learning_eligibility_v3.py`
- Modify: `tests/test_career_learning_decision.py`
- Modify: `plugins/professional-growth-coach/tests/test_private_schema_conformance.py`
- Modify: `plugins/professional-growth-coach/tests/run_static_checks.py`
- Modify: `tests/test_full_plugin.py`

**Interfaces:**
- Consumes: the exact Task 3 source group and eligibility artifact; it accepts no request rows or separate provider selection.
- Produces: `project_career_learning_decision_v3(...)`, `build_career_learning_decision_v3(...)`, `validate_career_learning_decision_v3(...)`, `snapshot_for_learning_bundle_v3(...)`, and `load_learning_bundle_v3(...)`.
- Uses a v3-owned exact route/join and projection. It does not reuse `project_decision_v2` or the v2 private join because v2 maps validation labs to `experience` and rejects `unknown` support, while v3 normatively maps them to `practice` and lets explicit candidate relation remain authoritative after the exact source join.
- Internal contract: `_project_learning_v3_from_frozen(...)` and `_validate_learning_v3_from_frozen(...)` consume the one Task 4 capture and call only Tasks 1–3 frozen-group internals.

- [ ] **Step 1: Write zero/one authority and provenance RED tests**

```python
def test_learning_v3_projects_only_the_eligibility_action(self):
    sources = recurrent_sources(locale="es")
    eligibility = build_eligibility_case("proof", sources=sources)
    bundle = LEARNING_V3_BUILDER.build_career_learning_decision_v3(
        sources.research, sources.dossier, sources.market,
        sources.response, sources.assessment, eligibility, None,
    )
    self.assertEqual("career-learning-decision-v3", bundle["schema_version"])
    self.assertEqual(1, len(bundle["decisions"]))
    row = bundle["decisions"][0]
    self.assertEqual("build_bounded_proof", row["decision_code"])
    self.assertEqual(["terraform"], row["source_signals"])
    self.assertEqual(["V-001", "V-003"], row["vacancy_ids"])
    self.assertEqual(["V-001-R-01", "V-003-R-01"], row["requirement_ids"])
    self.assertEqual("2/5", row["signal_routes"][0]["recurrence"])

def test_learning_v3_has_no_caller_decision_or_provider_override(self):
    signature = inspect.signature(LEARNING_V3_BUILDER.build_career_learning_decision_v3)
    self.assertNotIn("decision_requests", signature.parameters)
    self.assertNotIn("provider_option_id", signature.parameters)
```

Add all eight zero-decision states, all four one-decision mappings, exact claim/evidence/requirement/vacancy/role unions, current public vacancy order, provider ID only for research option, unrelated IDs/signals/provider displacement/Quantum prose rejection, source/order mutation, crossed response/assessment/eligibility snapshots, bounded exceptional input, deterministic ES/EN copy, v1/v2 fixture readability, and generic no-echo failures.

- [ ] **Step 2: Run RED**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest -q \
  tests.test_learning_eligibility_v3.CareerLearningDecisionV3Tests
```

Expected: missing v3 builder/validator import.

- [ ] **Step 3: Implement closed v3 schema and eligibility-only builder**

The schema retains every safe v2 decision projection field, changes the root version, adds `source_gap_response_snapshot`, `source_gap_assessment_snapshot`, and `source_next_action_eligibility_snapshot`, and constrains decisions to `maxItems: 1`. Unlike v2, `source_provider_research_snapshot` is explicitly `string | null`: it is non-null if and only if an allowed provider source is present in the captured group and is null for proof/practice/terminology and every zero-decision non-knowledge state. Implement:

```python
LEARNING_ACTIONS = {
    "build_bounded_proof": ("build_bounded_proof", None),
    "run_validation_lab": ("run_validation_lab", None),
    "research_provider_option": ("research_provider_option", "selected"),
    "run_role_search_experiment": ("run_role_search_experiment", None),
}

def build_career_learning_decision_v3(
    research: object,
    executive_dossier: object,
    market_dossier: object,
    gap_response: object,
    gap_assessment: object,
    eligibility: object,
    provider_research: object | None = None,
) -> dict[str, object]:
    frozen = bounded_plain_snapshot({
        "research": research,
        "executive_dossier": executive_dossier,
        "market_dossier": market_dossier,
        "gap_response": gap_response,
        "gap_assessment": gap_assessment,
        "eligibility": eligibility,
        "provider_research": provider_research,
    })
    validated = _validated_group(frozen)
    recomputed = _project_eligibility_from_frozen(validated.eligibility_source_group)
    return _project_bundle(validated, recomputed)
```

Build exact routes/unions in `project_career_learning_decision_v3.py` directly from the selected signal, assessment relation, recomputed alignment, active requirements, market public order, and eligibility-bound provider. The v3 projector owns the normative proof/practice/knowledge/terminology mappings and permits `unknown` internal support when the explicit confirmed relation and other eligibility gates allow it. Every action outside `LEARNING_ACTIONS` emits zero rows; no caller data decides rank/code/basis/copy.

- [ ] **Step 4: Implement validator and canonical fixtures**

Validator recomputes eligibility from response/assessment/source group, rebuilds the whole v3 bundle, and canonical-compares it. Generate proof ES, knowledge EN, selection-required ES, and unavailable ES fixtures plus dynamic tests for all other states. Do not update any v1/v2 fixture.

- [ ] **Step 5: Run Task 4 gates**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest -q \
  tests.test_learning_eligibility_v3 \
  tests.test_semantic_provenance_v2 \
  tests.test_career_learning_decision \
  tests.test_career_market_learning_dossier
PYTHONDONTWRITEBYTECODE=1 python3 -B \
  plugins/professional-growth-coach/tests/test_private_schema_conformance.py -q
PYTHONDONTWRITEBYTECODE=1 python3 -B plugins/professional-growth-coach/tests/run_static_checks.py
git diff --check
```

- [ ] **Step 6: Commit Task 4**

```bash
git add plugins/professional-growth-coach/schemas/career-learning-decision-v3.schema.json \
  plugins/professional-growth-coach/scripts/project_career_learning_decision_v3.py \
  plugins/professional-growth-coach/scripts/build_career_learning_decision_v3.py \
  plugins/professional-growth-coach/scripts/validate_career_learning_decision_v3.py \
  plugins/professional-growth-coach/tests/test_private_schema_conformance.py \
  plugins/professional-growth-coach/tests/run_static_checks.py \
  tests/evals/with-skill/fixtures/career-learning-decision-v3 \
  tests/test_learning_eligibility_v3.py tests/test_career_learning_decision.py \
  tests/test_full_plugin.py
git commit -m "feat: project one eligible learning decision v3"
```

---

### Task 5: Superdesign and v3 Executive-Dossier Composition

**Files:**
- Create: `.superdesign/resume.json`
- Create: `plugins/professional-growth-coach/assets/career-learning-eligibility-v1.css`
- Modify: `plugins/professional-growth-coach/scripts/render_executive_career_dossier_v2.py`
- Modify: `tests/test_executive_career_dossier_v2.py`
- Modify: `tests/test_repository_privacy.py`
- Modify: `tests/test_superdesign_theme_asset_parity.py`
- Modify: `tests/test_print_continuity_footer_integrity.py`
- Modify: `tests/test_dark_mode_accessibility.py`
- Modify: `.superdesign/design-system.md`
- Modify: `.superdesign/init/components.md`
- Modify: `.superdesign/init/extractable-components.md`
- Modify: `.superdesign/init/pages.md`
- Modify: `.superdesign/init/routes.md`
- Modify: `.superdesign/init/theme.md`

**Interfaces:**
- Extends `render_dossier_html(...)` with keyword-only `gap_response`, `gap_assessment`, and `next_action_eligibility`; v3 learning uses the existing `learning_decision` slot by schema version. Extends `write_dossier_html(...)` and CLI with matching all-or-none paths.
- Adds `_validated_v3_group(...) -> Mapping[str, object] | None`, `_render_weekly_decision_card(eligibility, market, locale) -> str`, `_render_learning_decision_v3(market, learning, locale) -> str`, and a v3-only CSS asset path. `_render_decide_now(...)` receives the validated eligibility only for generation v3 and appends the weekly card after its existing `article.decide-now-market`; `_render_main(...)` then leaves the detailed market/learning surface in its existing later position.
- Existing v1/v2/no-market calls and outputs remain byte-identical.

- [ ] **Step 1: Perform the cold existing-UI Superdesign workflow before visual production edits**

Confirm all six init files are non-empty and `.superdesign/resume.json` is absent. Run the bare preflight:

```bash
npx --yes @superdesign/cli@latest
```

Before any upload, re-run `rg -n '^def |^COPY =|^CSS_' plugins/professional-growth-coach/scripts/render_executive_career_dossier_v2.py`, confirm whether the current render/composition region still spans lines `559:1540`, and show the user the exact six-item context list. If backend work shifted those boundaries, show the revised numeric range rather than silently broadening the file:

```text
.superdesign/design-system.md
plugins/professional-growth-coach/assets/executive-career-dossier-v1.html
plugins/professional-growth-coach/assets/executive-career-dossier-v1.css
plugins/professional-growth-coach/assets/executive-career-dossier-v2.css
plugins/professional-growth-coach/assets/career-market-learning-dossier-v1.css
plugins/professional-growth-coach/scripts/render_executive_career_dossier_v2.py:559:1540
```

After explicit upload approval, create/reuse one project, create one pixel-faithful complete-market v2 baseline in one prompt, then one `iterate-design-draft --mode replace` direction containing the full-width weekly card. Use no assets, external interactions, gradients, fonts, or new brand marks. Fetch/inspect the draft, surface canvas/preview URLs, obtain canvas approval, and atomically persist project/target/context/fingerprints/baseline/active/version in `.superdesign/resume.json` before production UI edits.

- [ ] **Step 2: Write the complete renderer/CSS/writer/CLI RED matrix**

```python
def test_v3_weekly_card_is_ordered_named_and_single_action(self):
    rendered = self.renderer.render_dossier_html(**semantic_v3_case("proof", "es"))
    decide = decide_now_region(rendered)[2]
    self.assertLess(decide.index('class="card span-12 decide-now-card decide-now-market"'), decide.index('class="card span-12 weekly-decision"'))
    self.assertLess(rendered.index('class="card span-12 weekly-decision"'), rendered.index('class="section-block learning-decision"'))
    self.assertEqual(1, decide.count('class="card span-12 weekly-decision"'))
    self.assertEqual(1, decide.count('class="weekly-decision-action"'))
    self.assertIn("Decisión de esta semana", decide)
    audit = DossierDOMAudit()
    audit.feed(rendered)
    self.assertFalse(set(audit.references) - set(audit.ids))

def test_v3_provider_choice_list_is_complete_non_ranked_and_public(self):
    rendered = self.renderer.render_dossier_html(**semantic_v3_case("provider_choice", "en"))
    region = weekly_decision_region(rendered)
    self.assertIn("L1", region)
    self.assertIn("Terraform course", region)
    self.assertIn("HashiCorp", region)
    for forbidden in ("LP-001", "https://", "snap-", "V-003"):
        self.assertNotIn(forbidden, region)
    self.assertNotIn("<button", region)
    self.assertNotIn("<form", region)
    self.assertNotIn("<a ", region)
```

Add ES/EN tests for every eligibility state, unavailable exactly-one-existing-safe-step and no weekly card, exact relation/action/deliverable/done-when copy, visible and accessible Vn/title/employer, stable/resolved IDs, no private values/raw enums, historical v1/v2 byte snapshots, partial/cross-version rejection, mutable input snapshot, mode-600 atomic writer, CLI exit 2/no output, mobile one-column/no overflow, print atomicity, light/dark contrast, forced colors, and reduced motion. Pin one `article.weekly-decision`, one localized heading referenced by `aria-labelledby`, stable evidence and boundary IDs both referenced by `aria-describedby`, a visible public `Vn`, and that same ordinal plus public title/employer in the accessible name. Assert that v1/v2 inline CSS bytes do not contain any selector from `career-learning-eligibility-v1.css`.

- [ ] **Step 3: Run RED**

Run the exact new renderer/CSS test methods. Expected: missing v3 keyword arguments/weekly markup/CSS contracts, while historical snapshot assertions remain green.

- [ ] **Step 4: Implement strict v3 preflight and one-snapshot composition**

Add `_render_dossier_html_from_snapshot(frozen_group: Mapping[str, object]) -> str` as the sole v3 validation/composition/template function. At the first line of public `render_dossier_html`, branch only on whether any new v3 keyword argument is non-null; this identity check does not read an input object. For that branch, call `bounded_plain_snapshot` once with one mapping containing dossier, market, research, alignment, provider, response, assessment, eligibility, and learning, then call the internal snapshot consumer. Destructure only the captured built-in values and never call `_validate_and_freeze`, `deepcopy`, `.get`, iteration, comparison, or any validator on an original object. The legacy branch with no new v3 keyword retains its current byte-identical v1/v2 path.

Extend `_composition_generation` with only the coherent v3 tuple. `_validated_v3_group` receives the already captured mapping, validates/recomputes response/assessment/eligibility/learning through their internal frozen-group functions, and returns the validated artifacts without invoking any public recapturing entrypoint. Missing/extra/crossed versions raise the fixed existing composition diagnostic before template/CSS reads or writes. A renderer-specific hostile mapping test must prove that no sentinel returned after the first traversal reaches validation or HTML.

Extend public signatures and CLI with:

```python
def render_dossier_html(
    dossier,
    market_dossier=None,
    *,
    market_research=None,
    market_alignment=None,
    learning_decision=None,
    provider_research=None,
    gap_response=None,
    gap_assessment=None,
    next_action_eligibility=None,
) -> str: ...
```

Add `--gap-response`, `--gap-assessment`, and `--next-action-eligibility`; require the v3 group all-or-none. `write_dossier_html` loads each path, immediately places every loaded object into one mapping, captures it once with `bounded_plain_snapshot`, calls `_render_dossier_html_from_snapshot`, and generates chat summary/receipt only from the captured dossier. It must not call public `render_dossier_html`, reread a loaded object, or reuse the original dossier for post-render metadata. CLI passes paths to this writer and never loads or inspects semantic payloads separately. Writer/CLI hostile-object tests spy on the internal render/project calls and prove one capture plus no sentinel/no partial output.

- [ ] **Step 5: Implement only the approved weekly-card direction**

Render one named `article.card.span-12.weekly-decision` inside the existing `section.decide-now`, immediately after its existing `article.decide-now-market`. Because the detailed learning surface remains later in `_render_main`, DOM order is condensed market summary → weekly decision → detailed learning without relocating historical sections. The card references stable evidence/boundary IDs through `aria-describedby`, shows public Vn/title/employer, signal/recurrence when non-null, complete L1–Ln choices only in provider-selection state, exactly one action/deliverable/done-when, and the fixed boundary. `unavailable` returns an empty card string. All visible fields come from validated eligibility/market public projection and are HTML-escaped.

Extend `_render_learning_decision` with an explicit v3 branch that calls `_render_learning_decision_v3`. It renders the one retained safe proof/cost/action projection only when the validated v3 `decisions` array has one item and returns an empty string for every zero-decision state; it never falls through to a v1/v2 validator or renderer.

Put isolated `.weekly-decision*` rules in the new `career-learning-eligibility-v1.css` asset and concatenate that asset only when the validated composition generation is v3. Do not edit the market CSS loaded by historical v1/v2, so their inline CSS and HTML byte snapshots remain unchanged. At `max-width: 680px`, use one column, `min-width: 0`, and `overflow-wrap: anywhere`; add print `break-inside/page-break-inside: avoid`; forced-colors `Canvas`, `CanvasText`, and `Highlight`/`CanvasText`; preserve dark tokens and reduced-motion/no-script meaning.

- [ ] **Step 6: Synchronize Superdesign mirrors and resume state**

Copy the complete new v3 CSS asset bytes into `.superdesign/init/theme.md` and register its exact source/parity assertion in `tests/test_superdesign_theme_asset_parity.py`; update design-system/components/extractable/pages/routes only for the approved v3 composition. Preserve all existing targets when atomically writing resume JSON. Record `visual QA not run` in the task report unless browser/print/AT evidence was actually gathered.

- [ ] **Step 7: Run Task 5 gates**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest -q \
  tests.test_learning_eligibility_v3 \
  tests.test_executive_career_dossier_v2 \
  tests.test_repository_privacy \
  tests.test_superdesign_theme_asset_parity \
  tests.test_print_continuity_footer_integrity \
  tests.test_dark_mode_accessibility
git diff --check
```

- [ ] **Step 8: Commit Task 5**

```bash
git add .superdesign/resume.json .superdesign/design-system.md .superdesign/init \
  plugins/professional-growth-coach/scripts/render_executive_career_dossier_v2.py \
  plugins/professional-growth-coach/assets/career-learning-eligibility-v1.css \
  tests/test_executive_career_dossier_v2.py tests/test_repository_privacy.py \
  tests/test_superdesign_theme_asset_parity.py \
  tests/test_print_continuity_footer_integrity.py tests/test_dark_mode_accessibility.py
git commit -m "feat: render vacancy-first weekly decisions"
```

---

### Task 6: Routing, Documentation, Package Inventory, and Whole-Source Gates

**Files:**
- Create: `scripts/verify_installed_plugin_release.py`
- Create: `scripts/run_installed_learning_eligibility_v3_smokes.py`
- Modify: `scripts/check_repository_privacy.py`
- Modify: `plugins/professional-growth-coach/skills/professional-growth-coach/SKILL.md`
- Modify: `plugins/professional-growth-coach/skills/professional-growth-coach/references/routing.md`
- Modify: `plugins/professional-growth-coach/skills/recommend-career-learning/SKILL.md`
- Modify: `plugins/professional-growth-coach/skills/recommend-career-learning/references/learning-roi.md`
- Modify: `plugins/professional-growth-coach/README.md`
- Modify: `docs/release-validation.md`
- Modify: `plugins/professional-growth-coach/tests/run_static_checks.py`
- Modify: `tests/test_plugin_structure.py`
- Modify: `tests/test_full_plugin.py`
- Modify: `tests/test_repository_privacy.py`

**Interfaces:**
- Documents/routs: public vacancy+signal selection -> explicit gap response -> eligibility -> one action -> optional one learning decision.
- Package inventory includes all four schemas, eight builder/validator scripts, the v3 projector, the shared boundary, v3 fixtures, renderer flags, and tests.
- `resolve_exact_installed_cache(plugin_list: object, plugin: str, marketplace: str, expected_version: str, cache_family: Path) -> Path` requires exactly one enabled matching row and returns only `cache_family / plugin / expected_version`; `release_inventory(root: Path)` and `aggregate_release_digest(root: Path)` implement the spec's sorted POSIX-path/per-file-hash algorithm with relative diagnostics and bytecode/private-metadata rejection.
- `run_installed_learning_eligibility_v3_smokes.py --plugin-root PATH --source-archive PATH` inserts only the exact installed `scripts` directory, asserts imported module paths are descendants of that plugin root, and runs the accepted/rejected matrix without importing the mutable checkout.
- Produces a complete source tree ready for independent whole-branch review; no version/install/push yet.

- [ ] **Step 1: Write routing/inventory/privacy RED assertions**

Add tests that require exact schema/script/fixture sets, every new CLI flag, closed skill order, recurrence threshold `>=2`, no auto-selection, no learning substitution for professional experience, score-not-hiring-probability boundary, no external action, and package-only static behavior. Extend repository privacy mutations across every new rendered/source field and require fixed no-echo failure. Write RED tests for the release helper covering zero/multiple/disabled/wrong-version plugin-list rows, traversal-like plugin/version values, mismatched inventories, per-file mismatch, aggregate record ordering, bytecode/private metadata, and the exact enabled matching row. Add a synthetic attestation parser/assertion matrix in `tests/test_full_plugin.py` that requires every Task 7 field before the real attestation is written. Add smoke-harness tests that reject any imported semantic module outside the supplied installed plugin root.

- [ ] **Step 2: Run RED**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest -q \
  tests.test_plugin_structure tests.test_full_plugin tests.test_repository_privacy
```

Expected: explicit inventory/routing assertions fail for missing v3 paths/copy.

- [ ] **Step 3: Update routing and product/release documentation**

Write the exact five-step order from the spec. State that a single vacancy is insufficient for learning, candidate support is not a gap, provider choice is user-selected, professional experience cannot be replaced by learning, and application/profile/message/purchase actions remain outside this artifact. Document v3 CLI grouping and installed-cache repository-only scope without duplicating the full spec.

- [ ] **Step 4: Complete package/static/privacy registrations**

Add explicit paths to `run_static_checks.py`, `MARKET_DOSSIER_PACKAGE_PATHS`, `_load_market_package_modules`, `required_interfaces`, `tests/test_full_plugin.py`, and `DOSSIER_SOURCE_INVENTORY_PATHS` in `scripts/check_repository_privacy.py`; add schema conformance and installed-relative smoke imports; ensure package discovery outside the repository runs local tests or explicitly skips repository-only selectors without swallowing unlisted import/file errors. Keep all diagnostics relative and sanitized.

- [ ] **Step 5: Run the complete source verification matrix**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest -q \
  tests.test_learning_eligibility_v3 \
  tests.test_semantic_provenance_v2 \
  tests.test_career_market_learning_dossier \
  tests.test_career_learning_decision \
  tests.test_executive_career_dossier_v2 \
  tests.test_repository_privacy \
  tests.test_plugin_structure \
  tests.test_full_plugin \
  tests.test_superdesign_theme_asset_parity \
  tests.test_print_continuity_footer_integrity \
  tests.test_dark_mode_accessibility
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover \
  -s plugins/professional-growth-coach/tests -p 'test*.py' -q
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover \
  -s tests -p 'test*.py' -q
PYTHONDONTWRITEBYTECODE=1 python3 -B plugins/professional-growth-coach/tests/run_static_checks.py
PYTHONDONTWRITEBYTECODE=1 python3 -B scripts/check_repository_privacy.py
bash scripts/bootstrap_release_validation.sh
CODEX_SYSTEM_SKILLS_ROOT=/Users/kevinriosferrer/.codex/skills/.system \
  bash scripts/run_release_validation.sh
git diff --check
find plugins/professional-growth-coach -type f \( -name '*.pyc' -o -name '*.pyo' \) -print
find plugins/professional-growth-coach -type d -name __pycache__ -print
```

Expected: all commands exit 0; both `find` commands print nothing. Use the locked repo venv or the documented `VALIDATION_PYTHON` override; do not substitute a mutable global environment.

- [ ] **Step 6: Commit Task 6**

```bash
git add scripts/verify_installed_plugin_release.py \
  scripts/run_installed_learning_eligibility_v3_smokes.py \
  scripts/check_repository_privacy.py \
  plugins/professional-growth-coach/skills/professional-growth-coach \
  plugins/professional-growth-coach/skills/recommend-career-learning \
  plugins/professional-growth-coach/README.md docs/release-validation.md \
  plugins/professional-growth-coach/tests/run_static_checks.py \
  tests/test_plugin_structure.py tests/test_full_plugin.py tests/test_repository_privacy.py
git commit -m "docs: route vacancy-first learning decisions"
```

---

### Task 7: Independent Review, Two-Commit Release, Install, Attestation, and Publish

**Files:**
- Modify: `plugins/professional-growth-coach/.codex-plugin/plugin.json`
- Modify: `tests/evals/final/installed-smoke-test.md`

**Interfaces:**
- Consumes: reviewed Tasks 1–6.
- Produces: cachebuster commit A, exact installed public cache with reproducible parity, attestation-only commit B, final remote `main`, and aligned primary checkout.

- [ ] **Step 1: Run the SDD whole-branch review**

Generate the final review package from merge base `af908ce17a6214c572414d1cb9dde25af89d5b0e` through Task 6 HEAD. Dispatch the most capable reviewer with spec, plan, package, ledger rulings/deferred minors, and global constraints. Any P1/P2 or load-bearing spec failure gets one coordinated RED-first fix wave and one scoped re-review before release.

- [ ] **Step 2: Run independent security and product/UX audits**

Security probes: mutable-input TOCTOU, private/public ordinal confusion, arbitrary/crossed IDs, recurrence forgery, caller relation/action/copy, provider displacement, source snapshot drift, cycles/budgets/exceptions, diagnostics/no-echo, writer/CLI atomicity, and package-cache behavior. Product/UX probes: single action, unavailable single safe step, L1–Ln clarity/non-ranking, ES/EN copy, visible/accessible ordinals, ARIA, historical bytes, mobile/print/dark/forced-colors, Superdesign/docs parity. Record `visual QA not run` unless empirical evidence exists.

- [ ] **Step 3: Re-run the complete source matrix fresh**

Run Task 6 Step 5 from a clean worktree and record exact unittest totals, durations, static/privacy/release exit codes, and zero-bytecode output in the Task 7 report.

- [ ] **Step 4: Create and publish cachebuster commit A**

Run the supported cachebuster helper exactly once:

```bash
python3 /Users/kevinriosferrer/.codex/skills/.system/plugin-creator/scripts/update_plugin_cachebuster.py \
  plugins/professional-growth-coach
```

Require `git status --short` and `git diff --name-only` to show only `plugins/professional-growth-coach/.codex-plugin/plugin.json`, require the new version to have literal prefix `0.2.0+codex.` followed by a UTC timestamp in `YYYYMMDDHHMMSS` form, run structure/full-plugin/static checks, and commit only the manifest:

```bash
git add plugins/professional-growth-coach/.codex-plugin/plugin.json
git commit -m "chore: refresh vacancy-first learning plugin cache"
```

Record cachebuster commit A with `CACHEBUSTER_COMMIT=$(git rev-parse HEAD)` and resolve its plugin tree with `git rev-parse "$CACHEBUSTER_COMMIT":plugins/professional-growth-coach`. Push and verify with:

```bash
git push origin HEAD:main
git fetch origin main
test "$(git rev-parse HEAD)" = "$(git rev-parse origin/main)"
REMOTE_MAIN=$(git ls-remote --exit-code origin refs/heads/main | cut -f1)
test "$REMOTE_MAIN" = "$CACHEBUSTER_COMMIT"
```

Resolve the public marketplace source checkout from `codex plugin list --marketplace codex-marketplace-public --json`; it is expected to be `/Users/kevinriosferrer/projects/codex_marketplace`. Before alignment require that exact checkout to be clean, detached or on a branch whose HEAD is an ancestor of the new `origin/main`, and contain no commit absent from `origin/main`. For the expected path run:

```bash
PUBLIC_SOURCE=/Users/kevinriosferrer/projects/codex_marketplace
test -z "$(git -C "$PUBLIC_SOURCE" status --porcelain)"
git -C "$PUBLIC_SOURCE" fetch origin main
git -C "$PUBLIC_SOURCE" merge-base --is-ancestor HEAD origin/main
test -z "$(git -C "$PUBLIC_SOURCE" rev-list origin/main..HEAD)"
git -C "$PUBLIC_SOURCE" switch --detach "$CACHEBUSTER_COMMIT"
test "$CACHEBUSTER_COMMIT" = "$(git -C "$PUBLIC_SOURCE" rev-parse HEAD)"
```

If the reported source path is different, dirty, divergent, or has unpushed commits, stop and preserve it. Never modify the divergent `codex/canonical-consolidation-public` worktree merely because its name resembles the marketplace source. This authorized bridge is required before the public selector can install the new version.

- [ ] **Step 5: Install and resolve the exact public cache**

Run the following exact resolution flow. `TARGET_VERSION` is read from the committed manifest; the cache family is fixed to the configured public-marketplace family, and the helper prints only the validated exact root:

```bash
TARGET_VERSION=$(python3 -B -c 'import json; print(json.load(open("plugins/professional-growth-coach/.codex-plugin/plugin.json", encoding="utf-8"))["version"])')
codex plugin add professional-growth-coach@codex-marketplace-public --json
PLUGIN_LIST_JSON=$(mktemp)
chmod 600 "$PLUGIN_LIST_JSON"
codex plugin list --marketplace codex-marketplace-public --json > "$PLUGIN_LIST_JSON"
INSTALLED_PLUGIN_ROOT=$(python3 -B scripts/verify_installed_plugin_release.py resolve \
  --plugin-list "$PLUGIN_LIST_JSON" \
  --plugin professional-growth-coach \
  --marketplace codex-marketplace-public \
  --expected-version "$TARGET_VERSION" \
  --cache-family /Users/kevinriosferrer/.codex/plugins/cache/codex-marketplace-public)
```

Require exactly one enabled matching row and the exact new version. Resolve the cache directory only as cache family / plugin / exact reported version; do not use `latest`, lexicographic sorting, cache deletion, or manual config mutation.

- [ ] **Step 6: Prove exact archive/cache parity**

Create and verify the immutable source archive without a mutable-worktree comparison:

```bash
RELEASE_TMP=$(mktemp -d)
chmod 700 "$RELEASE_TMP"
SOURCE_ARCHIVE="$RELEASE_TMP/professional-growth-coach"
ARCHIVE_TAR="$RELEASE_TMP/professional-growth-coach.tar"
mkdir "$SOURCE_ARCHIVE"
git archive --format=tar --output="$ARCHIVE_TAR" \
  "$CACHEBUSTER_COMMIT":plugins/professional-growth-coach
tar -xf "$ARCHIVE_TAR" -C "$SOURCE_ARCHIVE"
python3 -B scripts/verify_installed_plugin_release.py parity \
  --source-root "$SOURCE_ARCHIVE" \
  --cache-root "$INSTALLED_PLUGIN_ROOT"
```

Require equal non-zero sorted POSIX relative inventories and equal per-file SHA-256. Compute aggregate SHA-256 over each sorted record:

```python
record = relative_path.encode("utf-8") + b"\0" + file_sha256_hex.encode("ascii") + b"\n"
```

Require aggregate equality, `diff -qr` silence, and zero `.pyc`, `.pyo`, or `__pycache__` on source/archive/cache. Diagnostics expose relative paths only.

- [ ] **Step 7: Run installed accepted/rejected v3 smokes**

Run `PYTHONDONTWRITEBYTECODE=1 python3 -B scripts/run_installed_learning_eligibility_v3_smokes.py --plugin-root "$INSTALLED_PLUGIN_ROOT" --source-archive "$SOURCE_ARCHIVE"`. The harness first asserts every imported product module resolves under that exact installed root, never the checkout. Require:

1. public V1+Terraform response maps to private V-003 only after validation;
2. 1/5 produces private packet and zero learning rows;
3. synthetic recurrent 2/5 proof produces one bounded-proof row;
4. supported/unknown/experience states produce their exact one action and zero learning rows;
5. provider absent/empty/choice/selected lifecycle is exact, L1 maps to LP-001, LP-002 displacement rejects;
6. all 12 basis/action rows, ES/EN copy, exact unions, snapshots, and v3 DOM/ARIA pass;
7. private IDs/URLs/prose/raw enums remain absent; forged/crossed/mutable/oversized/exceptional inputs reject generically without echo;
8. writer/CLI reject before output; v1/v2/no-market byte snapshots remain pinned;
9. installed package discovery/static checks pass and report repository conformance not bundled.

- [ ] **Step 8: Create attestation-only commit B**

Update `tests/evals/final/installed-smoke-test.md` with commit A as `source_commit`, its exact plugin tree, exact version/cache resolution, non-zero counts, per-file and aggregate hashes, accepted/rejected counts/scopes, source/package/static/release results, v1/v2 bytes, privacy/no-echo/atomicity, repository-only scope, external actions not executed, and honest visual/browser/AT scope. Commit only attestation documentation:

```bash
git add tests/evals/final/installed-smoke-test.md
git commit -m "docs: attest vacancy-first learning release"
```

Run the prewritten actual-attestation assertion in `tests/test_full_plugin.py` and require it to parse commit A/tree/version/counts/source aggregate/cache aggregate/smoke matrix/scope without accepting missing, duplicate, or stale fields.

- [ ] **Step 9: Final validation and publication**

Run `bash scripts/bootstrap_release_validation.sh`, then `CODEX_SYSTEM_SKILLS_ROOT=/Users/kevinriosferrer/.codex/skills/.system bash scripts/run_release_validation.sh` after commit B. Require clean status, then publish and verify exactly:

```bash
ATTESTATION_COMMIT=$(git rev-parse HEAD)
git push origin HEAD:main
git fetch origin main
test "$ATTESTATION_COMMIT" = "$(git rev-parse origin/main)"
REMOTE_MAIN=$(git ls-remote --exit-code origin refs/heads/main | cut -f1)
test "$REMOTE_MAIN" = "$ATTESTATION_COMMIT"
```

Re-resolve the public source checkout and run the same cleanliness/ancestry/no-local-only-commit checks with `ATTESTATION_COMMIT`, then `git -C "$PUBLIC_SOURCE" switch --detach "$ATTESTATION_COMMIT"` and assert its HEAD. Preserve every divergent/dirty worktree. If network verification fails, report it and do not claim a fresh live remote check. Any newly discovered release-documentation change stops this step and must be implemented/reviewed before cachebuster A; commit B remains attestation-only.

- [ ] **Step 10: Final handoff and next-cycle intake**

Report exact commits A/B, installed version/path class, parity counts/digests, test totals, accepted/rejected smokes, historical compatibility, security/product review, Superdesign/browser evidence scope, and every ledger ruling. Then audit the published increment for the next highest-value independent product, UX, and security opportunity; begin a new brainstorming/spec cycle rather than silently expanding this release.

## Spec Coverage Self-Review

| Binding contract | Planned evidence |
| --- | --- |
| Independent public response and no private selection input | Task 1 closed schema, public ordinal tests, source snapshot binding, no-echo/TOCTOU matrix |
| Exact private resolution without reconstructed intent | Task 2 response-first projection, Vn/Ln mapping, crossed-source and override rejection |
| Recurrence/support/relation/provider decision authority | Task 3 exhaustive 12-row ordered matrix, exact source recomputation, score/prose invariance |
| Zero-or-one v3 learning decision | Task 4 eligibility-only constructor, v3-owned route/join, exact unions and zero/eager cardinality tests |
| Unavailable retains one existing safe action | Tasks 3–5 unavailable row plus explicit absence of weekly card and learning grid |
| One-pass bounded input boundary | Tasks 1–5 shared captured mapping, hostile mutable inputs, budget/cycle/exception tests, renderer capture before any read |
| Historical v1/v2/no-market byte compatibility | Tasks 1–5 compatibility gates and v3-only CSS/DOM branches |
| Superdesign and accessibility | Task 5 cold SOP, upload/canvas approval, named article, resolved ARIA, mobile/print/dark/forced/reduced contracts and exact mirrors |
| Privacy and no external action | Tasks 1–7 closed schemas, repository inventory, renderer/CLI no-echo, no links/forms/buttons/private IDs, installed rejection smokes |
| Reproducible installed release | Tasks 6–7 tested resolver/parity/smoke helpers, cachebuster A, exact selector, archive/cache hashes, attestation B and final remote verification |

Self-review ruling: every normative spec section has an owning task, a prewritten RED assertion, a source or installed GREEN gate, and an explicit compatibility/privacy boundary. No unresolved implementation marker or vague substitute remains.

## Execution Handoff

Commit this reviewed plan as its own documentation commit before creating the SDD ledger or starting Task 1, and require the worktree to be clean immediately afterward. The user already selected Subagent-Driven execution with multiple expert agents. Execute Tasks 1–7 continuously with `superpowers:subagent-driven-development`, one implementer at a time, task review after every task, and one broad final review. Stop only for the Superdesign context-upload/canvas approval gate or the explicit external publication side effects described in Task 7.
