#!/usr/bin/env python3
"""Build a closed public-ordinal candidate gap response."""

from __future__ import annotations

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
        raise RuntimeError("required candidate response dependency is unavailable")
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


_snapshot = _sibling("semantic_provenance_snapshot.py")
_research = _sibling("validate_target_vacancy_research.py")
_market_builder = _sibling("build_career_market_learning_dossier_v2.py")
_provider = _sibling("validate_career_learning_provider_research.py")
_schema_validation = _sibling("validate_json_schema_subset.py")

bounded_plain_snapshot = _snapshot.bounded_plain_snapshot
SCHEMA_VERSION = "candidate-gap-response-v1"
_RESPONSE_FIELDS = frozenset(
    {
        "selected_vacancy_ordinal",
        "selected_signal",
        "relation",
        "selected_provider_ordinal",
    }
)
_RELATIONS = frozenset(
    {
        "supported",
        "proof_gap",
        "knowledge_gap",
        "practice_gap",
        "professional_experience_gap",
        "terminology_gap",
        "unknown",
    }
)
_SIGNAL = re.compile(r"[a-z][a-z0-9_]{1,63}\Z")
_VACANCY_ORDINAL = re.compile(r"V([1-5])\Z")
_PROVIDER_ORDINAL = re.compile(r"L([1-9][0-9]*)\Z")


