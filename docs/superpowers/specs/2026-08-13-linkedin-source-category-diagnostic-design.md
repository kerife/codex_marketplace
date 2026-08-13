# LinkedIn source-category diagnostic redaction

## Goal

Prevent malformed LinkedIn fixture values from being copied into validator
diagnostics while preserving useful source-list context and all valid-source
behavior.

## Design

When an official source URL is not registered for its category, the validator
will emit the stable message `official URL is not registered for
source_category` scoped to the source index. It will not include the submitted
category value. Existing enum validation remains responsible for identifying
invalid categories, and valid registered categories keep their current output.

This is deliberately API- and CLI-compatible: the returned error remains a
string, the CLI exit status is unchanged, and no schema, renderer, network, or
credential behavior changes.

## Verification

TDD coverage will exercise API and CLI paths with email-like, local-path-like,
and control-character category values. Each test must prove the supplied
sentinel is absent while the stable source-index diagnostic remains. The
focused LinkedIn suites, full plugin suite, static/privacy checks, official
release validator, source/cache parity, and installed smoke must pass before
publishing the cachebuster.
