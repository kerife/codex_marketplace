# Private first-interview practice handoff v1

## Goal

Turn the v2 board's single private practice checkpoint into a safe, explicit
handoff to the existing recruiter-practice-session-v2 flow, without copying
source prose, exposing internal provenance, retaining an answer, or enabling
external action.

## User-visible outcome

For a validated v2 board whose decision state is `ready`, the coach can create
one private practice session in `awaiting_answer`. The session asks the exact
validated board question, preserves the validated response structure, keeps the
pre-answer score as `unknown`, and tells the candidate to provide an answer in
a later explicit private request. The board and session remain draft-only and
offline. Non-ready board states do not create a session or invite a response.

## Boundaries

- The handoff accepts only an exact `ValidatedPrivateFirstInterviewConversionBoardV2`.
- The handoff revalidates the proof before reading any artifact fields.
- Only `decision.state=ready` is eligible; `clarify`, `pause`, and `stop` fail
  closed with one generic diagnostic and no partial output.
- The generated session is `recruiter-practice-session-v2`,
  `state=awaiting_answer`, with `observed_answer=null` and categorical feedback
  disabled until a later observed answer.
- The handoff provenance is an internal snapshot bound to the board proof; it
  is never rendered or returned in client-facing copy.
- No raw source text, source digest, internal IDs, URLs, candidate identity,
  controls, scripts, links, saves, messages, calendar actions, applications,
  uploads, or publication are produced.
- Existing dossier and recruiter-reply-triage practice sessions retain their
  current behavior.

## Contract

The new validator/builder pair exposes one opaque validated handoff object:

```python
build_private_first_interview_practice_handoff(
    validated_board: ValidatedPrivateFirstInterviewConversionBoardV2,
) -> ValidatedPrivateFirstInterviewPracticeHandoff
```

The object carries a sanitized `session` mapping with the existing v2 session
shape plus `handoff_context.source=private_first_interview_conversion_board`.
The handoff snapshot is an internal proof binding and is not a session field
that reaches rendering. The session's fixed rubric uses context, action,
observed result, and boundary; it does not score readiness or predict an
interview outcome.

## Visual behavior

The board practice checkpoint uses one state modifier:

- `ready`: practice is available in a later private request;
- `clarify`: name the missing fact before practicing;
- `pause`: wait for manual review and a useful change;
- `stop`: suppress all preparation detail as today.

The HTML stays static and offline. State copy is localized, the decision is
still the first reading unit, and the visible no-send/share/publish boundary
remains adjacent to the practice instruction.

## Verification

- TDD tests prove exact validated-proof input, ready-only eligibility,
  session-v2 shape, one-question/unknown score semantics, privacy redaction,
  generic failures, and preservation of existing session sources.
- Renderer tests prove localized state copy, visual state modifiers, no
  invitation in non-ready states, and no internal provenance leakage.
- Static/package checks prove schemas, docs, CSS, and tests are included.
- Browser, print-preview, and assistive-technology QA remain explicitly
  unrun unless valid empirical evidence is available.
