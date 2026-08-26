# Private First-Interview Provenance Boundary v2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) to implement this plan task-by-task. Every task ends with focused tests, an independent review, and a commit before the next task starts.

**Goal:** Add a v2 private first-interview board that persists no raw source, accepts only opaque validated source bundles, exposes honest provenance, and ships with stronger writer, UX, documentation, and release gates while leaving v1 frozen.

**Architecture:** Capture a source group once behind an immutable `ValidatedPrivateFirstInterviewSourceBundle`; use explicit `synthetic_fixture` or `composition_only` provenance; derive a sanitized v2 projection and revalidate it from private frozen payloads. Keep the existing v1 implementation unchanged, add a v2 proof/writer/renderer surface, and bind all package/release evidence to the new files. No upstream-attested state is claimed until a real external issuer/verifier exists.

**Tech Stack:** Python 3.11+, JSON Schema Draft 2020-12 subset validator, stdlib `unittest`, descriptor-anchored filesystem APIs, HTML escaping, self-contained HTML/CSS, existing static/privacy/parity/release harnesses, and saved Superdesign token references.

**Spec:** `docs/superpowers/specs/2026-08-26-private-first-interview-provenance-boundary-v2-design.md`

## Global Constraints

- Preserve the published v1 schema, fixtures, validator, builder, renderer, bytes, and historical tests exactly.
- The v2 public builder accepts only the exact `ValidatedPrivateFirstInterviewSourceBundle` class; raw mappings, serialized JSON, caller-authored artifacts, and duck-typed proofs fail with fixed no-echo errors.
- `synthetic_fixture` is issued only by the private fixture issuer; the exact v1 adapter is always `composition_only` and can never be upgraded. No upstream-attested state is emitted in this release.
- v2 artifacts never contain `source_group`, `source_group_json`, source rows, record/group IDs, raw fact summaries, URLs, PII, secrets, prompt-injection text, or arbitrary confidential prose.
- The only v2 persisted provenance fields are the closed contract/state/digest/source-kind metadata; digest and IDs never reach HTML, receipts, diagnostics, prompts, or public examples.
- Every v2 output remains `draft_only=true`, `external_actions_authorized=false`, `no_message_action=true`, `no_calendar_action=true`, all raw-retention flags false, `local_save_mode=disabled`, and `candidate_review_required=true`.
- No LinkedIn/Chrome access, external actions, forms, buttons, scripts, external links, network resources, uploads, publishing, purchases, enrollment, or scheduling.
- No browser, print-preview, or assistive-technology QA claim without direct runtime evidence; deterministic DOM/CSS checks are labeled accordingly.
- Work only in `/Users/kevinriosferrer/projects/job_search_coach/.worktrees/private-first-interview-board-v1-authorized`; use `apply_patch` for edits and commit after each green task.

---

### Task 1: Source-bundle proof boundary

**Files:**
- Create: `plugins/professional-growth-coach/schemas/private-first-interview-source-bundle-v1.schema.json`
- Create: `plugins/professional-growth-coach/scripts/private_first_interview_source_bundle.py`
- Create: `plugins/professional-growth-coach/tests/test_private_first_interview_source_bundle.py`
- Modify: `plugins/professional-growth-coach/tests/test_private_first_interview_conversion_board_v1.py` only for an unchanged-v1 regression assertion if required

**Interfaces:**
- Produces `ValidatedPrivateFirstInterviewSourceBundle` with no public raw-source accessor.
- Produces `issue_validated_private_first_interview_source_bundle(source_group: object, *, provenance_state: str) -> ValidatedPrivateFirstInterviewSourceBundle` for the private fixture issuer; the only accepted state is `synthetic_fixture`.
- Produces `adapt_v1_private_first_interview_proof(validated_v1: object) -> ValidatedPrivateFirstInterviewSourceBundle`, accepting only the exact published v1 proof class and assigning `composition_only`.
- Produces internal `_payload_json(value) -> tuple[str, str]` and `metadata(value) -> dict[str, object]` helpers for the v2 validator; metadata contains only contract, state, digest, and fixed source kinds.

