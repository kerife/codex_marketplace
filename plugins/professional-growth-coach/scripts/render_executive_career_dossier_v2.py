#!/usr/bin/env python3
"""Render the private LinkedIn coaching dossier v2 by composing v1 surfaces."""

from __future__ import annotations

import argparse
import copy
import html
import importlib.util
import json
import os
import re
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any


def _sibling(name: str) -> Any:
    path = Path(__file__).with_name(name)
    specification = importlib.util.spec_from_file_location(f"_pgc_v2_{path.stem}", path)
    if specification is None or specification.loader is None:
        raise RuntimeError("required dossier module is unavailable")
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


def _sibling_with_local_imports(name: str) -> Any:
    scripts_root = str(Path(__file__).resolve().parent)
    inserted = scripts_root not in sys.path
    if inserted:
        sys.path.insert(0, scripts_root)
    try:
        return _sibling(name)
    finally:
        if inserted:
            sys.path.remove(scripts_root)


VALIDATOR = _sibling("validate_executive_career_dossier_v2.py")
MARKET_VALIDATOR = _sibling_with_local_imports("validate_career_market_learning_dossier.py")
LEARNING_VALIDATOR = _sibling_with_local_imports("validate_career_learning_decision.py")
RESEARCH_VALIDATOR = _sibling("validate_target_vacancy_research.py")
COMPAT = _sibling("executive_career_dossier_v2_compat.py")
BASE = _sibling("render_executive_career_dossier.py")

ASSET_ROOT = Path(__file__).resolve().parents[1] / "assets"
TEMPLATE_PATH = ASSET_ROOT / "executive-career-dossier-v1.html"
BASE_CSS_PATH = ASSET_ROOT / "executive-career-dossier-v1.css"
CSS_PATH = ASSET_ROOT / "executive-career-dossier-v2.css"
MARKET_CSS_PATH = ASSET_ROOT / "career-market-learning-dossier-v1.css"

DossierValidationError = BASE.DossierValidationError
RenderReceipt = BASE.RenderReceipt


class MarketInputLoadError(ValueError):
    """A bounded market composition input could not be loaded."""


SECTION_LABELS = {
    "es": {
        "photo": "Foto", "banner": "Banner", "name": "Nombre",
        "profile_url": "URL del perfil", "headline": "Titular", "location": "Ubicación",
        "contact_info": "Información de contacto", "about": "Acerca de",
        "experience": "Experiencia", "skills": "Aptitudes", "featured": "Destacado",
        "certifications": "Certificaciones", "education": "Educación",
        "recommendations": "Recomendaciones", "activity": "Actividad",
        "analytics": "Analítica", "job_preferences": "Preferencias de empleo",
    },
    "en": {
        "photo": "Photo", "banner": "Banner", "name": "Name",
        "profile_url": "Profile URL", "headline": "Headline", "location": "Location",
        "contact_info": "Contact information", "about": "About", "experience": "Experience",
        "skills": "Skills", "featured": "Featured", "certifications": "Certifications",
        "education": "Education", "recommendations": "Recommendations", "activity": "Activity",
        "analytics": "Analytics", "job_preferences": "Job preferences",
    },
}

AVAILABILITY_LABELS = {
    "es": {
        "inspected_present": "Revisada y presente", "inspected_absent": "Revisada y ausente",
        "candidate_supplied": "Material proporcionado", "unavailable": "No disponible",
    },
    "en": {
        "inspected_present": "Inspected and present", "inspected_absent": "Inspected and absent",
        "candidate_supplied": "Candidate-supplied material", "unavailable": "Unavailable",
    },
}

REASON_LABELS = {
    "es": {
        "inspected_content_available": "Contenido revisado disponible",
        "inspected_section_absent": "La sección revisada está ausente",
        "candidate_material_supplied": "Material proporcionado para revisión",
        "authorization_required": "Autorización requerida",
        "inspection_declined": "Inspección declinada para esta sesión",
        "authorized_inspection_failed": "No se pudo completar la inspección autorizada",
    },
    "en": {
        "inspected_content_available": "Inspected content available",
        "inspected_section_absent": "Inspected section is absent",
        "candidate_material_supplied": "Material supplied for review",
        "authorization_required": "Authorization required",
        "inspection_declined": "Inspection declined for this session",
        "authorized_inspection_failed": "Authorized inspection could not be completed",
    },
}

REQUEST_DECISION_LABELS = {
    "es": {
        "pending_response": "Respuesta pendiente", "declined_for_session": "Declinada para esta sesión",
        "authorized_inspection_failed": "Inspección no completada",
    },
    "en": {
        "pending_response": "Response pending", "declined_for_session": "Declined for this session",
        "authorized_inspection_failed": "Inspection not completed",
    },
}

TEMPLATE_LABELS = {
    "es": {
        "context_action_result_v1": "Contexto, acción y resultado",
        "positioning_evidence_v1": "Posicionamiento y evidencia",
        "proof_scope_result_v1": "Prueba, alcance y resultado",
    },
    "en": {
        "context_action_result_v1": "Context, action, and result",
        "positioning_evidence_v1": "Positioning and evidence",
        "proof_scope_result_v1": "Proof, scope, and result",
    },
}

TEMPLATE_FIELD_LABELS = {
    "es": {
        "target_role": "Rol objetivo", "specialty": "Especialidad", "context": "Contexto",
        "action": "Acción", "scope": "Alcance", "result": "Resultado", "metric": "Métrica",
        "evidence_source": "Fuente de evidencia",
    },
    "en": {
        "target_role": "Target role", "specialty": "Specialty", "context": "Context",
        "action": "Action", "scope": "Scope", "result": "Result", "metric": "Metric",
        "evidence_source": "Evidence source",
    },
}

AUTHORIZATION_QUESTIONS = {
    locale: {
        section: (
            f"¿Autorizas inspeccionar en modo solo lectura la sección {label} durante esta sesión?"
            if locale == "es"
            else f"Do you authorize read-only inspection of the {label} section during this session?"
        )
        for section, label in labels.items()
    }
    for locale, labels in SECTION_LABELS.items()
}

