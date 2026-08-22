#!/usr/bin/env python3
"""Build closed learning decisions from independently validated v2 sources."""

from __future__ import annotations

import copy
import importlib.util
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any


def _sibling(name: str) -> Any:
    path = Path(__file__).with_name(name)
    specification = importlib.util.spec_from_file_location(f"_pgc_{path.stem}", path)
    if specification is None or specification.loader is None:
        raise RuntimeError("required learning builder dependency is unavailable")
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


_alignment = _sibling("derive_candidate_market_alignment_v2.py")
_market_builder = _sibling("build_career_market_learning_dossier_v2.py")
_market_validator = _sibling("validate_career_market_learning_dossier_v2.py")
_provider_validator = _sibling("validate_career_learning_provider_research.py")
_projection = _sibling("project_career_learning_decision_v2.py")

SCHEMA_VERSION = "career-learning-decision-v2"
_PRIVACY_BOUNDARY = "identity_free_structured_provenance_only"
_OUTCOME_BOUNDARY = "not_an_interview_offer_salary_or_roi_prediction"
_MAX_DEPTH = 32
_MAX_NODES = 10_000
_MAX_ITEMS = 150
_MAX_STRING = 4096


def _bounded_tree(value: object) -> bool:
    pending: list[tuple[str, object, int]] = [("visit", value, 0)]
    active: set[int] = set()
    nodes = 0
    while pending:
        operation, current, depth = pending.pop()
        if operation == "leave":
            active.discard(id(current))
            continue
        if operation == "children":
            try:
                child = next(current)
            except StopIteration:
                continue
            except Exception:
                return False
            pending.append(("children", current, depth))
            pending.append(("visit", child, depth))
            continue
        nodes += 1
        if nodes > _MAX_NODES or depth > _MAX_DEPTH:
            return False
        if isinstance(current, str):
            if len(current) > _MAX_STRING or any(
                0xD800 <= ord(character) <= 0xDFFF for character in current
            ):
                return False
            continue
        if current is None or isinstance(current, (bool, int, float)):
            continue
        if not isinstance(current, (Mapping, list)):
            return False
        identity = id(current)
        if identity in active:
            return False
        try:
            if len(current) > _MAX_ITEMS:
                return False
            children = iter(
                (item for pair in current.items() for item in pair)
                if isinstance(current, Mapping)
                else current
            )
        except Exception:
            return False
        active.add(identity)
        pending.append(("leave", current, depth))
        pending.append(("children", children, depth + 1))
    return True


def _validated_source_copies(
    research: object,
    market_dossier: object,
    executive_dossier: object,
    provider_research: object,
) -> tuple[dict[str, object], dict[str, object], dict[str, object], dict[str, object], dict[str, object]]:
    if not all(
        _bounded_tree(value)
        for value in (research, market_dossier, executive_dossier, provider_research)
    ):
        raise ValueError("learning decision v2 is invalid")
    try:
        research_copy, market_copy, dossier_copy, provider_copy = copy.deepcopy(
            (research, market_dossier, executive_dossier, provider_research)
        )
        alignment = _alignment.derive_candidate_market_alignment_v2(
            research_copy, dossier_copy
        )
        market_errors = _market_validator.validate_market_dossier_v2(
            market_copy, research_copy, dossier_copy
        )
        provider_errors = _provider_validator.validate_provider_research(provider_copy)
    except Exception:
        raise ValueError("learning decision v2 is invalid") from None
    if (
        not all(
            isinstance(value, dict)
            for value in (research_copy, market_copy, dossier_copy, provider_copy, alignment)
        )
        or market_errors
        or provider_errors
        or len({research_copy.get("locale"), market_copy.get("locale"), dossier_copy.get("locale"), provider_copy.get("locale")}) != 1
        or research_copy.get("as_of_date") != market_copy.get("as_of_date")
        or provider_copy.get("as_of_date") != research_copy.get("as_of_date")
        or research_copy.get("state") != market_copy.get("state")
    ):
        raise ValueError("learning decision v2 is invalid")
    return research_copy, market_copy, dossier_copy, provider_copy, alignment


