# Private Vacancy Application Packet Implementation Plan

> **For Codex:** REQUIRED EXECUTION SKILL: Use `superpowers:subagent-driven-development` to execute this plan task by task. Every behavior change follows `superpowers:test-driven-development`; each task receives an independent review before the next task starts.

**Goal:** Add an identity-free candidate fact matrix and a deterministic, vacancy-bound private application packet, render it as a secure offline JSON/HTML artifact, route it through the professional-growth coach, and release it with independently bound installed evidence.

**Architecture:** The existing `career-next-action-eligibility-v1` source group remains the only vacancy and trigger authority. A new candidate-fact source contract is independently rebuilt, then both validated groups are captured once and projected into one closed packet with exact signal matching, one readiness state, deterministic localized claims, atomic/no-echo writers, and a non-interactive offline renderer. Package, privacy, installed-smoke, and attestation gates bind the feature without changing historical 39/9 semantics or v1/v2/no-market bytes.

**Tech Stack:** Python 3.11+, JSON Schema Draft 2020-12, `unittest`, stdlib HTML/JSON/filesystem tooling, offline HTML/CSS, existing repository privacy/static/release harnesses, Superdesign design evidence.

**Spec:** `docs/superpowers/specs/2026-08-24-private-vacancy-application-packet-design.md`

**Superdesign evidence:** project `971e4b3b-dcab-4940-9b8e-36dd181cb3d1`, draft `a7447bcf-574b-470f-8dad-13f193c54cc7`, version 1, target key `vacancy-application-packet`. The generated draft is visual evidence only; this spec and repository contracts are authoritative.

## Scope check

This remains one coherent increment. The fact matrix is the packet's required evidence source; the packet contract, renderer, routing, package registration, and installed proof are sequential consumers of the same closed interface. Splitting them into separate plans would leave unreleasable intermediate contracts and duplicate cross-source validation work.

## Success criteria

- The two new schemas are closed, versioned, bounded, source-recomputed, identity-free, and covered by canonical ES/EN fixtures generated only by their builders.
- The packet is produced only for a validated eligibility source whose action is `prepare_private_vacancy_packet`; it accepts no independent vacancy selector.
- All six coverage/confidence rows, all three claim decisions, and all three readiness states are deterministic and mutually exclusive.
- JSON/HTML writers are atomic and fail with fixed generic no-echo diagnostics; no failure leaves partial output.
- The HTML has one decision hierarchy, semantic lists/table/landmarks, safe escaping, no external controls or resources, and static dark/forced-colors/reduced-motion/print support.
- Root routing and client delivery expose the exact identity-free packet path and never imply authorization or application readiness.
- Exact package/static/privacy inventories and canonical fixture recognizers fail closed on near misses.
- Historical bytes and 39 accepted / 9 rejected installed semantics remain pinned; the packet adds a separate 6 accepted / 12 rejected matrix.
- Source gates, manifest-only A, exact install/parity/snapshot-only smokes, attestation-only B, final official validator, and both authorized pushes complete with clean postflight state.

## Global constraints

- The design spec is binding when this plan is ambiguous.
- Work only in `/Users/kevinriosferrer/projects/codex_marketplace/.worktrees/learning-eligibility-vacancy-first`; preserve unrelated changes.
- No production code before a focused test has failed for the expected missing behavior.
- Capture each hostile/composite input once, freeze it, then validate and project that same snapshot. Never re-read caller-controlled mappings during validation or rendering.
- Use existing bounded snapshot, duplicate-key JSON, safe prose, schema loader, atomic writer, and generic diagnostic patterns; do not create a second general framework.
- Do not import v1/v2/v3 product modules in ways that weaken package-only installed execution or the verified private snapshot import boundary.
- No alias, substring, fuzzy, or prose-semantic matching. Only exact normalized signals and exact closed gate tokens may bind evidence.
- No candidate identity/contact/private analytics/credentials/HTML/source paths/snapshots/raw source prose in generated candidate-matrix/packet artifacts, HTML, receipt, diagnostics, client delivery, or attestation. Canonical `sources.json` may contain only the exact synthetic public URLs required by the existing target-research schema; no generated output may project them.
- `ready_for_manual_authorization` means private draft review only; `external_action_authorized=false` always.
- No JavaScript, forms, buttons, external links/assets, upload/export/apply controls, tracking pixel, or external action.
- Keep recruiter practice/reply-triage precedence above the packet route.
- Preserve existing v1/v2/no-market renderer bytes and the historical installed 39/9 case IDs and totals exactly.
- Preserve all existing installed-attestation keys and values; add only the six packet fields from spec §16.
- From the first plugin-tree commit through manifest-only A, the only permitted non-green source result is the exact named stale-attestation test `FullPluginIntegrationTests.test_checked_in_attestation_is_bound_to_immutable_git_archive_evidence`; run it separately, require its single expected binding failure, and require every other test green. On B, that test and the complete official validator must be green.
- Superdesign output is never copied wholesale. Translate only the approved hierarchy and repository tokens; omit the generated grid background, example facts, and any design detail that conflicts with the spec.
- Do not claim visual, print-preview, or assistive-technology QA unless empirically run.
- Do not perform LinkedIn/profile edits, recruiter contact, messaging, applications, uploads, publishing, purchases, enrollment, scheduling, calendar writes, or any other external career action.