COPY = {
    "es": {
        "decide_title": "Decide ahora",
        "decide_priorities": "Tres prioridades",
        "decide_coverage": "Cobertura visible",
        "decide_authorization": "Siguiente autorización",
        "decide_market": "Estado del mercado",
        "decide_reviewed": "Revisadas",
        "decide_provided": "Proporcionadas",
        "decide_unavailable": "No disponibles",
        "decide_sample": "Muestra validada",
        "decide_recurrence": "Señales recurrentes",
        "decide_no_market": "No hay puntuación ni recurrencia sin vacantes verificadas.",
        "decide_no_pending": "No hay una autorización pendiente en esta sesión.",
        "decide_navigation": "Navegación del resumen",
        "coverage_title": "Cobertura de secciones",
        "availability": "Disponibilidad", "reason": "Motivo", "request": "Decisión de inspección",
        "priorities": "Prioridades de coaching", "target": "Sección objetivo",
        "observation": "Observación", "why": "Por qué importa", "prompt": "Pregunta de coaching",
        "template": "Plantilla privada", "market_title": "Evidencia de mercado no disponible",
        "market_body": "Este dossier no incluye evidencia de mercado. Continúa con la evidencia del perfil ya revisada.",
        "market_available_title": "Evidencia de mercado fechada disponible",
        "market_available_body": "Hay evidencia de mercado fechada disponible para una revisión privada junto con la evidencia del perfil.",
        "template_boundary": "No incluyas texto sin procesar del perfil, datos de contacto ni valores privados.",
        "template_blank": "Espacio en blanco para completar en privado",
        "market_context": "Evidencia de mercado", "market_complete": "Cinco vacantes activas verificadas",
        "market_limited": "Muestra limitada de {count} vacantes activas verificadas",
        "market_limited_reason": "La búsqueda acotada terminó antes de reunir cinco vacantes.",
        "market_unavailable_reason": "La búsqueda acotada no produjo vacantes verificables para esta muestra.",
        "market_limitation": "Limitación de la muestra", "market_boundary": "La alineación es direccional y se basa sólo en evidencia documentada; no predice ajuste ni contratación.",
        "vacancy_alignment": "Alineación de evidencia por vacante", "score_boundary": "Puntuación direccional de evidencia documentada",
        "matrix_title": "Qué pide cada vacante y qué evidencia existe", "matrix_caption": "Matriz de evidencia de la muestra",
        "matrix_signal": "Señal", "matrix_profile": "Evidencia del perfil", "vacancy_key": "Clave de vacantes",
        "recurrence_title": "Señales recurrentes en la muestra", "recurrence_boundary": "La recurrencia describe sólo esta muestra validada; no representa demanda del mercado.",
        "gap_route": "Ruta para cerrar brechas", "gap_steps": ("Confirmar la brecha contra evidencia validada.", "Reunir una prueba práctica y acotada.", "Documentar el alcance sin inferir resultados.", "Revalidar si la nueva evidencia cambia la matriz."),
        "learning_title": "Qué estudiar —y qué no comprar aún—",
        "learning_intro": "Como coach, convierto las señales repetidas en decisiones de aprendizaje; primero revisamos la prueba y después decidimos si vale la pena pagar por conocimiento.",
        "learning_sample": "Muestra de vacantes revisada",
        "learning_target_role": "Rol objetivo",
        "learning_gap": "Brecha que estamos cerrando",
        "learning_option": "Opción",
        "learning_owner": "Proveedor o dueño",
        "learning_evidence": "Señal recurrente",
        "learning_basis": "Base de la decisión",
        "learning_cost_time": "Costo y tiempo",
        "learning_signal_boundary": "Señal esperada",
        "learning_source": "Fuente oficial",
        "learning_alternative": "Alternativa de menor costo",
        "learning_risk": "Riesgo de sobreinvertir",
        "learning_decision": "Decisión del coach",
        "learning_gate": "Siguiente revisión",
        "learning_boundary": "Esto es una hipótesis acotada de aprendizaje; no predice entrevista, oferta, salario ni retorno de inversión.",
        "learning_option_types": {"course": "Curso", "certification": "Certificación", "portfolio_project": "Proyecto de portafolio", "lab": "Laboratorio", "role_search": "Búsqueda de rol", "no_learning_yet": "Todavía no estudiar"},
        "learning_decisions": {"do_now": "Hazlo ahora", "defer": "Déjalo en pausa", "omit": "Omítelo por ahora", "research_first": "Investiga antes"},
        "learning_gap_types": {"knowledge": "Conocimiento", "proof": "Prueba", "experience": "Experiencia", "terminology": "Terminología", "low_return": "Bajo retorno"},
    },
    "en": {
        "decide_title": "Decide now",
        "decide_priorities": "Three priorities",
        "decide_coverage": "Visible coverage",
        "decide_authorization": "Next authorization",
        "decide_market": "Market state",
        "decide_reviewed": "Reviewed",
        "decide_provided": "Provided",
        "decide_unavailable": "Unavailable",
        "decide_sample": "Validated sample",
        "decide_recurrence": "Recurring signals",
        "decide_no_market": "No score or recurrence without verified vacancies.",
        "decide_no_pending": "There is no pending authorization in this session.",
        "decide_navigation": "Summary navigation",
        "coverage_title": "Section coverage", "availability": "Availability", "reason": "Reason",
        "request": "Inspection decision", "priorities": "Coaching priorities",
        "target": "Target section", "observation": "Observation", "why": "Why it matters",
        "prompt": "Coaching prompt", "template": "Private template",
        "market_title": "Market evidence unavailable",
        "market_body": "This dossier includes no market evidence. Continue with the profile evidence already reviewed.",
        "market_available_title": "Dated market evidence available",
        "market_available_body": "Dated market evidence is available for private review alongside the profile evidence.",
        "template_boundary": "Do not include raw profile text, contact data, or private values.",
        "template_blank": "Blank for private completion",
        "market_context": "Market evidence", "market_complete": "Five verified active vacancies",
        "market_limited": "Limited sample of {count} verified active vacancies",
        "market_limited_reason": "The bounded search ended before five vacancies were gathered.",
        "market_unavailable_reason": "The bounded search produced no verifiable vacancies for this sample.",
        "market_limitation": "Sample limitation", "market_boundary": "Alignment is directional and based only on documented evidence; it predicts neither fit nor hiring.",
        "vacancy_alignment": "Evidence alignment by vacancy", "score_boundary": "Directional documented-evidence score",
        "matrix_title": "What each vacancy requests and what evidence exists", "matrix_caption": "Sample evidence matrix",
        "matrix_signal": "Signal", "matrix_profile": "Profile evidence", "vacancy_key": "Vacancy key",
        "recurrence_title": "Recurring signals in the sample", "recurrence_boundary": "Recurrence describes only this validated sample; it does not represent market demand.",
        "gap_route": "Gap-closure route", "gap_steps": ("Confirm the gap against validated evidence.", "Gather one bounded practical proof.", "Document its scope without inferring outcomes.", "Revalidate whether the new evidence changes the matrix."),
        "learning_title": "What to study—and what not to buy yet",
        "learning_intro": "As your coach, I turn repeated signals into learning decisions; first we review the proof and then decide whether paying for knowledge is worth it.",
        "learning_sample": "Vacancy sample reviewed",
        "learning_target_role": "Target role",
        "learning_gap": "Gap we are closing",
        "learning_option": "Option",
        "learning_owner": "Provider or owner",
        "learning_evidence": "Recurring signal",
        "learning_basis": "Decision basis",
        "learning_cost_time": "Cost and time",
        "learning_signal_boundary": "Expected signal",
        "learning_source": "Official source",
        "learning_alternative": "Lower-cost alternative",
        "learning_risk": "Overinvestment risk",
        "learning_decision": "Coach decision",
        "learning_gate": "Next review",
        "learning_boundary": "This is a bounded learning hypothesis; it predicts neither an interview, offer, salary, nor return on investment.",
        "learning_option_types": {"course": "Course", "certification": "Certification", "portfolio_project": "Portfolio project", "lab": "Lab", "role_search": "Role search", "no_learning_yet": "No learning yet"},
        "learning_decisions": {"do_now": "Do now", "defer": "Defer", "omit": "Omit for now", "research_first": "Research first"},
        "learning_gap_types": {"knowledge": "Knowledge", "proof": "Proof", "experience": "Experience", "terminology": "Terminology", "low_return": "Low return"},
    },
}

MATRIX_STATE_COPY = {
    "verified_match": ("✓", "Evidencia directa", "Direct evidence"),
    "candidate_reported_match": ("●", "Reportado por cliente", "Candidate reported"),
    "adjacent_evidence": ("≈", "Evidencia adyacente", "Adjacent evidence"),
    "explicit_gap": ("!", "Brecha confirmada", "Confirmed gap"),
    "unknown": ("?", "No verificado", "Not verified"),
    "not_required": ("—", "No solicitado", "Not requested"),
}

TRACE_STEP_LABELS = {
    "es": ("Prioridad", "Evidencia disponible", "Plantilla privada", "Permiso de lectura"),
    "en": ("Priority", "Available evidence", "Private template", "Read-only permission"),
}

TRACE_EVIDENCE_LABELS = {
    "es": {
        "verified": "Evidencia directa",
        "candidate_reported": "Reportado por cliente",
        "inferred": "Inferido, requiere confirmación",
        "unknown": "No verificado",
    },
    "en": {
        "verified": "Direct evidence",
        "candidate_reported": "Candidate reported",
        "inferred": "Inferred, requires confirmation",
        "unknown": "Not verified",
    },
}

