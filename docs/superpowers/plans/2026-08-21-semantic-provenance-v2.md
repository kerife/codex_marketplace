# Semantic Provenance v2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build deterministic, snapshot-bound market and learning provenance v2 without changing v1 semantics or exposing internal evidence in candidate-facing HTML.

**Architecture:** Add four closed contracts in dependency order: pure candidate/market alignment, recomputed market dossier, independent provider research, and projected learning decisions. Builders derive all semantic joins from validated sources; validators recompute expected objects rather than trusting output fields; the renderer accepts only coherent v1/v1 or v2/v2 compositions and projects a privacy-safe per-signal view.

**Tech Stack:** Python 3 standard library, JSON Schema draft 2020-12, `unittest`, deterministic SHA-256 snapshots, HTML/CSS, existing plugin static/release harnesses.

**Spec:** `docs/superpowers/specs/2026-08-21-semantic-provenance-v2-design.md`

## Global Constraints

- Keep every v1 schema, validator, fixture, builder, and renderer path read-only compatible; do not change v1 meaning.
- Normalize a technology term only with Unicode NFKC, trim, casefold, replacement of non-empty ASCII whitespace or `-` runs with `_`, then require `^[a-z][a-z0-9_]{1,63}$`.
- Do not use NLP, embeddings, synonyms, stemming, substrings, aliases, provider prose, or caller prose to establish a semantic relationship.
- Builders raise generic `ValueError` before opening output files; validators return bounded generic diagnostics without echoing signals, IDs, URLs, paths, provider values, or prose.
- Preserve totality for malformed, cyclic, over-depth, oversized, non-string, and Unicode-edge inputs.
- Preserve v1 no-market renderer byte snapshots.
- Do not render internal IDs, snapshots, source URLs, source paraphrases, raw enums, or arbitrary input prose.
- Preserve proof/cost, privacy, authorization, mobile, print, dark-mode, forced-colors, and ARIA contracts.
- Tasks 1–5 are internal parts of one executable increment; only the reviewed complete stack is versioned, installed, attested, and pushed in Task 6.
- Never upload repository fixtures, dossiers, snapshots, or generated artifacts to an external design canvas. If Superdesign artifact upload is unavailable, use deterministic local HTML/CSS/DOM review and state that browser/assistive-technology QA was not run.

## File Structure

- `plugins/professional-growth-coach/scripts/derive_candidate_market_alignment_v2.py`: the sole pure constructor for v2 signal bindings and normalized term labels.
- `plugins/professional-growth-coach/scripts/build_career_market_learning_dossier_v2.py`: builds market v2 only from research and executive dossier sources.
- `plugins/professional-growth-coach/scripts/validate_career_market_learning_dossier_v2.py`: validates sources, recomputes alignment and the complete market object, and compares canonical objects.
- `plugins/professional-growth-coach/scripts/validate_career_learning_provider_research.py`: validates independent official-provider research and computes its snapshot.
- `plugins/professional-growth-coach/scripts/project_career_learning_decision_v2.py`: owns the closed decision-code table and all ES/EN output projection.
- `plugins/professional-growth-coach/scripts/build_career_learning_decision_v2.py`: accepts four-field decision requests and computes every other field.
- `plugins/professional-growth-coach/scripts/validate_career_learning_decision_v2.py`: recomputes and compares the complete learning v2 bundle.
- New `*-v2.schema.json` files: closed JSON contracts; v1 schemas remain unchanged.
- `tests/test_semantic_provenance_v2.py`: focused cross-source derivation, tampering, totality, and deterministic-copy tests.
- Existing market, learning, renderer, structure, privacy, static, and release tests: compatibility and package gates.

---

### Task 1: Pure Candidate/Market Alignment v2

**Files:**
- Create: `plugins/professional-growth-coach/schemas/candidate-market-alignment-v2.schema.json`
- Create: `plugins/professional-growth-coach/scripts/derive_candidate_market_alignment_v2.py`
- Create: `tests/test_semantic_provenance_v2.py`
- Modify: `plugins/professional-growth-coach/tests/test_private_schema_conformance.py`
- Modify: `plugins/professional-growth-coach/tests/run_static_checks.py`
- Modify: `tests/test_full_plugin.py`

**Interfaces:**
- Consumes: `validate_research(value) -> list[str]`, `validate_dossier(value) -> list[str]`, `snapshot_for_market_dossier(value) -> str`, and `snapshot_for_dossier(value) -> str` from existing sibling modules.
- Produces: `normalize_signal_term(value: object) -> str`, `derive_candidate_market_alignment_v2(research: object, executive_dossier: object) -> dict[str, object]`, and `snapshot_for_alignment_v2(value: Mapping[str, object]) -> str` with prefix `snap-alignment-sha256-`.
- Produces each binding with exactly `signal`, `support_state`, `claim_ids`, `evidence_ids`, `requirement_ids`, and `vacancy_ids`, all ID arrays unique and sorted.

- [ ] **Step 1: Write the complete normalization, derivation, ordering, and totality RED matrix**

Add imports through the test module's existing sibling-loader pattern, then add this exact matrix:

```python
def test_v2_normalization_is_exact_and_rejects_aliases(self):
    accepted = {
        "Terraform": "terraform",
        "  Google Cloud  ": "google_cloud",
        "Site-Reliability": "site_reliability",
    }
    for raw, expected in accepted.items():
        with self.subTest(raw=raw):
            self.assertEqual(expected, ALIGNMENT_V2.normalize_signal_term(raw))
    for raw in ("C++", "node.js", "site/reliability", "terra", "", None, 7):
        with self.subTest(raw=raw):
            with self.assertRaisesRegex(ValueError, "technology term is invalid"):
                ALIGNMENT_V2.normalize_signal_term(raw)

def test_observability_cannot_borrow_verified_headline_evidence(self):
    research, dossier = self.complete_sources()
    alignment = ALIGNMENT_V2.derive_candidate_market_alignment_v2(research, dossier)
    row = next(item for item in alignment["signal_bindings"] if item["signal"] == "observability")
    self.assertEqual("unknown", row["support_state"])
    self.assertEqual([], row["claim_ids"])
    self.assertEqual([], row["evidence_ids"])
```

