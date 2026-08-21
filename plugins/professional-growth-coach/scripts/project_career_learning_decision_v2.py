#!/usr/bin/env python3
"""Pure closed projection for semantic-provenance learning decisions v2."""

from __future__ import annotations

import copy
import importlib.util
import re
import sys
from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType
from typing import Any


def _sibling(name: str) -> Any:
    path = Path(__file__).with_name(name)
    specification = importlib.util.spec_from_file_location(f"_pgc_{path.stem}", path)
    if specification is None or specification.loader is None:
        raise RuntimeError("required learning projection dependency is unavailable")
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


_provider_validation = _sibling("validate_career_learning_provider_research.py")

_SIGNAL = re.compile(r"[a-z][a-z0-9_]{1,63}\Z")
_OPTION_ID = re.compile(r"LP-[0-9]{3}\Z")
_RECURRENCE = re.compile(r"[1-5]/[1-5]\Z")
_VACANCY_ORDINAL = re.compile(r"V[1-5]\Z")
_REQUEST_FIELDS = frozenset(
    {"decision_rank", "decision_code", "source_signals", "provider_option_id"}
)
_ROUTE_FIELDS = frozenset(
    {"signal", "term_label", "support_state", "recurrence", "vacancy_ordinals"}
)
_PROVIDER_OPTION_FIELDS = frozenset(
    {
        "option_id", "option_type", "provider", "option", "source_title", "source_date",
        "access_date", "source_state", "url", "geography", "availability", "current_cost",
        "currency", "tax", "duration", "prerequisite", "renewal", "maintenance", "unknowns",
        "covered_signals", "coverage_basis",
    }
)
_OUTCOME_BOUNDARY = "not_an_interview_offer_salary_or_roi_prediction"


def _frozen(**values: str) -> Mapping[str, str]:
    return MappingProxyType(values)


DECISION_RULES: Mapping[str, Mapping[str, str]] = MappingProxyType(
    {
        "build_bounded_proof": _frozen(
            gap_type="proof", option_type="portfolio_project", decision="do_now",
            provider="forbidden",
        ),
        "run_validation_lab": _frozen(
            gap_type="experience", option_type="lab", decision="do_now",
            provider="forbidden",
        ),
        "research_provider_option": _frozen(
            gap_type="knowledge", option_type="provider", decision="research_first",
            provider="required",
        ),
        "defer_learning_purchase": _frozen(
            gap_type="low_return", option_type="no_learning_yet", decision="defer",
            provider="forbidden",
        ),
        "run_role_search_experiment": _frozen(
            gap_type="terminology", option_type="role_search", decision="research_first",
            provider="forbidden",
        ),
    }
)


