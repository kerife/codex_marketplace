#!/usr/bin/env python3
"""Build a deterministic, identity-free vacancy evidence alignment dossier."""

from __future__ import annotations

import copy
import re
from collections.abc import Mapping

from dossier_snapshot import snapshot_for_dossier
from validate_executive_career_dossier_v2 import validate_dossier
from validate_target_vacancy_research import (
    snapshot_for_market_dossier,
    validate_research,
)


SUPPORT_NUMERATORS = {
    "verified_match": 2,
    "candidate_reported_match": 2,
    "adjacent_evidence": 1,
    "explicit_gap": 0,
    "unknown": 0,
}
IMPORTANCE_WEIGHTS = {"must_have": 2, "preferred": 1, "responsibility_only": 0}

_ALIGNMENT_FIELDS = frozenset(
    {
        "schema_version",
        "research_snapshot",
        "executive_dossier_snapshot",
        "signal_bindings",
        "privacy_boundary",
    }
)
_BINDING_FIELDS = frozenset({"signal", "support_state", "evidence_ids"})
_EVIDENCE_ID = re.compile(r"E-[0-9]{3}\Z")
_MARKET_SNAPSHOT = re.compile(r"snap-market-sha256-[0-9a-f]{64}\Z")
_DOSSIER_SNAPSHOT = re.compile(r"snap-dossier-sha256-[0-9a-f]{64}\Z")
_METHODOLOGY_BOUNDARIES = [
    "directional_documented_evidence_not_hiring_fit",
    "no_keyword_or_prose_match_inference",
    "no_sample_wide_score",
    "unknown_preserved_separately_from_explicit_gap",
]


