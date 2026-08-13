# Professional Growth Coach design system

## Purpose

Office-safe, evidence-first career review surfaces. The interface should make
the decision, safe next action, and boundary visible before secondary context.
It must remain useful when printed, viewed without external assets, or opened
with reduced motion and forced colors.

## Visual language

- Warm paper background with ink text and restrained forest/coral accents.
- Compact receipts use a centered shell, generous gutters, and one fact column
  through 640px; the second column begins at 641px.
- Cards and decision panels stay atomic in print and avoid relying on color
  alone for meaning.
- Focus indicators are explicit, high-contrast, and preserved in forced colors.

## Interaction and content rules

- Every surface has one skip link and one focusable `main#main-content` target.
- Safe next steps and employment boundaries are visible, printable, and never
  replaced by an external navigation dependency.
- Copy is evidence-safe: no private identifiers, local user paths, or secrets
  appear in diagnostics or public examples.
- No external fonts, scripts, or icon services are required by shipped assets.

## Fidelity contract

The shipped HTML/CSS assets under `plugins/professional-growth-coach/assets/`
are the source of truth. `.superdesign/init/layouts.md` and
`.superdesign/init/theme.md` mirror those files byte-for-byte where marked;
parity tests must fail if either artifact drifts.
