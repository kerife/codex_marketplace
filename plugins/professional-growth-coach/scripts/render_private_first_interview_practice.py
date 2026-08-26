#!/usr/bin/env python3
"""Proof-bound render entry points for the private first-interview loop."""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any


_FAILURE = "private first-interview practice renderer is unavailable"
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


_handoff_identity = _load(
    "private_first_interview_practice_handoff_identity.py",
    "private_first_interview_practice_handoff_identity",
)
_feedback_identity = _load(
    "private_first_interview_practice_feedback_identity.py",
    "private_first_interview_practice_feedback_identity",
)
_validator = _load("validate_recruiter_practice_session.py", "validate_recruiter_practice_session")
_renderer = _load("render_recruiter_practice_session.py", "render_recruiter_practice_session")

ValidatedPrivateFirstInterviewPracticeHandoff = _handoff_identity.ValidatedPrivateFirstInterviewPracticeHandoff
ValidatedPrivateFirstInterviewPracticeFeedback = _feedback_identity.ValidatedPrivateFirstInterviewPracticeFeedback


def _proof_session(proof: object, *, feedback: bool) -> dict[str, object]:
    identity = _feedback_identity if feedback else _handoff_identity
    expected_type = (
        ValidatedPrivateFirstInterviewPracticeFeedback
        if feedback
        else ValidatedPrivateFirstInterviewPracticeHandoff
    )
    if type(proof) is not expected_type:
        raise ValueError(_FAILURE)
    session_json, proof_binding = identity.payload(proof)
    if _SNAPSHOT.fullmatch(proof_binding) is None:
        raise ValueError(_FAILURE)
    try:
        session = json.loads(session_json)
    except Exception:
        raise ValueError(_FAILURE) from None
    if not isinstance(session, Mapping):
        raise ValueError(_FAILURE)
    if _validator.validate_session(session):
        raise ValueError(_FAILURE)
    context = session.get("handoff_context")
    if not isinstance(context, Mapping):
        raise ValueError(_FAILURE)
    if context.get("source") != "private_first_interview_conversion_board":
        raise ValueError(_FAILURE)
    if context.get("source_snapshot") != proof_binding:
        raise ValueError(_FAILURE)
    if session.get("state") != ("feedback_available" if feedback else "awaiting_answer"):
        raise ValueError(_FAILURE)
    if feedback:
        answer = session.get("observed_answer")
        feedback_data = session.get("feedback")
        if answer is None or not isinstance(feedback_data, Mapping) or feedback_data.get("score_state") != "categorical":
            raise ValueError(_FAILURE)
    elif session.get("observed_answer") is not None:
        raise ValueError(_FAILURE)
    return dict(session)


def render_private_first_interview_practice_handoff(proof: object) -> str:
    """Render only an exact, pre-answer board handoff proof."""
    try:
        return _renderer.render_session_html(_proof_session(proof, feedback=False))
    except Exception:
        raise ValueError(_FAILURE) from None


def render_private_first_interview_practice_feedback(proof: object) -> str:
    """Render only an exact, post-answer feedback proof."""
    try:
        return _renderer.render_session_html(_proof_session(proof, feedback=True))
    except Exception:
        raise ValueError(_FAILURE) from None
