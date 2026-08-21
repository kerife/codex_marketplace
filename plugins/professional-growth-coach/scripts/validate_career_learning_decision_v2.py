#!/usr/bin/env python3
"""Validate learning decision v2 bundles through complete source recomputation."""

from __future__ import annotations

import copy
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
        raise RuntimeError("required learning validator dependency is unavailable")
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


_builder = _sibling("build_career_learning_decision_v2.py")
_schema_validation = _sibling("validate_json_schema_subset.py")
_SCHEMA_PATH = Path(__file__).parents[1] / "schemas" / "career-learning-decision-v2.schema.json"
_REQUEST_FIELDS = (
    "decision_rank", "decision_code", "source_signals", "provider_option_id"
)
_MISMATCH = "learning decision does not match validated sources"


def _canonical_json(value: Mapping[str, object]) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _schema() -> dict[str, object]:
    value = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("learning decision schema is invalid")
    return value


def _schema_errors(value: object) -> list[str]:
    if not _builder._bounded_tree(value):
        return [_MISMATCH]
    try:
        return _schema_validation.validate_schema_instance(value, _schema())
    except Exception:
        return [_MISMATCH]


def validate_learning_bundle_v2(
    value: object,
    research: object,
    market_dossier: object,
    executive_dossier: object,
    provider_research: object,
) -> list[str]:
    """Accept only the complete canonical object rebuilt from validated sources."""
    try:
        if _schema_errors(value) or not isinstance(value, Mapping):
            return [_MISMATCH]
        value_copy = copy.deepcopy(value)
        decisions = value_copy.get("decisions")
        if not isinstance(decisions, list):
            return [_MISMATCH]
        requests = []
        for row in decisions:
            if not isinstance(row, Mapping):
                return [_MISMATCH]
            requests.append({field: copy.deepcopy(row[field]) for field in _REQUEST_FIELDS})
        expected = _builder.build_learning_bundle_v2(
            research, market_dossier, executive_dossier, provider_research, requests
        )
        if _canonical_json(value_copy) != _canonical_json(expected):
            return [_MISMATCH]
        return []
    except Exception:
        return [_MISMATCH]


def snapshot_for_learning_bundle_v2(value: Mapping[str, object]) -> str:
    """Return the canonical snapshot for one structurally valid v2 bundle."""
    try:
        if _schema_errors(value) or not isinstance(value, Mapping):
            raise ValueError("learning decision v2 is invalid")
        digest = hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()
        return f"snap-learning-v2-sha256-{digest}"
    except Exception:
        raise ValueError("learning decision v2 is invalid") from None
