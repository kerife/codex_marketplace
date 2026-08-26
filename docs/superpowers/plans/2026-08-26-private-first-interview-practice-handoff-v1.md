# Private first-interview practice handoff v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Connect an eligible private first-interview board v2 to one safe recruiter-practice-session-v2 awaiting-answer session.

**Architecture:** Add a proof-only handoff builder/validator that revalidates the existing board object, gates on `ready`, and projects a sanitized session mapping. Extend the existing session v2 provenance contract for this one source, then make the board's static practice checkpoint state-aware without adding controls or persistence.

**Tech Stack:** Python 3, JSON Schema subset, unittest, static HTML/CSS assets, Markdown documentation.

**Spec:** `docs/superpowers/specs/2026-08-26-private-first-interview-practice-handoff-v1-design.md`

## Global Constraints

- Accept only an exact `ValidatedPrivateFirstInterviewConversionBoardV2` and revalidate it before reading artifact fields.
- Only `decision.state=ready` creates a session; `clarify`, `pause`, and `stop` fail closed with a generic diagnostic and no partial output.
- Output exactly one `recruiter-practice-session-v2` session in `awaiting_answer` with `observed_answer=null`, `feedback.score=unknown`, `local_save_mode=disabled`, `raw_answer_retained=false`, `draft_only=true`, and `external_actions_authorized=false`.
- Never expose raw source prose, identity, URLs, internal IDs, digests, snapshots, controls, scripts, or external actions.
- Preserve existing dossier and private recruiter-reply-triage practice behavior.
- Browser, print-preview, and assistive-technology QA remain `not_run_not_claimed`.

### Task 1: Add the proof-only handoff contract

**Files:**
- Create: `plugins/professional-growth-coach/schemas/private-first-interview-practice-handoff-v1.schema.json`
- Create: `plugins/professional-growth-coach/scripts/validate_private_first_interview_practice_handoff.py`
- Create: `plugins/professional-growth-coach/scripts/build_private_first_interview_practice_handoff.py`
- Create: `plugins/professional-growth-coach/tests/test_private_first_interview_practice_handoff.py`
- Create: `plugins/professional-growth-coach/tests/fixtures/private-first-interview-practice-handoff/accepted-es.json`
- Create: `plugins/professional-growth-coach/tests/fixtures/private-first-interview-practice-handoff/accepted-en.json`

**Interfaces:**
- Consumes `ValidatedPrivateFirstInterviewConversionBoardV2` from `validate_private_first_interview_conversion_board_v2.py`.
- Produces `ValidatedPrivateFirstInterviewPracticeHandoff` and `build_private_first_interview_practice_handoff(validated_board)`.

- [ ] **Step 1: Write the failing test**

  Add tests for ready projection, exact proof type, non-ready generic failure, session closed shape, and absence of source prose/digest in the session mapping.

- [ ] **Step 2: Run the focused test and verify RED**

  Run `PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest -q plugins.professional-growth-coach.tests.test_private_first_interview_practice_handoff`.
  Expected: import failure because the handoff module does not yet exist.

- [ ] **Step 3: Write the minimal schema, validator, builder, and identity-free fixtures**

  Reuse the loader and proof revalidation patterns from the v2 board. The builder must return one opaque object, copy only localized question/structure plus fixed session metadata, and reject every state except `ready`.

- [ ] **Step 4: Run the focused test and verify GREEN**

  Run the same command; expected: all new tests pass with no diagnostics containing input values.

- [ ] **Step 5: Commit**

  `git add plugins/professional-growth-coach/schemas/private-first-interview-practice-handoff-v1.schema.json plugins/professional-growth-coach/scripts/validate_private_first_interview_practice_handoff.py plugins/professional-growth-coach/scripts/build_private_first_interview_practice_handoff.py plugins/professional-growth-coach/tests && git commit -m "feat: add private first-interview practice handoff"`

### Task 2: Extend recruiter practice v2 and board state copy

