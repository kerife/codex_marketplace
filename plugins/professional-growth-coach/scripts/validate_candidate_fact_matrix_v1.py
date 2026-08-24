#!/usr/bin/env python3
"""Validate and load source-recomputed candidate fact matrices."""

from __future__ import annotations

import importlib.util
import json
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any


def _sibling(name: str) -> Any:
    path = Path(__file__).with_name(name)
    module_name = path.stem if path.stem == "private_prose_safety" else f"_pgc_{path.stem}"
    specification = importlib.util.spec_from_file_location(module_name, path)
    if specification is None or specification.loader is None:
        raise RuntimeError("candidate fact matrix dependency is unavailable")
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


_builder = _sibling("build_candidate_fact_matrix_v1.py")
_snapshot = _sibling("semantic_provenance_snapshot.py")
_prose_safety = _sibling("private_prose_safety.py")
_schema_validation = _sibling("validate_json_schema_subset.py")
_loader = _sibling("private_input_loader.py")
_SCHEMA_PATH = Path(__file__).parents[1] / "schemas" / "candidate-fact-matrix-v1.schema.json"
_MISMATCH = "candidate fact matrix does not match validated sources"
_MAX_INPUT_BYTES = 256 * 1024


class CandidateFactMatrixLoadError(ValueError):
    """Raised for a fixed, no-echo candidate fact matrix load failure."""


def _schema() -> dict[str, object]:
    value = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("candidate fact matrix is invalid")
    return value


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _validate_candidate_fact_matrix_from_frozen(
    frozen_group: Mapping[str, object],
) -> list[str]:
    try:
        value = frozen_group["value"]
        source_group = frozen_group["source_group"]
        if (
            not isinstance(value, Mapping)
            or _schema_validation.validate_schema_instance(value, _schema())
        ):
            return [_MISMATCH]
        expected = _builder._project_candidate_fact_matrix_from_frozen(source_group)
        if _canonical_json(value) != _canonical_json(expected):
            return [_MISMATCH]
        return []
    except Exception:
        return [_MISMATCH]


def validate_candidate_fact_matrix_v1(value: object, source_group: object) -> list[str]:
    """Validate one artifact against the exact captured private input group."""
    try:
        frozen = _snapshot.bounded_plain_snapshot(
            {"value": value, "source_group": source_group}
        )
        return _validate_candidate_fact_matrix_from_frozen(frozen)
    except Exception:
        return [_MISMATCH]


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate key")
        result[key] = value
    return result


def load_candidate_fact_matrix_v1(path: Path) -> dict[str, object]:
    """Load one bounded closed artifact; source recomputation remains validator-only."""
    try:
        raw = _loader.read_bounded_bytes(path, _MAX_INPUT_BYTES)
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object)
        frozen = _snapshot.bounded_plain_snapshot({"value": value})["value"]
        if (
            not isinstance(frozen, dict)
            or _schema_validation.validate_schema_instance(frozen, _schema())
        ):
            raise ValueError("candidate fact matrix is invalid")
        return frozen
    except Exception:
        raise CandidateFactMatrixLoadError("cannot load candidate fact matrix") from None
