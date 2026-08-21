#!/usr/bin/env python3
"""Derive the closed, source-bound candidate/market alignment v2."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import re
import sys
import unicodedata
from collections.abc import Mapping
from pathlib import Path
from typing import Any


def _sibling(name: str) -> Any:
    path = Path(__file__).with_name(name)
    specification = importlib.util.spec_from_file_location(f"_pgc_{path.stem}", path)
    if specification is None or specification.loader is None:
        raise RuntimeError("required alignment dependency is unavailable")
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


_research = _sibling("validate_target_vacancy_research.py")
_dossier = _sibling("validate_executive_career_dossier_v2.py")
_dossier_snapshot = _sibling("dossier_snapshot.py")

validate_research = _research.validate_research
snapshot_for_market_dossier = _research.snapshot_for_market_dossier
validate_dossier = _dossier.validate_dossier
snapshot_for_dossier = _dossier_snapshot.snapshot_for_dossier

_SIGNAL = re.compile(r"[a-z][a-z0-9_]{1,63}\Z")
_SEPARATOR = re.compile(r"[\t\n\r\f\v -]+")
_REJECTED_ALIASES = frozenset({"terra"})
_CLAIM_ID = re.compile(r"C-[0-9]{3}\Z")
_EVIDENCE_ID = re.compile(r"E-[0-9]{3}\Z")
_REQUIREMENT_ID = re.compile(r"V-[0-9]{3}-R-[0-9]{2}\Z")
_VACANCY_ID = re.compile(r"V-[0-9]{3}\Z")
_RESEARCH_SNAPSHOT = re.compile(r"snap-market-sha256-[0-9a-f]{64}\Z")
_DOSSIER_SNAPSHOT = re.compile(r"snap-dossier-sha256-[0-9a-f]{64}\Z")
_MAX_DEPTH = 32
_MAX_NODES = 10_000
_MAX_LIST_ITEMS = 150
_ALIGNMENT_FIELDS = frozenset(
    {
        "schema_version",
        "research_snapshot",
        "executive_dossier_snapshot",
        "signal_bindings",
        "privacy_boundary",
    }
)
_BINDING_FIELDS = frozenset(
    {"signal", "support_state", "claim_ids", "evidence_ids", "requirement_ids", "vacancy_ids"}
)


def normalize_signal_term(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("technology term is invalid")
    normalized = _SEPARATOR.sub("_", unicodedata.normalize("NFKC", value).strip().casefold())
    if not _SIGNAL.fullmatch(normalized) or normalized in _REJECTED_ALIASES:
        raise ValueError("technology term is invalid")
    return normalized


def _safe_tree(value: object) -> bool:
    pending: list[tuple[object, int, bool]] = [(value, 0, False)]
    active: set[int] = set()
    nodes = 0
    while pending:
        current, depth, leaving = pending.pop()
        if leaving:
            active.discard(id(current))
            continue
        if isinstance(current, str):
            if any(0xD800 <= ord(character) <= 0xDFFF for character in current):
                return False
            continue
        if current is None or isinstance(current, (bool, int, float)):
            continue
        if not isinstance(current, (Mapping, list)) or depth > _MAX_DEPTH:
            return False
        identity = id(current)
        if identity in active:
            return False
        nodes += 1
        if nodes > _MAX_NODES:
            return False
        active.add(identity)
        pending.append((current, depth, True))
        children = current.values() if isinstance(current, Mapping) else current
        if isinstance(current, list) and len(current) > _MAX_LIST_ITEMS:
            return False
        pending.extend((child, depth + 1, False) for child in children)
    return True


def _validated_copies(research: object, executive_dossier: object) -> tuple[dict[str, object], dict[str, object]]:
    if not _safe_tree(research) or not _safe_tree(executive_dossier):
        raise ValueError("alignment input is invalid")
    try:
        research_copy = copy.deepcopy(research)
        dossier_copy = copy.deepcopy(executive_dossier)
        research_errors = validate_research(research_copy)
        dossier_errors = validate_dossier(dossier_copy)
    except (RecursionError, TypeError, ValueError):
        raise ValueError("alignment input is invalid") from None
    if (
        research_errors
        or dossier_errors
        or not isinstance(research_copy, dict)
        or not isinstance(dossier_copy, dict)
    ):
        raise ValueError("alignment input is invalid")
    return research_copy, dossier_copy


def _unique_term_index(terms: object) -> dict[str, tuple[str, ...]]:
    if not isinstance(terms, list):
        raise ValueError("alignment input is invalid")
    indexed: dict[str, tuple[str, ...]] = {}
    for row in terms:
        if not isinstance(row, Mapping) or not isinstance(row.get("claim_ids"), list):
            raise ValueError("alignment input is invalid")
        try:
            signal = normalize_signal_term(row.get("term"))
        except ValueError:
            raise ValueError("alignment input is invalid") from None
        claim_ids = row["claim_ids"]
        if (
            signal in indexed
            or not claim_ids
            or any(not isinstance(identifier, str) or not _CLAIM_ID.fullmatch(identifier) for identifier in claim_ids)
        ):
            raise ValueError("alignment input is invalid")
        indexed[signal] = tuple(sorted(set(claim_ids)))
    return indexed


def _research_signal_index(vacancies: object) -> dict[str, dict[str, list[str]]]:
    if not isinstance(vacancies, list):
        raise ValueError("alignment input is invalid")
    indexed: dict[str, dict[str, set[str]]] = {}
    for vacancy in vacancies:
        if not isinstance(vacancy, Mapping):
            raise ValueError("alignment input is invalid")
        vacancy_id = vacancy.get("vacancy_id")
        requirements = vacancy.get("requirements")
        if not isinstance(vacancy_id, str) or not _VACANCY_ID.fullmatch(vacancy_id) or not isinstance(requirements, list):
            raise ValueError("alignment input is invalid")
        for requirement in requirements:
            if not isinstance(requirement, Mapping):
                raise ValueError("alignment input is invalid")
            signal = requirement.get("signal")
            requirement_id = requirement.get("requirement_id")
            if (
                not isinstance(signal, str)
                or not _SIGNAL.fullmatch(signal)
                or not isinstance(requirement_id, str)
                or not _REQUIREMENT_ID.fullmatch(requirement_id)
            ):
                raise ValueError("alignment input is invalid")
            row = indexed.setdefault(signal, {"requirement_ids": set(), "vacancy_ids": set()})
            row["requirement_ids"].add(requirement_id)
            row["vacancy_ids"].add(vacancy_id)
    return {
        signal: {
            "requirement_ids": sorted(row["requirement_ids"]),
            "vacancy_ids": sorted(row["vacancy_ids"]),
        }
        for signal, row in indexed.items()
    }


def _record_index(rows: object) -> dict[str, Mapping[str, object]]:
    if not isinstance(rows, list):
        raise ValueError("alignment input is invalid")
    indexed: dict[str, Mapping[str, object]] = {}
    for row in rows:
        value = row.get("id") if isinstance(row, Mapping) else None
        if not isinstance(value, str) or value in indexed:
            raise ValueError("alignment input is invalid")
        indexed[value] = row
    return indexed


def _derive_binding(
    signal: str,
    market: Mapping[str, list[str]],
    term_index: Mapping[str, tuple[str, ...]],
    claim_index: Mapping[str, Mapping[str, object]],
    evidence_index: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    result: dict[str, object] = {
        "signal": signal,
        "support_state": "unknown",
        "claim_ids": [],
        "evidence_ids": [],
        "requirement_ids": market["requirement_ids"],
        "vacancy_ids": market["vacancy_ids"],
    }
    claim_ids = term_index.get(signal)
    if claim_ids is None:
        return result
    claims = [claim_index.get(identifier) for identifier in claim_ids]
    if any(claim is None for claim in claims):
        raise ValueError("alignment input is invalid")
    evidence_ids: set[str] = set()
    states: list[object] = []
    for claim in claims:
        assert claim is not None
        linked = claim.get("evidence_ids")
        if not isinstance(linked, list) or not linked:
            return result
        states.append(claim.get("state"))
        for evidence_id in linked:
            if not isinstance(evidence_id, str) or not _EVIDENCE_ID.fullmatch(evidence_id):
                raise ValueError("alignment input is invalid")
            evidence_ids.add(evidence_id)
    evidence = [evidence_index.get(identifier) for identifier in sorted(evidence_ids)]
    if any(row is None for row in evidence):
        raise ValueError("alignment input is invalid")
    for row in evidence:
        assert row is not None
        states.append(row.get("state"))
    if not evidence_ids or any(state in {"inferred", "unknown"} for state in states):
        return result
    if not all(state in {"verified", "candidate_reported"} for state in states):
        return result
    result["support_state"] = (
        "verified_match" if all(state == "verified" for state in states) else "candidate_reported_match"
    )
    result["claim_ids"] = sorted(claim_ids)
    result["evidence_ids"] = sorted(evidence_ids)
    return result


def derive_candidate_market_alignment_v2(
    research: object, executive_dossier: object
) -> dict[str, object]:
    research_copy, dossier_copy = _validated_copies(research, executive_dossier)
    term_index = _unique_term_index(dossier_copy["requested_technology_terms"])
    claim_index = _record_index(dossier_copy["claims"])
    evidence_index = _record_index(dossier_copy["evidence"])
    market_index = _research_signal_index(research_copy["vacancies"])
    bindings = [
        _derive_binding(signal, market_index[signal], term_index, claim_index, evidence_index)
        for signal in sorted(market_index)
    ]
    return {
        "schema_version": "candidate-market-alignment-v2",
        "research_snapshot": snapshot_for_market_dossier(research_copy),
        "executive_dossier_snapshot": snapshot_for_dossier(dossier_copy),
        "signal_bindings": bindings,
        "privacy_boundary": "identity_free_structured_provenance_only",
    }


def _canonical_json(value: Mapping[str, object]) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _id_list(value: object, pattern: re.Pattern[str]) -> bool:
    return (
        isinstance(value, list)
        and len(value) <= _MAX_LIST_ITEMS
        and all(isinstance(identifier, str) and pattern.fullmatch(identifier) for identifier in value)
        and value == sorted(value)
        and len(value) == len(set(value))
    )


def _validate_alignment_v2(value: object) -> dict[str, object]:
    if not _safe_tree(value) or not isinstance(value, Mapping) or set(value) != _ALIGNMENT_FIELDS:
        raise ValueError("alignment is invalid")
    bindings = value.get("signal_bindings")
    if (
        value.get("schema_version") != "candidate-market-alignment-v2"
        or value.get("privacy_boundary") != "identity_free_structured_provenance_only"
        or not isinstance(value.get("research_snapshot"), str)
        or not _RESEARCH_SNAPSHOT.fullmatch(value["research_snapshot"])
        or not isinstance(value.get("executive_dossier_snapshot"), str)
        or not _DOSSIER_SNAPSHOT.fullmatch(value["executive_dossier_snapshot"])
        or not isinstance(bindings, list)
        or len(bindings) > _MAX_LIST_ITEMS
    ):
        raise ValueError("alignment is invalid")
    previous_signal = ""
    validated_bindings: list[dict[str, object]] = []
    for binding in bindings:
        if not isinstance(binding, Mapping) or set(binding) != _BINDING_FIELDS:
            raise ValueError("alignment is invalid")
        signal = binding.get("signal")
        state = binding.get("support_state")
        if (
            not isinstance(signal, str)
            or not _SIGNAL.fullmatch(signal)
            or signal <= previous_signal
            or state not in {"verified_match", "candidate_reported_match", "unknown"}
            or not _id_list(binding.get("claim_ids"), _CLAIM_ID)
            or not _id_list(binding.get("evidence_ids"), _EVIDENCE_ID)
            or not _id_list(binding.get("requirement_ids"), _REQUIREMENT_ID)
            or not _id_list(binding.get("vacancy_ids"), _VACANCY_ID)
        ):
            raise ValueError("alignment is invalid")
        claim_ids = binding["claim_ids"]
        evidence_ids = binding["evidence_ids"]
        if (state == "unknown" and (claim_ids or evidence_ids)) or (
            state != "unknown" and (not claim_ids or not evidence_ids)
        ):
            raise ValueError("alignment is invalid")
        previous_signal = signal
        validated_bindings.append(dict(binding))
    return {
        "schema_version": value["schema_version"],
        "research_snapshot": value["research_snapshot"],
        "executive_dossier_snapshot": value["executive_dossier_snapshot"],
        "signal_bindings": validated_bindings,
        "privacy_boundary": value["privacy_boundary"],
    }


def snapshot_for_alignment_v2(value: Mapping[str, object]) -> str:
    validated = _validate_alignment_v2(value)
    digest = hashlib.sha256(_canonical_json(validated).encode("utf-8")).hexdigest()
    return f"snap-alignment-sha256-{digest}"