## Task 1: Candidate fact matrix contract

**Files:**

- Create: `plugins/professional-growth-coach/schemas/candidate-fact-matrix-v1.schema.json`
- Create: `plugins/professional-growth-coach/scripts/build_candidate_fact_matrix_v1.py`
- Create: `plugins/professional-growth-coach/scripts/validate_candidate_fact_matrix_v1.py`
- Create: `tests/test_candidate_fact_matrix_v1.py`
- Modify: `plugins/professional-growth-coach/tests/run_static_checks.py`
- Modify: `tests/test_plugin_structure.py`
- Modify: `tests/test_full_plugin.py`

### 1.1 Write the focused contract matrix first

- [ ] Add tests for the exact six top-level fields, exact source/fact row fields, closed objects, bounds, contiguous IDs, locale/timestamp agreement, ordering, uniqueness, weakest evidence propagation, forbidden zero-signal conditional, constraint-only contradiction, and full-artifact source recomputation.
- [ ] Add source-type/evidence-state compatibility tests: only `verified_record` may be `verified`; candidate-authored/profile/CV/portfolio/interview sources reject a caller upgrade to verified.
- [ ] Add positive tests for safe security vocabulary (`authentication`, `certificate_management`, `key_rotation`, professional certificate names).
- [ ] Add negative tests for identity/contact/private analytics/authentication secrets, URLs, HTML, controls, duplicate-key JSON, recursive/oversized/exception mappings, mutability after capture, crossed locale/timestamp, unknown source ordinals, and tampered snapshots.
- [ ] Name the production behavior that would make each test fail; use real builders/validators rather than mocks.

Run the focused class and confirm RED because the three production files do not exist:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest -v tests.test_candidate_fact_matrix_v1
```

### 1.2 Implement the minimal closed schema and projector

- [ ] Mirror the existing bounded snapshot/canonical JSON patterns used by `build_career_next_action_eligibility_v1.py` without importing mutable caller objects after capture.
- [ ] Expose explicit builder, validator, and snapshot functions named consistently with existing v1 modules.
- [ ] Assign `FS-###` and `F-###` only after input validation; preserve source/fact order and lexicographic signal order.
- [ ] Recompute evidence state using `unknown < inferred < candidate_reported < verified` and generate `snap-candidate-facts-sha256-...` from the canonical raw input.
- [ ] Return fixed generic diagnostics and never echo a source value or exception.
- [ ] Register the schema and scripts in the package/static inventories, including callable-interface checks.