TRACE_INSPECTION_LABELS = {
    "es": {
        "inspected_present": "Revisada y presente",
        "inspected_absent": "Revisada y ausente",
        "candidate_supplied": "Material proporcionado",
        "pending": "Respuesta pendiente",
        "pending_other": "Otra inspección está pendiente",
        "declined": "Declinada para esta sesión",
        "failed": "Inspección no completada",
        "unavailable": "No disponible",
    },
    "en": {
        "inspected_present": "Inspected and present",
        "inspected_absent": "Inspected and absent",
        "candidate_supplied": "Candidate-supplied material",
        "pending": "Response pending",
        "pending_other": "Another section is pending",
        "declined": "Declined for this session",
        "failed": "Inspection not completed",
        "unavailable": "Unavailable",
    },
}

TRACE_INSPECTION_LINK_LABELS = {
    "es": "Ver la tarjeta Decide ahora",
    "en": "View the Decide now card",
}

TRACE_BOUNDARY = {
    "es": "No se ejecuta ninguna acción externa; cualquier acción posterior requiere autorización separada.",
    "en": "No external action is executed; any later action requires separate authorization.",
}

TRACE_RAW_REFERENCE_RE = re.compile(r"\b(?:E-\d{3}|CAP-\d{3})\b")
TRACE_MARKET_STATES = frozenset({"complete", "limited_market_evidence", "market_evidence_unavailable"})


def _trace_market_preflight(value: object) -> None:
    """Reject malformed direct market graphs before projection can inspect them."""
    if not isinstance(value, Mapping):
        raise DossierValidationError(["decision trace market is unavailable"])
    pending: list[tuple[str, object, int]] = [("visit", value, 0)]
    active: set[int] = set()
    nodes = 0
    while pending:
        operation, current, depth = pending.pop()
        if operation == "leave":
            active.discard(id(current))
            continue
        if not isinstance(current, (Mapping, list, tuple)):
            continue
        if depth > 12 or id(current) in active:
            raise DossierValidationError(["decision trace market is unavailable"])
        nodes += 1
        if nodes > 10_000:
            raise DossierValidationError(["decision trace market is unavailable"])
        active.add(id(current))
        pending.append(("leave", current, depth))
        children = current.values() if isinstance(current, Mapping) else current
        pending.extend(("visit", child, depth + 1) for child in children)
    if value.get("state") not in TRACE_MARKET_STATES or not isinstance(value.get("vacancies"), (list, tuple)):
        raise DossierValidationError(["decision trace market is unavailable"])


def _trace_safe_paraphrase(value: object) -> str:
    """Apply the learning bundle prose/privacy guards to evidence display text."""
    if not isinstance(value, str):
        raise DossierValidationError(["decision trace evidence is unavailable"])
    try:
        safe_text = LEARNING_VALIDATOR._text(value)
        unsafe_semantics = LEARNING_VALIDATOR._text_has_identity_action_or_outcome_risk(value)
        v1 = VALIDATOR._v1
        privacy_errors = v1._privacy_errors(value)
        unsafe_action = v1.candidate_text_has_external_action(value)
        unsafe_outcome = v1.candidate_text_has_outcome_guarantee(value)
    except (AttributeError, TypeError, ValueError):
        raise DossierValidationError(["decision trace evidence is unavailable"]) from None
    if (
        not safe_text
        or unsafe_semantics
        or privacy_errors
        or unsafe_action
        or unsafe_outcome
        or TRACE_RAW_REFERENCE_RE.search(value)
    ):
        raise DossierValidationError(["decision trace evidence is unavailable"])
    return value


def _derive_decision_trace(
    priority: Mapping[str, object],
    dossier: Mapping[str, object],
    market_dossier: Mapping[str, object],
    locale: str,
) -> Mapping[str, object]:
    """Project one validated market priority into immutable display data."""
    if locale not in TRACE_STEP_LABELS or not isinstance(priority, Mapping):
        raise DossierValidationError(["decision trace input is unavailable"])
    try:
        _trace_market_preflight(market_dossier)
        plain_dossier = _plain(dossier)
        dossier_errors = VALIDATOR.validate_dossier(plain_dossier)
        if dossier_errors:
            raise DossierValidationError(dossier_errors)
        target = priority.get("target_section")
        if not isinstance(target, str) or target not in SECTION_LABELS[locale]:
            raise DossierValidationError(["decision trace target section is unavailable"])
        evidence_ids = priority.get("evidence_ids")
        if not isinstance(evidence_ids, (list, tuple)):
            raise DossierValidationError(["decision trace evidence references are unavailable"])
        records = {
            row.get("id"): row
            for row in BASE._rows(dossier.get("evidence"))
            if isinstance(row.get("id"), str)
        }
        evidence_views: list[dict[str, object]] = []
        for evidence_id in evidence_ids:
            record = records.get(evidence_id) if isinstance(evidence_id, str) else None
            if record is None or record.get("profile_section") != target:
                raise DossierValidationError(["decision trace evidence reference is unavailable"])
            state = record.get("state")
            paraphrase = record.get("paraphrase")
            if state not in TRACE_EVIDENCE_LABELS[locale] or not isinstance(paraphrase, str):
                raise DossierValidationError(["decision trace evidence is unavailable"])
            paraphrase = _trace_safe_paraphrase(paraphrase)
            evidence_views.append({
                "state": state,
                "state_label": TRACE_EVIDENCE_LABELS[locale][state],
                "paraphrase": paraphrase,
            })
        coverage = next(
            (
                row for row in BASE._rows(dossier.get("section_coverage"))
                if row.get("section") == target
            ),
            None,
        )
        if coverage is None:
            raise DossierValidationError(["decision trace inspection state is unavailable"])
        selected_pending = VALIDATOR.select_pending_inspection_section(plain_dossier)
        availability = coverage.get("availability")
        inspection_state = str(availability) if availability in {
            "inspected_present", "inspected_absent", "candidate_supplied"
        } else "unavailable"
        authorization_anchor: str | None = None
        if inspection_state == "unavailable":
            reason = coverage.get("reason")
            inspection_request = coverage.get("inspection_request")
            decision = inspection_request.get("decision") if isinstance(inspection_request, Mapping) else None
            if reason == "authorization_required" and decision == "pending_response":
                if target == selected_pending:
                    inspection_state = "pending"
                    authorization_anchor = "decide-now-authorization-title"
                else:
                    inspection_state = "pending_other"
            elif reason == "inspection_declined" and decision == "declined_for_session":
                inspection_state = "declined"
            elif reason == "authorized_inspection_failed" and decision == "authorized_inspection_failed":
                inspection_state = "failed"
        template = priority.get("client_template")
        if not isinstance(template, Mapping):
            raise DossierValidationError(["decision trace template is unavailable"])
        template_keys = template.get("field_keys")
        if not isinstance(template_keys, (list, tuple)):
            raise DossierValidationError(["decision trace template fields are unavailable"])
        template_fields = tuple(
            {"key": key, "label": TEMPLATE_FIELD_LABELS[locale][key]}
            for key in template_keys
            if isinstance(key, str) and key in TEMPLATE_FIELD_LABELS[locale]
        )
        if len(template_fields) != len(template_keys):
            raise DossierValidationError(["decision trace template fields are unavailable"])
        result: dict[str, object] = {
            "locale": locale,
            "target_section": target,
            "target_section_label": SECTION_LABELS[locale][target],
            "evidence_views": tuple(evidence_views),
            "template_fields": template_fields,
            "inspection_state": {
                "state": inspection_state,
                "label": TRACE_INSPECTION_LABELS[locale][inspection_state],
                "target_label": SECTION_LABELS[locale][target],
            },
            "steps": tuple({"key": key, "label": label} for key, label in zip(
                ("priority", "evidence", "template", "inspection"), TRACE_STEP_LABELS[locale], strict=True
            )),
        }
        if authorization_anchor is not None:
            result["authorization_anchor"] = authorization_anchor
        return BASE._mapping(BASE._freeze(result))
    except DossierValidationError:
        raise
    except (AttributeError, KeyError, RecursionError, TypeError, ValueError):
        raise DossierValidationError(["decision trace is unavailable"]) from None