COPY: Mapping[str, Mapping[str, object]] = MappingProxyType(
    {
        "es": MappingProxyType(
            {
                "option_names": MappingProxyType(
                    {
                        "build_bounded_proof": "Prueba acotada de {signals}",
                        "run_validation_lab": "Laboratorio de validación de {signals}",
                        "defer_learning_purchase": "Aplazar compra de formación para {signals}",
                        "run_role_search_experiment": "Experimento de búsqueda para {signals}",
                    }
                ),
                "decision_bases": MappingProxyType(
                    {
                        "build_bounded_proof": "Prioriza una prueba acotada antes de comprar formación; la ruta estructurada de evidencia es la base completa de esta decisión preliminar.",
                        "run_validation_lab": "Usa un laboratorio acotado para comprobar la señal documentada; la ruta estructurada de evidencia es la base completa de esta decisión preliminar.",
                        "research_provider_option": "Investiga esta opción verificada de proveedor antes de comprar; su vínculo estructurado de señal no predice resultados laborales.",
                        "defer_learning_purchase": "Aplaza la compra hasta completar una prueba acotada; la ruta estructurada de evidencia no demuestra retorno de inversión.",
                        "run_role_search_experiment": "Prueba una búsqueda acotada de roles antes de elegir formación; la ruta estructurada de evidencia no demuestra elegibilidad ni contratación.",
                    }
                ),
                "cost_time_band": "No evaluado; requiere confirmación separada.",
                "expected_signal_boundary": "Hipótesis acotada: una señal inspectable no predice entrevista, oferta, salario ni retorno de inversión.",
                "portfolio_or_no_learning_alternative": "Completa primero una prueba acotada y usa la evidencia existente antes de comprar formación.",
                "overbuying_risk": "Evita acumular credenciales o dividir el tiempo antes de completar una prueba de mayor señal.",
                "next_action_gate": "Revisión y autorización exacta obligatorias antes de inscripción, compra, programación de examen, publicación, difusión o mensajería externa.",
            }
        ),
        "en": MappingProxyType(
            {
                "option_names": MappingProxyType(
                    {
                        "build_bounded_proof": "Bounded {signals} proof",
                        "run_validation_lab": "{signals} validation lab",
                        "defer_learning_purchase": "Defer learning purchase for {signals}",
                        "run_role_search_experiment": "Role-search experiment for {signals}",
                    }
                ),
                "decision_bases": MappingProxyType(
                    {
                        "build_bounded_proof": "Prioritize one bounded proof before buying learning; the structured evidence route is the complete basis for this draft decision.",
                        "run_validation_lab": "Use a bounded lab to test the documented signal; the structured evidence route is the complete basis for this draft decision.",
                        "research_provider_option": "Research this verified provider option before buying; its structured signal binding does not predict employment outcomes.",
                        "defer_learning_purchase": "Defer the purchase until one bounded proof is complete; the structured evidence route does not establish return on investment.",
                        "run_role_search_experiment": "Run a bounded role search before choosing learning; the structured evidence route does not establish eligibility or hiring.",
                    }
                ),
                "cost_time_band": "Not evaluated; separate confirmation is required.",
                "expected_signal_boundary": "Bounded hypothesis: an inspectable signal predicts neither an interview, offer, salary, nor return on investment.",
                "portfolio_or_no_learning_alternative": "Complete one bounded proof first and use existing evidence before buying learning.",
                "overbuying_risk": "Avoid collecting credentials or splitting time before one higher-signal proof is complete.",
                "next_action_gate": "Review and exact authorization are required before enrollment, purchase, exam scheduling, publication, sharing, or external messaging.",
            }
        ),
    }
)


def _validate_closed_request(request: Mapping[str, object]) -> None:
    if not isinstance(request, Mapping) or set(request) != _REQUEST_FIELDS:
        raise ValueError("learning decision projection is invalid")
    rank = request.get("decision_rank")
    code = request.get("decision_code")
    signals = request.get("source_signals")
    provider_id = request.get("provider_option_id")
    if (
        isinstance(rank, bool)
        or not isinstance(rank, int)
        or not 1 <= rank <= 5
        or code not in DECISION_RULES
        or not isinstance(signals, list)
        or not 1 <= len(signals) <= 5
        or any(not isinstance(signal, str) or not _SIGNAL.fullmatch(signal) for signal in signals)
        or signals != sorted(set(signals))
        or (provider_id is not None and (not isinstance(provider_id, str) or not _OPTION_ID.fullmatch(provider_id)))
    ):
        raise ValueError("learning decision projection is invalid")


def _decision_rule(code: object) -> Mapping[str, str]:
    rule = DECISION_RULES.get(code) if isinstance(code, str) else None
    if rule is None:
        raise ValueError("learning decision projection is invalid")
    return rule


def _validated_public_label(route: Mapping[str, object]) -> str:
    if not isinstance(route, Mapping) or set(route) != _ROUTE_FIELDS:
        raise ValueError("learning decision projection is invalid")
    signal = route.get("signal")
    label = route.get("term_label")
    state = route.get("support_state")
    recurrence = route.get("recurrence")
    ordinals = route.get("vacancy_ordinals")
    if (
        not isinstance(signal, str)
        or not _SIGNAL.fullmatch(signal)
        or not _provider_validation._valid_text(label, strict_name=True)
        or len(label) > 80
        or state not in {"verified_match", "candidate_reported_match"}
        or not isinstance(recurrence, str)
        or not _RECURRENCE.fullmatch(recurrence)
        or not isinstance(ordinals, list)
        or not ordinals
        or any(not isinstance(item, str) or not _VACANCY_ORDINAL.fullmatch(item) for item in ordinals)
        or ordinals != sorted(set(ordinals))
    ):
        raise ValueError("learning decision projection is invalid")
    assert isinstance(label, str)
    return label


