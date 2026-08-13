# Public marketplace quality cycle: diagnostics, boundaries, and visual parity

## Intent

Keep the Professional Growth Coach safe to share from the public marketplace while improving the artifacts users actually review: deterministic diagnostics must not echo private-looking values, LinkedIn inputs must stay inside the bounded no-follow loader contract, and the Superdesign source of truth must describe the same receipt HTML that ships.

## Scope

### 1. LinkedIn diagnostic privacy

Validation errors may identify stable synthetic IDs such as `FACT-JSC1-READY`, `EVID-JSC1-HEADLINE`, and `SOURCE-JSC1-LINKEDIN`. Arbitrary enum values, duplicate references, and duplicate structural IDs are not safe to echo. A centralized diagnostic identifier helper will allow the canonical synthetic identifier grammar and replace every other value with `<redacted-value>`. Existing short, safe diagnostics remain byte-compatible.

### 2. LinkedIn input boundary

The report Markdown and bundle JSON loader paths will use the existing descriptor-anchored, no-follow, bounded reader. The loader will reject intermediate and leaf symlinks, reject non-regular or oversized inputs before parsing, and translate invalid UTF-8 into a generic deterministic input diagnostic. Regular canonical fixtures and duplicate/semantic validation behavior remain unchanged.

### 3. Superdesign HTML parity

The five shipped HTML templates are the visual source of truth. A parity test will extract the corresponding fenced blocks from `.superdesign/init/layouts.md` and compare them byte-for-byte with the shipped assets. The two compact receipt blocks must include the employment-continuity boundary token already emitted by the runtime templates. CSS parity remains covered separately.

## User-visible design direction

The product remains an offline, office-safe artifact system: compact receipts prioritize the decision and safe next step; triage/practice surfaces preserve manual handoff and no-action boundaries; long dossiers remain document-like. No new colors, fonts, network assets, or external UI framework are introduced. Superdesign context files describe actual templates and token values rather than inventing a web application shell.

## TDD acceptance

- Each production behavior begins with a failing regression test demonstrating the leak, unsafe path read, or parity drift.
- Focused tests pass for LinkedIn validators/loaders and Superdesign parity.
- The complete plugin suite, root suite, static checks, privacy scanner, and `git diff --check` pass.
- The public GitHub branch is updated only after those gates pass; Codex installation is refreshed and verified against the published source.

## Follow-up boundaries

Question-kind parity in triage-to-practice handoffs, forced-colors focus fallback on triage/practice, and state-aware triage copy are separate cycles. They should not be mixed into this release unless a new RED test demonstrates a regression in the scoped surfaces.
