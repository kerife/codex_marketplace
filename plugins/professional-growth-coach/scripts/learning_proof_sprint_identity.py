"""Opaque proof identity for one private learning-proof sprint package."""

from __future__ import annotations

import json


_CONSTRUCTOR_TOKEN = object()


class ValidatedLearningProofSprint:
    """Immutable proof that a sprint artifact matches one captured source group."""

    __slots__ = ("__artifact_json", "__source_group_json")

    def __new__(cls, token: object = None, artifact_json: str = "", source_group_json: str = ""):
        if token is not _CONSTRUCTOR_TOKEN:
            raise TypeError("validated learning proof sprint construction is private")
        return super().__new__(cls)

    def __init__(self, token: object = None, artifact_json: str = "", source_group_json: str = "") -> None:
        if token is not _CONSTRUCTOR_TOKEN:
            raise TypeError("validated learning proof sprint construction is private")
        object.__setattr__(self, "_ValidatedLearningProofSprint__artifact_json", artifact_json)
        object.__setattr__(self, "_ValidatedLearningProofSprint__source_group_json", source_group_json)

    def __setattr__(self, name: str, value: object) -> None:
        raise AttributeError("validated learning proof sprint is immutable")

    @property
    def artifact(self) -> dict[str, object]:
        value = json.loads(self.__artifact_json)
        if not isinstance(value, dict):
            raise RuntimeError("validated learning proof sprint is unavailable")
        return value


def _issue_validated_learning_proof_sprint(artifact_json: str, source_group_json: str) -> ValidatedLearningProofSprint:
    return ValidatedLearningProofSprint(_CONSTRUCTOR_TOKEN, artifact_json, source_group_json)


def _validation_payload_json(value: object) -> tuple[str, str]:
    if type(value) is not ValidatedLearningProofSprint:
        raise TypeError("validated learning proof sprint is unavailable")
    return (
        value._ValidatedLearningProofSprint__artifact_json,
        value._ValidatedLearningProofSprint__source_group_json,
    )
