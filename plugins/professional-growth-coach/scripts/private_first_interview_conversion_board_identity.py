"""Opaque proof identity for the private first-interview conversion board."""

from __future__ import annotations

import json


_CONSTRUCTOR_TOKEN = object()


class ValidatedPrivateFirstInterviewConversionBoard:
    """Immutable proof issued only after source and projection validation."""

    __slots__ = ("__artifact_json", "__source_group_json")

    def __new__(
        cls,
        token: object = None,
        artifact_json: str = "",
        source_group_json: str = "",
    ):
        if token is not _CONSTRUCTOR_TOKEN:
            raise TypeError(
                "validated private first-interview conversion board construction is private"
            )
        return super().__new__(cls)

    def __init__(
        self,
        token: object = None,
        artifact_json: str = "",
        source_group_json: str = "",
    ) -> None:
        if token is not _CONSTRUCTOR_TOKEN:
            raise TypeError(
                "validated private first-interview conversion board construction is private"
            )
        object.__setattr__(
            self,
            "_ValidatedPrivateFirstInterviewConversionBoard__artifact_json",
            artifact_json,
        )
        object.__setattr__(
            self,
            "_ValidatedPrivateFirstInterviewConversionBoard__source_group_json",
            source_group_json,
        )

    def __setattr__(self, name: str, value: object) -> None:
        raise AttributeError(
            "validated private first-interview conversion board is immutable"
        )

    @property
    def artifact(self) -> dict[str, object]:
        value = json.loads(self.__artifact_json)
        if not isinstance(value, dict):
            raise RuntimeError("validated private first-interview conversion board is unavailable")
        return value

    @property
    def source_group(self) -> dict[str, object]:
        value = json.loads(self.__source_group_json)
        if not isinstance(value, dict):
            raise RuntimeError("validated private first-interview conversion board is unavailable")
        return value


def _issue_validated_private_first_interview_conversion_board(
    artifact_json: str, source_group_json: str
) -> ValidatedPrivateFirstInterviewConversionBoard:
    return ValidatedPrivateFirstInterviewConversionBoard(
        _CONSTRUCTOR_TOKEN, artifact_json, source_group_json
    )


def _validation_payload_json(value: object) -> tuple[str, str]:
    """Return frozen payloads only for the exact proof-object class."""
    if type(value) is not ValidatedPrivateFirstInterviewConversionBoard:
        raise TypeError(
            "validated private first-interview conversion board is unavailable"
        )
    return (
        value._ValidatedPrivateFirstInterviewConversionBoard__artifact_json,
        value._ValidatedPrivateFirstInterviewConversionBoard__source_group_json,
    )
