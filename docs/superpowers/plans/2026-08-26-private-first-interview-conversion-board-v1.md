# Private First-Interview Conversion Board v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and publish a source-bound, private, offline JSON/HTML board that turns the existing first-interview seven-day text contract into a safe human-review surface.

**Architecture:** Add a closed schema, source-group builder, recomputing validator, exact proof-object identity, private atomic writer, and renderer. The renderer projects only bounded localized copy into a practice/triage-token HTML surface; it never accepts caller-authored final rows or performs external actions.

**Tech Stack:** Python 3.11, JSON Schema draft 2020-12, `unittest`, descriptor-anchored private file helpers, self-contained HTML/CSS, existing plugin static/privacy/release runners.

**Spec:** `docs/superpowers/specs/2026-08-26-private-first-interview-conversion-board-v1-design.md`

## Global Constraints

- Exact output cardinalities are 1 decision, 7 days, 4 branches, and 7 daily review templates.
- Every output is `draft_only=true`, `external_actions_authorized=false`, `no_message_action=true`, and `no_calendar_action=true`.
- The renderer accepts only the exact validator-issued proof-object class and emits no IDs, snapshots, URLs, recruiter text, PII, secrets, scripts, forms, buttons, or external resources.
- Invalid, crossed, stale, mutated, oversized, cyclic, duplicate, caller-authored, or unsafe inputs fail before template/CSS reads and leave no partial output.
- Existing textual networking, recruiter-triage, packet-routing, and prepare-role-interviews contracts remain unchanged.
- Browser, print-preview, and assistive-technology QA are not claimed without direct runtime evidence.

---

### Task 1: Lock the schema and fixture contract

**Files:**
- Create: `plugins/professional-growth-coach/schemas/private-first-interview-conversion-board-v1.schema.json`
- Create: `plugins/professional-growth-coach/tests/fixtures/private-first-interview-conversion-board-v1/accepted-es.json`
- Create: `plugins/professional-growth-coach/tests/fixtures/private-first-interview-conversion-board-v1/accepted-en.json`
- Create: `plugins/professional-growth-coach/tests/test_private_first_interview_conversion_board_v1.py`

**Interfaces:**
- Produces the canonical JSON field names and closed enums consumed by identity, builder, validator, renderer, and later release checks.
- Accepted fixtures contain one source group with seven unique day rows, four unique branches, seven unique review rows, and fixed private booleans.

- [ ] **Step 1: Write failing schema/fixture tests**

  Add tests that load both fixtures, require schema version `private-first-interview-conversion-board-v1`, assert exact 1/7/4/7 cardinalities, and reject a missing section, duplicate day, extra branch, or changed private boolean.

- [ ] **Step 2: Run the focused tests and verify the expected failure**

  Run:

  ```bash
  PYTHONDONTWRITEBYTECODE=1 .release-validation-venv/bin/python -B -m unittest plugins.professional-growth-coach.tests.test_private_first_interview_conversion_board_v1
  ```

  Expected: FAIL because the schema, fixtures, and test module do not yet exist.

- [ ] **Step 3: Add the closed schema and synthetic ES/EN fixtures**

  Use `additionalProperties: false`, bounded text limits, explicit enums, stable source snapshot patterns, and public projection fields. Keep all fixture values synthetic and identity-free.

- [ ] **Step 4: Run the focused tests and verify they pass**

  Run the command from Step 2. Expected: all schema/cardinality tests pass and no fixture contains a real identity, URL, or raw recruiter text.

- [ ] **Step 5: Commit the contract**

  ```bash
  git add plugins/professional-growth-coach/schemas/private-first-interview-conversion-board-v1.schema.json plugins/professional-growth-coach/tests/fixtures/private-first-interview-conversion-board-v1 plugins/professional-growth-coach/tests/test_private_first_interview_conversion_board_v1.py
  git commit -m "feat: define private interview conversion board contract"
  ```

### Task 2: Build source identity and fail-closed validation

**Files:**
- Create: `plugins/professional-growth-coach/scripts/private_first_interview_conversion_board_identity.py`
- Create: `plugins/professional-growth-coach/scripts/validate_private_first_interview_conversion_board_v1.py`
- Modify: `plugins/professional-growth-coach/tests/test_private_first_interview_conversion_board_v1.py`