def _load_schema(name: str) -> dict[str, object]:
    value = json.loads((Path(__file__).parents[1] / "schemas" / name).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("candidate gap response is invalid")
    return value


def _validate_sources(
    research: object,
    market_dossier: object,
    provider_research: object | None,
) -> tuple[Mapping[str, object], Mapping[str, object], Mapping[str, object] | None, str, str, str | None]:
    if (
        not isinstance(research, Mapping)
        or _research.validate_research(research)
        or not isinstance(market_dossier, Mapping)
        or _schema_validation.validate_schema_instance(
            market_dossier, _load_schema("career-market-learning-dossier-v2.schema.json")
        )
    ):
        raise ValueError("candidate gap response is invalid")
    research_snapshot = _research.snapshot_for_market_dossier(research)
    search_summary = market_dossier.get("search_summary")
    if (
        market_dossier.get("source_research_snapshot") != research_snapshot
        or market_dossier.get("locale") != research.get("locale")
        or market_dossier.get("as_of_date") != research.get("as_of_date")
        or market_dossier.get("state") != research.get("state")
        or not isinstance(search_summary, Mapping)
        or search_summary.get("locale") != research.get("locale")
        or search_summary.get("as_of_date") != research.get("as_of_date")
        or search_summary.get("state") != research.get("state")
    ):
        raise ValueError("candidate gap response is invalid")
    market_snapshot = _market_builder.snapshot_for_market_dossier_v2(market_dossier)
    provider_snapshot = None
    if provider_research is not None:
        if (
            not isinstance(provider_research, Mapping)
            or _provider.validate_provider_research(provider_research)
            or provider_research.get("locale") != research.get("locale")
            or provider_research.get("as_of_date") != research.get("as_of_date")
        ):
            raise ValueError("candidate gap response is invalid")
        provider_snapshot = _provider.snapshot_for_provider_research(provider_research)
    return (
        research,
        market_dossier,
        provider_research,
        research_snapshot,
        market_snapshot,
        provider_snapshot,
    )


def _normalized_sort_text(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("candidate gap response is invalid")
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def _eligible_provider_choices(
    provider_research: Mapping[str, object], signal: str
) -> list[Mapping[str, object]]:
    options = provider_research.get("options")
    if not isinstance(options, list):
        raise ValueError("candidate gap response is invalid")
    choices = [
        option
        for option in options
        if isinstance(option, Mapping)
        and option.get("source_state") == "active"
        and option.get("availability") == "available"
        and signal in option.get("covered_signals", [])
    ]
    return sorted(
        choices,
        key=lambda option: (
            _normalized_sort_text(option.get("option")),
            _normalized_sort_text(option.get("provider")),
        ),
    )


def _selected_vacancy(
    research: Mapping[str, object],
    market: Mapping[str, object],
    ordinal: object,
) -> Mapping[str, object]:
    match = _VACANCY_ORDINAL.fullmatch(ordinal) if isinstance(ordinal, str) else None
    vacancies = market.get("vacancies")
    if match is None or not isinstance(vacancies, list):
        raise ValueError("candidate gap response is invalid")
    index = int(match.group(1)) - 1
    if index >= len(vacancies) or not isinstance(vacancies[index], Mapping):
        raise ValueError("candidate gap response is invalid")
    vacancy_id = vacancies[index].get("vacancy_id")
    research_vacancies = research.get("vacancies")
    if not isinstance(research_vacancies, list):
        raise ValueError("candidate gap response is invalid")
    matches = [
        vacancy
        for vacancy in research_vacancies
        if isinstance(vacancy, Mapping) and vacancy.get("vacancy_id") == vacancy_id
    ]
    if len(matches) != 1:
        raise ValueError("candidate gap response is invalid")
    return matches[0]


def _selection_state(
    research: Mapping[str, object],
    market: Mapping[str, object],
    response: object,
    provider_research: Mapping[str, object] | None,
) -> str:
    unavailable = research.get("state") == "market_evidence_unavailable"
    if response is None:
        if provider_research is not None:
            raise ValueError("candidate gap response is invalid")
        return "unavailable" if unavailable else "selection_required"
    if unavailable or not isinstance(response, Mapping) or set(response) != _RESPONSE_FIELDS:
        raise ValueError("candidate gap response is invalid")

    ordinal = response.get("selected_vacancy_ordinal")
    signal = response.get("selected_signal")
    relation = response.get("relation")
    provider_ordinal = response.get("selected_provider_ordinal")
    if (
        not isinstance(signal, str)
        or _SIGNAL.fullmatch(signal) is None
        or not isinstance(relation, str)
        or relation not in _RELATIONS
    ):
        raise ValueError("candidate gap response is invalid")
    vacancy = _selected_vacancy(research, market, ordinal)
    requirements = vacancy.get("requirements")
    if not isinstance(requirements, list) or not any(
        isinstance(requirement, Mapping) and requirement.get("signal") == signal
        for requirement in requirements
    ):
        raise ValueError("candidate gap response is invalid")

    if relation == "unknown":
        if provider_research is not None or provider_ordinal is not None:
            raise ValueError("candidate gap response is invalid")
        return "partial"
    if relation != "knowledge_gap":
        if provider_research is not None or provider_ordinal is not None:
            raise ValueError("candidate gap response is invalid")
        return "complete"
    if provider_ordinal is None:
        return "complete"
    match = (
        _PROVIDER_ORDINAL.fullmatch(provider_ordinal)
        if isinstance(provider_ordinal, str)
        else None
    )
    if match is None or provider_research is None:
        raise ValueError("candidate gap response is invalid")
    choices = _eligible_provider_choices(provider_research, signal)
    if int(match.group(1)) > len(choices):
        raise ValueError("candidate gap response is invalid")
    return "complete"


def _project_candidate_gap_response_from_frozen(
    frozen_group: Mapping[str, object],
) -> dict[str, object]:
    research = frozen_group["research"]
    market = frozen_group["market_dossier"]
    response = frozen_group["response"]
    provider = frozen_group["provider_research"]
    (
        research,
        market,
        provider,
        research_snapshot,
        market_snapshot,
        provider_snapshot,
    ) = _validate_sources(research, market, provider)
    state = _selection_state(research, market, response, provider)
    selected = response if isinstance(response, Mapping) else {}
    return {
        "schema_version": SCHEMA_VERSION,
        "locale": research["locale"],
        "as_of_date": research["as_of_date"],
        "source_research_snapshot": research_snapshot,
        "source_market_snapshot": market_snapshot,
        "source_provider_research_snapshot": provider_snapshot,
        "response_state": state,
        "selected_vacancy_ordinal": selected.get("selected_vacancy_ordinal"),
        "selected_signal": selected.get("selected_signal"),
        "relation": selected.get("relation"),
        "selected_provider_ordinal": selected.get("selected_provider_ordinal"),
        "privacy_boundary": "identity_free_closed_candidate_response_only",
        "draft_only": True,
        "no_external_action": True,
    }


def build_candidate_gap_response_v1(
    research: object,
    market_dossier: object,
    response: object | None,
    provider_research: object | None = None,
) -> dict[str, object]:
    """Capture once, validate sources, and persist only the public response."""
    try:
        frozen = bounded_plain_snapshot(
            {
                "research": research,
                "market_dossier": market_dossier,
                "response": response,
                "provider_research": provider_research,
            }
        )
        return _project_candidate_gap_response_from_frozen(frozen)
    except Exception:
        raise ValueError("candidate gap response is invalid") from None
