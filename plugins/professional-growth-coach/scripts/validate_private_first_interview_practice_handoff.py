#!/usr/bin/env python3
"""Build and validate a proof-only handoff into recruiter practice v2."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any


_FAILURE = "private first-interview practice handoff is unavailable"


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


_board_validator = _load(
    "validate_private_first_interview_conversion_board_v2.py",
    "validate_private_first_interview_conversion_board_v2",
)
_session_validator = _load("validate_recruiter_practice_session.py", "validate_recruiter_practice_session")
_identity = _load(
    "private_first_interview_practice_handoff_identity.py",
    "private_first_interview_practice_handoff_identity",
)
ValidatedPrivateFirstInterviewConversionBoardV2 = _board_validator.ValidatedPrivateFirstInterviewConversionBoardV2
ValidatedPrivateFirstInterviewPracticeHandoff = _identity.ValidatedPrivateFirstInterviewPracticeHandoff


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _snapshot(artifact: Mapping[str, object]) -> str:
    digest = hashlib.sha256(_canonical_json(artifact).encode("utf-8")).hexdigest()
    return f"snap-practice-board-sha256-{digest}"


def _session(artifact: Mapping[str, object]) -> dict[str, object]:
    decision_rows = artifact.get("decision")
    if not isinstance(decision_rows, list) or len(decision_rows) != 1 or not isinstance(decision_rows[0], Mapping):
        raise ValueError(_FAILURE)
    decision = decision_rows[0]
    if decision.get("state") != "ready":
        raise ValueError(_FAILURE)
    rehearsal = artifact.get("rehearsal")
    if not isinstance(rehearsal, Mapping):
        raise ValueError(_FAILURE)
    response_structure = rehearsal.get("response_structure")
    if not isinstance(response_structure, str) or not response_structure.strip():
        raise ValueError(_FAILURE)
    locale = artifact.get("locale")
    if locale not in {"es", "en"}:
        raise ValueError(_FAILURE)
    es = locale == "es"
    session: dict[str, object] = {
        "schema_version": "recruiter-practice-session-v2",
        "session_kind": "private_recruiter_practice",
        "ui_locale": locale,
        "content_locale": locale,
        "state": "awaiting_answer",
        "safe_context": {
            "stage": "recruiter_screen",
            "vacancy_state": "safe_summary_provided",
            "summary": "Contexto privado de primera entrevista validado." if es else "Validated private first-interview context.",
        },
        "requirement": {
            "id": "R-001",
            "summary": "Explicar una decisión apoyada sin ampliar su alcance." if es else "Explain one supported decision without expanding its scope.",
            "fact_ids": ["F-001"],
        },
        "question": {
            "id": "Q-001",
            "kind": "screen_opening",
            "text": rehearsal.get("question"),
            "requirement_id": "R-001",
            "fact_ids": ["F-001"],
        },
        "facts": [
            {
                "id": "F-001",
                "state": "candidate_reported",
                "summary": "Una señal de decisión privada está disponible para practicar." if es else "One private decision signal is available for practice.",
            }
        ],
        "observed_answer": None,
        "rubric": {
            "id": "RB-001",
            "criterion": f"{response_structure}; espera la respuesta antes de comentar." if es else f"{response_structure}; wait for the answer before commenting.",
        },
        "feedback": {"score": "unknown", "score_state": "unknown", "observations": []},
        "delivery": {
            "draft_only": True,
            "external_actions_authorized": False,
            "local_save_mode": "disabled",
            "raw_answer_retained": False,
        },
        "handoff_context": {
            "source": "private_first_interview_conversion_board",
            "source_snapshot": _snapshot(artifact),
            "question_rank": 1,
            "question_id": "Q-001",
            "requirement_id": "R-001",
            "fact_ids": ["F-001"],
            "draft_only": True,
            "external_actions_authorized": False,
        },
    }
    errors = _session_validator.validate_session(session)
    if errors:
        raise ValueError(_FAILURE)
    return session


def validate_private_first_interview_practice_handoff(
    board: object,
) -> ValidatedPrivateFirstInterviewPracticeHandoff:
    """Revalidate one exact board proof and issue one opaque awaiting-answer session."""
    try:
        if type(board) is not ValidatedPrivateFirstInterviewConversionBoardV2:
            raise ValueError(_FAILURE)
        artifact = _board_validator._revalidate_validated_private_first_interview_conversion_board_v2(board)
        session = _session(artifact)
        return _identity.issue_validated_private_first_interview_practice_handoff(
            _canonical_json(session), _snapshot(artifact)
        )
    except Exception:
        raise ValueError(_FAILURE) from None
