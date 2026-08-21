# Career Learning Decision Bundle Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an optional validated learning/ROI decision bundle and conversational panel while preserving the existing market dossier v1 and no-market artifacts.

**Architecture:** Keep `career-market-learning-dossier-v1` unchanged. Add a closed `career-learning-decision-v1` schema plus dependency-free validator/builder that binds decisions to existing vacancy/evidence IDs; pass it to the v2 renderer only as an all-or-none optional group. The renderer emits a private, internal-navigation panel and fails closed when the bundle is absent or invalid.

**Tech Stack:** Python 3.11/3.14, closed JSON-schema subset, existing dossier validators/builders/renderers, static HTML/CSS, unittest, repository privacy/release validators.

**Spec:** `docs/superpowers/specs/2026-08-21-career-learning-decision-design.md`

## Global Constraints

- Existing `career-market-learning-dossier-v1` keeps `learning_state=not_evaluated` and `learning_decisions=[]`.
- N=0 emits no learning panel and no learning score/gap claim.
- Evaluated learning contains exactly 3–5 ranked decisions and one or more cheaper proof/no-learning alternatives.
- Provider facts require dated official sources; unstated cost, duration, eligibility, geography, renewal, and maintenance remain `unknown`.
- `draft_only=true`, `no_external_action=true`, and the fixed outcome boundary are mandatory.
- No candidate identity, raw vacancy/evidence IDs, private analytics, or external action controls may reach HTML.
- Do not consume cachebuster, install, or push until all pre-release gates and independent review are green.

### Task 1: Closed learning schema and pure validator

**Files:**
- Create: `plugins/professional-growth-coach/schemas/career-learning-decision-v1.schema.json`
- Create: `plugins/professional-growth-coach/scripts/validate_career_learning_decision.py`
- Test: `tests/test_career_learning_decision.py`
- Test: `plugins/professional-growth-coach/tests/test_private_schema_conformance.py`

**Interfaces:**
- Produces `validate_learning_bundle(value: object, market: Mapping[str, object], dossier: Mapping[str, object], research: Mapping[str, object]) -> list[str]`.
- Produces `load_learning_bundle(path: Path) -> dict[str, object]` with bounded diagnostics and no echoed input.

- [x] Write RED tests for absent bundle, N=0 rejection, evaluated 3-row acceptance, 2/6 row rejection, duplicate ranks, invalid option/decision/gap enums, stale/mismatched snapshots, unbound vacancy/evidence references, missing official provider metadata, identity/raw-ID/URL echo, cycles, and unknown fields.
- [x] Run the focused tests and record the expected failures because the schema/module do not exist.
- [x] Implement the closed schema and pure validator with iterative bounded traversal and redacted static diagnostics.
- [x] Run focused schema/validator tests in Python 3.14 and CPython 3.11; require all GREEN before integration.
- [x] Add the schema to package inventory/static checks without changing existing v1 schemas.
- [x] Commit `feat: validate career learning decisions` and harden it in `378f6e5`.

### Task 2: Evidence-bound learning builder

**Files:**
- Create: `plugins/professional-growth-coach/scripts/build_career_learning_decision.py`
- Test: `tests/test_career_learning_decision.py`
- Modify: `plugins/professional-growth-coach/tests/run_static_checks.py`

**Interfaces:**
- Consumes validated market research, market dossier, executive dossier, and identity-free learning rows.
- Produces `build_learning_bundle(research, market_dossier, executive_dossier, decisions) -> dict[str, object]` and `snapshot_for_learning_bundle(value) -> str`.

- [x] Write RED tests for snapshot binding, deterministic rank ordering, recurrence-to-gap binding, exact 3–5 output rows, `do_nothing_now`, project-vs-certificate alternatives, and all-or-none invalid input behavior.
- [x] Run the RED tests and confirm the builder import/contract failures.
- [x] Implement the smallest deterministic builder; preserve every provider unknown and never invent prices or eligibility.
- [x] Run builder/validator/conformance tests on both runtimes and verify v1 fixture deep equality.
- [x] Add package interface/fixture checks and commit `feat: build evidence-bound learning decisions` at `9826eb1`.

### Task 3: Conversational renderer and CSS

**Files:**
- Modify: `plugins/professional-growth-coach/scripts/render_executive_career_dossier_v2.py`
- Modify: `plugins/professional-growth-coach/assets/career-market-learning-dossier-v1.css`
- Modify: `.superdesign/init/theme.md`
- Test: `tests/test_executive_career_dossier_v2.py`
- Test: `tests/test_superdesign_theme_asset_parity.py`

**Interfaces:**
- Extends `render_dossier_html(..., learning_decision: Mapping[str, object] | None = None)` without changing existing callers.
- Adds one internal `#learning-decision-title` anchor from `Decide ahora` only when the validated bundle is rendered.

- [x] Write RED tests for N=0 omission, N=1..5 decision rendering, one conversational heading, no external controls/IDs/raw identity, internal navigation, and mobile/print/dark/forced-colors/reduced-motion CSS.
- [x] Run the focused renderer tests and verify the missing-panel failures.
- [x] Implement the minimal validated panel after recurrence rows and before gap closure; use `do_nothing_now` when evidence is insufficient.
- [x] Synchronize the Superdesign CSS dump and run renderer, parity, snapshot, and no-market byte tests.
- [x] Complete independent review after RED/GREEN fixes; root commit remains pending.

### Task 4: Review and release gates

**Files:**
- Modify only approved provenance/attestation files after functional review.
- Test: existing full plugin/root/privacy/release suites.

- [ ] Run independent review of the functional range and resolve every Critical/Important finding through RED/GREEN fixes.
- [ ] Run focused, plugin, root, static, privacy, release, schema, parity, and diff checks in Python 3.14 and CPython 3.11; document browser/AT limitations honestly.
- [ ] Rebind deterministic provenance to the functional parent, run the gates again, then invoke the official cachebuster exactly once.
- [ ] Install the exact public selector, verify 121+ source/cache parity and normalized hash, and run installed complete/limited/unavailable smokes.
- [ ] Commit the installation attestation, rerun post-release gates, and verify the public plugin is enabled at the exact version.
- [ ] Push `codex/canonical-consolidation-public:main` and verify `git ls-remote origin refs/heads/main` matches the attestation commit.
