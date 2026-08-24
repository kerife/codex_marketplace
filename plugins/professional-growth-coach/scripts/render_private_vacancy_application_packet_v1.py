#!/usr/bin/env python3
"""Render one validator-approved private vacancy application packet."""

from __future__ import annotations

import argparse
import hashlib
import html
import importlib.util
import json
import os
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any


_FAILURE = "cannot render private vacancy application packet"
_PLUGIN_ROOT = Path(__file__).resolve().parents[1]
_TEMPLATE_PATH = _PLUGIN_ROOT / "assets" / "private-vacancy-application-packet-v1.html"
_STYLESHEET_PATH = _PLUGIN_ROOT / "assets" / "private-vacancy-application-packet-v1.css"


def _sibling(name: str) -> Any:
    path = Path(__file__).with_name(name)
    specification = importlib.util.spec_from_file_location(f"_pgc_{path.stem}", path)
    if specification is None or specification.loader is None:
        raise RuntimeError("private vacancy packet dependency is unavailable")
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


def _packet_identity() -> Any:
    path = Path(__file__).with_name("private_vacancy_packet_identity.py")
    origin = os.path.realpath(os.fspath(path))
    module_name = (
        "_pgc_private_vacancy_packet_identity_"
        + hashlib.sha256(origin.encode("utf-8")).hexdigest()
    )
    existing = sys.modules.get(module_name)
    if existing is not None:
        if os.path.realpath(os.fspath(getattr(existing, "__file__", ""))) != origin:
            raise RuntimeError("private vacancy packet identity is unavailable")
        return existing
    specification = importlib.util.spec_from_file_location(module_name, path)
    if specification is None or specification.loader is None:
        raise RuntimeError("private vacancy packet identity is unavailable")
    module = importlib.util.module_from_spec(specification)
    sys.modules[module_name] = module
    try:
        specification.loader.exec_module(module)
    except BaseException:
        if sys.modules.get(module_name) is module:
            del sys.modules[module_name]
        raise
    return module


ASSET_LOADER = _sibling("private_asset_loader.py")
_VALIDATOR = _sibling("validate_private_vacancy_application_packet_v1.py")
_WRITER = _sibling("write_private_vacancy_application_packet_v1.py")
_IDENTITY = _packet_identity()

ValidatedPrivateVacancyPacket = _IDENTITY.ValidatedPrivateVacancyPacket
validate_private_vacancy_application_packet_v1 = (
    _VALIDATOR.validate_private_vacancy_application_packet_v1
)
PrivateVacancyApplicationPacketWriteReceipt = (
    _WRITER.PrivateVacancyApplicationPacketWriteReceipt
)


class PrivateVacancyApplicationPacketRenderError(ValueError):
    """Raised with the fixed, no-echo renderer diagnostic."""


_SIGNAL_LABELS = {
    "es": {
        "authentication": "autenticación",
        "certificate_management": "gestión de certificados",
        "incident_response": "respuesta a incidentes",
        "key_rotation": "rotación de llaves",
        "kubernetes": "Kubernetes",
        "linux": "Linux",
        "observability": "observabilidad",
        "python": "Python",
        "terraform": "Terraform",
    },
    "en": {
        "authentication": "authentication",
        "certificate_management": "certificate management",
        "incident_response": "incident response",
        "key_rotation": "key rotation",
        "kubernetes": "Kubernetes",
        "linux": "Linux",
        "observability": "observability",
        "python": "Python",
        "terraform": "Terraform",
    },
}

