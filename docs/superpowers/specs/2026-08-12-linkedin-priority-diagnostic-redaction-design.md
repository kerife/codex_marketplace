# LinkedIn priority diagnostic redaction

## Goal

Prevent malformed client-report priority codes from being copied into API or
CLI diagnostics while preserving deterministic rejection and the existing
valid-report behavior.

## Contract

- Generic priority codes are rejected with the fixed message
  `generic priority code is not allowed`.
- The rejected code value is never included in returned errors or stderr,
  including when it contains contact-like or other private text.
- CLI behavior remains exit code 2 with no traceback; valid reports remain
  silent and accepted.
- Control-character escaping remains covered by the existing diagnostics
  contract for other untrusted fields.

## Verification

TDD covers both surfaces: the validator API must omit a sentinel embedded in
an invalid priority code, and the CLI must omit the same sentinel while keeping
the fixed diagnostic and deterministic exit code.
