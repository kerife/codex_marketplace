# Canonical Marketplace Dossier V2 Consolidation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `codex_marketplace` the only active source and installation of Professional Growth Coach by reconciling the defensive controls from both repositories, porting the completed dossier-v2 experience, publishing one canonical release, and disabling the duplicate legacy selector without deleting recoverable history.

**Architecture:** Work only on the sanitized `codex_marketplace` history. Treat `job_search_coach@5feef6a` as a read-only source inventory and port behavior through tests-first, file-by-file reconciliation; never merge unrelated histories or replace the target tree. Preserve the marketplace catalog/public docs and combine both security-control sets before composing dossier v2 through the existing v1 validator and renderer. Release once after the whole-branch review, then remove only the legacy selector and marketplace configuration while retaining private bundles and the unpublished five-vacancy branch for the next canonical increment.

**Tech Stack:** Python 3.11 and 3.14, standard library only, JSON Schema 2020-12 dependency-free subset, `unittest`, offline HTML/CSS, Superdesign byte-parity contracts, Codex plugin marketplace/release tooling, Git worktrees and bundles.

## Global Constraints

- Canonical repository, remote, catalog, and publication branch remain `codex_marketplace`, its existing `origin`, `.agents/plugins/marketplace.json`, and `main`.
- The only installed selector after release is `professional-growth-coach@codex-marketplace-public`.
- Never merge with `--allow-unrelated-histories`, add the development repository as a public ref, or perform a root-tree overlay.
- Preserve `LICENSE`, public README/install guidance, marketplace identity, and all marketplace-only security controls.
- Treat `job_search_coach@5feef6a` and `codex/five-vacancy-market-dossier@269bbd7` as read-only migration sources. Do not change their code, manifests, provenance, refs, or remotes in this increment.
- Preserve local marketplace commit `0a05045` as a recoverable ref but do not cherry-pick it in this increment; its three-vacancy analytics examples are reviewed only in the follow-on five-vacancy plan.
- Preserve the five-vacancy branch in a verified private bundle; do not port or publish it until the follow-on plan completes its independent review.
- Exclude `.git`, `.release-validation-venv`, `.worktrees`, `.superpowers`, `.superdesign/tmp`, `__pycache__`, installed caches, generated HTML, private reports, local configuration, and old attestations from content migration.
- Preserve both depth and evaluation budgets, both regex length and complexity defenses, descriptor/no-follow input boundaries, fixed non-echo diagnostics, and fail-closed privacy behavior.
- Dossier v2 remains identity-free, private, offline, noninteractive, and evidence-bound. It exposes no session identifier, reusable authorization, candidate identity/contact, raw analytics, internal IDs, source snapshots, or local paths.
- Dossier v1 input, rendering, CLI behavior, fixtures, and practice-handoff semantics remain valid and byte-stable unless a focused regression test explicitly requires a shared security correction.
- Dossier v2 includes exactly 17 ordered section-ledger rows and three contextual coach-priority cards; its market area remains one bounded `market_evidence_unavailable` state in this increment.
- No LinkedIn modification, vacancy application, recruiter outreach, enrollment, message, connection, external action, remote asset, CDN, JavaScript chart, SVG, or canvas.
- Write a failing regression test and observe the intended RED result before every production behavior change.
- Each task ends in a scoped commit and independent spec/quality review. Critical or Important findings enter the SDD fix loop before the next task.
- Do not refresh deterministic provenance or consume the cachebuster until all functional gates and the whole-branch review are green.
- Invoke the official cachebuster exactly once for this release. If plugin files change afterward, the installation evidence is invalid and the release sequence must restart with a new reviewed version.
- Static contracts are not empirical browser or assistive-technology evidence. Report real browser/AT QA separately.

---

### Task 1: Preserve migration sources and reconcile the defensive baseline

**Files:**
- Modify: `plugins/professional-growth-coach/scripts/validate_json_schema_subset.py`
- Modify: `plugins/professional-growth-coach/scripts/private_prose_safety.py`
- Modify: `plugins/professional-growth-coach/scripts/validate_executive_career_dossier.py`
- Modify: `plugins/professional-growth-coach/scripts/validate_private_recruiter_conversion_outcome.py`
- Modify: `plugins/professional-growth-coach/scripts/validate_private_recruiter_followthrough_checkpoint.py`
- Modify: `plugins/professional-growth-coach/scripts/validate_private_recruiter_reply_triage.py`
- Modify: `plugins/professional-growth-coach/scripts/validate_recruiter_practice_session.py`
- Modify only if a failing union test requires it: `plugins/professional-growth-coach/scripts/validate_linkedin_client_report.py`
- Modify: `plugins/professional-growth-coach/scripts/dossier_practice_safe_text.py`
- Modify: `plugins/professional-growth-coach/scripts/summarize_outcomes.py`
- Modify: `plugins/professional-growth-coach/tests/test_private_schema_conformance.py`
- Modify: `plugins/professional-growth-coach/tests/test_private_prose_safety.py`
- Modify: `plugins/professional-growth-coach/tests/test_private_input_descriptor_boundary.py`
- Modify: `plugins/professional-growth-coach/tests/test_dossier_recruiter_practice_handoff.py`
- Modify: `tests/test_linkedin_client_report.py`
- Modify: `tests/test_linkedin_report_fixtures.py`
- Modify: `tests/test_executive_career_dossier.py`
- Modify: `tests/test_validate_case.py`
- Modify: `tests/test_summarize_outcomes.py`
- Modify: `tests/test_professional_growth_contract.py`