### 1.3 Verify and commit

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest -v tests.test_candidate_fact_matrix_v1
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest -v tests.test_plugin_structure tests.test_full_plugin.FullPluginIntegrationTests.test_static_checker_exists_and_passes
PYTHONDONTWRITEBYTECODE=1 python3 -B plugins/professional-growth-coach/tests/run_static_checks.py
git diff --check
```

Expected commit:

```bash
git add plugins/professional-growth-coach/schemas/candidate-fact-matrix-v1.schema.json plugins/professional-growth-coach/scripts/build_candidate_fact_matrix_v1.py plugins/professional-growth-coach/scripts/validate_candidate_fact_matrix_v1.py plugins/professional-growth-coach/tests/run_static_checks.py tests/test_candidate_fact_matrix_v1.py tests/test_plugin_structure.py tests/test_full_plugin.py
git commit -m "feat: add candidate fact matrix contract"
```

## Task 2: Vacancy-bound packet contract and canonical fixtures

**Files:**

- Create: `plugins/professional-growth-coach/schemas/private-vacancy-application-packet-v1.schema.json`
- Create: `plugins/professional-growth-coach/scripts/build_private_vacancy_application_packet_v1.py`
- Create: `plugins/professional-growth-coach/scripts/validate_private_vacancy_application_packet_v1.py`
- Create: `tests/test_private_vacancy_application_packet_v1.py`
- Create: `tests/evals/with-skill/fixtures/private-vacancy-application-packet-v1/{ready-es,ready-en,revise-missing-es,revise-review-en,stop-constraint-es,stop-constraint-en}/sources.json`
- Create: the builder-generated `candidate-fact-matrix.json` and `application-packet.json` siblings in each scenario directory
- Modify: `plugins/professional-growth-coach/tests/run_static_checks.py`
- Modify: `tests/test_plugin_structure.py`
- Modify: `tests/test_full_plugin.py`

### 2.1 Write the complete rule-engine RED matrix

- [ ] Build test helpers from existing canonical target-research, dossier, market, gap-response, gap-assessment, provider, and eligibility builders; never hand-author derived eligibility/packet output.
- [ ] Test exact top-level/row fields, bounds, IDs, joins, common locale/date, target binding, source snapshots, and no second vacancy selector.
- [ ] Exercise all six ordered coverage/confidence rules, including usable verified `signal_relation=unknown` with and without admissible support.
- [ ] Exercise `use`, `revise`, and `omit`; ensure required partial/missing/conflicting/review-required rows create null-draft claim-review rows and `revision_claim_ids` equals every revise/omit row.
- [ ] Exercise readiness precedence: verified gate contradiction -> `stop`; any required non-supported evidence -> `revise_first`; complete admissible evidence -> `ready_for_manual_authorization`.
- [ ] Assert verified gate contradictions trigger stop only when the constraint is clear and non-superseded; conflicting and superseded constraints do not trigger stop.
- [ ] Assert an all-optional/all-missing or otherwise zero-affirmative-claim packet is `revise_first`, never vacuously ready.
- [ ] Assert stop suppression, handoff availability/suppression, tracking proposal state, fixed approval boundary, manual review true, external action false.
- [ ] Assert exact literal matching rejects alias/substrings/caller prose and never converts a non-packet eligibility action into stop.
- [ ] Add crossed/tampered mutation cases for all seven eligibility-group values and both fact-group values; include hostile mappings, duplicate JSON, one-pass capture, size/recursion/exception, and generic/no-echo behavior.

Run and confirm RED on missing packet modules:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest -v tests.test_private_vacancy_application_packet_v1
```

### 2.2 Implement the packet source capture, schema, and deterministic projection

- [ ] Capture exactly `{eligibility_group, candidate_fact_group}` once, freeze it, run the existing eligibility validator on its seven values, run the new fact validator on its two values, and project only from that frozen group.
- [ ] Return an opaque immutable `ValidatedPrivateVacancyPacket` snapshot that carries the frozen composite and projected artifact; its constructor is private to the validator and no artifact-only validation entry point exists.
- [ ] Resolve the selected active vacancy, title, organization display label, requirements, and gate tokens through exact existing joins.
- [ ] Implement the spec's ordered total coverage/confidence table, admissible fact definition, deterministic surface caps/order, closed ES/EN copy tables, claim review, readiness precedence, stop suppression, handoff, tracking proposal, approval boundary, and four snapshot bindings.
- [ ] Do not accept any caller-authored derived copy or target selector.

### 2.3 Generate and pin the six canonical scenario directories

- [ ] Store one complete locale-matched `sources.json` per scenario with only synthetic role/organization/fact values.
- [ ] Generate both sibling artifacts exclusively through source-tree production builders. Installed-builder provenance is proved later by Tasks 7–8.
- [ ] Test byte-for-byte canonical reconstruction and complete path inventory. Source fixtures may contain only the exact synthetic public URLs required by the existing target-research schema; generated candidate-matrix and packet artifacts must contain zero identity/contact/private analytics/URL/secret material.