- [ ] **Step 1: Write RED tests for identity and provenance.** Add tests that issue a synthetic bundle through the private issuer, assert exact class identity, immutable attributes, fixed source kinds, deterministic digest, no `source_group` property, and distinct `synthetic_fixture`/`composition_only` metadata. Assert `upstream_attested` and any other unknown state, raw non-mapping, unsafe arbitrary confidential prose, wrong shape, oversized/cyclic input, and a forged duck-typed object raise fixed `ValueError`/`TypeError` without echoing input.

```python
bundle = source_bundle.issue_validated_private_first_interview_source_bundle(
    synthetic_source(), provenance_state="synthetic_fixture"
)
assert source_bundle.metadata(bundle)["provenance_state"] == "synthetic_fixture"
assert not hasattr(bundle, "source_group")
with pytest.raises(ValueError, match="source bundle is unavailable"):
    source_bundle.issue_validated_private_first_interview_source_bundle(
        synthetic_source(), provenance_state="composition_only"
    )
```

- [ ] **Step 2: Run the RED tests.**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest -v plugins.professional-growth-coach.tests.test_private_first_interview_source_bundle
```

Expected: import or interface failures because the new schema/module do not exist.

- [ ] **Step 3: Implement one-capture, private-payload issuance.** Reuse the existing bounded snapshot and safe-prose helpers. Validate the complete source shape and snapshot before storing canonical JSON in private slots. Permit only `synthetic_fixture` for the private issuer and `composition_only` for the v1 adapter; reject `upstream_attested` until an external issuer/verifier is integrated. Expose a copied metadata dictionary and no raw-source property.

- [ ] **Step 4: Run the source-bundle tests GREEN on both runtimes.**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest -q plugins.professional-growth-coach.tests.test_private_first_interview_source_bundle
PYTHONDONTWRITEBYTECODE=1 /Users/kevinriosferrer/.local/bin/python3.11 -B -m unittest -q plugins.professional-growth-coach.tests.test_private_first_interview_source_bundle
```

- [ ] **Step 5: Commit and request review.**

```bash
git add plugins/professional-growth-coach/schemas/private-first-interview-source-bundle-v1.schema.json plugins/professional-growth-coach/scripts/private_first_interview_source_bundle.py plugins/professional-growth-coach/tests/test_private_first_interview_source_bundle.py
git commit -m "feat: add private interview source bundle boundary"
```

Reviewer checks: no public raw accessor, no state upgrade, no unsafe prose acceptance, and v1 test output unchanged.

### Task 2: Sanitized v2 board contract and projection

**Files:**
- Create: `plugins/professional-growth-coach/schemas/private-first-interview-conversion-board-v2.schema.json`
- Create: `plugins/professional-growth-coach/scripts/private_first_interview_conversion_board_v2_identity.py`
- Create: `plugins/professional-growth-coach/scripts/build_private_first_interview_conversion_board_v2.py`
- Create: `plugins/professional-growth-coach/scripts/validate_private_first_interview_conversion_board_v2.py`
- Create: `plugins/professional-growth-coach/tests/test_private_first_interview_conversion_board_v2.py`

**Interfaces:**
- Produces `ValidatedPrivateFirstInterviewConversionBoardV2` with private artifact/source-bundle payloads.
- Produces `build_private_first_interview_conversion_board_v2(source_bundle: object, *, locale: str = "en", as_of_date: str) -> ValidatedPrivateFirstInterviewConversionBoardV2`.
- Produces `validate_private_first_interview_conversion_board_v2(source_bundle_or_artifact: object, *, locale: str = "en", as_of_date: str) -> ValidatedPrivateFirstInterviewConversionBoardV2`.
- Produces `_revalidate_validated_private_first_interview_conversion_board_v2(value: object) -> dict[str, object]` for writer/renderer consumers.

- [ ] **Step 1: Write RED tests for closed schema and source boundary.** Copy only the synthetic source fixture into an in-memory issuer helper. Assert v2 artifacts have 1/7/4/7 projection cardinalities, `source_provenance`, fixed delivery/approval values, no `source_group` or source prose, and a closed stop state. Assert raw mappings, v1 artifacts, caller-authored provenance, forged rehashed groups, unknown locale/date, duplicate keys, unsafe arbitrary confidential prose, and a forged proof object fail before projection.

