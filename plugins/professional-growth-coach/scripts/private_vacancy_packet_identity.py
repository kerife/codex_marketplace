"""Shared opaque proof identity for one private vacancy packet package root."""

from __future__ import annotations

import json


_CONSTRUCTOR_TOKEN = object()


class ValidatedPrivateVacancyPacket:
    """Opaque immutable proof that an artifact matches one complete source group."""

    __slots__ = ("__artifact_json", "__source_group_json")

    def __new__(
        cls,
        token: object = None,
        artifact_json: str = "",
        source_group_json: str = "",
    ):
        if token is not _CONSTRUCTOR_TOKEN:
            raise TypeError("validated private vacancy packet construction is private")
        return super().__new__(cls)

    def __init__(
        self,
        token: object = None,
        artifact_json: str = "",
        source_group_json: str = "",
    ) -> None:
        if token is not _CONSTRUCTOR_TOKEN:
            raise TypeError("validated private vacancy packet construction is private")
        object.__setattr__(self, "_ValidatedPrivateVacancyPacket__artifact_json", artifact_json)
        object.__setattr__(
            self,
            "_ValidatedPrivateVacancyPacket__source_group_json",
            source_group_json,
        )

    def __setattr__(self, name: str, value: object) -> None:
        raise AttributeError("validated private vacancy packet is immutable")

    @property
    def artifact(self) -> dict[str, object]:
        """Return a detached artifact copy without exposing the frozen composite."""
        value = json.loads(self.__artifact_json)
        if not isinstance(value, dict):
            raise RuntimeError("validated private vacancy packet is unavailable")
        return value


def _issue_validated_private_vacancy_packet(
    artifact_json: str, source_group_json: str
) -> ValidatedPrivateVacancyPacket:
    return ValidatedPrivateVacancyPacket(
        _CONSTRUCTOR_TOKEN,
        artifact_json,
        source_group_json,
    )
