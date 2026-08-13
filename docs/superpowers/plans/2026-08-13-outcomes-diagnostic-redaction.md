# Outcomes Diagnostic Redaction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stop malformed outcomes values and identifiers from being echoed in deterministic CLI diagnostics.

**Architecture:** Keep validation logic and JSON shape intact; only replace
untrusted value interpolation with stable row/field messages. Tests remain in
`tests/test_summarize_outcomes.py` and exercise the real subprocess CLI.

**Tech Stack:** Python 3, `unittest`, JSON stderr contract, offline plugin.

## Global Constraints

- Valid summaries and exit codes remain unchanged.
- Errors retain actionable row/field context where available.
- No raw CSV value, candidate ID, application ID, or control sequence appears in affected diagnostics.
- No schema, loader, CSS, or external-action changes.

---

### Task 1: RED tests

**Files:** `tests/test_summarize_outcomes.py`

- [ ] Add subprocess tests for an invalid date sentinel, invalid boolean
  sentinel, duplicate application ID sentinel, and unknown candidate sentinel.
- [ ] Update ordinary expected strings to omit `got ...` and quoted IDs.
- [ ] Run `PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest tests.test_summarize_outcomes -q` and confirm failures contain the current echoed values.

### Task 2: GREEN diagnostics

**Files:** `plugins/professional-growth-coach/scripts/summarize_outcomes.py`

- [ ] Change date errors to `row N: field must be empty or YYYY-MM-DD` and
  `--as-of must be YYYY-MM-DD`.
- [ ] Change boolean errors to `row N: field must be true, false, or empty`.
- [ ] Change duplicate IDs to `row N: duplicate application_id first seen on row M`.
- [ ] Change unknown-candidate errors to `candidate_id not found`.
- [ ] Run the focused tests and confirm all pass without changing valid output.

### Task 3: Gates and release

**Files:** follow-up plan, release provenance and installed attestation.

- [ ] Mark this diagnostic boundary landed and retain browser/OS QA and root
  harness limitations as follow-ups.
- [ ] Run plugin tests, static checks, privacy, official release validation,
  provenance, and `git diff --check`.
- [ ] Commit, cachebust once, rebind provenance, push, reinstall, compare the
  109-file source/cache inventory, and verify the installed validator.