def _indexed(rows: object, key: str) -> dict[str, Mapping[str, object]]:
    if not isinstance(rows, list):
        raise ValueError("learning decision v2 is invalid")
    result: dict[str, Mapping[str, object]] = {}
    for row in rows:
        value = row.get(key) if isinstance(row, Mapping) else None
        if not isinstance(value, str) or value in result:
            raise ValueError("learning decision v2 is invalid")
        result[value] = row
    return result


def _term_labels(executive_dossier: Mapping[str, object]) -> dict[str, str]:
    rows = executive_dossier.get("requested_technology_terms")
    if not isinstance(rows, list):
        raise ValueError("learning decision v2 is invalid")
    labels: dict[str, str] = {}
    for row in rows:
        if not isinstance(row, Mapping):
            raise ValueError("learning decision v2 is invalid")
        term = row.get("term")
        try:
            signal = _alignment.normalize_signal_term(term)
        except Exception:
            raise ValueError("learning decision v2 is invalid") from None
        if signal in labels or not _provider_validator._valid_text(term, strict_name=True):
            raise ValueError("learning decision v2 is invalid")
        assert isinstance(term, str)
        labels[signal] = term
    return labels


def _exact_routes_and_unions(
    request: Mapping[str, object],
    alignment: Mapping[str, object],
    market: Mapping[str, object],
    research: Mapping[str, object],
    dossier: Mapping[str, object],
) -> tuple[list[dict[str, object]], dict[str, list[str]]]:
    bindings = _indexed(alignment.get("signal_bindings"), "signal")
    matrix = _indexed(market.get("matrix_rows"), "signal")
    recurrence = _indexed(market.get("recurrence_rows"), "signal")
    vacancies = _indexed(research.get("vacancies"), "vacancy_id")
    public_vacancies = _indexed(market.get("vacancies"), "vacancy_id")
    labels = _term_labels(dossier)
    vacancy_ordinals = {
        vacancy_id: f"V{index}"
        for index, vacancy_id in enumerate(public_vacancies, start=1)
    }
    unions = {
        "claim_ids": set(),
        "source_evidence_ids": set(),
        "requirement_ids": set(),
        "vacancy_ids": set(),
        "target_role_families": set(),
    }
    routes: list[dict[str, object]] = []
    signals = request.get("source_signals")
    if not isinstance(signals, list):
        raise ValueError("learning decision v2 is invalid")
    for signal in signals:
        binding = bindings.get(signal) if isinstance(signal, str) else None
        matrix_row = matrix.get(signal) if isinstance(signal, str) else None
        recurrence_row = recurrence.get(signal) if isinstance(signal, str) else None
        label = labels.get(signal) if isinstance(signal, str) else None
        if (
            binding is None
            or matrix_row is None
            or recurrence_row is None
            or label is None
            or binding.get("support_state") == "unknown"
            or matrix_row.get("support_state") != binding.get("support_state")
            or recurrence_row.get("support_state") != binding.get("support_state")
        ):
            raise ValueError("learning decision v2 is invalid")
        relation = {
            "claim_ids": binding.get("claim_ids"),
            "source_evidence_ids": binding.get("evidence_ids"),
            "requirement_ids": binding.get("requirement_ids"),
            "vacancy_ids": binding.get("vacancy_ids"),
        }
        if any(
            not isinstance(values, list)
            or values != sorted(set(values))
            for values in relation.values()
        ):
            raise ValueError("learning decision v2 is invalid")
        for field, values in relation.items():
            unions[field].update(values)
        exact_vacancies = relation["vacancy_ids"]
        ordinals: list[str] = []
        for vacancy_id in exact_vacancies:
            vacancy = vacancies.get(vacancy_id)
            ordinal = vacancy_ordinals.get(vacancy_id)
            role_family = vacancy.get("role_family") if vacancy is not None else None
            if not isinstance(ordinal, str) or not isinstance(role_family, str):
                raise ValueError("learning decision v2 is invalid")
            ordinals.append(ordinal)
            unions["target_role_families"].add(role_family)
        display_fraction = recurrence_row.get("display_fraction")
        if not isinstance(display_fraction, str):
            raise ValueError("learning decision v2 is invalid")
        routes.append(
            {
                "signal": signal,
                "term_label": label,
                "support_state": binding["support_state"],
                "recurrence": display_fraction,
                "vacancy_ordinals": sorted(ordinals),
            }
        )
    routes.sort(key=lambda row: row["signal"])
    return routes, {field: sorted(values) for field, values in unions.items()}