**Interfaces:**
- Produces: a dependency-free `validate_schema_instance(value, schema) -> list[str]` that enforces both `MAX_SCHEMA_VALIDATION_DEPTH=64` and `MAX_SCHEMA_EVALUATIONS=4096` across one shared traversal budget.
- Produces: deterministic schema errors for invalid branches, keyword shapes, references, patterns, depth, evaluation exhaustion, and cyclic JSON values without traceback or untrusted-value echo.
- Preserves: `private_input_loader.read_bounded_bytes(path, max_bytes) -> bytes` with marketplace `ValueError`, `ENOTDIR`, parent-symlink, leaf-symlink, descriptor, FIFO, hardlink, and size handling.
- Produces: JSON loaders that convert CPython decoder `RecursionError` into their existing fixed invalid-input errors before CLI traceback escape.
- Produces: fixed/non-echo diagnostic behavior for priority codes, parser headings, duplicate references, source IDs/categories, path-like keys, case fields, and outcome scalar/intervention warnings.

- [ ] **Step 1: Record and verify private recovery bundles**

Run from outside both repositories with escalated write permission for their Git directories:

```bash
mkdir -p /Users/kevinriosferrer/projects/job_search_coach/.git/backups/2026-08-13
git -C /Users/kevinriosferrer/projects/job_search_coach bundle create \
  .git/backups/2026-08-13/job-search-coach-all.bundle --all
git -C /Users/kevinriosferrer/projects/job_search_coach bundle verify \
  .git/backups/2026-08-13/job-search-coach-all.bundle

mkdir -p /Users/kevinriosferrer/projects/codex_marketplace/.git/backups/2026-08-13
git -C /Users/kevinriosferrer/projects/codex_marketplace bundle create \
  .git/backups/2026-08-13/private-history-backup.bundle private-history-backup
git -C /Users/kevinriosferrer/projects/codex_marketplace bundle verify \
  .git/backups/2026-08-13/private-history-backup.bundle
```

Record the verified tips `job_search_coach/main=5feef6a`,
`codex/five-vacancy-market-dossier=269bbd7`, and
`codex_marketplace/origin/main=f6c9501` in this plan's ignored SDD report.
Do not add bundle paths to Git.

- [ ] **Step 2: Capture the two existing root-contract RED failures**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest \
  tests.test_linkedin_client_report.LinkedInClientReportDecisionTests.test_untrusted_priority_code_and_heading_escape_controls \
  tests.test_linkedin_report_fixtures.LinkedInReportFixtureTests.test_load_bundle_rejects_intermediate_parent_symlink \
  -v
```

Expected RED:

- the priority test expects an escaped submitted value while production returns
  only `generic priority code is not allowed`;
- the symlink test expects `unavailable` while production deliberately returns
  `fixture bundle input must not be a symlink`.

- [ ] **Step 3: Align the stale tests with the safer existing behavior**

Replace the priority assertion with this contract:

```python
priority_errors = validator.validate_client_report(priority_mutant, bundle)
rendered = "\n".join(priority_errors)
self.assertIn("generic priority code is not allowed", priority_errors)
self.assertNotIn("Profile", rendered)
self.assertNotIn("\x1b", rendered)
```

Change the intermediate-parent symlink expectation to the exact word
`symlink`; keep assertions that neither the target path nor fixture material is
echoed. Do not change production for either baseline mismatch.

- [ ] **Step 4: Verify the baseline contracts are GREEN**

Run the command from Step 2 again. Expected: two tests pass.

- [ ] **Step 5: Add the schema-union RED matrix**

Port and adapt these exact test methods from the development source into the
marketplace test without removing the marketplace depth/long-pattern tests:

```python
test_dependency_free_checker_bounds_nested_combinator_evaluations
test_dependency_free_checker_bounds_cyclic_schema_references
test_dependency_free_checker_rejects_missing_schema_references
test_dependency_free_checker_rejects_non_object_combinator_branches
test_dependency_free_checker_rejects_malformed_keyword_shapes
test_dependency_free_checker_rejects_invalid_regex_patterns
test_dependency_free_checker_rejects_nested_unbounded_regex
test_dependency_free_checker_rejects_cyclic_json_values_without_recursion_error
```

Add a union assertion that a schema deeper than 64 levels returns the existing
depth error even when the evaluation budget remains, and a broad combinator
tree returns the evaluation-limit error before unbounded work.

- [ ] **Step 6: Observe schema RED**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest \
  plugins/professional-growth-coach/tests/test_private_schema_conformance.py \
  -v
```