### 2.4 Verify and commit

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest -v tests.test_candidate_fact_matrix_v1 tests.test_private_vacancy_application_packet_v1
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest -v tests.test_learning_eligibility_v3
PYTHONDONTWRITEBYTECODE=1 python3 -B plugins/professional-growth-coach/tests/run_static_checks.py
git diff --check
```

Expected commit:

```bash
git add plugins/professional-growth-coach/schemas/private-vacancy-application-packet-v1.schema.json plugins/professional-growth-coach/scripts/build_private_vacancy_application_packet_v1.py plugins/professional-growth-coach/scripts/validate_private_vacancy_application_packet_v1.py plugins/professional-growth-coach/tests/run_static_checks.py tests/test_private_vacancy_application_packet_v1.py tests/test_plugin_structure.py tests/test_full_plugin.py tests/evals/with-skill/fixtures/private-vacancy-application-packet-v1
git commit -m "feat: build vacancy application packet"
```

## Task 3: Atomic JSON writer and CLI receipt

**Files:**

- Create: `plugins/professional-growth-coach/scripts/write_private_vacancy_application_packet_v1.py`
- Create: `tests/test_write_private_vacancy_application_packet_v1.py`
- Modify: `plugins/professional-growth-coach/tests/run_static_checks.py`
- Modify: `tests/test_plugin_structure.py`
- Modify: `tests/test_full_plugin.py`

### 3.1 Write writer/CLI RED tests

- [ ] Assert successful canonical UTF-8 JSON from `ValidatedPrivateVacancyPacket`, mode-0600 temp file, fsync/replace, resolved output path, and exact eight-key receipt.
- [ ] Assert invalid/tampered/crossed inputs, destination failures, ordinary exceptions, hostile mappings, duplicate JSON, and receipt mismatches yield fixed exit-2 diagnostics with no stdout, source/path/exception echo, temp residue, or partial destination.
- [ ] Assert existing destination bytes survive a failed replacement and successful replacement returns the exact resolved destination.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest -v tests.test_write_private_vacancy_application_packet_v1
```

### 3.2 Implement the smallest writer/CLI

- [ ] Reuse the repository's existing private atomic writer pattern and duplicate-key loader.
- [ ] The public CLI captures the complete composite once and obtains `ValidatedPrivateVacancyPacket`; the internal JSON writer accepts only that opaque snapshot. Validate/build completely in memory before opening a destination; serialize once; create the temporary file in the destination directory; fsync, atomic replace, and finally clean up.
- [ ] Emit only `artifact_type`, `schema_version`, `locale`, `readiness_state`, `vacancy_id`, `output_path`, `private_draft`, and `external_action_authorized` after replace succeeds.

### 3.3 Verify and commit

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest -v tests.test_write_private_vacancy_application_packet_v1 tests.test_private_vacancy_application_packet_v1
PYTHONDONTWRITEBYTECODE=1 python3 -B plugins/professional-growth-coach/tests/run_static_checks.py
git diff --check
```

Expected commit:

```bash
git add plugins/professional-growth-coach/scripts/write_private_vacancy_application_packet_v1.py plugins/professional-growth-coach/tests/run_static_checks.py tests/test_write_private_vacancy_application_packet_v1.py tests/test_plugin_structure.py tests/test_full_plugin.py
git commit -m "feat: write private application packet"
```

## Task 4: Offline HTML renderer and product surface

**Files:**

- Create: `plugins/professional-growth-coach/assets/private-vacancy-application-packet-v1.html`
- Create: `plugins/professional-growth-coach/assets/private-vacancy-application-packet-v1.css`
- Create: `plugins/professional-growth-coach/scripts/render_private_vacancy_application_packet_v1.py`
- Create: `tests/test_render_private_vacancy_application_packet_v1.py`
- Modify: `.superdesign/design-system.md`
- Modify: `.superdesign/resume.json`
- Modify: `.superdesign/init/components.md`
- Modify: `.superdesign/init/layouts.md`
- Modify: `.superdesign/init/routes.md`
- Modify: `.superdesign/init/theme.md`
- Modify: `.superdesign/init/pages.md`
- Modify: `.superdesign/init/extractable-components.md`
- Modify: `plugins/professional-growth-coach/tests/run_static_checks.py`

### 4.1 Write renderer RED tests from the semantic contract

- [ ] Assert exact one `<h1>`, one focusable `main#main-content`, labelled section/article landmarks, stable unique IDs, definition lists, semantic requirement/draft lists, and one real claim-review table with caption/thead/scoped headers/localized names.
- [ ] Assert exactly one readiness decision; visible state text independent of color; ES/EN deterministic copy; DOM order equals spec §8.
- [ ] Assert stop output suppresses draft materials, claim table, handoff detail, and proposed tracking detail while retaining bounded stop reasons and explicit no-action boundary.
- [ ] Assert all dynamic text is escaped and HTML contains no candidate/source/snapshot IDs, paths, URLs, raw enums, forms, buttons, scripts, external links/resources, upload/export/apply controls, caller-authored derived prose, or unprojected source prose. Exact validated `fact_text` used by closed templates remains allowed.
- [ ] Assert CSP, noindex/referrer metadata, dark mode, forced-colors, reduced-motion, mobile, print, print atomicity, and repeated private/no-action boundary rules are present statically.
- [ ] Pin the existing historical v1/v2/no-market HTML bytes in the same run.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest -v tests.test_render_private_vacancy_application_packet_v1
```

### 4.2 Translate the approved Superdesign hierarchy into repository-native assets

- [ ] Use the draft only for the compact editorial hierarchy: decision hero, context facts, coverage cards, unsupported evidence, private drafts, claim table, handoff, tracking proposal, and approval boundary.
- [ ] Use only existing paper/surface/ink/forest/coral/line/system-sans tokens and repository spacing/card patterns.
- [ ] Omit the generated grid background, sample role/metrics/facts, wide `1180px` shell, and any unsupported copy. Use the compact triage shell width and spec-localized closed copy.
- [ ] Have the full validator return an opaque immutable validated-packet snapshot only after recomputing against the complete composite. Build the renderer from that opaque snapshot; expose no artifact-only validation path; read CSS/template only after validation; return one string.
- [ ] In the in-process packet workflow, capture the composite once and pass the same opaque snapshot to the JSON writer and HTML renderer/writer. Standalone CLI paths capture the artifact and complete source group together. Add a hostile one-pass test proving JSON, HTML, and receipt cannot come from different captures.
- [ ] Mirror shipped asset bytes into Superdesign init documentation and update the design-system description; do not modify the generated remote draft.

### 4.3 Verify and commit

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest -v tests.test_render_private_vacancy_application_packet_v1 tests.test_write_private_vacancy_application_packet_v1
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest -v tests.test_career_market_learning_dossier
PYTHONDONTWRITEBYTECODE=1 python3 -B plugins/professional-growth-coach/tests/run_static_checks.py
git diff --check
```

