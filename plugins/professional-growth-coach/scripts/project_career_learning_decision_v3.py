#!/usr/bin/env python3
"""Project one v3 learning row only from recomputed eligibility and sources."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Mapping
from types import MappingProxyType


LEARNING_ACTIONS: Mapping[str, tuple[str, str | None]] = MappingProxyType(
    {
        "build_bounded_proof": ("build_bounded_proof", None),
        "run_validation_lab": ("run_validation_lab", None),
        "research_provider_option": ("research_provider_option", "selected"),
        "run_role_search_experiment": ("run_role_search_experiment", None),
    }
)

_ACTION_RULES: Mapping[str, Mapping[str, str]] = MappingProxyType(
    {
        "build_bounded_proof": MappingProxyType(
            {
                "relation": "proof_gap",
                "gap_type": "proof",
                "option_type": "portfolio_project",
                "decision": "do_now",
            }
        ),
        "run_validation_lab": MappingProxyType(
            {
                "relation": "practice_gap",
                "gap_type": "practice",
                "option_type": "lab",
                "decision": "do_now",
            }
        ),
        "research_provider_option": MappingProxyType(
            {
                "relation": "knowledge_gap",
                "gap_type": "knowledge",
                "option_type": "provider",
                "decision": "research_first",
            }
        ),
        "run_role_search_experiment": MappingProxyType(
            {
                "relation": "terminology_gap",
                "gap_type": "terminology",
                "option_type": "role_search",
                "decision": "research_first",
            }
        ),
    }
)

COPY: Mapping[str, Mapping[str, object]] = MappingProxyType(
    {
        "es": MappingProxyType(
            {
                "option_names": MappingProxyType(
                    {
                        "build_bounded_proof": "Prueba acotada de {signal}",
                        "run_validation_lab": "Laboratorio de validación de {signal}",
                        "run_role_search_experiment": "Experimento de búsqueda para {signal}",
                    }
                ),
                "decision_bases": MappingProxyType(
                    {
                        "build_bounded_proof": "Prioriza una prueba acotada antes de comprar formación; la ruta estructurada de evidencia es la base completa de esta decisión preliminar.",
                        "run_validation_lab": "Usa un laboratorio acotado para comprobar la señal documentada; la ruta estructurada de evidencia es la base completa de esta decisión preliminar.",
                        "research_provider_option": "Investiga esta opción verificada de proveedor antes de comprar; su vínculo estructurado de señal no predice resultados laborales.",
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
                        "build_bounded_proof": "Bounded {signal} proof",
                        "run_validation_lab": "{signal} validation lab",
                        "run_role_search_experiment": "Role-search experiment for {signal}",
                    }
                ),
                "decision_bases": MappingProxyType(
                    {
                        "build_bounded_proof": "Prioritize one bounded proof before buying learning; the structured evidence route is the complete basis for this draft decision.",
                        "run_validation_lab": "Use a bounded lab to test the documented signal; the structured evidence route is the complete basis for this draft decision.",
                        "research_provider_option": "Research this verified provider option before buying; its structured signal binding does not predict employment outcomes.",
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

_SIGNAL = re.compile(r"[a-z][a-z0-9_]{1,63}\Z")
_SEPARATOR = re.compile(r"[\t\n\r\f\v -]+")
_OUTCOME_BOUNDARY = "not_an_interview_offer_salary_or_roi_prediction"


def _normalized_signal(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("learning decision v3 projection is invalid")
    normalized = _SEPARATOR.sub(
        "_", unicodedata.normalize("NFKC", value).strip().casefold()
    )
    if _SIGNAL.fullmatch(normalized) is None:
        raise ValueError("learning decision v3 projection is invalid")
    return normalized


def _exact_binding(
    alignment: Mapping[str, object], signal: str
) -> Mapping[str, object]:
    bindings = alignment.get("signal_bindings")
    if not isinstance(bindings, list):
        raise ValueError("learning decision v3 projection is invalid")
    matches = [
        row
        for row in bindings
        if isinstance(row, Mapping) and row.get("signal") == signal
    ]
    if len(matches) != 1:
        raise ValueError("learning decision v3 projection is invalid")
    return matches[0]


def _sorted_unique_strings(value: object) -> list[str]:
    if (
        not isinstance(value, list)
        or any(not isinstance(item, str) for item in value)
        or value != sorted(set(value))
    ):
        raise ValueError("learning decision v3 projection is invalid")
    return list(value)


def _exact_source_route(
    signal: str,
    eligibility: Mapping[str, object],
    alignment: Mapping[str, object],
    research: Mapping[str, object],
    market: Mapping[str, object],
    dossier: Mapping[str, object],
) -> tuple[dict[str, object], dict[str, list[str]]]:
    binding = _exact_binding(alignment, signal)
    support = binding.get("support_state")
    if support not in {"verified_match", "candidate_reported_match", "unknown"}:
        raise ValueError("learning decision v3 projection is invalid")
    if support != eligibility.get("candidate_support_state"):
        raise ValueError("learning decision v3 projection is invalid")

    vacancies = research.get("vacancies")
    if not isinstance(vacancies, list):
        raise ValueError("learning decision v3 projection is invalid")
    active_count = 0
    vacancy_ids: set[str] = set()
    requirement_ids: set[str] = set()
    role_families: set[str] = set()
    for vacancy in vacancies:
        if not isinstance(vacancy, Mapping) or vacancy.get("source_state") != "active":
            continue
        active_count += 1
        vacancy_id = vacancy.get("vacancy_id")
        role_family = vacancy.get("role_family")
        requirements = vacancy.get("requirements")
        if (
            not isinstance(vacancy_id, str)
            or not isinstance(role_family, str)
            or not isinstance(requirements, list)
        ):
            raise ValueError("learning decision v3 projection is invalid")
        matching = [
            requirement
            for requirement in requirements
            if isinstance(requirement, Mapping)
            and requirement.get("signal") == signal
        ]
        if matching:
            vacancy_ids.add(vacancy_id)
            role_families.add(role_family)
        for requirement in matching:
            identifier = requirement.get("requirement_id")
            if not isinstance(identifier, str):
                raise ValueError("learning decision v3 projection is invalid")
            requirement_ids.add(identifier)
    if active_count == 0 or len(vacancy_ids) < 2:
        raise ValueError("learning decision v3 projection is invalid")
    exact_vacancies = sorted(vacancy_ids)
    exact_requirements = sorted(requirement_ids)
    if (
        _sorted_unique_strings(binding.get("vacancy_ids")) != exact_vacancies
        or _sorted_unique_strings(binding.get("requirement_ids"))
        != exact_requirements
    ):
        raise ValueError("learning decision v3 projection is invalid")

    public_rows = market.get("vacancies")
    if not isinstance(public_rows, list):
        raise ValueError("learning decision v3 projection is invalid")
    public_order: dict[str, str] = {}
    for index, vacancy in enumerate(public_rows, 1):
        identifier = vacancy.get("vacancy_id") if isinstance(vacancy, Mapping) else None
        if not isinstance(identifier, str) or identifier in public_order:
            raise ValueError("learning decision v3 projection is invalid")
        public_order[identifier] = f"V{index}"
    try:
        ordinals = sorted(public_order[identifier] for identifier in exact_vacancies)
    except KeyError:
        raise ValueError("learning decision v3 projection is invalid") from None

    recurrence = f"{len(exact_vacancies)}/{active_count}"
    if recurrence != eligibility.get("recurrence"):
        raise ValueError("learning decision v3 projection is invalid")

    terms = dossier.get("requested_technology_terms")
    if not isinstance(terms, list):
        raise ValueError("learning decision v3 projection is invalid")
    labels = [
        row.get("term")
        for row in terms
        if isinstance(row, Mapping) and _normalized_signal(row.get("term")) == signal
    ]
    if len(labels) != 1 or not isinstance(labels[0], str):
        raise ValueError("learning decision v3 projection is invalid")

    route = {
        "signal": signal,
        "term_label": labels[0],
        "support_state": support,
        "recurrence": recurrence,
        "vacancy_ordinals": ordinals,
    }
    unions = {
        "claim_ids": _sorted_unique_strings(binding.get("claim_ids")),
        "source_evidence_ids": _sorted_unique_strings(binding.get("evidence_ids")),
        "requirement_ids": exact_requirements,
        "vacancy_ids": exact_vacancies,
        "target_role_families": sorted(role_families),
    }
    return route, unions


def _provider_projection(
    action: str,
    eligibility: Mapping[str, object],
    provider: Mapping[str, object] | None,
    signal: str,
) -> tuple[str | None, str, str, str | None]:
    selected = eligibility.get("selected_provider_option_id")
    if action != "research_provider_option":
        if selected is not None or provider is not None:
            raise ValueError("learning decision v3 projection is invalid")
        return None, _ACTION_RULES[action]["option_type"], "candidate_owned", None
    if not isinstance(selected, str) or not isinstance(provider, Mapping):
        raise ValueError("learning decision v3 projection is invalid")
    options = provider.get("options")
    if not isinstance(options, list):
        raise ValueError("learning decision v3 projection is invalid")
    matches = [
        option
        for option in options
        if isinstance(option, Mapping) and option.get("option_id") == selected
    ]
    if len(matches) != 1:
        raise ValueError("learning decision v3 projection is invalid")
    option = matches[0]
    covered = option.get("covered_signals")
    option_type = option.get("option_type")
    owner = option.get("provider")
    option_name = option.get("option")
    if (
        option.get("source_state") != "active"
        or option.get("availability") != "available"
        or not isinstance(covered, list)
        or signal not in covered
        or option_type not in {"course", "certification"}
        or not isinstance(owner, str)
        or not isinstance(option_name, str)
    ):
        raise ValueError("learning decision v3 projection is invalid")
    return selected, option_type, owner, option_name


def project_career_learning_decision_v3(
    locale: str,
    eligibility: Mapping[str, object],
    alignment: Mapping[str, object],
    research: Mapping[str, object],
    market_dossier: Mapping[str, object],
    executive_dossier: Mapping[str, object],
    provider_research: Mapping[str, object] | None,
) -> dict[str, object] | None:
    """Return the sole source-projected learning row, or no row."""
    try:
        action = eligibility.get("recommended_next_action")
        if action not in LEARNING_ACTIONS:
            return None
        if not isinstance(action, str) or locale not in COPY:
            raise ValueError("learning decision v3 projection is invalid")
        rule = _ACTION_RULES[action]
        signal = eligibility.get("selected_signal")
        relation = eligibility.get("candidate_relation")
        if (
            not isinstance(signal, str)
            or _SIGNAL.fullmatch(signal) is None
            or relation != rule["relation"]
        ):
            raise ValueError("learning decision v3 projection is invalid")
        route, unions = _exact_source_route(
            signal,
            eligibility,
            alignment,
            research,
            market_dossier,
            executive_dossier,
        )
        provider_id, option_type, owner, provider_option_name = _provider_projection(
            action, eligibility, provider_research, signal
        )
        localized = COPY[locale]
        option_name = provider_option_name
        if option_name is None:
            templates = localized["option_names"]
            if not isinstance(templates, Mapping):
                raise ValueError("learning decision v3 projection is invalid")
            template = templates.get(action)
            if not isinstance(template, str):
                raise ValueError("learning decision v3 projection is invalid")
            option_name = template.format(signal=route["term_label"])
        bases = localized["decision_bases"]
        if not isinstance(bases, Mapping) or not isinstance(bases.get(action), str):
            raise ValueError("learning decision v3 projection is invalid")
        return {
            "decision_rank": 1,
            "decision_code": action,
            "source_signals": [signal],
            "provider_option_id": provider_id,
            **unions,
            "gap_type": rule["gap_type"],
            "option_type": option_type,
            "decision": rule["decision"],
            "option_name": option_name,
            "provider_or_owner": owner,
            "signal_routes": [route],
            "cost_time_band": localized["cost_time_band"],
            "expected_signal_boundary": localized["expected_signal_boundary"],
            "portfolio_or_no_learning_alternative": localized[
                "portfolio_or_no_learning_alternative"
            ],
            "overbuying_risk": localized["overbuying_risk"],
            "decision_basis": bases[action],
            "next_action_gate": localized["next_action_gate"],
            "outcome_boundary": _OUTCOME_BOUNDARY,
            "draft_only": True,
            "no_external_action": True,
        }
    except Exception:
        raise ValueError("learning decision v3 projection is invalid") from None