Expected: only the newly ported branch-shape, malformed-keyword, evaluation,
missing-ref, and cyclic-value cases fail; existing marketplace depth, regex
length/complexity, and diagnostic-redaction cases remain green.

- [ ] **Step 7: Implement the schema-control union**

Keep these marketplace constants and add the development evaluation constant:

```python
MAX_SCHEMA_VALIDATION_DEPTH = 64
MAX_SCHEMA_EVALUATIONS = 4_096
MAX_SCHEMA_PATTERN_LENGTH = 1_024
```

Make `_validate` receive both `_depth: int` and `budget: list[int]`, decrement
the same budget for every `$ref`, items, contains, allOf, oneOf, anyOf, not,
if/then/else traversal, and retain an `active_ref_targets: set[int]` cycle
guard. Add `_keyword_shapes_valid`, `_pattern_error`, missing/invalid `$ref`
normalization, non-object branch rejection, and cycle-safe `_json_equal`.
Preserve `safe_diagnostic_field_name` and the marketplace's broad nested-
quantifier and pattern-length guards.

- [ ] **Step 8: Verify schema GREEN**

Run the Step 6 command. Expected: all schema conformance tests pass with no
traceback and no raw sensitive/control-bearing field names.

- [ ] **Step 9: Add decoder-recursion RED tests without weakening descriptors**

Port the development fixture builders and matrices into
`test_private_input_descriptor_boundary.py`:

```python
_decoder_recursion_fixture
_expected_decoder_or_post_decode_messages
DIRECT_RECURSION_CASES
CLI_RECURSION_CASES
```

Assert every direct loader and CLI returns one of its existing fixed messages,
nonzero CLI status, one bounded stderr line, and no `Traceback`. Keep all
marketplace tests for NUL/`ValueError`, regular files, parent and leaf symlinks,
hardlinks, FIFO, descriptors, and size boundaries.

- [ ] **Step 10: Observe decoder-recursion RED on CPython 3.11**

```bash
PYTHONDONTWRITEBYTECODE=1 \
  /Users/kevinriosferrer/projects/codex_marketplace/.release-validation-venv/bin/python \
  -B -m unittest \
  plugins/professional-growth-coach/tests/test_private_input_descriptor_boundary.py \
  -v
```

Expected: the deep valid JSON fixture leaks `RecursionError` from one or more
loaders; existing descriptor cases remain green.

- [ ] **Step 11: Normalize decoder recursion in the five JSON loaders**

Add `RecursionError` only to the existing `json.loads` exception tuples in:

```text
validate_executive_career_dossier.load_dossier
validate_private_recruiter_conversion_outcome.load_outcome
validate_private_recruiter_followthrough_checkpoint._load_json
validate_private_recruiter_reply_triage.load_triage
validate_recruiter_practice_session.load_session
```

Do not replace `private_input_loader.py` with the development version.

- [ ] **Step 12: Verify the cross-version descriptor boundary**

Run the focused test with both interpreters:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest \
  plugins/professional-growth-coach/tests/test_private_input_descriptor_boundary.py -v

PYTHONDONTWRITEBYTECODE=1 \
  /Users/kevinriosferrer/projects/codex_marketplace/.release-validation-venv/bin/python \
  -B -m unittest \
  plugins/professional-growth-coach/tests/test_private_input_descriptor_boundary.py -v
```

- [ ] **Step 13: Add RED privacy/diagnostic union cases**

Port only missing cases from the development tests and assert API plus CLI
non-echo behavior for:

```python
sentinels = (
    "/etc/passwd",
    "/opt/data/profile.json",
    r"D:\\work\\candidate\\profile.json",
    r"\\\\server\\share\\profile.json",
    "ordinary\x1b[31mINJECTED\nLINE",
)
```

Cover parser dimensions/headings, generic priority codes, duplicate
fact/evidence/claim references, source IDs/categories, case keys, dossier
unlabelled names with diacritics/particles, and outcome scalar/intervention
warnings. Preserve readable ordinary relative keys and safe synthetic IDs.

- [ ] **Step 14: Observe the focused privacy RED set**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest \
  tests.test_executive_career_dossier \
  tests.test_linkedin_client_report \
  tests.test_linkedin_report_fixtures \
  tests.test_validate_case \
  tests.test_summarize_outcomes \
  plugins/professional-growth-coach/tests/test_private_prose_safety.py \
  plugins/professional-growth-coach/tests/test_dossier_recruiter_practice_handoff.py \
  -v
```

Expected: missing development-only non-echo and identity cases fail; all
canonical controls continue passing.

- [ ] **Step 15: Implement the minimum diagnostic/privacy union**

Reconcile these exact functions and no broader module replacement:

```text
private_prose_safety.safe_diagnostic_field_name
dossier_practice_safe_text.has_unlabelled_person_intro
dossier_practice_safe_text.is_safe_handoff_text
validate_executive_career_dossier.candidate_text_privacy_errors
validate_linkedin_client_report._safe_diagnostic_field_name
validate_linkedin_client_report._safe_diagnostic_identifier
validate_linkedin_client_report._safe_source_category
validate_linkedin_client_report.parse_score_table
validate_linkedin_client_report.parse_copy_blocks
validate_linkedin_client_report._validate_report_priorities
validate_linkedin_client_report._validate_report_copies
validate_linkedin_client_report._validate_sources
validate_linkedin_client_report._scan_privacy
summarize_outcomes.parse_iso_date
summarize_outcomes.parse_boolean
summarize_outcomes.read_rows
summarize_outcomes.parse_window
summarize_outcomes.summarize
summarize_outcomes.main
```

Preserve the canonical generic priority diagnostic and parent-symlink
contract. Route untrusted labels through `safe_diagnostic_field_name`, IDs
through the closed identifier helper, categories through the category
allowlist, and arbitrary values through fixed `<redacted-value>` diagnostics.
The outcomes functions return generic invalid-value/warning messages without
the submitted intervention identifier. Do not introduce one-off copies of
redaction regexes.

- [ ] **Step 16: Verify Task 1 focused and neighboring suites**

Run Steps 8, 12 and 14, then:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover \
  -s plugins/professional-growth-coach/tests -p 'test_*.py' -v

PYTHONDONTWRITEBYTECODE=1 python3 -B scripts/check_repository_privacy.py \
  --repo-root .

git diff --check
```

The static checker may report only the twelve final-cycle `source_commit`
values made stale by the design commit. Any other failure blocks the commit.

- [ ] **Step 17: Make the locked-interpreter root test work from a linked worktree**

Add a test-first helper contract in `test_professional_growth_contract.py`:

```python
locked_python = Path(
    os.environ.get(
        "VALIDATION_PYTHON",
        REPO_ROOT / ".release-validation-venv" / "bin" / "python",
    )
)
```

Run the specific test with `VALIDATION_PYTHON` set to the canonical checkout's
pinned interpreter and require a clean import.

- [ ] **Step 18: Commit Task 1**

Stage only the allowlisted Task 1 files and commit:

```bash
git commit -m "fix: reconcile canonical privacy boundaries"
```

Do not stage deterministic provenance, plugin manifest, installation evidence,
or any file from the source repositories.

---

### Task 2: Port the closed dossier-v2 runtime by composition

**Files:**
- Create: `plugins/professional-growth-coach/schemas/executive-career-dossier-v2.schema.json`
- Create: `plugins/professional-growth-coach/scripts/executive_career_dossier_v2_compat.py`
- Create: `plugins/professional-growth-coach/scripts/validate_executive_career_dossier_v2.py`
- Create: `plugins/professional-growth-coach/scripts/render_executive_career_dossier_v2.py`
- Create: `plugins/professional-growth-coach/assets/executive-career-dossier-v2.css`
- Create: `tests/evals/with-skill/fixtures/executive-career-dossier-v2/scenario-a-es.json`
- Create: `tests/evals/with-skill/fixtures/executive-career-dossier-v2/scenario-c-en.json`
- Create: `tests/test_executive_career_dossier_v2.py`
- Modify: `plugins/professional-growth-coach/scripts/validate_executive_career_dossier.py`
- Modify: `plugins/professional-growth-coach/scripts/private_asset_loader.py`
- Modify: `plugins/professional-growth-coach/tests/test_private_asset_loader.py`
- Modify: `plugins/professional-growth-coach/tests/test_design_tokens.py`
- Modify: `plugins/professional-growth-coach/tests/test_private_schema_conformance.py`
- Modify: `tests/test_private_asset_boundary.py`
- Modify: `tests/test_dark_mode_accessibility.py`
- Modify: `tests/test_print_continuity_footer_integrity.py`
- Modify: `tests/test_superdesign_theme_asset_parity.py`
- Modify: `.superdesign/init/theme.md`

**Interfaces:**
- Produces: `CANONICAL_PROFILE_SECTIONS`, an ordered tuple of exactly 17 keys.
- Produces: `project_v2_to_v1(value: Mapping[str, object]) -> dict[str, object]`, returning a deep copy and never mutating the v2 input.
- Produces: v2 `validate_dossier(value: object) -> list[str]`, `load_dossier(path: Path) -> dict[str, object]`, `select_pending_inspection_section(value) -> str | None`, and CLI exit `0|2`.
- Produces: v2 `render_dossier_html`, `build_chat_summary`, `write_dossier_html`, and CLI by composing the validated v1 renderer/private writer.
- Preserves: exact v1 validation and render output for unchanged v1 fixtures.

- [ ] **Step 1: Add the v2 tests and fixtures before runtime files**

Port the reviewed ES and EN synthetic fixtures and
`tests/test_executive_career_dossier_v2.py` from `job_search_coach@5feef6a`.
Remove no assertions. The tests must require:

```python
EXPECTED_PROFILE_SECTIONS = (
    "photo", "banner", "name", "profile_url", "headline", "location",
    "contact_info", "about", "experience", "skills", "featured",
    "certifications", "education", "recommendations", "activity",
    "analytics", "job_preferences",
)
```

They also require three contextual priorities bound to `headline`, `about`,
and `experience`; same-section evidence; current-session-only pending/declined
decisions; private `0600` output; one pending authorization question; and no
positive authorization/session field.

- [ ] **Step 2: Observe dossier-v2 RED**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest \
  tests.test_executive_career_dossier_v2 -v
```