Expected commit:

```bash
git add plugins/professional-growth-coach/assets/private-vacancy-application-packet-v1.html plugins/professional-growth-coach/assets/private-vacancy-application-packet-v1.css plugins/professional-growth-coach/scripts/render_private_vacancy_application_packet_v1.py plugins/professional-growth-coach/tests/run_static_checks.py tests/test_render_private_vacancy_application_packet_v1.py .superdesign/design-system.md .superdesign/resume.json .superdesign/init/components.md .superdesign/init/layouts.md .superdesign/init/routes.md .superdesign/init/theme.md .superdesign/init/pages.md .superdesign/init/extractable-components.md
git commit -m "feat: render private application packet"
```

## Task 5: Skill routing and identity-free client delivery

**Files:**

- Modify: `plugins/professional-growth-coach/skills/professional-growth-coach/SKILL.md`
- Modify: `plugins/professional-growth-coach/skills/professional-growth-coach/references/routing.md`
- Modify: `plugins/professional-growth-coach/skills/optimize-career-assets/SKILL.md`
- Modify: `plugins/professional-growth-coach/skills/optimize-career-assets/references/asset-workflow.md`
- Modify: `plugins/professional-growth-coach/README.md`
- Create: `tests/test_private_vacancy_application_packet_routing.py`
- Modify: `tests/test_plugin_structure.py`
- Modify: `tests/test_full_plugin.py`

### 5.1 Write routing/client-delivery RED tests

- [ ] Pin precedence: recruiter practice and reply triage remain higher; otherwise an exact validated composite with recomputed `prepare_private_vacancy_packet` routes to `optimize-career-assets`.
- [ ] Assert missing composite members yield a bounded private-evidence request rather than an untyped packet or fallthrough.
- [ ] Assert execution proof requires validated JSON, validated HTML, and exact CLI receipt from the same captured source group.
- [ ] Assert client delivery exposes exactly `private_packet_summary`, `readiness_decision`, `verified_local_artifact`, and `approval_boundary`, ends with localized “No external action is performed.”, and omits candidate/router/module/internal/source/snapshot/raw-prose fields.
- [ ] Pin the existing textual `application_claim_review_matrix` evaluator behavior while replacing the old prose-only packet field list with the versioned schema reference.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest -v tests.test_private_vacancy_application_packet_routing
```

### 5.2 Implement the minimum documentation/routing migration

- [ ] Add one explicit root branch, its required inputs, its precedence, its proof contract, and the exact delivery exception.
- [ ] Replace the older identity-bearing application packet prose contract in `optimize-career-assets` with the new identity-free schema; retain claim truthfulness, no-outcome, consent, and exact action-and-target authorization boundaries.
- [ ] Update README inventories/entry points without presenting drafts as authorization.

### 5.3 Verify and commit

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest -v tests.test_private_vacancy_application_packet_routing tests.test_plugin_structure tests.test_full_plugin.FullPluginIntegrationTests.test_static_checker_exists_and_passes
PYTHONDONTWRITEBYTECODE=1 python3 -B plugins/professional-growth-coach/tests/run_static_checks.py
git diff --check
```

