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
Invalid official `source_category` values now use a stable diagnostic and never
echo submitted email-like, path-like, or control-character text.
The JSON schema subset validator now redacts sensitive unsupported-field names
and escapes diagnostic controls; ordinary field names remain visible.
The remaining visual and accessibility follow-ups stay separate.

The outcomes CSV CLI now uses the shared descriptor-anchored 256 KiB input
boundary and rejects symlinked, non-regular, oversized, and invalid UTF-8
inputs before parsing.

Outcomes diagnostics now avoid echoing missing paths, duplicate headers, or
invalid window arguments. Shared private-field diagnostics also redact
absolute paths under common system roots while preserving ordinary field names.

The dossier now exposes localized, card-specific accessible names for copy
buttons while preserving their visible labels and live status targets. Its
private utility controls are an explicit action group rather than a misleading
navigation landmark; no visual browser QA is claimed.

Repeated dossier priority, scorecard, visual-review, and copy articles now
reference their visible headings with deterministic `aria-labelledby` IDs.

The dossier and recruiter triage, practice, checkpoint, and conversion
validators now reject deeply nested or cyclic direct-API mappings with stable
nesting-limit errors instead of propagating `RecursionError`.

Compact receipt footers now expose a visible continuity separator and retain
system colors in forced-colors mode. Their stronger high-contrast separator
weight still needs browser/OS confirmation.

1. Run real browser QA for keyboard skip navigation, 320px/200% reflow,
   dark mode, forced colors, reduced motion, and print pagination. The current
   evidence is source/render-contract based; no browser screenshot is claimed.
   The forced-colors surface mappings landed in this release, but still need
   OS-level visual confirmation.
2. Consider a separate full-suite harness pass for the few long-running root
   tests that time out under broad discovery; the focused plugin, static,
   privacy, and installed-release gates are green for this release.
3. Extend bounded-depth and cycle checks to any future public validator APIs;
   the current dossier and recruiter validators are covered.

The public repository must keep the release gates green before each follow-up:
plugin tests, static checks, privacy scan, Superdesign parity, and installed
smoke validation.