Expected: import/file failures for the absent v2 validator, renderer, schema,
CSS and compatibility module.

- [ ] **Step 3: Implement the pure v2-to-v1 projection**

Create `executive_career_dossier_v2_compat.py` with the exact ordered section
tuple and a deep-copy projection. The projection removes only v2 ledger,
inspection-request and contextual-coaching fields, rebuilding the v1 priority
shape without changing source evidence, scorecards, market context, or locale.

Add a mutation test proving the projected object and original v2 object do not
share nested dictionaries or lists.

Use this public shape:

```python
CANONICAL_PROFILE_SECTIONS: tuple[str, ...] = EXPECTED_PROFILE_SECTIONS

def project_v2_to_v1(value: Mapping[str, object]) -> dict[str, object]:
    projected = copy.deepcopy(dict(value))
    projected["schema_version"] = "executive-career-dossier-v1"
    projected.pop("section_coverage", None)
    for evidence in projected.get("evidence", []):
        if isinstance(evidence, dict):
            evidence.pop("profile_section", None)
    for priority in projected.get("priorities", []):
        if isinstance(priority, dict):
            for key in (
                "target_section", "coach_observation", "why_it_matters",
                "coach_prompt", "client_template", "privacy_boundary",
            ):
                priority.pop(key, None)
    return projected
```

The test must compare the result deeply to the shipped source-v1 dossier, not
only validate its schema.

- [ ] **Step 4: Create the closed v2 schema and semantic validator**

Port the reviewed schema and validator behavior, not source metadata. The
semantic validator must:

- invoke Task 1's dependency-free schema checker;
- validate the pure v1 projection with the canonical v1 validator;
- require the exact 17-row order and closed row/request state matrix;
- bind present/candidate-reported rows and priorities to same-section evidence;
- apply v1 external-action, live-state, employment-continuity, analytics and
  market-evidence guards to every v2 coaching field;
- use fixed non-echo diagnostics;
- enforce duplicate-key, depth 12, 256 KiB, FIFO, symlink, hardlink, invalid
  UTF-8 and decoder-recursion boundaries.

- [ ] **Step 5: Implement the v2 renderer by v1 composition**

Use the existing v1 renderer/template/private writer. Add only:

- one semantic localized 17-row coverage ledger;
- three localized coach cards with closed blank templates;
- one bounded `market_evidence_unavailable` surface;
- one localized summary question for the first pending section;
- the v2 stylesheet loaded through the private asset loader.

Do not render internal IDs, source snapshots, enum values, request/session
fields, identity/contact values, raw analytics, or URLs.

- [ ] **Step 6: Port the v2 CSS and asset contracts**

Invoke `superdesign:superdesign` before editing the visible surface. Run the
required bare CLI preflight:

```bash
npx --yes @superdesign/cli@latest
```

Read all six non-empty canonical init files (`components.md`, `layouts.md`,
`routes.md`, `theme.md`, `pages.md`, `extractable-components.md`) and the
existing product design system. Treat the reviewed source v2 artifact as the
visual target: reproduce its existing structure first and preserve canonical
tokens rather than inventing a new palette, typography, card system or layout.
Use the Superdesign canvas for the comparison/audit and record its generated
canvas and preview references in the ignored Task 2 report, never in product
fixtures or public diagnostics.

Add the v2 CSS to `private_asset_loader.py`'s exact allowlist and append its
byte-exact dump to `.superdesign/init/theme.md`. Add RED/GREEN tests for:

- token-only colors and spacing;
- 480px one-column ledger without a horizontal-scroll-only primitive;
- dark, forced-colors, reduced-motion and preferred-contrast modes;
- print page margins and atomic cards/rows;
- one skip link, one `main`, one H1, unique IDs and resolved ARIA references.

- [ ] **Step 7: Verify dossier-v2 GREEN and v1 preservation**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest \
  tests.test_executive_career_dossier_v2 \
  tests.test_executive_career_dossier \
  tests.test_private_asset_boundary \
  tests.test_dark_mode_accessibility \
  tests.test_print_continuity_footer_integrity \
  tests.test_superdesign_theme_asset_parity \
  plugins/professional-growth-coach/tests/test_private_asset_loader.py \
  plugins/professional-growth-coach/tests/test_design_tokens.py \
  plugins/professional-growth-coach/tests/test_private_schema_conformance.py \
  -v
