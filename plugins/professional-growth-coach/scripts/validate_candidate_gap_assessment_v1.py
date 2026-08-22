#!/usr/bin/env python3
"""Validate and load closed candidate gap assessments."""

from __future__ import annotations

import hashlib
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
        raise RuntimeError("required candidate assessment dependency is unavailable")
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


_builder = _sibling("build_candidate_gap_assessment_v1.py")
_response_validator = _sibling("validate_candidate_gap_response_v1.py")
_snapshot = _sibling("semantic_provenance_snapshot.py")
_schema_validation = _sibling("validate_json_schema_subset.py")
_loader = _sibling("private_input_loader.py")
_SCHEMA_PATH = Path(__file__).parents[1] / "schemas" / "candidate-gap-assessment-v1.schema.json"
_MISMATCH = "candidate gap assessment does not match validated sources"
_MAX_INPUT_BYTES = 256 * 1024


class CandidateGapAssessmentLoadError(ValueError):
    """Raised for a fixed, no-echo candidate assessment load failure."""


def _schema() -> dict[str, object]:
    value = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("candidate gap assessment is invalid")
    return value


def _canonical_json(value: Mapping[str, object]) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _validate_candidate_gap_assessment_from_frozen(
    frozen_group: Mapping[str, object],
) -> list[str]:
    try:
        value = frozen_group["value"]
        response_group = {
            "value": frozen_group["gap_response"],
            "research": frozen_group["research"],
            "market_dossier": frozen_group["market_dossier"],
            "provider_research": frozen_group["provider_research"],
        }
        if (
            not isinstance(value, Mapping)
            or _schema_validation.validate_schema_instance(value, _schema())
            or _response_validator._validate_candidate_gap_response_from_frozen(
                response_group
            )
        ):
            return [_MISMATCH]
        expected = _builder._project_candidate_gap_assessment_from_frozen(
            {
                "research": frozen_group["research"],
                "executive_dossier": frozen_group["executive_dossier"],
                "market_dossier": frozen_group["market_dossier"],
                "gap_response": frozen_group["gap_response"],
                "provider_research": frozen_group["provider_research"],
            }
        )
        if _canonical_json(value) != _canonical_json(expected):
            return [_MISMATCH]
        return []
    except Exception:
        return [_MISMATCH]


def validate_candidate_gap_assessment_v1(
    value: object,
    research: object,
    executive_dossier: object,
    market_dossier: object,
    gap_response: object,
    provider_research: object | None = None,
) -> list[str]:
    """Validate one assessment against its independently supplied source group."""
    try:
        frozen = _snapshot.bounded_plain_snapshot(
            {
                "value": value,
                "research": research,
                "executive_dossier": executive_dossier,
                "market_dossier": market_dossier,
                "gap_response": gap_response,
                "provider_research": provider_research,
            }
        )
        return _validate_candidate_gap_assessment_from_frozen(frozen)
    except Exception:
        return [_MISMATCH]


def snapshot_for_candidate_gap_assessment_v1(value: Mapping[str, object]) -> str:
    """Return the canonical digest for one structurally valid assessment."""
    try:
        frozen = _snapshot.bounded_plain_snapshot({"value": value})["value"]
        if (
            not isinstance(frozen, Mapping)
            or _schema_validation.validate_schema_instance(frozen, _schema())
        ):
            raise ValueError("candidate gap assessment is invalid")
        digest = hashlib.sha256(_canonical_json(frozen).encode("utf-8")).hexdigest()
        return f"snap-gap-assessment-v1-sha256-{digest}"
    except Exception:
        raise ValueError("candidate gap assessment is invalid") from None


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate key")
        result[key] = value
    return result


def load_candidate_gap_assessment_v1(path: Path) -> dict[str, object]:
    """Load one bounded, closed assessment with a fixed failure diagnostic."""
    try:
        raw = _loader.read_bounded_bytes(path, _MAX_INPUT_BYTES)
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object)
        frozen = _snapshot.bounded_plain_snapshot({"value": value})["value"]
        if (
            not isinstance(frozen, dict)
            or _schema_validation.validate_schema_instance(frozen, _schema())
        ):
            raise ValueError("invalid assessment")
        return frozen
    except Exception:
        raise CandidateGapAssessmentLoadError(
            "cannot load candidate gap assessment"
        ) from None
