# Public marketplace follow-ups

This release is statically ready. The items below are deliberately deferred
so they can be handled in a separate cycle without blocking publication.

1. Run real browser QA for keyboard skip navigation, 320px/200% reflow,
   dark mode, forced colors, reduced motion, and print pagination. The current
   evidence is source/render-contract based; no browser screenshot is claimed.
2. Decide whether the dossier utility action group needs a visual browser pass
   after its navigation-landmark correction; keep it an action group, not a
   navigation landmark, unless it gains actual links.
3. Extend forced-colors mappings to the practice and triage context, prompt,
   rehearsal, evidence, and boundary surfaces. Current browser/mobile capture
   confirms normal flow and ARIA references, but real OS high-contrast mode was
   unavailable for this cycle.
4. Consider a separate full-suite harness pass for the few long-running root
   tests that time out under broad discovery; the focused plugin, static,
   privacy, and installed-release gates are green for this release.

The public repository must keep the release gates green before each follow-up:
plugin tests, static checks, privacy scan, Superdesign parity, and installed
smoke validation.