Expected commit:

```bash
git add plugins/professional-growth-coach/skills/professional-growth-coach/SKILL.md plugins/professional-growth-coach/skills/professional-growth-coach/references/routing.md plugins/professional-growth-coach/skills/optimize-career-assets/SKILL.md plugins/professional-growth-coach/skills/optimize-career-assets/references/asset-workflow.md plugins/professional-growth-coach/README.md tests/test_private_vacancy_application_packet_routing.py tests/test_plugin_structure.py tests/test_full_plugin.py
git commit -m "feat: route private application packets"
```

## Task 6: Exact package, static, and privacy registration

**Files:**

- Modify: `plugins/professional-growth-coach/tests/run_static_checks.py`
- Modify: `scripts/check_repository_privacy.py`
- Modify: `tests/test_repository_privacy.py`
- Modify: `tests/test_plugin_structure.py`
- Modify: `tests/test_full_plugin.py`

### 6.1 Write fail-closed inventory/privacy RED tests

- [ ] Assert every new schema/script/asset/fixture/test path is in the exact appropriate inventory and that missing, extra, symlink, FIFO, socket, device, and non-regular paths fail.
- [ ] Add an exact set of six canonical `sources.json` recognizers. Require the exact root shape, bounds, synthetic provenance, source recomputation of both artifacts, and exact sibling equality.
- [ ] Add near misses for unregistered path, nested private values, mutated fact prose, crossed group, coordinated rebuild, tampered sibling, extra/missing key, and unsafe file type; each must fall back to the generic scanner and report only sanitized path/rule/count.
- [ ] Ensure safe projections still scan candidate fact text, target research, and packet copy rather than discarding source content.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest -v tests.test_repository_privacy tests.test_plugin_structure tests.test_full_plugin.FullPluginIntegrationTests.test_static_checker_exists_and_passes
```

### 6.2 Implement closed registrations only

- [ ] Extend existing exact inventories and recognizers; no suffix allowlist, path-prefix ignore, broad exclusion, or early-return bypass.
- [ ] Rebuild canonical sources through production functions inside the checker and scan the bounded safe projections.
- [ ] Preserve fixed generic diagnostics and zero source-value echo.

### 6.3 Verify and commit

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest -v tests.test_repository_privacy
PYTHONDONTWRITEBYTECODE=1 python3 -B scripts/check_repository_privacy.py
PYTHONDONTWRITEBYTECODE=1 python3 -B plugins/professional-growth-coach/tests/run_static_checks.py
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest -v tests.test_plugin_structure tests.test_full_plugin.FullPluginIntegrationTests.test_static_checker_exists_and_passes
git diff --check
```

Expected commit:

```bash
git add plugins/professional-growth-coach/tests/run_static_checks.py scripts/check_repository_privacy.py tests/test_repository_privacy.py tests/test_plugin_structure.py tests/test_full_plugin.py
git commit -m "test: register private packet release surface"
```

## Task 7: Additive installed packet matrix and independent attestation binding

**Files:**

- Modify: `scripts/run_installed_learning_eligibility_v3_smokes.py`
- Modify: `tests/test_plugin_structure.py`
- Modify: `tests/test_full_plugin.py`
- Modify: `scripts/run_release_validation.sh`
- Modify: `plugins/professional-growth-coach/README.md`
- Modify: `docs/release-validation.md`

### 7.1 Write installed-harness RED tests

