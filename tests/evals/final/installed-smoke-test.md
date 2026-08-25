# Installed synthetic smoke attestation

no_real_profile_mapping: true

This attestation binds the installed vacancy-first release to immutable commit
A and its exact plugin tree. The case is synthetic, repository-only, and does
not map any real profile, recruiter, employer, or account.

## Closed release contract

attestation_state: `vacancy_first_installed_green`

plugin_identity: `professional-growth-coach@codex-marketplace-public`

source_commit: `6d45d4bb0916446cb956d50caf63d1d52c97feda`

source_tree: `199639e7128494ecc2a0625ce5952792ef262e9e`

installed_cache_family: `codex-marketplace-public/professional-growth-coach`

installed_cache_version: `0.2.0+codex.20260825051725`

installed_cache_resolution: `exact_enabled_reported_version_not_alias_or_glob`

source_file_count: `162`

installed_file_count: `162`

sorted_relative_inventory_equal: `true`

per_file_sha256_equal: `true`

source_aggregate_sha256: `9715c4228f9b3321747226d2302694d990749222ca607d083d587dcc2b8359aa`

cache_aggregate_sha256: `9715c4228f9b3321747226d2302694d990749222ca607d083d587dcc2b8359aa`

source_bytecode_count: `0`

installed_bytecode_count: `0`

source_pycache_directory_count: `0`

installed_pycache_directory_count: `0`

source_verification_matrix: `passed`

installed_package_static_scope: `passed_repository_conformance_not_bundled`

installed_semantic_accepted_smokes: `39/39`

installed_semantic_rejected_smokes: `9/9`

installed_packet_accepted_smokes: `6/6`

installed_packet_rejected_smokes: `12/12`

installed_packet_accepted_case_ids: `packet_ready_es,packet_ready_en,packet_revise_missing_es,packet_revise_review_en,packet_stop_constraint_es,packet_stop_constraint_en`

installed_packet_rejected_case_ids: `packet_wrong_action,packet_crossed_research,packet_crossed_fact_source,packet_tampered_matrix,packet_tampered_packet,packet_alias_signal,packet_substring_signal,packet_caller_prose,packet_private_value,packet_confidential_claim,packet_hostile_mapping,packet_writer_cli_partial`

installed_packet_artifact_provenance: `validated_installed_builder_output_only`

installed_packet_renderer_provenance: `validated_installed_renderer_output_only`

installed_import_boundary: `verified_private_snapshot_only`

installed_output_atomicity: `passed_generic_no_echo`

visual_browser_assistive_technology_QA: `not_run_not_claimed`

repository_conformance_from_installed_cache: `not_bundled_not_claimed`

external_action_state: `not_executed`

## Publication and resolution evidence

- Cachebuster timestamp: 2026-08-25T05:17:25Z.
- Commit A changed only the plugin manifest, was pushed to remote `main`, and
  was verified by fetch plus a live remote-head lookup before installation.
- The public marketplace source was re-resolved from the exact installed row,
  proved clean and non-divergent, and aligned detached to commit A.
- Installation used only the exact public selector. The resulting row was the
  sole matching row, enabled, and reported the committed version. No manual
  configuration edit, cache deletion, mutable alias, glob, or lexicographic
  cache selection occurred.

## Source verification evidence

- The pre-A source matrix passed 333/333 tests in 3576.499 seconds. The
  checked-in installed-attestation binding was tested separately and correctly
  rejected the prior release with its one fixed stale-contract diagnostic; the
  prior attestation was not rewritten early.
- Skill and plugin validation both passed.
- Plugin package discovery passed 223/223 tests; the final pre-A official run
  completed that phase in 144.015 seconds.
- Repository root discovery passed 1478/1478 tests in 4332.487 seconds with the
  same single installed-attestation binding test deferred. The documented
  locked `VALIDATION_PYTHON` override was used.