def _join_labels(locale: str, labels: list[str]) -> str:
    if locale not in COPY or not labels:
        raise ValueError("learning decision projection is invalid")
    if len(labels) == 1:
        return labels[0]
    if len(labels) == 2:
        return (" y " if locale == "es" else " and ").join(labels)
    separator = " y " if locale == "es" else ", and "
    return ", ".join(labels[:-1]) + separator + labels[-1]


def _provider_fields(
    rule: Mapping[str, str],
    provider_option: Mapping[str, object] | None,
    source_signals: object,
    provider_option_id: object,
) -> dict[str, str]:
    if rule["provider"] == "forbidden":
        if provider_option is not None or provider_option_id is not None:
            raise ValueError("learning decision projection is invalid")
        return {"option_type": rule["option_type"], "provider_or_owner": "candidate_owned"}
    if not isinstance(provider_option, Mapping):
        raise ValueError("learning decision projection is invalid")
    if set(provider_option) != _PROVIDER_OPTION_FIELDS:
        raise ValueError("learning decision projection is invalid")
    option_type = provider_option.get("option_type")
    provider = provider_option.get("provider")
    option = provider_option.get("option")
    if (
        provider_option.get("option_id") != provider_option_id
        or option_type not in {"course", "certification"}
        or provider_option.get("source_state") != "active"
        or provider_option.get("availability") != "available"
        or provider_option.get("covered_signals") != source_signals
        or not _provider_validation._valid_text(provider, provider=True)
        or not _provider_validation._valid_text(option, strict_name=True)
    ):
        raise ValueError("learning decision projection is invalid")
    assert isinstance(option_type, str) and isinstance(provider, str) and isinstance(option, str)
    return {"option_type": option_type, "provider_or_owner": provider, "option_name": option}


def _complete_projection(
    locale: str,
    request: Mapping[str, object],
    routes: list[dict[str, object]],
    rule: Mapping[str, str],
    signal_label: str,
    provider_fields: Mapping[str, str],
) -> dict[str, object]:
    localized = COPY[locale]
    code = request["decision_code"]
    if not isinstance(code, str):
        raise ValueError("learning decision projection is invalid")
    option_name = provider_fields.get("option_name")
    if option_name is None:
        templates = localized["option_names"]
        if not isinstance(templates, Mapping) or code not in templates:
            raise ValueError("learning decision projection is invalid")
        option_name = str(templates[code]).format(signals=signal_label)
    bases = localized["decision_bases"]
    if not isinstance(bases, Mapping) or code not in bases:
        raise ValueError("learning decision projection is invalid")
    return {
        "decision_rank": request["decision_rank"],
        "decision_code": code,
        "source_signals": list(request["source_signals"]),
        "provider_option_id": request["provider_option_id"],
        "gap_type": rule["gap_type"],
        "option_type": provider_fields["option_type"],
        "decision": rule["decision"],
        "option_name": option_name,
        "provider_or_owner": provider_fields["provider_or_owner"],
        "signal_routes": copy.deepcopy(routes),
        "cost_time_band": localized["cost_time_band"],
        "expected_signal_boundary": localized["expected_signal_boundary"],
        "portfolio_or_no_learning_alternative": localized["portfolio_or_no_learning_alternative"],
        "overbuying_risk": localized["overbuying_risk"],
        "decision_basis": bases[code],
        "next_action_gate": localized["next_action_gate"],
        "outcome_boundary": _OUTCOME_BOUNDARY,
        "draft_only": True,
        "no_external_action": True,
    }


def project_decision_v2(
    locale: str,
    request: Mapping[str, object],
    routes: list[dict[str, object]],
    provider_option: Mapping[str, object] | None,
) -> dict[str, object]:
    """Project all semantics from one closed request and exact source routes."""
    try:
        _validate_closed_request(request)
        rule = _decision_rule(request["decision_code"])
        if not isinstance(routes, list) or len(routes) != len(request["source_signals"]):
            raise ValueError("learning decision projection is invalid")
        labels = [_validated_public_label(route) for route in routes]
        route_signals = [route["signal"] for route in routes]
        if route_signals != request["source_signals"]:
            raise ValueError("learning decision projection is invalid")
        signal_label = _join_labels(locale, labels)
        provider_fields = _provider_fields(
            rule, provider_option, request["source_signals"], request["provider_option_id"]
        )
        return _complete_projection(
            locale, request, routes, rule, signal_label, provider_fields
        )
    except Exception:
        raise ValueError("learning decision projection is invalid") from None