**Interfaces:**
- `ValidatedPrivateFirstInterviewConversionBoard` is an immutable validator-issued object containing the frozen source group and canonical public projection.
- `validate_private_first_interview_conversion_board_v1(source_group: object) -> ValidatedPrivateFirstInterviewConversionBoard` recomputes and compares the projection before returning.

- [ ] **Step 1: Write failing validation tests**

  Add tests for exact class identity, source crossing, changed source after validation, forged/duck-typed proof objects, duplicate keys, unsafe prose, PII/secret/URL/HTML/control-character input, send/calendar/fit/probability/guarantee language, and generic bounded diagnostics with no source echo.

- [ ] **Step 2: Run tests to verify the failures**

  ```bash
  PYTHONDONTWRITEBYTECODE=1 .release-validation-venv/bin/python -B -m unittest plugins.professional-growth-coach.tests.test_private_first_interview_conversion_board_v1
  ```

  Expected: FAIL because identity and validator modules are absent.

- [ ] **Step 3: Implement canonical identity and recomputing validator**

  Reuse `semantic_provenance_snapshot.py`, bounded snapshot helpers, and the existing private prose safety patterns. Validate source-group membership, cardinalities, states, closed booleans, and public projection. Do not retain raw recruiter/candidate prose in the projection.

- [ ] **Step 4: Run focused tests and verify all rejection cases pass**

  Use the command from Step 2. Expected: every accepted fixture validates; every mutation/crossing/unsafe case fails closed without echo.

- [ ] **Step 5: Commit identity and validation**

  ```bash
  git add plugins/professional-growth-coach/scripts/private_first_interview_conversion_board_identity.py plugins/professional-growth-coach/scripts/validate_private_first_interview_conversion_board_v1.py plugins/professional-growth-coach/tests/test_private_first_interview_conversion_board_v1.py
  git commit -m "feat: validate private interview conversion board snapshots"
  ```

### Task 3: Implement deterministic builder and private writer

**Files:**
- Create: `plugins/professional-growth-coach/scripts/build_private_first_interview_conversion_board_v1.py`
- Create: `plugins/professional-growth-coach/scripts/write_private_first_interview_conversion_board_v1.py`
- Modify: `plugins/professional-growth-coach/tests/test_private_first_interview_conversion_board_v1.py`

**Interfaces:**
- `build_private_first_interview_conversion_board_v1(source_group: object) -> ValidatedPrivateFirstInterviewConversionBoard` derives the same projection as the validator.
- `write_private_first_interview_conversion_board_v1(validated_board: object, output: Path, *, force: bool = False) -> WriteReceipt` writes only validated output with mode `0600`.

- [ ] **Step 1: Write failing builder/writer tests**

  Assert deterministic canonical output, stop-state suppression, no caller-authored final rows, private mode `0600`, refusal to overwrite without `force`, symlink/non-regular rejection, and no output after invalid input or a simulated write failure.

- [ ] **Step 2: Run tests and verify failure**

  ```bash
  PYTHONDONTWRITEBYTECODE=1 .release-validation-venv/bin/python -B -m unittest plugins.professional-growth-coach.tests.test_private_first_interview_conversion_board_v1
  ```

  Expected: FAIL because builder and writer modules are absent.

- [ ] **Step 3: Implement the smallest deterministic builder and atomic writer**

  Build only from the validator-approved source group. Reuse the learning-proof private writer shape, descriptor anchoring, exclusive temporary file, flush/fsync, and final mode check. Keep `local_save_mode=disabled` in the artifact contract; the writer is a deliberate local private-artifact boundary, not an automatic save.

- [ ] **Step 4: Run focused tests and verify pass**

  Expected: accepted fixtures produce byte-identical projections; all invalid and filesystem safety tests pass.

- [ ] **Step 5: Commit builder and writer**

  ```bash
  git add plugins/professional-growth-coach/scripts/build_private_first_interview_conversion_board_v1.py plugins/professional-growth-coach/scripts/write_private_first_interview_conversion_board_v1.py plugins/professional-growth-coach/tests/test_private_first_interview_conversion_board_v1.py
  git commit -m "feat: build and write private interview conversion boards"
  ```

