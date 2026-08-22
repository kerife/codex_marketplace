#!/usr/bin/env python3
"""Validate and load closed candidate gap responses."""

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
        raise RuntimeError("required candidate response dependency is unavailable")
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


_builder = _sibling("build_candidate_gap_response_v1.py")
_snapshot = _sibling("semantic_provenance_snapshot.py")
_schema_validation = _sibling("validate_json_schema_subset.py")
_loader = _sibling("private_input_loader.py")
_SCHEMA_PATH = Path(__file__).parents[1] / "schemas" / "candidate-gap-response-v1.schema.json"
_MISMATCH = "candidate gap response does not match validated sources"
_MAX_INPUT_BYTES = 256 * 1024


class CandidateGapResponseLoadError(ValueError):
    """Raised for a fixed, no-echo candidate response load failure."""


def _schema() -> dict[str, object]:
    value = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("candidate gap response is invalid")
    return value


def _canonical_json(value: Mapping[str, object]) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _validate_candidate_gap_response_from_frozen(
    frozen_group: Mapping[str, object],
) -> list[str]:
    try:
        value = frozen_group["value"]
        research = frozen_group["research"]
        market = frozen_group["market_dossier"]
        provider = frozen_group["provider_research"]
        if (
            not isinstance(value, Mapping)
            or _schema_validation.validate_schema_instance(value, _schema())
        ):
            return [_MISMATCH]
        (
            research,
            market,
            provider,
            research_snapshot,
            market_snapshot,
            provider_snapshot,
        ) = _builder._validate_sources(research, market, provider)
        selection = {
            field: value[field]
            for field in (
                "selected_vacancy_ordinal",
                "selected_signal",
                "relation",
                "selected_provider_ordinal",
            )
        }
        response_input: object = selection
        if value.get("response_state") in {"unavailable", "selection_required"}:
            response_input = None
        expected_state = _builder._selection_state(
            research, market, response_input, provider
        )
        fixed = {
            "locale": research.get("locale"),
            "as_of_date": research.get("as_of_date"),
            "source_research_snapshot": research_snapshot,
            "source_market_snapshot": market_snapshot,
            "source_provider_research_snapshot": provider_snapshot,
            "response_state": expected_state,
        }
        if any(value.get(field) != expected for field, expected in fixed.items()):
            return [_MISMATCH]
        return []
    except Exception:
        return [_MISMATCH]


def validate_candidate_gap_response_v1(
    value: object,
    research: object,
    market_dossier: object,
    provider_research: object | None = None,
) -> list[str]:
    """Validate one response against independently supplied frozen sources."""
    try:
        frozen = _snapshot.bounded_plain_snapshot(
            {
                "value": value,
                "research": research,
                "market_dossier": market_dossier,
                "provider_research": provider_research,
            }
        )
        return _validate_candidate_gap_response_from_frozen(frozen)
    except Exception:
        return [_MISMATCH]


def snapshot_for_candidate_gap_response_v1(value: Mapping[str, object]) -> str:
    """Return the canonical digest for one structurally valid response."""
    try:
        frozen = _snapshot.bounded_plain_snapshot({"value": value})["value"]
        if (
            not isinstance(frozen, Mapping)
            or _schema_validation.validate_schema_instance(frozen, _schema())
        ):
            raise ValueError("candidate gap response is invalid")
        digest = hashlib.sha256(_canonical_json(frozen).encode("utf-8")).hexdigest()
        return f"snap-gap-response-v1-sha256-{digest}"
    except Exception:
        raise ValueError("candidate gap response is invalid") from None


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate key")
        result[key] = value
    return result


def load_candidate_gap_response_v1(path: Path) -> dict[str, object]:
    """Load one bounded, closed response with a fixed failure diagnostic."""
    try:
        raw = _loader.read_bounded_bytes(path, _MAX_INPUT_BYTES)
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object)
        frozen = _snapshot.bounded_plain_snapshot({"value": value})["value"]
        if (
            not isinstance(frozen, dict)
            or _schema_validation.validate_schema_instance(frozen, _schema())
        ):
            raise ValueError("invalid response")
        return frozen
    except Exception:
        raise CandidateGapResponseLoadError("cannot load candidate gap response") from None
