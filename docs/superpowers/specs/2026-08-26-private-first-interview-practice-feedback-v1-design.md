# Private first-interview practice feedback v1

## Goal

Close the private first-interview practice loop after the existing board-to-
session handoff. A later explicit answer becomes one ephemeral
`feedback_available` session with bounded, categorical coaching and no numeric
readiness claim.

## Contract

`build_private_first_interview_practice_feedback(handoff, answer)` accepts only
the exact `ValidatedPrivateFirstInterviewPracticeHandoff` in
`awaiting_answer` state. It revalidates the handoff session and its
`snap-practice-board-sha256-...` binding, rejects empty, unsafe, stale, crossed,
or repeated input with one generic diagnostic, and returns an opaque validated
feedback proof. The answer is held only in the in-memory session projection;
`storage=ephemeral`, `raw_answer_retained=false`, and `local_save_mode=disabled`
remain immutable.

The projection emits exactly one of `solid`, `confirm`, or `do_not_assert`,
keeps `score=unknown` and `score_state=categorical`, and cites only `OBS-001`
and `RB-001`. The classifier is a deterministic shape cue, not semantic
verification or an interview prediction. The renderer uses its existing fixed
bilingual copy and never renders the answer, IDs, digest, or snapshot.

When action and result cues are both present, bounded negation or uncertainty
cues downgrade the label to `confirm`. A positive action-plus-result answer
remains `solid`; action without a result remains `confirm`; and an answer
without enough action evidence remains `do_not_assert`. This is a
conservative diagnostic guard, not semantic verification.

The exact handoff is reserved atomically for one successful feedback
projection. Replay and concurrent reuse fail closed; invalid input releases
the reservation and does not consume the handoff.

## Experience

For sourced sessions, the reading order prioritizes the question and next safe
action, then answer structure and review; the compact origin receipt follows
the review. No form, link, control, script, network resource, save, or external
action is introduced. Existing print, dark, forced-colors, reduced-motion, and
employment-continuity boundaries remain unchanged.

## Acceptance

- Exact handoff identity, binding, state, and no-replay checks fail closed.
- Safe Spanish and English answers produce one valid categorical observation.
- Unsafe prose never appears in diagnostics or output HTML.
- The v2 session validator accepts the projection and rejects numeric scores.
- HTML omits raw answer text, internal identifiers, and provenance metadata.
- Existing practice, board, package, privacy, and release checks remain green.
