#!/usr/bin/env python3
"""Create one proof-bound, final private practice revision handoff."""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any


_FAILURE = "private first-interview practice revision is unavailable"
_SNAPSHOT = re.compile(r"^snap-practice-board-sha256-[0-9a-f]{64}$")


def _load(name: str, module_name: str) -> Any:
    existing = sys.modules.get(module_name)
    if existing is not None:
        return existing
    path = Path(__file__).with_name(name)
    specification = importlib.util.spec_from_file_location(module_name, path)
    if specification is None or specification.loader is None:
        raise RuntimeError(_FAILURE)
    module = importlib.util.module_from_spec(specification)
    sys.modules[module_name] = module
    specification.loader.exec_module(module)
    return module


_feedback_identity = _load(
    "private_first_interview_practice_feedback_identity.py",
    "private_first_interview_practice_feedback_identity",
)
_handoff_identity = _load(
    "private_first_interview_practice_handoff_identity.py",
    "private_first_interview_practice_handoff_identity",
)
_validator = _load("validate_recruiter_practice_session.py", "validate_recruiter_practice_session")

ValidatedPrivateFirstInterviewPracticeFeedback = _feedback_identity.ValidatedPrivateFirstInterviewPracticeFeedback
ValidatedPrivateFirstInterviewPracticeHandoff = _handoff_identity.ValidatedPrivateFirstInterviewPracticeHandoff


def _copy_mapping(value: object) -> dict[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(_FAILURE)
    return json.loads(json.dumps(dict(value), ensure_ascii=False))


def build_private_first_interview_practice_revision(
    feedback: object,
) -> ValidatedPrivateFirstInterviewPracticeHandoff:
    """Return the one explicit final-attempt handoff without the prior answer."""
    reserved = False
    try:
        if type(feedback) is not ValidatedPrivateFirstInterviewPracticeFeedback:
            raise ValueError(_FAILURE)
        session_json, proof_binding = _feedback_identity.payload(feedback)
        if _SNAPSHOT.fullmatch(proof_binding) is None:
            raise ValueError(_FAILURE)
        session = json.loads(session_json)
        if not isinstance(session, Mapping):
            raise ValueError(_FAILURE)
        if _validator.validate_session(session):
            raise ValueError(_FAILURE)
        if session.get("state") != "feedback_available":
            raise ValueError(_FAILURE)
        if session.get("observed_answer") is None or not isinstance(session.get("feedback"), Mapping):
            raise ValueError(_FAILURE)
        context = session.get("handoff_context")
        if not isinstance(context, Mapping):
            raise ValueError(_FAILURE)
        if context.get("source") != "private_first_interview_conversion_board":
            raise ValueError(_FAILURE)
        if context.get("source_snapshot") != proof_binding:
            raise ValueError(_FAILURE)
        if context.get("attempt", 1) != 1 or context.get("final_attempt") is not None:
            raise ValueError(_FAILURE)

        _feedback_identity.reserve_revision(feedback)
        reserved = True
        revised_context = {
            "source": context["source"],
            "source_snapshot": context["source_snapshot"],
            "question_rank": context["question_rank"],
            "question_id": context["question_id"],
            "requirement_id": context["requirement_id"],
            "fact_ids": list(context["fact_ids"]),
            "draft_only": context["draft_only"],
            "external_actions_authorized": context["external_actions_authorized"],
            "attempt": 2,
            "final_attempt": True,
        }
        revised = {
            "schema_version": session["schema_version"],
            "session_kind": session["session_kind"],
            "ui_locale": session["ui_locale"],
            "content_locale": session["content_locale"],
            "state": "awaiting_answer",
            "safe_context": _copy_mapping(session["safe_context"]),
            "requirement": _copy_mapping(session["requirement"]),
            "question": _copy_mapping(session["question"]),
            "facts": [_copy_mapping(item) for item in session["facts"]],
            "observed_answer": None,
            "rubric": _copy_mapping(session["rubric"]),
            "feedback": {"score": "unknown", "score_state": "unknown", "observations": []},
            "delivery": _copy_mapping(session["delivery"]),
            "handoff_context": revised_context,
        }
        if _validator.validate_session(revised):
            raise ValueError(_FAILURE)
        handoff = _handoff_identity.issue_validated_private_first_interview_practice_handoff(
            json.dumps(revised, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
            proof_binding,
        )
        _feedback_identity.commit_revision(feedback)
        reserved = False
        return handoff
    except Exception:
        if reserved:
            _feedback_identity.release_revision(feedback)
        raise ValueError(_FAILURE) from None