def _validate_and_freeze(dossier: Mapping[str, object]) -> Mapping[str, object]:
    errors = VALIDATOR.validate_dossier(dossier)
    if errors:
        raise DossierValidationError(errors)
    return BASE._mapping(BASE._freeze(dossier))


def _plain(value: object) -> object:
    if isinstance(value, Mapping):
        return {key: _plain(nested) for key, nested in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(nested) for nested in value]
    return value


def _validated_market_group(
    dossier: Mapping[str, object],
    market_dossier: Mapping[str, object] | None,
    market_research: Mapping[str, object] | None,
    market_alignment: Mapping[str, object] | None,
) -> Mapping[str, object] | None:
    supplied = tuple(
        value is not None
        for value in (market_dossier, market_research, market_alignment)
    )
    if any(supplied) and not all(supplied):
        raise DossierValidationError(["market composition inputs must be supplied together"])
    if not any(supplied):
        return None
    try:
        market_copy, research_copy, alignment_copy = copy.deepcopy(
            (market_dossier, market_research, market_alignment)
        )
    except (RecursionError, TypeError, ValueError) as error:
        raise DossierValidationError(["market composition inputs have malformed structure"]) from error
    errors = MARKET_VALIDATOR.validate_market_dossier(
        market_copy, research_copy, _plain(dossier), alignment_copy
    )
    if errors:
        raise DossierValidationError(errors)
    frozen_market = BASE._freeze(market_copy)
    BASE._freeze(research_copy)
    BASE._freeze(alignment_copy)
    return BASE._mapping(frozen_market)


def _validated_learning_group(
    dossier: Mapping[str, object],
    market_dossier: Mapping[str, object] | None,
    market_research: Mapping[str, object] | None,
    learning_decision: Mapping[str, object] | None,
) -> Mapping[str, object] | None:
    """Return only a source-bound evaluated bundle and reject malformed supplied input."""
    if learning_decision is None:
        return None
    if not isinstance(learning_decision, Mapping):
        raise DossierValidationError(["learning decision must be an object"])
    if market_dossier is None or market_research is None:
        raise DossierValidationError(["learning decision requires the validated market composition group"])
    try:
        candidate = copy.deepcopy(learning_decision)
        errors = LEARNING_VALIDATOR.validate_learning_bundle(
            candidate,
            _plain(market_dossier),
            _plain(dossier),
            _plain(market_research),
        )
        if errors:
            raise DossierValidationError(errors)
        if not isinstance(candidate, Mapping):
            raise DossierValidationError(["learning decision must be an object"])
        if candidate.get("state") != "evaluated":
            return None
        decisions = candidate.get("decisions")
        vacancies = _plain(market_dossier).get("vacancies")
        if not isinstance(decisions, list) or not 3 <= len(decisions) <= 5:
            return None
        if not isinstance(vacancies, list) or not vacancies:
            return None
        frozen = BASE._freeze(candidate)
        return BASE._mapping(frozen)
    except DossierValidationError:
        raise
    except (AttributeError, KeyError, RecursionError, TypeError, ValueError):
        raise DossierValidationError(["learning decision is unavailable"]) from None


def _learning_signal_labels(
    market_dossier: Mapping[str, object], evidence_ids: object, locale: str
) -> str:
    if not isinstance(evidence_ids, (list, tuple)):
        return COPY[locale]["learning_evidence"]
    signals: list[str] = []
    for row in BASE._rows(market_dossier.get("matrix_rows")):
        row_evidence = row.get("evidence_ids")
        if isinstance(row_evidence, (list, tuple)) and any(item in evidence_ids for item in row_evidence):
            signal = _signal_label(row.get("signal", ""))
            if signal and signal not in signals:
                signals.append(signal)
    return ", ".join(signals) if signals else COPY[locale]["learning_evidence"]


def _render_learning_decision(
    market_dossier: Mapping[str, object],
    learning_decision: Mapping[str, object] | None,
    locale: str,
) -> str:
    if learning_decision is None:
        return ""
    labels = COPY[locale]
    decisions = BASE._rows(learning_decision.get("decisions"))
    vacancies = BASE._rows(market_dossier.get("vacancies"))
    cards: list[str] = []
    for row in decisions:
        rank = int(row["decision_rank"])
        heading_id = f"learning-decision-card-title-{rank}"
        option_type = labels["learning_option_types"].get(str(row["option_type"]), str(row["option_type"]))
        decision_label = labels["learning_decisions"].get(str(row["decision"]), str(row["decision"]))
        gap_label = labels["learning_gap_types"].get(str(row["gap_type"]), str(row["gap_type"]))
        provider_source = row.get("provider_source")
        source_markup = ""
        if isinstance(provider_source, Mapping):
            source_markup = (
                f'<p><span class="label">{labels["learning_source"]}</span>'
                f'{html.escape(str(provider_source.get("source_date", "")), quote=True)}; '
                f'{html.escape(str(provider_source.get("unknowns", "")), quote=True)}</p>'
            )
        cards.append(
            f'''<article class="card span-4 learning-decision-card" aria-labelledby="{heading_id}">
          <div class="learning-decision-header"><span class="learning-decision-rank" aria-hidden="true">{rank}</span><h3 id="{heading_id}">{html.escape(str(row['option_name']), quote=True)}</h3></div>
          <p class="learning-decision-role"><span class="label">{labels['learning_target_role']}</span>{html.escape(str(row['target_role']), quote=True)}</p>
          <p><span class="label">{labels['learning_gap']}</span>{html.escape(gap_label, quote=True)}</p>
          <p><span class="label">{labels['learning_option']}</span>{html.escape(option_type, quote=True)}</p>
          <p><span class="label">{labels['learning_owner']}</span>{html.escape(str(row['provider_or_owner']), quote=True)}</p>
          <p><span class="label">{labels['learning_evidence']}</span>{html.escape(_learning_signal_labels(market_dossier, row.get('source_gap_ids'), locale), quote=True)}</p>
          <div class="learning-decision-proof">
            <p><span class="label">{labels['learning_basis']}</span>{html.escape(str(row['decision_basis']), quote=True)}</p>
            <p><span class="label">{labels['learning_cost_time']}</span>{html.escape(str(row['cost_time_band']), quote=True)}</p>
            <p><span class="label">{labels['learning_signal_boundary']}</span>{html.escape(str(row['expected_signal_boundary']), quote=True)}</p>
            {source_markup}
          </div>
          <p><span class="label">{labels['learning_alternative']}</span>{html.escape(str(row['portfolio_or_no_learning_alternative']), quote=True)}</p>
          <p><span class="label">{labels['learning_risk']}</span>{html.escape(str(row['overbuying_risk']), quote=True)}</p>
          <p><span class="label">{labels['learning_decision']}</span>{html.escape(decision_label, quote=True)}</p>
          <p><span class="label">{labels['learning_gate']}</span>{html.escape(str(row['next_action_gate']), quote=True)}</p>
        </article>'''
        )
    sample_count = len(vacancies)
    return f'''<section class="section-block learning-decision" aria-labelledby="learning-decision-title">
      <h2 id="learning-decision-title">{labels['learning_title']}</h2>
      <p class="learning-decision-intro">{labels['learning_intro']}</p>
      <p class="learning-decision-sample"><strong>{labels['learning_sample']}:</strong> N={sample_count}</p>
      <div class="dossier-grid learning-decision-grid">{"".join(cards)}</div>
      <p class="learning-decision-boundary">{labels['learning_boundary']}</p>
    </section>'''


