# Installed synthetic smoke attestation

no_real_profile_mapping: true

This attestation binds the installed vacancy-first release to immutable commit
A and its exact plugin tree. The case is synthetic, repository-only, and does
not map any real profile, recruiter, employer, or account.

## Closed release contract

attestation_state: `vacancy_first_installed_green`

plugin_identity: `professional-growth-coach@codex-marketplace-public`

source_commit: `e9414f2fb101fa0aa76eb0a7173aeae807f32866`

source_tree: `3a0eec05f365888a3825f2482a577d52d00598aa`

installed_cache_family: `codex-marketplace-public/professional-growth-coach`

installed_cache_version: `0.2.0+codex.20260824020329`

installed_cache_resolution: `exact_enabled_reported_version_not_alias_or_glob`

source_file_count: `151`

installed_file_count: `151`

sorted_relative_inventory_equal: `true`

per_file_sha256_equal: `true`

source_aggregate_sha256: `1458825375258afe42d09ff88ab47fb8f3605135a86a1041bf839c7aef3555f1`

cache_aggregate_sha256: `1458825375258afe42d09ff88ab47fb8f3605135a86a1041bf839c7aef3555f1`

source_bytecode_count: `0`

installed_bytecode_count: `0`

source_pycache_directory_count: `0`

installed_pycache_directory_count: `0`

source_verification_matrix: `passed`

installed_package_static_scope: `passed_repository_conformance_not_bundled`

installed_semantic_accepted_smokes: `39/39`

installed_semantic_rejected_smokes: `9/9`

installed_import_boundary: `verified_private_snapshot_only`

installed_output_atomicity: `passed_generic_no_echo`

visual_browser_assistive_technology_QA: `not_run_not_claimed`

repository_conformance_from_installed_cache: `not_bundled_not_claimed`

external_action_state: `not_executed`

## Publication and resolution evidence

- Cachebuster timestamp: 2026-08-24T02:03:29Z.
- Commit A changed only the plugin manifest, was pushed to remote `main`, and
  was verified by fetch plus a live remote-head lookup before installation.
- The public marketplace source was re-resolved from the exact installed row,
  proved clean and non-divergent, and aligned detached to commit A.
- Installation used only the exact public selector. The resulting row was the
  sole matching row, enabled, and reported the committed version. No manual
  configuration edit, cache deletion, mutable alias, glob, or lexicographic
  cache selection occurred.

## Source verification evidence

- The official source release runner completed successfully with exit 0;
  skill and plugin validation both passed.
- Plugin package discovery: 223/223 tests passed in 141.149 seconds.
- Repository root discovery: 1408/1408 tests passed in 3347.310 seconds.
- Static validation passed private-schema, dossier-handoff, and package checks.
- Repository privacy passed without findings or sensitive-value echo.
- Post-cachebuster structure/full-plugin verification passed 270/270 tests in
  1306.624 seconds; post-cachebuster static validation also passed.
- A fresh validation-environment bootstrap was blocked by the established
  persistent-install sandbox policy. Every gate used the documented, verified
  locked CPython 3.11.15 arm64 environment with PyYAML 6.0.3.

## Immutable archive and installed package evidence

- Source was extracted from commit A with `git archive`; no mutable-worktree
  content comparison was used.
- Source and cache each contained 151 non-empty sorted POSIX relative files.
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

## Historical compatibility

- v1: 97,805 bytes; SHA-256
  `4dbb6be8e1a95cdcc8f3e937dcca600fb26f9dc53d7ef519027048c73b12316f`.
- v2: 101,282 bytes; SHA-256
  `0232f7d71de6e85f1b18d7407703b7af944c936c9c905b55fd9a3592067d6167`.
- no-market: 48,801 bytes; SHA-256
  `19d85f8a4061ca5eb44746801a2f0094a9109d9d5764e80d515d84bafdfd79d6`.

## Scope boundary

- Superdesign evidence is structural source/canvas evidence from the approved
  selection-required navigation-help direction. **Visual QA not run**: no
  empirical browser, print-preview, or assistive-technology QA is claimed.
- No LinkedIn/profile edit, recruiter connection, message, application,
  purchase, enrollment, upload, or other external career action was executed.
- This deterministic synthetic attestation demonstrates release integrity and
  bounded product behavior; it does not establish real-world truth, hiring
  probability, interview probability, or employment outcome.