def rounded_percent(numerator: int, denominator: int) -> int:
    return (100 * numerator + denominator // 2) // denominator


def _binding_map(bindings: object) -> dict[str, Mapping[str, object]]:
    if not isinstance(bindings, list):
        raise ValueError("alignment signal bindings are invalid")
    result: dict[str, Mapping[str, object]] = {}
    for item in bindings:
        if not isinstance(item, Mapping):
            raise ValueError("signal binding is invalid")
        signal = item.get("signal")
        if not isinstance(signal, str) or signal in result:
            raise ValueError("signal binding is invalid")
        result[signal] = item
    return result


def alignment_score(
    requirements: object, bindings: object
) -> tuple[int, int, int]:
    """Return earned, maximum, and evidence-known integer points."""
    if not isinstance(requirements, list):
        raise ValueError("requirements are invalid")
    by_signal = _binding_map(bindings)
    earned = 0
    maximum = 0
    known = 0
    for requirement in requirements:
        if not isinstance(requirement, Mapping):
            raise ValueError("requirements are invalid")
        signal = requirement.get("signal")
        importance = requirement.get("importance")
        if not isinstance(signal, str) or importance not in IMPORTANCE_WEIGHTS:
            raise ValueError("requirements are invalid")
        binding = by_signal.get(signal)
        if binding is None or binding.get("support_state") not in SUPPORT_NUMERATORS:
            raise ValueError("signal binding is invalid")
        weight = IMPORTANCE_WEIGHTS[importance]
        denominator_points = 2 * weight
        maximum += denominator_points
        earned += SUPPORT_NUMERATORS[binding["support_state"]] * weight
        if binding["support_state"] != "unknown":
            known += denominator_points
    return earned, maximum, known


def recurrence_rows(
    vacancies: object, bindings: object
) -> list[dict[str, object]]:
    """Return per-signal k/N recurrence without a sample-wide score."""
    if not isinstance(vacancies, list):
        raise ValueError("vacancies are invalid")
    sample_size = len(vacancies)
    if sample_size == 0:
        return []
    by_signal = _binding_map(bindings)
    rows: list[dict[str, object]] = []
    for signal, binding in by_signal.items():
        occurrences = 0
        for vacancy in vacancies:
            requirements = vacancy.get("requirements") if isinstance(vacancy, Mapping) else None
            if not isinstance(requirements, list):
                raise ValueError("vacancies are invalid")
            if any(
                isinstance(requirement, Mapping) and requirement.get("signal") == signal
                for requirement in requirements
            ):
                occurrences += 1
        rows.append(
            {
                "signal": signal,
                "occurrences": occurrences,
                "sample_size": sample_size,
                "display_fraction": f"{occurrences}/{sample_size}",
                "support_state": binding["support_state"],
                "evidence_ids": list(binding.get("evidence_ids", [])),
            }
        )
    return sorted(rows, key=lambda row: (-row["occurrences"], row["signal"]))


def _validate_alignment_structure(value: object) -> Mapping[str, object]:
    if not isinstance(value, Mapping) or set(value) != _ALIGNMENT_FIELDS:
        raise ValueError("alignment has invalid closed structure")
    if value.get("schema_version") != "candidate-market-alignment-v1":
        raise ValueError("alignment has invalid schema version")
    if not isinstance(value.get("research_snapshot"), str) or not _MARKET_SNAPSHOT.fullmatch(value["research_snapshot"]):
        raise ValueError("alignment has invalid research snapshot")
    if not isinstance(value.get("executive_dossier_snapshot"), str) or not _DOSSIER_SNAPSHOT.fullmatch(value["executive_dossier_snapshot"]):
        raise ValueError("alignment has invalid dossier snapshot")
    if value.get("privacy_boundary") != "identity_free_evidence_references_only":
        raise ValueError("alignment has invalid privacy boundary")
    bindings = value.get("signal_bindings")
    if not isinstance(bindings, list) or len(bindings) > 150:
        raise ValueError("alignment signal bindings are invalid")
    seen: set[str] = set()
    for item in bindings:
        if not isinstance(item, Mapping) or set(item) != _BINDING_FIELDS:
            raise ValueError("signal binding has invalid closed structure")
        signal = item.get("signal")
        state = item.get("support_state")
        identifiers = item.get("evidence_ids")
        if not isinstance(signal, str) or not signal or len(signal) > 120 or signal in seen:
            raise ValueError("signal binding has invalid signal")
        seen.add(signal)
        if state not in SUPPORT_NUMERATORS:
            raise ValueError("signal binding has invalid support state")
        if (
            not isinstance(identifiers, list)
            or len(identifiers) > 20
            or any(not isinstance(identifier, str) or not _EVIDENCE_ID.fullmatch(identifier) for identifier in identifiers)
            or len(identifiers) != len(set(identifiers))
        ):
            raise ValueError("signal binding has invalid evidence IDs")
        if (state == "unknown") != (len(identifiers) == 0):
            raise ValueError("signal binding has incompatible evidence IDs")
    return value


def _validated_inputs(
    research: object, executive_dossier: object, alignment: object
) -> tuple[Mapping[str, object], Mapping[str, object], Mapping[str, object]]:
    try:
        research_copy, dossier_copy, alignment_copy = copy.deepcopy(
            (research, executive_dossier, alignment)
        )
    except (RecursionError, TypeError, ValueError) as error:
        raise ValueError("alignment inputs have malformed structure") from error
    if validate_research(research_copy):
        raise ValueError("research validation failed")
    if validate_dossier(dossier_copy):
        raise ValueError("dossier validation failed")
    validated_alignment = _validate_alignment_structure(alignment_copy)
    if validated_alignment["research_snapshot"] != snapshot_for_market_dossier(research_copy):
        raise ValueError("alignment research snapshot is stale")
    if validated_alignment["executive_dossier_snapshot"] != snapshot_for_dossier(dossier_copy):
        raise ValueError("alignment dossier snapshot is stale")

    vacancies = research_copy.get("vacancies")
    evidence = dossier_copy.get("evidence")
    if not isinstance(vacancies, list) or not isinstance(evidence, list):
        raise ValueError("alignment inputs have malformed structure")
    expected_signals = {
        requirement["signal"]
        for vacancy in vacancies
        for requirement in vacancy["requirements"]
    }
    by_signal = _binding_map(validated_alignment["signal_bindings"])
    if set(by_signal) != expected_signals:
        raise ValueError("alignment signal bindings must cover research signals exactly")
    evidence_states = {
        row["id"]: row["state"]
        for row in evidence
        if isinstance(row, Mapping) and isinstance(row.get("id"), str)
    }
    allowed_states = {
        "verified_match": {"verified"},
        "candidate_reported_match": {"candidate_reported"},
        "adjacent_evidence": {"verified", "candidate_reported"},
        "explicit_gap": {"verified", "candidate_reported"},
        "unknown": set(),
    }
    for binding in by_signal.values():
        state = binding["support_state"]
        if any(evidence_states.get(identifier) not in allowed_states[state] for identifier in binding["evidence_ids"]):
            raise ValueError("signal binding evidence state is incompatible")
    if research_copy.get("locale") != dossier_copy.get("locale"):
        raise ValueError("research and dossier locale must match")
    return research_copy, dossier_copy, validated_alignment


def _qualitative_band(alignment_percent: int, coverage_percent: int) -> str:
    if coverage_percent < 50:
        return "insufficient_evidence"
    if alignment_percent >= 75:
        return "higher_documented_alignment"
    if alignment_percent >= 50:
        return "moderate_documented_alignment"
    return "lower_documented_alignment"


def build_market_dossier(
    research: object, executive_dossier: object, alignment: object
) -> dict[str, object]:
    """Validate all inputs and return a newly allocated derived dossier."""
    research_copy, dossier_copy, alignment_copy = _validated_inputs(
        research, executive_dossier, alignment
    )
    bindings = alignment_copy["signal_bindings"]
    employers = {row["employer_id"]: row["display_name"] for row in research_copy["employers"]}
    cards: list[dict[str, object]] = []
    for vacancy in research_copy["vacancies"]:
        earned, maximum, known = alignment_score(vacancy["requirements"], bindings)
        alignment_percent = rounded_percent(earned, maximum) if maximum else 0
        coverage_percent = rounded_percent(known, maximum) if maximum else 0
        card = {
            field: copy.deepcopy(vacancy[field])
            for field in (
                "vacancy_id",
                "employer_id",
                "title",
                "role_family",
                "location",
                "arrangement",
                "geographic_compatibility",
                "source_kind",
                "source_url",
                "official_referrer_url",
                "source_state",
                "access_date",
                "publication_date",
                "freshness_status",
            )
        }
        card.update(
            {
                "employer": employers[vacancy["employer_id"]],
                "earned_points": earned,
                "maximum_points": maximum,
                "known_points": known,
                "alignment_percent": alignment_percent,
                "evidence_coverage_percent": coverage_percent,
                "interpretation": "directional_documented_evidence_not_hiring_fit",
                "qualitative_band": _qualitative_band(alignment_percent, coverage_percent),
            }
        )
        cards.append(card)
    cards.sort(key=lambda row: (-row["alignment_percent"], row["vacancy_id"]))
    vacancy_order = [card["vacancy_id"] for card in cards]
    vacancy_by_id = {vacancy["vacancy_id"]: vacancy for vacancy in research_copy["vacancies"]}
    by_signal = _binding_map(bindings)
    matrix_rows = []
    for signal in sorted(by_signal):
        binding = by_signal[signal]
        cells = []
        for vacancy_id in vacancy_order:
            requirements = [
                {
                    "requirement_id": requirement["requirement_id"],
                    "importance": requirement["importance"],
                    "source_paraphrase": requirement["source_paraphrase"],
                }
                for requirement in vacancy_by_id[vacancy_id]["requirements"]
                if requirement["signal"] == signal
            ]
            cells.append(
                {
                    "vacancy_id": vacancy_id,
                    "required": bool(requirements),
                    "requirements": requirements,
                }
            )
        matrix_rows.append(
            {
                "signal": signal,
                "support_state": binding["support_state"],
                "evidence_ids": list(binding["evidence_ids"]),
                "cells": cells,
            }
        )
    limit = research_copy["search_limit"]
    scope = research_copy["search_scope"]
    return {
        "schema_version": "career-market-learning-dossier-v1",
        "locale": research_copy["locale"],
        "as_of_date": research_copy["as_of_date"],
        "state": research_copy["state"],
        "source_research_snapshot": alignment_copy["research_snapshot"],
        "source_executive_dossier_snapshot": alignment_copy["executive_dossier_snapshot"],
        "search_summary": {
            "locale": research_copy["locale"],
            "as_of_date": research_copy["as_of_date"],
            "state": research_copy["state"],
            "vacancy_count": len(cards),
            "maximum_vacancies": scope["maximum_vacancies"],
            "bounded_queries_run": limit["bounded_queries_run"],
            "limit_reason": limit["limit_reason"],
            "limitation": limit["limitation"],
        },
        "vacancies": cards,
        "matrix_rows": matrix_rows,
        "recurrence_rows": recurrence_rows(research_copy["vacancies"], bindings),
        "learning_state": "not_evaluated",
        "learning_decisions": [],
        "methodology_boundaries": list(_METHODOLOGY_BOUNDARIES),
        "privacy_boundary": "public_vacancy_metadata_and_identity_free_evidence_references_only",
        "no_external_action": True,
    }
