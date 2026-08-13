# LinkedIn bundle depth boundary

## Goal

Keep malformed LinkedIn fixture bundles from causing an uncontrolled Python
recursion failure in the public validator API while preserving all valid
canonical fixtures and their existing diagnostics.

## Design

`validate_fixture_bundle` performs an iterative container-depth preflight before
recursive schema/privacy validation. A bundle deeper than 64 mapping/list
levels returns the fixed diagnostic `fixture nesting exceeds safe depth limit`.
The preflight is iterative, so it cannot itself overflow while inspecting the
malformed value. JSON loading remains bounded by the existing byte limit; this
change adds a structural bound rather than changing schema fields or valid
fixture content.

## Verification

- A 1,000-level synthetic bundle fails with the fixed diagnostic and no
  `RecursionError`.
- Existing LinkedIn fixture and client-report suites remain green.
- Plugin, static, privacy, release-validator, parity, and installed smoke
  gates must pass before publication.

## Deferred

Control-character escaping in privacy-scan diagnostic paths and the light
dossier progress-track contrast improvement remain separate cycles.
