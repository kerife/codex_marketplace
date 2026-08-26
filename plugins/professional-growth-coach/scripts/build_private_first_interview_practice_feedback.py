#!/usr/bin/env python3
"""Create one ephemeral, categorical feedback projection for a practice answer."""

from __future__ import annotations

import copy
import importlib.util
import json
import re
import sys
import unicodedata
from collections.abc import Mapping
from pathlib import Path
from typing import Any


_FAILURE = "private first-interview practice feedback is unavailable"
_SNAPSHOT = re.compile(r"^snap-practice-board-sha256-[0-9a-f]{64}$")
_ACTION = re.compile(
    r"\b(?:implemented?|built|led|designed|redesigned|created|changed|automated|migrated|"
    r"hice|implement(?:e|é)|constru[ií]|lideré|diseñé|creé|cambié|automatiz(?:é|e)|migré)\b",
    re.IGNORECASE,
)
_RESULT = re.compile(
    r"\b(?:result|impact|outcome|reduced|increased|improved|observed|"
    r"resultado|impacto|logro|reduj[eo]|aument[óo]|mejor[óo]|observé|observ[eé])\b",
    re.IGNORECASE,
)


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


_handoff = _load(
    "build_private_first_interview_practice_handoff.py",
    "build_private_first_interview_practice_handoff",
)
_handoff_identity = _load(
    "private_first_interview_practice_handoff_identity.py",
    "private_first_interview_practice_handoff_identity",
)
_session_validator = _load(
    "validate_recruiter_practice_session.py",
    "validate_recruiter_practice_session",
)
_identity = _load(
    "private_first_interview_practice_feedback_identity.py",
    "private_first_interview_practice_feedback_identity",
)
ValidatedPrivateFirstInterviewPracticeHandoff = _handoff.ValidatedPrivateFirstInterviewPracticeHandoff
ValidatedPrivateFirstInterviewPracticeFeedback = _identity.ValidatedPrivateFirstInterviewPracticeFeedback


_STATEMENTS = {
    "es": {
        "solid": "La respuesta conecta una acción con un resultado observado dentro del alcance confirmado.",
        "confirm": "La respuesta presenta una acción útil; confirma el resultado observado antes de ampliarla.",
        "do_not_assert": "Falta una base observable suficiente; reemplaza la afirmación por evidencia o una aclaración acotada.",
    },
    "en": {
        "solid": "The answer connects an action to an observed result within the confirmed scope.",
        "confirm": "The answer presents a useful action; confirm the observed result before expanding it.",
        "do_not_assert": "There is not enough observable basis; replace the claim with evidence or a bounded clarification.",
    },
}


def _classify(answer: str) -> str:
    normalized = unicodedata.normalize("NFKC", answer)
    if _ACTION.search(normalized) and _RESULT.search(normalized):
        return "solid"
    if _ACTION.search(normalized):
        return "confirm"
    return "do_not_assert"


def _answer_is_acceptable(answer: object) -> bool:
    return (
        isinstance(answer, str)
        and bool(answer.strip())
        and len(answer) <= 2000
        and _session_validator.is_safe_prose_text(answer)
    )


def build_private_first_interview_practice_feedback(
    handoff: object, answer: object
) -> ValidatedPrivateFirstInterviewPracticeFeedback:
    """Revalidate one awaiting-answer handoff and return ephemeral feedback."""
    try:
        if type(handoff) is not ValidatedPrivateFirstInterviewPracticeHandoff:
            raise ValueError(_FAILURE)
        if not _answer_is_acceptable(answer):
            raise ValueError(_FAILURE)
        session_json, proof_binding = _handoff_identity.payload(handoff)
        if _SNAPSHOT.fullmatch(proof_binding) is None:
            raise ValueError(_FAILURE)
        session = json.loads(session_json)
        if not isinstance(session, Mapping):
            raise ValueError(_FAILURE)
        if _session_validator.validate_session(session):
            raise ValueError(_FAILURE)
        if session.get("state") != "awaiting_answer" or session.get("observed_answer") is not None:
            raise ValueError(_FAILURE)
        handoff_context = session.get("handoff_context")
        if not isinstance(handoff_context, Mapping):
            raise ValueError(_FAILURE)
        if handoff_context.get("source") != "private_first_interview_conversion_board":
            raise ValueError(_FAILURE)
        if handoff_context.get("source_snapshot") != proof_binding:
            raise ValueError(_FAILURE)

        projected = copy.deepcopy(dict(session))
        locale = projected.get("content_locale") or projected.get("locale")
        if locale not in _STATEMENTS:
            raise ValueError(_FAILURE)
        label = _classify(answer)
        projected["state"] = "feedback_available"
        projected["observed_answer"] = {
            "id": "OBS-001",
            "text": answer,
            "storage": "ephemeral",
        }
        projected["feedback"] = {
            "score": "unknown",
            "score_state": "categorical",
            "observations": [
                {
                    "label": label,
                    "statement": _STATEMENTS[locale][label],
                    "source_refs": ["OBS-001", "RB-001"],
                }
            ],
        }
        if _session_validator.validate_session(projected):
            raise ValueError(_FAILURE)
        return _identity.issue_validated_private_first_interview_practice_feedback(
            json.dumps(projected, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
            proof_binding,
        )
    except Exception:
        raise ValueError(_FAILURE) from None