```

Capture the v1 fixture render hashes before and after Task 2 and require exact
equality for each unchanged v1 fixture.

- [ ] **Step 8: Commit Task 2**

```bash
git commit -m "feat: add canonical dossier v2 runtime"
```

Stage only Task 2 runtime, fixtures, tests and theme dump. Do not port the
development manifest, final provenance, installed smoke, five-vacancy assets,
or `.superdesign/design-system.md`.

---

### Task 3: Route, scan and document dossier v2 as the canonical profile output

**Files:**
- Modify: `plugins/professional-growth-coach/scripts/build_dossier_recruiter_practice_handoff.py`
- Modify: `plugins/professional-growth-coach/scripts/validate_dossier_recruiter_practice_handoff.py`
- Modify: `plugins/professional-growth-coach/tests/test_dossier_recruiter_practice_handoff.py`
- Modify: `scripts/check_repository_privacy.py`
- Modify: `tests/test_repository_privacy.py`
- Modify: `plugins/professional-growth-coach/tests/run_static_checks.py`
- Modify: `tests/test_full_plugin.py`
- Modify: `tests/test_plugin_structure.py`
- Modify: `tests/test_skill_contracts.py`
- Modify: `plugins/professional-growth-coach/README.md`
- Modify: `plugins/professional-growth-coach/skills/optimize-professional-profile/SKILL.md`
- Modify: `plugins/professional-growth-coach/skills/optimize-professional-profile/references/html-dossier.md`
- Modify: `plugins/professional-growth-coach/skills/optimize-professional-profile/references/profile-audit.md`
- Modify only if source bindings require it: `tests/evals/final/executive-career-dossier-pressure-summary.json`

**Interfaces:**
- The normal local profile-audit branch validates and renders dossier v2.
- Dossier-practice handoff accepts v2 only after v2 validation, projects to v1
  for established semantics, and binds the snapshot to the original v2 object.
- Repository privacy validates a bounded v2 object, scans its pure v1
  projection, and conservatively scans malformed v2 without granting an
  allowance.
- Package/static inventory contains exactly the new schema, scripts, CSS and
  tests while preserving public marketplace identity.

- [ ] **Step 1: Add RED handoff, privacy, routing and package tests**

Require:

```python
assert validate_v2_dossier(v2_fixture) == []
assert build_handoff(v2_fixture)["source_snapshot"] == snapshot_for_dossier(v2_fixture)
assert build_handoff(mutated_v2_fixture) raises dossier_validation_failed
```

Add repository privacy tests for:

- valid shipped v2 fixtures accepted through real validation/projection;
- malformed ledger/request status scanned conservatively;
- candidate identity, contact, local path, raw analytics and action text in v2
  coaching fields rejected without echo;
- missing validator/projector fails closed.

Add skill/static tests that the normal local route names v2, asks at most one
pending authorization question, and keeps v1 only for compatibility/debug
paths.

- [ ] **Step 2: Observe integration RED**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest \
  plugins/professional-growth-coach/tests/test_dossier_recruiter_practice_handoff.py \
  tests.test_repository_privacy \
  tests.test_skill_contracts \
  tests.test_plugin_structure \
  tests.test_full_plugin \
  -v
```

Expected: v2 routing, package inventory, handoff snapshot and privacy projection
cases fail while Task 2's direct validator/renderer tests remain green.

- [ ] **Step 3: Implement v2-aware handoff without changing v1 semantics**

Dispatch based on exact `schema_version`. Validate v2 first; project a deep
copy to v1 for the existing handoff field selection; compute and validate the
source snapshot from the original v2 object. Any post-snapshot change to a
ledger row, priority, evidence `profile_section` or coaching field must fail.

- [ ] **Step 4: Implement fail-closed repository privacy projection**

Add a bounded contract loader for v2. When structural and semantic validation
both succeed, scan the pure v1 projection plus the explicitly allowed closed
v2 statuses. When imports, validation, projection or status checks fail, scan
the entire value conservatively. No exception may turn malformed input into an
allowance.

- [ ] **Step 5: Update package/static inventory and public skill routing**

Read `skill-creator` and `superpowers:writing-skills` before editing the skill.
Use v2 for the normal local dossier route, retain v1 compatibility, preserve
the public selector `codex-marketplace-public`, and document the one-question
inspection ledger without promising current market research.

Regenerate only the deterministic dossier pressure source bindings affected by
the routed docs. Bind them to the Task 3 functional commit; do not touch cycle
provenance or installed-smoke metadata.

- [ ] **Step 6: Verify Task 3 integration**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest \
  tests.test_executive_career_dossier_v2 \
  plugins/professional-growth-coach/tests/test_dossier_recruiter_practice_handoff.py \
  tests.test_repository_privacy \
  tests.test_skill_contracts \
  tests.test_plugin_structure \
  tests.test_full_plugin \
  -v

PYTHONDONTWRITEBYTECODE=1 python3 -B scripts/check_repository_privacy.py \
  --repo-root .

