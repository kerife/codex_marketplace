# Dossier article naming

## Goal

Give repeated dossier article landmarks a deterministic accessible name so
screen-reader users can distinguish priority, scorecard, visual-review, and
copy cards while navigating the document.

## Design

Each repeated card keeps its existing visible heading and receives a stable
heading ID. The containing article references that heading with
`aria-labelledby`. IDs are derived only from validated closed keys or stable
numeric positions: priority rank, dimension key, visual key, and copy index.
Questions and other already-labelled landmarks remain unchanged. No visible
copy, CSS, JavaScript, schema, or external action changes.

## Verification

Renderer tests cover Spanish and English output, requiring every repeated card
to have one unique reference that resolves to its own `h3`. Existing renderer,
static, privacy, Superdesign parity, plugin, and installed-release gates remain
required before publication. This is structural evidence; browser and actual
screen-reader QA remain separate follow-ups.