- [ ] Add exact accepted case IDs `packet_ready_es`, `packet_ready_en`, `packet_revise_missing_es`, `packet_revise_review_en`, `packet_stop_constraint_es`, `packet_stop_constraint_en` and the exact twelve rejected IDs from spec §14.1.
- [ ] Assert all packet cases execute modules and renderer from `verified_private_snapshot_only`; source/cache/original paths are poisoned after snapshot and cannot satisfy lazy or transitive imports.
- [ ] Assert accepted packet artifacts are outputs of installed builders/validators/renderers, not repository fixtures; assert rejected cases fail generically with no echo/partial output.
- [ ] Assert the receipt preserves historical accepted/rejected totals and IDs as 39/9 and exposes a separate ordered 6/12 packet matrix and provenance.
- [ ] Extend the attestation parser to require exactly the prior field set plus six packet keys, independently derive commit/tree/archive/version/count/digest expectations, and reject missing/extra/duplicate/reordered/stale/unresolved/crossed values.
- [ ] Update `docs/release-validation.md` to preserve the historical 39/9 contract and document the separate packet 6/12 fields; add a static/full-plugin behavioral assertion that parses the documented field set rather than grepping prose.
- [ ] Add an opt-in `ALLOW_STALE_INSTALLED_ATTESTATION=1` path to `scripts/run_release_validation.sh`. It must run the named real-attestation test alone and require exactly its known binding failure, then run every other package/root test and gate green. The default path remains strict and fully green; any other failure or use after B is an error.
- [ ] Add `JobSearchCoachPluginStructureTests.test_release_runner_stale_attestation_opt_in_is_exact_and_bounded` as a real subprocess test. It must prove default mode remains strict, invalid opt-in values reject, the opt-in accepts only the fully qualified named assertion, every other package/root test still executes, any additional failure rejects, and opt-in rejects once the named attestation test is green on B.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest -v tests.test_plugin_structure.JobSearchCoachPluginStructureTests.test_installed_smoke_runs_private_packet_matrix_from_installed_root tests.test_plugin_structure.JobSearchCoachPluginStructureTests.test_installed_smoke_receipt_preserves_semantic_matrix_and_parity tests.test_plugin_structure.JobSearchCoachPluginStructureTests.test_release_runner_stale_attestation_opt_in_is_exact_and_bounded tests.test_full_plugin.FullPluginIntegrationTests.test_vacancy_first_attestation_parser_requires_complete_fresh_task_7_evidence tests.test_full_plugin.FullPluginIntegrationTests.test_static_checker_exists_and_passes
```

### 7.2 Implement the additive installed proof

- [ ] Extend the installed synthetic fixture/source loader minimally so it builds all packet scenarios in memory without importing the mutable checkout.
- [ ] Run schema/interface/static checks and both semantic matrices entirely under the existing private snapshot import context and minimal isolated child environments.
- [ ] Compose one closed receipt with separate matrices; do not publish a misleading 45/21 total.
- [ ] Bind the real checked-in attestation file to independently recomputed Git/archive expectations during the official source gate.

### 7.3 Verify and commit

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest -v tests.test_plugin_structure.JobSearchCoachPluginStructureTests.test_installed_smoke_runs_private_packet_matrix_from_installed_root tests.test_plugin_structure.JobSearchCoachPluginStructureTests.test_installed_smoke_receipt_preserves_semantic_matrix_and_parity tests.test_plugin_structure.JobSearchCoachPluginStructureTests.test_release_runner_stale_attestation_opt_in_is_exact_and_bounded tests.test_full_plugin.FullPluginIntegrationTests.test_vacancy_first_attestation_parser_requires_complete_fresh_task_7_evidence tests.test_full_plugin.FullPluginIntegrationTests.test_static_checker_exists_and_passes
PYTHONDONTWRITEBYTECODE=1 python3 -B scripts/check_repository_privacy.py
PYTHONDONTWRITEBYTECODE=1 python3 -B plugins/professional-growth-coach/tests/run_static_checks.py
git diff --check
```

Expected commit:

```bash
git add scripts/run_installed_learning_eligibility_v3_smokes.py scripts/run_release_validation.sh tests/test_plugin_structure.py tests/test_full_plugin.py plugins/professional-growth-coach/README.md docs/release-validation.md
git commit -m "test: bind installed private packet evidence"
```

## Task 8: Whole-branch verification and release

**Files:**

- Modify once: `plugins/professional-growth-coach/.codex-plugin/plugin.json` (manifest-only commit A)
- Modify once after exact install: `tests/evals/final/installed-smoke-test.md` (attestation-only commit B)
- Modify only if required by verified release evidence: existing release report/ledger files outside functional commits

### 8.1 Independent whole-branch review

- [ ] Generate one review package from the branch merge base through Task 7 HEAD.
- [ ] Dispatch the most capable reviewer with the spec, plan ledger, deferred findings, and exact diff package.
- [ ] If findings exist, dispatch exactly one fix agent for the complete list, then one scoped re-review. Do not implement controller-side fixes.

### 8.2 Fresh source gates before the cachebuster

