# Coach Decision Trace Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a market-only, privacy-safe decision trace to each validated v2 coach-priority card without changing persisted schemas, v1 output, or no-market bytes.

**Architecture:** Derive an immutable display projection in the v2 renderer from existing validated priorities, evidence, section coverage, and authorization state. Keep the trace inside each priority card; reuse the existing single Decide ahora authorization card through an internal anchor instead of repeating its question. Add only renderer/CSS/test contracts, with all malformed explicit inputs failing before output.

**Tech Stack:** Python 3.11/3.14, `unittest`, HTML escaping, existing v2 renderer/CSS, static privacy checker, locked release validator.

**Spec:** `docs/superpowers/specs/2026-08-21-coach-decision-trace-design.md`

## Global Constraints

- Render the trace only when a validated market dossier is composed; preserve v2 no-market bytes and v1 output.
- Do not add a persisted `decision_trace` schema, builder, handoff field, or external service.
- Keep exactly one literal authorization question; trace cards link to the existing authorization card.
- Never render evidence IDs, capture references, paths, URLs, emails, raw profile text, or unvalidated paraphrases.
- External actions, hiring/outcome promises, eligibility inference, forms, buttons, and external links remain forbidden.
- Invalid explicit market/trace inputs fail before output; diagnostics are bounded and non-echoing.
- Verify current Python and CPython 3.11, full plugin, static, privacy, release, diff-check, and protected v1/no-market snapshots.

### Task 1: Derive and test the trace projection

**Files:**
- Modify: `tests/test_executive_career_dossier_v2.py` (new table-driven trace contracts beside existing priority/authorization tests)
- Modify: `plugins/professional-growth-coach/scripts/render_executive_career_dossier_v2.py` (private projection helpers near `_render_coach_priorities`)
- Test fixtures: use existing `scenario-a-es.json` and `scenario-c-en.json` through the current fixture loaders; do not create persistent raw-profile fixtures.

**Interfaces:**
- Produces a private renderer helper that accepts one validated priority plus frozen dossier/market mappings and returns a display-only mapping with `target_section`, ordered `evidence_views`, `template_fields`, `inspection_state`, and optional `authorization_anchor`.
- Consumes existing `evidence_ids`, `section_coverage`, `client_template`, `authorization`, and market composition validation; no new public schema field.

- [ ] **Step 1: Write failing tests for the derived contract.** Add ES/EN cases asserting every priority card has four trace labels, concrete evidence state/paraphrase, existing template field keys, localized inspection status, and at most one `href="#decide-now-authorization-title"`. Assert the literal authorization question count remains one.

- [ ] **Step 2: Add failing privacy/failure cases.** Mutate an evidence ID to an unresolved or wrong-section value, inject raw capture/path/profile URL text into a paraphrase source, and pass malformed explicit market input. Assert `DossierValidationError`, no output path, no raw value in diagnostics, and unchanged no-market snapshot.

- [ ] **Step 3: Run the focused tests and record RED.**

  ```bash
  PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest tests.test_executive_career_dossier_v2.ExecutiveCareerDossierV2RendererTests -q
  ```

  Expected: new trace assertions fail before production changes; existing v1/no-market tests remain the control baseline.

- [ ] **Step 4: Implement the minimal projection.** Resolve evidence through existing validators, map states to localized safe labels/paraphrases, derive template field labels from the already validated `client_template`, and map coverage states to `inspected_present`, `candidate_supplied`, `pending`, `declined`, `failed`, or `unavailable`. For pending state return only `authorization_anchor="decide-now-authorization-title"`; never duplicate question copy.

- [ ] **Step 5: Run focused tests GREEN on both interpreters.**

  ```bash
  PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest tests.test_executive_career_dossier_v2 -q
  PYTHONDONTWRITEBYTECODE=1 /Users/kevinriosferrer/.local/bin/python3.11 -B -m unittest tests.test_executive_career_dossier_v2 -q
  ```

