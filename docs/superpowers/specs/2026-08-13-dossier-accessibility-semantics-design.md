# Dossier accessibility semantics

## Goal

Make the executive dossier's copy controls distinguishable to assistive
technology and make its private utility controls use the correct landmark
semantics, without changing the visual layout or copy behavior.

## Contract

- Every rendered copy button whose card has a non-null draft keeps the visible
  localized label (`Copiar borrador` or `Copy draft`) and gains a localized,
  card-specific `aria-label`.
- Spanish labels identify the card category, for example
  `Copiar borrador: Titular`; English labels use the equivalent category, for
  example `Copy draft: Headline`.
- Omitted cards remain text-only and expose no copy target or copy button.
- Copy status and confirmation associations remain in `aria-describedby`; the
  clipboard handler, `data-copy-*` attributes, CSP, and private/offline policy
  do not change.
- The header utility container is a `<div class="utility-actions no-print"
  role="group" aria-label="...">`, not a `<nav>`, because it contains a
  privacy status and a print action but no navigation links.
- Existing visual selectors continue to match `.utility-actions`; no CSS or
  Superdesign token changes are required.

## Validation

Renderer tests cover Spanish and English localized accessible names, stable
visible labels, omitted-copy behavior, status/confirmation associations, and
the absence of a misleading utility navigation landmark. Existing dossier
render, privacy, static, and Superdesign parity suites remain green.