Use the repository's documented locked `VALIDATION_PYTHON` override where the fresh local venv cannot be created. Do not claim a fresh bootstrap unless it actually succeeds.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest -q tests.test_candidate_fact_matrix_v1 tests.test_private_vacancy_application_packet_v1 tests.test_write_private_vacancy_application_packet_v1 tests.test_render_private_vacancy_application_packet_v1 tests.test_private_vacancy_application_packet_routing tests.test_learning_eligibility_v3 tests.test_semantic_provenance_v2 tests.test_career_learning_decision tests.test_career_market_learning_dossier tests.test_plugin_structure tests.test_repository_privacy
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s plugins/professional-growth-coach/tests -p 'test*.py' -q
PYTHONDONTWRITEBYTECODE=1 python3 -B plugins/professional-growth-coach/tests/run_static_checks.py
PYTHONDONTWRITEBYTECODE=1 python3 -B scripts/check_repository_privacy.py
ALLOW_STALE_INSTALLED_ATTESTATION=1 CODEX_SYSTEM_SKILLS_ROOT="$CODEX_SYSTEM_SKILLS_ROOT" VALIDATION_PYTHON="$VALIDATION_PYTHON" PYTHONDONTWRITEBYTECODE=1 bash scripts/run_release_validation.sh
```

- [ ] Run the broad source suite with the one named real-attestation binding selector omitted and require exit 0/final `OK`; run that selector alone and require exactly its known binding assertion to fail. Require zero privacy findings, exact expected adversarial probe handling, clean diff, and zero bytecode before any release mutation. Any second failing selector blocks release.

### 8.3 Create and verify manifest-only A

- [ ] Capture the sole release timestamp with `date -u +%Y%m%d%H%M%S`, then use `apply_patch` exactly once to replace only the manifest's `version` value with `0.2.0+codex.<captured UTC timestamp>`. There is no checked-in cachebuster helper in this repository; do not invent a script or use a second timestamp. If `apply_patch` is denied, verify zero diff before one authorized retry.
- [ ] Audit the version as one UTC cachebuster line and the diff as exactly the manifest path.
- [ ] Rerun structure/full-plugin, static, privacy, source discovery, and official release validation on exact A. Isolate only the expected stale installed-attestation freshness/binding test; every other test must be green.
- [ ] Commit only the manifest as `chore: bump professional growth coach version`.
- [ ] Push the authorized `git push origin HEAD:main`, fetch, and verify live `origin/main` equals A before installation.

### 8.4 Install exact A and verify immutable parity

- [ ] Precheck the public checkout is clean, detached/ancestral, with zero local-only commits; align it safely to exact A.
- [ ] Install only `professional-growth-coach@codex-marketplace-public`; require exactly one enabled row at the exact version.
- [ ] Resolve only the exact public cache-family/plugin/version path; reject latest/glob/sort/delete/config-edit shortcuts.
- [ ] Compare immutable A `git archive` extraction with the exact cache: sorted inventory, every SHA-256, aggregate digest, `diff -qr`, regular path/symlink/private metadata/bytecode checks.
- [ ] Run installed historical 39/9 and additive packet 6/12 smokes entirely from the verified private snapshot and record the closed receipt.

### 8.5 Create attestation-only B and finish

- [ ] Update only `tests/evals/final/installed-smoke-test.md`, preserving every historical field/value contract and adding exactly the six packet fields from spec §16.
- [ ] Validate the real file with independently derived A commit/tree/archive/version/file-count/digest values and negative controls for missing, extra, duplicate, reordered IDs, stale/unresolved commits, wrong tree/version/count/digest, and crossed source/cache values.
- [ ] Commit only the attestation as `test: attest installed private packet release`.
- [ ] Run the complete official validator on B; require package/root/static/privacy/skill/plugin gates green.
- [ ] Push the authorized `git push origin HEAD:main`, fetch, and verify remote/public checkout exact B.
- [ ] Reconfirm the installed exact enabled row, A archive/cache parity, receipt/parser, clean status/diff, and zero bytecode.
- [ ] Record empirical limits: no visual/print-preview/AT claim unless run; no external career action performed.

## Final verification checklist

- [ ] `git status --short` empty.
- [ ] `git diff --check` silent.
- [ ] No `__pycache__`, `.pyc`, or `.pyo` in source, archive, or installed cache.
- [ ] All task reports and reviews are present in this plan's ignored SDD workspace.
- [ ] Every ledger ruling is surfaced in the final handoff with its cost if wrong.
- [ ] Live remote main, clean public checkout, feature worktree, and attestation B agree.
- [ ] Installed selector remains exactly one enabled public row at A's version.
- [ ] Historical 39/9 and packet 6/12 remain separate, fully enumerated, and bound to the same installed package evidence.
- [ ] No external career action was executed.
