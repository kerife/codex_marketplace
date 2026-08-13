# Public marketplace follow-ups

This release is statically ready. The items below are deliberately deferred
so they can be handled in a separate cycle without blocking publication.

The practice light-theme border token now meets the 3:1 non-text contrast
floor against both white and the paper surface; browser and print confirmation
remain part of the visual-QA follow-up below.

LinkedIn fixture validation now rejects nesting deeper than the bounded parser
limit with a deterministic error instead of allowing an API-level recursion
failure. The dossier progress-track contrast improvement and browser/print
confirmation remain deferred below.

The dossier light progress track now uses a dedicated token with at least 3:1
contrast against both white and paper surfaces; browser and print confirmation
remain deferred.

LinkedIn validator diagnostics now escape control characters in untrusted field
paths, priority codes, and unexpected copy headings. Generic priority rejection
messages also use a fixed diagnostic and no longer echo arbitrary report text.
The remaining visual and accessibility follow-ups stay separate.

The outcomes CSV CLI now uses the shared descriptor-anchored 256 KiB input
boundary and rejects symlinked, non-regular, oversized, and invalid UTF-8
inputs before parsing.

1. Run real browser QA for keyboard skip navigation, 320px/200% reflow,
   dark mode, forced colors, reduced motion, and print pagination. The current
   evidence is source/render-contract based; no browser screenshot is claimed.
   The forced-colors surface mappings landed in this release, but still need
   OS-level visual confirmation.
2. Decide whether the dossier utility action group needs a visual browser pass
   after its navigation-landmark correction; keep it an action group, not a
   navigation landmark, unless it gains actual links.
3. Consider a separate full-suite harness pass for the few long-running root
   tests that time out under broad discovery; the focused plugin, static,
   privacy, and installed-release gates are green for this release.
4. Add contextual accessible labels to the dossier copy buttons so screen
   reader users can distinguish the three cards.
5. Correct the dossier utility action group from a misleading navigation
   landmark to an explicit action group, then run the visual browser pass.

The public repository must keep the release gates green before each follow-up:
plugin tests, static checks, privacy scan, Superdesign parity, and installed
smoke validation.