### Task 4: Add the offline visual product

**Files:**
- Create: `plugins/professional-growth-coach/assets/private-first-interview-conversion-board-v1.html`
- Create: `plugins/professional-growth-coach/assets/private-first-interview-conversion-board-v1.css`
- Create: `plugins/professional-growth-coach/scripts/render_private_first_interview_conversion_board_v1.py`
- Create: `plugins/professional-growth-coach/tests/test_render_private_first_interview_conversion_board_v1.py`

**Interfaces:**
- `render_private_first_interview_conversion_board_v1(validated_board: object) -> str` accepts only `ValidatedPrivateFirstInterviewConversionBoard` from the same package identity.
- The template receives only closed labels and escaped projection values; it contains no runtime script or external resource.

- [ ] **Step 1: Write failing renderer/DOM/CSS tests**

  Assert one `h1`, skip link, focusable `main#main-content`, unique headings, decision-before-context order, four branches, seven days, seven review templates, visible boundary, CSP/noindex/no-referrer, no forms/buttons/scripts/URLs/IDs/snapshots, and responsive/print/dark/forced/reduced hooks. Assert stop suppresses detailed sections.

- [ ] **Step 2: Run tests and verify failure**

  ```bash
  PYTHONDONTWRITEBYTECODE=1 .release-validation-venv/bin/python -B -m unittest plugins.professional-growth-coach.tests.test_render_private_first_interview_conversion_board_v1
  ```

  Expected: FAIL because the renderer and assets are absent.

- [ ] **Step 3: Implement template, CSS, and renderer**

  Reuse `private_asset_loader.py`, the `practice_triage` palette, existing shell spacing, semantic lists/definition lists, and print boundary conventions. Render fixed localized copy for state and risk topics; escape every source-derived value.

- [ ] **Step 4: Run renderer tests and verify pass**

  Expected: ES/EN accepted fixtures render deterministic offline HTML and every structural/privacy/mode assertion passes.

- [ ] **Step 5: Commit the visual product**

  ```bash
  git add plugins/professional-growth-coach/assets/private-first-interview-conversion-board-v1.html plugins/professional-growth-coach/assets/private-first-interview-conversion-board-v1.css plugins/professional-growth-coach/scripts/render_private_first_interview_conversion_board_v1.py plugins/professional-growth-coach/tests/test_render_private_first_interview_conversion_board_v1.py
  git commit -m "feat: render private interview conversion board"
  ```

### Task 5: Integrate package contracts and documentation

**Files:**
- Modify: `plugins/professional-growth-coach/scripts/private_asset_loader.py`
- Modify: `plugins/professional-growth-coach/tests/run_static_checks.py`
- Modify: `scripts/check_repository_privacy.py`
- Modify: `plugins/professional-growth-coach/tests/test_plugin_structure.py`
- Modify: `plugins/professional-growth-coach/tests/test_superdesign_theme_asset_parity.py`
- Modify: `plugins/professional-growth-coach/README.md`
- Modify: `plugins/professional-growth-coach/skills/professional-growth-coach/references/routing.md`
- Modify: `.superdesign/design-system.md`, `.superdesign/init/layouts.md`, `.superdesign/init/pages.md`, `.superdesign/init/components.md`, `.superdesign/init/theme.md`

**Interfaces:**
- Package inventory includes every new schema/script/asset/test fixture.
- Static/privacy checks know the new artifact without changing historical contracts.
- Routing exposes the board only as an explicit private branch after recruiter triage and before manual interview preparation.

- [ ] **Step 1: Add failing inventory/docs/parity tests**

  Assert all new paths are present, the asset loader permits only package-local regular assets, Superdesign references name the board, and the token validator includes its CSS in `practice_triage`.

