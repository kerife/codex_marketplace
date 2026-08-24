#!/usr/bin/env python3
"""Validate source-recomputed private vacancy application packets."""

from __future__ import annotations

import importlib.util
import json
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any


def _sibling(name: str) -> Any:
    path = Path(__file__).with_name(name)
    specification = importlib.util.spec_from_file_location(f"_pgc_{path.stem}", path)
    if specification is None or specification.loader is None:
        raise RuntimeError("private vacancy packet dependency is unavailable")
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


_builder = _sibling("build_private_vacancy_application_packet_v1.py")
_snapshot = _sibling("semantic_provenance_snapshot.py")
_schema_validation = _sibling("validate_json_schema_subset.py")
_loader = _sibling("private_input_loader.py")
_SCHEMA_PATH = (
    Path(__file__).parents[1]
    / "schemas"
    / "private-vacancy-application-packet-v1.schema.json"
)
_MISMATCH = "private vacancy application packet does not match validated sources"
_MAX_INPUT_BYTES = 512 * 1024
_CONSTRUCTOR_TOKEN = object()


class PrivateVacancyApplicationPacketLoadError(ValueError):
    """Raised for a fixed, no-echo packet load failure."""


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


def _schema() -> dict[str, object]:
    value = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("private vacancy application packet is invalid")
    return value


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _validated_snapshot(
    value: Mapping[str, object], source_group: Mapping[str, object]
) -> ValidatedPrivateVacancyPacket:
    return ValidatedPrivateVacancyPacket(
        _CONSTRUCTOR_TOKEN,
        _canonical_json(value),
        _canonical_json(source_group),
    )


def _validate_private_vacancy_packet_from_frozen(
    frozen_group: Mapping[str, object],
) -> ValidatedPrivateVacancyPacket:
    value = frozen_group["value"]
    source_group = frozen_group["source_group"]
    if (
        not isinstance(value, Mapping)
        or not isinstance(source_group, Mapping)
        or _schema_validation.validate_schema_instance(value, _schema())
    ):
        raise ValueError(_MISMATCH)
    expected = _builder._project_private_vacancy_packet_from_frozen(source_group)
    if _canonical_json(value) != _canonical_json(expected):
        raise ValueError(_MISMATCH)
    return _validated_snapshot(value, source_group)


def validate_private_vacancy_application_packet_v1(
    value: object, source_group: object
) -> ValidatedPrivateVacancyPacket:
    """Return opaque validation proof only for one complete captured composite."""
    try:
        frozen = _snapshot.bounded_plain_snapshot(
            {"value": value, "source_group": source_group}
        )
        return _validate_private_vacancy_packet_from_frozen(frozen)
    except Exception:
        raise ValueError(_MISMATCH) from None


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate key")
        result[key] = value
    return result


def load_private_vacancy_application_packet_v1(path: Path) -> dict[str, object]:
    """Load one bounded closed artifact; complete validation still requires sources."""
    try:
        raw = _loader.read_bounded_bytes(path, _MAX_INPUT_BYTES)
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object)
        frozen = _snapshot.bounded_plain_snapshot({"value": value})["value"]
        if (
            not isinstance(frozen, dict)
            or _schema_validation.validate_schema_instance(frozen, _schema())
        ):
            raise ValueError("private vacancy application packet is invalid")
        return frozen
    except Exception:
        raise PrivateVacancyApplicationPacketLoadError(
            "cannot load private vacancy application packet"
        ) from None
