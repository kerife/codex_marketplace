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

1. Run real browser QA for keyboard skip navigation, 320px/200% reflow,
   dark mode, forced colors, reduced motion, and print pagination. The current
   evidence is source/render-contract based; no browser screenshot is claimed.
   The forced-colors surface mappings landed in this release, but still need
   OS-level visual confirmation.
2. Decide whether the dossier utility action group needs a visual browser pass
   after its navigation-landmark correction; keep it an action group, not a
   navigation landmark, unless it gains actual links.
3. Redact arbitrary generic priority codes in LinkedIn report diagnostics.
   Canonical IDs and controlled claim codes are now safe, but a malformed
   report can still echo arbitrary priority prose in one rejection message.
4. Consider a separate full-suite harness pass for the few long-running root
   tests that time out under broad discovery; the focused plugin, static,
   privacy, and installed-release gates are green for this release.
5. Add control-character escaping to privacy-scan diagnostic paths and review
   the remaining arbitrary priority-code diagnostic sink.

The public repository must keep the release gates green before each follow-up:
plugin tests, static checks, privacy scan, Superdesign parity, and installed
smoke validation.
