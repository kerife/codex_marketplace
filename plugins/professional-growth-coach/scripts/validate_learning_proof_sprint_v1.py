#!/usr/bin/env python3
"""Validate source-recomputed private learning-proof sprint artifacts."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any


def _sibling(name: str) -> Any:
    path = Path(__file__).with_name(name)
    if path.stem == "learning_proof_sprint_identity":
        origin = os.path.realpath(os.fspath(path))
        module_name = "_pgc_learning_proof_sprint_identity_" + hashlib.sha256(origin.encode("utf-8")).hexdigest()
        existing = sys.modules.get(module_name)
        if existing is not None:
            return existing
    else:
        module_name = path.stem if path.stem == "private_prose_safety" else f"_pgc_{path.stem}"
    specification = importlib.util.spec_from_file_location(module_name, path)
    if specification is None or specification.loader is None:
        raise RuntimeError("learning proof sprint dependency is unavailable")
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


_builder = _sibling("build_learning_proof_sprint_v1.py")
_snapshot = _sibling("semantic_provenance_snapshot.py")
_schema_validation = _sibling("validate_json_schema_subset.py")
_loader = _sibling("private_input_loader.py")
_identity = _sibling("learning_proof_sprint_identity.py")
_SCHEMA_PATH = Path(__file__).parents[1] / "schemas" / "learning-proof-sprint-v1.schema.json"
_MISMATCH = "learning proof sprint does not match validated sources"
_MAX_INPUT_BYTES = 512 * 1024
ValidatedLearningProofSprint = _identity.ValidatedLearningProofSprint


class LearningProofSprintLoadError(ValueError):
    """Raised for a fixed, no-echo private sprint load failure."""


def _schema() -> dict[str, object]:
    value = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("learning proof sprint is invalid")
    return value


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _validated_snapshot(value: Mapping[str, object], source_group: Mapping[str, object]) -> ValidatedLearningProofSprint:
    return _identity._issue_validated_learning_proof_sprint(
        _canonical_json(value), _canonical_json(source_group)
    )


def _validate_from_frozen(frozen: Mapping[str, object]) -> ValidatedLearningProofSprint:
    try:
        value = frozen["value"]
        source_group = frozen["source_group"]
        if (
            not isinstance(value, Mapping)
            or not isinstance(source_group, Mapping)
            or _schema_validation.validate_schema_instance(value, _schema())
        ):
            raise ValueError(_MISMATCH)
        expected = _builder._project_from_frozen(source_group)
        if _canonical_json(value) != _canonical_json(expected):
            raise ValueError(_MISMATCH)
        return _validated_snapshot(value, source_group)
    except Exception:
        raise ValueError(_MISMATCH) from None


def validate_learning_proof_sprint_v1(value: object, source_group: object) -> ValidatedLearningProofSprint:
    """Return an opaque proof only after source and artifact recomputation agree."""
    try:
        frozen = _snapshot.bounded_plain_snapshot({"value": value, "source_group": source_group})
        return _validate_from_frozen(frozen)
    except Exception:
        raise ValueError(_MISMATCH) from None


def build_validated_learning_proof_sprint_v1(source_group: object) -> ValidatedLearningProofSprint:
    """Capture one source group, build its artifact, and issue one opaque proof."""
    try:
        frozen_source_group = _snapshot.bounded_plain_snapshot(source_group)
        value = _builder._project_from_frozen(frozen_source_group)
        return _validate_from_frozen({"value": value, "source_group": frozen_source_group})
    except Exception:
        raise ValueError(_MISMATCH) from None


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate key")
        result[key] = value
    return result


def _revalidate_validated_learning_proof_sprint(value: object) -> dict[str, object]:
    try:
        artifact_json, source_group_json = _identity._validation_payload_json(value)
        if len(artifact_json.encode("utf-8")) > _MAX_INPUT_BYTES or len(source_group_json.encode("utf-8")) > _MAX_INPUT_BYTES:
            raise ValueError(_MISMATCH)
        artifact = json.loads(artifact_json, object_pairs_hook=_unique_object)
        source_group = json.loads(source_group_json, object_pairs_hook=_unique_object)
        frozen = _snapshot.bounded_plain_snapshot({"value": artifact, "source_group": source_group})
        _validate_from_frozen(frozen)
        if not isinstance(frozen["value"], dict):
            raise ValueError(_MISMATCH)
        return frozen["value"]
    except Exception:
        raise ValueError(_MISMATCH) from None


def load_learning_proof_sprint_v1(path: Path) -> dict[str, object]:
    """Load one bounded closed artifact without claiming source validation."""
    try:
        if path.is_symlink():
            raise ValueError("symlink input")
        raw = _loader.read_bounded_bytes(path, _MAX_INPUT_BYTES)
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object)
        frozen = _snapshot.bounded_plain_snapshot({"value": value})["value"]
        if not isinstance(frozen, dict) or _schema_validation.validate_schema_instance(frozen, _schema()):
            raise ValueError("learning proof sprint is invalid")
        return frozen
    except Exception:
        raise LearningProofSprintLoadError("cannot load learning proof sprint") from None
