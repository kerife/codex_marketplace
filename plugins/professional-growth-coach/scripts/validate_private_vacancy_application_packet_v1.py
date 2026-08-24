#!/usr/bin/env python3
"""Validate source-recomputed private vacancy application packets."""

from __future__ import annotations

import importlib.util
import hashlib
import json
import os
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


def _packet_identity() -> Any:
    path = Path(__file__).with_name("private_vacancy_packet_identity.py")
    origin = os.path.realpath(os.fspath(path))
    module_name = (
        "_pgc_private_vacancy_packet_identity_"
        + hashlib.sha256(origin.encode("utf-8")).hexdigest()
    )
    existing = sys.modules.get(module_name)
    if existing is not None:
        if os.path.realpath(os.fspath(getattr(existing, "__file__", ""))) != origin:
            raise RuntimeError("private vacancy packet identity is unavailable")
        return existing
    specification = importlib.util.spec_from_file_location(module_name, path)
    if specification is None or specification.loader is None:
        raise RuntimeError("private vacancy packet identity is unavailable")
    module = importlib.util.module_from_spec(specification)
    sys.modules[module_name] = module
    try:
        specification.loader.exec_module(module)
    except BaseException:
        if sys.modules.get(module_name) is module:
            del sys.modules[module_name]
        raise
    return module


_builder = _sibling("build_private_vacancy_application_packet_v1.py")
_snapshot = _sibling("semantic_provenance_snapshot.py")
_schema_validation = _sibling("validate_json_schema_subset.py")
_loader = _sibling("private_input_loader.py")
_identity = _packet_identity()
_SCHEMA_PATH = (
    Path(__file__).parents[1]
    / "schemas"
    / "private-vacancy-application-packet-v1.schema.json"
)
_MISMATCH = "private vacancy application packet does not match validated sources"
_MAX_INPUT_BYTES = 512 * 1024
ValidatedPrivateVacancyPacket = _identity.ValidatedPrivateVacancyPacket


class PrivateVacancyApplicationPacketLoadError(ValueError):
    """Raised for a fixed, no-echo packet load failure."""


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
    return _identity._issue_validated_private_vacancy_packet(
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


def build_validated_private_vacancy_application_packet_v1(
    source_group: object,
) -> ValidatedPrivateVacancyPacket:
    """Capture one complete composite, build its packet, and issue one opaque proof."""
    try:
        frozen_source_group = _snapshot.bounded_plain_snapshot(source_group)
        if not isinstance(frozen_source_group, Mapping):
            raise ValueError(_MISMATCH)
        value = _builder._project_private_vacancy_packet_from_frozen(
            frozen_source_group
        )
        return _validate_private_vacancy_packet_from_frozen(
            {"value": value, "source_group": frozen_source_group}
        )
    except Exception:
        raise ValueError(_MISMATCH) from None


def _revalidate_validated_private_vacancy_packet(
    validated_packet: object,
) -> dict[str, object]:
    """Recompute a carried artifact from its full frozen composite for a consumer."""
    try:
        artifact_json, source_group_json = _identity._validation_payload_json(
            validated_packet
        )
        if (
            len(artifact_json.encode("utf-8")) > _MAX_INPUT_BYTES
            or len(source_group_json.encode("utf-8")) > _MAX_INPUT_BYTES
        ):
            raise ValueError(_MISMATCH)
        value = json.loads(artifact_json, object_pairs_hook=_unique_object)
        source_group = json.loads(
            source_group_json, object_pairs_hook=_unique_object
        )
        frozen = _snapshot.bounded_plain_snapshot(
            {"value": value, "source_group": source_group}
        )
        _validate_private_vacancy_packet_from_frozen(frozen)
        frozen_value = frozen["value"]
        if not isinstance(frozen_value, dict):
            raise ValueError(_MISMATCH)
        return frozen_value
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