def _provider_option(
    request: Mapping[str, object], provider_research: Mapping[str, object]
) -> Mapping[str, object] | None:
    identifier = request.get("provider_option_id")
    if identifier is None:
        return None
    options = _indexed(provider_research.get("options"), "option_id")
    return options.get(identifier) if isinstance(identifier, str) else None


def _state(value: object) -> str:
    states = {
        "complete": "complete",
        "limited_market_evidence": "limited",
        "market_evidence_unavailable": "unavailable",
    }
    result = states.get(value) if isinstance(value, str) else None
    if result is None:
        raise ValueError("learning decision v2 is invalid")
    return result


def _project_bundle(
    research: Mapping[str, object],
    market: Mapping[str, object],
    dossier: Mapping[str, object],
    provider: Mapping[str, object],
    alignment: Mapping[str, object],
    requests: object,
) -> dict[str, object]:
    learning_state = _state(market.get("state"))
    if learning_state == "unavailable":
        if requests not in (None, []):
            raise ValueError("learning decision v2 is invalid")
        decision_rows: list[dict[str, object]] = []
    else:
        if not isinstance(requests, list) or not 1 <= len(requests) <= 5:
            raise ValueError("learning decision v2 is invalid")
        if [row.get("decision_rank") if isinstance(row, Mapping) else None for row in requests] != list(range(1, len(requests) + 1)):
            raise ValueError("learning decision v2 is invalid")
        decision_rows = []
        for request in requests:
            if not isinstance(request, Mapping):
                raise ValueError("learning decision v2 is invalid")
            routes, unions = _exact_routes_and_unions(
                request, alignment, market, research, dossier
            )
            projected = _projection.project_decision_v2(
                str(research["locale"]), request, routes, _provider_option(request, provider)
            )
            projected.update(unions)
            decision_rows.append(projected)
    return {
        "schema_version": SCHEMA_VERSION,
        "locale": research["locale"],
        "as_of_date": research["as_of_date"],
        "state": learning_state,
        "source_research_snapshot": alignment["research_snapshot"],
        "source_dossier_snapshot": alignment["executive_dossier_snapshot"],
        "source_alignment_snapshot": _alignment.snapshot_for_alignment_v2(alignment),
        "source_market_snapshot": _market_builder.snapshot_for_market_dossier_v2(market),
        "source_provider_research_snapshot": _provider_validator.snapshot_for_provider_research(provider),
        "decisions": decision_rows,
        "privacy_boundary": _PRIVACY_BOUNDARY,
        "no_external_action": True,
        "outcome_boundary": _OUTCOME_BOUNDARY,
    }


def build_learning_bundle_v2(
    research: object,
    market_dossier: object,
    executive_dossier: object,
    provider_research: object,
    decision_requests: object,
) -> dict[str, object]:
    """Build the canonical source-recomputed learning bundle v2."""
    try:
        if not _bounded_tree(decision_requests):
            raise ValueError("learning decision v2 is invalid")
        research_copy, market_copy, dossier_copy, provider_copy, alignment = (
            _validated_source_copies(
                research, market_dossier, executive_dossier, provider_research
            )
        )
        requests_copy = copy.deepcopy(decision_requests)
        return _project_bundle(
            research_copy, market_copy, dossier_copy, provider_copy, alignment, requests_copy
        )
    except Exception:
        raise ValueError("learning decision v2 is invalid") from None
