#!/usr/bin/env python3
"""Recompute one vacancy-first career next-action eligibility decision."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any


def _sibling(name: str) -> Any:
    path = Path(__file__).with_name(name)
    specification = importlib.util.spec_from_file_location(f"_pgc_{path.stem}", path)
    if specification is None or specification.loader is None:
        raise RuntimeError("required eligibility dependency is unavailable")
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


_snapshot = _sibling("semantic_provenance_snapshot.py")
_response_builder = _sibling("build_candidate_gap_response_v1.py")
_response_validator = _sibling("validate_candidate_gap_response_v1.py")
_assessment_builder = _sibling("build_candidate_gap_assessment_v1.py")
_assessment_validator = _sibling("validate_candidate_gap_assessment_v1.py")
_alignment = _sibling("derive_candidate_market_alignment_v2.py")

bounded_plain_snapshot = _snapshot.bounded_plain_snapshot
SCHEMA_VERSION = "career-next-action-eligibility-v1"
_SOURCE_FIELDS = frozenset(
    {
        "research",
        "executive_dossier",
        "market_dossier",
        "gap_response",
        "gap_assessment",
        "provider_research",
    }
)


def _frozen_row(**values: str) -> Mapping[str, str]:
    return MappingProxyType(values)


ELIGIBILITY_RULES: Mapping[str, Mapping[str, str]] = MappingProxyType(
    {
        "unavailable": _frozen_row(
            state="unavailable",
            decision_basis_code="market_unavailable",
            recommended_next_action="no_learning_yet",
        ),
        "selection_required": _frozen_row(
            state="selection_required",
            decision_basis_code="selection_missing",
            recommended_next_action="select_target_vacancy_and_signal",
        ),
        "insufficient_recurrence": _frozen_row(
            state="insufficient_recurrence",
            decision_basis_code="recurrence_below_two",
            recommended_next_action="prepare_private_vacancy_packet",
        ),
        "gap_unknown": _frozen_row(
            state="insufficient_gap_evidence",
            decision_basis_code="gap_unknown",
            recommended_next_action="confirm_gap_relation",
        ),
        "supported": _frozen_row(
            state="insufficient_gap_evidence",
            decision_basis_code="candidate_supported",
            recommended_next_action="prepare_private_vacancy_packet",
        ),
        "provider_choice": _frozen_row(
            state="provider_selection_required",
            decision_basis_code="provider_choice_missing",
            recommended_next_action="select_provider_option",
        ),
        "provider_evidence": _frozen_row(
            state="provider_evidence_required",
            decision_basis_code="provider_evidence_missing",
            recommended_next_action="no_learning_yet",
        ),
        "experience": _frozen_row(
            state="learning_not_applicable",
            decision_basis_code="professional_experience_required",
            recommended_next_action="prepare_private_vacancy_packet",
        ),
        "proof": _frozen_row(
            state="eligible",
            decision_basis_code="proof_gap_recurrent",
            recommended_next_action="build_bounded_proof",
        ),
        "practice": _frozen_row(
            state="eligible",
            decision_basis_code="practice_gap_recurrent",
            recommended_next_action="run_validation_lab",
        ),
        "terminology": _frozen_row(
            state="eligible",
            decision_basis_code="terminology_gap_recurrent",
            recommended_next_action="run_role_search_experiment",
        ),
        "knowledge": _frozen_row(
            state="eligible",
            decision_basis_code="knowledge_gap_recurrent_provider_selected",
            recommended_next_action="research_provider_option",
        ),
    }
)


def _action_copy(
    label: str, private_deliverable: str, done_when: str
) -> Mapping[str, str]:
    return MappingProxyType(
        {
            "label": label,
            "private_deliverable": private_deliverable,
            "done_when": done_when,
        }
    )


def _locale_copy(
    *,
    states: Mapping[str, str],
    relations: Mapping[str, str],
    actions: Mapping[str, Mapping[str, str]],
    boundary: str,
) -> Mapping[str, object]:
    return MappingProxyType(
        {
            "states": MappingProxyType(dict(states)),
            "relations": MappingProxyType(dict(relations)),
            "actions": MappingProxyType(dict(actions)),
            "boundaries": MappingProxyType(
                {
                    "not_an_interview_offer_salary_or_hiring_prediction": boundary
                }
            ),
        }
    )


COPY: Mapping[str, Mapping[str, object]] = MappingProxyType(
    {
        "es": _locale_copy(
            states={
                "selection_required": "Elige una pareja válida de vacante y señal (V1–Vn) para decidir el siguiente paso; no se preselecciona ninguna.",
                "insufficient_recurrence": "La señal aparece en {recurrence}; no alcanza el umbral de dos vacantes activas.",
                "gap_unknown": "La relación de brecha todavía no está confirmada.",
                "candidate_supported": "La señal está respaldada; ese respaldo no demuestra una brecha.",
                "provider_selection_required": "Hay recurrencia y una brecha de conocimiento confirmada; falta elegir una opción oficial verificada.",
                "provider_evidence_required": "Hay recurrencia y una brecha de conocimiento confirmada, pero no hay una opción oficial verificada para esta señal.",
                "learning_not_applicable": "La brecha requiere experiencia profesional o de producción; un laboratorio, curso o certificación no la sustituye.",
                "eligible": "La señal aparece en {recurrence} y la relación {relation_label} fue confirmada por la persona candidata.",
            },
            relations={
                "proof_gap": "brecha de evidencia práctica",
                "practice_gap": "brecha de práctica",
                "terminology_gap": "brecha de terminología",
                "knowledge_gap": "brecha de conocimiento",
            },
            actions={
                "select_target_vacancy_and_signal": _action_copy(
                    "Elige vacante y señal",
                    "Una pareja pública Vn + señal elegida por ti.",
                    "La vacante y la señal pertenecen a la misma vacante activa.",
                ),
                "confirm_gap_relation": _action_copy(
                    "Confirma la relación de brecha",
                    "Una respuesta estructurada, sin prosa libre, para la señal elegida.",
                    "La relación queda confirmada o marcada como desconocida.",
                ),
                "prepare_private_vacancy_packet": _action_copy(
                    "Prepara primero el paquete privado de vacante",
                    "Un borrador privado y verificable para la vacante elegida; no se envía.",
                    "Cada afirmación está respaldada o marcada para confirmar u omitir.",
                ),
                "build_bounded_proof": _action_copy(
                    "Construye una prueba acotada",
                    "Una prueba privada e inspeccionable de la señal elegida.",
                    "La prueba muestra alcance, acción y resultado sin afirmar producción no demostrada.",
                ),
                "run_validation_lab": _action_copy(
                    "Ejecuta un laboratorio de práctica",
                    "Un laboratorio privado y acotado para practicar la señal.",
                    "El resultado es inspeccionable y no se presenta como experiencia profesional.",
                ),
                "select_provider_option": _action_copy(
                    "Elige una opción oficial para investigar",
                    "Una opción pública elegida explícitamente; no es una recomendación de compra.",
                    "La opción activa cubre la señal exacta y su fuente oficial está fechada.",
                ),
                "research_provider_option": _action_copy(
                    "Investiga la opción elegida",
                    "Una revisión privada de costo, tiempo, requisitos y desconocidos.",
                    "Costo, tiempo, requisitos y mantenimiento están confirmados o marcados como desconocidos.",
                ),
                "run_role_search_experiment": _action_copy(
                    "Prueba una búsqueda acotada de roles",
                    "Una búsqueda privada con la terminología elegida; no se postula.",
                    "La consulta devuelve evidencia fechada o queda registrada como no disponible.",
                ),
                "no_learning_yet": _action_copy(
                    "No compres aprendizaje todavía",
                    "Una nota privada de la evidencia de proveedor que falta.",
                    "Existe una fuente oficial vigente o la decisión permanece aplazada.",
                ),
            },
            boundary="Límite: esta decisión usa evidencia documentada; no predice entrevista, oferta, salario ni contratación y no ejecuta ninguna acción externa.",
        ),
        "en": _locale_copy(
            states={
                "selection_required": "Choose one valid vacancy-and-signal pair (V1–Vn) to decide the next step; none is preselected.",
                "insufficient_recurrence": "The signal appears in {recurrence}; it does not meet the two-active-vacancy threshold.",
                "gap_unknown": "The gap relation is not confirmed yet.",
                "candidate_supported": "The signal is supported; that support does not establish a gap.",
                "provider_selection_required": "Recurrence and a confirmed knowledge gap exist; one verified official option still needs to be selected.",
                "provider_evidence_required": "Recurrence and a confirmed knowledge gap exist, but no verified official option covers this signal.",
                "learning_not_applicable": "The gap requires professional or production experience; a lab, course, or certification cannot substitute for it.",
                "eligible": "The signal appears in {recurrence}, and the {relation_label} relation was candidate-confirmed.",
            },
            relations={
                "proof_gap": "proof gap",
                "practice_gap": "practice gap",
                "terminology_gap": "terminology gap",
                "knowledge_gap": "knowledge gap",
            },
            actions={
                "select_target_vacancy_and_signal": _action_copy(
                    "Choose vacancy and signal",
                    "One public Vn + signal pair chosen by you.",
                    "The vacancy and signal belong to the same active vacancy.",
                ),
                "confirm_gap_relation": _action_copy(
                    "Confirm the gap relation",
                    "One structured response without free-form prose for the selected signal.",
                    "The relation is confirmed or marked unknown.",
                ),
                "prepare_private_vacancy_packet": _action_copy(
                    "Prepare the private vacancy packet first",
                    "One private, verifiable draft for the selected vacancy; it is not sent.",
                    "Every claim is supported or marked to confirm or omit.",
                ),
                "build_bounded_proof": _action_copy(
                    "Build one bounded proof",
                    "One private, inspectable proof for the selected signal.",
                    "The proof shows scope, action, and result without claiming unsupported production work.",
                ),
                "run_validation_lab": _action_copy(
                    "Run one practice lab",
                    "One private, bounded lab for practicing the signal.",
                    "The result is inspectable and is not presented as professional experience.",
                ),
                "select_provider_option": _action_copy(
                    "Choose one official option to research",
                    "One explicitly selected public option; this is not a purchase recommendation.",
                    "The active option covers the exact signal and has a dated official source.",
                ),
                "research_provider_option": _action_copy(
                    "Research the selected option",
                    "One private review of cost, time, prerequisites, and unknowns.",
                    "Cost, time, prerequisites, and maintenance are confirmed or marked unknown.",
                ),
                "run_role_search_experiment": _action_copy(
                    "Run one bounded role-search experiment",
                    "One private search using the selected terminology; no application is submitted.",
                    "The query returns dated evidence or is recorded as unavailable.",
                ),
                "no_learning_yet": _action_copy(
                    "Do not buy learning yet",
                    "One private note of the missing provider evidence.",
                    "A current official source exists or the decision remains deferred.",
                ),
            },
            boundary="Boundary: this decision uses documented evidence; it predicts neither an interview, offer, salary, nor hiring outcome and performs no external action.",
        ),
    }
)


@dataclass(frozen=True)
class _ValidatedGroup:
    research: Mapping[str, object]
    dossier: Mapping[str, object]
    market: Mapping[str, object]
    response: Mapping[str, object]
    assessment: Mapping[str, object]
    provider: Mapping[str, object] | None
    research_snapshot: str
    dossier_snapshot: str
    market_snapshot: str
    provider_snapshot: str | None


def _canonical_snapshot(prefix: str, value: Mapping[str, object]) -> str:
    canonical = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return f"{prefix}{digest}"


def _validated_group(frozen_group: Mapping[str, object]) -> _ValidatedGroup:
    if set(frozen_group) != _SOURCE_FIELDS:
        raise ValueError("career next-action eligibility is invalid")
    assessment_group = {
        "value": frozen_group["gap_assessment"],
        "research": frozen_group["research"],
        "executive_dossier": frozen_group["executive_dossier"],
        "market_dossier": frozen_group["market_dossier"],
        "gap_response": frozen_group["gap_response"],
        "provider_research": frozen_group["provider_research"],
    }
    if _assessment_validator._validate_candidate_gap_assessment_from_frozen(
        assessment_group
    ):
        raise ValueError("career next-action eligibility is invalid")
    response_group = {
        "value": frozen_group["gap_response"],
        "research": frozen_group["research"],
        "market_dossier": frozen_group["market_dossier"],
        "provider_research": frozen_group["provider_research"],
    }
    if _response_validator._validate_candidate_gap_response_from_frozen(response_group):
        raise ValueError("career next-action eligibility is invalid")
    (
        research,
        dossier,
        market,
        response,
        provider,
        research_snapshot,
        dossier_snapshot,
        market_snapshot,
        provider_snapshot,
    ) = _assessment_builder._validated_group(
        {
            "research": frozen_group["research"],
            "executive_dossier": frozen_group["executive_dossier"],
            "market_dossier": frozen_group["market_dossier"],
            "gap_response": frozen_group["gap_response"],
            "provider_research": frozen_group["provider_research"],
        }
    )
    assessment = frozen_group["gap_assessment"]
    if not isinstance(assessment, Mapping):
        raise ValueError("career next-action eligibility is invalid")
    return _ValidatedGroup(
        research,
        dossier,
        market,
        response,
        assessment,
        provider,
        research_snapshot,
        dossier_snapshot,
        market_snapshot,
        provider_snapshot,
    )


def _selected_alignment(
    alignment: Mapping[str, object], signal: str
) -> Mapping[str, object]:
    rows = alignment.get("signal_bindings")
    if not isinstance(rows, list):
        raise ValueError("career next-action eligibility is invalid")
    matches = [
        row
        for row in rows
        if isinstance(row, Mapping) and row.get("signal") == signal
    ]
    if len(matches) != 1:
        raise ValueError("career next-action eligibility is invalid")
    return matches[0]


def _selection_values(
    validated: _ValidatedGroup,
) -> tuple[str, str, str, str, int, str]:
    selected_vacancy_id = validated.assessment.get("selected_vacancy_id")
    selected_signal = validated.assessment.get("selected_signal")
    rows = validated.assessment.get("assessments")
    if (
        not isinstance(selected_vacancy_id, str)
        or not isinstance(selected_signal, str)
        or not isinstance(rows, list)
        or len(rows) != 1
        or not isinstance(rows[0], Mapping)
        or rows[0].get("signal") != selected_signal
        or not isinstance(rows[0].get("relation"), str)
    ):
        raise ValueError("career next-action eligibility is invalid")
    relation = rows[0]["relation"]
    market_vacancies = validated.market.get("vacancies")
    if not isinstance(market_vacancies, list):
        raise ValueError("career next-action eligibility is invalid")
    ordinals = [
        index
        for index, vacancy in enumerate(market_vacancies, 1)
        if isinstance(vacancy, Mapping)
        and vacancy.get("vacancy_id") == selected_vacancy_id
    ]
    if len(ordinals) != 1:
        raise ValueError("career next-action eligibility is invalid")
    research_vacancies = validated.research.get("vacancies")
    if not isinstance(research_vacancies, list):
        raise ValueError("career next-action eligibility is invalid")
    active_ids: set[str] = set()
    recurring_ids: set[str] = set()
    selected_has_signal = False
    for vacancy in research_vacancies:
        if not isinstance(vacancy, Mapping) or vacancy.get("source_state") != "active":
            continue
        vacancy_id = vacancy.get("vacancy_id")
        requirements = vacancy.get("requirements")
        if not isinstance(vacancy_id, str) or not isinstance(requirements, list):
            raise ValueError("career next-action eligibility is invalid")
        active_ids.add(vacancy_id)
        has_signal = any(
            isinstance(requirement, Mapping)
            and requirement.get("signal") == selected_signal
            for requirement in requirements
        )
        if has_signal:
            recurring_ids.add(vacancy_id)
        if vacancy_id == selected_vacancy_id:
            selected_has_signal = has_signal
    if not selected_has_signal or not active_ids:
        raise ValueError("career next-action eligibility is invalid")
    return (
        selected_vacancy_id,
        selected_signal,
        relation,
        f"{len(recurring_ids)}/{len(active_ids)}",
        len(recurring_ids),
        f"V{ordinals[0]}",
    )


def _provider_choices(
    validated: _ValidatedGroup, signal: str
) -> list[Mapping[str, object]]:
    if validated.provider is None:
        return []
    return _response_builder._eligible_provider_choices(validated.provider, signal)


def _project_eligibility(
    validated: _ValidatedGroup, alignment: Mapping[str, object]
) -> dict[str, object]:
    assessment_state = validated.assessment.get("state")
    selection: tuple[str, str, str, str, int, str] | None = None
    support_state: str | None = None
    public_choices: list[dict[str, object]] = []
    selected_provider_option_id: str | None = None
    if assessment_state == "unavailable":
        rule_key = "unavailable"
    elif assessment_state == "selection_required":
        rule_key = "selection_required"
    else:
        selection = _selection_values(validated)
        selected_vacancy_id, selected_signal, relation, recurrence, occurrences, _ordinal = selection
        support = _selected_alignment(alignment, selected_signal).get("support_state")
        if support not in {"verified_match", "candidate_reported_match", "unknown"}:
            raise ValueError("career next-action eligibility is invalid")
        support_state = support
        if occurrences < 2:
            rule_key = "insufficient_recurrence"
        elif relation == "unknown":
            rule_key = "gap_unknown"
        elif relation == "supported":
            rule_key = "supported"
        elif relation == "professional_experience_gap":
            rule_key = "experience"
        elif relation == "proof_gap":
            rule_key = "proof"
        elif relation == "practice_gap":
            rule_key = "practice"
        elif relation == "terminology_gap":
            rule_key = "terminology"
        elif relation == "knowledge_gap":
            choices = _provider_choices(validated, selected_signal)
            selected = validated.assessment.get("selected_provider_option_id")
            if not choices:
                if selected is not None:
                    raise ValueError("career next-action eligibility is invalid")
                rule_key = "provider_evidence"
            elif selected is None:
                rule_key = "provider_choice"
                public_choices = [
                    {
                        "public_provider_ordinal": f"L{index}",
                        "option_name": option["option"],
                        "provider_or_owner": option["provider"],
                    }
                    for index, option in enumerate(choices, 1)
                ]
            else:
                if not isinstance(selected, str) or not any(
                    option.get("option_id") == selected for option in choices
                ):
                    raise ValueError("career next-action eligibility is invalid")
                rule_key = "knowledge"
                selected_provider_option_id = selected
        else:
            raise ValueError("career next-action eligibility is invalid")
    rule = ELIGIBILITY_RULES[rule_key]
    action = rule["recommended_next_action"]
    locale = validated.research.get("locale")
    if locale not in COPY:
        raise ValueError("career next-action eligibility is invalid")
    action_copy = COPY[locale]["actions"][action]
    if not isinstance(action_copy, Mapping):
        raise ValueError("career next-action eligibility is invalid")
    alignment_snapshot = _alignment.snapshot_for_alignment_v2(alignment)
    return {
        "schema_version": SCHEMA_VERSION,
        "locale": locale,
        "as_of_date": validated.research["as_of_date"],
        "state": rule["state"],
        "source_research_snapshot": validated.research_snapshot,
        "source_dossier_snapshot": validated.dossier_snapshot,
        "source_alignment_snapshot": alignment_snapshot,
        "source_market_snapshot": validated.market_snapshot,
        "source_gap_response_snapshot": _assessment_builder._snapshot_for_frozen_gap_response(
            validated.response
        ),
        "source_gap_assessment_snapshot": _canonical_snapshot(
            "snap-gap-assessment-v1-sha256-", validated.assessment
        ),
        "source_provider_research_snapshot": validated.provider_snapshot,
        "selected_vacancy_id": selection[0] if selection is not None else None,
        "selected_signal": selection[1] if selection is not None else None,
        "selected_provider_option_id": selected_provider_option_id,
        "public_vacancy_ordinal": selection[5] if selection is not None else None,
        "recurrence": selection[3] if selection is not None else None,
        "candidate_support_state": support_state,
        "candidate_relation": selection[2] if selection is not None else None,
        "recommended_next_action": action,
        "decision_basis_code": rule["decision_basis_code"],
        "eligible_provider_choices": public_choices,
        "private_deliverable": action_copy["private_deliverable"],
        "done_when": action_copy["done_when"],
        "privacy_boundary": "identity_free_structured_eligibility_only",
        "draft_only": True,
        "no_external_action": True,
        "outcome_boundary": "not_an_interview_offer_salary_or_hiring_prediction",
    }


def _project_eligibility_from_frozen(
    frozen_group: Mapping[str, object],
) -> dict[str, object]:
    """Project only from one already captured built-in source group."""
    validated = _validated_group(frozen_group)
    alignment = _alignment.derive_candidate_market_alignment_v2(
        validated.research, validated.dossier
    )
    return _project_eligibility(validated, alignment)


def build_career_next_action_eligibility_v1(
    research: object,
    executive_dossier: object,
    market_dossier: object,
    gap_response: object,
    gap_assessment: object,
    provider_research: object | None = None,
) -> dict[str, object]:
    """Capture once and recompute the sole next-action authority."""
    try:
        frozen = bounded_plain_snapshot(
            {
                "research": research,
                "executive_dossier": executive_dossier,
                "market_dossier": market_dossier,
                "gap_response": gap_response,
                "gap_assessment": gap_assessment,
                "provider_research": provider_research,
            }
        )
        return _project_eligibility_from_frozen(frozen)
    except Exception:
        raise ValueError("career next-action eligibility is invalid") from None
