# Outcomes diagnostic redaction

## Goal

Keep malformed outcomes CSV diagnostics useful without echoing candidate-
supplied values into stderr, logs, or automation artifacts.

## Contract

- Date errors identify the row and field but never include the supplied value.
- Boolean errors identify the row and field but never include the supplied value.
- Duplicate application errors identify the row and first-seen row but never
  include the application ID.
- Unknown candidate selection reports a stable error without echoing the
  requested candidate ID.
- Valid summaries, safety summaries, exit codes, stdout behavior, and existing
  input-boundary errors remain unchanged.

## TDD acceptance

Regression tests use email/path/control-like sentinels in each affected input
and assert the sentinel is absent from JSON stderr while the stable field/row
diagnostic remains. Existing ordinary invalid-input tests are updated to the
new fixed messages.