def _matrix_state(state: str, locale: str) -> str:
    symbol, spanish, english = MATRIX_STATE_COPY[state]
    label = spanish if locale == "es" else english
    return (
        f'<span class="matrix-state-symbol" aria-hidden="true">{symbol}</span>'
        f'<span class="matrix-state-text">{label}</span>'
    )


def _signal_label(value: object) -> str:
    return html.escape(str(value).replace("_", " ").title(), quote=True)

def _render_section_coverage(dossier: Mapping[str, object], locale: str) -> str:
    labels = COPY[locale]
    rows: list[str] = []
    for index, row in enumerate(BASE._rows(dossier["section_coverage"]), start=1):
        section = str(row["section"])
        heading_id = f"section-coverage-title-{index}"
        request = row.get("inspection_request")
        request_fact = ""
        if isinstance(request, Mapping):
            request_fact = (
                f'<dt>{labels["request"]}</dt><dd class="section-coverage-request">'
                f'{REQUEST_DECISION_LABELS[locale][str(request["decision"])]}</dd>'
            )
        rows.append(
            f'<li class="section-coverage-row"><article aria-labelledby="{heading_id}">\n'
            f'  <h3 id="{heading_id}">{SECTION_LABELS[locale][section]}</h3>\n'
            f'  <dl class="section-coverage-facts">'
            f'<dt>{labels["availability"]}</dt><dd>{AVAILABILITY_LABELS[locale][str(row["availability"])]}</dd>'
            f'<dt>{labels["reason"]}</dt><dd>{REASON_LABELS[locale][str(row["reason"])]}</dd>'
            f'{request_fact}</dl>\n'
            f'</article></li>'
        )
    return f'''<section class="section-block section-coverage-ledger" aria-labelledby="section-coverage-ledger-title">
      <h2 id="section-coverage-ledger-title">{labels['coverage_title']}</h2>
      <ol class="section-coverage-list">{''.join(rows)}</ol>
    </section>'''


def _render_decide_now(
    dossier: Mapping[str, object],
    locale: str,
    market_dossier: Mapping[str, object],
    learning_decision: Mapping[str, object] | None = None,
) -> str:
    labels = COPY[locale]
    coverage_rows = BASE._rows(dossier["section_coverage"])
    reviewed = sum(
        1 for row in coverage_rows if row.get("availability") in {"inspected_present", "inspected_absent"}
    )
    provided = sum(1 for row in coverage_rows if row.get("availability") == "candidate_supplied")
    unavailable = sum(1 for row in coverage_rows if row.get("availability") == "unavailable")
    priorities = BASE._rows(dossier["priorities"])
    priority_ids = [f"coach-priority-title-{priority['rank']}" for priority in priorities]
    market_title_id = "market-context-title"
    described_by = "decide-now-summary"
    pending = VALIDATOR.select_pending_inspection_section(BASE._mapping(_plain(dossier)))
    pending_index = next(
        (
            index
            for index, row in enumerate(coverage_rows, start=1)
            if row.get("section") == pending
        ),
        None,
    )
    priority_items = "".join(
        f'<li><a href="#{priority_ids[index]}"><span class="decide-now-rank">{priority["rank"]}</span> '
        f'{html.escape(str(priority["title"]), quote=True)} '
        f'<span class="decide-now-target">({SECTION_LABELS[locale][str(priority["target_section"])]})</span></a></li>'
        for index, priority in enumerate(priorities)
    )
    authorization = (
        AUTHORIZATION_QUESTIONS[locale][pending]
        if pending is not None
        else labels["decide_no_pending"]
    )
    market_state = str(market_dossier["state"])
    vacancies = BASE._rows(market_dossier.get("vacancies"))
    sample_count = len(vacancies)
    if market_state == "market_evidence_unavailable" or sample_count == 0:
        market_content = (
            f'<p id="decide-now-market-summary"><strong>{labels["decide_sample"]}:</strong> N=0</p>'
            f'<p>{labels["decide_no_market"]}</p>'
        )
    else:
        fractions = "".join(
            f'<li><span class="decide-now-signal">{_signal_label(row["signal"])}</span> '
            f'<span class="decide-now-fraction">{html.escape(str(row["display_fraction"]), quote=True)}</span></li>'
            for row in BASE._rows(market_dossier.get("recurrence_rows"))
        )
        market_content = (
            f'<p id="decide-now-market-summary"><strong>{labels["decide_sample"]}:</strong> '
            f'N={sample_count}</p>'
            f'<h4>{labels["decide_recurrence"]}</h4>'
            f'<ul class="decide-now-recurrence">{fractions}</ul>'
        )
    navigation_items = "".join(
        f'<li><a href="#{priority_ids[index]}">{html.escape(str(priority["title"]), quote=True)}</a></li>'
        for index, priority in enumerate(priorities)
    )
    if pending_index is not None:
        navigation_items += (
            f'<li><a href="#section-coverage-title-{pending_index}">'
            f'{SECTION_LABELS[locale][str(pending)]}</a></li>'
        )
    navigation_items += f'<li><a href="#{market_title_id}">{labels["decide_market"]}</a></li>'
    if learning_decision is not None:
        navigation_items += f'<li><a href="#learning-decision-title">{labels["learning_title"]}</a></li>'
    return f'''<section class="section-block decide-now" aria-labelledby="decide-now-title" aria-describedby="{described_by}">
      <h2 id="decide-now-title">{labels['decide_title']}</h2>
      <p id="decide-now-summary" class="decide-now-summary">{labels['decide_priorities']} · {labels['decide_coverage']} · {labels['decide_market']}</p>
      <nav class="decide-now-navigation" aria-label="{labels['decide_navigation']}"><ul>{navigation_items}</ul></nav>
      <div class="dossier-grid decide-now-grid">
        <article class="card span-4 decide-now-card" aria-labelledby="decide-now-priorities-title">
          <h3 id="decide-now-priorities-title">{labels['decide_priorities']}</h3>
          <ol class="decide-now-list">{priority_items}</ol>
        </article>
        <article class="card span-4 decide-now-card" aria-labelledby="decide-now-coverage-title">
          <h3 id="decide-now-coverage-title">{labels['decide_coverage']}</h3>
          <dl class="decide-now-facts">
            <dt>{labels['decide_reviewed']}</dt><dd>{reviewed}</dd>
            <dt>{labels['decide_provided']}</dt><dd>{provided}</dd>
            <dt>{labels['decide_unavailable']}</dt><dd>{unavailable}</dd>
          </dl>
        </article>
        <article class="card span-4 decide-now-card decide-now-authorization" aria-labelledby="decide-now-authorization-title">
          <h3 id="decide-now-authorization-title">{labels['decide_authorization']}</h3>
          <p>{html.escape(authorization, quote=True)}</p>
        </article>
        <article class="card span-12 decide-now-card decide-now-market" aria-labelledby="decide-now-market-title">
          <h3 id="decide-now-market-title">{labels['decide_market']}</h3>
          {market_content}
        </article>
      </div>
    </section>'''


