#!/usr/bin/env python3
"""Opaque proof identity for the sanitized private first-interview board v2."""

from __future__ import annotations

import json


_UNAVAILABLE = "private first-interview conversion board does not match validated sources"


def _proof_boundary():
    constructor_token = object()
    issuer_marker = object()

    class ValidatedPrivateFirstInterviewConversionBoardV2:
        """Immutable v2 proof with private artifact and source-bundle payloads."""

        __slots__ = (
            "__issuer_marker",
            "__artifact_json",
            "__source_group_json",
            "__metadata_json",
        )

        def __new__(
            cls,
            token: object = None,
            artifact_json: str = "",
            source_group_json: str = "",
            metadata_json: str = "",
        ):
            if token is not constructor_token:
                raise TypeError(_UNAVAILABLE)
            return super().__new__(cls)

        def __init__(
            self,
            token: object = None,
            artifact_json: str = "",
            source_group_json: str = "",
            metadata_json: str = "",
        ) -> None:
            if token is not constructor_token:
                raise TypeError(_UNAVAILABLE)
            object.__setattr__(
                self,
                "_ValidatedPrivateFirstInterviewConversionBoardV2__issuer_marker",
                issuer_marker,
            )
            object.__setattr__(
                self,
                "_ValidatedPrivateFirstInterviewConversionBoardV2__artifact_json",
                artifact_json,
            )
            object.__setattr__(
                self,
                "_ValidatedPrivateFirstInterviewConversionBoardV2__source_group_json",
                source_group_json,
            )
            object.__setattr__(
                self,
                "_ValidatedPrivateFirstInterviewConversionBoardV2__metadata_json",
                metadata_json,
            )

        def __setattr__(self, name: str, value: object) -> None:
            raise AttributeError(_UNAVAILABLE)

        @property
        def artifact(self) -> dict[str, object]:
            try:
                value = json.loads(self.__artifact_json)
            except Exception:
                raise RuntimeError(_UNAVAILABLE) from None
            if not isinstance(value, dict):
                raise RuntimeError(_UNAVAILABLE)
            return value

    def issue(
        artifact_json: str, source_group_json: str, metadata_json: str
    ) -> ValidatedPrivateFirstInterviewConversionBoardV2:
        return ValidatedPrivateFirstInterviewConversionBoardV2(
            constructor_token, artifact_json, source_group_json, metadata_json
        )

    def payload(value: object) -> tuple[str, str, str]:
        if type(value) is not ValidatedPrivateFirstInterviewConversionBoardV2:
            raise TypeError(_UNAVAILABLE)
        try:
            marker = value._ValidatedPrivateFirstInterviewConversionBoardV2__issuer_marker
            artifact_json = value._ValidatedPrivateFirstInterviewConversionBoardV2__artifact_json
            source_group_json = value._ValidatedPrivateFirstInterviewConversionBoardV2__source_group_json
            metadata_json = value._ValidatedPrivateFirstInterviewConversionBoardV2__metadata_json
        except AttributeError:
            raise TypeError(_UNAVAILABLE) from None
        if marker is not issuer_marker:
            raise TypeError(_UNAVAILABLE)
        if not all(isinstance(item, str) for item in (artifact_json, source_group_json, metadata_json)):
            raise ValueError(_UNAVAILABLE)
        return artifact_json, source_group_json, metadata_json

    return ValidatedPrivateFirstInterviewConversionBoardV2, issue, payload


(
    ValidatedPrivateFirstInterviewConversionBoardV2,
    _issue_validated_private_first_interview_conversion_board_v2,
    _validation_payload_json,
) = _proof_boundary()