- [ ] **Step 6: Commit the projection/tests.**

  ```bash
  git add plugins/professional-growth-coach/scripts/render_executive_career_dossier_v2.py tests/test_executive_career_dossier_v2.py
  git commit -m "feat: derive coach decision trace"
  ```

### Task 2: Render the trace accessibly and responsively

**Files:**
- Modify: `plugins/professional-growth-coach/scripts/render_executive_career_dossier_v2.py` (trace markup in `_render_coach_priorities`)
- Modify: `plugins/professional-growth-coach/assets/career-market-learning-dossier-v1.css` (trace layout, print, dark, forced-colors, reduced-motion rules)
- Modify: `tests/test_executive_career_dossier_v2.py` (DOM/ARIA/CSS and output-order assertions)
- Preserve: `tests/test_executive_career_dossier.py` and no-market protected snapshots unchanged.

**Interfaces:**
- Consumes Task 1 display mapping.
- Produces one `<section class="decision-trace">` per priority with generated rank/ordinal IDs only for ARIA; no evidence IDs in visible HTML.

- [ ] **Step 1: Write failing markup/CSS tests.** Assert the ordered sequence `Prioridad → Evidencia disponible → Plantilla privada → Permiso de lectura`, exactly one labelled trace per card, unique/resolved ARIA IDs, no forms/buttons/external hrefs, and CSS contracts for `max-width:640px`, print `break-inside:avoid`, forced-colors, dark mode, and reduced motion.

- [ ] **Step 2: Run the focused markup test to verify RED.**

  ```bash
  PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest tests.test_executive_career_dossier_v2.ExecutiveCareerDossierV2RendererTests.test_decision_trace_markup_and_accessibility -q
  ```

- [ ] **Step 3: Implement minimal HTML/CSS.** Use `<section aria-labelledby>`, an ordered list, escaped display strings, internal anchor links only, fluid `minmax(0, ...)` tracks, and localized status/boundary copy. Keep the authorization question in the existing Decide ahora card only.

- [ ] **Step 4: Run Task 2 GREEN plus no-market/v1 byte controls.**

  ```bash
  PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest tests.test_executive_career_dossier_v2 tests.test_executive_career_dossier -q
  ```

- [ ] **Step 5: Commit the renderer/CSS slice.**

  ```bash
  git add plugins/professional-growth-coach/scripts/render_executive_career_dossier_v2.py plugins/professional-growth-coach/assets/career-market-learning-dossier-v1.css tests/test_executive_career_dossier_v2.py
  git commit -m "feat: render accessible coach decision trace"
  ```

### Task 3: Whole-range review and release integration

**Files:**
- Modify only tests/docs needed to record the task report and deterministic provenance; do not alter schemas or v1 snapshots.
- Review: Task 1 and Task 2 commits, `docs/superpowers/specs/2026-08-21-coach-decision-trace-design.md`.

**Interfaces:**
- Consumes both implementation commits and their focused evidence.
- Produces independent review report, fresh gate evidence, exact release attestation, installed smoke, and remote `main` update.

- [ ] **Step 1: Run the independent review probes.** Verify ES/EN evidence states, unresolved IDs, raw-value no-echo, one-question consent, ARIA resolution, external-control absence, safe controls, v1/no-market bytes, and malformed direct/CLI/writer fail-before-output.

- [ ] **Step 2: Run release gates from the final tree.** Run both focused interpreters, `tests.test_full_plugin`, static checks, repository privacy, locked release validation, and `git diff --check`. Classify only the documented cycle provenance records as attestation work.

- [ ] **Step 3: Consume the official cachebuster once, install exact local selector, and verify source/cache parity.** Generate a `0600` installed smoke with a valid market trace and a rejected invalid trace; do not claim browser/AT QA if Superdesign/browser remains unavailable.

- [ ] **Step 4: Rebind deterministic provenance, commit attestation, and re-run every gate that could be affected.** Verify worktree cleanliness and installed version/hash before publication.

- [ ] **Step 5: Push `codex/canonical-consolidation-public:main` and verify `git ls-remote origin refs/heads/main` equals the attested commit.**