def _render_decision_trace(
    priority: Mapping[str, object],
    dossier: Mapping[str, object],
    market_dossier: Mapping[str, object],
    locale: str,
    fields: str,
    template_heading_id: str,
    template_boundary_id: str,
) -> str:
    trace = _derive_decision_trace(priority, dossier, market_dossier, locale)
    rank = str(priority["rank"])
    steps = trace["steps"]
    evidence_views = trace["evidence_views"]
    evidence_items = "".join(
        f'<li id="decision-trace-evidence-{rank}-{ordinal}" class="decision-trace-evidence-item">'
        f'<span class="decision-trace-evidence-state">{html.escape(str(view["state_label"]), quote=True)}</span> '
        f'<span class="decision-trace-evidence-paraphrase">{html.escape(str(view["paraphrase"]), quote=True)}</span></li>'
        for ordinal, view in enumerate(evidence_views, start=1)
    )
    if not evidence_items:
        evidence_items = (
            f'<li id="decision-trace-evidence-{rank}-1" class="decision-trace-evidence-item">'
            f'{TRACE_INSPECTION_LABELS[locale]["unavailable"]}</li>'
        )
    inspection = trace["inspection_state"]
    authorization_link = ""
    if trace.get("authorization_anchor"):
        authorization_link = (
            f'<a href="#{html.escape(str(trace["authorization_anchor"]), quote=True)}">'
            f'{TRACE_INSPECTION_LINK_LABELS[locale]}</a>'
        )
    return f'''<section class="decision-trace" aria-labelledby="decision-trace-title-{rank}">
            <h4 id="decision-trace-title-{rank}" class="decision-trace-title">{html.escape(str(priority['title']), quote=True)}</h4>
            <ol class="decision-trace-steps">
              <li id="decision-trace-priority-{rank}" class="decision-trace-step">
                <span class="decision-trace-step-label">{html.escape(str(steps[0]['label']), quote=True)}</span>
                <p><span class="label">{COPY[locale]['target']}</span>{html.escape(str(trace['target_section_label']), quote=True)}</p>
              </li>
              <li id="decision-trace-evidence-step-{rank}" class="decision-trace-step">
                <span class="decision-trace-step-label">{html.escape(str(steps[1]['label']), quote=True)}</span>
                <ul class="decision-trace-evidence-list">{evidence_items}</ul>
              </li>
              <li id="decision-trace-template-{rank}" class="decision-trace-step">
                <span class="decision-trace-step-label">{html.escape(str(steps[2]['label']), quote=True)}</span>
                <section class="coach-template" aria-labelledby="{template_heading_id}" aria-describedby="{template_boundary_id}">
                  <h5 id="{template_heading_id}">{COPY[locale]['template']}: {TEMPLATE_LABELS[locale][str(priority['client_template']['template_id'])]}</h5>
                  <ul class="coach-template-list">{fields}</ul>
                  <p id="{template_boundary_id}" class="coach-template-boundary">{COPY[locale]['template_boundary']}</p>
                </section>
              </li>
              <li id="decision-trace-inspection-{rank}" class="decision-trace-step">
                <span class="decision-trace-step-label">{html.escape(str(steps[3]['label']), quote=True)}</span>
                <p><span class="label">{html.escape(str(inspection['target_label']), quote=True)}</span>{html.escape(str(inspection['label']), quote=True)}</p>
                {authorization_link}
              </li>
            </ol>
            <p class="decision-trace-boundary">{TRACE_BOUNDARY[locale]}</p>
          </section>'''


def _render_coach_priorities(
    dossier: Mapping[str, object],
    locale: str,
    market_dossier: Mapping[str, object] | None = None,
) -> str:
    labels = COPY[locale]
    cards: list[str] = []
    for priority in BASE._rows(dossier["priorities"]):
        rank = priority["rank"]
        heading_id = f"coach-priority-title-{rank}"
        template_heading_id = f"coach-template-title-{rank}"
        template_boundary_id = f"coach-template-boundary-{rank}"
        template = BASE._mapping(priority["client_template"])
        fields = "".join(
            f'<li><span class="coach-template-field">{TEMPLATE_FIELD_LABELS[locale][str(key)]}</span>'
            f'<span class="coach-template-blank" role="img" aria-label="{labels["template_blank"]}"></span></li>'
            for key in template["field_keys"]
        )
        if market_dossier is None:
            cards.append(f'''<article class="card span-4 coach-priority-card" aria-labelledby="{heading_id}">
          <div class="priority-header"><h3 id="{heading_id}">{html.escape(str(priority['title']), quote=True)}</h3><span class="priority-rank">{rank}</span></div>
          <p><span class="label">{labels['target']}</span>{SECTION_LABELS[locale][str(priority['target_section'])]}</p>
          <p class="coach-observation"><span class="label">{labels['observation']}</span>{html.escape(str(priority['coach_observation']), quote=True)}</p>
          <p><span class="label">{labels['why']}</span>{html.escape(str(priority['why_it_matters']), quote=True)}</p>
          <p class="coach-prompt"><span class="label">{labels['prompt']}</span>{html.escape(str(priority['coach_prompt']), quote=True)}</p>
          <section class="coach-template" aria-labelledby="{template_heading_id}" aria-describedby="{template_boundary_id}">
            <h4 id="{template_heading_id}">{labels['template']}: {TEMPLATE_LABELS[locale][str(template['template_id'])]}</h4>
            <ul class="coach-template-list">{fields}</ul>
            <p id="{template_boundary_id}" class="coach-template-boundary">{labels['template_boundary']}</p>
          </section>
        </article>''')
            continue
        trace_markup = _render_decision_trace(
            priority,
            dossier,
            market_dossier,
            locale,
            fields,
            template_heading_id,
            template_boundary_id,
        )
        cards.append(f'''<article class="card span-4 coach-priority-card" aria-labelledby="{heading_id}">
          <div class="priority-header"><h3 id="{heading_id}">{html.escape(str(priority['title']), quote=True)}</h3><span class="priority-rank">{rank}</span></div>
          <p><span class="label">{labels['target']}</span>{SECTION_LABELS[locale][str(priority['target_section'])]}</p>
          <p class="coach-observation"><span class="label">{labels['observation']}</span>{html.escape(str(priority['coach_observation']), quote=True)}</p>
          <p><span class="label">{labels['why']}</span>{html.escape(str(priority['why_it_matters']), quote=True)}</p>
          <p class="coach-prompt"><span class="label">{labels['prompt']}</span>{html.escape(str(priority['coach_prompt']), quote=True)}</p>
          {trace_markup}
        </article>''')
    return f'''<section class="section-block coach-priorities" aria-labelledby="coach-priorities-title">
      <h2 id="coach-priorities-title">{labels['priorities']}</h2>
      <div class="dossier-grid priorities-grid">{''.join(cards)}</div>
    </section>'''


def _render_market_evidence_unavailable(locale: str) -> str:
    labels = COPY[locale]
    return f'''<div class="dossier-grid section-block">
      <section class="card market-unavailable-card span-12" aria-labelledby="market-unavailable-title">
        <h2 id="market-unavailable-title">{labels['market_title']}</h2>
        <p>{labels['market_body']}</p>
      </section>
    </div>'''


