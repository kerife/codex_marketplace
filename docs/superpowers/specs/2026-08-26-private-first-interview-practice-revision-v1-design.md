# Private first-interview practice revision v1

## Goal

Close one explicit feedback-to-revision loop without forms, persistence,
numeric scoring, or external action.

## Contract

`build_private_first_interview_practice_revision(feedback)` accepts only an
exact `ValidatedPrivateFirstInterviewPracticeFeedback` proof from the private
first-interview board in `feedback_available` state. It atomically consumes
that proof once and returns a new opaque `ValidatedPrivateFirstInterviewPracticeHandoff`
with `state=awaiting_answer`, `attempt=2`, and `final_attempt=true`.

The new session is constructed from the validated question, rubric, facts,
safe context, delivery boundary, and source snapshot. It sets
`observed_answer=null`, `score=unknown`, `score_state=unknown`, and an empty
observation list. The prior answer, feedback statement, and internal proof
state are never copied into the new session or renderer.

## Acceptance

- Only an exact feedback proof is accepted.
- Replay and concurrent revision requests allow exactly one success.
- Invalid input does not consume the feedback proof.
- A second feedback is terminal; no third revision is available.
- The rendered second attempt clearly states that it is final and that the
  prior answer was not reused.
- Existing first-attempt privacy, proof binding, renderer, and no-external-
  action guarantees remain intact.