**Files:**
- Modify: `plugins/professional-growth-coach/schemas/recruiter-practice-session-v2.schema.json`
- Modify: `plugins/professional-growth-coach/scripts/validate_recruiter_practice_session.py`
- Modify: `plugins/professional-growth-coach/scripts/render_recruiter_practice_session.py`
- Modify: `plugins/professional-growth-coach/scripts/render_private_first_interview_conversion_board_v2.py`
- Modify: `plugins/professional-growth-coach/assets/private-first-interview-conversion-board-v2.css`
- Modify: `plugins/professional-growth-coach/tests/test_render_recruiter_practice_session.py`
- Modify: `plugins/professional-growth-coach/tests/test_render_private_first_interview_conversion_board_v2.py`

**Interfaces:**
- The existing practice validator accepts the new handoff source only with its exact snapshot pattern and required fields.
- The board renderer adds a state modifier and localized practice availability copy; it does not add controls or links.

- [ ] **Step 1: Write the failing tests**

  Assert the new source validates, existing sources still validate, ready copy is present, non-ready output contains no later-response invitation, and state classes are present in deterministic HTML.

- [ ] **Step 2: Run the focused tests and verify RED**

  Run the two renderer/validator test modules; expected failures identify the missing source contract and state-aware markup.

- [ ] **Step 3: Implement minimal contract and rendering changes**

  Add only the new source enum/pattern and state-specific localized copy/class. Keep `stop` suppression and static CSP/offline behavior unchanged.

- [ ] **Step 4: Run focused tests and verify GREEN**

  Run the two modules plus the new handoff tests; expected all pass.

- [ ] **Step 5: Commit**

  `git add plugins/professional-growth-coach/schemas/recruiter-practice-session-v2.schema.json plugins/professional-growth-coach/scripts plugins/professional-growth-coach/assets/private-first-interview-conversion-board-v2.css plugins/professional-growth-coach/tests && git commit -m "feat: connect private interview practice handoff"`

### Task 3: Document routing and release evidence

**Files:**
- Modify: `plugins/professional-growth-coach/README.md`
- Modify: `plugins/professional-growth-coach/skills/professional-growth-coach/references/routing.md`
- Modify: `.superdesign/design-system.md`

- [ ] **Step 1: Write documentation assertions**

  Extend the existing structure tests to require the handoff name, ready-only rule, one-question/unknown semantics, and explicit no-action boundary.

- [ ] **Step 2: Run documentation tests and verify RED**

  Run the exact structure tests; expected failures identify missing text.

- [ ] **Step 3: Add concise routing, user copy, and structural visual guidance**

  State that the handoff is manual/private, uses the exact board proof, and does not auto-start or retain a response. Record the four state visual meanings and the honest visual-QA boundary.

- [ ] **Step 4: Run documentation/static checks and verify GREEN**

  Run the structure tests and package static checks; expected no new warnings.

- [ ] **Step 5: Commit**

  `git add plugins/professional-growth-coach/README.md plugins/professional-growth-coach/skills/professional-growth-coach/references/routing.md .superdesign/design-system.md && git commit -m "docs: describe private interview practice handoff"`

### Task 4: Review, version, install, attest, and publish

**Files:**
- Modify: `plugins/professional-growth-coach/.codex-plugin/plugin.json`
- Modify: `tests/evals/final/installed-smoke-test.md`

- [ ] **Step 1: Run focused and package verification**

  Run the handoff, practice-session, board renderer, private board, design-token, structure, and full-plugin release-surface tests. Record explicit counts and any inherited timeout without claiming a full green suite.

- [ ] **Step 2: Request an independent code review**

  Review the complete diff against the pre-cycle `origin/main` commit. Fix all Critical/Important findings and rerun affected tests.

- [ ] **Step 3: Bump the plugin version and verify source parity**

  Use a fresh timestamped version, push the candidate to `origin/main`, install it from the exact public selector, and verify 199-file per-file/aggregate parity.

- [ ] **Step 4: Verify the installed cache**

  Run the installed handoff/session/renderer tests from the exact cache directory; capture the count and output.

- [ ] **Step 5: Update immutable attestation and verify it**

  Bind commit, tree, exact cache version, file count, and aggregate digest to `installed-smoke-test.md`; run the immutable archive attestation test.

- [ ] **Step 6: Publish the final attestation**

  Commit and run `git push origin HEAD:main`, then verify `git ls-remote origin refs/heads/main` equals the local final commit.