def _render_market_context(
    market_dossier: Mapping[str, object] | None,
    locale: str,
    learning_decision: Mapping[str, object] | None = None,
) -> str:
    labels = COPY[locale]
    if market_dossier is None:
        return f'''<div class="dossier-grid section-block">
      <section class="card market-unavailable-card span-12" aria-labelledby="market-unavailable-title">
        <h2 id="market-unavailable-title">{labels['market_title']}</h2>
        <p>{labels['market_body']}</p>
      </section>
    </div>'''

    summary = BASE._mapping(market_dossier["search_summary"])
    state = str(market_dossier["state"])
    if state == "market_evidence_unavailable":
        return f'''<section class="section-block market-summary" aria-labelledby="market-context-title">
      <div class="dossier-grid">
        <div class="card market-unavailable-card span-12">
          <h2 id="market-context-title">{labels['market_title']}</h2>
          <p><strong>{labels['market_limitation']}:</strong> {labels['market_unavailable_reason']}</p>
        </div>
      </div>
    </section>'''

    vacancies = BASE._rows(market_dossier["vacancies"])
    count = len(vacancies)
    summary_heading = (
        labels["market_complete"]
        if state == "complete"
        else labels["market_limited"].format(count=count)
    )
    limitation_markup = ""
    if state == "limited_market_evidence":
        limitation_markup = (
            f'<p class="market-limitation"><strong>{labels["market_limitation"]}:</strong> '
            f'{labels["market_limited_reason"]}</p>'
        )

    cards: list[str] = []
    vacancy_labels: list[tuple[str, str]] = []
    for index, vacancy in enumerate(vacancies, start=1):
        short = f"V{index}"
        employer = html.escape(str(vacancy["employer"]), quote=True)
        title = html.escape(str(vacancy["title"]), quote=True)
        full_label = f"{employer} · {title}"
        vacancy_labels.append((short, full_label))
        employer_id = f"vacancy-alignment-employer-{index}"
        heading_id = f"vacancy-alignment-title-{index}"
        score_id = f"vacancy-alignment-score-{index}"
        score = int(vacancy["alignment_percent"])
        score_text = f"{score} de 100" if locale == "es" else f"{score} out of 100"
        cards.append(f'''<article class="vacancy-alignment-card" aria-labelledby="{employer_id} {heading_id}">
          <p class="vacancy-key-label">{short}</p>
          <p id="{employer_id}" class="vacancy-employer">{employer}</p>
          <h3 id="{heading_id}">{title}</h3>
          <p id="{score_id}" class="vacancy-alignment-score">{score_text}</p>
          <progress class="vacancy-alignment-progress" value="{score}" max="100" aria-labelledby="{employer_id} {heading_id} {score_id}"></progress>
          <p class="vacancy-score-boundary">{labels['score_boundary']}</p>
        </article>''')

    key_items = "".join(
        f'<li class="market-vacancy-key-item"><strong>{short}</strong> — {full}</li>'
        for short, full in vacancy_labels
    )
    vacancy_headers = "".join(
        f'<th id="market-matrix-col-v{index}" scope="col"><span aria-hidden="true">{short}</span>'
        f'<span class="visually-hidden">{full}</span></th>'
        for index, (short, full) in enumerate(vacancy_labels, start=1)
    )

    matrix_rows: list[str] = []
    for row_index, row in enumerate(BASE._rows(market_dossier["matrix_rows"]), start=1):
        row_header_id = f"market-matrix-row-{row_index}"
        support_state = str(row["support_state"])
        profile_copy = _matrix_state(support_state, locale)
        cells = [
            f'<td class="market-matrix-state-cell market-profile-state" data-label="{labels["matrix_profile"]}" '
            f'headers="market-matrix-col-profile {row_header_id}">{profile_copy}</td>'
        ]
        for vacancy_index, cell in enumerate(BASE._rows(row["cells"]), start=1):
            state_copy = support_state if cell["required"] else "not_required"
            short, full = vacancy_labels[vacancy_index - 1]
            data_label = html.escape(f"{short} · {html.unescape(full)}", quote=True)
            cells.append(
                f'<td class="market-matrix-state-cell" data-label="{data_label}" '
                f'headers="market-matrix-col-v{vacancy_index} {row_header_id}">'
                f'{_matrix_state(state_copy, locale)}</td>'
            )
        matrix_rows.append(
            f'<tr class="market-matrix-row"><th id="{row_header_id}" scope="row">'
            f'{_signal_label(row["signal"])}</th>{"".join(cells)}</tr>'
        )

    recurrence_items: list[str] = []
    for index, row in enumerate(BASE._rows(market_dossier["recurrence_rows"]), start=1):
        heading_id = f"recurrence-signal-{index}"
        fraction_id = f"recurrence-fraction-{index}"
        recurrence_items.append(f'''<div class="recurrence-row" aria-labelledby="{heading_id}">
          <strong id="{heading_id}" class="recurrence-signal">{_signal_label(row['signal'])}</strong>
          <progress class="recurrence-progress" value="{row['occurrences']}" max="{row['sample_size']}" aria-labelledby="{heading_id} {fraction_id}"></progress>
          <span id="{fraction_id}" class="recurrence-fraction">{html.escape(str(row['display_fraction']), quote=True)}</span>
        </div>''')
    gap_steps = "".join(f"<li>{step}</li>" for step in labels["gap_steps"])
    learning_markup = _render_learning_decision(market_dossier, learning_decision, locale)

    return f'''<section class="section-block market-summary" aria-labelledby="market-context-title">
        <div class="market-summary-card">
          <h2 id="market-context-title">{labels['market_context']}</h2>
          <p class="market-summary-heading">{summary_heading}</p>
          <p>{labels['market_boundary']}</p>
          {limitation_markup}
        </div>
        <section class="market-vacancy-section" aria-labelledby="vacancy-alignment-title">
          <h2 id="vacancy-alignment-title">{labels['vacancy_alignment']}</h2>
          <div class="vacancy-alignment-grid">{"".join(cards)}</div>
        </section>
        <section class="market-matrix-section" aria-labelledby="market-matrix-title">
          <h2 id="market-matrix-title">{labels['matrix_title']}</h2>
          <div class="market-matrix-group">
            <h3 id="market-vacancy-key-title">{labels['vacancy_key']}</h3>
            <ol class="market-vacancy-key" aria-labelledby="market-vacancy-key-title">{key_items}</ol>
            <table class="market-matrix">
              <caption>{labels['matrix_caption']}</caption>
              <thead><tr><th id="market-matrix-col-signal" scope="col">{labels['matrix_signal']}</th><th id="market-matrix-col-profile" scope="col">{labels['matrix_profile']}</th>{vacancy_headers}</tr></thead>
              <tbody>{"".join(matrix_rows)}</tbody>
            </table>
          </div>
        </section>
        <section class="market-recurrence" aria-labelledby="market-recurrence-title">
          <h2 id="market-recurrence-title">{labels['recurrence_title']}</h2>
          <p>{labels['recurrence_boundary']}</p>
          <div class="recurrence-list">{"".join(recurrence_items)}</div>
        </section>
        {learning_markup}
        <section class="gap-closure-route" aria-labelledby="gap-closure-route-title">
          <h2 id="gap-closure-route-title">{labels['gap_route']}</h2>
          <ol>{gap_steps}</ol>
        </section>
      </section>'''

def _render_market_surface(
    dossier: Mapping[str, object],
    locale: str,
    market_dossier: Mapping[str, object] | None,
    learning_decision: Mapping[str, object] | None = None,
) -> str:
    if market_dossier is not None:
        return _render_market_context(market_dossier, locale, learning_decision)
    if BASE._mapping(dossier["market_context"])["state"] == "not_researched":
        return _render_market_evidence_unavailable(locale)
    labels = COPY[locale]
    return f'''<div class="dossier-grid section-block">
      <section class="card market-evidence-available-card span-12" aria-labelledby="market-evidence-available-title">
        <h2 id="market-evidence-available-title">{labels['market_available_title']}</h2>
        <p>{labels['market_available_body']}</p>
      </section>
    </div>'''