```python
bundle = issue_fixture_bundle()
proof = build_v2.build_private_first_interview_conversion_board_v2(bundle)
artifact = proof.artifact
assert "source_group" not in artifact
assert artifact["source_provenance"]["provenance_state"] == "synthetic_fixture"
assert len(artifact["week"]) == 7
with self.assertRaisesRegex(ValueError, "does not match validated sources"):
    build_v2.build_private_first_interview_conversion_board_v2(raw_source_mapping())
```

- [ ] **Step 2: Run the RED tests.**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest -v plugins.professional-growth-coach.tests.test_private_first_interview_conversion_board_v2
```

Expected: import/schema/proof failures because the v2 files do not exist.

- [ ] **Step 3: Implement the closed v2 schema and deterministic projection.** Port the v1 localized projection without copying source fields. Generate `source_provenance` exclusively from bundle metadata, recompute projection from the bundle's private canonical source, enforce stop suppression, and compare canonical JSON on revalidation. Reject every caller-authored top-level provenance value and every raw input path.

- [ ] **Step 4: Run focused v2, v1, schema, and privacy tests GREEN.**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest -q plugins.professional-growth-coach.tests.test_private_first_interview_conversion_board_v2
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest -q plugins.professional-growth-coach.tests.test_private_first_interview_conversion_board_v1
PYTHONDONTWRITEBYTECODE=1 python3 -B scripts/check_repository_privacy.py
```

- [ ] **Step 5: Commit and review the v2 contract.**

```bash
git add plugins/professional-growth-coach/schemas/private-first-interview-conversion-board-v2.schema.json plugins/professional-growth-coach/scripts/private_first_interview_conversion_board_v2_identity.py plugins/professional-growth-coach/scripts/build_private_first_interview_conversion_board_v2.py plugins/professional-growth-coach/scripts/validate_private_first_interview_conversion_board_v2.py plugins/professional-growth-coach/tests/test_private_first_interview_conversion_board_v2.py
git commit -m "feat: add sanitized private interview board v2"
```

Reviewer checks: v1 bytes are unchanged; artifact contains only sanitized metadata; composition-only cannot become attested; all diagnostics are generic.

### Task 3: Private v2 writer and installed-safe filesystem boundary

**Files:**
- Create: `plugins/professional-growth-coach/scripts/write_private_first_interview_conversion_board_v2.py`
- Create: `plugins/professional-growth-coach/tests/test_write_private_first_interview_conversion_board_v2.py`
- Modify: `plugins/professional-growth-coach/scripts/private_input_loader.py` only if a shared non-destructive parent-permission helper is required

**Interfaces:**
- Produces `write_private_first_interview_conversion_board_v2(validated_board: object, output: Path, *, force: bool = False) -> WriteReceipt`.
- `WriteReceipt` contains only artifact type, schema version, locale, output path, `private_draft=True`, and `external_action_authorized=False`; it never contains digest, IDs, or source values.

- [ ] **Step 1: Write RED writer tests.** Assert exact v2 proof identity is required; output bytes are canonical; file mode is `0600`; an existing regular target requires `force`; force replaces only a regular target; symlink, directory, FIFO, insecure existing parent, wrong-owner parent, invalid proof, and simulated fsync failure leave no output or temporary file. Assert diagnostics never echo path/source values in the exception message.

- [ ] **Step 2: Run the RED writer tests.**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest -v plugins.professional-growth-coach.tests.test_write_private_first_interview_conversion_board_v2
```

Expected: module/import failures.

- [ ] **Step 3: Implement descriptor-anchored atomic writing.** Revalidate the exact proof before resolving the output; walk every parent with `O_NOFOLLOW`, require a directory owned by the current UID with no group/world write bits, create missing parents as `0700`, create a unique exclusive temporary file as `0600`, flush/fsync, use `os.replace` only under `force=True`, hard-link/unlink otherwise, fsync the parent, and clean all descriptors/temp files on every exception.

- [ ] **Step 4: Run writer and v1 writer tests GREEN.**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest -q plugins.professional-growth-coach.tests.test_write_private_first_interview_conversion_board_v2 plugins.professional-growth-coach.tests.test_private_first_interview_conversion_board_v1
```

- [ ] **Step 5: Commit.**

```bash
git add plugins/professional-growth-coach/scripts/write_private_first_interview_conversion_board_v2.py plugins/professional-growth-coach/tests/test_write_private_first_interview_conversion_board_v2.py
git commit -m "feat: harden private interview v2 writer"
```