- [ ] **Step 2: Run package structure/static/privacy tests and verify failure**

  ```bash
  PYTHONDONTWRITEBYTECODE=1 .release-validation-venv/bin/python -B -m unittest plugins.professional-growth-coach.tests.test_plugin_structure plugins.professional-growth-coach.tests.test_superdesign_theme_asset_parity
  PYTHONDONTWRITEBYTECODE=1 .release-validation-venv/bin/python -B plugins/professional-growth-coach/tests/run_static_checks.py
  PYTHONDONTWRITEBYTECODE=1 .release-validation-venv/bin/python -B scripts/check_repository_privacy.py
  ```

  Expected: FAIL with missing inventory, docs, or asset-family coverage.

- [ ] **Step 3: Integrate the paths and documentation**

  Add the exact files to closed inventories and privacy surfaces, keep the textual contract unchanged, update routing and README copy, and document the layout/component/token family plus the explicit no-external-action boundary.

- [ ] **Step 4: Run the same tests and verify pass**

  Expected: structure, static, privacy, token, and Superdesign parity checks pass without historical byte drift.

- [ ] **Step 5: Commit integration and docs**

  ```bash
  git add plugins/professional-growth-coach scripts/check_repository_privacy.py .superdesign plugins/professional-growth-coach/README.md
  git commit -m "docs: integrate private interview conversion board"
  ```

### Task 6: Run release validation and publish the installed release

**Files:**
- Modify: `plugins/professional-growth-coach/.codex-plugin/plugin.json`
- Modify: `tests/evals/final/installed-smoke-test.md`

**Interfaces:**
- The manifest version uniquely identifies the published install.
- The attestation binds the exact source commit/tree, installed version, file inventory, and smoke counts.

- [ ] **Step 1: Run focused, package, static, privacy, and historical tests before versioning**

  ```bash
  PYTHONDONTWRITEBYTECODE=1 .release-validation-venv/bin/python -B -m unittest discover -s plugins/professional-growth-coach/tests -p 'test*.py' -q
  PYTHONDONTWRITEBYTECODE=1 .release-validation-venv/bin/python -B -m unittest tests.test_full_plugin.FullPluginIntegrationTests.test_checked_in_attestation_is_bound_to_immutable_git_archive_evidence
  ```

- [ ] **Step 2: Bump the plugin version and commit**

  Use a fresh `0.2.0+codex.YYYYMMDDHHMMSS` value, then:

  ```bash
  git add plugins/professional-growth-coach/.codex-plugin/plugin.json
  git commit -m "chore: attest private interview board release"
  ```

- [ ] **Step 3: Install and verify the exact Codex release**

  ```bash
  codex plugin add professional-growth-coach@codex-marketplace-public --json
  VERSION="$(python3 -c 'import json; print(json.load(open("plugins/professional-growth-coach/.codex-plugin/plugin.json"))["version"])' )"
  CACHE_ROOT="/Users/kevinriosferrer/.codex/plugins/cache/codex-marketplace-public/professional-growth-coach/$VERSION"
  PYTHONDONTWRITEBYTECODE=1 python3 -B scripts/verify_installed_plugin_release.py parity --source-root plugins/professional-growth-coach --cache-root "$CACHE_ROOT"
  PYTHONDONTWRITEBYTECODE=1 python3 -B scripts/run_installed_learning_eligibility_v3_smokes.py --plugin-root "$CACHE_ROOT" --source-archive plugins/professional-growth-coach
  ```

  Expected: the exact enabled version is selected; source/cache inventory and aggregate digests match; all accepted/rejected smoke matrices are green; and no bytecode/private metadata artifacts exist.

- [ ] **Step 4: Update and bind the attestation**

  Record the immutable source commit/tree, installed version, aggregate digest, file counts, package/semantic/packet smoke counts, and explicit `visual_browser_assistive_technology_QA=not_run_not_claimed`. Run the attestation binding test.

- [ ] **Step 5: Push each release commit and verify remote head**

  ```bash
  git push origin HEAD:main
  git ls-remote origin refs/heads/main
  git status --short --branch
  ```

  Expected: remote head equals the published commit and the checkout is clean.

## Execution review checklist

- [ ] Each task has a failing test before production code.
- [ ] Each commit is independently testable and pushed before the next release checkpoint.
- [ ] No external career action, browser edit, message, calendar event, or recruiter contact is executed.
- [ ] Next-cycle opportunities are recorded only after the release evidence is complete.
