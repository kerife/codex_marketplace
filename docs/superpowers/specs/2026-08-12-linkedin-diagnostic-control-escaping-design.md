# LinkedIn diagnostic control escaping

## Goal

Prevent candidate-supplied Markdown and JSON context from injecting terminal
controls or forged lines into LinkedIn validator diagnostics.

## Design

Reuse the validator's existing Unicode control escaping helper for three
untrusted diagnostic contexts: unexpected copy-section headings, generic
priority codes, and JSON privacy-scan field-path segments. The helper renders
control, format, surrogate, and Unicode line-separator characters as literal
`\u` escapes while preserving ordinary text and existing safe synthetic IDs.
Suspicious field names continue to use the existing redaction policy.

No schema, valid fixture, visible report, or CLI exit-code behavior changes.
Both API-level diagnostics and CLI stderr receive the same safe representation.

## Verification

- API tests cover ESC/LF in a JSON field path, a generic priority code, and an
  unexpected H3 heading.
- CLI regression confirms no raw ESC or injected line is emitted.
- Existing LinkedIn, plugin, static, privacy, release-validator, and installed
  smoke gates remain green.

## Deferred

Contextual accessible labels for dossier copy buttons and browser/OS visual QA
remain separate cycles.
