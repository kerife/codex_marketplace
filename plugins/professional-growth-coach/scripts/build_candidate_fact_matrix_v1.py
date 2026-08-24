#!/usr/bin/env python3
"""Build one closed, identity-free candidate fact matrix."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import sys
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path
from typing import Any


def _sibling(name: str) -> Any:
    path = Path(__file__).with_name(name)
    specification = importlib.util.spec_from_file_location(f"_pgc_{path.stem}", path)
    if specification is None or specification.loader is None:
        raise RuntimeError("candidate fact matrix dependency is unavailable")
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


_snapshot = _sibling("semantic_provenance_snapshot.py")

SCHEMA_VERSION = "candidate-fact-matrix-v1"
SIGNAL_VOCABULARY = "candidate-claim-signal-v1"
_SOURCE_FIELDS = frozenset({"locale", "captured_at", "sources", "facts"})
_RAW_SOURCE_FIELDS = frozenset({"source_type", "evidence_state"})
_RAW_FACT_FIELDS = frozenset(
    {
        "fact_type",
        "source_ordinals",
        "signal_bindings",
        "signal_relation",
        "conflict_state",
        "confidentiality",
    }
)
_SIGNAL_BINDING_FIELDS = frozenset({"kind", "signal"})
_SOURCE_TYPES = frozenset(
    {"cv", "professional_profile", "portfolio", "interview_notes", "candidate_statement", "verified_record"}
)
_EVIDENCE_ORDER = {"unknown": 0, "inferred": 1, "candidate_reported": 2, "verified": 3}
_FACT_TYPES = frozenset(
    {"skill", "experience", "outcome", "credential", "portfolio_evidence", "work_preference", "constraint"}
)
_SIGNAL_RELATIONS = frozenset({"supports", "contradicts", "unknown"})
_CONFLICT_STATES = frozenset({"clear", "conflicting", "superseded"})
_CONFIDENTIALITIES = frozenset({"usable", "review_required", "forbidden"})
_REQUIREMENT_SIGNALS = frozenset(
    {
        "authentication",
        "certificate_management",
        "incident_response",
        "key_rotation",
        "kubernetes",
        "linux",
        "observability",
        "python",
        "terraform",
    }
)
_ELIGIBILITY_GATE_SIGNALS = frozenset(
    {
        "work_authorization",
        "country_geography",
        "work_arrangement",
        "language",
        "seniority",
        "experience_floor",
        "employment_arrangement",
    }
)
_SIGNAL_CATALOGS = {
    "requirement": _REQUIREMENT_SIGNALS,
    "eligibility_gate": _ELIGIBILITY_GATE_SIGNALS,
}
_TIMESTAMP = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z\Z")


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _source_snapshot(source_group: Mapping[str, object]) -> str:
    digest = hashlib.sha256(_canonical_json(source_group).encode("utf-8")).hexdigest()
    return f"snap-candidate-facts-sha256-{digest}"


def _is_exact_utc_timestamp(value: str) -> bool:
    if _TIMESTAMP.fullmatch(value) is None:
        return False
    try:
        datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return False
    return True


def _validate_source_row(row: object) -> None:
    if not isinstance(row, Mapping) or set(row) != _RAW_SOURCE_FIELDS:
        raise ValueError("candidate fact matrix is invalid")
    source_type = row.get("source_type")
    evidence_state = row.get("evidence_state")
    if (
        type(source_type) is not str
        or source_type not in _SOURCE_TYPES
        or type(evidence_state) is not str
        or evidence_state not in _EVIDENCE_ORDER
        or (source_type != "verified_record" and evidence_state == "verified")
    ):
        raise ValueError("candidate fact matrix is invalid")


def _validate_signal_binding(row: object) -> None:
    if not isinstance(row, Mapping) or set(row) != _SIGNAL_BINDING_FIELDS:
        raise ValueError("candidate fact matrix is invalid")
    kind = row.get("kind")
    signal = row.get("signal")
    if (
        type(kind) is not str
        or kind not in _SIGNAL_CATALOGS
        or type(signal) is not str
        or signal not in _SIGNAL_CATALOGS[kind]
    ):
        raise ValueError("candidate fact matrix is invalid")


def _validate_fact_row(row: object, source_count: int) -> None:
    if not isinstance(row, Mapping) or set(row) != _RAW_FACT_FIELDS:
        raise ValueError("candidate fact matrix is invalid")
    fact_type = row.get("fact_type")
    ordinals = row.get("source_ordinals")
    bindings = row.get("signal_bindings")
    relation = row.get("signal_relation")
    conflict = row.get("conflict_state")
    confidentiality = row.get("confidentiality")
    if type(fact_type) is not str or fact_type not in _FACT_TYPES:
        raise ValueError("candidate fact matrix is invalid")
    if (
        not isinstance(ordinals, list)
        or not 1 <= len(ordinals) <= 5
        or any(type(ordinal) is not int or not 1 <= ordinal <= source_count for ordinal in ordinals)
        or ordinals != sorted(set(ordinals))
    ):
        raise ValueError("candidate fact matrix is invalid")
    if (
        not isinstance(bindings, list)
        or len(bindings) > 20
        or type(relation) is not str
        or relation not in _SIGNAL_RELATIONS
        or type(conflict) is not str
        or conflict not in _CONFLICT_STATES
        or type(confidentiality) is not str
        or confidentiality not in _CONFIDENTIALITIES
    ):
        raise ValueError("candidate fact matrix is invalid")
    for binding in bindings:
        _validate_signal_binding(binding)
    binding_keys = [(binding["kind"], binding["signal"]) for binding in bindings]
    if binding_keys != sorted(set(binding_keys)):
        raise ValueError("candidate fact matrix is invalid")
    if confidentiality == "forbidden":
        if bindings or relation != "unknown":
            raise ValueError("candidate fact matrix is invalid")
    elif not bindings:
        raise ValueError("candidate fact matrix is invalid")
    if relation == "contradicts" and fact_type != "constraint":
        raise ValueError("candidate fact matrix is invalid")


def _validated_source_group(frozen_group: object) -> Mapping[str, object]:
    if not isinstance(frozen_group, Mapping) or set(frozen_group) != _SOURCE_FIELDS:
        raise ValueError("candidate fact matrix is invalid")
    locale = frozen_group.get("locale")
    captured_at = frozen_group.get("captured_at")
    sources = frozen_group.get("sources")
    facts = frozen_group.get("facts")
    if (
        type(locale) is not str
        or locale not in {"es", "en"}
        or type(captured_at) is not str
        or not _is_exact_utc_timestamp(captured_at)
        or not isinstance(sources, list)
        or not 1 <= len(sources) <= 20
        or not isinstance(facts, list)
        or not 1 <= len(facts) <= 100
    ):
        raise ValueError("candidate fact matrix is invalid")
    for row in sources:
        _validate_source_row(row)
    if len({_canonical_json(row) for row in sources}) != len(sources):
        raise ValueError("candidate fact matrix is invalid")
    for row in facts:
        _validate_fact_row(row, len(sources))
    if len({_canonical_json(row) for row in facts}) != len(facts):
        raise ValueError("candidate fact matrix is invalid")
    return frozen_group


def _project_candidate_fact_matrix_from_frozen(
    frozen_group: Mapping[str, object],
) -> dict[str, object]:
    """Project IDs and evidence minima from one detached raw source group."""
    group = _validated_source_group(frozen_group)
    sources = group["sources"]
    facts = group["facts"]
    assert isinstance(sources, list) and isinstance(facts, list)
    projected_sources = [
        {
            "source_id": f"FS-{ordinal:03d}",
            "source_type": row["source_type"],
            "evidence_state": row["evidence_state"],
            "captured_at": group["captured_at"],
        }
        for ordinal, row in enumerate(sources, start=1)
    ]
    projected_facts: list[dict[str, object]] = []
    for ordinal, row in enumerate(facts, start=1):
        ordinals = row["source_ordinals"]
        assert isinstance(ordinals, list)
        source_rows = [projected_sources[source_ordinal - 1] for source_ordinal in ordinals]
        weakest = min(
            (source_row["evidence_state"] for source_row in source_rows),
            key=lambda state: _EVIDENCE_ORDER[state],
        )
        projected_facts.append(
            {
                "fact_id": f"F-{ordinal:03d}",
                "fact_type": row["fact_type"],
                "evidence_state": weakest,
                "source_ids": [source_row["source_id"] for source_row in source_rows],
                "signal_bindings": [
                    {"kind": binding["kind"], "signal": binding["signal"]}
                    for binding in row["signal_bindings"]
                ],
                "signal_relation": row["signal_relation"],
                "conflict_state": row["conflict_state"],
                "confidentiality": row["confidentiality"],
            }
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "locale": group["locale"],
        "case_scope": "single_candidate",
        "signal_vocabulary": SIGNAL_VOCABULARY,
        "sources": projected_sources,
        "facts": projected_facts,
        "source_snapshot": _source_snapshot(group),
    }


def build_candidate_fact_matrix_v1(source_group: object) -> dict[str, object]:
    """Capture one raw private group and emit its closed fact projection."""
    try:
        frozen = _snapshot.bounded_plain_snapshot(source_group)
        return _project_candidate_fact_matrix_from_frozen(frozen)
    except Exception:
        raise ValueError("candidate fact matrix is invalid") from None


def snapshot_for_candidate_fact_matrix_v1(source_group: object) -> str:
    """Return the canonical raw-input binding after the same capture validation."""
    try:
        frozen = _snapshot.bounded_plain_snapshot(source_group)
        group = _validated_source_group(frozen)
        return _source_snapshot(group)
    except Exception:
        raise ValueError("candidate fact matrix is invalid") from None
