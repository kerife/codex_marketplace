#!/usr/bin/env python3
"""Validate a source-bound private first-interview conversion board."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any


def _sibling(name: str) -> Any:
    path = Path(__file__).with_name(name)
    origin = os.path.realpath(os.fspath(path))
    if name == "private_first_interview_conversion_board_identity.py":
        existing = sys.modules.get("private_first_interview_conversion_board_identity")
        if existing is not None:
            return existing
        module_name = "private_first_interview_conversion_board_identity"
    else:
        module_name = "_pgc_private_first_interview_" + hashlib.sha256(origin.encode()).hexdigest()
    existing = sys.modules.get(module_name)
    if existing is not None:
        return existing
    specification = importlib.util.spec_from_file_location(module_name, path)
    if specification is None or specification.loader is None:
        raise RuntimeError("private first-interview dependency is unavailable")
    module = importlib.util.module_from_spec(specification)
    sys.modules[module_name] = module
    specification.loader.exec_module(module)
    return module


_snapshot = _sibling("semantic_provenance_snapshot.py")
_schema_validation = _sibling("validate_json_schema_subset.py")
_identity = _sibling("private_first_interview_conversion_board_identity.py")
_prose = _sibling("private_prose_safety.py")
_SCHEMA_PATH = Path(__file__).parents[1] / "schemas" / "private-first-interview-conversion-board-v1.schema.json"
_MISMATCH = "private first-interview conversion board does not match validated sources"
_MAX_INPUT_BYTES = 512 * 1024
ValidatedPrivateFirstInterviewConversionBoard = _identity.ValidatedPrivateFirstInterviewConversionBoard

_STATES = ("ready", "clarify", "pause", "stop")
_BRANCHES = ("advance", "clarify", "pause", "stop")
_RISK_TOPICS = ("production", "compensation", "eligibility", "availability", "confidentiality")


def _schema() -> dict[str, object]:
    value = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(_MISMATCH)
    return value


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _strings(value: object):
    if isinstance(value, Mapping):
        for key, item in value.items():
            yield from _strings(key)
            yield from _strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _strings(item)
    elif isinstance(value, str):
        yield value


def _unsafe_source_text(value: object) -> bool:
    forbidden = (
        "http://", "https://", "<script", "<style", "send this", "envía esto",
        "calendar event", "evento de calendario", "fit score", "probability",
        "probabilidad", "guarantee", "garantía", "salary", "sueldo", "api_key",
        "password", "credential", "secret", "token",
    )
    metadata_fields = {"group_id", "source_snapshot", "record_id", "check_id", "day", "branch", "topic", "state"}
    def prose_values(node: object):
        if isinstance(node, Mapping):
            for key, item in node.items():
                if key in metadata_fields:
                    continue
                yield from prose_values(item)
        elif isinstance(node, list):
            for item in node:
                yield from prose_values(item)
        elif isinstance(node, str):
            yield node
    for text in prose_values(value):
        if not _prose.is_safe_prose_text(text):
            return True
        if _prose.contains_obfuscated_candidate_identity(text) or _prose.contains_candidate_identity(text):
            return True
        lowered = text.casefold()
        if any(term in lowered for term in forbidden):
            return True
    return False


def _source_group_shape(source: object) -> bool:
    if not isinstance(source, Mapping):
        return False
    required = {
        "group_id", "source_snapshot", "recruiter_outreach_lab", "quality_gate",
        "first_interview_7_day_plan", "weekly_coach_plan", "decision_ladder",
        "plan_days", "daily_review_logs",
    }
    if set(source) != required:
        return False
    if len(source["decision_ladder"]) != 4 or len(source["plan_days"]) != 7 or len(source["daily_review_logs"]) != 7:
        return False
    if [row.get("branch") for row in source["decision_ladder"]] != list(_BRANCHES):
        return False
    if [row.get("day") for row in source["plan_days"]] != list(range(1, 8)):
        return False
    if [row.get("day") for row in source["daily_review_logs"]] != list(range(1, 8)):
        return False
    gate = source["quality_gate"]
    if not isinstance(gate, Mapping) or len(gate.get("checks", [])) != 3:
        return False
    if {row.get("topic") for row in gate["checks"]} != {"specificity", "evidence", "boundary"}:
        return False
    snapshot = source.get("source_snapshot")
    if not isinstance(snapshot, str):
        return False
    without_snapshot = dict(source)
    without_snapshot.pop("source_snapshot", None)
    expected_snapshot = "snap-private-first-interview-v1-sha256-" + hashlib.sha256(
        _canonical_json(without_snapshot).encode("utf-8")
    ).hexdigest()
    if snapshot != expected_snapshot:
        return False
    return True


def _state(source: Mapping[str, object]) -> str:
    states = [
        source.get("recruiter_outreach_lab", {}).get("state"),
        source.get("quality_gate", {}).get("state"),
        source.get("first_interview_7_day_plan", {}).get("state"),
        source.get("weekly_coach_plan", {}).get("state"),
    ]
    for value in _STATES[::-1]:
        if value in states:
            return value
    return "clarify"


def _localized(locale: str) -> dict[str, object]:
    if locale == "es":
        return {
            "decision": {"objective": "Preparar una entrevista", "current_state": "Preparación privada lista", "next_safe_action": "Revisar y ensayar", "signal": "Contexto y hechos presentes", "boundary": "No envía, agenda, aplica ni garantiza resultados"},
            "sequence": [("Estado actual", "Identificar lo conocido"), ("Preparación privada", "Preparar evidencia"), ("Revisión humana", "Revisar señales"), ("Límite de autorización", "Mantener acciones externas desactivadas")],
            "proof": [("Responsabilidad operativa", "Un hecho apoyado puede explicarse", "Revisar el alcance")],
            "risk": [("¿Está claro el alcance?", "Describir solo hechos", "Confirmar alcance", "No afirmar responsabilidad no apoyada"), ("¿Se conoce compensación?", "Mantener valores desconocidos", "Confirmar antes de decidir", "No inferir compensación"), ("¿Está confirmada elegibilidad?", "Tratar lo desconocido como tal", "Revisión humana", "No afirmar elegibilidad"), ("¿Está confirmada disponibilidad?", "Indicar solo ventana revisada", "Confirmar horario", "No prometer disponibilidad"), ("¿Expone material privado?", "Usar evidencia abstracta", "Revisar límite", "No divulgar texto fuente")],
            "rehearsal": ("¿Cómo explicarías una decisión apoyada?", "Revisar claridad", "Contexto, acción, resultado, límite", "Esperar revisión humana", "unknown"),
            "week": [("Revisar contexto", "Solo hechos acotados", "Nombrar un pendiente", "Contexto claro", "Aclarar contexto", "Detener ante fuente no apoyada"), ("Elegir evidencia", "No ampliar el hecho", "Revisar alcance", "Límite claro", "Sin evidencia", "Detener sin apoyo"), ("Ensayar respuesta", "Respuesta ligada a fuente", "Revisar estructura", "Respuesta estable", "Acortar respuesta", "Detener ante invención"), ("Revisar límites", "Mantener pendientes", "Listar confirmaciones", "Pendientes visibles", "Pausar", "Detener ante restricción crítica"), ("Redactar pregunta", "Sin texto privado", "Revisar utilidad", "Pregunta concreta", "Deferir pregunta", "Detener ante divulgación"), ("Revisar ramas", "Sin predicciones", "Elegir rama segura", "Rama basada en evidencia", "Pausar", "Detener sin apoyo"), ("Revisión final", "Acciones externas desactivadas", "Confirmar límite", "Límite explícito", "Mantener privado", "Detener antes de acción no autorizada")],
            "branches": [("Una señal acotada", "Continuar privado", "Contacto externo", "señal apoyada", "¿Qué cambió?", "Resumen factual"), ("Pendiente nombrado", "Registrar aclaración", "Suponer contexto", "pregunta abierta", "¿Qué confirmar?", "Pregunta acotada"), ("Sin cambio útil", "Esperar revisión", "Predecir", "señal débil", "¿Es más seguro esperar?", "Sin urgencia artificial"), ("Restricción registrada", "Cerrar revisión", "Proceder externamente", "condición de parada", "¿Qué límite falló?", "Sin acción externa")],
            "branch_triggers": ["Contexto confirmado", "Falta contexto", "Señal débil", "Falla límite"],
            "daily": [("strong", "advance", "Apoyo acotado", "Continuar privado", "claridad", "Sin resultado externo", "¿Qué falta?"), ("strong", "advance", "Punto apoyado", "Ensayar", "evidencia", "No valida resultado", "¿Qué la apoya?"), ("mixed", "clarify", "Estructura usable", "Revisar límite", "claridad", "No es entrevista", "¿Qué es seguro?"), ("unknown", "clarify", "Hay confirmaciones", "Visibilizar pendientes", "restricciones", "Desconocido no es fallo", "¿Qué confirmar?"), ("strong", "advance", "Pregunta acotada", "Revisar privado", "pregunta", "No crea mensaje", "¿Es útil?"), ("mixed", "pause", "No requiere movimiento", "Esperar", "decisión", "Sin probabilidad", "¿Qué evidencia hay?"), ("strong", "advance", "Límite intacto", "Mantener acciones desactivadas", "integridad", "No autoriza acción", "¿Límite intacto?")],
        }
    return {
        "decision": {"objective": "Prepare for a first interview", "current_state": "Private preparation is ready for review", "next_safe_action": "Review the bounded evidence and rehearse", "signal": "Role context and supported facts are present", "boundary": "This board does not message, schedule, apply, or guarantee an outcome"},
        "sequence": [("Current state", "Identify what is known and what remains unknown"), ("Private preparation", "Prepare bounded evidence and a rehearsal"), ("Human review", "Review the signal and the stop conditions"), ("Authorization gate", "Keep external action disabled until separately authorized")],
        "proof": [("Operational ownership", "A supported experience fact can be explained in context", "Review the exact scope before using it"), ("Incident reasoning", "A bounded example can show how a decision was made", "Do not add unsupported impact")],
        "risk": [("Is the operational scope clear?", "Describe only supported scope", "Confirm scope privately", "Do not claim unsupported ownership"), ("Is compensation context known?", "Leave unknown values open", "Confirm before any decision", "Do not infer compensation"), ("Is eligibility confirmed?", "Treat unknown eligibility as unknown", "Request human confirmation", "Do not claim eligibility"), ("Is availability confirmed?", "State only the reviewed window", "Confirm timing privately", "Do not promise availability"), ("Could this expose private material?", "Use abstracted evidence only", "Review the boundary", "Do not disclose private source text")],
        "rehearsal": ("How would you explain one supported operational decision?", "Check clarity without adding claims", "Context, action, observable result, boundary", "Pause for human review before any external use", "unknown"),
        "week": [("Review role context privately", "Use only bounded source facts", "Name one unknown", "Context is specific", "Clarify the missing context", "Stop if the source is unsupported"), ("Select one supported proof point", "Do not expand the fact", "Check its scope", "Evidence has a boundary", "Use no proof point", "Stop if support cannot be shown"), ("Rehearse one concise answer", "Keep the answer source-bound", "Check the structure", "Answer is stable", "Shorten the answer", "Stop if it requires invention"), ("Check critical constraints", "Keep unknowns explicit", "List confirmation needs", "Unknowns are visible", "Pause for clarification", "Stop on an unresolved critical constraint"), ("Draft a private question", "Question contains no private source text", "Check usefulness", "Question is specific", "Defer the question", "Stop if it would disclose confidential material"), ("Review the decision ladder", "Use no outcome prediction", "Select a safe branch", "Branch is evidence-led", "Pause", "Stop if the branch cannot be supported"), ("Run a final private review", "Keep all external actions disabled", "Confirm the boundary", "Boundary remains explicit", "Keep the board private", "Stop before any unauthorized action")],
        "branches": [("One bounded signal", "Continue private preparation", "External outreach", "supported signal", "What changed in the evidence?", "Use a factual summary only"), ("Named unknown", "Record the clarification need", "Assume the missing context", "open question", "What must be confirmed?", "Ask only a bounded question"), ("No useful change", "Wait for private review", "Escalate or predict", "weak signal", "Is waiting safer?", "Do not manufacture urgency"), ("Recorded constraint", "End the board review", "Proceed externally", "stop condition", "What boundary failed?", "Do not draft an external action")],
        "branch_triggers": ["Supported context is confirmed", "A material context is missing", "The signal is too weak", "A safety boundary fails"],
        "daily": [("strong", "advance", "Context has bounded support", "Continue privately", "context clarity", "No external outcome is measured", "What remains unknown?"), ("strong", "advance", "One supportable point is selected", "Rehearse privately", "evidence clarity", "Selection is not validation of outcome", "What supports this point?"), ("mixed", "clarify", "Structure is usable", "Review the boundary", "answer clarity", "Rehearsal is not an interview result", "What can be stated safely?"), ("unknown", "clarify", "Confirmation items remain", "Keep unknowns visible", "constraint clarity", "Unknowns are not failures", "Which item needs confirmation?"), ("strong", "advance", "Question is bounded", "Review privately", "question quality", "No message is created", "Does it seek useful context?"), ("mixed", "pause", "Evidence does not require movement", "Wait for review", "decision clarity", "No probability is inferred", "Which branch fits the evidence?"), ("strong", "advance", "Private boundary is intact", "Keep external action disabled", "boundary integrity", "Completion does not authorize action", "Is the private boundary intact?")],
    }


def _project_from_frozen(source_group: Mapping[str, object], *, locale: str = "en", as_of_date: str = "1970-01-01") -> dict[str, object]:
    if not _source_group_shape(source_group):
        raise ValueError(_MISMATCH)
    copy = _localized(locale)
    states = [source_group[name].get("state") for name in ("recruiter_outreach_lab", "quality_gate", "first_interview_7_day_plan", "weekly_coach_plan")]
    current_state = next((state for state in _STATES[::-1] if state in states), "clarify")
    artifact: dict[str, object] = {"schema_version": "private-first-interview-conversion-board-v1", "artifact_kind": "private_first_interview_conversion_board", "locale": locale, "as_of_date": as_of_date, "source_group": source_group}
    artifact["decision"] = [{"state": current_state, **copy["decision"]}]
    if current_state == "stop":
        artifact["approval_boundary"] = {"artifact_state": "private_draft", "allowed_next_step": "manual_private_review", "prohibited_actions": ["message", "connect", "apply", "schedule", "calendar_create", "publish", "share", "upload", "submit", "export", "external_edit", "purchase", "enroll"], "authorization_required": True}
        artifact["delivery"] = {"draft_only": True, "external_actions_authorized": False, "no_message_action": True, "no_calendar_action": True, "raw_event_retained": False, "raw_reply_retained": False, "raw_answer_retained": False, "local_save_mode": "disabled", "candidate_review_required": True}
        return artifact
    stages = ("current_state", "private_preparation", "human_review", "authorization_gate")
    artifact["sequence"] = [{"stage": stage, "label": copy["sequence"][i][0], "description": copy["sequence"][i][1]} for i, stage in enumerate(stages)]
    artifact["proof_cards"] = [{"vacancy_signal": a, "evidence_summary": b, "caveat": c} for a, b, c in copy["proof"]]
    artifact["risk_checks"] = [{"topic": topic, "trigger_question": row[0], "safe_response_boundary": row[1], "confirmation_needed": row[2], "forbidden_claim": row[3]} for topic, row in zip(_RISK_TOPICS, copy["risk"])]
    q, purpose, structure, wait, score = copy["rehearsal"]
    artifact["rehearsal"] = {"question": q, "purpose": purpose, "response_structure": structure, "wait_boundary": wait, "pre_response_score": score}
    artifact["week"] = [{"day": i + 1, "private_action": row["action"], "evidence_boundary": copy["week"][i][1], "review_checkpoint": copy["week"][i][2], "observable_signal": copy["week"][i][3], "fallback": copy["week"][i][4], "stop_rule": copy["week"][i][5]} for i, row in enumerate(source_group["plan_days"])]
    artifact["decision_ladder"] = [{"branch": row["branch"], "trigger": copy["branch_triggers"][i], "evidence_requirement": copy["branches"][i][0], "next_safe_action": copy["branches"][i][1], "blocked_action": copy["branches"][i][2], "measurement_label": copy["branches"][i][3], "review_question": copy["branches"][i][4], "script_boundary": copy["branches"][i][5]} for i, row in enumerate(source_group["decision_ladder"])]
    artifact["daily_reviews"] = [{"day": i + 1, "observed_signal": row["observed_signal"], "signal_quality": copy["daily"][i][0], "decision": copy["daily"][i][1], "evidence_log": copy["daily"][i][2], "next_safe_action": copy["daily"][i][3], "metric_label": copy["daily"][i][4], "confounder_note": copy["daily"][i][5], "coach_question": copy["daily"][i][6]} for i, row in enumerate(source_group["daily_review_logs"])]
    artifact["approval_boundary"] = {"artifact_state": "private_draft", "allowed_next_step": "manual_private_review", "prohibited_actions": ["message", "connect", "apply", "schedule", "calendar_create", "publish", "share", "upload", "submit", "export", "external_edit", "purchase", "enroll"], "authorization_required": True}
    artifact["delivery"] = {"draft_only": True, "external_actions_authorized": False, "no_message_action": True, "no_calendar_action": True, "raw_event_retained": False, "raw_reply_retained": False, "raw_answer_retained": False, "local_save_mode": "disabled", "candidate_review_required": True}
    return artifact


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(_MISMATCH)
        result[key] = value
    return result


def _validate_composite(value: Mapping[str, object]) -> ValidatedPrivateFirstInterviewConversionBoard:
    source = value.get("source_group")
    if not _source_group_shape(source) or _unsafe_source_text(source):
        raise ValueError(_MISMATCH)
    if _schema_validation.validate_schema_instance(value, _schema()):
        raise ValueError(_MISMATCH)
    expected = _project_from_frozen(source, locale=value.get("locale", "en"), as_of_date=value.get("as_of_date", "1970-01-01"))
    if _canonical_json(value) != _canonical_json(expected):
        raise ValueError(_MISMATCH)
    return _identity._issue_validated_private_first_interview_conversion_board(_canonical_json(value), _canonical_json(source))


def validate_private_first_interview_conversion_board_v1(source_group: object) -> ValidatedPrivateFirstInterviewConversionBoard:
    """Return a proof for one raw source group or an exact composite artifact."""
    try:
        frozen = _snapshot.bounded_plain_snapshot(source_group)
        if not isinstance(frozen, Mapping):
            raise ValueError(_MISMATCH)
        if "source_group" in frozen:
            return _validate_composite(frozen)
        if _unsafe_source_text(frozen):
            raise ValueError(_MISMATCH)
        artifact = _project_from_frozen(frozen)
        return _validate_composite(artifact)
    except Exception:
        raise ValueError(_MISMATCH) from None


def _revalidate_validated_private_first_interview_conversion_board(value: object) -> dict[str, object]:
    try:
        artifact_json, source_json = _identity._validation_payload_json(value)
        if len(artifact_json.encode()) > _MAX_INPUT_BYTES or len(source_json.encode()) > _MAX_INPUT_BYTES:
            raise ValueError(_MISMATCH)
        artifact = json.loads(artifact_json, object_pairs_hook=_unique_object)
        source = json.loads(source_json, object_pairs_hook=_unique_object)
        if not isinstance(artifact, Mapping) or not isinstance(source, Mapping):
            raise ValueError(_MISMATCH)
        proof = _validate_composite(artifact)
        if _canonical_json(proof.source_group) != _canonical_json(source):
            raise ValueError(_MISMATCH)
        return proof.artifact
    except Exception:
        raise ValueError(_MISMATCH) from None
