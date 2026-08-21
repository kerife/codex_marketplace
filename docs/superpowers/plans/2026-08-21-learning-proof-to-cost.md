# Proof-to-Cost Learning Card Implementation Plan

**Goal:** expose already validated learning-decision fields that make effort,
cost uncertainty, and bounded signal comparable without changing the bundle.

## Task 1 — TDD renderer projection

- Add table-driven ES/EN tests covering decision basis, cost/time, expected
  signal, and conditional provider source date/unknowns.
- Assert portfolio/no-learning rows do not gain fabricated provider metadata;
  no-market and v1 snapshots remain byte-identical.
- Implement localized labels and escaped paragraphs in
  `_render_learning_decision` only.

## Task 2 — Responsive presentation and regression gates

- Add only the minimal CSS needed for readable proof-to-cost facts on mobile,
  print, dark, forced-colors, and reduced-motion surfaces.
- Update the Superdesign CSS dump in the same change and keep the parity test
  green.
- Run current Python and CPython 3.11 focused suites, v1/market suites,
  repository privacy, static checks, release validation, and diff-check.

## Task 3 — Independent review and release

- Probe provider/no-provider, evaluated/unavailable, ES/EN, malformed bundle,
  raw ID/URL, and no external-control cases.
- Review the exact diff, commit, consume cachebuster once, install and smoke
  the exact selector, rebind provenance, rerun gates, and push/verify `main`.