### Task 4: Renderer, trust strip, and visual parity

**Files:**
- Create: `plugins/professional-growth-coach/scripts/render_private_first_interview_conversion_board_v2.py`
- Create: `plugins/professional-growth-coach/assets/private-first-interview-conversion-board-v2.html`
- Create: `plugins/professional-growth-coach/assets/private-first-interview-conversion-board-v2.css`
- Create: `plugins/professional-growth-coach/tests/test_render_private_first_interview_conversion_board_v2.py`
- Modify: `.superdesign/init/pages.md`, `.superdesign/init/routes.md`, `.superdesign/init/components.md`, `.superdesign/init/extractable-components.md`, `.superdesign/init/layouts.md`, `.superdesign/init/theme.md`, `.superdesign/design-system.md`

**Interfaces:**
- Produces `render_private_first_interview_conversion_board_v2(validated_board: object) -> str` and rejects every non-exact v2 proof object.
- HTML has one `board-trust-strip` between decision and sequence; it shows “Fuente sintética de prueba” for fixture data or “Procedencia por composición; revisar fuente” for composition-only, plus “Texto original no almacenado” and “Revisión manual requerida”.

- [ ] **Step 1: Write RED renderer tests.** Assert ES/EN semantic structure, trust-strip order and text, presence in stop state, no digest/IDs/source prose, escaped values, one h1, focusable main, skip link, no forms/buttons/scripts/external URLs, CSP/noindex/no-referrer, and explicit `aria-labelledby`. Assert CSS contains mobile, intermediate-width, print, dark, forced-colors (including both boundary classes), reduced-motion, `main:focus-visible`, and mobile column reset hooks.

- [ ] **Step 2: Run RED renderer tests.**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest -v plugins.professional-growth-coach.tests.test_render_private_first_interview_conversion_board_v2
```

- [ ] **Step 3: Implement renderer and assets.** Reuse only repository `practice_triage` tokens and sanitized v2 fields; escape all text; render a static trust strip before details; keep stop minimal; do not expose digest or provenance IDs; use semantic sections/lists and text state labels. Add `main:focus-visible`, skip-link focus, `minmax()` sequence layout, mobile column reset, and forced-color rules for trust and approval boundaries.

- [ ] **Step 4: Run renderer, token, and Superdesign parity tests GREEN.**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest -q plugins.professional-growth-coach.tests.test_render_private_first_interview_conversion_board_v2 plugins.professional-growth-coach.tests.test_design_tokens tests.test_superdesign_theme_asset_parity
```

- [ ] **Step 5: Commit.**

```bash
git add plugins/professional-growth-coach/scripts/render_private_first_interview_conversion_board_v2.py plugins/professional-growth-coach/assets/private-first-interview-conversion-board-v2.html plugins/professional-growth-coach/assets/private-first-interview-conversion-board-v2.css plugins/professional-growth-coach/tests/test_render_private_first_interview_conversion_board_v2.py .superdesign
git commit -m "feat: render private interview provenance trust boundary"
```

### Task 5: Routing, documentation, package gates, and release evidence

**Files:**
- Modify: `plugins/professional-growth-coach/README.md`
- Modify: `plugins/professional-growth-coach/skills/professional-growth-coach/SKILL.md`
- Modify: `README.md`
- Modify: `plugins/professional-growth-coach/tests/run_static_checks.py`
- Modify: `tests/test_plugin_structure.py`
- Modify: `scripts/check_repository_privacy.py`
- Modify: `tests/test_full_plugin.py`
- Create/modify: `plugins/professional-growth-coach/tests/fixtures/private-first-interview-conversion-board-v2/accepted-es.json`
- Create/modify: `plugins/professional-growth-coach/tests/fixtures/private-first-interview-conversion-board-v2/accepted-en.json`
- Modify: `plugins/professional-growth-coach/tests/evals/final/installed-smoke-test.md`

**Interfaces:**
- Documentation routes new requests to the v2 library path and labels v1 as frozen legacy compatibility only.
- Static/privacy/package checks require every v2 file, forbid `source_group` in v2 schema/artifacts, run writer smoke, and retain historical v1 checks.