VALIDATION_PYTHON=/Users/kevinriosferrer/projects/codex_marketplace/.release-validation-venv/bin/python \
  scripts/run_release_validation.sh

git diff --check
```

The static wrapper may fail only for the twelve deferred cycle provenance
values. Any runtime, privacy, package, route or pressure-binding failure blocks
the commit.

- [ ] **Step 7: Commit Task 3**

```bash
git commit -m "feat: route canonical profile audits to dossier v2"
```

---

### Task 4: Whole-branch review and canonical release attestation

**Files:**
- Modify once via official helper: `plugins/professional-growth-coach/.codex-plugin/plugin.json`
- Modify mechanically: `tests/evals/final/cycle-1/*.json`
- Modify mechanically: `tests/evals/final/cycle-2/*.json`
- Modify mechanically: `tests/evals/final/cycle-1.md`
- Modify mechanically: `tests/evals/final/cycle-2.md`
- Modify mechanically: `tests/evals/final/installed-smoke-test.md`
- Modify if currentness requires it: `tests/evals/final/executive-career-dossier-pressure-summary.json`
- Modify if currentness requires it: `tests/evals/final/linkedin-client-report-v2-pressure-summary.json`

**Interfaces:**
- Produces one reviewed canonical functional HEAD, one cachebuster commit, one
  attestation commit, one installed canonical version, and exact source/cache
  parity evidence.
- Produces final-cycle provenance whose `source_commit` is the cachebuster
  commit or its functional parent according to the established validator, and
  whose `source_tree` resolves in the canonical repository.
- Does not copy any development source hash, timestamp, cache path, count or
  installed-smoke statement.

- [ ] **Step 1: Run a broad whole-branch review before release metadata**

Generate an SDD review package from `f6c9501` through Task 3 HEAD. Dispatch the
most capable reviewer with the approved design, this plan, the package and the
ledger. Resolve every Critical/Important finding through one reviewed fix wave
before proceeding.

- [ ] **Step 2: Run all pre-cachebuster gates**

Run in a writable checkout with the pinned Python path exported:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover \
  -s plugins/professional-growth-coach/tests -p 'test_*.py' -q

PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover \
  -s tests -p 'test_*.py' -q

PYTHONDONTWRITEBYTECODE=1 \
  /Users/kevinriosferrer/projects/codex_marketplace/.release-validation-venv/bin/python \
  -B -m unittest tests.test_executive_career_dossier_v2 -q

PYTHONDONTWRITEBYTECODE=1 python3 -B \
  plugins/professional-growth-coach/tests/run_static_checks.py

PYTHONDONTWRITEBYTECODE=1 python3 -B scripts/check_repository_privacy.py \
  --repo-root .

VALIDATION_PYTHON=/Users/kevinriosferrer/projects/codex_marketplace/.release-validation-venv/bin/python \
  scripts/run_release_validation.sh

git diff --check
```

Generate the complete tracked-file inventory and the newly public diff for the
reviewer without printing ignored artifacts:

```bash
git ls-files -z > /private/tmp/canonical-marketplace-tracked-files.zlist
git diff --name-status -z f6c9501..HEAD \
  > /private/tmp/canonical-marketplace-public-diff.zlist
```

The privacy reviewer must open every newly added tracked file and every changed
public fixture/document, confirm the exclusion list, and record a zero-finding
public-release verdict in the ignored Task 4 report. The repository privacy
checker remains mandatory but does not replace this inventory review.

Before the cachebuster, the only permitted nonzero assertions are the twelve
cycle provenance values. Rebind them to Task 3 HEAD/tree, rerun the full root
and static suites, and require every command to exit zero before continuing.

- [ ] **Step 3: Commit the functional provenance rebind**

Commit only deterministic pressure/cycle provenance required to make the
functional tree current:

```bash
git commit -m "test: bind canonical dossier v2 provenance"
```

Rerun Step 2 and require complete success.

- [ ] **Step 4: Invoke the official cachebuster exactly once**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B \
  /Users/kevinriosferrer/.codex/skills/.system/plugin-creator/scripts/update_plugin_cachebuster.py \
  plugins/professional-growth-coach
```

Verify the diff changes only `.codex-plugin/plugin.json`, preserves base
version `0.2.0`, and creates a unique `0.2.0+codex.<timestamp>` value. Commit:

```bash
git commit -m "chore: bump canonical dossier v2 release"
```

- [ ] **Step 5: Install the exact canonical version**

Refresh the configured public marketplace and install only its selector:

```bash
codex plugin marketplace upgrade codex-marketplace-public --json
codex plugin add professional-growth-coach@codex-marketplace-public --json
codex plugin list --json
```

If the Git marketplace cannot observe an unpublished branch, publish the
reviewed commits first after obtaining the required default-branch mutation
approval, verify the remote hash, then run these commands. Never repoint the
public marketplace at `job_search_coach` or a temporary worktree.

- [ ] **Step 6: Prove source/cache parity and installed behavior**

Resolve the installed cache path from `codex plugin list --json`. Compare:

```bash
diff -qr --exclude='__pycache__' \
  plugins/professional-growth-coach \
  /absolute/cache/path/from-plugin-list
```

Require identical relative file inventory, equal filtered file counts, equal
normalized path-plus-file-SHA256 digest, and an enabled version exactly equal
to the manifest. Run installed validator/renderer smokes for both v2 fixtures,
v1 compatibility, private writes, and no external action.

- [ ] **Step 7: Create and commit the installation attestation**

Update all final-cycle JSON/index values and
`installed-smoke-test.md` with the measured canonical version, cache path
identity, access timestamp, canonical source commit/tree, file counts, digest,
and exact smoke outcomes. Do not use expressions or placeholders.

Commit:

```bash
git commit -m "test: attest canonical dossier v2 installation"
```

- [ ] **Step 8: Run every post-attestation gate fresh**

Repeat every command from Step 2, the official validator against source and
installed cache, source/cache diff/count/hash, installed v1/v2 smokes, privacy
scan of every newly tracked public file, `git diff --check`, and clean status.
All must exit zero.

---

### Task 5: Publish the canonical increment and remove duplicate resolution

**Files:**
- External state: `codex_marketplace` remote `main`
- External state: Codex plugin and marketplace configuration
- External state: linked worktrees owned by `job_search_coach`
- Evidence only: this plan's ignored SDD report and ledger

**Interfaces:**
- Produces: remote `codex_marketplace/main` at the verified attestation HEAD.
- Produces: exactly one installed/enabled Professional Growth Coach selector,
  `professional-growth-coach@codex-marketplace-public`.
- Preserves: verified Git bundles, `job_search_coach` source/history and the
  five-vacancy branch for the next canonical port.

- [ ] **Step 1: Publish and independently verify the canonical remote**

Push the reviewed branch through the repository's accepted main workflow.
Then verify with both the local tracking ref and an independent remote query
that `origin/main` equals the attestation HEAD. Do not claim publication from a
local tracking ref alone.

- [ ] **Step 2: Back up Codex configuration and remove only the legacy selector**

Create a timestamped mode-`0600` backup without printing its contents. Then:

```bash
codex plugin remove \
  professional-growth-coach@professional-growth-coach-local --json
codex plugin list --json
```

Require the public selector to remain enabled at the attested version before
removing the legacy marketplace.

- [ ] **Step 3: Remove the legacy marketplace and stale trust entry**

```bash
codex plugin marketplace remove professional-growth-coach-local --json
codex plugin marketplace list --json
```

Remove only the exact legacy project trust stanza from active TOML, validate
the TOML parser, and confirm no active marketplace/plugin/source string points
to `job_search_coach`. Do not delete caches manually.

- [ ] **Step 4: Verify single identity in a genuinely fresh Codex process**

Start a new Codex CLI process with no inherited task context. Require:

- only `professional-growth-coach@codex-marketplace-public` is discoverable;
- the version equals the attested manifest;
- dossier-v2 validation/rendering is available;
- v1 compatibility still works;
- no skill root resolves from the legacy cache/source.

If a fresh process cannot be started safely, leave decommission verification
explicitly incomplete and ask the user to open one new task; do not infer
success from the current task's already-loaded skill list.

- [ ] **Step 5: Freeze but do not archive/delete the development repository**

Verify both linked worktrees and their refs are present in the bundle. Remove
only clean linked worktree registrations that are no longer running; keep the
repository, bundle and unpublished five-vacancy branch recoverable. Add no new
product/release commits to `job_search_coach`.

Do not archive the public GitHub repository yet. Archival belongs to the
follow-on five-vacancy canonical release, after the last unpublished branch is
ported and independently verified.

- [ ] **Step 6: Close the ledger and immediately open the follow-on plan**

Record remote hash, canonical selector/version, cache parity, config backup,
fresh-process evidence, preserved bundle refs and remaining unported branch.
Then create the separate canonical five-vacancy migration plan using the
approved design and `codex/five-vacancy-market-dossier@269bbd7` only as a
read-only source. Do not resume feature development in `job_search_coach`.

---

## Plan Self-Review Checklist

- [ ] Every approved consolidation requirement maps to a task or to the
  explicitly named follow-on five-vacancy plan.
- [ ] No step makes development Git history reachable from the public repo.
- [ ] No step copies a whole divergent validator, loader, test tree or root.
- [ ] The schema checker retains both depth and evaluation budgets and both
  regex defenses.
- [ ] Dossier v2 positive privacy allowance cannot exist before real validation
  and projection are installed.
- [ ] V1 preservation has direct behavioral and byte-level evidence.
- [ ] Provenance is regenerated only from canonical commits and measured cache
  state.
- [ ] Release/install/configuration mutations occur only after fresh full gates
  and independent review.
- [ ] The legacy selector is removed only after canonical installed smokes pass.
- [ ] The five-vacancy branch is bundled and retained for the next increment.
