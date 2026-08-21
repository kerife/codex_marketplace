#!/usr/bin/env python3
"""Build deterministic, evidence-bound career learning decisions."""

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
    spec = importlib.util.spec_from_file_location(f"_pgc_learning_builder_{path.stem}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("learning builder dependency is unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_learning_validator = _sibling("validate_career_learning_decision.py")
_research_validator = _sibling("validate_target_vacancy_research.py")
_market_validator = _sibling("validate_career_market_learning_dossier.py")
_dossier_validator = _sibling("validate_executive_career_dossier_v2.py")
_snapshot = _sibling("dossier_snapshot.py")

LEARNING_SCHEMA_VERSION = "career-learning-decision-v1"
LEARNING_SNAPSHOT_PREFIX = "snap-learning-sha256-"
_PRIVACY_BOUNDARY = "public_vacancy_metadata_and_identity_free_evidence_references_only"
_OUTCOME_BOUNDARY = "not_an_interview_offer_salary_or_roi_prediction"


def _safe_copy(value: object) -> object:
    if not isinstance(value, (Mapping, list)):
        raise ValueError("learning input has malformed structure")
    try:
        copied = copy.deepcopy(value)
    except (RecursionError, TypeError, ValueError):
        raise ValueError("learning input has malformed structure") from None
    cycle, over_limit = _learning_validator._graph_flags(copied)
    if cycle or over_limit:
        raise ValueError("learning input has malformed structure")
    return copied


def _market_alignment(market: Mapping[str, object]) -> dict[str, object]:
    rows = market.get("matrix_rows")
    if not isinstance(rows, list):
        raise ValueError("learning market input is invalid")
    bindings: list[dict[str, object]] = []
    for row in rows:
        if not isinstance(row, Mapping):
            raise ValueError("learning market input is invalid")
        bindings.append(
            {
                "signal": row.get("signal"),
                "support_state": row.get("support_state"),
                "evidence_ids": copy.deepcopy(row.get("evidence_ids")),
            }
        )
    return {
        "schema_version": "candidate-market-alignment-v1",
        "research_snapshot": market.get("source_research_snapshot"),
        "executive_dossier_snapshot": market.get("source_executive_dossier_snapshot"),
        "signal_bindings": bindings,
        "privacy_boundary": "identity_free_evidence_references_only",
    }


def _validate_sources(
    research: Mapping[str, object],
    market: Mapping[str, object],
    dossier: Mapping[str, object],
) -> tuple[list[str], list[str], list[str]]:
    research_errors = _research_validator.validate_research(research)
    dossier_errors = _dossier_validator.validate_dossier(dossier)
    try:
        alignment = _market_alignment(market)
        market_errors = _market_validator.validate_market_dossier(
            market, research, dossier, alignment
        )
    except (AttributeError, KeyError, RecursionError, TypeError, ValueError):
        market_errors = ["market input is invalid"]
    return research_errors, dossier_errors, market_errors


def _evidence_and_vacancy_ids(
    research: Mapping[str, object], market: Mapping[str, object]
) -> tuple[list[str], list[str], list[str]]:
    research_vacancies = research.get("vacancies")
    market_vacancies = market.get("vacancies")
    if not isinstance(research_vacancies, list) or not isinstance(market_vacancies, list):
        raise ValueError("learning source references are invalid")
    research_ids = [
        row.get("vacancy_id")
        for row in research_vacancies
        if isinstance(row, Mapping) and isinstance(row.get("vacancy_id"), str)
    ]
    market_ids = [
        row.get("vacancy_id")
        for row in market_vacancies
        if isinstance(row, Mapping) and isinstance(row.get("vacancy_id"), str)
    ]
    if research_ids != market_ids and set(research_ids) != set(market_ids):
        raise ValueError("learning source references are inconsistent")
    recurrence = market.get("recurrence_rows")
    matrix = market.get("matrix_rows")
    evidence_ids: list[str] = []
    for rows in (recurrence, matrix):
        if not isinstance(rows, list):
            raise ValueError("learning source references are invalid")
        for row in rows:
            if not isinstance(row, Mapping) or not isinstance(row.get("evidence_ids"), list):
                raise ValueError("learning source references are invalid")
            for identifier in row["evidence_ids"]:
                if isinstance(identifier, str) and identifier not in evidence_ids:
                    evidence_ids.append(identifier)
    return research_ids, market_ids, evidence_ids


def _canonical_decisions(
    decisions: object,
    vacancy_ids: list[str],
    market_evidence_ids: list[str],
) -> list[dict[str, object]]:
    if not isinstance(decisions, list) or not 3 <= len(decisions) <= 5:
        raise ValueError("learning decisions must contain three to five rows")
    try:
        copied = copy.deepcopy(decisions)
    except (RecursionError, TypeError, ValueError):
        raise ValueError("learning decisions have malformed structure") from None
    ranks: list[object] = []
    for row in copied:
        if not isinstance(row, Mapping):
            raise ValueError("learning decision row is invalid")
        rank = row.get("decision_rank")
        ranks.append(rank)
        references = row.get("vacancy_ids")
        gaps = row.get("source_gap_ids")
        if not isinstance(references, list) or any(identifier not in vacancy_ids for identifier in references):
            raise ValueError("learning decision vacancy references are invalid")
        if not isinstance(gaps, list) or any(identifier not in market_evidence_ids for identifier in gaps):
            raise ValueError("learning decision gap references are invalid")
    if any(type(rank) is not int for rank in ranks) or sorted(ranks) != list(range(1, len(copied) + 1)):
        raise ValueError("learning decision ranks must be ordered")
    copied.sort(key=lambda row: row["decision_rank"])
    return [dict(row) for row in copied]


def build_learning_bundle(
    research: Mapping[str, object],
    market_dossier: Mapping[str, object],
    executive_dossier: Mapping[str, object],
    decisions: object,
) -> dict[str, object]:
    """Validate trusted sources and return a newly allocated learning bundle."""
    try:
        research_copy = _safe_copy(research)
        market_copy = _safe_copy(market_dossier)
        dossier_copy = _safe_copy(executive_dossier)
        if not isinstance(research_copy, Mapping) or not isinstance(market_copy, Mapping) or not isinstance(dossier_copy, Mapping):
            raise ValueError("learning source inputs are invalid")
        research_errors, dossier_errors, market_errors = _validate_sources(
            research_copy, market_copy, dossier_copy
        )
        if research_errors or dossier_errors or market_errors:
            raise ValueError("learning source inputs are invalid")
        research_ids, market_ids, market_evidence_ids = _evidence_and_vacancy_ids(
            research_copy, market_copy
        )
        if not research_ids:
            if decisions not in (None, []):
                raise ValueError("learning decisions are unavailable for a zero-vacancy market")
            result: dict[str, object] = {
                "schema_version": LEARNING_SCHEMA_VERSION,
                "locale": market_copy["locale"],
                "as_of_date": market_copy["as_of_date"],
                "source_market_snapshot": _snapshot.snapshot_for_dossier(market_copy),
                "source_dossier_snapshot": _snapshot.snapshot_for_dossier(dossier_copy),
                "source_research_snapshot": _research_validator.snapshot_for_market_dossier(research_copy),
                "state": "unavailable",
                "decisions": [],
                "privacy_boundary": _PRIVACY_BOUNDARY,
                "no_external_action": True,
                "outcome_boundary": _OUTCOME_BOUNDARY,
            }
        else:
            canonical = _canonical_decisions(decisions, market_ids, market_evidence_ids)
            result = {
                "schema_version": LEARNING_SCHEMA_VERSION,
                "locale": market_copy["locale"],
                "as_of_date": market_copy["as_of_date"],
                "source_market_snapshot": _snapshot.snapshot_for_dossier(market_copy),
                "source_dossier_snapshot": _snapshot.snapshot_for_dossier(dossier_copy),
                "source_research_snapshot": _research_validator.snapshot_for_market_dossier(research_copy),
                "state": "evaluated",
                "decisions": canonical,
                "privacy_boundary": _PRIVACY_BOUNDARY,
                "no_external_action": True,
                "outcome_boundary": _OUTCOME_BOUNDARY,
            }
        errors = _learning_validator.validate_learning_bundle(
            result, market_copy, dossier_copy, research_copy
        )
        if errors:
            raise ValueError("learning decision bundle is invalid")
        return result
    except ValueError:
        raise
    except (AttributeError, KeyError, RecursionError, TypeError):
        raise ValueError("learning decision inputs are invalid") from None


def snapshot_for_learning_bundle(value: Mapping[str, object]) -> str:
    """Return a deterministic content-bound identifier for a learning bundle."""
    try:
        cycle, over_limit = _learning_validator._graph_flags(value)
        if cycle or over_limit or not isinstance(value, Mapping):
            raise ValueError("learning bundle is malformed")
        canonical = json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    except (TypeError, ValueError, RecursionError):
        raise ValueError("learning bundle is malformed") from None
    return f"{LEARNING_SNAPSHOT_PREFIX}{hashlib.sha256(canonical).hexdigest()}"
