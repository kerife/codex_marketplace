# Dossier progress-track contrast

## Goal

Make the incomplete light-theme progress track distinguishable as a meaningful
non-text component without changing the dossier markup, score values, ARIA
labels, or dark/forced-color behavior.

## Design

Declare `--progress-track` in the dossier light palette with a minimum 3:1
contrast against both `#ffffff` and the paper surface. Use it for the native
`progress` background and the WebKit progress-bar pseudo-element. Keep the
existing dark-mode overrides, filled-value color, visible numeric fallback,
print rules, and Superdesign CSS dump unchanged except for the synchronized
light token and selectors.

## Verification

- A static RED test fails while the light track has no dedicated token.
- GREEN asserts both contrast ratios and WebKit selector coverage.
- Design-token allowlist, Superdesign parity, renderer, plugin, privacy, static,
  release-validator, and installed smoke gates pass before publication.

## Deferred

Real browser/print/OS contrast confirmation remains a separate visual-QA task.
