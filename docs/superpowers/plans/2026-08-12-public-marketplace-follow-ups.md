# Public marketplace follow-ups

This release is statically ready. The items below are deliberately deferred
so they can be handled in a separate cycle without blocking publication.

1. Run real browser QA for keyboard skip navigation, 320px/200% reflow,
   dark mode, forced colors, reduced motion, and print pagination. The current
   evidence is source/render-contract based; no browser screenshot is claimed.
2. Add explicit `Highlight` focus-color overrides for the skip targets in the
   triage and practice forced-colors blocks, then synchronize the Superdesign
   theme dump and accessibility contract tests.
3. Decide whether the dossier utility action group needs a visual browser pass
   after its navigation-landmark correction; keep it an action group, not a
   navigation landmark, unless it gains actual links.
4. Consider mapping invalid NUL-byte API paths to the shared generic input
   error. POSIX command-line arguments cannot contain NUL, so this is API
   hardening rather than a marketplace blocker.

The public repository must keep the release gates green before each follow-up:
plugin tests, static checks, privacy scan, Superdesign parity, and installed
smoke validation.
