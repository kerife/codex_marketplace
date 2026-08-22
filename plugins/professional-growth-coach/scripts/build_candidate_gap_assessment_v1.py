#!/usr/bin/env python3
"""Resolve one validated public gap response to private source references."""

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


_snapshot = _sibling("semantic_provenance_snapshot.py")
_response_builder = _sibling("build_candidate_gap_response_v1.py")
_response_validator = _sibling("validate_candidate_gap_response_v1.py")
_dossier_validator = _sibling("validate_executive_career_dossier_v2.py")
_dossier_snapshot = _sibling("dossier_snapshot.py")
_alignment = _sibling("derive_candidate_market_alignment_v2.py")
_market_validator = _sibling("validate_career_market_learning_dossier_v2.py")

bounded_plain_snapshot = _snapshot.bounded_plain_snapshot
SCHEMA_VERSION = "candidate-gap-assessment-v1"


def _snapshot_for_frozen_gap_response(response: Mapping[str, object]) -> str:
    canonical = json.dumps(
        response,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return f"snap-gap-response-v1-sha256-{digest}"


def _requested_signals(dossier: Mapping[str, object]) -> frozenset[str]:
    rows = dossier.get("requested_technology_terms")
    if not isinstance(rows, list):
        raise ValueError("candidate gap assessment is invalid")
    signals: set[str] = set()
    for row in rows:
        if not isinstance(row, Mapping):
            raise ValueError("candidate gap assessment is invalid")
        signals.add(_alignment.normalize_signal_term(row.get("term")))
    return frozenset(signals)


def _validated_group(
    frozen_group: Mapping[str, object],
) -> tuple[
    Mapping[str, object],
    Mapping[str, object],
    Mapping[str, object],
    Mapping[str, object],
    Mapping[str, object] | None,
    str,
    str,
    str,
    str | None,
]:
    research = frozen_group["research"]
    dossier = frozen_group["executive_dossier"]
    market = frozen_group["market_dossier"]
    response = frozen_group["gap_response"]
    provider = frozen_group["provider_research"]
    response_group = {
        "value": response,
        "research": research,
        "market_dossier": market,
        "provider_research": provider,
    }
    if _response_validator._validate_candidate_gap_response_from_frozen(response_group):
        raise ValueError("candidate gap assessment is invalid")
    if (
        not isinstance(dossier, Mapping)
        or _dossier_validator.validate_dossier(dossier)
        or _market_validator.validate_market_dossier_v2(market, research, dossier)
        or not isinstance(response, Mapping)
    ):
        raise ValueError("candidate gap assessment is invalid")
    (
        research,
        market,
        provider,
        research_snapshot,
        market_snapshot,
        provider_snapshot,
    ) = _response_builder._validate_sources(research, market, provider)
    dossier_snapshot = _dossier_snapshot.snapshot_for_dossier(dossier)
    if (
        market.get("source_executive_dossier_snapshot") != dossier_snapshot
        or dossier.get("locale") != research.get("locale")
    ):
        raise ValueError("candidate gap assessment is invalid")
    return (
        research,
        dossier,
        market,
        response,
        provider,
        research_snapshot,
        dossier_snapshot,
        market_snapshot,
        provider_snapshot,
    )


def _selected_provider_id(
    provider: Mapping[str, object] | None,
    signal: str,
    ordinal: object,
) -> str | None:
    if ordinal is None:
        return None
    if not isinstance(ordinal, str) or provider is None:
        raise ValueError("candidate gap assessment is invalid")
    choices = _response_builder._eligible_provider_choices(provider, signal)
    index = int(ordinal[1:]) - 1
    if index < 0 or index >= len(choices):
        raise ValueError("candidate gap assessment is invalid")
    option_id = choices[index].get("option_id")
    if not isinstance(option_id, str):
        raise ValueError("candidate gap assessment is invalid")
    return option_id


def _project_assessment(
    research: Mapping[str, object],
    dossier: Mapping[str, object],
    market: Mapping[str, object],
    response: Mapping[str, object],
    provider: Mapping[str, object] | None,
    research_snapshot: str,
    dossier_snapshot: str,
    market_snapshot: str,
    provider_snapshot: str | None,
) -> dict[str, object]:
    state = response["response_state"]
    selected_vacancy_id = None
    selected_signal = response["selected_signal"]
    selected_provider_id = None
    assessments: list[dict[str, object]] = []
    if state in {"partial", "complete"}:
        vacancy = _response_builder._selected_vacancy(
            research, market, response["selected_vacancy_ordinal"]
        )
        selected_vacancy_id = vacancy.get("vacancy_id")
        if not isinstance(selected_vacancy_id, str) or not isinstance(selected_signal, str):
            raise ValueError("candidate gap assessment is invalid")
        if selected_signal not in _requested_signals(dossier):
            raise ValueError("candidate gap assessment is invalid")
        relation = response["relation"]
        if not isinstance(relation, str):
            raise ValueError("candidate gap assessment is invalid")
        selected_provider_id = _selected_provider_id(
            provider, selected_signal, response["selected_provider_ordinal"]
        )
        confirmed = relation != "unknown"
        assessments.append(
            {
                "signal": selected_signal,
                "relation": relation,
                "confirmation_state": (
                    "candidate_confirmed" if confirmed else "not_assessed"
                ),
                "assessment_date": research["as_of_date"] if confirmed else None,
            }
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "locale": research["locale"],
        "as_of_date": research["as_of_date"],
        "state": state,
        "source_research_snapshot": research_snapshot,
        "source_dossier_snapshot": dossier_snapshot,
        "source_market_snapshot": market_snapshot,
        "source_gap_response_snapshot": _snapshot_for_frozen_gap_response(response),
        "source_provider_research_snapshot": provider_snapshot,
        "selected_vacancy_id": selected_vacancy_id,
        "selected_signal": selected_signal,
        "selected_provider_option_id": selected_provider_id,
        "assessments": assessments,
        "privacy_boundary": "identity_free_closed_candidate_assessment_only",
        "draft_only": True,
        "no_external_action": True,
    }


def _project_candidate_gap_assessment_from_frozen(
    frozen_group: Mapping[str, object],
) -> dict[str, object]:
    """Project only from one already captured built-in source group."""
    return _project_assessment(*_validated_group(frozen_group))


def build_candidate_gap_assessment_v1(
    research: object,
    executive_dossier: object,
    market_dossier: object,
    gap_response: object,
    provider_research: object | None = None,
) -> dict[str, object]:
    """Capture the complete group once and resolve its public response."""
    try:
        frozen = bounded_plain_snapshot(
            {
                "research": research,
                "executive_dossier": executive_dossier,
                "market_dossier": market_dossier,
                "gap_response": gap_response,
                "provider_research": provider_research,
            }
        )
        return _project_candidate_gap_assessment_from_frozen(frozen)
    except Exception:
        raise ValueError("candidate gap assessment is invalid") from None
