#!/usr/bin/env python3
"""Opaque identity for one private first-interview practice handoff."""

from __future__ import annotations

import json
from threading import Lock


_UNAVAILABLE = "private first-interview practice handoff is unavailable"
_CONSTRUCTOR_TOKEN = object()
_ISSUER_MARKER = object()
_STATE_LOCK = Lock()
_IN_FLIGHT: set[object] = set()
_CONSUMED: set[object] = set()


class ValidatedPrivateFirstInterviewPracticeHandoff:
    """Immutable handoff carrying one internally validated session mapping."""

    __slots__ = ("__issuer_marker", "__session_json", "__proof_binding")

    def __new__(cls, token: object = None, session_json: str = "", proof_binding: str = ""):
        if token is not _CONSTRUCTOR_TOKEN:
            raise TypeError(_UNAVAILABLE)
        return super().__new__(cls)

    def __init__(self, token: object = None, session_json: str = "", proof_binding: str = "") -> None:
        if token is not _CONSTRUCTOR_TOKEN:
            raise TypeError(_UNAVAILABLE)
        object.__setattr__(self, "_ValidatedPrivateFirstInterviewPracticeHandoff__issuer_marker", _ISSUER_MARKER)
        object.__setattr__(self, "_ValidatedPrivateFirstInterviewPracticeHandoff__session_json", session_json)
        object.__setattr__(self, "_ValidatedPrivateFirstInterviewPracticeHandoff__proof_binding", proof_binding)

    def __setattr__(self, name: str, value: object) -> None:
        raise AttributeError(_UNAVAILABLE)

    @property
    def session(self) -> dict[str, object]:
        try:
            value = json.loads(self.__session_json)
        except Exception:
            raise RuntimeError(_UNAVAILABLE) from None
        if not isinstance(value, dict):
            raise RuntimeError(_UNAVAILABLE)
        return value


def issue_validated_private_first_interview_practice_handoff(
    session_json: str, proof_binding: str
) -> ValidatedPrivateFirstInterviewPracticeHandoff:
    return ValidatedPrivateFirstInterviewPracticeHandoff(
        _CONSTRUCTOR_TOKEN, session_json, proof_binding
    )


def payload(value: object) -> tuple[str, str]:
    if type(value) is not ValidatedPrivateFirstInterviewPracticeHandoff:
        raise TypeError(_UNAVAILABLE)
    try:
        marker = value._ValidatedPrivateFirstInterviewPracticeHandoff__issuer_marker
        session_json = value._ValidatedPrivateFirstInterviewPracticeHandoff__session_json
        proof_binding = value._ValidatedPrivateFirstInterviewPracticeHandoff__proof_binding
    except AttributeError:
        raise TypeError(_UNAVAILABLE) from None
    if marker is not _ISSUER_MARKER or not isinstance(session_json, str) or not isinstance(proof_binding, str):
        raise ValueError(_UNAVAILABLE)
    return session_json, proof_binding


def reserve_for_feedback(value: object) -> None:
    """Atomically reserve an exact handoff for one feedback projection."""
    payload(value)
    with _STATE_LOCK:
        if value in _IN_FLIGHT or value in _CONSUMED:
            raise ValueError(_UNAVAILABLE)
        _IN_FLIGHT.add(value)


def commit_feedback(value: object) -> None:
    with _STATE_LOCK:
        if value not in _IN_FLIGHT:
            raise ValueError(_UNAVAILABLE)
        _IN_FLIGHT.remove(value)
        _CONSUMED.add(value)


def release_feedback(value: object) -> None:
    with _STATE_LOCK:
        _IN_FLIGHT.discard(value)
