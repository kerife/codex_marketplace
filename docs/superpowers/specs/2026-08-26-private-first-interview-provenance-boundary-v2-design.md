# Private First-Interview Provenance Boundary v2

## Status

Approved architectural design for the next plugin increment. This increment
adds a secure v2 route while preserving the published v1 contract as a frozen
compatibility surface. The v2 route is private, offline, draft-only, and never
an authorization to message, connect, apply, publish, upload, or schedule.

## Goal

Prevent the private first-interview board from persisting raw source material
or presenting caller-computed provenance as upstream validation. Produce the
same useful decision surface from an opaque validator-issued source bundle,
with explicit provenance state, deterministic sanitization, stronger writer
checks, and a visible trust boundary.

## Scope and non-goals

In scope:

- A closed `private-first-interview-source-bundle-v1` internal proof contract
  and an immutable, opaque `ValidatedPrivateFirstInterviewSourceBundle`.
- A versioned `private-first-interview-conversion-board-v2` schema, identity,
  builder, validator, private writer, renderer, HTML, and CSS.
- A v1-compatible adapter that accepts only the exact published v1 proof
  object and labels the resulting bundle `composition_only`; it must never
  claim upstream attestation.
- An upstream-attested path that accepts only an exact upstream proof object
  issued by the source-bundle validator, plus an explicitly labeled synthetic
  fixture path. Raw mappings and forged duck-typed proofs are rejected by the
  public v2 builder.
- A sanitized projection containing closed provenance metadata but no raw
  source rows, source prose, internal record IDs, or source snapshot in HTML.
- Writer smoke coverage for mode `0600`, force semantics, symlink and
  non-regular targets, parent-directory checks, temporary-file cleanup, and
  installed-cache execution.
- Routing/documentation updates, root starter prompt, Superdesign trust-strip
  references, package/static/privacy/parity checks, and a new installed
  release attestation.

Out of scope:

- Changing the v1 schema, v1 fixtures, v1 validator semantics, or historical
  v1/no-market bytes. v1 is documented as legacy compatibility only.
- Claiming cryptographic authenticity for an upstream proof unless a real
  upstream verifier is present. The proof class is an interface boundary; the
  v2 artifact must expose `composition_only` whenever the v1 adapter is used.
- LinkedIn/Chrome access, recruiter discovery, messages, applications,
  uploads, calendar writes, publishing, purchases, enrollment, or any other
  external career action.
- Persisting or rendering candidate identity, contact details, raw recruiter
  replies, vacancy URLs, confidential prose, credentials, or private analytics.
- Browser, print-preview, or assistive-technology QA without a valid runtime.

## Design decisions

### Compatibility and versioning

The published v1 package remains byte- and API-compatible for existing callers
and historical release tests. New consumers use v2. README routing must make
v2 the recommended path and state that v1 is a frozen legacy contract whose
source-bound JSON may contain historical source data and must not be used for
new persistence. No v1 function silently changes meaning.

### Source proof boundary

`ValidatedPrivateFirstInterviewSourceBundle` is an immutable class with private
payload slots. Its public surface exposes only a bounded metadata view:

```text
source_contract = "private-first-interview-source-bundle-v1"
provenance_state = "upstream_attested" | "synthetic_fixture" | "composition_only"
source_digest = "snap-private-first-interview-v1-sha256-" followed by exactly
64 lowercase hexadecimal characters
source_kinds = ["recruiter_outreach_lab", "quality_gate",
                "first_interview_7_day_plan", "weekly_coach_plan",
                "decision_ladder", "plan_days", "daily_review_logs"]
```

The exact source payload is captured once and retained only inside the proof
object for recomputation; no public property returns it. The v2 builder accepts
only the exact class, not a mapping, serialized JSON, or duck-typed object.
The validator issues `upstream_attested` only from its private upstream-proof
issuer. A fixture issuer may issue `synthetic_fixture` for tests, and the v1
adapter issues `composition_only`; neither state is silently upgraded. A raw,
correctly re-hashed but fabricated group has no accepted public v2 entry point.

### Sanitized artifact

The v2 artifact has these closed top-level fields:

1. `schema_version`, `artifact_kind`, `locale`, and `as_of_date`.
2. `source_provenance` with the contract, state, digest, and fixed source-kind
   labels; it contains no source rows or prose.
3. The v1 projection sections (`decision`, `sequence`, `proof_cards`,
   `risk_checks`, `rehearsal`, `week`, `decision_ladder`, `daily_reviews`) with
   the same cardinalities and localized copy, recomputed from the frozen
   bundle.
4. `approval_boundary` and `delivery` with the existing fixed private booleans.

The `stop` state emits only `decision`, `source_provenance`,
`approval_boundary`, and `delivery`. For non-stop states, all displayed values
come from closed localized tables or bounded, safety-filtered summaries. The
artifact never contains `source_group`, `record_id`, `group_id`, or raw
`fact_summary` values.

### Safety and provenance semantics

- `upstream_attested` means the exact upstream proof class was issued by the
  source validator; it is not a hiring or interview outcome claim.
- `synthetic_fixture` is test-only data and must be visibly labeled as such;
  it is never presented as candidate evidence or an upstream source.
- `composition_only` means the v1 proof was structurally and snapshot bound,
  but upstream origin was not independently attested. The renderer shows this
  as a review warning and never upgrades it.