_COPY = {
    "es": {
        "document_title": "Paquete privado para vacante",
        "private": "Privado · Borrador",
        "subtitle": "Preparación local para revisión humana; no es una solicitud enviada.",
        "skip": "Saltar al contenido principal",
        "readiness": "Decisión de preparación",
        "context": "Contexto de la vacante",
        "vacancy": "Vacante",
        "organization": "Organización",
        "as_of": "Vigencia del paquete",
        "requirements": "Requisitos y evidencia",
        "requirements_intro": "Cobertura cerrada a requisitos públicos y evidencia privada validada.",
        "requirement": "Requisito",
        "priority": "Prioridad",
        "coverage": "Cobertura",
        "confidence": "Confianza",
        "evidence_count": "Registros de evidencia",
        "required": "Obligatorio",
        "preferred": "Preferente",
        "contextual": "Contextual",
        "supported": "Respaldado",
        "partial": "Parcial",
        "missing": "Faltante",
        "conflicting": "En conflicto",
        "high": "Alta",
        "medium": "Media",
        "low": "Baja",
        "unknown": "Desconocida",
        "unsupported": "Evidencia faltante o no respaldada",
        "unsupported_none": "No hay brechas sin resolver en este paquete.",
        "next_private_step": "Siguiente paso privado",
        "drafts": "Borradores de aplicación",
        "drafts_intro": "Texto privado derivado únicamente de evidencia validada; revisar antes de usar.",
        "cv_bullets": "Viñetas de CV",
        "recruiter_summary": "Resumen para reclutamiento",
        "message_angle": "Ángulo de mensaje",
        "claim_review": "Revisión de afirmaciones",
        "claim_caption": "Decisión humana requerida por cada afirmación propuesta.",
        "claim": "Afirmación",
        "surface": "Superficie",
        "requirements_col": "Requisitos",
        "decision": "Decisión",
        "review_note": "Nota de revisión",
        "use": "Usar tras revisión",
        "revise": "Revisar",
        "omit": "Omitir",
        "claim_number": "Afirmación {number}",
        "no_claim_draft": "Sin afirmación redactada",
        "requirement_surface": "Requisito · {signal}",
        "surface_value": "{surface} · {signal}",
        "handoff": "Entrega para primera entrevista",
        "handoff_state": "Disponibilidad",
        "available": "Disponible con entrada manual",
        "suppressed": "Suprimida",
        "tracking": "Evento de seguimiento propuesto",
        "tracking_intro": "Propuesta local; no se inicia ni registra automáticamente.",
        "tracking_event": "Evento",
        "tracking_status": "Estado",
        "tracking_manual": "Registro",
        "tracking_automatic": "Inicio automático",
        "application_packet_drafted": "Paquete de candidatura redactado",
        "proposed": "Propuesto",
        "manual_recording_required": "Registro manual obligatorio",
        "not_automatic": "No",
        "tracking_steps": (
            "Revisar el paquete en privado.",
            "Autorizar por separado cualquier acción externa.",
            "Registrar manualmente el resultado solo después de una acción autorizada.",
        ),
        "approval": "Límite de aprobación",
        "approval_intro": "Este borrador no concede autorización para editar, compartir, enviar, publicar, contactar, agendar, comprar ni inscribirse.",
        "allowed_next": "Único siguiente paso permitido",
        "manual_review": "Revisión manual privada",
        "prohibited": "Acciones que siguen prohibidas",
        "prohibited_list": (
            "Editar, exportar, subir, compartir, enviar o publicar externamente",
            "Aplicar, conectar, contactar o enviar mensajes",
            "Agendar o crear eventos de calendario",
            "Comprar o inscribirse",
        ),
        "suppressed_title": "Trabajo privado suprimido",
        "suppressed_intro": "La decisión de detener elimina borradores, revisión de afirmaciones y detalles de entrega o seguimiento.",
        "suppressed_handoff": "La preparación de entrevista permanece suprimida.",
        "suppressed_tracking": "No se propone ni inicia un evento de seguimiento.",
        "no_external": "No se realiza ninguna acción externa.",
        "print_private": "PRIVADO · BORRADOR",
        "print_boundary": "SIN AUTORIZACIÓN EXTERNA",
        "footer_note": "Artefacto local para revisión manual. Sin formularios, controles ni conexiones externas.",
    },
    "en": {
        "document_title": "Private vacancy application packet",
        "private": "Private · Draft",
        "subtitle": "Local preparation for human review; this is not a submitted application.",
        "skip": "Skip to main content",
        "readiness": "Readiness decision",
        "context": "Vacancy context",
        "vacancy": "Vacancy",
        "organization": "Organization",
        "as_of": "Packet as of",
        "requirements": "Requirements and evidence",
        "requirements_intro": "Coverage is closed to public requirements and validated private evidence.",
        "requirement": "Requirement",
        "priority": "Priority",
        "coverage": "Coverage",
        "confidence": "Confidence",
        "evidence_count": "Evidence records",
        "required": "Required",
        "preferred": "Preferred",
        "contextual": "Contextual",
        "supported": "Supported",
        "partial": "Partial",
        "missing": "Missing",
        "conflicting": "Conflicting",
        "high": "High",
        "medium": "Medium",
        "low": "Low",
        "unknown": "Unknown",
        "unsupported": "Unsupported or missing evidence",
        "unsupported_none": "No unresolved evidence gaps appear in this packet.",
        "next_private_step": "Next private step",
        "drafts": "Application drafts",
        "drafts_intro": "Private text derived only from validated evidence; review before use.",
        "cv_bullets": "CV bullets",
        "recruiter_summary": "Recruiter summary",
        "message_angle": "Message angle",
        "claim_review": "Claim review",
        "claim_caption": "A human decision remains required for every proposed claim.",
        "claim": "Claim",
        "surface": "Surface",
        "requirements_col": "Requirements",
        "decision": "Decision",
        "review_note": "Review note",
        "use": "Use after review",
        "revise": "Revise",
        "omit": "Omit",
        "claim_number": "Claim {number}",
        "no_claim_draft": "No claim drafted",
        "requirement_surface": "Requirement · {signal}",
        "surface_value": "{surface} · {signal}",
        "handoff": "First-interview handoff",
        "handoff_state": "Availability",
        "available": "Available with manual entry",
        "suppressed": "Suppressed",
        "tracking": "Proposed tracking event",
        "tracking_intro": "Local proposal only; nothing is started or recorded automatically.",
        "tracking_event": "Event",
        "tracking_status": "Status",
        "tracking_manual": "Recording",
        "tracking_automatic": "Automatic start",
        "application_packet_drafted": "Application packet drafted",
        "proposed": "Proposed",
        "manual_recording_required": "Manual recording required",
        "not_automatic": "No",
        "tracking_steps": (
            "Review the packet privately.",
            "Authorize any external action separately.",
            "Record the outcome manually only after an authorized action.",
        ),
        "approval": "Approval boundary",
        "approval_intro": "This draft grants no authorization to edit, share, submit, publish, contact, schedule, purchase, or enroll.",
        "allowed_next": "Only allowed next step",
        "manual_review": "Private manual review",
        "prohibited": "Actions that remain prohibited",
        "prohibited_list": (
            "Edit, export, upload, share, submit, or publish externally",
            "Apply, connect, contact, or send messages",
            "Schedule or create calendar events",
            "Purchase or enroll",
        ),
        "suppressed_title": "Private work is suppressed",
        "suppressed_intro": "The stop decision removes drafts, claim review, and handoff or tracking detail.",
        "suppressed_handoff": "Interview preparation remains suppressed.",
        "suppressed_tracking": "No tracking event is proposed or started.",
        "no_external": "No external action is performed.",
        "print_private": "PRIVATE · DRAFT",
        "print_boundary": "NO EXTERNAL AUTHORIZATION",
        "footer_note": "Local artifact for manual review. No forms, controls, or external connections.",
    },
}


