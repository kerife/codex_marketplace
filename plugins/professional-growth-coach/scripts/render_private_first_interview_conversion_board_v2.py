#!/usr/bin/env python3
"""Render a sanitized private first-interview board v2 offline."""

from __future__ import annotations

import html
import importlib.util
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any


ASSET_ROOT = Path(__file__).resolve().parents[1] / "assets"
TEMPLATE_PATH = ASSET_ROOT / "private-first-interview-conversion-board-v2.html"
CSS_PATH = ASSET_ROOT / "private-first-interview-conversion-board-v2.css"


def _load(name: str, module_name: str) -> Any:
    existing = sys.modules.get(module_name)
    if existing is not None:
        return existing
    path = Path(__file__).with_name(name)
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError("private board renderer dependency unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


ASSET_LOADER = _load("private_asset_loader.py", "private_first_interview_board_v2_asset_loader")
VALIDATOR = _load("validate_private_first_interview_conversion_board_v2.py", "validate_private_first_interview_conversion_board_v2")


class PrivateFirstInterviewConversionBoardV2RenderError(ValueError):
    """Raised when a board is not an exact validator-issued v2 proof."""


def _e(value: object) -> str:
    return html.escape(str(value) if value is not None else "", quote=True)


def _paragraph(label: str, value: object) -> str:
    return f"<dt>{_e(label)}</dt><dd>{_e(value)}</dd>"


def _list_rows(rows: object, render_row: Any) -> str:
    if not isinstance(rows, list):
        raise PrivateFirstInterviewConversionBoardV2RenderError("private board artifact is unavailable")
    return "".join(render_row(row, index) for index, row in enumerate(rows, 1))


def _render_artifact(artifact: Mapping[str, object]) -> str:
    locale = artifact.get("locale")
    decision_rows = artifact.get("decision")
    provenance = artifact.get("source_provenance")
    if locale not in ("en", "es") or not isinstance(decision_rows, list) or len(decision_rows) != 1 or not isinstance(provenance, Mapping):
        raise PrivateFirstInterviewConversionBoardV2RenderError("private board artifact is unavailable")
    decision = decision_rows[0]
    if not isinstance(decision, Mapping):
        raise PrivateFirstInterviewConversionBoardV2RenderError("private board artifact is unavailable")
    es = locale == "es"
    labels = {
        "title": "Tablero privado de primera entrevista" if es else "Private first-interview conversion board",
        "skip": "Ir al contenido principal" if es else "Skip to main content",
        "kicker": "Revisión privada · solo borrador" if es else "Private review · draft only",
        "heading": "Preparación para la primera entrevista" if es else "First-interview preparation",
        "state": "Estado" if es else "State", "objective": "Objetivo" if es else "Objective",
        "cockpit": "Centro de decisión" if es else "Decision cockpit",
        "decide_now": "Decide ahora" if es else "Decide now",
        "current": "Situación actual" if es else "Current situation", "next": "Siguiente acción segura" if es else "Next safe action",
        "signal": "Señal observada" if es else "Observed signal", "boundary": "Límite" if es else "Boundary",
        "sequence": "Secuencia de revisión" if es else "Review sequence", "proof": "Señales de prueba" if es else "Proof signals",
        "risks": "Comprobaciones de riesgo" if es else "Risk checks",
        "week": "Plan privado de siete días" if es else "Seven-day private plan", "ladder": "Escalera de decisión" if es else "Decision ladder",
        "reviews": "Plantillas de revisión diaria" if es else "Daily review templates", "private": "Límite privado" if es else "Private boundary",
        "footer": "No se realizó ninguna acción externa." if es else "No external action was taken.",
        "details": "Detalle" if es else "Detail", "day": "Día" if es else "Day", "trigger": "Disparador" if es else "Trigger",
        "trust": "Límite de procedencia" if es else "Provenance boundary",
        "synthetic": "Fuente sintética de prueba" if es else "Synthetic test source",
        "composition": "Procedencia por composición; revisar fuente" if es else "Composition provenance; review source",
        "not_stored": "Texto original no almacenado" if es else "Original text is not stored",
        "manual": "Revisión manual requerida" if es else "Manual review required",
        "practice_gate": "Punto de práctica" if es else "Practice checkpoint",
        "response_structure": "Estructura de respuesta" if es else "Response structure",
        "score_before_response": "Puntuación antes de responder" if es else "Score before response",
        "later_request": "Responde solo en una solicitud posterior explícita." if es else "Respond only in a later explicit request.",
        "practice_clarify": "Aclara antes de practicar. Nombra el hecho pendiente; todavía no se evaluará una respuesta." if es else "Clarify before practicing. Name the missing fact; no response will be evaluated yet.",
        "practice_pause": "Práctica en pausa. Reanuda solo después de una revisión manual con un cambio útil." if es else "Practice is paused. Resume only after a manual review with a useful change.",
        "reentry_title": "Cómo continuar en privado" if es else "How to continue privately",
        "reentry_text": "Vuelve a la conversación privada y responde con contexto breve, acción concreta y resultado observado. La respuesta se usa una sola vez y no se guarda." if es else "Return to the private conversation and respond with brief context, a concrete action, and an observed result. Your answer is used once and is not saved.",
        "do_not_share_response": "No envíes, compartas ni publiques esta respuesta." if es else "Do not send, share, or publish this response.",
        "decision_states": {
            "ready": "Lista para revisión" if es else "Ready for review",
            "clarify": "Aclarar primero" if es else "Clarify first",
            "pause": "Pausar y revisar" if es else "Pause and review",
            "stop": "Detener" if es else "End review",
        },
        "branches": {
            "advance": "Continuar en privado" if es else "Continue privately",
            "clarify": "Aclarar primero" if es else "Clarify first",
            "pause": "Pausar y revisar" if es else "Pause and review",
            "stop": "Detener" if es else "End review",
        },
    }
    state = decision.get("state")
    state_label = labels["decision_states"].get(state)
    if state_label is None:
        raise PrivateFirstInterviewConversionBoardV2RenderError("private board artifact is unavailable")
    header = (
        '<header class="board-header" aria-labelledby="board-heading"><div>'
        f'<p class="board-kicker">{_e(labels["kicker"])}</p><h1 id="board-heading">{_e(labels["heading"])}</h1></div>'
        f'<p class="board-state">{_e(state_label)}</p></header>'
    )
    decision_html = (
        f'<section class="board-decision board-decision-cockpit" data-board-state="{_e(state)}" aria-labelledby="decision-heading"><h2 id="decision-heading">'
        f'{_e(labels["cockpit"])}</h2><dl>{_paragraph(labels["state"], state_label)}'
        f'{_paragraph(labels["objective"], decision.get("objective"))}{_paragraph(labels["current"], decision.get("current_state"))}'
        f'{_paragraph(labels["next"], decision.get("next_safe_action"))}{_paragraph(labels["signal"], decision.get("signal"))}</dl>'
        f'<p class="board-cockpit-prompt"><strong>{_e(labels["decide_now"])}:</strong> {_e(decision.get("next_safe_action"))}</p>'
        f'<p class="board-boundary"><strong>{_e(labels["boundary"])}:</strong> {_e(decision.get("boundary"))}</p></section>'
    )
    provenance_state = provenance.get("provenance_state")
    if provenance_state not in {"synthetic_fixture", "composition_only"}:
        raise PrivateFirstInterviewConversionBoardV2RenderError("private board artifact is unavailable")
    trust_copy = labels["synthetic"] if provenance_state == "synthetic_fixture" else labels["composition"]
    trust = (
        '<section class="board-trust-strip" aria-labelledby="trust-heading"><h2 id="trust-heading">'
        f'{_e(labels["trust"])}</h2><ul><li>{_e(trust_copy)}</li><li>{_e(labels["not_stored"])}</li>'
        f'<li>{_e(labels["manual"])}</li></ul></section>'
    )
    sections = [decision_html, trust]
    if state != "stop":
        def _branch_label(row: Mapping[str, object]) -> str:
            branch = row.get("branch", row.get("decision"))
            label = labels["branches"].get(branch)
            if label is None:
                raise PrivateFirstInterviewConversionBoardV2RenderError("private board artifact is unavailable")
            return label

        ladder = _list_rows(artifact.get("decision_ladder"), lambda row, i: f'<li class="board-branch"><h3>{_e(_branch_label(row))}</h3><dl>{_paragraph(labels["trigger"], row.get("trigger"))}{_paragraph("Requisito" if es else "Requirement", row.get("evidence_requirement"))}{_paragraph("Acción segura" if es else "Safe action", row.get("next_safe_action"))}{_paragraph("Acción bloqueada" if es else "Blocked action", row.get("blocked_action"))}{_paragraph("Pregunta" if es else "Review question", row.get("review_question"))}</dl></li>')
        sequence = _list_rows(artifact.get("sequence"), lambda row, i: f'<li><span class="board-number">{i}</span><h3>{_e(row.get("label"))}</h3><p>{_e(row.get("description"))}</p></li>')
        proof = _list_rows(artifact.get("proof_cards"), lambda row, i: f'<li class="board-proof-card"><h3>{_e(row.get("vacancy_signal"))}</h3><p>{_e(row.get("evidence_summary"))}</p><p><strong>{_e(labels["details"])}:</strong> {_e(row.get("caveat"))}</p></li>')
        risks = _list_rows(artifact.get("risk_checks"), lambda row, i: f'<li class="board-risk-card"><h3>{_e(row.get("topic"))}</h3><dl>{_paragraph("Pregunta" if es else "Question", row.get("trigger_question"))}{_paragraph("Límite seguro" if es else "Safe boundary", row.get("safe_response_boundary"))}{_paragraph("Confirmación" if es else "Confirmation", row.get("confirmation_needed"))}{_paragraph("No afirmar" if es else "Do not claim", row.get("forbidden_claim"))}</dl></li>')
        rehearsal = artifact.get("rehearsal")
        if not isinstance(rehearsal, Mapping):
            raise PrivateFirstInterviewConversionBoardV2RenderError("private board artifact is unavailable")
        if state == "ready":
            practice_instruction = labels["later_request"]
        elif state == "clarify":
            practice_instruction = labels["practice_clarify"]
        else:
            practice_instruction = labels["practice_pause"]
        practice_gate = f'<section class="board-practice-gate" data-board-state="{_e(state)}" aria-labelledby="practice-gate-heading"><h2 id="practice-gate-heading">{_e(labels["practice_gate"])}</h2><p class="board-practice-question"><strong>{_e(rehearsal.get("question"))}</strong></p><dl class="board-facts">{_paragraph(labels["response_structure"], rehearsal.get("response_structure"))}{_paragraph(labels["score_before_response"], rehearsal.get("pre_response_score"))}</dl><p class="board-practice-instruction">{_e(practice_instruction)}</p><p class="board-boundary">{_e(labels["do_not_share_response"])}</p></section>'
        reentry_capsule = (
            f'<aside class="board-reentry-capsule" aria-labelledby="reentry-capsule-heading"><h2 id="reentry-capsule-heading">{_e(labels["reentry_title"])}</h2><p>{_e(labels["reentry_text"])}</p></aside>'
            if state == "ready"
            else ""
        )
        week = _list_rows(artifact.get("week"), lambda row, i: f'<li class="board-day"><h3>{_e(labels["day"])} {_e(row.get("day"))}</h3><p><strong>{_e(row.get("private_action"))}</strong></p><dl>{_paragraph("Límite de evidencia" if es else "Evidence boundary", row.get("evidence_boundary"))}{_paragraph("Punto de revisión" if es else "Review checkpoint", row.get("review_checkpoint"))}{_paragraph("Señal observable" if es else "Observable signal", row.get("observable_signal"))}{_paragraph("Alternativa" if es else "Fallback", row.get("fallback"))}{_paragraph("Regla de parada" if es else "Stop rule", row.get("stop_rule"))}</dl></li>')
        reviews = _list_rows(artifact.get("daily_reviews"), lambda row, i: f'<li class="board-review"><h3>{_e(labels["day"])} {_e(row.get("day"))}</h3><p><strong>{_e(_branch_label(row))}</strong> · {_e(row.get("signal_quality"))}</p><dl>{_paragraph("Señal" if es else "Signal", row.get("observed_signal"))}{_paragraph("Registro" if es else "Evidence log", row.get("evidence_log"))}{_paragraph("Siguiente acción" if es else "Next action", row.get("next_safe_action"))}{_paragraph("Pregunta del coach" if es else "Coach question", row.get("coach_question"))}</dl></li>')
        sections.extend((f'<section class="board-ladder" aria-labelledby="ladder-heading"><h2 id="ladder-heading">{_e(labels["ladder"])}</h2><ol class="board-ladder-list">{ladder}</ol></section>', practice_gate, reentry_capsule, f'<section class="board-sequence" aria-labelledby="sequence-heading"><h2 id="sequence-heading">{_e(labels["sequence"])}</h2><ol>{sequence}</ol></section>', f'<section class="board-proof" aria-labelledby="proof-heading"><h2 id="proof-heading">{_e(labels["proof"])}</h2><ul class="board-proof-list">{proof}</ul></section>', f'<section class="board-risks" aria-labelledby="risks-heading"><h2 id="risks-heading">{_e(labels["risks"])}</h2><ul class="board-risk-list">{risks}</ul></section>', f'<section class="board-week" aria-labelledby="week-heading"><h2 id="week-heading">{_e(labels["week"])}</h2><ol class="board-week-list">{week}</ol></section>', f'<section class="board-reviews" aria-labelledby="reviews-heading"><h2 id="reviews-heading">{_e(labels["reviews"])}</h2><ol class="board-review-list">{reviews}</ol></section>'))
    boundary = artifact.get("approval_boundary")
    if not isinstance(boundary, Mapping) or not isinstance(boundary.get("prohibited_actions"), list):
        raise PrivateFirstInterviewConversionBoardV2RenderError("private board artifact is unavailable")
    prohibited = "".join(f"<li>{_e(action)}</li>" for action in boundary["prohibited_actions"])
    approval = f'<section class="board-approval-boundary" aria-labelledby="approval-heading"><h2 id="approval-heading">{_e(labels["private"])}</h2><p><strong>{_e("Siguiente paso permitido" if es else "Allowed next step")}:</strong> {_e(boundary.get("allowed_next_step"))}</p><p><strong>{_e("Autorización requerida" if es else "Authorization required")}:</strong> {_e(str(boundary.get("authorization_required")).lower())}</p><p>{_e("Acciones prohibidas" if es else "Prohibited actions")}:</p><ul>{prohibited}</ul><p class="board-boundary"><strong>{_e("Límite de autorización" if es else "Authorization boundary")}:</strong> {_e("Mantén esta revisión privada; no ejecutes ninguna acción externa." if es else "Keep this review private; do not execute any external action.")}</p></section>'
    footer = f'<footer class="board-footer"><strong>{_e(labels["private"])}</strong><p>{_e(labels["footer"])} {_e(labels["manual"])}</p><p>{_e("Acciones externas desactivadas." if es else "External actions remain disabled.")}</p></footer>'
    template = ASSET_LOADER.read_private_asset(ASSET_ROOT.parent, TEMPLATE_PATH)
    css = ASSET_LOADER.read_private_asset(ASSET_ROOT.parent, CSS_PATH)
    values = {"{{LANG}}": _e(locale), "{{TITLE}}": _e(labels["title"]), "{{INLINE_CSS}}": css, "{{SKIP}}": _e(labels["skip"]), "{{HEADER}}": header, "{{MAIN}}": '<div class="board-main">' + "".join(sections) + approval + "</div>", "{{FOOTER}}": footer}
    for token, value in values.items():
        if template.count(token) != 1:
            raise RuntimeError("private board template token contract is invalid")
        template = template.replace(token, value)
    if "{{" in template or "}}" in template:
        raise RuntimeError("private board template token contract is invalid")
    return template


def _validated_artifact(value: object) -> Mapping[str, object]:
    if type(value) is not VALIDATOR.ValidatedPrivateFirstInterviewConversionBoardV2:
        raise PrivateFirstInterviewConversionBoardV2RenderError("validated private board is required")
    try:
        artifact = VALIDATOR._revalidate_validated_private_first_interview_conversion_board_v2(value)
        if not isinstance(artifact, Mapping):
            raise ValueError
        return artifact
    except Exception:
        raise PrivateFirstInterviewConversionBoardV2RenderError("validated private board is required") from None


def render_private_first_interview_conversion_board_v2(validated_board: object) -> str:
    return _render_artifact(_validated_artifact(validated_board))
