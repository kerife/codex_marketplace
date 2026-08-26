#!/usr/bin/env python3
"""Render a validated private first-interview conversion board offline."""

from __future__ import annotations

import html
import importlib.util
import os
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

ASSET_ROOT = Path(__file__).resolve().parents[1] / "assets"
TEMPLATE_PATH = ASSET_ROOT / "private-first-interview-conversion-board-v1.html"
CSS_PATH = ASSET_ROOT / "private-first-interview-conversion-board-v1.css"


def _load(name: str, module_name: str) -> Any:
    path = Path(__file__).with_name(name)
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError("private first-interview renderer dependency unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


ASSET_LOADER = _load("private_asset_loader.py", "private_first_interview_board_asset_loader")
VALIDATOR = _load("validate_private_first_interview_conversion_board_v1.py", "private_first_interview_board_validator")


class PrivateFirstInterviewConversionBoardRenderError(ValueError):
    """Raised when a board is not an exact validator-issued proof."""


def _e(value: object) -> str:
    return html.escape(str(value) if value is not None else "", quote=True)


def _paragraph(label: str, value: object) -> str:
    return f"<dt>{_e(label)}</dt><dd>{_e(value)}</dd>"


def _render_artifact(artifact: Mapping[str, object]) -> str:
    locale = artifact.get("locale")
    if locale not in ("en", "es") or not isinstance(artifact.get("decision"), list):
        raise PrivateFirstInterviewConversionBoardRenderError("private board artifact is unavailable")
    es = locale == "es"
    labels = {
        "title": "Tablero privado de primera entrevista" if es else "Private first-interview conversion board",
        "skip": "Ir al contenido principal" if es else "Skip to main content",
        "kicker": "Revisión privada · solo borrador" if es else "Private review · draft only",
        "heading": "Preparación para la primera entrevista" if es else "First-interview preparation",
        "state": "Estado" if es else "State", "objective": "Objetivo" if es else "Objective",
        "current": "Situación actual" if es else "Current situation", "next": "Siguiente acción segura" if es else "Next safe action",
        "signal": "Señal observada" if es else "Observed signal", "boundary": "Límite" if es else "Boundary",
        "sequence": "Secuencia de revisión" if es else "Review sequence", "proof": "Señales de prueba" if es else "Proof signals",
        "risks": "Comprobaciones de riesgo" if es else "Risk checks", "rehearsal": "Ensayo privado" if es else "Private rehearsal",
        "week": "Plan privado de siete días" if es else "Seven-day private plan", "ladder": "Escalera de decisión" if es else "Decision ladder",
        "reviews": "Plantillas de revisión diaria" if es else "Daily review templates", "private": "Límite privado" if es else "Private boundary",
        "footer": "No se realizó ninguna acción externa." if es else "No external action was taken.",
        "details": ("Detalle" if es else "Detail"), "day": "Día" if es else "Day", "trigger": "Disparador" if es else "Trigger",
    }
    decision = artifact["decision"][0]
    header = f'<header class="board-header"><div><p class="board-kicker">{_e(labels["kicker"])}</p><h1>{_e(labels["heading"])}</h1></div><p class="board-state">{_e(decision["state"])}</p></header>'
    decision_html = f'<section class="board-decision"><h2>{_e(labels["objective"])}</h2><dl>{_paragraph(labels["state"], decision["state"])}{_paragraph(labels["objective"], decision["objective"])}{_paragraph(labels["current"], decision["current_state"])}{_paragraph(labels["next"], decision["next_safe_action"])}{_paragraph(labels["signal"], decision["signal"])}</dl><p class="board-boundary"><strong>{_e(labels["boundary"])}:</strong> {_e(decision["boundary"])}</p></section>'
    sections = [decision_html]
    if decision["state"] != "stop":
        sequence = "".join(f'<li><span class="board-number">{i}</span><h3>{_e(row["label"])}</h3><p>{_e(row["description"])}</p></li>' for i, row in enumerate(artifact["sequence"], 1))
        proof = "".join(f'<li class="board-proof-card"><h3>{_e(row["vacancy_signal"])}</h3><p>{_e(row["evidence_summary"])}</p><p><strong>{_e(labels["details"])}:</strong> {_e(row["caveat"])}</p></li>' for row in artifact["proof_cards"])
        risks = "".join(f'<li class="board-risk-card"><h3>{_e(row["topic"])}</h3><dl>{_paragraph("Pregunta" if es else "Question", row["trigger_question"])}{_paragraph("Límite seguro" if es else "Safe boundary", row["safe_response_boundary"])}{_paragraph("Confirmación" if es else "Confirmation", row["confirmation_needed"])}{_paragraph("No afirmar" if es else "Do not claim", row["forbidden_claim"])}</dl></li>' for row in artifact["risk_checks"])
        rehearsal = artifact["rehearsal"]
        rehearsal_html = f'<section class="board-rehearsal"><h2>{_e(labels["rehearsal"])}</h2><p><strong>{_e(rehearsal["question"])}</strong></p><dl class="board-facts">{_paragraph("Propósito" if es else "Purpose", rehearsal["purpose"])}{_paragraph("Estructura" if es else "Structure", rehearsal["response_structure"])}{_paragraph("Espera" if es else "Wait boundary", rehearsal["wait_boundary"])}{_paragraph("Puntuación previa" if es else "Pre-response score", rehearsal["pre_response_score"])}</dl></section>'
        week = "".join(f'<li class="board-day"><h3>{_e(labels["day"])} {_e(row["day"])}</h3><p><strong>{_e(row["private_action"])}</strong></p><dl>{_paragraph("Límite de evidencia" if es else "Evidence boundary", row["evidence_boundary"])}{_paragraph("Punto de revisión" if es else "Review checkpoint", row["review_checkpoint"])}{_paragraph("Señal observable" if es else "Observable signal", row["observable_signal"])}{_paragraph("Alternativa" if es else "Fallback", row["fallback"])}{_paragraph("Regla de parada" if es else "Stop rule", row["stop_rule"])}</dl></li>' for row in artifact["week"])
        ladder = "".join(f'<li class="board-branch"><h3>{_e(row["branch"])}</h3><dl>{_paragraph(labels["trigger"], row["trigger"])}{_paragraph("Requisito" if es else "Requirement", row["evidence_requirement"])}{_paragraph("Acción segura" if es else "Safe action", row["next_safe_action"])}{_paragraph("Acción bloqueada" if es else "Blocked action", row["blocked_action"])}{_paragraph("Pregunta" if es else "Review question", row["review_question"])}</dl></li>' for row in artifact["decision_ladder"])
        reviews = "".join(f'<li class="board-review"><h3>{_e(labels["day"])} {_e(row["day"])}</h3><p><strong>{_e(row["decision"])}</strong> · {_e(row["signal_quality"])}</p><dl>{_paragraph("Señal" if es else "Signal", row["observed_signal"])}{_paragraph("Registro" if es else "Evidence log", row["evidence_log"])}{_paragraph("Siguiente acción" if es else "Next action", row["next_safe_action"])}{_paragraph("Pregunta del coach" if es else "Coach question", row["coach_question"])}</dl></li>' for row in artifact["daily_reviews"])
        sections.extend((f'<section class="board-sequence"><h2>{_e(labels["sequence"])}</h2><ol>{sequence}</ol></section>', f'<section class="board-proof"><h2>{_e(labels["proof"])}</h2><ul class="board-proof-list">{proof}</ul></section>', f'<section class="board-risks"><h2>{_e(labels["risks"])}</h2><ul class="board-risk-list">{risks}</ul></section>', rehearsal_html, f'<section class="board-week"><h2>{_e(labels["week"])}</h2><ol class="board-week-list">{week}</ol></section>', f'<section class="board-ladder"><h2>{_e(labels["ladder"])}</h2><ol class="board-ladder-list">{ladder}</ol></section>', f'<section class="board-reviews"><h2>{_e(labels["reviews"])}</h2><ol class="board-review-list">{reviews}</ol></section>'))
    boundary = artifact["approval_boundary"]
    prohibited = "".join(f"<li>{_e(action)}</li>" for action in boundary["prohibited_actions"])
    approval = (
        f'<section class="board-approval-boundary"><h2>{_e(labels["private"])}</h2>'
        f'<p><strong>{_e("Siguiente paso permitido" if es else "Allowed next step")}:</strong> {_e(boundary["allowed_next_step"])}</p>'
        f'<p><strong>{_e("Autorización requerida" if es else "Authorization required")}:</strong> {_e(str(boundary["authorization_required"]).lower())}</p>'
        f'<p>{_e("Acciones prohibidas" if es else "Prohibited actions")}:</p><ul>{prohibited}</ul>'
        f'<p class="board-boundary"><strong>{_e("Límite de autorización" if es else "Authorization boundary")}:</strong> {_e("Mantén esta revisión privada; no ejecutes ninguna acción externa." if es else "Keep this review private; do not execute any external action.")}</p></section>'
    )
    footer = f'<footer class="board-footer"><strong>{_e(labels["private"])}</strong><p>{_e(labels["footer"])} {_e("Revisión manual requerida." if es else "Manual private review is required.")}</p><p>{_e("Acciones externas desactivadas." if es else "External actions remain disabled.")}</p></footer>'
    template = ASSET_LOADER.read_private_asset(ASSET_ROOT.parent, TEMPLATE_PATH)
    css = ASSET_LOADER.read_private_asset(ASSET_ROOT.parent, CSS_PATH)
    values = {"{{LANG}}": _e(locale), "{{TITLE}}": _e(labels["title"]), "{{INLINE_CSS}}": css, "{{SKIP}}": _e(labels["skip"]), "{{HEADER}}": header, "{{MAIN}}": '<div class="board-main">' + ''.join(sections) + approval + '</div>', "{{FOOTER}}": footer}
    for token, value in values.items():
        if template.count(token) != 1:
            raise RuntimeError("private board template token contract is invalid")
        template = template.replace(token, value)
    if "{{" in template or "}}" in template:
        raise RuntimeError("private board template token contract is invalid")
    del boundary
    return template


def _validated_artifact(value: object) -> Mapping[str, object]:
    if type(value) is not VALIDATOR.ValidatedPrivateFirstInterviewConversionBoard:
        raise PrivateFirstInterviewConversionBoardRenderError("validated private board is required")
    try:
        artifact = VALIDATOR._revalidate_validated_private_first_interview_conversion_board(value)
        if not isinstance(artifact, Mapping):
            raise ValueError
        return artifact
    except Exception:
        raise PrivateFirstInterviewConversionBoardRenderError("validated private board is required") from None


def render_private_first_interview_conversion_board_v1(validated_board: object) -> str:
    return _render_artifact(_validated_artifact(validated_board))