- Any unsafe source prose, PII, URL, HTML, control character, prompt-injection
  language, secret-looking value, outcome prediction, salary/eligibility/
  availability claim, or external-action instruction fails closed before the
  v2 proof is issued. Errors are fixed and do not echo input.
- The source digest is integrity metadata only. It is not rendered in HTML,
  receipts, diagnostics, starter prompts, or public documentation examples.
- `draft_only=true`, `external_actions_authorized=false`,
  `no_message_action=true`, `no_calendar_action=true`, all raw-retention flags
  false, `local_save_mode=disabled`, and `candidate_review_required=true` are
  mandatory and immutable.

## Interfaces

Create the following exact library interfaces:

```python
issue_validated_private_first_interview_source_bundle(
    source_group: object, *, provenance_state: str
) -> ValidatedPrivateFirstInterviewSourceBundle

adapt_v1_private_first_interview_proof(
    validated_v1: object
) -> ValidatedPrivateFirstInterviewSourceBundle

build_private_first_interview_conversion_board_v2(
    source_bundle: object, *, locale: str = "en", as_of_date: str
) -> ValidatedPrivateFirstInterviewConversionBoardV2

validate_private_first_interview_conversion_board_v2(
    source_bundle_or_artifact: object, *, locale: str = "en", as_of_date: str
) -> ValidatedPrivateFirstInterviewConversionBoardV2

write_private_first_interview_conversion_board_v2(
    validated_board: object, output: Path, *, force: bool = False
) -> WriteReceipt

render_private_first_interview_conversion_board_v2(
    validated_board: object
) -> str
```

The public builder rejects raw source mappings, serialized artifacts, and
caller-authored projection rows. A private test/fixture issuer may create a
`synthetic_fixture` proof only to model an upstream validator; production
documentation must use the v1 adapter and visibly retain `composition_only`
unless a real upstream issuer is integrated.

## File and data flow

1. An upstream validator issues an opaque source bundle, or the explicit v1
   adapter wraps an exact v1 proof as `composition_only`.
2. The v2 builder captures the bundle metadata once, recomputes the localized
   projection, and issues an opaque board proof.
3. The v2 validator rehydrates only private frozen payloads, checks duplicate
   keys, schema, source digest, provenance state, and canonical projection
   equality, then returns a sanitized artifact.
4. The writer revalidates the exact proof before opening output, verifies the
   parent chain is a private directory owned by the current user with no
   group/world write bits, writes through a mode-600 exclusive temporary file,
   fsyncs, atomically replaces only with `force=True`, and removes temporary
   files on every failure.
5. The renderer accepts only the exact v2 proof class and renders a trust strip
   that says “Fuente validada” for `upstream_attested`, “Fuente sintética de
   prueba” for `synthetic_fixture`, or “Procedencia por composición; revisar
   fuente” for `composition_only`, plus “Texto original no almacenado” and
   “Revisión manual requerida”. No digest or IDs are shown.

## Visual product direction

Use the existing `practice_triage` design-token family and the saved
Superdesign editorial hierarchy. Add one compact trust strip directly below
the decision card, before the sequence. It uses an icon-independent text label,
an explicit state word, and a short boundary sentence so state is never
communicated by color alone. The strip must stack at 640px, remain legible in
print/dark/forced-colors modes, honor reduced motion, and repeat the private
boundary in print. It contains no controls, links, forms, scripts, network
resources, digest, IDs, or source prose.

## Testing and acceptance gates

Focused tests must prove:

- v1 fixtures and historical tests remain unchanged and green;
- exact proof identity, immutability, one-capture behavior, bounded metadata,
  and rejection of raw/duck-typed/forged v2 inputs;
- `upstream_attested`, `synthetic_fixture`, and `composition_only` are
  distinct, deterministic, and never silently upgraded;
- v2 JSON has no `source_group` and no raw source values, preserves 1/7/4/7
  projection cardinalities, and suppresses detail in `stop` state;
- unsafe arbitrary confidential prose, PII, secrets, URLs, HTML, controls,
  prompt injection, prediction, salary, eligibility, availability, and action
  language fail with generic no-echo errors;
- renderer output is escaped, semantic, offline, noindex/no-referrer/CSP,
  non-interactive, and omits digest/IDs/source strings;
- writer mode `0600`, force/no-force, symlink/non-regular target, insecure
  parent, temp cleanup, and installed-cache smoke behavior;
- package inventory, static checks, repository privacy, Superdesign token
  parity, source/cache aggregate parity, installed semantic smokes, and the
  immutable release attestation all bind the same published commit.

The release must report the existing static dossier timeout separately if it
recurs, and must not claim browser or assistive-technology QA without direct
evidence.

## Documentation and release

Update the plugin README, root README, routing skill, package inventory,
privacy/static checks, `.superdesign` pages/components/theme/design-system,
fixtures, and installed-smoke attestation. Add one Spanish and one English
starter prompt that explicitly asks for the v2 private board from validated
source context and says not to perform external actions. Do not include raw
source examples, IDs, digests, URLs, or secrets in public docs.

The increment is accepted only after focused and full applicable tests pass,
the exact source/cache parity verifier passes, the plugin is reinstalled in
Codex, `origin/main` contains the attested commit, and post-push clean-state
checks succeed.
