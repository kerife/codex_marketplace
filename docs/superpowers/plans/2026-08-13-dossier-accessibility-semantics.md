# Dossier Accessibility Semantics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give dossier copy buttons contextual accessible names and replace the misleading utility navigation landmark with an action group.

**Architecture:** Keep all changes in the existing Python renderer and its
render-contract tests. Derive `aria-label` text from the already validated
localized category labels, preserve visible text and data attributes, and
change only the utility container element/role; no CSS, JavaScript, schema, or
external-resource changes.

**Tech Stack:** Python 3, `unittest`, deterministic offline HTML renderer,
Superdesign static parity checks, Codex plugin release validator.

## Global Constraints

- Visible labels stay `Copiar borrador` / `Copy draft`.
- Only non-null draft blocks render a copy button and `data-copy-target`.
- `aria-describedby` continues to reference the live status and optional confirmation.
- `.utility-actions` keeps its existing class and print behavior.
- No draft text, private identifiers, external URLs, CSS, JS, schema, or clipboard behavior changes.

---

### Task 1: Add failing renderer contracts

**Files:**
- Modify: `tests/test_executive_career_dossier.py` near `test_copy_controls_have_stable_names_and_live_status_targets`
- Modify: `tests/test_executive_career_dossier.py` near `test_rendered_dossier_has_private_offline_landmarks_and_skip_navigation`

**Interfaces:**
- Consumes: `self.es_dossier`, `self.en_dossier`, and `self.renderer.render_dossier_html`.
- Produces: assertions requiring contextual `aria-label` values and a
  `div[role=group]` utility container.

- [ ] **Step 1: Write the failing tests**

  Add a test that extracts every copy button's visible text and `aria-label`.
  Assert Spanish labels are unique and equal to:
  `Copiar borrador: Titular`, `Copiar borrador: Apertura de Acerca de`, and
  `Copiar borrador: Bullet de experiencia`; assert English labels are unique,
  retain `Copy draft` as visible text, and contain the localized category.
  Assert every button still references its status and that an omitted card has
  no `data-copy-target`. Add a separate test asserting the utility header has
  `<div class="utility-actions no-print" role="group" ...>` and no utility
  `<nav>`.

- [ ] **Step 2: Run the tests to verify RED**

  Run:
  `PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest tests.test_executive_career_dossier.ExecutiveCareerDossierRenderTests.test_copy_controls_have_contextual_accessible_names tests.test_executive_career_dossier.ExecutiveCareerDossierRenderTests.test_utility_actions_are_an_action_group -q`

  Expected: both tests fail because buttons have no `aria-label` and the
  utility container is currently a `<nav>`.

### Task 2: Implement the minimal semantic renderer change

**Files:**
- Modify: `plugins/professional-growth-coach/scripts/render_executive_career_dossier.py` in `_render_header` and `_render_copy_blocks`

**Interfaces:**
- Consumes: `COPY[locale]`, `COPY_LABELS[locale]`, validated copy block
  categories, and the existing `described_by`/status IDs.
- Produces: localized `aria-label` attributes and a utility `<div role="group">`.

- [ ] **Step 1: Add the contextual copy label**

  Compute:
  `copy_label = f"{labels['copy_button']}: {COPY_LABELS[locale][text(block['category'])]}"`
  only inside the non-null draft branch, and add
  `aria-label="{copy_label}"` to the existing button. Leave its visible text,
  `data-copy-*`, `aria-describedby`, and status markup unchanged.

- [ ] **Step 2: Correct the utility landmark**

  Replace only the opening/closing `_render_header` tags:
  `<nav class="utility-actions no-print" aria-label="...">` becomes
  `<div class="utility-actions no-print" role="group" aria-label="...">`,
  and the closing `</nav>` becomes `</div>`. Preserve the privacy chip,
  print button, class, label, and all CSS hooks.

- [ ] **Step 3: Run the focused GREEN tests**

  Re-run the two tests from Task 1. Expected: both pass with no output other
  than the unittest success summary.

### Task 3: Regression and release gates

**Files:**
- Modify: `docs/superpowers/plans/2026-08-12-public-marketplace-follow-ups.md`
- Create: `docs/superpowers/specs/2026-08-13-dossier-accessibility-semantics-design.md`
- Modify: release provenance files only during the release attestation step.

**Interfaces:**
- Consumes: the renderer contract from Task 2 and the existing release
  cachebuster/provenance workflow.
- Produces: a published, installed plugin whose source and cache are byte
  identical and whose follow-up list no longer claims these semantics are
  pending.

- [ ] **Step 1: Run dossier and parity regressions**

  Run:
  `PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest tests.test_executive_career_dossier tests.test_superdesign_theme_asset_parity tests.test_repository_privacy -q`

- [ ] **Step 2: Run plugin/static/release validation**

  Run the plugin discovery suite, `plugins/professional-growth-coach/tests/run_static_checks.py`, `scripts/check_repository_privacy.py`, `scripts/run_release_validation.sh`, and `git diff --check`.

- [ ] **Step 3: Update the follow-up record**

  Mark contextual copy labels and utility action-group semantics as landed;
  retain browser/OS visual QA, root-suite environmental limitations, and the
  next CSV diagnostic-redaction cycle as explicit follow-ups.

- [ ] **Step 4: Cachebuster, provenance, publish, and reinstall**

  Commit the functional change, run the official cachebuster once, rebind
  cycle sidecars and installed smoke attestation to the new cachebuster commit
  and plugin tree, run validators, push `main`, run
  `codex plugin add professional-growth-coach@codex-marketplace-public --json`,
  compare source/cache hashes, and verify the installed validator.