- [ ] **Step 1: Add failing inventory and routing assertions.** Require all v2 files in package inventory, v2 fixtures to be synthetic and identity-free, root/plugin README starter prompts in ES/EN, explicit composition-only wording, trust-strip asset references, and writer runtime smoke. Assert no public doc contains a digest, internal ID, raw source example, or external-action instruction.

- [ ] **Step 2: Run the RED integration checks.**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest -v tests.test_plugin_structure tests.test_full_plugin
PYTHONDONTWRITEBYTECODE=1 python3 -B scripts/check_repository_privacy.py
```

- [ ] **Step 3: Implement docs/checks/fixtures.** Add exact v2 starter prompts, update routing precedence, add package inventory/static recognizers and installed writer smoke, extend privacy checks and parity inventory, and record `visual_browser_assistive_technology_QA: not_run_not_claimed` in the attestation. Keep v1 references and all historical counts unchanged.

- [ ] **Step 4: Run the complete applicable suite.**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s plugins/professional-growth-coach/tests -p 'test*.py' -q
PYTHONDONTWRITEBYTECODE=1 python3 -B scripts/check_repository_privacy.py
PYTHONDONTWRITEBYTECODE=1 python3 -B plugins/professional-growth-coach/tests/run_static_checks.py
```

If the known executive-dossier timeout recurs, stop that runner, preserve the traceback in the private task ledger, and report the exact timeout separately; do not convert it into a board success claim.

- [ ] **Step 5: Commit integration.**

```bash
git add plugins/professional-growth-coach/README.md plugins/professional-growth-coach/skills/professional-growth-coach/SKILL.md README.md plugins/professional-growth-coach/tests/run_static_checks.py tests/test_plugin_structure.py scripts/check_repository_privacy.py tests/test_full_plugin.py plugins/professional-growth-coach/tests/fixtures/private-first-interview-conversion-board-v2 plugins/professional-growth-coach/tests/evals/final/installed-smoke-test.md
git commit -m "docs: integrate private interview provenance v2"
```

### Task 6: Independent release verification, install, and publication

**Files:**
- Modify: `plugins/professional-growth-coach/.codex-plugin/plugin.json` (version only after all source gates are green)
- Modify: `plugins/professional-growth-coach/tests/evals/final/installed-smoke-test.md`
- Modify: release ledger under `.superpowers/sdd/2026-08-26-private-first-interview-provenance-boundary-v2/`

**Interfaces:**
- Release attestation binds the immutable Git archive tree, source/cache aggregate, installed plugin version, v1 historical counts, v2 semantic counts, writer smoke result, and visual-QA boundary.

- [ ] **Step 1: Dispatch independent security, product, and UX agents against the completed tree.** Each agent receives the candidate commit and returns only findings; no release file is changed until findings are reviewed and resolved.

- [ ] **Step 2: Run focused and full verification from a clean source tree.** Capture exact outputs for v2 tests, v1 regression, package suite, privacy checker, static checker, source/cache parity, and installed smokes. Confirm no source/cache file hash mismatch and no untracked generated artifacts.

- [ ] **Step 3: Bump only the plugin manifest version and update attestation.** Generate a new timestamped `0.2.0+codex` version at release time, run manifest-only checks, then run the immutable-attestation test separately so its expected stale failure is the only temporary failure before attestation update.

- [ ] **Step 4: Commit the release and push exactly as authorized.**

```bash
git add plugins/professional-growth-coach/.codex-plugin/plugin.json plugins/professional-growth-coach/tests/evals/final/installed-smoke-test.md .superpowers/sdd/2026-08-26-private-first-interview-provenance-boundary-v2
git commit -m "chore: attest private interview provenance v2 release"
git push origin HEAD:main
```

- [ ] **Step 5: Fetch/verify and reinstall in Codex.** Confirm `git ls-remote origin refs/heads/main` equals the release commit, detach the public checkout at `origin/main`, run `codex plugin add professional-growth-coach@codex-marketplace-public --json`, and verify the installed version, source/cache per-file SHA-256 parity, v2 installed smokes, and clean public checkout.

- [ ] **Step 6: Record postflight evidence and close the cycle.** Update the ledger with commit, remote, installed version, aggregate digest, test counts, writer smoke, privacy/static status, and `visual_browser_assistive_technology_QA: not_run_not_claimed`; leave the persistent improvement goal active for the next expert audit.
