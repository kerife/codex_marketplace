#!/usr/bin/env python3
"""Build a source-recomputed career market learning dossier v2."""

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
        raise RuntimeError("required market dossier dependency is unavailable")
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


_alignment = _sibling("derive_candidate_market_alignment_v2.py")

SUPPORT_NUMERATORS = {"verified_match": 2, "candidate_reported_match": 2, "unknown": 0}
IMPORTANCE_WEIGHTS = {"must_have": 2, "preferred": 1, "responsibility_only": 0}
METHODOLOGY_BOUNDARIES = [
    "directional_documented_evidence_not_hiring_fit",
    "no_keyword_or_prose_match_inference",
    "no_sample_wide_score",
    "unknown_preserved_separately_from_explicit_gap",
]
_CARD_SOURCE_FIELDS = (
    "vacancy_id", "employer_id", "title", "role_family", "location", "arrangement",
    "geographic_compatibility", "source_kind", "source_url", "official_referrer_url",
    "source_state", "access_date", "publication_date", "freshness_status",
)


def _canonical_json(value: Mapping[str, object]) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def rounded_percent(numerator: int, denominator: int) -> int:
    return (100 * numerator + denominator // 2) // denominator


def _qualitative_band(alignment_percent: int, coverage_percent: int) -> str:
    if coverage_percent < 50:
        return "insufficient_evidence"
    if alignment_percent >= 75:
        return "higher_documented_alignment"
    if alignment_percent >= 50:
        return "moderate_documented_alignment"
    return "lower_documented_alignment"


def _binding_map(bindings: object) -> dict[str, Mapping[str, object]]:
    if not isinstance(bindings, list):
        raise ValueError("market dossier v2 is invalid")
    result: dict[str, Mapping[str, object]] = {}
    for binding in bindings:
        if not isinstance(binding, Mapping) or not isinstance(binding.get("signal"), str):
            raise ValueError("market dossier v2 is invalid")
        signal = binding["signal"]
        if signal in result:
            raise ValueError("market dossier v2 is invalid")
        result[signal] = binding
    return result


def _alignment_score(requirements: object, bindings: object) -> tuple[int, int, int]:
    if not isinstance(requirements, list):
        raise ValueError("market dossier v2 is invalid")
    by_signal = _binding_map(bindings)
    earned = maximum = known = 0
    for requirement in requirements:
        if not isinstance(requirement, Mapping):
            raise ValueError("market dossier v2 is invalid")
        signal, importance = requirement.get("signal"), requirement.get("importance")
        binding = by_signal.get(signal) if isinstance(signal, str) else None
        if binding is None or importance not in IMPORTANCE_WEIGHTS:
            raise ValueError("market dossier v2 is invalid")
        weight = IMPORTANCE_WEIGHTS[importance]
        points = 2 * weight
        maximum += points
        state = binding.get("support_state")
        if state not in SUPPORT_NUMERATORS:
            raise ValueError("market dossier v2 is invalid")
        earned += SUPPORT_NUMERATORS[state] * weight
        if state != "unknown":
            known += points
    return earned, maximum, known


def _validated_source_copies(research: object, executive_dossier: object) -> tuple[dict[str, object], dict[str, object]]:
    # The alignment derivation is the bounded source validation boundary.
    _alignment.derive_candidate_market_alignment_v2(research, executive_dossier)
    try:
        research_copy, dossier_copy = copy.deepcopy((research, executive_dossier))
    except (RecursionError, TypeError, ValueError):
        raise ValueError("market dossier v2 sources are invalid") from None
    if not isinstance(research_copy, dict) or not isinstance(dossier_copy, dict):
        raise ValueError("market dossier v2 sources are invalid")
    if research_copy.get("locale") != dossier_copy.get("locale"):
        raise ValueError("market dossier v2 source locales must match")
    return research_copy, dossier_copy


def _project_market_v2(
    research: Mapping[str, object], executive_dossier: Mapping[str, object], alignment: Mapping[str, object]
) -> dict[str, object]:
    del executive_dossier
    bindings = alignment.get("signal_bindings")
    by_signal = _binding_map(bindings)
    employers = {row["employer_id"]: row["display_name"] for row in research["employers"]}
    cards: list[dict[str, object]] = []
    for vacancy in research["vacancies"]:
        earned, maximum, known = _alignment_score(vacancy["requirements"], bindings)
        alignment_percent = rounded_percent(earned, maximum) if maximum else 0
        coverage_percent = rounded_percent(known, maximum) if maximum else 0
        card = {field: copy.deepcopy(vacancy[field]) for field in _CARD_SOURCE_FIELDS}
        card.update({
            "employer": employers[vacancy["employer_id"]], "earned_points": earned,
            "maximum_points": maximum, "known_points": known,
            "alignment_percent": alignment_percent, "evidence_coverage_percent": coverage_percent,
            "interpretation": "directional_documented_evidence_not_hiring_fit",
            "qualitative_band": _qualitative_band(alignment_percent, coverage_percent),
        })
        cards.append(card)
    cards.sort(key=lambda row: (-row["alignment_percent"], row["vacancy_id"]))
    vacancy_order = [card["vacancy_id"] for card in cards]
    vacancy_by_id = {vacancy["vacancy_id"]: vacancy for vacancy in research["vacancies"]}
    matrix_rows: list[dict[str, object]] = []
    for signal in sorted(by_signal):
        binding = by_signal[signal]
        cells = []
        for vacancy_id in vacancy_order:
            requirements = [
                {"requirement_id": requirement["requirement_id"], "importance": requirement["importance"], "source_paraphrase": requirement["source_paraphrase"]}
                for requirement in vacancy_by_id[vacancy_id]["requirements"]
                if requirement["signal"] == signal
            ]
            cells.append({"vacancy_id": vacancy_id, "required": bool(requirements), "requirements": requirements})
        matrix_rows.append({
            "signal": signal, "support_state": binding["support_state"],
            "claim_ids": list(binding["claim_ids"]), "evidence_ids": list(binding["evidence_ids"]),
            "requirement_ids": list(binding["requirement_ids"]), "vacancy_ids": list(binding["vacancy_ids"]),
            "cells": cells,
        })
    recurrence_rows: list[dict[str, object]] = []
    vacancies = research["vacancies"]
    if vacancies:
        for signal, binding in by_signal.items():
            occurrences = sum(any(requirement["signal"] == signal for requirement in vacancy["requirements"]) for vacancy in vacancies)
            recurrence_rows.append({
                "signal": signal, "occurrences": occurrences, "sample_size": len(vacancies),
                "display_fraction": f"{occurrences}/{len(vacancies)}", "support_state": binding["support_state"],
                "evidence_ids": list(binding["evidence_ids"]),
            })
        recurrence_rows.sort(key=lambda row: (-row["occurrences"], row["signal"]))
    limit, scope = research["search_limit"], research["search_scope"]
    return {
        "schema_version": "career-market-learning-dossier-v2", "locale": research["locale"],
        "as_of_date": research["as_of_date"], "state": research["state"],
        "source_research_snapshot": alignment["research_snapshot"],
        "source_executive_dossier_snapshot": alignment["executive_dossier_snapshot"],
        "source_alignment_snapshot": _alignment.snapshot_for_alignment_v2(alignment),
        "search_summary": {"locale": research["locale"], "as_of_date": research["as_of_date"], "state": research["state"], "vacancy_count": len(cards), "maximum_vacancies": scope["maximum_vacancies"], "bounded_queries_run": limit["bounded_queries_run"], "limit_reason": limit["limit_reason"], "limitation": limit["limitation"]},
        "vacancies": cards, "matrix_rows": matrix_rows, "recurrence_rows": recurrence_rows,
        "learning_state": "not_evaluated", "learning_decisions": [],
        "methodology_boundaries": list(METHODOLOGY_BOUNDARIES),
        "privacy_boundary": "public_vacancy_metadata_and_identity_free_evidence_references_only",
        "no_external_action": True,
    }


def snapshot_for_market_dossier_v2(value: Mapping[str, object]) -> str:
    if not isinstance(value, Mapping):
        raise ValueError("market dossier v2 is invalid")
    digest = hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()
    return f"snap-market-dossier-v2-sha256-{digest}"


def build_market_dossier_v2(research: object, executive_dossier: object) -> dict[str, object]:
    """Derive the market dossier only from validated research and dossier sources."""
    try:
        research_copy, dossier_copy = _validated_source_copies(research, executive_dossier)
        alignment = _alignment.derive_candidate_market_alignment_v2(research_copy, dossier_copy)
        result = _project_market_v2(research_copy, dossier_copy, alignment)
        validator = _sibling("validate_career_market_learning_dossier_v2.py")
        if validator.validate_market_dossier_v2(result, research_copy, dossier_copy):
            raise ValueError("market dossier v2 is invalid")
        return result
    except Exception:
        raise ValueError("market dossier v2 is invalid") from None