- Static validation passed private-schema, dossier-handoff, and package checks.
- Repository privacy passed without findings or sensitive-value echo.
- Post-cachebuster structure/full-plugin verification passed all 275 non-stale
  tests in 2413.866 seconds; the only failure was the same exact binding test
  deferred until this attestation update. The final post-cachebuster official
  run passed package 223/223 in 146.054 seconds and root 1478/1478 in 4411.091
  seconds; post-cachebuster static and privacy validation also passed.
- The unfiltered real binding test and canonical release runner are post-B
  publication gates and are not claimed by this pre-B attestation text.
- A fresh validation-environment bootstrap was blocked by the established
  persistent-install sandbox policy. Every gate used the documented, verified
  locked CPython 3.11.15 arm64 environment with PyYAML 6.0.3.

## Immutable archive and installed package evidence

- Source was extracted from commit A with `git archive`; no mutable-worktree
  content comparison was used.
- Source and cache each contained 162 non-empty sorted POSIX relative files.
  Every path and lowercase per-file SHA-256 matched, and the aggregate digest
  over `path + NUL + file hash + LF` matched on both sides.
- `diff -qr` was silent. Source and cache contained no `.pyc`, `.pyo`,
  `__pycache__`, symlink, or rejected private metadata artifact.
- After parity capture, installed discovery loaded the required closed schemas,
  fixtures, and product interfaces from an independent private snapshot of the
  exact cache bytes. Installed package static checks passed; repository-only
  conformance was correctly not bundled and not claimed.
- Snapshot directories were private and copied files were independent. This
  binds validation against ordinary concurrent cache updates; it does not claim
  isolation from an active same-user process.

## Installed semantic evidence

- Accepted groups: response mapping, recurrence routes, non-learning routes,
  provider lifecycle, the complete ES action matrix, closed EN copy, exact
  provenance unions and snapshots, DOM/ARIA, and historical bytes.
- The 39 accepted cases include public V1 resolving to private V-003 only after
  validation; exact 1/5 and 2/5 recurrence routes; supported, unknown, and
  professional-experience zero-learning states; provider absent, empty,
  choice, L1-to-LP-001, and L2-to-LP-002 states; all 12 action rows; localized
  ES/EN copy including the selection-required row; one named weekly card; and
  pinned historical rendering.
- Rejected groups: provider displacement, private disclosure, forged sources,
  crossed sources, mutable one-pass input, oversized input, exceptional input,
  writer output, and CLI output.
- All 9 rejected cases failed closed with generic diagnostics and no echo.
  Invalid writer and CLI groups left no partial output.
- Every imported product module resolved below the verified cache snapshot;
  no product module or dependency resolved from the mutable checkout or an
  untrusted prior module-search path. Only the snapshot and resolved locked
  runtime/site roots remained eligible. Controller import state was restored
  after the run.
- The private vacancy packet matrix accepted all 6 closed ES/EN readiness cases
  and rejected all 12 crossed, tampered, alias, substring, prose, private-value,
  hostile-mapping, and partial-output cases. JSON and HTML were derived only
  from the installed builder and renderer through one verified private
  snapshot; invalid CLI/writer cases left no partial output.

## Historical compatibility

- v1: 97,805 bytes; SHA-256
  `4dbb6be8e1a95cdcc8f3e937dcca600fb26f9dc53d7ef519027048c73b12316f`.
- v2: 101,282 bytes; SHA-256
  `0232f7d71de6e85f1b18d7407703b7af944c936c9c905b55fd9a3592067d6167`.
- no-market: 48,801 bytes; SHA-256
  `19d85f8a4061ca5eb44746801a2f0094a9109d9d5764e80d515d84bafdfd79d6`.

## Scope boundary

- Superdesign evidence is structural source/canvas evidence from the approved
  private vacancy-packet direction. **Visual QA not run**: no
  empirical browser, print-preview, or assistive-technology QA is claimed.
- No LinkedIn/profile edit, recruiter connection, message, application,
  purchase, enrollment, upload, or other external career action was executed.
- This deterministic synthetic attestation demonstrates release integrity and
  bounded product behavior; it does not establish real-world truth, hiring
  probability, interview probability, or employment outcome.