In the same RED edit, add the exact-union golden below plus mutations for duplicate normalized terms, missing claim, missing evidence, inferred evidence, reordered/duplicated IDs, cyclic mappings, depth-overflow, oversized lists, and lone surrogates. Assert either the canonical object or exact generic `ValueError`, never raw sentinel text.

```python
def test_complete_fixture_derives_only_terraform_support(self):
    research, dossier = self.complete_sources()
    result = ALIGNMENT_V2.derive_candidate_market_alignment_v2(research, dossier)
    supported = [
        (row["signal"], row["support_state"], row["claim_ids"], row["evidence_ids"])
        for row in result["signal_bindings"]
        if row["support_state"] != "unknown"
    ]
    self.assertEqual([("terraform", "candidate_reported_match", ["C-002"], ["E-004"])], supported)
    self.assertEqual(sorted(result["signal_bindings"], key=lambda row: row["signal"]), result["signal_bindings"])
```

- [ ] **Step 2: Run the focused tests and record RED**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest -q tests.test_semantic_provenance_v2`

Expected: import failure for missing `derive_candidate_market_alignment_v2.py`; record the command and failure in the SDD report before production edits.

- [ ] **Step 3: Add the closed alignment schema**

Create a draft-2020-12 schema with `additionalProperties: false` at root and binding levels. Pin these constants: root `schema_version` to `candidate-market-alignment-v2`, `privacy_boundary` to `identity_free_structured_provenance_only`; signal regex `^[a-z][a-z0-9_]{1,63}$`; claim IDs `^C-[0-9]{3}$`; evidence IDs `^E-[0-9]{3}$`; requirement IDs `^V-[0-9]{3}-R-[0-9]{2}$`; vacancy IDs `^V-[0-9]{3}$`; snapshots to their existing lowercase SHA-256 prefixes. Require all six binding fields and all five root fields, and set `uniqueItems: true` on ID arrays.

- [ ] **Step 4: Implement exact normalization and derivation**

Implement these public functions and keep helper failures generic:

```python
_SIGNAL = re.compile(r"[a-z][a-z0-9_]{1,63}\Z")
_SEPARATOR = re.compile(r"[\t\n\r\f\v -]+")