def _render_main(
    dossier: Mapping[str, object],
    locale: str,
    market_dossier: Mapping[str, object] | None,
    learning_decision: Mapping[str, object] | None = None,
) -> str:
    projected = COMPAT.project_v2_to_v1(BASE._mapping(_plain(dossier)))
    opening = BASE._render_verdict(projected, locale) + BASE._render_recruiter_scan(projected, locale)
    bridge_holds = BASE._render_holds(projected, locale) + BASE._render_screen_bridge(projected, locale)
    decide_now = _render_decide_now(dossier, locale, market_dossier, learning_decision) if market_dossier is not None else ""
    return f'''<main id="main-content" class="shell" tabindex="-1">
      <div class="dossier-grid">{opening}</div>
      {decide_now}{_render_section_coverage(dossier, locale)}
      {_render_coach_priorities(dossier, locale, market_dossier)}
      <div class="dossier-grid section-block">{BASE._render_analytics(projected, locale)}</div>
      {BASE._render_dimensions(projected, locale)}
      {BASE._render_visual_review(projected, locale)}
      {_render_market_surface(dossier, locale, market_dossier, learning_decision)}
      {BASE._render_copy_blocks(projected, locale)}
      <div class="dossier-grid section-block">{bridge_holds}</div>
      {BASE._render_questions(projected, locale)}
      <div class="dossier-grid section-block">{BASE._render_plan(projected, locale)}{BASE._render_details(projected, locale)}</div>
    </main>
    <footer class="shell footer"><strong>{BASE.COPY[locale]['action_boundary']}</strong> <span class="employment-boundary">{BASE.COPY[locale]['employment_boundary']}</span></footer>'''


def build_chat_summary(dossier: Mapping[str, object]) -> str:
    frozen = _validate_and_freeze(dossier)
    locale = str(frozen["locale"])
    projected = COMPAT.project_v2_to_v1(BASE._mapping(_plain(frozen)))
    verdict = BASE._mapping(projected["verdict"])
    first_priority = BASE._rows(projected["priorities"])[0]
    parts = [
        BASE._summary_text(verdict["statement"], 60),
        f"{BASE.COPY[locale]['first_action']}: {BASE._summary_text(first_priority['action'], 55)}",
    ]
    pending = VALIDATOR.select_pending_inspection_section(BASE._mapping(_plain(frozen)))
    if pending is not None:
        parts.append(AUTHORIZATION_QUESTIONS[locale][pending])
    else:
        questions = BASE._rows(projected["questions"])
        if questions:
            parts.append(
                f"{BASE.COPY[locale]['first_question']}: "
                f"{BASE._summary_text(questions[0]['question'], 45)}"
            )
    parts.append(BASE.COPY[locale]["action_boundary"])
    summary = "\n\n".join(parts)
    if len(summary.split()) > 180:
        raise RuntimeError("chat summary budget is invalid")
    return summary


def render_dossier_html(
    dossier: Mapping[str, object],
    market_dossier: Mapping[str, object] | None = None,
    *,
    market_research: Mapping[str, object] | None = None,
    market_alignment: Mapping[str, object] | None = None,
    learning_decision: Mapping[str, object] | None = None,
) -> str:
    frozen = _validate_and_freeze(dossier)
    frozen_market = _validated_market_group(
        frozen, market_dossier, market_research, market_alignment
    )
    frozen_learning = _validated_learning_group(
        frozen, frozen_market, market_research, learning_decision
    )
    locale = str(frozen["locale"])
    template = BASE.ASSET_LOADER.read_private_asset(ASSET_ROOT.parent, TEMPLATE_PATH)
    base_css = BASE.ASSET_LOADER.read_private_asset(ASSET_ROOT.parent, BASE_CSS_PATH)
    extension_css = BASE.ASSET_LOADER.read_private_asset(ASSET_ROOT.parent, CSS_PATH)
    market_css = (
        BASE.ASSET_LOADER.read_private_asset(ASSET_ROOT.parent, MARKET_CSS_PATH)
        if frozen_market is not None
        else ""
    )
    static_tokens = BASE.STATIC_TEMPLATE_TOKEN.findall(template)
    if sorted(static_tokens) != sorted(BASE.TEMPLATE_TOKENS):
        raise RuntimeError("dossier template token contract is invalid")
    substitutions = {
        "{{LANG}}": locale,
        "{{TITLE}}": BASE.COPY[locale]["title"],
        "{{INLINE_CSS}}": base_css + extension_css + market_css,
        "{{HEADER}}": BASE._render_header(locale),
        "{{MAIN}}": _render_main(frozen, locale, frozen_market, frozen_learning),
        "{{INLINE_SCRIPT}}": BASE.INLINE_SCRIPT,
    }
    return BASE.STATIC_TEMPLATE_TOKEN.sub(lambda match: substitutions[match.group(0)], template)


def write_dossier_html(
    dossier_path: Path,
    output_path: Path,
    *,
    market_dossier_path: Path | None = None,
    market_research_path: Path | None = None,
    market_alignment_path: Path | None = None,
    learning_decision_path: Path | None = None,
    force: bool = False,
) -> RenderReceipt:
    dossier = VALIDATOR.load_dossier(Path(dossier_path))
    errors = VALIDATOR.validate_dossier(dossier)
    if errors:
        raise DossierValidationError(errors)
    market_paths = (market_dossier_path, market_research_path, market_alignment_path)
    if any(path is not None for path in market_paths) and not all(
        path is not None for path in market_paths
    ):
        raise DossierValidationError(["market composition inputs must be supplied together"])
    market_dossier = None
    market_research = None
    market_alignment = None
    learning_decision = None
    if learning_decision_path is not None and not all(path is not None for path in market_paths):
        raise DossierValidationError(["learning decision requires the validated market composition group"])
    if all(path is not None for path in market_paths):
        try:
            market_dossier = VALIDATOR.load_dossier(Path(market_dossier_path))
            market_research = RESEARCH_VALIDATOR.load_research(Path(market_research_path))
            market_alignment = VALIDATOR.load_dossier(Path(market_alignment_path))
        except (VALIDATOR.DossierLoadError, RESEARCH_VALIDATOR.ResearchLoadError) as error:
            raise MarketInputLoadError("cannot load market composition input") from error
        if learning_decision_path is not None:
            try:
                learning_decision = LEARNING_VALIDATOR.load_learning_bundle(Path(learning_decision_path))
            except LEARNING_VALIDATOR.LearningBundleLoadError as error:
                raise MarketInputLoadError("cannot load learning decision input") from error
            learning_errors = LEARNING_VALIDATOR.validate_learning_bundle(
                learning_decision, market_dossier, dossier, market_research
            )
            if learning_errors:
                raise DossierValidationError(learning_errors)
    try:
        expanded_output = Path(output_path).expanduser()
    except RuntimeError as error:
        raise OSError("output path is unavailable") from error
    output = Path(os.path.abspath(os.fspath(expanded_output)))
    rendered = render_dossier_html(
        dossier,
        market_dossier,
        market_research=market_research,
        market_alignment=market_alignment,
        learning_decision=learning_decision,
    )
    summary = build_chat_summary(dossier)
    BASE._atomic_private_write(output, rendered.encode("utf-8"), force=force)
    return RenderReceipt(output, "text/html", str(dossier["locale"]), summary)


def _cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render a private career dossier v2.")
    parser.add_argument("dossier", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--market-dossier", type=Path)
    parser.add_argument("--market-research", type=Path)
    parser.add_argument("--market-alignment", type=Path)
    parser.add_argument("--learning-decision", type=Path)
    parser.add_argument("--force", action="store_true")
    arguments = parser.parse_args(argv)
    try:
        receipt = write_dossier_html(
            arguments.dossier,
            arguments.output,
            market_dossier_path=arguments.market_dossier,
            market_research_path=arguments.market_research,
            market_alignment_path=arguments.market_alignment,
            learning_decision_path=arguments.learning_decision,
            force=arguments.force,
        )
    except OSError:
        print("cannot write dossier artifact", file=sys.stderr)
        return 3
    except (VALIDATOR.DossierLoadError, MarketInputLoadError, DossierValidationError) as error:
        if isinstance(error, DossierValidationError):
            print("\n".join(error.errors), file=sys.stderr)
        else:
            print(str(error), file=sys.stderr)
        return 2
    print(json.dumps({
        "artifact_path": str(receipt.artifact_path),
        "artifact_type": receipt.artifact_type,
        "locale": receipt.locale,
        "chat_summary": receipt.chat_summary,
    }, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
