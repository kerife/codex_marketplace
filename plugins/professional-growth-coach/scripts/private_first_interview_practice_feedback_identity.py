#!/usr/bin/env python3
"""Opaque identity for one ephemeral private interview practice feedback result."""

from __future__ import annotations

import json
import weakref
from threading import Lock


_UNAVAILABLE = "private first-interview practice feedback is unavailable"
_CONSTRUCTOR_TOKEN = object()
_ISSUER_MARKER = object()
_STATE_LOCK = Lock()
_REVISION_IN_FLIGHT: weakref.WeakSet[object] = weakref.WeakSet()
_REVISED: weakref.WeakSet[object] = weakref.WeakSet()


class ValidatedPrivateFirstInterviewPracticeFeedback:
    """Immutable feedback carrying one in-memory session projection."""

    __slots__ = ("__issuer_marker", "__session_json", "__proof_binding", "__weakref__")

    def __new__(cls, token: object = None, session_json: str = "", proof_binding: str = ""):
        if token is not _CONSTRUCTOR_TOKEN:
            raise TypeError(_UNAVAILABLE)
        return super().__new__(cls)

    def __init__(self, token: object = None, session_json: str = "", proof_binding: str = "") -> None:
        if token is not _CONSTRUCTOR_TOKEN:
            raise TypeError(_UNAVAILABLE)
        object.__setattr__(self, "_ValidatedPrivateFirstInterviewPracticeFeedback__issuer_marker", _ISSUER_MARKER)
        object.__setattr__(self, "_ValidatedPrivateFirstInterviewPracticeFeedback__session_json", session_json)
        object.__setattr__(self, "_ValidatedPrivateFirstInterviewPracticeFeedback__proof_binding", proof_binding)

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


def issue_validated_private_first_interview_practice_feedback(
    session_json: str, proof_binding: str
) -> ValidatedPrivateFirstInterviewPracticeFeedback:
    return ValidatedPrivateFirstInterviewPracticeFeedback(
        _CONSTRUCTOR_TOKEN, session_json, proof_binding
    )


def payload(value: object) -> tuple[str, str]:
    if type(value) is not ValidatedPrivateFirstInterviewPracticeFeedback:
        raise TypeError(_UNAVAILABLE)
    try:
        marker = value._ValidatedPrivateFirstInterviewPracticeFeedback__issuer_marker
        session_json = value._ValidatedPrivateFirstInterviewPracticeFeedback__session_json
        proof_binding = value._ValidatedPrivateFirstInterviewPracticeFeedback__proof_binding
    except AttributeError:
        raise TypeError(_UNAVAILABLE) from None
    if marker is not _ISSUER_MARKER or not isinstance(session_json, str) or not isinstance(proof_binding, str):
        raise ValueError(_UNAVAILABLE)
    return session_json, proof_binding


def reserve_revision(value: object) -> None:
    """Atomically reserve one exact feedback proof for a single revision."""
    payload(value)
    with _STATE_LOCK:
        if value in _REVISION_IN_FLIGHT or value in _REVISED:
            raise ValueError(_UNAVAILABLE)
        _REVISION_IN_FLIGHT.add(value)


def commit_revision(value: object) -> None:
    with _STATE_LOCK:
        if value not in _REVISION_IN_FLIGHT:
            raise ValueError(_UNAVAILABLE)
        _REVISION_IN_FLIGHT.discard(value)
        _REVISED.add(value)


def release_revision(value: object) -> None:
    with _STATE_LOCK:
        _REVISION_IN_FLIGHT.discard(value)