def normalize_signal_term(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("technology term is invalid")
    normalized = _SEPARATOR.sub("_", unicodedata.normalize("NFKC", value).strip().casefold())
    if not _SIGNAL.fullmatch(normalized):
        raise ValueError("technology term is invalid")
    return normalized

def derive_candidate_market_alignment_v2(
    research: object, executive_dossier: object
) -> dict[str, object]:
    research_copy, dossier_copy = _validated_copies(research, executive_dossier)
    term_index = _unique_term_index(dossier_copy["requested_technology_terms"])
    claim_index = {row["id"]: row for row in dossier_copy["claims"]}
    evidence_index = {row["id"]: row for row in dossier_copy["evidence"]}
    market_index = _research_signal_index(research_copy["vacancies"])
    bindings = [
        _derive_binding(signal, market_index[signal], term_index, claim_index, evidence_index)
        for signal in sorted(market_index)
    ]
    return {
        "schema_version": "candidate-market-alignment-v2",
        "research_snapshot": snapshot_for_market_dossier(research_copy),
        "executive_dossier_snapshot": snapshot_for_dossier(dossier_copy),
        "signal_bindings": bindings,
        "privacy_boundary": "identity_free_structured_provenance_only",
    }

def snapshot_for_alignment_v2(value: Mapping[str, object]) -> str:
    validated = _validate_alignment_v2(value)
    digest = hashlib.sha256(_canonical_json(validated).encode("utf-8")).hexdigest()
    return f"snap-alignment-sha256-{digest}"
```

`_unique_term_index` must fail on normalization collisions. `_derive_binding` must emit `verified_match` only when every linked claim and evidence record is `verified`; emit `candidate_reported_match` when at least one is `candidate_reported` and none is `inferred`/`unknown`; otherwise emit `unknown` with empty claim/evidence arrays. It must always retain the exact market-side requirement/vacancy arrays.

- [ ] **Step 5: Run the complete prewritten RED matrix green**

Rerun every Task 1 test written in Step 1. Expected: all pass without weakening an assertion or changing the malicious fixtures.

- [ ] **Step 6: Register schema and tests in package/static inventories**

Add the new schema and script paths to the explicit inventories in `run_static_checks.py` and `tests/test_full_plugin.py`. Extend private schema conformance to load the schema and validate a derived fixture object without modifying v1 assertions.

- [ ] **Step 7: Run Task 1 gates**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest -q \
  tests.test_semantic_provenance_v2 \
  tests.test_career_market_learning_dossier \
  tests.test_plugin_structure
PYTHONDONTWRITEBYTECODE=1 python3 -B plugins/professional-growth-coach/tests/run_static_checks.py
git diff --check
```

Expected: all commands exit 0 and the plugin tree contains no `__pycache__`, `.pyc`, or `.pyo`.

- [ ] **Step 8: Commit Task 1**

```bash
git add plugins/professional-growth-coach/schemas/candidate-market-alignment-v2.schema.json \
  plugins/professional-growth-coach/scripts/derive_candidate_market_alignment_v2.py \
  plugins/professional-growth-coach/tests/test_private_schema_conformance.py \
  plugins/professional-growth-coach/tests/run_static_checks.py \
  tests/test_semantic_provenance_v2.py tests/test_full_plugin.py
git commit -m "feat: derive semantic market alignment v2"
```

---

### Task 2: Recomputed Career Market Learning Dossier v2

**Files:**
- Create: `plugins/professional-growth-coach/schemas/career-market-learning-dossier-v2.schema.json`
- Create: `plugins/professional-growth-coach/scripts/build_career_market_learning_dossier_v2.py`
- Create: `plugins/professional-growth-coach/scripts/validate_career_market_learning_dossier_v2.py`
- Create: `tests/evals/with-skill/fixtures/career-market-learning-dossier-v2/complete-five-es.json`
- Create: `tests/evals/with-skill/fixtures/career-market-learning-dossier-v2/limited-four-en.json`
- Create: `tests/evals/with-skill/fixtures/career-market-learning-dossier-v2/unavailable-es.json`
- Modify: `tests/test_semantic_provenance_v2.py`
- Modify: `plugins/professional-growth-coach/tests/test_private_schema_conformance.py`
- Modify: `plugins/professional-growth-coach/tests/run_static_checks.py`
- Modify: `tests/test_full_plugin.py`

**Interfaces:**
- Consumes: `derive_candidate_market_alignment_v2(research, executive_dossier) -> dict[str, object]`.
- Produces: `build_market_dossier_v2(research: object, executive_dossier: object) -> dict[str, object]`, `validate_market_dossier_v2(value: object, research: object, executive_dossier: object) -> list[str]`, and `snapshot_for_market_dossier_v2(value: Mapping[str, object]) -> str`.
- The validator must derive expected output from the two sources and compare canonical objects; it must not accept an alignment argument.

- [ ] **Step 1: Write the complete RED matrix for recomputation, arithmetic, tampering, ordering, stale sources, and unavailable state**

```python
def test_market_v2_recomputes_alignment_and_rejects_reference_tampering(self):
    research, dossier = self.complete_sources()
    market = MARKET_V2_BUILDER.build_market_dossier_v2(research, dossier)
    self.assertEqual([], MARKET_V2_VALIDATOR.validate_market_dossier_v2(market, research, dossier))
    terraform = next(row for row in market["matrix_rows"] if row["signal"] == "terraform")
    self.assertEqual(["C-002"], terraform["claim_ids"])
    self.assertEqual(["E-004"], terraform["evidence_ids"])
    mutations = {
        "claim": ("claim_ids", ["C-001"]),
        "evidence": ("evidence_ids", ["E-001"]),
        "requirement": ("requirement_ids", ["V-001-R-01"]),
        "vacancy": ("vacancy_ids", ["V-001"]),
    }
    for name, (field, replacement) in mutations.items():
        with self.subTest(name=name):
            altered = copy.deepcopy(market)
            next(row for row in altered["matrix_rows"] if row["signal"] == "terraform")[field] = replacement
            errors = MARKET_V2_VALIDATOR.validate_market_dossier_v2(altered, research, dossier)
            self.assertEqual(["market dossier does not match validated sources"], errors)
```

In this same pre-production test edit, pin the complete fixture's Terraform-only supported row and deterministic score/coverage percentages from a hand-calculated expectation; reject row reordering, deleted rows, duplicate IDs, stale source snapshots, crossed research/dossier pairs, and any synthetic caller alignment field. Assert unavailable output has no candidate support.

- [ ] **Step 2: Run RED**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest -q tests.test_semantic_provenance_v2`

Expected: import failure for missing market v2 builder/validator.

- [ ] **Step 3: Create the v2 market schema**

Copy the v1 structural bounds only where the fields remain identical, change the root version constant, require `source_alignment_snapshot` with prefix `snap-alignment-sha256-`, and require v2 matrix rows to include exact `claim_ids`, `evidence_ids`, `requirement_ids`, and `vacancy_ids`. Keep every object closed and retain the dated search summary, vacancy cards, recurrence rows, methodology, privacy, learning-not-evaluated, and no-action boundaries.

- [ ] **Step 4: Implement builder as a source-only adapter over shared arithmetic**

Expose only:

```python
def build_market_dossier_v2(research: object, executive_dossier: object) -> dict[str, object]:
    research_copy, dossier_copy = _validated_source_copies(research, executive_dossier)
    alignment = derive_candidate_market_alignment_v2(research_copy, dossier_copy)
    result = _project_market_v2(research_copy, dossier_copy, alignment)
    if validate_market_dossier_v2(result, research_copy, dossier_copy):
        raise ValueError("market dossier v2 is invalid")
    return result
```

`_project_market_v2` must reuse the v1 integer rounding and recurrence arithmetic but populate every matrix row from the exact v2 binding. For unavailable research, emit empty cards/matrix/recurrence and a snapshot of the empty canonical alignment.

- [ ] **Step 5: Implement validator by complete recomputation**

After bounded deep-copy and schema validation, compute `alignment = derive_candidate_market_alignment_v2(validated_research, validated_dossier)` and then `expected = _project_market_v2(validated_research, validated_dossier, alignment)`. Return `[]` only when `canonical_json(value) == canonical_json(expected)`; otherwise return exactly `['market dossier does not match validated sources']`. Catch structural/graph/type exceptions and return one generic diagnostic.

- [ ] **Step 6: Run the complete prewritten Task 2 matrix green**

Rerun every Task 2 test from Step 1. Expected: all arithmetic, tampering, ordering, stale-source, and unavailable assertions pass without changing their inputs.

- [ ] **Step 7: Generate canonical fixtures through the builder and register inventory**

Use a short `python3 -B` command that imports the builder by file path, loads each existing research/dossier pair, calls `build_market_dossier_v2`, and writes sorted UTF-8 JSON with a trailing newline to the three exact fixture paths. Then add those files, the schema, and both scripts to static/full-plugin inventories and schema-conformance tests.

- [ ] **Step 8: Run Task 2 gates**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest -q \
  tests.test_semantic_provenance_v2 \
  tests.test_career_market_learning_dossier \
  tests.test_plugin_structure \
  plugins/professional-growth-coach/tests/test_private_schema_conformance.py
PYTHONDONTWRITEBYTECODE=1 python3 -B plugins/professional-growth-coach/tests/run_static_checks.py
git diff --check
```

- [ ] **Step 9: Commit Task 2**

```bash
git add plugins/professional-growth-coach/schemas/career-market-learning-dossier-v2.schema.json \
  plugins/professional-growth-coach/scripts/build_career_market_learning_dossier_v2.py \
  plugins/professional-growth-coach/scripts/validate_career_market_learning_dossier_v2.py \
  plugins/professional-growth-coach/tests/test_private_schema_conformance.py \
  plugins/professional-growth-coach/tests/run_static_checks.py \
  tests/evals/with-skill/fixtures/career-market-learning-dossier-v2 \
  tests/test_semantic_provenance_v2.py tests/test_full_plugin.py
git commit -m "feat: build recomputed market dossier v2"
```

---

### Task 3: Independent Career Learning Provider Research

**Files:**
- Create: `plugins/professional-growth-coach/schemas/career-learning-provider-research-v1.schema.json`
- Create: `plugins/professional-growth-coach/scripts/validate_career_learning_provider_research.py`
- Create: `tests/evals/with-skill/fixtures/career-learning-provider-research/complete-es.json`
- Create: `tests/evals/with-skill/fixtures/career-learning-provider-research/limited-en.json`
- Create: `tests/evals/with-skill/fixtures/career-learning-provider-research/unavailable-es.json`
- Modify: `tests/test_semantic_provenance_v2.py`
- Modify: `plugins/professional-growth-coach/tests/test_private_schema_conformance.py`
- Modify: `plugins/professional-growth-coach/tests/run_static_checks.py`
- Modify: `tests/test_full_plugin.py`

**Interfaces:**
- Consumes: shared public-prose/privacy guards from `private_prose_safety.py`; normalized signal syntax from Task 1, but never derives a signal from provider prose.
- Produces: `validate_provider_research(value: object) -> list[str]`, `load_provider_research(path: Path) -> dict[str, object]`, and `snapshot_for_provider_research(value: Mapping[str, object]) -> str` with prefix `snap-provider-sha256-`.

- [ ] **Step 1: Write the complete provider-source structure, provenance, privacy, and totality RED matrix**

```python
def test_provider_research_is_independent_closed_and_snapshot_bound(self):
    provider = self.provider_fixture("complete-es.json")
    self.assertEqual([], PROVIDER_VALIDATOR.validate_provider_research(provider))
    self.assertRegex(
        PROVIDER_VALIDATOR.snapshot_for_provider_research(provider),
        r"\Asnap-provider-sha256-[0-9a-f]{64}\Z",
    )
    terraform = next(row for row in provider["options"] if row["option_id"] == "LP-001")
    self.assertEqual(["terraform"], terraform["covered_signals"])
    argo = next(row for row in provider["options"] if row["option_id"] == "LP-002")
    self.assertEqual([], argo["covered_signals"])

def test_provider_research_rejects_caller_semantics_and_private_values_without_echo(self):
    provider = self.provider_fixture("complete-es.json")
    for field, value in (
        ("provider", "Synthetic Candidate"),
        ("url", "https://www.cncf.io/terraform-course"),
        ("coverage_basis", "caller_claim"),
    ):
        with self.subTest(field=field):
            altered = copy.deepcopy(provider)
            altered["options"][0][field] = value
            errors = PROVIDER_VALIDATOR.validate_provider_research(altered)
            self.assertTrue(errors)
            self.assertNotIn(str(value), " ".join(errors))
```

In this same pre-production edit, reject duplicate option IDs, unsorted/duplicate signals, invalid signal syntax, future source/access dates, non-HTTPS URLs, credential-bearing URLs, a known provider paired with a public HTTPS host outside its exact official-host allowlist, option/state incompatibility, invalid coverage basis, arbitrary fields, cycles, depth overflow, huge strings/lists, raw controls, lone surrogates, and personal/contact-like data. Assert all diagnostics are bounded and exclude every injected sentinel.

- [ ] **Step 2: Run RED**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest -q tests.test_semantic_provenance_v2`

Expected: missing provider schema/validator/fixture failures.

- [ ] **Step 3: Create the exact closed provider schema**

Require root fields `schema_version`, `locale`, `as_of_date`, `state`, `options`, `privacy_boundary`, and `no_external_action`. Set constants `career-learning-provider-research-v1`, `public_provider_metadata_only`, and `true`; bound options to 0–20. Require each option to have exactly the twenty-one fields listed by the spec, `option_id` pattern `^LP-[0-9]{3}$`, closed enums for type/state/availability/coverage basis, HTTPS URL syntax, normalized unique/sorted signal keys, ISO dates, bounded strings/arrays, and `additionalProperties: false`.

- [ ] **Step 4: Implement total validation and canonical snapshot**

Implement:

```python
def validate_provider_research(value: object) -> list[str]:
    root = _bounded_plain_copy(value)
    errors = _closed_structure_errors(root)
    errors.extend(_date_and_state_errors(root))
    errors.extend(_option_errors(root))
    return _bounded_unique_errors(errors)

def snapshot_for_provider_research(value: Mapping[str, object]) -> str:
    if validate_provider_research(value):
        raise ValueError("provider research is invalid")
    digest = hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()
    return f"snap-provider-sha256-{digest}"
```

`_option_errors` must verify official HTTPS, date ordering against `as_of_date`, sorted/unique signals, public-provider prose guards for every text field, raw controls/Unicode/length limits, and the rule that unavailable source options carry no coverage. It must not infer coverage from provider, title, URL, or prose.

For the initial bounded provider set, define the exact provider/host relation in production as immutable data, not caller input:

```python
_OFFICIAL_PROVIDER_HOSTS = {
    "HashiCorp": frozenset({"developer.hashicorp.com"}),
    "Argo Project": frozenset({"argo-cd.readthedocs.io"}),
}
```

Require `urlsplit(url).hostname` to be an exact member for that provider after standard hostname normalization; reject userinfo, IP literals, alternate ports, subdomain suffix tricks, and every provider absent from the mapping. Expanding the provider set requires a reviewed code/test change plus independent source evidence.

- [ ] **Step 5: Add complete, limited, and unavailable fixtures**

Create synthetic public-provider fixtures. `complete-es.json` contains LP-001, an active HashiCorp Terraform option explicitly bound to `terraform`, and LP-002, an unrelated Argo option with `covered_signals: []`. `limited-en.json` contains one active option and explicit unknowns. `unavailable-es.json` contains zero options. Use synthetic source titles and official public URLs only; no person names, local paths, contact data, or private dossier data.

- [ ] **Step 6: Run the complete prewritten Task 3 matrix green**

Rerun every provider test from Step 1. Expected: structure, provider/host, state/date, privacy, no-echo, and totality assertions all pass unchanged.

- [ ] **Step 7: Register source contract in package gates**

Add schema, validator, and three fixtures to static and release inventories. Extend schema conformance with all three fixtures and one closed-field mutation.

- [ ] **Step 8: Run Task 3 gates**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest -q \
  tests.test_semantic_provenance_v2 \
  tests.test_plugin_structure \
  plugins/professional-growth-coach/tests/test_private_schema_conformance.py
PYTHONDONTWRITEBYTECODE=1 python3 -B plugins/professional-growth-coach/tests/run_static_checks.py
git diff --check
```

- [ ] **Step 9: Commit Task 3**

```bash
git add plugins/professional-growth-coach/schemas/career-learning-provider-research-v1.schema.json \
  plugins/professional-growth-coach/scripts/validate_career_learning_provider_research.py \
  plugins/professional-growth-coach/tests/test_private_schema_conformance.py \
  plugins/professional-growth-coach/tests/run_static_checks.py \
  tests/evals/with-skill/fixtures/career-learning-provider-research \
  tests/test_semantic_provenance_v2.py tests/test_full_plugin.py
git commit -m "feat: validate independent learning provider research"
```

---

### Task 4: Closed Career Learning Decision v2 Projection

**Files:**
- Create: `plugins/professional-growth-coach/schemas/career-learning-decision-v2.schema.json`
- Create: `plugins/professional-growth-coach/scripts/project_career_learning_decision_v2.py`
- Create: `plugins/professional-growth-coach/scripts/build_career_learning_decision_v2.py`
- Create: `plugins/professional-growth-coach/scripts/validate_career_learning_decision_v2.py`
- Create: `tests/evals/with-skill/fixtures/career-learning-decision-v2/complete-es.json`
- Create: `tests/evals/with-skill/fixtures/career-learning-decision-v2/limited-en.json`
- Create: `tests/evals/with-skill/fixtures/career-learning-decision-v2/unavailable-es.json`
- Modify: `tests/test_semantic_provenance_v2.py`
- Modify: `tests/test_career_learning_decision.py`
- Modify: `plugins/professional-growth-coach/tests/test_private_schema_conformance.py`
- Modify: `plugins/professional-growth-coach/tests/run_static_checks.py`
- Modify: `tests/test_full_plugin.py`

**Interfaces:**
- Consumes: research, executive dossier, market v2, alignment v2, and provider research validated independently.
- Produces: `project_decision_v2(locale: str, request: Mapping[str, object], routes: list[dict[str, object]], provider_option: Mapping[str, object] | None) -> dict[str, object]`.
- Produces: `build_learning_bundle_v2(research, market_dossier, executive_dossier, provider_research, decision_requests) -> dict[str, object]`.
- Produces: `validate_learning_bundle_v2(value, research, market_dossier, executive_dossier, provider_research) -> list[str]` and `snapshot_for_learning_bundle_v2(value) -> str`.
- Each request is closed to `decision_rank`, `decision_code`, `source_signals`, and `provider_option_id`.

- [ ] **Step 1: Write the complete RED matrix for exact routes, closed projection, provider displacement, tampering, and totality**

```python
def test_learning_v2_accepts_only_four_input_fields_and_exact_terraform_route(self):
    sources = self.complete_v2_sources()
    requests = [{
        "decision_rank": 1,
        "decision_code": "build_bounded_proof",
        "source_signals": ["terraform"],
        "provider_option_id": None,
    }]
    result = LEARNING_V2_BUILDER.build_learning_bundle_v2(*sources, requests)
    row = result["decisions"][0]
    self.assertEqual(["C-002"], row["claim_ids"])
    self.assertEqual(["E-004"], row["source_evidence_ids"])
    self.assertEqual(["V-003-R-01"], row["requirement_ids"])
    self.assertEqual(["V-003"], row["vacancy_ids"])
    self.assertEqual(["terraform"], [route["signal"] for route in row["signal_routes"]])

def test_quantum_semantics_and_caller_output_fields_fail_closed(self):
    sources = self.complete_v2_sources()
    bad_rows = [
        {"decision_rank": 1, "decision_code": "build_bounded_proof", "source_signals": ["quantum_computing"], "provider_option_id": None},
        {"decision_rank": 1, "decision_code": "research_provider_option", "source_signals": ["terraform"], "provider_option_id": "LP-002"},
        {"decision_rank": 1, "decision_code": "build_bounded_proof", "source_signals": ["terraform"], "provider_option_id": None, "decision_basis": "Quantum computing changes everything"},
    ]
    for row in bad_rows:
        with self.subTest(row=row):
            with self.assertRaises(ValueError) as raised:
                LEARNING_V2_BUILDER.build_learning_bundle_v2(*sources, [row])
            self.assertNotIn("Quantum", str(raised.exception))
```

In this same pre-production edit, pin the full returned projection object for all five codes in ES and EN. Reject unrelated evidence/vacancy substitutions, source-signal reorder/duplicates, unknown signals, stale/crossed snapshots, a Terraform request using LP-002 whose `covered_signals` is empty, arbitrary option/basis/risk/cost/action fields, provider omission, provider snapshot omission, cycles, oversized values, and Unicode edges without echo.

- [ ] **Step 2: Run RED**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest -q tests.test_semantic_provenance_v2`

Expected: missing projection/builder/validator import failures.

- [ ] **Step 3: Create closed learning v2 schema**

Require root versions/snapshots/locale/date/state/decisions/privacy/no-action/outcome fields from the spec. Require each decision to contain exactly the four request fields plus the derived fields listed in the spec. Close and bound `signal_routes`; pin ID patterns; require normalized/sorted/unique signals and IDs; close the five decision codes and their resulting gap/option/decision enums. Do not include any v1 free-text input field.

- [ ] **Step 4: Implement the single pure projection table**

Define one immutable `DECISION_RULES` mapping for the five codes and one immutable `COPY` mapping for ES/EN. Implement:

```python
def project_decision_v2(
    locale: str,
    request: Mapping[str, object],
    routes: list[dict[str, object]],
    provider_option: Mapping[str, object] | None,
) -> dict[str, object]:
    _validate_closed_request(request)
    rule = _decision_rule(request["decision_code"])
    labels = [_validated_public_label(route) for route in routes]
    signal_label = _join_labels(locale, labels)
    provider_fields = _provider_fields(rule, provider_option, request["source_signals"])
    return _complete_projection(locale, request, routes, rule, signal_label, provider_fields)
```

`_complete_projection` must generate all visible semantic fields from the fixed spec table. `_provider_fields` must require an active option whose `covered_signals` exactly equals `source_signals` for `research_provider_option`, and must forbid a provider ID for every other code.

- [ ] **Step 5: Implement builder joins and unavailable behavior**

Recompute alignment v2; validate market v2 and provider research; reject any source signal missing from alignment/market or carrying `unknown`; derive exact unions of claim/evidence/requirement/vacancy IDs and exact role families; build one per-signal route with public term label, localized state, recurrence `k/N`, and public vacancy ordinals. Sort signals and routes lexicographically. For unavailable market, accept only `None` or `[]` requests and emit unavailable learning with zero decisions.

- [ ] **Step 6: Implement validator through builder recomputation**

After validating all source snapshots and the closed output schema, reduce each output decision to its four request fields, call `build_learning_bundle_v2` with those requests, and compare the complete canonical expected object to the supplied value. Return one generic mismatch diagnostic. This pins every projected string and every join without trusting output semantics.

- [ ] **Step 7: Run the complete prewritten Task 4 matrix green**

Rerun every Task 4 test from Step 1. Expected: all ES/EN projection, exact-union, provider-displacement, tampering, closed-input, no-echo, and totality assertions pass unchanged.

- [ ] **Step 8: Generate and register learning v2 fixtures**

Generate complete ES with four Terraform decisions (`build_bounded_proof`, `run_validation_lab`, `research_provider_option`, `defer_learning_purchase`), limited EN with bounded supported decisions, and unavailable ES with zero decisions. Register the schema, three scripts, and fixtures in private schema, static, and release inventories.

- [ ] **Step 9: Run Task 4 gates**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest -q \
  tests.test_semantic_provenance_v2 \
  tests.test_career_learning_decision \
  tests.test_career_market_learning_dossier \
  tests.test_plugin_structure \
  plugins/professional-growth-coach/tests/test_private_schema_conformance.py
PYTHONDONTWRITEBYTECODE=1 python3 -B plugins/professional-growth-coach/tests/run_static_checks.py
git diff --check
```

- [ ] **Step 10: Commit Task 4**

```bash
git add plugins/professional-growth-coach/schemas/career-learning-decision-v2.schema.json \
  plugins/professional-growth-coach/scripts/project_career_learning_decision_v2.py \
  plugins/professional-growth-coach/scripts/build_career_learning_decision_v2.py \
  plugins/professional-growth-coach/scripts/validate_career_learning_decision_v2.py \
  plugins/professional-growth-coach/tests/test_private_schema_conformance.py \
  plugins/professional-growth-coach/tests/run_static_checks.py \
  tests/evals/with-skill/fixtures/career-learning-decision-v2 \
  tests/test_semantic_provenance_v2.py tests/test_career_learning_decision.py tests/test_full_plugin.py
git commit -m "feat: project learning decisions from semantic provenance"
```

---

### Task 5: Strict Version Routing and Privacy-Safe Renderer Projection

**Files:**
- Modify: `plugins/professional-growth-coach/scripts/render_executive_career_dossier_v2.py`
- Modify: `tests/test_executive_career_dossier_v2.py`
- Modify: `tests/test_repository_privacy.py`
- Modify: `tests/test_superdesign_theme_asset_parity.py`
- Modify: `.superdesign/design-system.md`
- Modify: `.superdesign/init/pages.md`
- Modify: `.superdesign/init/routes.md`
- Modify: `plugins/professional-growth-coach/README.md`

**Interfaces:**
- Consumes: market v1 + optional learning v1 + the existing v1 source group, or market v2 + required research/executive-dossier sources + optional learning v2. Provider research is required only when learning v2 is present; market v2 without learning accepts `provider_research=None`. Versions are never mixed.
- Extends: `render_dossier_html(dossier, market_dossier=None, *, market_research=None, market_alignment=None, learning_decision=None, provider_research=None) -> str` and `write_dossier_html(dossier_path: Path, output_path: Path, *, market_dossier_path: Path | None = None, market_research_path: Path | None = None, market_alignment_path: Path | None = None, learning_decision_path: Path | None = None, provider_research_path: Path | None = None, force: bool = False) -> RenderReceipt` while keeping existing callers valid. `market_alignment` remains required for v1 composition and must be absent for v2 because v2 recomputes it from research and dossier.
- Produces: one public route row per learning v2 source signal containing only the validated technology label, localized support state, vacancy ordinals, recurrence, deterministic basis, and deterministic decision label.

- [ ] **Step 1: Write the complete RED matrix for composition, privacy, ARIA, state behavior, and v1 byte compatibility**

```python
def test_renderer_accepts_only_coherent_market_learning_versions(self):
    v1 = self.v1_render_sources()
    v2 = self.v2_render_sources()
    self.assertIn("market-context", RENDERER.render_dossier_html(**v1))
    self.assertIn("learning-signal-route", RENDERER.render_dossier_html(**v2))
    market_only_v2 = dict(v2, learning_decision=None, provider_research=None)
    self.assertIn("market-context", RENDERER.render_dossier_html(**market_only_v2))
    self.assertNotIn("learning-signal-route", RENDERER.render_dossier_html(**market_only_v2))
    crossed = [dict(v2, learning_decision=v1["learning_decision"]), dict(v1, market_dossier=v2["market_dossier"], market_alignment=None)]
    for arguments in crossed:
        with self.subTest(versions=[value.get("schema_version") for value in arguments.values() if isinstance(value, dict)]):
            with self.assertRaisesRegex(ValueError, "market and learning versions are incompatible"):
                RENDERER.render_dossier_html(**arguments)

def test_learning_v2_route_omits_internal_and_source_values(self):
    html = RENDERER.render_dossier_html(**self.v2_render_sources())
    for forbidden in ("C-002", "E-004", "V-003-R-01", "snap-", "https://", "Synthetic test requirement"):
        self.assertNotIn(forbidden, html)
    self.assertIn("Terraform", html)
    self.assertIn("1/5", html)
    self.assertIn("V3", html)
```

In this same pre-production edit, assert complete/limited ES/EN v2 outputs have one route group per decision, one row per signal, unique/resolved IDs and ARIA references, correct recurrence/ordinals, and no raw enums. Cover every v1/v2 pairing in the composition matrix; assert unavailable and legacy no-market omit the route; and pin the existing v1 no-market byte length/SHA snapshots unchanged. Inject synthetic private names, contact-like strings, local paths, URLs, snapshots, internal IDs, raw controls, and arbitrary source prose into every accepted v2 source field, then assert generic pre-render failure, no echo, and no partial output file.

- [ ] **Step 2: Run RED**

Run the two new tests by their exact class/method names under `tests.test_executive_career_dossier_v2`.

Expected: missing v2 version routing/provider argument and missing `learning-signal-route` markup.

- [ ] **Step 3: Add strict preflight dispatch**

Before rendering any market content, inspect root `schema_version` values and choose exactly one path:

```python
def _market_learning_generation(market: Mapping[str, object], learning: Mapping[str, object] | None) -> str:
    market_version = market.get("schema_version")
    learning_version = learning.get("schema_version") if learning is not None else None
    allowed = {
        ("career-market-learning-dossier-v1", None): "v1",
        ("career-market-learning-dossier-v1", "career-learning-decision-v1"): "v1",
        ("career-market-learning-dossier-v2", None): "v2",
        ("career-market-learning-dossier-v2", "career-learning-decision-v2"): "v2",
    }
    generation = allowed.get((market_version, learning_version))
    if generation is None:
        raise ValueError("market and learning versions are incompatible")
    return generation
```

For v2 learning, require and validate provider research plus all exact snapshots before any HTML assembly. For unavailable market v2, accept only unavailable learning v2 with zero decisions. Legacy no-market accepts no v2 bundle.

- [ ] **Step 4: Add deterministic safe signal-route view model**

Build renderer rows only from the validated v2 decision `signal_routes` plus adjacent public vacancy ordinals. Escape every visible value. Do not read claim/evidence/requirement/vacancy IDs, provider source titles/descriptions/URLs/unknowns, snapshots, or source paraphrases while constructing markup.

```python
def _learning_signal_route_view(row: Mapping[str, object], locale: str) -> list[dict[str, str]]:
    return [
        {
            "label": _escaped_public_term(route["term_label"]),
            "support": LABELS[locale]["support_states"][route["support_state"]],
            "vacancies": ", ".join(route["vacancy_ordinals"]),
            "recurrence": route["recurrence"],
        }
        for route in row["signal_routes"]
    ]
```

Render each list inside the existing learning card with a localized heading and existing card/boundary structure. Reuse existing typography and fact-grid classes unless a focused CSS addition is required by deterministic layout evidence.

- [ ] **Step 5: Run the prewritten ARIA, state, and v1 compatibility matrix green**

Rerun the composition, ARIA, state, and byte-snapshot tests written in Step 1. Expected: all pass without updating a preexisting v1 snapshot.

- [ ] **Step 6: Run the prewritten repository privacy matrix green**

Rerun the source-field mutation matrix written in Step 1 through direct rendering and CLI/file-writing entrypoints. Expected: fixed generic failures, no sentinel echo, and no output file.

- [ ] **Step 7: Perform Superdesign review within the privacy boundary**

Review only the existing local design system and deterministic rendered DOM/CSS. Do not upload fixtures or generated artifacts. Record in `.superdesign/design-system.md` and route/page maps that v2 adds a compact per-signal proof route, retains v1/no-market/unavailable behavior, exposes no internal IDs or sources, and keeps mobile/print/dark/forced-colors contracts. If no browser/canvas session is used, explicitly record `visual QA not run; deterministic DOM/CSS contract only` in the task report, not in shipped candidate HTML.

- [ ] **Step 8: Run Task 5 gates**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest -q \
  tests.test_semantic_provenance_v2 \
  tests.test_career_market_learning_dossier \
  tests.test_career_learning_decision \
  tests.test_executive_career_dossier_v2 \
  tests.test_repository_privacy \
  tests.test_superdesign_theme_asset_parity \
  tests.test_print_continuity_footer_integrity \
  tests.test_dark_mode_accessibility
git diff --check
```

- [ ] **Step 9: Commit Task 5**

```bash
git add plugins/professional-growth-coach/scripts/render_executive_career_dossier_v2.py \
  plugins/professional-growth-coach/README.md \
  tests/test_executive_career_dossier_v2.py tests/test_repository_privacy.py \
  tests/test_superdesign_theme_asset_parity.py \
  .superdesign/design-system.md .superdesign/init/pages.md .superdesign/init/routes.md
git commit -m "feat: render safe semantic learning routes"
```

---

### Task 6: Whole-Branch Review, Release, Install, Attestation, and Publish

**Files:**
- Modify: `plugins/professional-growth-coach/.codex-plugin/plugin.json`
- Modify: `tests/evals/final/installed-smoke-test.md`
- Modify if inventory assertions require it: `docs/release-validation.md`

**Interfaces:**
- Consumes: the complete reviewed Task 1–5 stack.
- Produces: one cachebuster plugin version, an exact installed cache matching source, an honest attestation, and remote `main` containing the reviewed release.

- [ ] **Step 1: Run independent spec and code-quality review**

Prepare the SDD review package with base commit, Task 1–5 commits, spec, plan, changed-file list, and exact test results. Require a reviewer to return `PASS` only if all spec requirements are present and no P1/P2 findings remain. Any finding returns to the responsible task with a new RED test before production edits.

- [ ] **Step 2: Run independent security and product/UX reviews**

Security must probe the two original semantic bypasses, arbitrary/crossed IDs, caller semantic prose, provider displacement, privacy/no-echo, totality, snapshot staleness, and version mixing. Product/UX must inspect deterministic ES/EN HTML for evidence-route clarity, internal-value absence, unique/resolved ARIA, v1/no-market preservation, mobile/print/dark/forced-colors contracts, and documentation parity. Do not claim browser or assistive-technology QA unless empirically run.

- [ ] **Step 3: Run the complete source verification matrix**

```bash
export PYTHONDONTWRITEBYTECODE=1
python3 -B -m unittest -q \
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
python3 -B -m unittest discover -s plugins/professional-growth-coach/tests -p 'test*.py' -q
python3 -B plugins/professional-growth-coach/tests/run_static_checks.py
python3 -B scripts/check_repository_privacy.py
python3 -B scripts/run_release_validation.py
git diff --check
find plugins/professional-growth-coach -type f \( -name '*.pyc' -o -name '*.pyo' \) -print
find plugins/professional-growth-coach -type d -name __pycache__ -print
```

Expected: every test/check exits 0 and both `find` commands print nothing.

- [ ] **Step 4: Bump cachebuster only after source gates pass**

Set `version` in `plugin.json` to `0.2.0+codex.<UTC YYYYMMDDHHMMSS>` using the existing manifest format. Run structure/static/full-plugin checks again. Commit only the manifest:

```bash
git add plugins/professional-growth-coach/.codex-plugin/plugin.json
git commit -m "chore: refresh semantic provenance plugin cache"
```

- [ ] **Step 5: Install the exact plugin version**

Use the existing Codex plugin install workflow for `professional-growth-coach@codex-marketplace-public`, then verify `codex plugin list` reports enabled and the exact cachebuster. Do not delete old caches or mutate unrelated plugins.

- [ ] **Step 6: Prove exact source/cache inventory and byte parity**

Resolve the installed cache directory from the exact reported version, not lexicographic guessing. Compare sorted relative inventories and SHA-256 for every file, including schemas, scripts, fixtures, and tests. Require equal non-zero file counts, zero `.pyc`/`.pyo`/`__pycache__`, and `diff -qr` silence. Diagnostics may show relative paths only.

- [ ] **Step 7: Run installed accepted/rejected semantic smokes**

With `PYTHONDONTWRITEBYTECODE=1` and installed `scripts` on `PYTHONPATH`, run:

1. derive current fixture alignment and assert only Terraform is supported;
2. build/validate market v2 and assert C-002/E-004/V-003-R-01/V-003;
3. validate provider source and build accepted Terraform decisions;
4. reject observability/E-001, unrelated Terraform IDs, Quantum caller prose, and the unrelated provider option with generic no-echo failures;
5. render ES/EN v2 and assert public labels/recurrence/ordinals are visible while IDs/snapshots/URLs/prose are absent;
6. render legacy no-market and compare pinned byte/SHA snapshots;
7. run installed package discovery and static package checks with zero cache mutation.

- [ ] **Step 8: Write honest attestation**

Update `tests/evals/final/installed-smoke-test.md` with source commit/tree, exact installed version, file count, normalized digest, zero-bytecode counts, source/cache parity, source/package/static/release results, accepted and rejected semantic smoke counts, v1 snapshot result, privacy/no-echo result, and design evidence scope. Do not claim repository-only conformance from the cache or visual/browser/assistive-technology QA that was not run.

- [ ] **Step 9: Commit attestation and verify the release commit**

```bash
git add tests/evals/final/installed-smoke-test.md docs/release-validation.md
git commit -m "docs: attest semantic provenance v2 release"
PYTHONDONTWRITEBYTECODE=1 python3 -B scripts/run_release_validation.py
git status --short
```

Expected: release validation exits 0 and status is clean. If `docs/release-validation.md` did not require a change, omit it from `git add`.

- [ ] **Step 10: Push and independently verify remote main**

Push the reviewed HEAD to `main`, fetch the remote reference, and require local HEAD, local `origin/main`, and `git ls-remote origin refs/heads/main` to resolve to the same commit. If live network verification is unavailable, report that constraint and do not claim a new live remote check.

- [ ] **Step 11: Final handoff**

Report the exact commit, plugin version, installed cache result, source/cache parity, test/check totals, accepted/rejected semantic smokes, v1 compatibility, privacy/no-echo result, and explicitly deferred items. State that this release proves structured provenance consistency, not real-world truth or employment outcomes.