def _escape(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("text is unavailable")
    return html.escape(value, quote=True)


def _mapping(value: object) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError("mapping is unavailable")
    return value


def _rows(value: object) -> Sequence[object]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise ValueError("rows are unavailable")
    return value


def _artifact(validated_packet: object) -> dict[str, object]:
    if type(validated_packet) is not ValidatedPrivateVacancyPacket:
        raise PrivateVacancyApplicationPacketRenderError(_FAILURE)
    try:
        artifact = validated_packet.artifact
        if not isinstance(artifact, dict):
            raise ValueError("artifact is unavailable")
        return artifact
    except Exception:
        raise PrivateVacancyApplicationPacketRenderError(_FAILURE) from None


def _definition_list(rows: Sequence[tuple[str, str]], css_class: str) -> str:
    items = "".join(
        f"<div><dt>{label}</dt><dd>{value}</dd></div>" for label, value in rows
    )
    return f'<dl class="{css_class}">{items}</dl>'


def _section(identifier: str, css_class: str, title: str, body: str) -> str:
    title_id = f"{identifier}-title"
    return (
        f'  <section id="{identifier}" class="{css_class}" '
        f'aria-labelledby="{title_id}">\n'
        f'    <h2 id="{title_id}">{title}</h2>\n{body}\n'
        "  </section>"
    )


def _requirements(artifact: Mapping[str, object], locale: str) -> str:
    copy = _COPY[locale]
    cards: list[str] = []
    for number, raw_row in enumerate(_rows(artifact["requirement_evidence"]), start=1):
        row = _mapping(raw_row)
        signal = _SIGNAL_LABELS[locale][str(row["signal"])]
        fact_count = len(_rows(row["fact_ids"]))
        details = _definition_list(
            (
                (_escape(copy["priority"]), _escape(copy[str(row["priority"])])),
                (_escape(copy["coverage"]), _escape(copy[str(row["coverage"])])),
                (_escape(copy["confidence"]), _escape(copy[str(row["confidence"])])),
                (_escape(copy["evidence_count"]), str(fact_count)),
            ),
            "packet-detail-list",
        )
        cards.append(
            f'<li><article class="packet-requirement-card" '
            f'aria-labelledby="requirement-title-{number}">'
            f'<p class="packet-eyebrow">{_escape(copy["requirement"])} {number}</p>'
            f'<h3 id="requirement-title-{number}">{_escape(signal)}</h3>'
            f"{details}</article></li>"
        )
    body = (
        f'    <p class="packet-note">{_escape(copy["requirements_intro"])}</p>\n'
        f'    <ul class="packet-card-grid">{"".join(cards)}</ul>'
    )
    return _section(
        "packet-requirements", "packet-section packet-requirements", _escape(copy["requirements"]), body
    )


def _unsupported(artifact: Mapping[str, object], locale: str) -> str:
    copy = _COPY[locale]
    items: list[str] = []
    for raw_row in _rows(artifact["unsupported_or_missing_claims"]):
        row = _mapping(raw_row)
        signal = _SIGNAL_LABELS[locale][str(row["signal"])]
        items.append(
            f"<li><strong>{_escape(signal)}</strong> — "
            f'{_escape(copy["next_private_step"])}: {_escape(row["next_private_step"])}</li>'
        )
    body = (
        f'    <ul class="packet-list">{"".join(items)}</ul>'
        if items
        else f'    <p>{_escape(copy["unsupported_none"])}</p>'
    )
    return _section(
        "packet-unsupported", "packet-section packet-unsupported", _escape(copy["unsupported"]), body
    )


def _draft_index(artifact: Mapping[str, object]) -> dict[str, tuple[str, Mapping[str, object]]]:
    index: dict[str, tuple[str, Mapping[str, object]]] = {}
    drafts = _mapping(artifact["draft_materials"])
    for surface in ("cv_bullets", "recruiter_summary", "message_angle"):
        for raw_row in _rows(drafts[surface]):
            row = _mapping(raw_row)
            index[str(row["draft_id"])] = (surface, row)
    return index


def _signal_index(artifact: Mapping[str, object]) -> dict[str, str]:
    result: dict[str, str] = {}
    for raw_row in _rows(artifact["requirement_evidence"]):
        row = _mapping(raw_row)
        result[str(row["requirement_id"])] = str(row["signal"])
    return result


def _drafts(artifact: Mapping[str, object], locale: str) -> str:
    copy = _COPY[locale]
    drafts = _mapping(artifact["draft_materials"])
    groups: list[str] = []
    for surface in ("cv_bullets", "recruiter_summary", "message_angle"):
        items = "".join(
            f'<li class="packet-draft-card">{_escape(_mapping(row)["text"])}</li>'
            for row in _rows(drafts[surface])
        )
        groups.append(
            f'<article aria-labelledby="draft-{surface}-title">'
            f'<h3 id="draft-{surface}-title">{_escape(copy[surface])}</h3>'
            f'<ol class="packet-list">{items}</ol></article>'
        )
    body = (
        f'    <p class="packet-note">{_escape(copy["drafts_intro"])}</p>\n'
        f'    <div class="packet-card-grid">{"".join(groups)}</div>'
    )
    return _section("packet-drafts", "packet-section packet-drafts", _escape(copy["drafts"]), body)


def _claim_review(artifact: Mapping[str, object], locale: str) -> str:
    copy = _COPY[locale]
    drafts = _draft_index(artifact)
    signals = _signal_index(artifact)
    body_rows: list[str] = []
    for number, raw_claim in enumerate(_rows(artifact["claim_review"]), start=1):
        claim = _mapping(raw_claim)
        requirement_ids = [str(value) for value in _rows(claim["requirement_ids"])]
        signal_labels = [_SIGNAL_LABELS[locale][signals[value]] for value in requirement_ids]
        signal_text = ", ".join(signal_labels)
        draft_id = claim["draft_id"]
        if draft_id is None:
            surface = str(copy["requirement_surface"]).format(signal=signal_text)
            claim_text = str(copy["no_claim_draft"])
        else:
            surface_name, draft = drafts[str(draft_id)]
            surface = str(copy["surface_value"]).format(
                surface=copy[surface_name], signal=signal_text
            )
            claim_text = str(draft["text"])
        body_rows.append(
            f'<tr id="claim-row-{number}">'
            f'<th id="claim-row-label-{number}" scope="row">'
            f'<span class="packet-eyebrow">'
            f'{_escape(str(copy["claim_number"]).format(number=number))}</span> — '
            f'{_escape(claim_text)}</th>'
            f'<td>{_escape(surface)}</td>'
            f'<td>{_escape(signal_text)}</td>'
            f'<td>{_escape(copy[str(claim["confidence"])])}</td>'
            f'<td>{_escape(copy[str(claim["decision"])])}</td>'
            f'<td>{_escape(claim["review_note"])}</td></tr>'
        )
    table = (
        '<div class="packet-table-region"><table>'
        f'<caption>{_escape(copy["claim_caption"])}</caption>'
        '<thead><tr>'
        f'<th scope="col">{_escape(copy["claim"])}</th>'
        f'<th scope="col">{_escape(copy["surface"])}</th>'
        f'<th scope="col">{_escape(copy["requirements_col"])}</th>'
        f'<th scope="col">{_escape(copy["confidence"])}</th>'
        f'<th scope="col">{_escape(copy["decision"])}</th>'
        f'<th scope="col">{_escape(copy["review_note"])}</th>'
        f'</tr></thead><tbody>{"".join(body_rows)}</tbody></table></div>'
    )
    return _section(
        "packet-claim-review", "packet-section packet-claim-review", _escape(copy["claim_review"]), f"    {table}"
    )


def _handoff(artifact: Mapping[str, object], locale: str) -> str:
    copy = _COPY[locale]
    handoff = _mapping(artifact["first_interview_prep_handoff"])
    details = _definition_list(
        (
            (_escape(copy["handoff_state"]), _escape(copy[str(handoff["state"])])),
            (_escape(copy["next_private_step"]), _escape(handoff["next_private_step"])),
        ),
        "packet-detail-list",
    )
    return _section(
        "packet-handoff", "packet-section packet-handoff", _escape(copy["handoff"]), f"    {details}"
    )


def _tracking(artifact: Mapping[str, object], locale: str) -> str:
    copy = _COPY[locale]
    tracking = _mapping(artifact["tracking_proposal"])
    event = {
        "application_packet_drafted": copy["application_packet_drafted"],
    }[str(tracking["event_kind"])]
    status = {"proposed": copy["proposed"]}[str(tracking["record_state"])]
    automatic = {False: copy["not_automatic"]}[tracking["auto_start"]]
    manual = {True: copy["manual_recording_required"]}[
        tracking["manual_reentry_required"]
    ]
    details = _definition_list(
        (
            (_escape(copy["tracking_event"]), _escape(event)),
            (_escape(copy["tracking_status"]), _escape(status)),
            (_escape(copy["tracking_manual"]), _escape(manual)),
            (_escape(copy["tracking_automatic"]), _escape(automatic)),
        ),
        "packet-summary-grid",
    )
    items = "".join(f"<li>{_escape(step)}</li>" for step in copy["tracking_steps"])
    body = (
        f'    <p class="packet-note">{_escape(copy["tracking_intro"])}</p>\n'
        f"    {details}\n"
        f'    <ol class="packet-list">{items}</ol>'
    )
    return _section(
        "packet-tracking", "packet-section packet-tracking", _escape(copy["tracking"]), body
    )


def _suppressed(locale: str) -> str:
    copy = _COPY[locale]
    body = (
        f'    <p>{_escape(copy["suppressed_intro"])}</p>\n'
        '    <ul class="packet-list">'
        f'<li>{_escape(copy["suppressed_handoff"])}</li>'
        f'<li>{_escape(copy["suppressed_tracking"])}</li></ul>'
    )
    return _section(
        "packet-suppressed", "packet-suppressed", _escape(copy["suppressed_title"]), body
    )


def _approval(locale: str) -> str:
    copy = _COPY[locale]
    prohibited = "".join(
        f"<li>{_escape(item)}</li>" for item in copy["prohibited_list"]
    )
    details = _definition_list(
        ((_escape(copy["allowed_next"]), _escape(copy["manual_review"])),),
        "packet-detail-list",
    )
    body = (
        f'    <div class="packet-boundary"><p>{_escape(copy["approval_intro"])}</p>{details}</div>\n'
        f'    <h3>{_escape(copy["prohibited"])}</h3>\n'
        f'    <ul class="packet-list">{prohibited}</ul>\n'
        f'    <p><strong>{_escape(copy["no_external"])}</strong></p>'
    )
    return _section("packet-approval", "packet-approval", _escape(copy["approval"]), body)


def _render_document(artifact: Mapping[str, object], template: str, css: str) -> str:
    locale = str(artifact["locale"])
    copy = _COPY[locale]
    target = _mapping(artifact["target_binding"])
    readiness = _mapping(artifact["readiness"])
    status_class = {
        "ready_for_manual_authorization": "is-ready",
        "revise_first": "is-revise",
        "stop": "is-stop",
    }[str(readiness["state"])]
    header = (
        '  <header class="packet-header packet-shell">\n'
        f'    <p class="packet-kicker">{_escape(copy["private"])}</p>\n'
        f'    <h1 id="packet-title">{_escape(copy["document_title"])}</h1>\n'
        f'    <p class="packet-subtitle">{_escape(copy["subtitle"])}</p>\n'
        "  </header>"
    )
    readiness_body = (
        f'    <p class="packet-status-label">{_escape(copy["readiness"])}</p>\n'
        f'    <h2 id="readiness-title">{_escape(readiness["headline"])}</h2>\n'
        f'    <p>{_escape(readiness["rationale"])}</p>'
    )
    readiness_section = (
        f'  <section id="packet-readiness" class="packet-readiness {status_class}" '
        f'aria-labelledby="readiness-title">\n{readiness_body}\n  </section>'
    )
    context = _definition_list(
        (
            (_escape(copy["vacancy"]), _escape(target["vacancy_title"])),
            (_escape(copy["organization"]), _escape(target["organization_label"])),
            (_escape(copy["as_of"]), _escape(artifact["as_of_date"])),
        ),
        "packet-summary-grid",
    )
    context_section = _section(
        "packet-context", "packet-section packet-context", _escape(copy["context"]), f"    {context}"
    )
    body_sections = [
        readiness_section,
        context_section,
        _requirements(artifact, locale),
        _unsupported(artifact, locale),
    ]
    if str(readiness["state"]) == "stop":
        body_sections.append(_suppressed(locale))
    else:
        body_sections.extend(
            (
                _drafts(artifact, locale),
                _claim_review(artifact, locale),
                _handoff(artifact, locale),
                _tracking(artifact, locale),
            )
        )
    body_sections.append(_approval(locale))
    main = (
        '  <main id="main-content" class="packet-shell" tabindex="-1" '
        'aria-labelledby="packet-title">\n'
        + "\n".join(body_sections)
        + "\n  </main>"
    )
    footer = (
        f'  <footer class="packet-footer packet-shell" '
        f'data-print-private="{_escape(copy["print_private"])}" '
        f'data-print-boundary="{_escape(copy["print_boundary"])}">\n'
        f'    <p><strong>{_escape(copy["print_private"])} · '
        f'{_escape(copy["print_boundary"])}</strong></p>\n'
        f'    <p>{_escape(copy["footer_note"])}</p>\n'
        "  </footer>"
    )
    replacements = {
        "{{LANG}}": locale,
        "{{DOCUMENT_TITLE}}": _escape(copy["document_title"]),
        "{{INLINE_CSS}}": css.rstrip("\n"),
        "{{PRINT_PRIVATE}}": _escape(copy["print_private"]),
        "{{PRINT_BOUNDARY}}": _escape(copy["print_boundary"]),
        "{{SKIP_LINK}}": _escape(copy["skip"]),
        "{{HEADER}}": header,
        "{{MAIN}}": main,
        "{{FOOTER}}": footer,
    }
    rendered = template
    for token, replacement in replacements.items():
        if rendered.count(token) != 1:
            raise ValueError("template token is unavailable")
        rendered = rendered.replace(token, replacement)
    if "{{" in rendered or "}}" in rendered:
        raise ValueError("template token is unavailable")
    return rendered


def render_private_vacancy_application_packet_v1(validated_packet: object) -> str:
    """Render only an opaque, fully validated private packet snapshot."""
    artifact = _artifact(validated_packet)
    try:
        template = ASSET_LOADER.read_private_asset(
            _PLUGIN_ROOT, _TEMPLATE_PATH, "private vacancy application packet template"
        )
        css = ASSET_LOADER.read_private_asset(
            _PLUGIN_ROOT, _STYLESHEET_PATH, "private vacancy application packet stylesheet"
        )
        return _render_document(artifact, template, css)
    except Exception:
        raise PrivateVacancyApplicationPacketRenderError(_FAILURE) from None


def write_private_vacancy_application_packet_html_v1(
    validated_packet: object,
    output_path: object,
    *,
    force: bool = False,
) -> PrivateVacancyApplicationPacketWriteReceipt:
    """Atomically write one HTML rendering from the supplied opaque snapshot."""
    artifact = _artifact(validated_packet)
    try:
        content = render_private_vacancy_application_packet_v1(validated_packet).encode("utf-8")
        output = _WRITER._resolved_output_path(output_path)
        receipt = _WRITER._receipt_for(artifact, output)
        _WRITER._atomic_private_write(output, content, force=force)
        return receipt
    except Exception:
        raise PrivateVacancyApplicationPacketRenderError(_FAILURE) from None


def _load_validated_packet(packet_path: Path, source_group_path: Path):
    try:
        artifact = _VALIDATOR.load_private_vacancy_application_packet_v1(packet_path)
        source_group = _WRITER._load_source_group(source_group_path)
        return validate_private_vacancy_application_packet_v1(artifact, source_group)
    except Exception:
        raise PrivateVacancyApplicationPacketRenderError(_FAILURE) from None


class _NoEchoArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        del message
        raise PrivateVacancyApplicationPacketRenderError(_FAILURE)


def _cli(argv: list[object] | None = None) -> int:
    parser = _NoEchoArgumentParser(
        description="Render a private vacancy application packet."
    )
    parser.add_argument("packet", type=Path)
    parser.add_argument("--source-group", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--force", action="store_true")
    try:
        args = parser.parse_args(argv)
        validated = _load_validated_packet(args.packet, args.source_group)
        receipt = write_private_vacancy_application_packet_html_v1(
            validated, args.output, force=args.force
        )
        if not _WRITER._receipt_matches(receipt, validated, args.output):
            raise PrivateVacancyApplicationPacketRenderError(_FAILURE)
        print(
            json.dumps(
                _WRITER._receipt_payload(receipt),
                ensure_ascii=False,
                separators=(",", ":"),
            )
        )
        return 0
    except SystemExit as error:
        return 0 if error.code == 0 else 2
    except BaseException:
        print(_FAILURE, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(_cli())
