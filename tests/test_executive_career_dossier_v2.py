"""Behavioral contracts for the status-only executive career dossier v2."""

from __future__ import annotations

import copy
import functools
import hashlib
import html
import importlib.util
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
import unittest
from collections.abc import Iterator, Mapping
from html.parser import HTMLParser
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "plugins" / "professional-growth-coach" / "scripts"
VALIDATOR_PATH = SCRIPTS / "validate_executive_career_dossier_v2.py"
RENDERER_PATH = SCRIPTS / "render_executive_career_dossier_v2.py"
V1_RENDERER_PATH = SCRIPTS / "render_executive_career_dossier.py"
FIXTURE_ROOT = REPO_ROOT / "tests" / "evals" / "with-skill" / "fixtures" / "executive-career-dossier"
V2_FIXTURE_ROOT = FIXTURE_ROOT.with_name("executive-career-dossier-v2")
RESEARCH_FIXTURE_ROOT = FIXTURE_ROOT.with_name("target-vacancy-research")
MARKET_FIXTURE_ROOT = FIXTURE_ROOT.with_name("career-market-learning-dossier")
MARKET_V2_FIXTURE_ROOT = FIXTURE_ROOT.with_name("career-market-learning-dossier-v2")
LEARNING_V2_FIXTURE_ROOT = FIXTURE_ROOT.with_name("career-learning-decision-v2")
PROVIDER_RESEARCH_FIXTURE_ROOT = FIXTURE_ROOT.with_name(
    "career-learning-provider-research"
)
ELIGIBILITY_V3_FIXTURE_ROOT = FIXTURE_ROOT.with_name(
    "career-next-action-eligibility-v1"
)
LEARNING_V3_FIXTURE_ROOT = FIXTURE_ROOT.with_name("career-learning-decision-v3")
WEEKLY_CSS_PATH = (
    REPO_ROOT
    / "plugins"
    / "professional-growth-coach"
    / "assets"
    / "career-learning-eligibility-v1.css"
)
NO_MARKET_RENDER_SNAPSHOTS = {
    "scenario-a-es.json": (48801, "19d85f8a4061ca5eb44746801a2f0094a9109d9d5764e80d515d84bafdfd79d6"),
    "scenario-c-en.json": (46856, "7f4513fc555d60a6042981168437aea3b1dc470027fd700d1604588e291ece7c"),
}
HISTORICAL_COMPLETE_RENDER_SNAPSHOTS = {
    "v1": (97805, "4dbb6be8e1a95cdcc8f3e937dcca600fb26f9dc53d7ef519027048c73b12316f"),
    "v2": (101282, "0232f7d71de6e85f1b18d7407703b7af944c936c9c905b55fd9a3592067d6167"),
}
ELIGIBILITY_V3_CASES = (
    "unavailable",
    "selection_required",
    "insufficient_recurrence",
    "gap_unknown",
    "supported",
    "provider_choice",
    "provider_evidence",
    "experience",
    "proof",
    "practice",
    "terminology",
    "knowledge",
)
WEEKLY_STATE_COPY = {
    "es": {
        "selection_required": "Elige una pareja válida de vacante y señal (V1–Vn) para decidir el siguiente paso; no se preselecciona ninguna.",
        "insufficient_recurrence": "La señal aparece en 1/5; no alcanza el umbral de dos vacantes activas.",
        "gap_unknown": "La relación de brecha todavía no está confirmada.",
        "supported": "La señal está respaldada; ese respaldo no demuestra una brecha.",
        "provider_choice": "Hay recurrencia y una brecha de conocimiento confirmada; falta elegir una opción oficial verificada.",
        "provider_evidence": "Hay recurrencia y una brecha de conocimiento confirmada, pero no hay una opción oficial verificada para esta señal.",
        "experience": "La brecha requiere experiencia profesional o de producción; un laboratorio, curso o certificación no la sustituye.",
        "proof": "La señal aparece en 2/5 y la relación brecha de evidencia práctica fue confirmada por la persona candidata.",
        "practice": "La señal aparece en 2/5 y la relación brecha de práctica fue confirmada por la persona candidata.",
        "terminology": "La señal aparece en 2/5 y la relación brecha de terminología fue confirmada por la persona candidata.",
        "knowledge": "La señal aparece en 2/5 y la relación brecha de conocimiento fue confirmada por la persona candidata.",
    },
    "en": {
        "selection_required": "Choose one valid vacancy-and-signal pair (V1–Vn) to decide the next step; none is preselected.",
        "insufficient_recurrence": "The signal appears in 1/4; it does not meet the two-active-vacancy threshold.",
        "gap_unknown": "The gap relation is not confirmed yet.",
        "supported": "The signal is supported; that support does not establish a gap.",
        "provider_choice": "Recurrence and a confirmed knowledge gap exist; one verified official option still needs to be selected.",
        "provider_evidence": "Recurrence and a confirmed knowledge gap exist, but no verified official option covers this signal.",
        "experience": "The gap requires professional or production experience; a lab, course, or certification cannot substitute for it.",
        "proof": "The signal appears in 2/4, and the proof gap relation was candidate-confirmed.",
        "practice": "The signal appears in 2/4, and the practice gap relation was candidate-confirmed.",
        "terminology": "The signal appears in 2/4, and the terminology gap relation was candidate-confirmed.",
        "knowledge": "The signal appears in 2/4, and the knowledge gap relation was candidate-confirmed.",
    },
}
WEEKLY_ACTION_COPY = {
    "es": {
        "select_target_vacancy_and_signal": ("Elige vacante y señal", "Una pareja pública Vn + señal elegida por ti.", "La vacante y la señal pertenecen a la misma vacante activa."),
        "confirm_gap_relation": ("Confirma la relación de brecha", "Una respuesta estructurada, sin prosa libre, para la señal elegida.", "La relación queda confirmada o marcada como desconocida."),
        "select_provider_option": ("Elige una opción oficial para investigar", "Una opción pública elegida explícitamente; no es una recomendación de compra.", "La opción activa cubre la señal exacta y su fuente oficial está fechada."),
        "prepare_private_vacancy_packet": ("Prepara primero el paquete privado de vacante", "Un borrador privado y verificable para la vacante elegida; no se envía.", "Cada afirmación está respaldada o marcada para confirmar u omitir."),
        "build_bounded_proof": ("Construye una prueba acotada", "Una prueba privada e inspeccionable de la señal elegida.", "La prueba muestra alcance, acción y resultado sin afirmar producción no demostrada."),
        "run_validation_lab": ("Ejecuta un laboratorio de práctica", "Un laboratorio privado y acotado para practicar la señal.", "El resultado es inspeccionable y no se presenta como experiencia profesional."),
        "research_provider_option": ("Investiga la opción elegida", "Una revisión privada de costo, tiempo, requisitos y desconocidos.", "Costo, tiempo, requisitos y mantenimiento están confirmados o marcados como desconocidos."),
        "run_role_search_experiment": ("Prueba una búsqueda acotada de roles", "Una búsqueda privada con la terminología elegida; no se postula.", "La consulta devuelve evidencia fechada o queda registrada como no disponible."),
        "no_learning_yet": ("No compres aprendizaje todavía", "Una nota privada de la evidencia de proveedor que falta.", "Existe una fuente oficial vigente o la decisión permanece aplazada."),
    },
    "en": {
        "select_target_vacancy_and_signal": ("Choose vacancy and signal", "One public Vn + signal pair chosen by you.", "The vacancy and signal belong to the same active vacancy."),
        "confirm_gap_relation": ("Confirm the gap relation", "One structured response without free-form prose for the selected signal.", "The relation is confirmed or marked unknown."),
        "select_provider_option": ("Choose one official option to research", "One explicitly selected public option; this is not a purchase recommendation.", "The active option covers the exact signal and has a dated official source."),
        "prepare_private_vacancy_packet": ("Prepare the private vacancy packet first", "One private, verifiable draft for the selected vacancy; it is not sent.", "Every claim is supported or marked to confirm or omit."),
        "build_bounded_proof": ("Build one bounded proof", "One private, inspectable proof for the selected signal.", "The proof shows scope, action, and result without claiming unsupported production work."),
        "run_validation_lab": ("Run one practice lab", "One private, bounded lab for practicing the signal.", "The result is inspectable and is not presented as professional experience."),
        "research_provider_option": ("Research the selected option", "One private review of cost, time, prerequisites, and unknowns.", "Cost, time, prerequisites, and maintenance are confirmed or marked unknown."),
        "run_role_search_experiment": ("Run one bounded role-search experiment", "One private search using the selected terminology; no application is submitted.", "The query returns dated evidence or is recorded as unavailable."),
        "no_learning_yet": ("Do not buy learning yet", "One private note of the missing provider evidence.", "A current official source exists or the decision remains deferred."),
    },
}
COPY_MARKET_PLACEHOLDER_ES = (
    "Este dossier no incluye evidencia de mercado. Continúa con la evidencia del perfil ya revisada."
)

UNSAFE_COACHING_PROSE = (
    (
        "coach_observation",
        "Publish this on LinkedIn now.",
        "must remain a private review action",
    ),
    (
        "why_it_matters",
        "Publish this on LinkedIn now.",
        "must remain a private review action",
    ),
    (
        "coach_prompt",
        "Publish this on LinkedIn now.",
        "must remain a private review action",
    ),
    (
        "coach_observation",
        "The profile is now live on LinkedIn.",
        "must remain a private review action",
    ),
    (
        "why_it_matters",
        "The profile is now live on LinkedIn.",
        "must remain a private review action",
    ),
    (
        "coach_prompt",
        "The profile is now live on LinkedIn.",
        "must remain a private review action",
    ),
    (
        "coach_prompt",
        "Quit your job now.",
        "must preserve current employment by default",
    ),
    (
        "coach_observation",
        "There were 314 private profile views.",
        "analytics measures require observed aggregate analytics",
    ),
    (
        "why_it_matters",
        "Employers are actively hiring 1000 SREs.",
        "market claims require local dated market evidence",
    ),
)

SAFE_COACHING_PROSE = (
    ("coach_observation", "The incident response scope is ready for private review."),
    ("why_it_matters", "Technical scope supports a focused private coaching review."),
    ("coach_prompt", "Review the private incident response scope for technical clarity."),
)

CANONICAL_PROFILE_SECTIONS = (
    "photo", "banner", "name", "profile_url", "headline", "location",
    "contact_info", "about", "experience", "skills", "featured",
    "certifications", "education", "recommendations", "activity",
    "analytics", "job_preferences",
)

V2_ROUTE_SUPPORT_LABELS = {
    "es": {
        "verified_match": "Evidencia directa",
        "candidate_reported_match": "Reportado por cliente",
    },
    "en": {
        "verified_match": "Direct evidence",
        "candidate_reported_match": "Candidate reported",
    },
}

V2_SOURCE_MUTATION_CASES = (
    ("private name", "dossier_private_name", "Private Candidate Name"),
    ("contact", "research_contact", "private.person@example.test"),
    ("local path", "provider_local_path", "/Users/private-person/source.json"),
    ("url", "provider_url", "https://example.test/private-source"),
    ("snapshot", "market_snapshot", "snap-private-sha256-" + "a" * 64),
    ("internal id", "learning_internal_id", "E-999"),
    ("control", "provider_control", "private\u202esource"),
    ("source prose", "research_source_prose", "Arbitrary private source prose sentinel."),
    ("provider date mismatch", "provider_as_of_date", "2026-08-12"),
)


def _contrast_ratio(foreground: str, background: str) -> float:
    def relative_luminance(value: str) -> float:
        channels = [int(value[index : index + 2], 16) / 255 for index in (1, 3, 5)]
        linear = [
            channel / 12.92
            if channel <= 0.04045
            else ((channel + 0.055) / 1.055) ** 2.4
            for channel in channels
        ]
        return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]

    foreground_luminance = relative_luminance(foreground)
    background_luminance = relative_luminance(background)
    lighter = max(foreground_luminance, background_luminance)
    darker = min(foreground_luminance, background_luminance)
    return (lighter + 0.05) / (darker + 0.05)


def unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, nested in pairs:
        if key in value:
            raise ValueError("duplicate JSON key")
        value[key] = nested
    return value


def load_v1_fixture(name: str) -> dict[str, object]:
    value = json.loads(
        (FIXTURE_ROOT / name).read_text(encoding="utf-8"), object_pairs_hook=unique_object
    )
    if not isinstance(value, dict):
        raise ValueError("fixture must be an object")
    return value


def make_v2_dossier(locale: str = "es") -> dict[str, object]:
    dossier = copy.deepcopy(load_v1_fixture(
        "scenario-a-es.json" if locale == "es" else "scenario-c-en.json"
    ))
    dossier["schema_version"] = "executive-career-dossier-v2"
    inspected = set(dossier["evidence_scope"]["inspected_sections"])
    dossier["section_coverage"] = []
    for section in CANONICAL_PROFILE_SECTIONS:
        if section in inspected:
            dossier["section_coverage"].append({
                "section": section,
                "availability": "inspected_present",
                "evidence_state": "verified",
                "reason": "inspected_content_available",
            })
            continue
        decision = "declined_for_session" if section == "certifications" else "pending_response"
        dossier["section_coverage"].append({
            "section": section,
            "availability": "unavailable",
            "evidence_state": "unknown",
            "reason": "inspection_declined" if decision == "declined_for_session" else "authorization_required",
            "inspection_request": {
                "access_type": "read_only_visible_section_inspection",
                "decision": decision,
                "scope": "current_session_only",
                "carry_forward": False,
            },
        })
    profile_sections = (
        {"E-001": "headline", "E-002": "about", "E-003": "experience", "E-004": "skills", "E-006": "photo", "E-007": "banner"}
        if locale == "es"
        else {"E-001": "headline", "E-002": "skills", "E-003": "about", "E-004": "experience", "E-005": "photo"}
    )
    for evidence in dossier["evidence"]:
        evidence["profile_section"] = profile_sections.get(evidence["id"])
    priority_sections = ("headline", "about", "experience")
    for priority, section in zip(dossier["priorities"], priority_sections, strict=True):
        priority["evidence_ids"] = (
            {"headline": ["E-001"], "about": ["E-002"], "experience": ["E-003"]}
            if locale == "es"
            else {"headline": ["E-001"], "about": ["E-003"], "experience": ["E-004"]}
        )[section]
        priority.update({
            "target_section": section,
            "coach_observation": f"Coach observation for {section}.",
            "why_it_matters": f"Evidence from {section} changes the review.",
            "coach_prompt": f"Complete the private template for {section}.",
            "client_template": {
                "template_id": "context_action_result_v1",
                "field_keys": ["context", "action", "result"],
            },
            "privacy_boundary": "no_raw_profile_text_or_private_values",
        })
    return dossier


def load_json_fixture(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_object)
    if not isinstance(value, dict):
        raise ValueError("fixture must be an object")
    return value


def market_alignment(
    research: dict[str, object], dossier: dict[str, object]
) -> dict[str, object]:
    scripts = str(SCRIPTS)
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    from dossier_snapshot import snapshot_for_dossier
    from validate_target_vacancy_research import snapshot_for_market_dossier

    configured = {
        "python": ("verified_match", ["E-001"]),
        "kubernetes": ("candidate_reported_match", ["E-003"]),
        "terraform": ("adjacent_evidence", ["E-004"]),
        "observability": ("unknown", []),
        "linux": ("explicit_gap", ["E-003"]),
    }
    signals = {
        requirement["signal"]
        for vacancy in research["vacancies"]
        for requirement in vacancy["requirements"]
    }
    return {
        "schema_version": "candidate-market-alignment-v1",
        "research_snapshot": snapshot_for_market_dossier(research),
        "executive_dossier_snapshot": snapshot_for_dossier(dossier),
        "signal_bindings": [
            {
                "signal": signal,
                "support_state": configured[signal][0],
                "evidence_ids": configured[signal][1],
            }
            for signal in sorted(signals)
        ],
        "privacy_boundary": "identity_free_evidence_references_only",
    }


def market_case(
    research_name: str, dossier_name: str
) -> tuple[dict[str, object], dict[str, object], dict[str, object], dict[str, object]]:
    dossier = load_json_fixture(V2_FIXTURE_ROOT / dossier_name)
    research = load_json_fixture(RESEARCH_FIXTURE_ROOT / research_name)
    market = load_json_fixture(MARKET_FIXTURE_ROOT / research_name)
    return dossier, market, research, market_alignment(research, dossier)


def learning_case(
    research_name: str, dossier_name: str, count: int = 3, decision_count: int = 3
) -> tuple[dict[str, object], dict[str, object], dict[str, object], dict[str, object], dict[str, object]]:
    """Build a small validated learning bundle for renderer contract tests."""
    if count == 0:
        dossier, market, research, alignment = market_case(research_name, dossier_name)
    elif count < 5:
        dossier, market, research, alignment = build_limited_market_case(count)
    else:
        dossier, market, research, alignment = market_case(research_name, dossier_name)
    scripts = str(SCRIPTS)
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    from build_career_learning_decision import build_learning_bundle

    vacancy_ids = [row["vacancy_id"] for row in market["vacancies"]]
    evidence_id = next(
        (
            evidence_id
            for row in market["matrix_rows"]
            for evidence_id in row["evidence_ids"]
        ),
        "E-001",
    )
    provider_source = {
        "provider": "HashiCorp",
        "option": "Terraform Associate",
        "source_title": "HashiCorp Certified: Terraform Associate",
        "source_date": market["as_of_date"],
        "source_state": "active",
        "url": "https://developer.hashicorp.com/certifications/infrastructure-automation",
        "geography": "unknown: official page does not establish Mexico eligibility",
        "availability": "active: official provider page is available",
        "current_cost": "unknown: official page does not state the current fee",
        "currency": "unknown: no verified currency",
        "tax": "unknown: tax treatment is not stated",
        "duration": "provider duration unknown: official page does not state exam duration",
        "prerequisite": "unknown: official page does not state prerequisites",
        "renewal": "unknown: official page does not state renewal",
        "maintenance": "unknown: official page does not state maintenance",
        "unknowns": "Mexico eligibility and preparation time are not stated",
    }
    rows = [
        {
            "decision_rank": 1,
            "target_role": "Senior SRE / Platform Engineer",
            "gap_type": "proof",
            "option_type": "portfolio_project",
            "option_name": "Terraform and observability proof artifact",
            "provider_or_owner": "candidate-owned proof project",
            "source_gap_ids": [evidence_id],
            "vacancy_ids": vacancy_ids[: min(2, len(vacancy_ids))],
            "market_evidence_state": "current dated vacancy evidence",
            "cost_time_band": "unknown: candidate effort requires separate confirmation",
            "expected_signal_boundary": "bounded hypothesis: creates inspectable evidence without promising a hiring outcome",
            "portfolio_or_no_learning_alternative": "Complete one bounded proof artifact before buying another credential.",
            "overbuying_risk": "Avoid certificate collecting before one higher-signal artifact is complete.",
            "decision": "do_now",
            "decision_basis": "Repeated vacancy evidence supports a candidate-owned proof artifact before a purchase.",
            "next_action_gate": "No external action; exact authorization is required before publication, sharing, or messaging.",
            "outcome_boundary": "not_an_interview_offer_salary_or_roi_prediction",
            "draft_only": True,
            "no_external_action": True,
            "provider_source": None,
        },
        {
            "decision_rank": 2,
            "target_role": "Senior SRE / Platform Engineer",
            "gap_type": "knowledge",
            "option_type": "course",
            "option_name": "Terraform Associate study path",
            "provider_or_owner": "HashiCorp",
            "source_gap_ids": [evidence_id],
            "vacancy_ids": vacancy_ids[: min(2, len(vacancy_ids))],
            "market_evidence_state": "current dated vacancy evidence",
            "cost_time_band": "unknown: current cost and candidate effort require separate confirmation",
            "expected_signal_boundary": "bounded hypothesis: may corroborate knowledge without promising a hiring outcome",
            "portfolio_or_no_learning_alternative": "Build a bounded Terraform proof artifact before enrolling.",
            "overbuying_risk": "Avoid paying before a cheaper proof comparison is reviewed.",
            "decision": "research_first",
            "decision_basis": "Repeated vacancy evidence supports research, but official provider cost and eligibility remain unknown.",
            "next_action_gate": "No external action; purchase or enrollment requires exact authorization after source review.",
            "outcome_boundary": "not_an_interview_offer_salary_or_roi_prediction",
            "draft_only": True,
            "no_external_action": True,
            "provider_source": provider_source,
        },
        {
            "decision_rank": 3,
            "target_role": "Senior SRE / Platform Engineer",
            "gap_type": "low_return",
            "option_type": "no_learning_yet",
            "option_name": "Finish the current proof artifact first",
            "provider_or_owner": "none",
            "source_gap_ids": [evidence_id],
            "vacancy_ids": vacancy_ids[: min(2, len(vacancy_ids))],
            "market_evidence_state": "current dated vacancy evidence",
            "cost_time_band": "unknown: candidate effort requires separate confirmation",
            "expected_signal_boundary": "bounded hypothesis: protects time for higher-signal proof without promising a hiring outcome",
            "portfolio_or_no_learning_alternative": "Use the existing proof artifact as the lower-cost alternative.",
            "overbuying_risk": "Avoid starting a course before the evidence gap is reviewed again.",
            "decision": "do_now",
            "decision_basis": "Candidate-owned evidence is a higher-priority next move than generic learning.",
            "next_action_gate": "No external action; exact authorization is required before publication, sharing, or messaging.",
            "outcome_boundary": "not_an_interview_offer_salary_or_roi_prediction",
            "draft_only": True,
            "no_external_action": True,
            "provider_source": None,
        },
    ]
    rows.extend(
        [
            {
                **copy.deepcopy(rows[0]),
                "decision_rank": 4,
                "option_type": "lab",
                "option_name": "Observability incident-response lab",
                "decision": "research_first",
            },
            {
                **copy.deepcopy(rows[0]),
                "decision_rank": 5,
                "option_type": "role_search",
                "option_name": "Search for a role that values existing proof",
                "decision": "defer",
            },
        ]
    )
    rows = rows[:decision_count]
    if not vacancy_ids:
        rows = []
    bundle = build_learning_bundle(research, market, dossier, rows)
    return dossier, market, research, alignment, bundle


def semantic_v2_case(
    state: str = "complete",
) -> tuple[
    dict[str, object],
    dict[str, object],
    dict[str, object],
    dict[str, object],
    dict[str, object],
]:
    names = {
        "complete": (
            "scenario-a-es.json",
            "complete-five-es.json",
            "complete-es.json",
            "complete-es.json",
        ),
        "limited": (
            "scenario-c-market-en.json",
            "limited-four-en.json",
            "limited-en.json",
            "limited-en.json",
        ),
        "unavailable": (
            "scenario-a-es.json",
            "unavailable-es.json",
            "unavailable-es.json",
            "unavailable-es.json",
        ),
    }
    dossier_name, market_name, learning_name, provider_name = names[state]
    return (
        load_json_fixture(V2_FIXTURE_ROOT / dossier_name),
        load_json_fixture(MARKET_V2_FIXTURE_ROOT / market_name),
        load_json_fixture(RESEARCH_FIXTURE_ROOT / market_name),
        load_json_fixture(LEARNING_V2_FIXTURE_ROOT / learning_name),
        load_json_fixture(PROVIDER_RESEARCH_FIXTURE_ROOT / provider_name),
    )


def eligibility_v3_case(
    condition: str, locale: str
) -> tuple[dict[str, object], dict[str, object]]:
    root = ELIGIBILITY_V3_FIXTURE_ROOT / f"{condition}-{locale}"
    sources = load_json_fixture(root / "sources.json")
    eligibility = load_json_fixture(root / "eligibility.json")
    return sources, eligibility


@functools.lru_cache(maxsize=None)
def _built_learning_v3(condition: str, locale: str) -> dict[str, object]:
    sources, eligibility = eligibility_v3_case(condition, locale)
    scripts = str(SCRIPTS)
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    from build_career_learning_decision_v3 import build_career_learning_decision_v3

    return build_career_learning_decision_v3(
        sources["research"],
        sources["executive_dossier"],
        sources["market_dossier"],
        sources["gap_response"],
        sources["gap_assessment"],
        eligibility,
        sources["provider_research"],
    )


def semantic_v3_case(condition: str, locale: str) -> dict[str, object]:
    sources, eligibility = eligibility_v3_case(condition, locale)
    canonical = {
        ("proof", "es"): "proof-es",
        ("knowledge", "en"): "knowledge-en",
        ("selection_required", "es"): "selection-required-es",
        ("unavailable", "es"): "unavailable-es",
    }.get((condition, locale))
    learning = (
        load_json_fixture(LEARNING_V3_FIXTURE_ROOT / canonical / "learning.json")
        if canonical is not None
        else copy.deepcopy(_built_learning_v3(condition, locale))
    )
    return {
        "dossier": sources["executive_dossier"],
        "market_dossier": sources["market_dossier"],
        "market_research": sources["research"],
        "market_alignment": None,
        "learning_decision": learning,
        "provider_research": sources["provider_research"],
        "gap_response": sources["gap_response"],
        "gap_assessment": sources["gap_assessment"],
        "next_action_eligibility": eligibility,
    }


def build_limited_market_case(
    count: int,
) -> tuple[dict[str, object], dict[str, object], dict[str, object], dict[str, object]]:
    dossier = load_json_fixture(V2_FIXTURE_ROOT / "scenario-c-en.json")
    research = load_json_fixture(RESEARCH_FIXTURE_ROOT / "limited-four-en.json")
    research["employers"] = research["employers"][:count]
    research["vacancies"] = research["vacancies"][:count]
    alignment = market_alignment(research, dossier)
    scripts = str(SCRIPTS)
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    from build_career_market_learning_dossier import build_market_dossier

    return dossier, build_market_dossier(research, dossier, alignment), research, alignment


def load_validator() -> object:
    specification = importlib.util.spec_from_file_location(
        "validate_executive_career_dossier_v2", VALIDATOR_PATH
    )
    assert specification is not None and specification.loader is not None
    validator = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = validator
    specification.loader.exec_module(validator)
    return validator


def load_renderer() -> object:
    specification = importlib.util.spec_from_file_location(
        "render_executive_career_dossier_v2", RENDERER_PATH
    )
    assert specification is not None and specification.loader is not None
    renderer = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = renderer
    specification.loader.exec_module(renderer)
    return renderer


def load_v1_renderer() -> object:
    specification = importlib.util.spec_from_file_location(
        "render_executive_career_dossier_decide_now_v1", V1_RENDERER_PATH
    )
    assert specification is not None and specification.loader is not None
    renderer = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = renderer
    specification.loader.exec_module(renderer)
    return renderer


def visible_text(rendered: str) -> str:
    without_code = re.sub(r"(?is)<(?:style|script)\b.*?</(?:style|script)>", " ", rendered)
    return " ".join(html.unescape(re.sub(r"(?s)<[^>]+>", " ", without_code)).split())


def decide_now_region(rendered: str) -> tuple[set[str], str, str]:
    match = re.search(
        r'<section(?=[^>]*class="[^"]*\bdecide-now\b[^"]*")'
        r'(?=[^>]*aria-labelledby="decide-now-title")'
        r'(?=[^>]*aria-describedby="([^"]+)")[^>]*>(.*?)</section>',
        rendered,
        re.DOTALL,
    )
    if match is None:
        raise AssertionError("Decide now section is missing")
    return set(re.findall(r'<a href="#([^"]+)">', match.group(2))), match.group(1), match.group(2)


def weekly_decision_region(rendered: str) -> str:
    match = re.search(
        r'<article class="card span-12 weekly-decision"[^>]*>(.*?)</article>',
        rendered,
        re.DOTALL,
    )
    if match is None:
        raise AssertionError("weekly decision card is missing")
    return match.group(0)


class OnePassMapping(Mapping[str, object]):
    """Expose one safe items traversal and make every other read observable."""

    def __init__(self, value: Mapping[str, object], sentinel: str) -> None:
        self._value = dict(value)
        self.sentinel = sentinel
        self.items_calls = 0

    def items(self):
        self.items_calls += 1
        if self.items_calls != 1:
            raise RuntimeError(self.sentinel)
        return self._value.items()

    def __getitem__(self, key: str) -> object:
        raise RuntimeError(self.sentinel)

    def __iter__(self) -> Iterator[str]:
        raise RuntimeError(self.sentinel)

    def __len__(self) -> int:
        raise RuntimeError(self.sentinel)

    def get(self, key: str, default: object = None) -> object:
        raise RuntimeError(self.sentinel)

    def __deepcopy__(self, memo: object) -> object:
        raise RuntimeError(self.sentinel)

    def __str__(self) -> str:
        raise RuntimeError(self.sentinel)


class DossierDOMAudit(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: list[str] = []
        self.references: list[str] = []
        self.classes: list[str] = []
        self.tag_counts: dict[str, int] = {}
        self.heading_levels: list[int] = []
        self.start_tags: list[tuple[str, dict[str, str | None]]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.tag_counts[tag] = self.tag_counts.get(tag, 0) + 1
        values = dict(attrs)
        self.start_tags.append((tag, values))
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self.heading_levels.append(int(tag[1]))
        identifier = values.get("id")
        if identifier:
            self.ids.append(identifier)
        for field in ("aria-labelledby", "aria-describedby"):
            references = values.get(field)
            if references:
                self.references.extend(references.split())
        classes = values.get("class")
        if classes:
            self.classes.extend(classes.split())


class LearningRouteDOMParser(HTMLParser):
    """Collect each public route row within its rendered decision group."""

    _VOID_TAGS = frozenset({
        "area", "base", "br", "col", "embed", "hr", "img", "input", "link",
        "meta", "param", "source", "track", "wbr",
    })

    def __init__(self) -> None:
        super().__init__()
        self.groups: list[tuple[int, list[tuple[str, str, str, str]]]] = []
        self._stack: list[str] = []
        self._card_rank: int | None = None
        self._card_depth: int | None = None
        self._group_rows: list[tuple[str, str, str, str]] | None = None
        self._group_depth: int | None = None
        self._row: dict[str, object] | None = None
        self._row_depth: int | None = None
        self._strong_depth: int | None = None
        self._paragraph_depth: int | None = None
        self._label_depth: int | None = None

    @staticmethod
    def _classes(values: dict[str, str | None]) -> set[str]:
        return set((values.get("class") or "").split())

    @staticmethod
    def _text(parts: object) -> str:
        assert isinstance(parts, list)
        return " ".join("".join(str(part) for part in parts).split())

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag not in self._VOID_TAGS:
            self._stack.append(tag)
        depth = len(self._stack)
        values = dict(attrs)
        classes = self._classes(values)
        if tag == "article" and "learning-decision-card" in classes:
            match = re.fullmatch(
                r"learning-decision-card-title-(\d+)",
                values.get("aria-labelledby") or "",
            )
            if match is None:
                raise AssertionError("learning decision card has no canonical rank label")
            self._card_rank = int(match.group(1))
            self._card_depth = depth
        elif tag == "div" and "learning-signal-route" in classes:
            if self._card_rank is None:
                raise AssertionError("learning route is outside a decision card")
            self._group_rows = []
            self.groups.append((self._card_rank, self._group_rows))
            self._group_depth = depth
        elif tag == "div" and "learning-signal-route-row" in classes:
            if self._group_rows is None:
                raise AssertionError("learning route row is outside a route group")
            self._row = {"label": [], "facts": [], "paragraph": None}
            self._row_depth = depth
        elif self._row is not None and tag == "strong":
            self._strong_depth = depth
        elif self._row is not None and tag == "p":
            self._row["paragraph"] = []
            self._paragraph_depth = depth
        elif (
            self._row is not None
            and self._paragraph_depth is not None
            and tag == "span"
            and "label" in classes
        ):
            self._label_depth = depth

    def handle_data(self, data: str) -> None:
        if self._row is None:
            return
        if self._strong_depth is not None:
            label = self._row["label"]
            assert isinstance(label, list)
            label.append(data)
        elif self._paragraph_depth is not None and self._label_depth is None:
            paragraph = self._row["paragraph"]
            assert isinstance(paragraph, list)
            paragraph.append(data)

    def handle_endtag(self, tag: str) -> None:
        depth = len(self._stack)
        if tag == "span" and self._label_depth == depth:
            self._label_depth = None
        elif tag == "strong" and self._strong_depth == depth:
            self._strong_depth = None
        elif tag == "p" and self._paragraph_depth == depth:
            assert self._row is not None
            facts = self._row["facts"]
            assert isinstance(facts, list)
            facts.append(self._text(self._row["paragraph"]))
            self._row["paragraph"] = None
            self._paragraph_depth = None
        elif tag == "div" and self._row_depth == depth:
            assert self._row is not None and self._group_rows is not None
            facts = self._row["facts"]
            assert isinstance(facts, list)
            if len(facts) != 3:
                raise AssertionError("learning route row must contain three public facts")
            self._group_rows.append((self._text(self._row["label"]), *facts))
            self._row = None
            self._row_depth = None
        elif tag == "div" and self._group_depth == depth:
            self._group_rows = None
            self._group_depth = None
        elif tag == "article" and self._card_depth == depth:
            self._card_rank = None
            self._card_depth = None
        if tag not in self._VOID_TAGS:
            if not self._stack or self._stack[-1] != tag:
                raise AssertionError(f"unexpected closing tag: {tag}")
            self._stack.pop()


class ExecutiveCareerDossierV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.validator = load_validator()

    def test_v2_requires_the_exact_canonical_section_ledger(self) -> None:
        dossier = make_v2_dossier()
        self.assertEqual(self.validator.validate_dossier(dossier), [])
        self.assertEqual(tuple(row["section"] for row in dossier["section_coverage"]), CANONICAL_PROFILE_SECTIONS)
        for mutation in (
            dossier["section_coverage"][:-1],
            list(reversed(dossier["section_coverage"])),
            dossier["section_coverage"] + [copy.deepcopy(dossier["section_coverage"][0])],
        ):
            invalid = copy.deepcopy(dossier)
            invalid["section_coverage"] = mutation
            self.assertIn(
                "section_coverage must contain every canonical section exactly once in canonical order",
                self.validator.validate_dossier(invalid),
            )

    def test_unavailable_sections_require_current_session_read_only_decisions(self) -> None:
        dossier = make_v2_dossier()
        dossier["section_coverage"][10] = {
            "section": "featured", "availability": "unavailable", "evidence_state": "unknown",
            "reason": "authorization_required", "inspection_request": {
                "access_type": "read_only_visible_section_inspection", "decision": "pending_response",
                "scope": "current_session_only", "carry_forward": False,
            },
        }
        self.assertEqual(self.validator.validate_dossier(dossier), [])
        missing = copy.deepcopy(dossier)
        del missing["section_coverage"][10]["inspection_request"]
        self.assertIn("section_coverage[10] unavailable section requires inspection_request", self.validator.validate_dossier(missing))
        forbidden = make_v2_dossier()
        forbidden["section_coverage"][0]["inspection_request"] = copy.deepcopy(dossier["section_coverage"][10]["inspection_request"])
        self.assertIn("section_coverage[0] inspected section forbids inspection_request", self.validator.validate_dossier(forbidden))

    def test_ledger_state_matrix_is_closed_and_status_only(self) -> None:
        dossier = make_v2_dossier()
        cases = (
            ("inspected_present", "verified", "inspected_content_available", None),
            ("inspected_absent", "verified", "inspected_section_absent", None),
            ("candidate_supplied", "candidate_reported", "candidate_material_supplied", None),
            ("unavailable", "unknown", "authorization_required", "pending_response"),
            ("unavailable", "unknown", "inspection_declined", "declined_for_session"),
            ("unavailable", "unknown", "authorized_inspection_failed", "authorized_inspection_failed"),
        )
        for availability, state, reason, decision in cases:
            with self.subTest(availability=availability, decision=decision):
                invalid = copy.deepcopy(dossier)
                row = invalid["section_coverage"][10]
                row.update({"availability": availability, "evidence_state": state, "reason": reason})
                if decision is None:
                    row.pop("inspection_request", None)
                else:
                    row["inspection_request"]["decision"] = decision
                if availability == "candidate_supplied":
                    invalid["evidence"].append({
                        "id": "E-999", "state": "candidate_reported", "section": "proof",
                        "source_kind": "candidate_statement", "paraphrase": "Candidate material was supplied.",
                        "capture_ref": None, "profile_section": "featured",
                    })
                if availability == "inspected_present":
                    invalid["evidence"].append({
                        "id": "E-998", "state": "verified", "section": "proof",
                        "source_kind": "authorized_visible", "paraphrase": "Visible section was inspected.",
                        "capture_ref": "CAP-001", "profile_section": "featured",
                    })
                self.assertEqual(self.validator.validate_dossier(invalid), [])
        for mutation in (
            {"decision": "authorized_for_session"},
            {"carry_forward": True},
            {"access_type": "write_visible_section_inspection"},
            {"scope": "future_sessions"},
        ):
            invalid = make_v2_dossier()
            invalid["section_coverage"][10]["inspection_request"].update(mutation)
            self.assertTrue(self.validator.validate_dossier(invalid))

    def test_legacy_scope_is_a_constraint_not_the_complete_ledger(self) -> None:
        dossier = make_v2_dossier()
        self.assertEqual(self.validator.validate_dossier(dossier), [])
        contradictory = copy.deepcopy(dossier)
        contradictory["section_coverage"][4].update({
            "availability": "unavailable", "evidence_state": "unknown", "reason": "authorization_required",
            "inspection_request": {"access_type": "read_only_visible_section_inspection", "decision": "pending_response", "scope": "current_session_only", "carry_forward": False},
        })
        self.assertIn("section_coverage[4] contradicts evidence_scope.inspected_sections", self.validator.validate_dossier(contradictory))
        unavailable = copy.deepcopy(dossier)
        unavailable["evidence_scope"]["unavailable_sections"] = ["featured"]
        unavailable["section_coverage"][10] = {"section": "featured", "availability": "inspected_absent", "evidence_state": "verified", "reason": "inspected_section_absent"}
        self.assertIn("section_coverage[10] contradicts evidence_scope.unavailable_sections", self.validator.validate_dossier(unavailable))

    def test_present_or_candidate_rows_require_section_evidence_without_score_mutation(self) -> None:
        dossier = make_v2_dossier()
        before = copy.deepcopy(dossier)
        self.assertEqual(self.validator.validate_dossier(dossier), [])
        self.assertEqual(dossier, before)
        missing = copy.deepcopy(dossier)
        missing["evidence"][0]["profile_section"] = None
        self.assertIn("section_coverage[4] requires evidence for its profile_section", self.validator.validate_dossier(missing))
        pending = copy.deepcopy(dossier)
        pending["section_coverage"][10]["inspection_request"]["decision"] = "pending_response"
        declined = copy.deepcopy(pending)
        declined["section_coverage"][10].update({"reason": "inspection_declined"})
        declined["section_coverage"][10]["inspection_request"]["decision"] = "declined_for_session"
        self.assertEqual(pending["coverage"], declined["coverage"])
        self.assertEqual(self.validator.validate_dossier(pending), [])
        self.assertEqual(self.validator.validate_dossier(declined), [])

    def test_contextual_priorities_bind_same_section_evidence(self) -> None:
        dossier = make_v2_dossier()
        self.assertEqual(self.validator.validate_dossier(dossier), [])
        dossier["priorities"][0]["evidence_ids"] = ["E-002"]
        self.assertIn("priorities[0].evidence_ids must bind to the target section", self.validator.validate_dossier(dossier))

    def test_priority_contract_is_closed_and_safe(self) -> None:
        for field in ("target_section", "coach_observation", "why_it_matters", "coach_prompt", "client_template", "privacy_boundary"):
            invalid = make_v2_dossier()
            del invalid["priorities"][0][field]
            self.assertTrue(self.validator.validate_dossier(invalid), field)
        for field_keys in ([], ["context", "action", "result", "scope", "metric", "target_role"], ["context", "context"]):
            invalid = make_v2_dossier()
            invalid["priorities"][0]["client_template"]["field_keys"] = field_keys
            self.assertTrue(self.validator.validate_dossier(invalid), field_keys)
        invalid = make_v2_dossier()
        invalid["priorities"][0]["client_template"]["template_id"] = "unknown_template"
        self.assertTrue(self.validator.validate_dossier(invalid))

    def test_new_coaching_prose_reuses_v1_action_employment_analytics_and_market_guards(self) -> None:
        for field, value, diagnostic in UNSAFE_COACHING_PROSE:
            with self.subTest(field=field, diagnostic=diagnostic):
                dossier = make_v2_dossier()
                dossier["priorities"][0][field] = value
                errors = self.validator.validate_dossier(dossier)
                self.assertIn(f"priorities[0].{field} {diagnostic}", errors)
                self.assertNotIn(value, "\n".join(errors))

        for field, value in SAFE_COACHING_PROSE:
            with self.subTest(field=field):
                dossier = make_v2_dossier()
                dossier["priorities"][0][field] = value
                self.assertEqual(self.validator.validate_dossier(dossier), [])

    def test_v2_dated_market_coaching_prose_and_projection_use_v1_hire_and_hiring_semantics(self) -> None:
        source = load_v1_fixture("scenario-market-en.json")
        dossier = make_v2_dossier("en")
        market_evidence = copy.deepcopy(source["evidence"][-1])
        market_evidence["profile_section"] = None
        dossier["evidence"].append(market_evidence)
        dossier["market_context"] = copy.deepcopy(source["market_context"])
        self.assertEqual(self.validator.project_v2_to_v1(dossier), source)

        for text in (
            "Employers actively hire SREs.",
            "Employers are actively hiring SREs.",
        ):
            with self.subTest(text=text, surface="v2 coaching prose"):
                unlinked = copy.deepcopy(dossier)
                unlinked["priorities"][0]["why_it_matters"] = text
                self.assertIn(
                    "priorities[0].why_it_matters market claims require local dated market evidence",
                    self.validator.validate_dossier(unlinked),
                )

            with self.subTest(text=text, surface="v1 projection", evidence="unlinked"):
                projected = self.validator.project_v2_to_v1(dossier)
                projected["priorities"][0]["why_now"] = text
                self.assertEqual(self.validator._v1.validate_dossier(projected), [])

        safe = copy.deepcopy(dossier)
        safe["priorities"][0]["why_it_matters"] = (
            "Technical controls remain available for private review."
        )
        self.assertEqual(self.validator.validate_dossier(safe), [])

    def test_v2_schema_checker_runs_before_semantic_validation(self) -> None:
        dossier = make_v2_dossier()
        dossier["section_coverage"][0]["availability"] = "unsupported"
        errors = self.validator.validate_dossier(dossier)
        self.assertIn("v2 schema validation failed", errors)
        self.assertNotIn("unsupported", "\n".join(errors))

    def test_v2_direct_validation_is_total_for_self_and_nested_cycles(self) -> None:
        self_cycle: dict[str, object] = {}
        self_cycle["opaque_self_cycle"] = self_cycle
        nested_cycle: dict[str, object] = {"branch": []}
        nested_cycle["branch"].append({"opaque_nested_cycle": nested_cycle})
        for value in (self_cycle, nested_cycle):
            with self.subTest(kind="self" if value is self_cycle else "nested"):
                errors = self.validator.validate_dossier(value)
                self.assertEqual(errors, ["v2 dossier contains cyclic data", "v2 schema validation failed"])
                self.assertNotIn("opaque", "\n".join(errors))

    def test_v2_external_action_guard_applies_to_every_coaching_field(self) -> None:
        for field in ("coach_observation", "why_it_matters", "coach_prompt"):
            for unsafe in (
                "Consider publishing this on LinkedIn.",
                "The next step is sending the message to the recruiter.",
                "Conectar contexto y publicar esto en LinkedIn.",
            ):
                with self.subTest(field=field, unsafe=unsafe):
                    dossier = make_v2_dossier()
                    dossier["priorities"][0][field] = unsafe
                    errors = self.validator.validate_dossier(dossier)
                    self.assertIn(f"priorities[0].{field} must remain a private review action", errors)
                    self.assertNotIn(unsafe, "\n".join(errors))

    def test_exact_internal_writing_fixture_phrase_remains_valid(self) -> None:
        dossier = make_v2_dossier()
        dossier["priorities"][0]["coach_observation"] = (
            "La apertura describe responsabilidades sin conectar todavía contexto y resultado."
        )
        self.assertEqual(self.validator.validate_dossier(dossier), [])

    def test_projection_deep_copy_isolation_survives_nested_mutation(self) -> None:
        source = make_v2_dossier()
        original = copy.deepcopy(source)
        projected = self.validator.project_v2_to_v1(source)
        projected["evidence"][0]["paraphrase"] = "changed"
        projected["priorities"][0]["evidence_ids"].append("E-999")
        self.assertEqual(source, original)

    def test_every_locale_section_question_and_declined_failed_state_is_explicit(self) -> None:
        renderer = load_renderer()
        for locale, labels in renderer.SECTION_LABELS.items():
            for section, label in labels.items():
                with self.subTest(locale=locale, section=section):
                    question = renderer.AUTHORIZATION_QUESTIONS[locale][section]
                    self.assertIn(label, question)
                    self.assertIn("sesión" if locale == "es" else "session", question)
        dossier = make_v2_dossier()
        for row in dossier["section_coverage"]:
            request = row.get("inspection_request")
            if isinstance(request, dict):
                request["decision"] = "declined_for_session"
                row["reason"] = "inspection_declined"
        dossier["section_coverage"][10]["inspection_request"]["decision"] = "authorized_inspection_failed"
        dossier["section_coverage"][10]["reason"] = "authorized_inspection_failed"
        self.assertIsNone(self.validator.select_pending_inspection_section(dossier))

    def test_every_ledger_and_request_boundary_rejects_session_or_positive_authorization_fields(self) -> None:
        mutations = (
            ("section_coverage", 10, "session_id"),
            ("section_coverage", 10, "authorized_for_session"),
            ("inspection_request", 10, "session_id"),
            ("inspection_request", 10, "authorization_granted"),
        )
        for boundary, index, key in mutations:
            with self.subTest(boundary=boundary, key=key):
                dossier = make_v2_dossier()
                target = dossier["section_coverage"][index]
                if boundary == "inspection_request":
                    target = target["inspection_request"]
                target[key] = True
                errors = self.validator.validate_dossier(dossier)
                self.assertTrue(errors)
                self.assertNotIn(key, "\n".join(errors))

    def test_every_evidence_record_requires_a_canonical_or_null_profile_section(self) -> None:
        for label, replacement in (("missing", None), ("unknown", "unknown_section"), ("number", 3), ("array", [])):
            with self.subTest(replacement=label):
                dossier = make_v2_dossier()
                if label == "missing":
                    del dossier["evidence"][4]["profile_section"]
                else:
                    dossier["evidence"][4]["profile_section"] = replacement
                self.assertTrue(self.validator.validate_dossier(dossier))

    def test_selector_falls_back_to_canonical_pending_section_not_targeted_by_a_priority(self) -> None:
        dossier = make_v2_dossier()
        for row in dossier["section_coverage"]:
            if isinstance(row.get("inspection_request"), dict):
                row["inspection_request"]["decision"] = "declined_for_session"
                row["reason"] = "inspection_declined"
        dossier["section_coverage"][10]["inspection_request"]["decision"] = "pending_response"
        dossier["section_coverage"][10]["reason"] = "authorization_required"
        self.assertEqual(self.validator.select_pending_inspection_section(dossier), "featured")

    def test_v2_diagnostics_do_not_echo_new_prose_values(self) -> None:
        sentinels = (
            "/private/path/profile.json", "https://www.linkedin.com/in/example",
            "person@example.test", "unsafe\x1b[31m", "unsafe\u202evalue",
        )
        for field in ("coach_observation", "why_it_matters", "coach_prompt", "privacy_boundary"):
            for sentinel in sentinels:
                with self.subTest(field=field, sentinel=repr(sentinel)):
                    dossier = make_v2_dossier()
                    dossier["priorities"][0][field] = sentinel
                    errors = self.validator.validate_dossier(dossier)
                    self.assertTrue(errors)
                    self.assertNotIn(sentinel, "\n".join(errors))

    def test_selector_returns_one_pending_priority_then_ledger_section(self) -> None:
        dossier = make_v2_dossier()
        dossier["section_coverage"][4].update({
            "availability": "unavailable", "evidence_state": "unknown", "reason": "authorization_required",
            "inspection_request": {"access_type": "read_only_visible_section_inspection", "decision": "pending_response", "scope": "current_session_only", "carry_forward": False},
        })
        self.assertEqual(self.validator.select_pending_inspection_section(dossier), "headline")
        dossier["section_coverage"][4].update({"availability": "inspected_present", "evidence_state": "verified", "reason": "inspected_content_available"})
        dossier["section_coverage"][7].update({
            "availability": "unavailable", "evidence_state": "unknown", "reason": "authorization_required",
            "inspection_request": {"access_type": "read_only_visible_section_inspection", "decision": "pending_response", "scope": "current_session_only", "carry_forward": False},
        })
        self.assertEqual(self.validator.select_pending_inspection_section(dossier), "about")
        for row in dossier["section_coverage"]:
            request = row.get("inspection_request")
            if isinstance(request, dict):
                request["decision"] = "declined_for_session"
                row["reason"] = "inspection_declined"
        self.assertIsNone(self.validator.select_pending_inspection_section(dossier))


class ExecutiveCareerDossierV2RendererTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.renderer = load_renderer()
        cls.validator = load_validator()

    def v1_render_sources(self) -> dict[str, object]:
        dossier, market, research, alignment, learning = learning_case(
            "complete-five-es.json", "scenario-a-es.json", count=5
        )
        return {
            "dossier": dossier,
            "market_dossier": market,
            "market_research": research,
            "market_alignment": alignment,
            "learning_decision": learning,
        }

    def v2_render_sources(self, state: str = "complete") -> dict[str, object]:
        dossier, market, research, learning, provider = semantic_v2_case(state)
        return {
            "dossier": dossier,
            "market_dossier": market,
            "market_research": research,
            "market_alignment": None,
            "learning_decision": learning,
            "provider_research": provider,
        }

    def test_v3_weekly_card_is_ordered_named_and_single_action(self):
        rendered = self.renderer.render_dossier_html(**semantic_v3_case("proof", "es"))
        decide = decide_now_region(rendered)[2]
        self.assertLess(
            decide.index('class="card span-12 decide-now-card decide-now-market"'),
            decide.index('class="card span-12 weekly-decision"'),
        )
        self.assertLess(
            rendered.index('class="card span-12 weekly-decision"'),
            rendered.index('class="section-block learning-decision"'),
        )
        self.assertEqual(1, decide.count('class="card span-12 weekly-decision"'))
        self.assertEqual(1, decide.count('class="weekly-decision-action"'))
        self.assertEqual(1, decide.count("weekly-decision-secondary"))
        self.assertIn("Decisión de esta semana", decide)
        audit = DossierDOMAudit()
        audit.feed(rendered)
        self.assertEqual(len(audit.ids), len(set(audit.ids)))
        self.assertFalse(set(audit.references) - set(audit.ids))

    def test_v3_provider_choice_list_is_complete_non_ranked_and_public(self):
        rendered = self.renderer.render_dossier_html(
            **semantic_v3_case("provider_choice", "en")
        )
        region = weekly_decision_region(rendered)
        self.assertIn("L1", region)
        self.assertIn("Terraform course", region)
        self.assertIn("HashiCorp", region)
        self.assertIn("not ranked", region)
        for forbidden in ("LP-001", "LP-003", "https://", "snap-", "V-003"):
            self.assertNotIn(forbidden, region)
        self.assertNotIn("<button", region)
        self.assertNotIn("<form", region)
        self.assertNotIn("<a ", region)

        sources, eligibility = eligibility_v3_case("provider_choice", "en")
        eligibility = copy.deepcopy(eligibility)
        eligibility["eligible_provider_choices"].extend(
            [
                {
                    "public_provider_ordinal": "L2",
                    "option_name": "Kubernetes lab",
                    "provider_or_owner": "CNCF",
                },
                {
                    "public_provider_ordinal": "L3",
                    "option_name": "Terraform proof lab",
                    "provider_or_owner": "candidate-owned",
                },
            ]
        )
        complete_region = self.renderer._render_weekly_decision_card(
            eligibility, sources["market_dossier"], "en"
        )
        self.assertEqual(3, complete_region.count('class="weekly-decision-choice"'))
        self.assertLess(complete_region.index("L1"), complete_region.index("L2"))
        self.assertLess(complete_region.index("L2"), complete_region.index("L3"))
        for public_value in (
            "Terraform course",
            "HashiCorp",
            "Kubernetes lab",
            "CNCF",
            "Terraform proof lab",
            "candidate-owned",
        ):
            self.assertIn(public_value, complete_region)

    def test_v3_gap_unknown_lists_the_closed_relation_choices_only(self) -> None:
        """Break caught: omitting, reordering, or exposing a raw relation choice."""
        expected = {
            "es": (
                "Elige una relación",
                (
                    "Ya puedo respaldarla con evidencia",
                    "Me falta evidencia práctica",
                    "Me falta conocimiento",
                    "Me falta práctica",
                    "Me falta experiencia profesional o de producción",
                    "Sólo me falta la terminología",
                    "Todavía no puedo evaluarlo",
                ),
            ),
            "en": (
                "Choose one relation",
                (
                    "I can already support it with evidence",
                    "I lack practical proof",
                    "I lack knowledge",
                    "I lack practice",
                    "I lack professional or production experience",
                    "I only lack the terminology",
                    "I cannot assess it yet",
                ),
            ),
        }
        raw_relations = (
            "supported",
            "proof_gap",
            "knowledge_gap",
            "practice_gap",
            "professional_experience_gap",
            "terminology_gap",
            "unknown",
        )
        marker = 'class="weekly-decision-relations"'
        for locale, (heading, labels) in expected.items():
            with self.subTest(locale=locale, condition="gap_unknown"):
                sources, eligibility = eligibility_v3_case("gap_unknown", locale)
                region = self.renderer._render_weekly_decision_card(
                    eligibility, sources["market_dossier"], locale
                )
                self.assertIn(
                    '<section class="weekly-decision-relations" '
                    'aria-labelledby="weekly-decision-relations-title">',
                    region,
                )
                self.assertIn(
                    f'<h4 id="weekly-decision-relations-title">{heading}</h4>',
                    region,
                )
                self.assertIn("<ul>", region)
                self.assertIn("</ul>", region)
                self.assertEqual(7, region.count('class="weekly-decision-relation"'))
                self.assertLess(
                    region.index('id="weekly-decision-evidence"'),
                    region.index(marker),
                )
                self.assertLess(
                    region.index(marker),
                    region.index('class="weekly-decision-action"'),
                )
                relation_group = region[
                    region.index(marker) : region.index(
                        "</section>", region.index(marker)
                    )
                ]
                self.assertEqual(
                    list(labels),
                    [
                        html.unescape(text)
                        for text in re.findall(
                            r'<li class="weekly-decision-relation">(.*?)</li>',
                            relation_group,
                            re.DOTALL,
                        )
                    ],
                )
                self.assertEqual(1, region.count('class="weekly-decision-action"'))
                self.assertIn(
                    'aria-describedby="weekly-decision-evidence '
                    'weekly-decision-boundary"',
                    region,
                )
                for forbidden in raw_relations:
                    self.assertNotIn(forbidden, relation_group)
                private_values = (
                    str(eligibility["selected_vacancy_id"]),
                    str(eligibility["source_alignment_snapshot"]),
                    str(sources["research"]["vacancies"][1]["source_url"]),
                    str(
                        sources["research"]["vacancies"][1]["requirements"][0][
                            "source_paraphrase"
                        ]
                    ),
                )
                for private_value in private_values:
                    self.assertNotIn(private_value, region)
                for forbidden in (
                    "<a ",
                    "<button",
                    "<form",
                    "<input",
                    "<select",
                    "<textarea",
                ):
                    self.assertNotIn(forbidden, region)

            for condition in ELIGIBILITY_V3_CASES:
                if condition == "gap_unknown":
                    continue
                with self.subTest(locale=locale, condition=condition):
                    sources, eligibility = eligibility_v3_case(condition, locale)
                    region = self.renderer._render_weekly_decision_card(
                        eligibility, sources["market_dossier"], locale
                    )
                    self.assertNotIn(marker, region)
                    if condition == "selection_required":
                        self.assertIn(
                            'aria-describedby="weekly-decision-evidence '
                            'weekly-decision-selection-help '
                            'weekly-decision-boundary"',
                            region,
                        )
                        self.assertEqual(
                            1, region.count('href="#market-vacancy-key-title"')
                        )
                        self.assertEqual(
                            1, region.count('href="#market-matrix-title"')
                        )
                        self.assertLess(
                            region.index('href="#market-vacancy-key-title"'),
                            region.index('href="#market-matrix-title"'),
                        )

    def test_v3_every_state_has_exact_es_en_copy_and_one_primary_action(self) -> None:
        for locale in ("es", "en"):
            for condition in ELIGIBILITY_V3_CASES:
                with self.subTest(locale=locale, condition=condition):
                    sources, eligibility = eligibility_v3_case(condition, locale)
                    region = self.renderer._render_weekly_decision_card(
                        eligibility, sources["market_dossier"], locale
                    )
                    if condition == "unavailable":
                        self.assertEqual("", region)
                        continue
                    self.assertEqual(1, region.count('class="weekly-decision-action"'))
                    self.assertIn(WEEKLY_STATE_COPY[locale][condition], html.unescape(region))
                    action = eligibility["recommended_next_action"]
                    expected_copy = WEEKLY_ACTION_COPY[locale][action]
                    for expected in expected_copy:
                        self.assertIn(expected, html.unescape(region))
                    self.assertEqual(
                        1,
                        region.count(
                            "no ejecuta ninguna acción externa"
                            if locale == "es"
                            else "performs no external action"
                        ),
                    )

    def test_v3_selection_required_links_one_localized_help_to_market_choices(
        self,
    ) -> None:
        class SelectionHelpLinkParser(HTMLParser):
            def __init__(self) -> None:
                super().__init__()
                self.links: list[tuple[str, str]] = []
                self.text: list[str] = []
                self._in_help = False
                self._href: str | None = None
                self._text: list[str] = []

            def handle_starttag(
                self, tag: str, attrs: list[tuple[str, str | None]]
            ) -> None:
                values = dict(attrs)
                if tag == "p" and values.get("id") == "weekly-decision-selection-help":
                    self._in_help = True
                elif self._in_help and tag == "a":
                    href = values.get("href")
                    if href is None:
                        raise AssertionError("selection help link must have an href")
                    self._href = href
                    self._text = []

            def handle_data(self, data: str) -> None:
                if self._in_help:
                    self.text.append(data)
                if self._href is not None:
                    self._text.append(data)

            def handle_endtag(self, tag: str) -> None:
                if tag == "a" and self._href is not None:
                    self.links.append(("".join(self._text).strip(), self._href))
                    self._href = None
                    self._text = []
                elif tag == "p" and self._in_help:
                    self._in_help = False

        expected_help = {
            "es": (
                "Formato de selección: Vn + señal.",
                "Revisa la clave de vacantes y la matriz de señales.",
            ),
            "en": (
                "Selection format: Vn + signal.",
                "Review the vacancy key and signal matrix.",
            ),
        }
        expected_links = {
            "es": (
                ("clave de vacantes", "#market-vacancy-key-title"),
                ("matriz de señales", "#market-matrix-title"),
            ),
            "en": (
                ("vacancy key", "#market-vacancy-key-title"),
                ("signal matrix", "#market-matrix-title"),
            ),
        }
        for locale in ("es", "en"):
            for condition in ELIGIBILITY_V3_CASES:
                with self.subTest(locale=locale, condition=condition):
                    rendered = self.renderer.render_dossier_html(
                        **semantic_v3_case(condition, locale)
                    )
                    marker = 'id="weekly-decision-selection-help"'
                    if condition != "selection_required":
                        self.assertNotIn(marker, rendered)
                        continue

                    region = weekly_decision_region(rendered)
                    links = SelectionHelpLinkParser()
                    links.feed(region)
                    help_text = " ".join("".join(links.text).split())
                    for expected in expected_help[locale]:
                        self.assertIn(expected, help_text)
                    self.assertEqual(expected_links[locale], tuple(links.links))
                    self.assertIn(
                        'aria-describedby="weekly-decision-evidence '
                        'weekly-decision-selection-help weekly-decision-boundary"',
                        region,
                    )
                    self.assertEqual(1, region.count(marker))
                    self.assertEqual(
                        1,
                        region.count('href="#market-vacancy-key-title"'),
                    )
                    self.assertEqual(
                        1,
                        region.count('href="#market-matrix-title"'),
                    )
                    self.assertEqual(
                        1,
                        rendered.count('id="market-vacancy-key-title"'),
                    )
                    self.assertEqual(
                        1,
                        rendered.count('id="market-matrix-title"'),
                    )
                    self.assertNotIn('id="weekly-decision-vacancy"', region)
                    self.assertNotIn('class="weekly-decision-signal"', region)
                    self.assertNotIn('class="weekly-decision-recurrence"', region)
                    self.assertNotIn("<button", region)
                    self.assertNotIn("<form", region)
                    self.assertNotIn("https://", region)
                    self.assertEqual(1, region.count('class="weekly-decision-action"'))

                    audit = DossierDOMAudit()
                    audit.feed(rendered)
                    self.assertEqual(len(audit.ids), len(set(audit.ids)))
                    self.assertFalse(set(audit.references) - set(audit.ids))

    def test_v3_unavailable_preserves_one_existing_safe_step_only(self) -> None:
        for locale in ("es", "en"):
            with self.subTest(locale=locale):
                rendered = self.renderer.render_dossier_html(
                    **semantic_v3_case("unavailable", locale)
                )
                decide = decide_now_region(rendered)[2]
                self.assertNotIn('class="card span-12 weekly-decision"', rendered)
                self.assertNotIn('class="section-block learning-decision"', rendered)
                self.assertEqual(1, decide.count(self.renderer.COPY[locale]["decide_no_market"]))
                self.assertEqual(
                    1,
                    decide.count(
                        'class="card span-4 decide-now-card decide-now-authorization"'
                    ),
                )
                self.assertNotIn("weekly-decision-secondary", decide)

    def test_v3_learning_navigation_exists_only_when_the_detailed_panel_exists(
        self,
    ) -> None:
        zero_decision_conditions = (
            "unavailable",
            "selection_required",
            "insufficient_recurrence",
            "gap_unknown",
            "supported",
            "provider_choice",
            "provider_evidence",
            "experience",
        )
        eligible_conditions = ("proof", "practice", "terminology", "knowledge")
        for locale in ("es", "en"):
            for condition in zero_decision_conditions + eligible_conditions:
                with self.subTest(locale=locale, condition=condition):
                    arguments = semantic_v3_case(condition, locale)
                    expected_count = 1 if condition in eligible_conditions else 0
                    self.assertEqual(
                        expected_count,
                        len(arguments["learning_decision"]["decisions"]),
                    )
                    rendered = self.renderer.render_dossier_html(**arguments)
                    decide = decide_now_region(rendered)[2]
                    self.assertEqual(
                        expected_count,
                        decide.count('href="#learning-decision-title"'),
                    )
                    self.assertEqual(
                        expected_count,
                        rendered.count('id="learning-decision-title"'),
                    )
                    if condition == "unavailable":
                        self.assertNotIn(
                            self.renderer.COPY[locale]["learning_title"], decide
                        )

    def test_v3_public_vacancy_ordinal_title_and_employer_are_visible_and_named(self) -> None:
        rendered = self.renderer.render_dossier_html(**semantic_v3_case("proof", "es"))
        region = weekly_decision_region(rendered)
        self.assertIn("V2", visible_text(region))
        self.assertIn("Fixture DevOps Role C", visible_text(region))
        self.assertIn("Fixture Employer C", visible_text(region))
        self.assertRegex(
            region,
            r'aria-labelledby="weekly-decision-title weekly-decision-vacancy"',
        )
        self.assertRegex(
            region,
            r'aria-describedby="weekly-decision-evidence weekly-decision-boundary"',
        )
        self.assertRegex(
            region,
            r'id="weekly-decision-vacancy"[^>]*>.*V2.*Fixture DevOps Role C.*Fixture Employer C',
        )

    def test_v3_weekly_card_escapes_every_public_projection_field(self) -> None:
        sources, eligibility = eligibility_v3_case("proof", "en")
        market = copy.deepcopy(sources["market_dossier"])
        eligibility = copy.deepcopy(eligibility)
        eligibility["public_vacancy_ordinal"] = "V1"
        eligibility["selected_signal"] = '<script data-private="x">signal</script>'
        eligibility["private_deliverable"] = '<img src=x onerror="bad">'
        eligibility["done_when"] = 'done & <strong>unsafe</strong>'
        market["vacancies"][0]["title"] = '<svg onload="bad">Title</svg>'
        market["vacancies"][0]["employer"] = 'Employer & "Owner"'
        region = self.renderer._render_weekly_decision_card(
            eligibility, market, "en"
        )
        for raw in ("<script", "</script>", "<img", "<strong>unsafe", "<svg"):
            self.assertNotIn(raw, region)
        for escaped in (
            "&lt;Script",
            "&lt;img",
            "done &amp; &lt;strong&gt;unsafe&lt;/strong&gt;",
            "&lt;svg",
            "Employer &amp; &quot;Owner&quot;",
        ):
            self.assertIn(escaped, region)

    def test_v3_learning_panel_closes_practice_and_unknown_labels_in_es_and_en(self) -> None:
        base_row = {
            "decision_rank": 1,
            "option_name": "Bounded lab",
            "gap_type": "practice",
            "option_type": "lab",
            "provider_or_owner": "candidate_owned",
            "decision_basis": "Bounded basis.",
            "signal_routes": [{
                "term_label": "Terraform",
                "support_state": "unknown",
                "vacancy_ordinals": ["V1", "V2"],
                "recurrence": "2/4",
            }],
            "cost_time_band": "Not evaluated.",
            "expected_signal_boundary": "Bounded signal.",
            "portfolio_or_no_learning_alternative": "Private alternative.",
            "overbuying_risk": "Bounded risk.",
            "decision": "do_now",
            "next_action_gate": "Separate authorization required.",
        }
        for locale, gap_label, support_label in (
            ("es", "Práctica", "No verificado"),
            ("en", "Practice", "Not verified"),
        ):
            with self.subTest(locale=locale):
                rendered = self.renderer._render_learning_decision_v3(
                    {"vacancies": [{}, {}]},
                    {"schema_version": "career-learning-decision-v3", "decisions": [base_row]},
                    locale,
                )
                self.assertIn(gap_label, rendered)
                self.assertIn(support_label, rendered)
                self.assertNotIn(">practice<", rendered)
                self.assertNotIn(">unknown<", rendered)
                self.assertEqual(
                    "",
                    self.renderer._render_learning_decision_v3(
                        {"vacancies": [{}, {}]},
                        {"schema_version": "career-learning-decision-v3", "decisions": []},
                        locale,
                    ),
                )

    def test_v3_all_partial_masks_and_crossed_inputs_fail_before_asset_reads(self) -> None:
        proof = semantic_v3_case("proof", "es")
        fields = (
            "gap_response",
            "gap_assessment",
            "next_action_eligibility",
            "learning_decision",
        )
        base = {
            key: proof[key]
            for key in (
                "dossier",
                "market_dossier",
                "market_research",
                "market_alignment",
                "provider_research",
            )
        }
        with mock.patch.object(
            self.renderer.BASE.ASSET_LOADER,
            "read_private_asset",
            side_effect=AssertionError("asset read before v3 preflight"),
        ) as asset_read:
            for mask in range(1, (1 << len(fields)) - 1):
                arguments = dict(base)
                arguments.update(
                    {
                        field: proof[field] if mask & (1 << index) else None
                        for index, field in enumerate(fields)
                    }
                )
                with self.subTest(mask=mask), self.assertRaises(
                    self.renderer.DossierValidationError
                ) as raised:
                    self.renderer.render_dossier_html(**arguments)
                self.assertEqual(
                    ("market composition inputs must be supplied together",),
                    raised.exception.errors,
                )
            crossed = semantic_v3_case("selection_required", "es")
            for field in fields:
                arguments = dict(proof)
                arguments[field] = crossed[field]
                with self.subTest(crossed=field), self.assertRaises(
                    self.renderer.DossierValidationError
                ):
                    self.renderer.render_dossier_html(**arguments)
            asset_read.assert_not_called()

    def test_lone_v3_learning_uses_one_snapshot_before_schema_access_and_no_echo(self) -> None:
        sentinel = "lone-v3-learning-private-sentinel"
        hostile = OnePassMapping(
            {"schema_version": "career-learning-decision-v3", sentinel: "private"},
            sentinel,
        )
        with mock.patch.object(
            self.renderer.BASE.ASSET_LOADER,
            "read_private_asset",
            side_effect=AssertionError("asset read before v3 preflight"),
        ) as asset_read, self.assertRaises(
            self.renderer.DossierValidationError
        ) as raised:
            self.renderer.render_dossier_html(
                make_v2_dossier(), learning_decision=hostile
            )
        self.assertEqual(1, hostile.items_calls)
        self.assertEqual(
            ("market composition inputs must be supplied together",),
            raised.exception.errors,
        )
        self.assertNotIn(sentinel, str(raised.exception))
        asset_read.assert_not_called()

    def test_v3_group_is_captured_once_without_deepcopy_or_original_rereads(self) -> None:
        arguments = semantic_v3_case("proof", "es")
        sentinel = "v3-original-reread-sentinel"
        wrapped: list[OnePassMapping] = []
        for field, value in list(arguments.items()):
            if isinstance(value, Mapping):
                current = OnePassMapping(value, sentinel)
                wrapped.append(current)
                arguments[field] = current
        with mock.patch.object(
            self.renderer,
            "bounded_plain_snapshot",
            wraps=self.renderer.bounded_plain_snapshot,
        ) as snapshot:
            rendered = self.renderer.render_dossier_html(**arguments)
        self.assertIn('class="card span-12 weekly-decision"', rendered)
        self.assertEqual(1, snapshot.call_count)
        self.assertTrue(wrapped)
        self.assertTrue(all(value.items_calls == 1 for value in wrapped))
        self.assertNotIn(sentinel, rendered)

    def test_historical_v1_v2_bytes_and_inline_css_exclude_v3_selectors(self) -> None:
        renders = {
            "v1": self.renderer.render_dossier_html(**self.v1_render_sources()),
            "v2": self.renderer.render_dossier_html(**self.v2_render_sources()),
        }
        for generation, rendered in renders.items():
            with self.subTest(generation=generation):
                expected_size, expected_digest = HISTORICAL_COMPLETE_RENDER_SNAPSHOTS[
                    generation
                ]
                encoded = rendered.encode("utf-8")
                self.assertEqual(expected_size, len(encoded))
                self.assertEqual(expected_digest, hashlib.sha256(encoded).hexdigest())
                inline_css = re.search(r"<style>(.*?)</style>", rendered, re.DOTALL)
                self.assertIsNotNone(inline_css)
                self.assertNotIn(".weekly-decision", inline_css.group(1))
                self.assertNotIn('id="weekly-decision-selection-help"', rendered)

    def v2_multi_signal_render_sources(self) -> dict[str, object]:
        sources = copy.deepcopy(self.v2_render_sources())
        dossier = sources["dossier"]
        research = sources["market_research"]
        provider = sources["provider_research"]
        assert isinstance(dossier, dict)
        assert isinstance(research, dict)
        assert isinstance(provider, dict)
        dossier["requested_technology_terms"].append(
            {"term": "Python", "claim_ids": ["C-001"]}
        )
        dossier["claims"][0]["paraphrase"] = (
            "Python supports a concrete professional proposition."
        )
        dossier["evidence"][0]["paraphrase"] = (
            "Python is present in the supplied material."
        )
        dossier["evidence"][1]["paraphrase"] = (
            "Python scope is available for bounded review."
        )
        scripts = str(SCRIPTS)
        if scripts not in sys.path:
            sys.path.insert(0, scripts)
        from build_career_learning_decision_v2 import build_learning_bundle_v2
        from build_career_market_learning_dossier_v2 import build_market_dossier_v2

        market = build_market_dossier_v2(research, dossier)
        learning = build_learning_bundle_v2(
            research,
            market,
            dossier,
            provider,
            [{
                "decision_rank": 1,
                "decision_code": "build_bounded_proof",
                "source_signals": ["python", "terraform"],
                "provider_option_id": None,
            }],
        )
        sources["market_dossier"] = market
        sources["learning_decision"] = learning
        return sources

    def mutated_v2_render_sources(self, mutation: str, sentinel: str) -> dict[str, object]:
        sources = copy.deepcopy(self.v2_render_sources())
        if mutation == "dossier_private_name":
            sources["dossier"]["claims"][0]["paraphrase"] = sentinel
        elif mutation == "research_contact":
            sources["market_research"]["vacancies"][0]["title"] = sentinel
        elif mutation == "provider_local_path":
            sources["provider_research"]["options"][0]["unknowns"] = sentinel
        elif mutation == "provider_url":
            sources["provider_research"]["options"][0]["url"] = sentinel
        elif mutation == "market_snapshot":
            sources["market_dossier"]["source_alignment_snapshot"] = sentinel
        elif mutation == "learning_internal_id":
            sources["learning_decision"]["decisions"][0]["claim_ids"] = [sentinel]
        elif mutation == "provider_control":
            sources["provider_research"]["options"][0]["source_title"] = sentinel
        elif mutation == "research_source_prose":
            sources["market_research"]["vacancies"][0]["requirements"][0][
                "source_paraphrase"
            ] = sentinel
        elif mutation == "provider_as_of_date":
            sources["provider_research"]["as_of_date"] = sentinel
            for option in sources["provider_research"]["options"]:
                option["source_date"] = sentinel
                option["access_date"] = sentinel
        else:
            raise AssertionError(f"unknown source mutation: {mutation}")
        return sources

    @staticmethod
    def expected_v2_mutation_errors(mutation: str) -> tuple[str, ...]:
        if mutation in {"provider_url", "provider_control", "provider_local_path"}:
            return ("provider research is invalid",)
        if mutation in {"learning_internal_id", "provider_as_of_date"}:
            return ("learning decision does not match validated sources",)
        return ("market dossier does not match validated sources",)

    def test_renderer_accepts_only_coherent_market_learning_versions(self) -> None:
        v1 = self.v1_render_sources()
        v2 = self.v2_render_sources()
        self.assertIn("market-context", self.renderer.render_dossier_html(**v1))
        self.assertIn(
            'class="learning-signal-route"',
            self.renderer.render_dossier_html(**v2),
        )

        market_only_v2 = dict(v2, learning_decision=None, provider_research=None)
        market_only = self.renderer.render_dossier_html(**market_only_v2)
        self.assertIn("market-context", market_only)
        self.assertNotIn('class="learning-signal-route"', market_only)

        pairs = (
            ("v1 without learning", dict(v1, learning_decision=None), True),
            ("v1 with v1 learning", v1, True),
            (
                "v1 with v2 learning",
                dict(
                    v1,
                    learning_decision=v2["learning_decision"],
                    provider_research=v2["provider_research"],
                ),
                False,
            ),
            ("v2 without learning", market_only_v2, True),
            (
                "v2 with v1 learning",
                dict(
                    v2,
                    learning_decision=v1["learning_decision"],
                    provider_research=None,
                ),
                False,
            ),
            ("v2 with v2 learning", v2, True),
        )
        for label, arguments, accepted in pairs:
            with self.subTest(pair=label):
                if accepted:
                    self.assertIn(
                        "market-context", self.renderer.render_dossier_html(**arguments)
                    )
                else:
                    with self.assertRaises(
                        self.renderer.MarketCompositionVersionError
                    ) as raised:
                        self.renderer.render_dossier_html(**arguments)
                    self.assertIs(
                        type(raised.exception),
                        self.renderer.MarketCompositionVersionError,
                    )
                    self.assertEqual(
                        "market and learning versions are incompatible",
                        str(raised.exception),
                    )

    def test_learning_v2_route_omits_internal_and_source_values(self) -> None:
        sources = self.v2_render_sources()
        html_output = self.renderer.render_dossier_html(**sources)
        forbidden = (
            "C-002",
            "E-004",
            "V-003-R-01",
            "V-003",
            "LP-001",
            "snap-",
            "https://",
            "Synthetic test requirement",
            "candidate_reported_match",
            "research_first",
            "candidate_owned",
        )
        for value in forbidden:
            with self.subTest(forbidden=value):
                self.assertNotIn(value, html_output)
        self.assertIn("Terraform", html_output)
        self.assertIn("1/5", html_output)
        self.assertIn("V1", html_output)

    def test_learning_v2_cards_render_complete_localized_proof_and_cost_decisions(self) -> None:
        for state, sources in (
            ("complete", self.v2_render_sources("complete")),
            ("limited", self.v2_render_sources("limited")),
        ):
            with self.subTest(state=state):
                learning = sources["learning_decision"]
                assert isinstance(learning, dict)
                locale = str(learning["locale"])
                rendered = self.renderer.render_dossier_html(**sources)
                for decision in learning["decisions"]:
                    rank = decision["decision_rank"]
                    card = re.search(
                        rf'<article class="card span-4 learning-decision-card"[^>]*aria-labelledby="learning-decision-card-title-{rank}".*?</article>',
                        rendered,
                        re.DOTALL,
                    )
                    self.assertIsNotNone(card)
                    card_html = card.group(0)
                    self.assertIn(
                        f'id="learning-decision-card-title-{rank}">{html.escape(decision["option_name"], quote=True)}</h3>',
                        card_html,
                    )
                    expected_owner = decision["provider_or_owner"]
                    if expected_owner == "candidate_owned":
                        expected_owner = "Candidato" if locale == "es" else "Candidate"
                    for projected in (
                        expected_owner,
                        decision["cost_time_band"],
                        decision["expected_signal_boundary"],
                        decision["portfolio_or_no_learning_alternative"],
                        decision["overbuying_risk"],
                        decision["decision_basis"],
                        decision["next_action_gate"],
                    ):
                        with self.subTest(state=state, rank=rank, projected=projected):
                            self.assertIn(html.escape(projected, quote=True), card_html)
                    self.assertIn(
                        f'class="learning-decision-proof" role="group" aria-labelledby="learning-decision-proof-title-{rank}"',
                        card_html,
                    )
                    self.assertIn(
                        f'id="learning-decision-proof-title-{rank}"', card_html
                    )
                provider_decisions = [
                    row for row in learning["decisions"]
                    if row["provider_option_id"] is not None
                ]
                self.assertTrue(provider_decisions)
                for decision in provider_decisions:
                    rank = decision["decision_rank"]
                    card = re.search(
                        rf'aria-labelledby="learning-decision-card-title-{rank}".*?</article>',
                        rendered,
                        re.DOTALL,
                    )
                    self.assertIsNotNone(card)
                    self.assertIn(decision["provider_or_owner"], card.group(0))
                    self.assertIn(decision["option_name"], card.group(0))

    def test_learning_v2_routes_are_localized_resolved_and_complete(self) -> None:
        cases = (
            ("complete", self.v2_render_sources("complete")),
            ("limited", self.v2_render_sources("limited")),
            ("multi-signal", self.v2_multi_signal_render_sources()),
        )
        for state, sources in cases:
            with self.subTest(state=state):
                learning = sources["learning_decision"]
                assert isinstance(learning, dict)
                decisions = learning["decisions"]
                assert isinstance(decisions, list)
                rendered = self.renderer.render_dossier_html(**sources)
                self.assertEqual(
                    len(decisions),
                    rendered.count('class="learning-signal-route"'),
                )
                expected_rows = sum(len(row["signal_routes"]) for row in decisions)
                self.assertEqual(
                    expected_rows,
                    rendered.count('class="learning-signal-route-row"'),
                )
                locale = str(learning["locale"])
                expected_groups: list[
                    tuple[int, list[tuple[str, str, str, str]]]
                ] = []
                for decision in decisions:
                    expected_routes: list[tuple[str, str, str, str]] = []
                    for route in decision["signal_routes"]:
                        expected_routes.append(
                            (
                                route["term_label"],
                                V2_ROUTE_SUPPORT_LABELS[locale][route["support_state"]],
                                ", ".join(route["vacancy_ordinals"]),
                                route["recurrence"],
                            )
                        )
                        self.assertNotIn(route["support_state"], rendered)
                    expected_groups.append(
                        (decision["decision_rank"], expected_routes)
                    )
                    self.assertIn(
                        html.escape(decision["decision_basis"], quote=True), rendered
                    )
                    self.assertNotIn(decision["decision"], rendered)
                route_parser = LearningRouteDOMParser()
                route_parser.feed(rendered)
                self.assertEqual(expected_groups, route_parser.groups)
                if state == "multi-signal":
                    self.assertEqual(
                        [("Python", "Evidencia directa", "V1", "1/5"),
                         ("Terraform", "Reportado por cliente", "V2", "1/5")],
                        route_parser.groups[0][1],
                    )
                audit = DossierDOMAudit()
                audit.feed(rendered)
                self.assertEqual(len(audit.ids), len(set(audit.ids)))
                self.assertEqual(set(), set(audit.references) - set(audit.ids))

    def test_v2_omitted_groups_unavailable_and_legacy_states_fail_closed(self) -> None:
        v1 = self.v1_render_sources()
        v2 = self.v2_render_sources()
        omissions = (
            (
                "market root",
                dict(v2, market_dossier=None),
                ("market composition inputs must be supplied together",),
            ),
            (
                "v1 alignment",
                dict(v1, market_alignment=None),
                ("v1 market composition requires alignment",),
            ),
            (
                "v2 research",
                dict(v2, market_research=None),
                ("market composition inputs must be supplied together",),
            ),
            (
                "v2 provider",
                dict(v2, provider_research=None),
                ("v2 learning and provider research must be supplied together",),
            ),
            (
                "provider without learning",
                dict(v2, learning_decision=None),
                ("v2 learning and provider research must be supplied together",),
            ),
            (
                "v2 with alignment",
                dict(v2, market_alignment=v1["market_alignment"]),
                ("v2 market composition recomputes alignment",),
            ),
            (
                "v1 with provider",
                dict(v1, provider_research=v2["provider_research"]),
                ("v1 market composition excludes provider research",),
            ),
        )
        for label, arguments, expected_errors in omissions:
            with self.subTest(group=label):
                with self.assertRaises(self.renderer.DossierValidationError) as raised:
                    self.renderer.render_dossier_html(**arguments)
                self.assertIs(type(raised.exception), self.renderer.DossierValidationError)
                self.assertEqual(expected_errors, raised.exception.errors)
                self.assertEqual("dossier validation failed", str(raised.exception))

        malformed_version = copy.deepcopy(v2)
        malformed_version["market_dossier"]["schema_version"] = [
            "career-market-learning-dossier-v2"
        ]
        with self.assertRaises(self.renderer.DossierValidationError) as raised:
            self.renderer.render_dossier_html(**malformed_version)
        self.assertIs(type(raised.exception), self.renderer.DossierValidationError)
        self.assertEqual(
            ("market composition inputs have malformed structure",),
            raised.exception.errors,
        )

        unavailable = self.renderer.render_dossier_html(
            **self.v2_render_sources("unavailable")
        )
        self.assertIn("market-context", unavailable)
        self.assertNotIn('class="learning-signal-route"', unavailable)
        legacy = self.renderer.render_dossier_html(v2["dossier"])
        self.assertNotIn('class="learning-signal-route"', legacy)

        for name, (expected_size, expected_digest) in NO_MARKET_RENDER_SNAPSHOTS.items():
            with self.subTest(snapshot=name):
                rendered = self.renderer.render_dossier_html(
                    load_json_fixture(V2_FIXTURE_ROOT / name)
                )
                self.assertEqual(expected_size, len(rendered.encode("utf-8")))
                self.assertEqual(
                    expected_digest,
                    hashlib.sha256(rendered.encode("utf-8")).hexdigest(),
                )

    def test_v2_learning_group_snapshots_before_schema_access_without_original_deepcopy(self) -> None:
        sources = self.v2_render_sources()
        sentinel = "renderer-deepcopy-runtime-sentinel"
        baseline = self.renderer.render_dossier_html(**sources)
        cases = (
            (
                "market",
                "market_dossier",
            ),
            (
                "learning",
                "learning_decision",
            ),
            (
                "provider",
                "provider_research",
            ),
        )
        for name, field in cases:
            with self.subTest(source=name):
                hostile = OnePassMapping(sources[field], sentinel)
                arguments = dict(sources, **{field: hostile})
                with mock.patch.object(
                    self.renderer,
                    "bounded_plain_snapshot",
                    wraps=self.renderer.bounded_plain_snapshot,
                ) as snapshot:
                    rendered = self.renderer.render_dossier_html(**arguments)
                self.assertEqual(1, snapshot.call_count)
                self.assertEqual(1, hostile.items_calls)
                self.assertEqual(baseline, rendered)
                self.assertNotIn(sentinel, rendered)

    def test_v2_private_source_mutations_fail_before_render_without_echo(self) -> None:
        for label, mutation, sentinel in V2_SOURCE_MUTATION_CASES:
            with self.subTest(mutation=label):
                sources = self.mutated_v2_render_sources(mutation, sentinel)
                with self.assertRaises(self.renderer.DossierValidationError) as raised:
                    self.renderer.render_dossier_html(**sources)
                self.assertIs(type(raised.exception), self.renderer.DossierValidationError)
                self.assertEqual(
                    self.expected_v2_mutation_errors(mutation),
                    raised.exception.errors,
                )
                self.assertEqual("dossier validation failed", str(raised.exception))
                self.assertNotIn(sentinel, str(raised.exception))
                self.assertNotIn(sentinel, "\n".join(raised.exception.errors))

    def test_v2_private_source_mutations_leave_no_writer_or_cli_output(self) -> None:
        for label, mutation, sentinel in V2_SOURCE_MUTATION_CASES:
            with self.subTest(mutation=label), tempfile.TemporaryDirectory() as directory:
                sources = self.mutated_v2_render_sources(mutation, sentinel)
                root = Path(directory)
                paths: dict[str, Path] = {}
                for name, value in sources.items():
                    if value is None:
                        continue
                    path = root / f"{name}.json"
                    path.write_text(json.dumps(value), encoding="utf-8")
                    paths[name] = path
                expected_errors = self.expected_v2_mutation_errors(mutation)
                writer_output = root / "writer.html"
                with mock.patch.object(
                    self.renderer,
                    "bounded_plain_snapshot",
                    wraps=self.renderer.bounded_plain_snapshot,
                ) as snapshot, mock.patch.object(
                    self.renderer.VALIDATOR,
                    "load_dossier",
                    side_effect=AssertionError("schema load before shared snapshot"),
                ) as dossier_loader, mock.patch.object(
                    self.renderer.RESEARCH_VALIDATOR,
                    "load_research",
                    side_effect=AssertionError("schema load before shared snapshot"),
                ) as research_loader, mock.patch.object(
                    self.renderer.LEARNING_VALIDATOR,
                    "load_learning_bundle",
                    side_effect=AssertionError("schema load before shared snapshot"),
                ) as learning_loader, mock.patch.object(
                    self.renderer.PROVIDER_VALIDATOR,
                    "load_provider_research",
                    side_effect=AssertionError("schema load before shared snapshot"),
                ) as provider_loader, mock.patch.object(
                    self.renderer.BASE.ASSET_LOADER,
                    "read_private_asset",
                    side_effect=AssertionError("asset read before validation"),
                ) as asset_read, self.assertRaises(
                    self.renderer.DossierValidationError
                ) as raised:
                    self.renderer.write_dossier_html(
                        paths["dossier"],
                        writer_output,
                        market_dossier_path=paths["market_dossier"],
                        market_research_path=paths["market_research"],
                        learning_decision_path=paths["learning_decision"],
                        provider_research_path=paths["provider_research"],
                    )
                self.assertEqual(1, snapshot.call_count)
                for schema_loader in (
                    dossier_loader,
                    research_loader,
                    learning_loader,
                    provider_loader,
                ):
                    schema_loader.assert_not_called()
                asset_read.assert_not_called()
                self.assertIs(type(raised.exception), self.renderer.DossierValidationError)
                self.assertEqual(expected_errors, raised.exception.errors)
                self.assertEqual("dossier validation failed", str(raised.exception))
                expected_stderr = "\n".join(expected_errors) + "\n"
                self.assertNotIn(sentinel, str(raised.exception))
                self.assertFalse(writer_output.exists())

                cli_output = root / "cli.html"
                result = subprocess.run(
                    [
                        sys.executable,
                        "-B",
                        str(RENDERER_PATH),
                        str(paths["dossier"]),
                        "--market-dossier",
                        str(paths["market_dossier"]),
                        "--market-research",
                        str(paths["market_research"]),
                        "--learning-decision",
                        str(paths["learning_decision"]),
                        "--provider-research",
                        str(paths["provider_research"]),
                        "--output",
                        str(cli_output),
                    ],
                    cwd=REPO_ROOT,
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=20,
                )
                self.assertEqual(2, result.returncode)
                self.assertEqual("", result.stdout)
                self.assertEqual(expected_stderr, result.stderr)
                self.assertNotIn(sentinel, result.stderr)
                self.assertNotIn("Traceback", result.stderr)
                self.assertFalse(cli_output.exists())

    def test_localized_ledger_has_one_named_region_and_exact_semantic_rows(self) -> None:
        expected_labels = {
            "es": (
                "Foto", "Banner", "Nombre", "URL del perfil", "Titular", "Ubicación",
                "Información de contacto", "Acerca de", "Experiencia", "Aptitudes",
                "Destacado", "Certificaciones", "Educación", "Recomendaciones",
                "Actividad", "Analítica", "Preferencias de empleo",
            ),
            "en": (
                "Photo", "Banner", "Name", "Profile URL", "Headline", "Location",
                "Contact information", "About", "Experience", "Skills", "Featured",
                "Certifications", "Education", "Recommendations", "Activity",
                "Analytics", "Job preferences",
            ),
        }
        for locale in ("es", "en"):
            with self.subTest(locale=locale):
                rendered = self.renderer.render_dossier_html(make_v2_dossier(locale))
                regions = re.findall(
                    r'<section class="section-block section-coverage-ledger" aria-labelledby="([^"]+)">(.*?)</section>',
                    rendered,
                    re.DOTALL,
                )
                self.assertEqual(len(regions), 1)
                region_label, body = regions[0]
                self.assertEqual(len(re.findall(rf'<h2 id="{re.escape(region_label)}">', body)), 1)
                rows = re.findall(
                    r'<li class="section-coverage-row"><article aria-labelledby="([^"]+)">\s*'
                    r'<h3 id="\1">([^<]+)</h3>\s*<dl class="section-coverage-facts">(.*?)</dl>\s*'
                    r'</article></li>',
                    body,
                    re.DOTALL,
                )
                self.assertEqual(len(rows), 17)
                self.assertEqual(tuple(label for _, label, _ in rows), expected_labels[locale])
                self.assertEqual(len({heading_id for heading_id, _, _ in rows}), 17)
                for _, _, facts in rows:
                    self.assertIn("<dt>", facts)
                    self.assertIn("<dd>", facts)
                    self.assertGreaterEqual(facts.count("<dt>"), 2)
                    self.assertEqual(facts.count("<dt>"), len(re.findall(r"<dd(?:\s|>)", facts)))

    def test_unavailable_rows_show_localized_reason_and_request_decision(self) -> None:
        for locale, labels in (
            ("es", ("No disponible", "Autorización requerida", "Respuesta pendiente")),
            ("en", ("Unavailable", "Authorization required", "Response pending")),
        ):
            with self.subTest(locale=locale):
                rendered = self.renderer.render_dossier_html(make_v2_dossier(locale))
                for label in labels:
                    self.assertIn(label, rendered)
                self.assertIn('class="section-coverage-request"', rendered)

    def test_three_named_coach_cards_render_closed_blank_templates_without_legacy_priority_copy(self) -> None:
        for locale in ("es", "en"):
            with self.subTest(locale=locale):
                dossier = make_v2_dossier(locale)
                rendered = self.renderer.render_dossier_html(dossier)
                cards = re.findall(
                    r'<article class="card span-4 coach-priority-card" aria-labelledby="([^"]+)">(.*?)</article>',
                    rendered,
                    re.DOTALL,
                )
                self.assertEqual(len(cards), 3)
                self.assertNotIn('class="timebox"', rendered)
                for (heading_id, card), priority in zip(cards, dossier["priorities"], strict=True):
                    self.assertEqual(len(re.findall(rf'<h3 id="{re.escape(heading_id)}">', card)), 1)
                    self.assertIn('class="coach-observation"', card)
                    self.assertIn('class="coach-prompt"', card)
                    self.assertIn('class="coach-template"', card)
                    blanks = re.findall(r'<li><span class="coach-template-field">[^<]+</span><span class="coach-template-blank" role="img" aria-label="[^"]+"></span></li>', card)
                    self.assertGreaterEqual(len(blanks), 1)
                    self.assertLessEqual(len(blanks), 5)
                    for old_value in ("problem", "action"):
                        self.assertNotIn(str(priority[old_value]), card)

    def test_market_projection_derives_four_localized_trace_steps_without_raw_ids(self) -> None:
        expected = {
            "es": ("Prioridad", "Evidencia disponible", "Plantilla privada", "Permiso de lectura"),
            "en": ("Priority", "Available evidence", "Private template", "Read-only permission"),
        }
        for locale in ("es", "en"):
            with self.subTest(locale=locale):
                if locale == "es":
                    dossier, market, research, alignment = market_case(
                        "complete-five-es.json", "scenario-a-es.json"
                    )
                else:
                    dossier, market, research, alignment = build_limited_market_case(4)
                for priority in dossier["priorities"]:
                    projected = self.renderer._derive_decision_trace(priority, dossier, market, locale)
                    self.assertEqual(4, len(projected["steps"]))
                    self.assertEqual(expected[locale], tuple(step["label"] for step in projected["steps"]))
                    self.assertEqual(locale, projected["locale"])
                    self.assertIn("target_section", projected)
                    self.assertIn("target_section_label", projected)
                    self.assertTrue(projected["evidence_views"])
                    for evidence in projected["evidence_views"]:
                        self.assertTrue(evidence["state_label"])
                        self.assertTrue(evidence["paraphrase"])
                        self.assertNotRegex(evidence["paraphrase"], r"E-\d+|CAP-\d+|https?://|/private/")
                    self.assertTrue(projected["template_fields"])
                rendered = self.renderer.render_dossier_html(
                    dossier, market, market_research=research, market_alignment=alignment,
                )
                self.assertEqual(1, visible_text(rendered).count(
                    "¿Autorizas inspeccionar" if locale == "es" else "Do you authorize read-only inspection"
                ))

    def test_market_projection_exposes_localized_inspection_states_and_pending_anchor(self) -> None:
        dossier, market, research, alignment = market_case(
            "complete-five-es.json", "scenario-a-es.json"
        )
        priority = copy.deepcopy(dossier["priorities"][0])
        priority["target_section"] = "name"
        priority["evidence_ids"] = []
        projected = self.renderer._derive_decision_trace(priority, dossier, market, "es")
        self.assertEqual("name", projected["target_section"])
        self.assertEqual((), projected["evidence_views"])
        self.assertEqual("pending", projected["inspection_state"]["state"])
        self.assertEqual("decide-now-authorization-title", projected["authorization_anchor"])
        self.assertEqual("Nombre", projected["inspection_state"]["target_label"])

    def test_market_projection_maps_candidate_declined_and_failed_inspection_states(self) -> None:
        dossier, market, _research, _alignment = market_case(
            "complete-five-es.json", "scenario-a-es.json"
        )
        for target, expected_state, reason, decision in (
            ("experience", "candidate_supplied", "candidate_material_supplied", None),
            ("certifications", "declined", "inspection_declined", "declined_for_session"),
            ("education", "failed", "authorized_inspection_failed", "authorized_inspection_failed"),
        ):
            with self.subTest(target=target):
                candidate = copy.deepcopy(dossier)
                priority = copy.deepcopy(candidate["priorities"][0])
                priority["target_section"] = target
                priority["evidence_ids"] = []
                row = next(item for item in candidate["section_coverage"] if item["section"] == target)
                row["availability"] = "candidate_supplied" if expected_state == "candidate_supplied" else "unavailable"
                row["evidence_state"] = "candidate_reported" if expected_state == "candidate_supplied" else "unknown"
                row["reason"] = reason
                if decision is None:
                    row.pop("inspection_request", None)
                else:
                    row["inspection_request"]["decision"] = decision
                projected = self.renderer._derive_decision_trace(priority, candidate, market, "es")
                self.assertEqual(expected_state, projected["inspection_state"]["state"])
                self.assertNotIn("authorization_anchor", projected)

    def test_market_projection_does_not_authorize_a_nonselected_pending_section(self) -> None:
        dossier, market, _research, _alignment = market_case(
            "complete-five-es.json", "scenario-a-es.json"
        )
        candidate = copy.deepcopy(dossier)
        priority = copy.deepcopy(candidate["priorities"][0])
        priority["target_section"] = "profile_url"
        priority["evidence_ids"] = []
        self.assertEqual("name", self.validator.select_pending_inspection_section(candidate))
        projected = self.renderer._derive_decision_trace(priority, candidate, market, "es")
        self.assertEqual("pending_other", projected["inspection_state"]["state"])
        self.assertEqual("Otra inspección está pendiente", projected["inspection_state"]["label"])
        self.assertNotIn("authorization_anchor", projected)

    def test_market_projection_rejects_raw_paraphrase_values_without_echo(self) -> None:
        dossier, market, research, alignment = market_case(
            "complete-five-es.json", "scenario-a-es.json"
        )
        for value in (
            "https://example.invalid/profile",
            "/private/path/profile.json",
            "Publish this to LinkedIn now.",
            "My name is John Doe.",
            "See E-001 CAP-001",
        ):
            with self.subTest(value=value):
                invalid = copy.deepcopy(dossier)
                invalid["evidence"][0]["paraphrase"] = value
                with self.assertRaises(self.renderer.DossierValidationError) as context:
                    self.renderer.render_dossier_html(
                        invalid, market, market_research=research, market_alignment=alignment,
                    )
                errors = "\n".join(context.exception.errors)
                self.assertNotIn(value, errors)

    def test_market_projection_direct_helper_rejects_private_action_identity_and_raw_refs(self) -> None:
        dossier, market, research, alignment = market_case(
            "complete-five-es.json", "scenario-a-es.json"
        )
        for value in (
            "/private/path/profile.json",
            "Publish this to LinkedIn now.",
            "My name is John Doe.",
            "See E-001 CAP-001",
        ):
            with self.subTest(value=value):
                invalid = copy.deepcopy(dossier)
                invalid["evidence"][0]["paraphrase"] = value
                with self.assertRaises(self.renderer.DossierValidationError) as context:
                    self.renderer._derive_decision_trace(
                        invalid["priorities"][0], invalid, market, "es"
                    )
                self.assertNotIn(value, "\n".join(context.exception.errors))

    def test_market_projection_direct_helper_rejects_malformed_or_cyclic_market(self) -> None:
        dossier, market, research, alignment = market_case(
            "complete-five-es.json", "scenario-a-es.json"
        )
        cyclic: dict[str, object] = {"state": "complete_market_evidence"}
        cyclic["self"] = cyclic
        for invalid_market in ({"state": "not-a-market", "vacancies": []}, cyclic):
            with self.subTest(cyclic=invalid_market is cyclic):
                with self.assertRaises(self.renderer.DossierValidationError) as context:
                    self.renderer._derive_decision_trace(
                        dossier["priorities"][0], dossier, invalid_market, "es"
                    )
                self.assertNotIn("not-a-market", "\n".join(context.exception.errors))
                with self.assertRaises(self.renderer.DossierValidationError) as render_context:
                    self.renderer.render_dossier_html(
                        dossier,
                        invalid_market,
                        market_research=research,
                        market_alignment=alignment,
                    )
                self.assertNotIn("not-a-market", "\n".join(render_context.exception.errors))

    def test_market_projection_rejects_unresolved_or_wrong_section_ids_without_echo(self) -> None:
        dossier, market, research, alignment = market_case(
            "complete-five-es.json", "scenario-a-es.json"
        )
        for evidence_ids, sentinel in ((["E-999"], "E-999"), (["E-002"], "E-002")):
            with self.subTest(evidence_ids=evidence_ids):
                invalid = copy.deepcopy(dossier)
                invalid["priorities"][0]["evidence_ids"] = evidence_ids
                with self.assertRaises(self.renderer.DossierValidationError) as context:
                    self.renderer.render_dossier_html(
                        invalid, market, market_research=research, market_alignment=alignment,
                    )
                errors = "\n".join(context.exception.errors)
                self.assertNotIn(sentinel, errors)

    def test_market_projection_rejects_malformed_explicit_market_before_output_and_no_market_is_unchanged(self) -> None:
        dossier = load_json_fixture(V2_FIXTURE_ROOT / "scenario-a-es.json")
        malformed = {"state": "not-a-market"}
        with self.assertRaises(self.renderer.DossierValidationError) as context:
            self.renderer.render_dossier_html(dossier, malformed, market_research={}, market_alignment={})
        self.assertNotIn("not-a-market", "\n".join(context.exception.errors))
        rendered = self.renderer.render_dossier_html(dossier)
        expected_size, expected_digest = NO_MARKET_RENDER_SNAPSHOTS["scenario-a-es.json"]
        self.assertEqual(expected_size, len(rendered.encode("utf-8")))
        self.assertEqual(expected_digest, hashlib.sha256(rendered.encode("utf-8")).hexdigest())

    def test_decision_trace_markup_and_accessibility(self) -> None:
        css = (REPO_ROOT / "plugins" / "professional-growth-coach" / "assets" / "career-market-learning-dossier-v1.css").read_text(encoding="utf-8")
        for contract in (
            ".decision-trace",
            "grid-template-columns: repeat(2, minmax(0, 1fr))",
            "grid-template-columns: minmax(0, 1fr)",
            "@media (max-width: 640px)",
            "@media print",
            "break-inside: avoid",
            "@media screen and (prefers-color-scheme: dark)",
            "@media (forced-colors: active)",
            "@media (prefers-reduced-motion: reduce)",
            "background: Canvas",
            "color: CanvasText",
        ):
            with self.subTest(contract=contract):
                self.assertIn(contract, css)
        trace_css = re.search(r"\.decision-trace-steps\s*\{(.*?)\}", css, re.DOTALL)
        self.assertIsNotNone(trace_css)
        self.assertIn("repeat(2, minmax(0, 1fr))", trace_css.group(1))
        self.assertNotIn("repeat(4,", trace_css.group(1))

        for locale in ("es", "en"):
            with self.subTest(locale=locale):
                if locale == "es":
                    dossier, market, research, alignment = market_case(
                        "complete-five-es.json", "scenario-a-es.json"
                    )
                    labels = ("Prioridad", "Evidencia disponible", "Plantilla privada", "Permiso de lectura")
                    pending_question = "¿Autorizas inspeccionar"
                else:
                    dossier, market, research, alignment = build_limited_market_case(4)
                    labels = ("Priority", "Available evidence", "Private template", "Read-only permission")
                    pending_question = "Do you authorize read-only inspection"
                rendered = self.renderer.render_dossier_html(
                    dossier, market, market_research=research, market_alignment=alignment,
                )
                cards = re.findall(
                    r'<article class="card span-4 coach-priority-card" aria-labelledby="([^\"]+)">(.*?)</article>',
                    rendered,
                    re.DOTALL,
                )
                self.assertEqual(3, len(cards))
                for (heading_id, card), priority in zip(cards, dossier["priorities"], strict=True):
                    rank = priority["rank"]
                    trace = re.search(
                        rf'<section class="decision-trace" aria-labelledby="decision-trace-title-{rank}"[^>]*>(.*?</ol>.*?)</section>',
                        card,
                        re.DOTALL,
                    )
                    self.assertIsNotNone(trace)
                    trace_body = trace.group(1)
                    self.assertIn(
                        f'aria-describedby="decision-trace-boundary-{rank}"',
                        trace.group(0),
                    )
                    self.assertIn(
                        f'id="decision-trace-boundary-{rank}" class="decision-trace-boundary"',
                        trace_body,
                    )
                    self.assertEqual(
                        labels,
                        tuple(re.findall(r'<span class="decision-trace-step-label">([^<]+)</span>', trace_body)),
                    )
                    self.assertIn(f'id="decision-trace-title-{rank}"', trace_body)
                    self.assertIn(f'id="decision-trace-priority-{rank}"', trace_body)
                    self.assertIn(f'id="decision-trace-evidence-{rank}-1"', trace_body)
                    self.assertIn(f'id="decision-trace-template-{rank}"', trace_body)
                    self.assertIn(f'id="decision-trace-inspection-{rank}"', trace_body)
                    self.assertIn("Sección objetivo" if locale == "es" else "Target section", trace_body)
                    self.assertNotIn("Rol objetivo" if locale == "es" else "Target role", trace_body)
                    self.assertNotRegex(trace_body, r"<(?:form|button|input|select|textarea)\b")
                    hrefs = re.findall(r'<a\s+[^>]*href="([^"]+)"', trace_body)
                    self.assertTrue(all(href == "#decide-now-authorization-title" for href in hrefs))
                audit = DossierDOMAudit()
                audit.feed(rendered)
                self.assertEqual(len(audit.ids), len(set(audit.ids)))
                self.assertEqual(set(), set(audit.references) - set(audit.ids))
                self.assertEqual(3, rendered.count('class="decision-trace"'))
                self.assertEqual(1, visible_text(rendered).count(pending_question))

    def test_light_secondary_text_token_is_contrasting_and_visible_selectors_do_not_use_divider_muted(self) -> None:
        base_css = (
            REPO_ROOT / "plugins" / "professional-growth-coach" / "assets" / "executive-career-dossier-v1.css"
        ).read_text(encoding="utf-8")
        market_css = (
            REPO_ROOT / "plugins" / "professional-growth-coach" / "assets" / "career-market-learning-dossier-v1.css"
        ).read_text(encoding="utf-8")
        extension_css = (
            REPO_ROOT / "plugins" / "professional-growth-coach" / "assets" / "executive-career-dossier-v2.css"
        ).read_text(encoding="utf-8")

        self.assertIn("--muted-text: #53605a", base_css)
        dark_css = base_css[base_css.index("@media screen and (prefers-color-scheme: dark)") :]
        self.assertIn("--muted-text: #b8c4d8", dark_css)
        self.assertGreaterEqual(_contrast_ratio("#53605a", "#ffffff"), 4.5)
        self.assertGreaterEqual(_contrast_ratio("#53605a", "#f6f4ee"), 4.5)

        visible_text_selectors = (
            ".market-learning-state",
            ".market-next-safe-action",
            ".decide-now-summary",
            ".decide-now-target",
            ".learning-decision-sample",
            ".learning-decision-role",
            ".learning-decision-boundary",
            ".decision-trace-boundary",
        )
        for selector in visible_text_selectors:
            with self.subTest(selector=selector):
                self.assertRegex(
                    market_css,
                    rf"{re.escape(selector)}\s*\{{[^}}]*color:\s*var\(--muted-text\)",
                )

        self.assertRegex(
            extension_css,
            r"\.coach-template-boundary\s*\{[^}]*color:\s*var\(--muted-text\)",
        )
        forced_market = re.search(
            r"@media \(forced-colors: active\)\s*\{(.*?)\n\}", market_css, re.DOTALL
        )
        self.assertIsNotNone(forced_market)
        self.assertIn(".market-learning-state", forced_market.group(1))
        self.assertIn(".market-next-safe-action", forced_market.group(1))
        self.assertIn(".decision-trace-boundary", forced_market.group(1))
        for selector in (
            ".learning-decision-sample",
            ".learning-decision-role",
            ".learning-decision-boundary",
        ):
            self.assertRegex(
                market_css,
                rf"{re.escape(selector)}[^{{]*\{{[^}}]*color:\s*CanvasText",
            )
        forced_v2 = re.search(
            r"@media \(forced-colors: active\)\s*\{(.*?)\n\}", extension_css, re.DOTALL
        )
        self.assertIsNotNone(forced_v2)
        self.assertIn(".coach-template-boundary", forced_v2.group(1))

    def test_light_theme_declares_line_token_for_v2_extension(self) -> None:
        base_css = (
            REPO_ROOT / "plugins" / "professional-growth-coach" / "assets" / "executive-career-dossier-v1.css"
        ).read_text(encoding="utf-8")
        light_css = base_css.split(
            "@media screen and (prefers-color-scheme: dark)", 1
        )[0]
        self.assertIn("--line: #b8c7c0", light_css)
        extension_css = (
            REPO_ROOT / "plugins" / "professional-growth-coach" / "assets" / "executive-career-dossier-v2.css"
        ).read_text(encoding="utf-8")
        self.assertIn("border-bottom: 1px solid var(--line)", extension_css)

    def test_coach_templates_expose_localized_private_blank_and_boundary(self) -> None:
        for locale, expected in (
            ("es", ("No incluyas texto sin procesar del perfil, datos de contacto ni valores privados.", "Espacio en blanco para completar en privado")),
            ("en", ("Do not include raw profile text, contact data, or private values.", "Blank for private completion")),
        ):
            with self.subTest(locale=locale):
                rendered = self.renderer.render_dossier_html(make_v2_dossier(locale))
                self.assertIn(expected[0], rendered)
                self.assertIn(expected[1], rendered)
                self.assertEqual(rendered.count('class="coach-template" aria-labelledby='), 3)
                self.assertEqual(rendered.count('aria-describedby="coach-template-boundary-'), 3)

    def test_visible_product_surface_excludes_internal_and_private_values(self) -> None:
        dossier = make_v2_dossier("es")
        rendered_text = visible_text(self.renderer.render_dossier_html(dossier))
        forbidden = {
            "read_only_visible_section_inspection", "pending_response",
            "declined_for_session", "authorization_required",
            "context_action_result_v1", "profile_url", "contact_info",
            "/private/path/profile.json", "https://www.linkedin.com/in/example",
            "person@example.test",
        }
        forbidden.update(record["id"] for record in dossier["evidence"])
        for token in forbidden:
            with self.subTest(token=token):
                self.assertNotIn(token, rendered_text)

    def test_writer_rejects_unsafe_new_coaching_prose_before_creating_visible_output(self) -> None:
        for field, value, diagnostic in UNSAFE_COACHING_PROSE:
            with self.subTest(field=field, diagnostic=diagnostic):
                dossier = make_v2_dossier()
                dossier["priorities"][0][field] = value
                with tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    source = root / "unsafe.json"
                    output = root / "unsafe.html"
                    source.write_text(json.dumps(dossier), encoding="utf-8")
                    with self.assertRaises(self.renderer.DossierValidationError) as context:
                        self.renderer.write_dossier_html(source, output)
                    self.assertFalse(output.exists())
                errors = "\n".join(context.exception.errors)
                self.assertIn(f"priorities[0].{field} {diagnostic}", errors)
                self.assertNotIn(value, errors)

    def test_all_coaching_fields_fail_writer_and_cli_before_output(self) -> None:
        for field in ("coach_observation", "why_it_matters", "coach_prompt"):
            with self.subTest(field=field):
                dossier = make_v2_dossier()
                unsafe = "Conectar contexto y publicar esto en LinkedIn."
                dossier["priorities"][0][field] = unsafe
                with tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    source = root / "unsafe.json"
                    output = root / "unsafe.html"
                    source.write_text(json.dumps(dossier), encoding="utf-8")
                    result = subprocess.run(
                        [sys.executable, "-B", str(VALIDATOR_PATH), str(source)],
                        cwd=REPO_ROOT, text=True, capture_output=True, check=False,
                    )
                    self.assertEqual(result.returncode, 2)
                    self.assertIn(f"priorities[0].{field} must remain a private review action", result.stderr)
                    self.assertNotIn(unsafe, result.stderr)
                    with self.assertRaises(self.renderer.DossierValidationError) as context:
                        self.renderer.write_dossier_html(source, output)
                    self.assertFalse(output.exists())
                errors = "\n".join(context.exception.errors)
                self.assertIn(f"priorities[0].{field} must remain a private review action", errors)
                self.assertNotIn(unsafe, errors)

    def test_market_placeholder_is_one_bounded_non_recommendation_state(self) -> None:
        for name in ("scenario-a-es.json", "scenario-c-en.json"):
            with self.subTest(name=name):
                dossier = json.loads((V2_FIXTURE_ROOT / name).read_text(encoding="utf-8"))
                rendered = self.renderer.render_dossier_html(dossier)
                regions = re.findall(
                    r'<section class="card market-unavailable-card span-12" aria-labelledby="market-unavailable-title">(.*?)</section>',
                    rendered,
                    re.DOTALL,
                )
                self.assertEqual(len(regions), 1)
                text_value = visible_text(regions[0]).casefold()
                self.assertNotIn("<progress", regions[0].casefold())
                self.assertNotRegex(text_value, r"\d+(?:\.\d+)?%")
                for forbidden in (
                    "score", "vacancy", "vacante", "employer", "empleador",
                    "course", "curso", "paid", "pago",
                ):
                    self.assertNotIn(forbidden, text_value)

    def test_no_market_bytes_are_protected_while_complete_market_requires_trusted_group(self) -> None:
        for fixture_name, (byte_count, digest) in NO_MARKET_RENDER_SNAPSHOTS.items():
            with self.subTest(fixture=fixture_name):
                dossier = load_json_fixture(V2_FIXTURE_ROOT / fixture_name)
                rendered = self.renderer.render_dossier_html(dossier)
                self.assertEqual(byte_count, len(rendered.encode("utf-8")))
                self.assertEqual(digest, hashlib.sha256(rendered.encode("utf-8")).hexdigest())

        dossier, market, research, alignment = market_case(
            "complete-five-es.json", "scenario-a-es.json"
        )
        rendered = self.renderer.render_dossier_html(
            dossier,
            market,
            market_research=research,
            market_alignment=alignment,
        )
        self.assertEqual(5, rendered.count('class="vacancy-alignment-card"'))

    def test_dated_market_state_has_a_separate_bounded_truthful_surface(self) -> None:
        source = load_v1_fixture("scenario-market-en.json")
        dossier = make_v2_dossier("en")
        market_evidence = copy.deepcopy(source["evidence"][-1])
        market_evidence["profile_section"] = None
        dossier["evidence"].append(market_evidence)
        dossier["market_context"] = copy.deepcopy(source["market_context"])
        self.assertEqual(self.validator.validate_dossier(dossier), [])
        rendered = self.renderer.render_dossier_html(dossier)
        self.assertIn('class="card market-evidence-available-card span-12"', rendered)
        self.assertNotIn("This dossier includes no market evidence.", rendered)
        surface = re.search(r'<section class="card market-evidence-available-card span-12".*?</section>', rendered, re.DOTALL)
        self.assertIsNotNone(surface)
        for forbidden in ("e-008", "vacancy", "http", "score"):
            self.assertNotIn(forbidden, visible_text(surface.group(0)).casefold())

    def test_complete_market_composition_has_labelled_progress_matrix_recurrence_and_gap_route(self) -> None:
        dossier, market, research, alignment = market_case(
            "complete-five-es.json", "scenario-a-es.json"
        )

        rendered = self.renderer.render_dossier_html(
            dossier,
            market,
            market_research=research,
            market_alignment=alignment,
        )

        self.assertNotIn(
            '<div class="dossier-grid section-block">\n      <section class="section-block market-summary"',
            rendered,
        )

        cards = re.findall(
            r'<article class="vacancy-alignment-card" aria-labelledby="([^"]+)">(.*?)</article>',
            rendered,
            re.DOTALL,
        )
        self.assertEqual(5, len(cards))
        self.assertEqual(
            [(row["employer"], row["title"]) for row in market["vacancies"]],
            [
                (
                    re.search(r'class="vacancy-employer">([^<]+)</', card).group(1),
                    re.search(r'<h3 id="[^"]+">([^<]+)</h3>', card).group(1),
                )
                for _, card in cards
            ],
        )
        for index, ((labelled_by, card), vacancy) in enumerate(
            zip(cards, market["vacancies"], strict=True), start=1
        ):
            employer_id = f"vacancy-alignment-employer-{index}"
            heading_id = f"vacancy-alignment-title-{index}"
            score_id = f"vacancy-alignment-score-{index}"
            boundary_id = f"vacancy-alignment-boundary-{index}"
            self.assertEqual(
                f"{employer_id} {heading_id} {score_id} "
                f"vacancy-alignment-coverage-{index} vacancy-alignment-band-{index} {boundary_id}",
                re.search(
                    rf'<progress class="vacancy-alignment-progress"[^>]*aria-labelledby="([^"]+)"',
                    card,
                ).group(1),
            )
            self.assertIn(
                f'<p id="{employer_id}" class="vacancy-employer">', card
            )
            self.assertIn(f'<h3 id="{heading_id}">', card)
            self.assertIn(
                f'<p id="{score_id}" class="vacancy-alignment-score">'
                f'{vacancy["alignment_percent"]} de 100</p>',
                card,
            )
            self.assertIn(
                f'<p id="vacancy-alignment-coverage-{index}" class="vacancy-evidence-coverage">'
                f'Cobertura de evidencia: '
                f'{vacancy["evidence_coverage_percent"]}%</p>',
                card,
            )
            self.assertRegex(
                card,
                rf'<p id="vacancy-alignment-band-{index}" class="vacancy-qualitative-band">[^<]+</p>',
            )
            self.assertRegex(
                card,
                rf'<progress class="vacancy-alignment-progress" value="{vacancy["alignment_percent"]}" '
                rf'max="100" aria-labelledby="{employer_id} {heading_id} {score_id} '
                rf'vacancy-alignment-coverage-{index} vacancy-alignment-band-{index} '
                rf'vacancy-alignment-boundary-{index}">',
            )
            self.assertIn(
                f'<p id="{boundary_id}" class="vacancy-score-boundary">', card
            )

        audit = DossierDOMAudit()
        audit.feed(rendered)
        self.assertEqual(len(audit.ids), len(set(audit.ids)))
        self.assertEqual(set(), set(audit.references) - set(audit.ids))

        self.assertEqual(1, rendered.count('<table class="market-matrix">'))
        self.assertIn('<caption>Matriz de evidencia de la muestra</caption>', rendered)
        self.assertIn('<th id="market-matrix-col-signal" scope="col">Señal</th>', rendered)
        self.assertIn('<th id="market-matrix-col-profile" scope="col">Evidencia del perfil</th>', rendered)
        self.assertNotIn("insufficient_evidence", rendered)
        self.assertNotIn("higher_documented_alignment", rendered)
        vacancy_headers = re.findall(
            r'<th id="market-matrix-col-v([1-5])" scope="col"><span aria-hidden="true">V\1</span>'
            r'<span class="visually-hidden">([^<]+)</span></th>',
            rendered,
        )
        self.assertEqual(5, len(vacancy_headers))
        key_items = re.findall(
            r'<li class="market-vacancy-key-item"><strong>V([1-5])</strong> — ([^<]+)</li>',
            rendered,
        )
        self.assertEqual(5, len(key_items))
        for index, vacancy in enumerate(market["vacancies"], start=1):
            full_label = f'{vacancy["employer"]} · {vacancy["title"]}'
            self.assertIn((str(index), full_label), key_items)
            self.assertIn((str(index), full_label), vacancy_headers)
            self.assertIn(
                f'data-label="V{index}"', rendered
            )

        rows = re.findall(
            r'<tr class="market-matrix-row">(.*?)</tr>', rendered, re.DOTALL
        )
        self.assertEqual(len(market["matrix_rows"]), len(rows))
        for row in rows:
            row_heading = re.search(
                r'<th id="([^"]+)" scope="row">([^<]+)</th>', row
            )
            self.assertIsNotNone(row_heading)
            cells = re.findall(r'<td ([^>]+)>(.*?)</td>', row, re.DOTALL)
            self.assertEqual(6, len(cells))
            for attributes, body in cells:
                self.assertIn('data-label="', attributes)
                self.assertIn('headers="', attributes)
                self.assertRegex(
                    body,
                    r'<span class="matrix-state-symbol" aria-hidden="true">[✓●≈!?—]</span>'
                    r'<span class="matrix-state-text">[^<]+</span>',
                )

        recurrence_rows = re.findall(
            r'<div class="recurrence-row" aria-labelledby="([^"]+)">(.*?)</div>',
            rendered,
            re.DOTALL,
        )
        self.assertEqual(len(market["recurrence_rows"]), len(recurrence_rows))
        for index, ((heading_id, body), row) in enumerate(
            zip(recurrence_rows, market["recurrence_rows"], strict=True), start=1
        ):
            fraction_id = f"recurrence-fraction-{index}"
            self.assertIn(f'id="{heading_id}"', body)
            self.assertIn(
                f'<span id="{fraction_id}" class="recurrence-fraction">'
                f'{row["display_fraction"]}</span>',
                body,
            )
            self.assertRegex(
                body,
                rf'<progress class="recurrence-progress" value="{row["occurrences"]}" '
                rf'max="{row["sample_size"]}" aria-labelledby="{heading_id} {fraction_id}" '
                rf'aria-describedby="market-recurrence-boundary">',
            )
        self.assertEqual(1, rendered.count('<p id="market-recurrence-boundary">'))
        self.assertNotIn("market demand", visible_text(rendered).casefold())

        route = re.findall(
            r'<section class="gap-closure-route" aria-labelledby="gap-closure-route-title">(.*?)</section>',
            rendered,
            re.DOTALL,
        )
        self.assertEqual(1, len(route))
        self.assertEqual(4, len(re.findall(r'<li>', route[0])))
        for priority in dossier["priorities"]:
            self.assertEqual(1, visible_text(rendered).count(priority["why_it_matters"]))
        market_region = rendered[
            rendered.index('<section class="section-block market-summary"'):
            rendered.index('<section class="section-block" aria-labelledby="copy-title">')
        ]
        market_text = visible_text(market_region)
        learning_disclosure = (
            "Evaluación de aprendizaje: no evaluada en este incremento de mercado; "
            "no se recomienda curso ni certificación."
        )
        self.assertEqual(1, market_text.count(learning_disclosure))
        market_text_without_learning_disclosure = market_text.replace(learning_disclosure, "")
        for forbidden in ("curso", "course", "certificación", "certification"):
            self.assertNotIn(forbidden, market_text_without_learning_disclosure.casefold())

        self.assertNotIn("aria-live", market_region)
        forbidden_values = {
            market["source_research_snapshot"],
            market["source_executive_dossier_snapshot"],
            "Synthetic test requirement.",
        }
        for vacancy in research["vacancies"]:
            forbidden_values.update(
                {
                    vacancy["vacancy_id"],
                    vacancy["employer_id"],
                    vacancy["source_url"],
                    *[item["requirement_id"] for item in vacancy["requirements"]],
                }
            )
            if vacancy["official_referrer_url"] is not None:
                forbidden_values.add(vacancy["official_referrer_url"])
        forbidden_values.update(
            evidence_id
            for row in alignment["signal_bindings"]
            for evidence_id in row["evidence_ids"]
        )
        for value in forbidden_values:
            with self.subTest(forbidden=value):
                self.assertNotIn(value, rendered)

    def test_recurrence_boundary_is_described_in_es_and_en_progress(self) -> None:
        for research_name, dossier_name in (
            ("complete-five-es.json", "scenario-a-es.json"),
            ("limited-four-en.json", "scenario-c-en.json"),
        ):
            with self.subTest(locale=research_name):
                dossier, market, research, alignment = market_case(
                    research_name, dossier_name
                )
                rendered = self.renderer.render_dossier_html(
                    dossier,
                    market,
                    market_research=research,
                    market_alignment=alignment,
                )
                self.assertEqual(
                    1, rendered.count('<p id="market-recurrence-boundary">')
                )
                recurrence_progresses = re.findall(
                    r'<progress class="recurrence-progress"[^>]*aria-describedby="([^"]+)"',
                    rendered,
                )
                self.assertEqual(len(market["recurrence_rows"]), len(recurrence_progresses))
                self.assertTrue(
                    all(boundary == "market-recurrence-boundary" for boundary in recurrence_progresses)
                )

    def test_market_score_boundary_is_named_in_es_and_en_progress(self) -> None:
        for research_name, dossier_name in (
            ("complete-five-es.json", "scenario-a-es.json"),
            ("limited-four-en.json", "scenario-c-en.json"),
        ):
            with self.subTest(locale=research_name):
                dossier, market, research, alignment = market_case(
                    research_name, dossier_name
                )
                rendered = self.renderer.render_dossier_html(
                    dossier,
                    market,
                    market_research=research,
                    market_alignment=alignment,
                )
                progress_names = re.findall(
                    r'<progress class="vacancy-alignment-progress"[^>]*aria-labelledby="([^"]+)"',
                    rendered,
                )
                self.assertEqual(len(market["vacancies"]), len(progress_names))
                for index, labelled_by in enumerate(progress_names, start=1):
                    boundary_id = f"vacancy-alignment-boundary-{index}"
                    self.assertIn(boundary_id, labelled_by)
                    self.assertEqual(
                        1,
                        rendered.count(
                            f'<p id="{boundary_id}" class="vacancy-score-boundary">'
                        ),
                    )

    def test_mobile_matrix_cells_use_short_vacancy_keys_while_key_and_headers_keep_full_labels(self) -> None:
        dossier, market, research, alignment = market_case(
            "complete-five-es.json", "scenario-a-es.json"
        )
        rendered = self.renderer.render_dossier_html(
            dossier,
            market,
            market_research=research,
            market_alignment=alignment,
        )

        for index, vacancy in enumerate(market["vacancies"], start=1):
            full_label = f'{vacancy["employer"]} · {vacancy["title"]}'
            with self.subTest(index=index):
                self.assertIn(
                    f'<td class="market-matrix-state-cell" data-label="V{index}" ',
                    rendered,
                )
                self.assertIn(
                    f'<li class="market-vacancy-key-item"><strong>V{index}</strong> — {full_label}</li>',
                    rendered,
                )
                self.assertIn(
                    f'<th id="market-matrix-col-v{index}" scope="col"><span aria-hidden="true">V{index}</span>'
                    f'<span class="visually-hidden">{full_label}</span></th>',
                    rendered,
                )

    def test_decide_now_precedes_coverage_and_uses_semantic_references_without_actions_or_echo(self) -> None:
        dossier, market, research, alignment = market_case(
            "complete-five-es.json", "scenario-a-es.json"
        )
        rendered = self.renderer.render_dossier_html(
            dossier,
            market,
            market_research=research,
            market_alignment=alignment,
        )

        references, described_by, region = decide_now_region(rendered)
        self.assertLess(
            rendered.index('class="section-block decide-now"'),
            rendered.index('class="section-block section-coverage-ledger"'),
        )
        pending = self.validator.select_pending_inspection_section(dossier)
        pending_index = next(
            index for index, row in enumerate(dossier["section_coverage"], start=1)
            if row["section"] == pending
        )
        self.assertEqual(
            {
                "coach-priority-title-1",
                "coach-priority-title-2",
                "coach-priority-title-3",
                f"section-coverage-title-{pending_index}",
                "market-context-title",
            },
            references,
        )
        self.assertEqual("decide-now-summary", described_by)
        self.assertNotRegex(region, r"<(?:button|input|select|textarea|form)\b")
        self.assertNotRegex(region, r'<a href="https?://')
        for forbidden in (
            market["source_research_snapshot"],
            market["source_executive_dossier_snapshot"],
            *(
                value
                for vacancy in research["vacancies"]
                for value in (vacancy["vacancy_id"], vacancy["employer_id"], vacancy["source_url"])
            ),
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, region)

        v1_rendered = load_v1_renderer().render_dossier_html(
            load_v1_fixture("scenario-a-es.json")
        )
        self.assertNotIn('class="section-block decide-now"', v1_rendered)

    def test_decide_now_uses_zero_market_without_score_recurrence_or_gap_route(self) -> None:
        dossier, market, research, alignment = market_case(
            "unavailable-es.json", "scenario-a-es.json"
        )
        rendered = self.renderer.render_dossier_html(
            dossier,
            market,
            market_research=research,
            market_alignment=alignment,
        )

        references, _described_by, region = decide_now_region(rendered)
        self.assertIn("market-context-title", references)
        self.assertNotIn("vacancy-alignment", region)
        self.assertNotIn("recurrence-row", region)
        self.assertNotIn("gap-closure-route", region)
        self.assertNotIn("<progress", region)
        self.assertNotRegex(visible_text(region), r"\b\d+(?:\.\d+)?%\b|\b\d+/0\b")

    def test_decide_now_uses_actual_one_to_five_denominators_and_one_pending_authorization(self) -> None:
        for count in range(1, 6):
            with self.subTest(count=count):
                if count == 5:
                    dossier, market, research, alignment = market_case(
                        "complete-five-es.json", "scenario-a-es.json"
                    )
                    authorization = "¿Autorizas inspeccionar"
                else:
                    dossier, market, research, alignment = build_limited_market_case(count)
                    authorization = "Do you authorize read-only inspection"
                rendered = self.renderer.render_dossier_html(
                    dossier,
                    market,
                    market_research=research,
                    market_alignment=alignment,
                )

                _references, _described_by, region = decide_now_region(rendered)
                text = visible_text(region)
                self.assertEqual(1, text.count(authorization))
                self.assertEqual(
                    [row["display_fraction"] for row in market["recurrence_rows"]],
                    re.findall(r"\b\d+/\d+\b", text),
                )
                self.assertTrue(
                    all(f"/{count}" in fraction for fraction in re.findall(r"\b\d+/\d+\b", text))
                )

    def test_decide_now_authorization_explains_ranked_priority_impact_in_es_and_en(self) -> None:
        for locale, research_name, dossier_name, section_label, expected_intro in (
            (
                "es",
                "complete-five-es.json",
                "scenario-a-es.json",
                "Titular",
                "La inspección de solo lectura de Titular puede informar estas prioridades:",
            ),
            (
                "en",
                "limited-four-en.json",
                "scenario-c-en.json",
                "Headline",
                "Read-only inspection of the Headline section may inform these priorities:",
            ),
        ):
            with self.subTest(locale=locale):
                dossier = make_v2_dossier(locale)
                for row in dossier["section_coverage"]:
                    request = row.get("inspection_request")
                    if isinstance(request, dict):
                        request["decision"] = "declined_for_session"
                        row["reason"] = "inspection_declined"
                    if row["section"] == "headline":
                        row.update({
                            "availability": "unavailable",
                            "evidence_state": "unknown",
                            "reason": "authorization_required",
                            "inspection_request": {
                                "access_type": "read_only_visible_section_inspection",
                                "decision": "pending_response",
                                "scope": "current_session_only",
                                "carry_forward": False,
                            },
                        })
                dossier["priorities"][1]["target_section"] = "headline"
                _source_dossier, market, research, _alignment = market_case(
                    research_name, dossier_name
                )

                rendered = self.renderer._render_decide_now(
                    dossier, locale, market
                )
                impact = re.search(
                    r'<div id="decide-now-authorization-impact".*?</div>',
                    rendered,
                    re.DOTALL,
                )
                self.assertIsNotNone(impact)
                impact_html = impact.group(0)
                impact_text = visible_text(impact_html)
                self.assertIn(expected_intro, impact_text)
                self.assertIn(section_label, impact_text)
                matching = sorted(
                    (
                        priority
                        for priority in dossier["priorities"]
                        if priority["target_section"] == "headline"
                    ),
                    key=lambda priority: priority["rank"],
                )
                self.assertEqual(2, len(matching))
                self.assertLess(
                    impact_text.index(str(matching[0]["title"])),
                    impact_text.index(str(matching[1]["title"])),
                )
                self.assertRegex(
                    rendered,
                    r'class="card span-4 decide-now-card decide-now-authorization"[^>]*'
                    r'aria-describedby="decide-now-authorization-impact"',
                )
                question = self.renderer.AUTHORIZATION_QUESTIONS[locale]["headline"]
                self.assertEqual(1, visible_text(rendered).count(question))
                audit = DossierDOMAudit()
                audit.feed(rendered)
                self.assertIn("decide-now-authorization-impact", audit.ids)
                self.assertIn("decide-now-authorization-impact", audit.references)
                for forbidden in (
                    market["source_research_snapshot"],
                    market["source_executive_dossier_snapshot"],
                    *(vacancy["source_url"] for vacancy in research["vacancies"]),
                ):
                    self.assertNotIn(forbidden, impact_html)
                self.assertNotRegex(impact_html, r"<(?:a|button|input|select|textarea|form)\b")

    def test_decide_now_authorization_impact_is_bounded_or_absent_without_pending(self) -> None:
        for locale, research_name, dossier_name, expected in (
            (
                "es",
                "complete-five-es.json",
                "scenario-a-es.json",
                "La inspección de solo lectura de Nombre completa la cobertura visible; "
                "cualquier cambio de prioridad requiere otra revisión.",
            ),
            (
                "en",
                "limited-four-en.json",
                "scenario-c-en.json",
                "Read-only inspection of the Banner section completes visible coverage; "
                "any reprioritization requires another review.",
            ),
        ):
            with self.subTest(locale=locale, state="coverage-only"):
                dossier = make_v2_dossier(locale)
                _source_dossier, market, _research, _alignment = market_case(
                    research_name, dossier_name
                )
                pending = self.validator.select_pending_inspection_section(dossier)
                rendered = self.renderer._render_decide_now(dossier, locale, market)
                impact = re.search(
                    r'<div id="decide-now-authorization-impact".*?</div>',
                    rendered,
                    re.DOTALL,
                )
                self.assertIsNotNone(impact)
                impact_text = visible_text(impact.group(0))
                self.assertEqual(expected, impact_text)
                for priority in dossier["priorities"]:
                    self.assertNotIn(str(priority["title"]), impact_text)
                self.assertEqual(
                    1,
                    visible_text(rendered).count(
                        self.renderer.AUTHORIZATION_QUESTIONS[locale][pending]
                    ),
                )

            with self.subTest(locale=locale, state="no-pending"):
                for row in dossier["section_coverage"]:
                    request = row.get("inspection_request")
                    if isinstance(request, dict):
                        request["decision"] = "declined_for_session"
                        row["reason"] = "inspection_declined"
                rendered = self.renderer._render_decide_now(dossier, locale, market)
                self.assertNotIn("decide-now-authorization-impact", rendered)
                self.assertFalse(
                    any(
                        question in visible_text(rendered)
                        for question in self.renderer.AUTHORIZATION_QUESTIONS[locale].values()
                    )
                )

    def test_decide_now_styles_cover_responsive_print_and_forced_colors_without_fixed_tracks(self) -> None:
        css = (REPO_ROOT / "plugins" / "professional-growth-coach" / "assets" / "career-market-learning-dossier-v1.css").read_text(encoding="utf-8")
        for contract in (
            ".decide-now-card",
            "@media (max-width: 640px)",
            "@media print",
            "@media (forced-colors: active)",
            "@media (prefers-reduced-motion: reduce)",
            "background: Canvas",
            "color: CanvasText",
            "background: Highlight",
            "color: HighlightText",
        ):
            with self.subTest(contract=contract):
                self.assertIn(contract, css)
        self.assertNotIn("min-width: 7rem", css)

    def test_learning_panel_is_omitted_without_bundle_and_for_zero_market(self) -> None:
        dossier, market, research, alignment = market_case(
            "unavailable-es.json", "scenario-a-es.json"
        )
        legacy = self.renderer.render_dossier_html(dossier)
        self.assertNotIn('class="learning-decision"', legacy)
        unavailable = learning_case(
            "unavailable-es.json", "scenario-a-es.json", count=0
        )
        rendered = self.renderer.render_dossier_html(
            unavailable[0],
            unavailable[1],
            market_research=unavailable[2],
            market_alignment=unavailable[3],
            learning_decision=unavailable[4],
        )
        self.assertNotIn('class="learning-decision"', rendered)
        self.assertNotIn("learning-decision-title", rendered)

    def test_learning_panel_renders_three_to_five_conversational_rows_without_private_or_external_content(self) -> None:
        for count in (3, 5):
            with self.subTest(count=count):
                case = learning_case(
                    "complete-five-es.json", "scenario-a-es.json", count=count, decision_count=count
                )
                rendered = self.renderer.render_dossier_html(
                    case[0],
                    case[1],
                    market_research=case[2],
                    market_alignment=case[3],
                    learning_decision=case[4],
                )
                self.assertIn('class="section-block learning-decision"', rendered)
                expected_learning_title = (
                    "Qué estudiar —y qué no comprar aún—"
                    if case[0]["locale"] == "es"
                    else "What to study—and what not to buy yet"
                )
                self.assertIn(expected_learning_title, visible_text(rendered))
                panel = re.search(
                    r'<section class="section-block learning-decision".*?</section>',
                    rendered,
                    re.DOTALL,
                )
                self.assertIsNotNone(panel)
                panel_text = visible_text(panel.group(0))
                expected_signal = self.renderer._signal_label(case[1]["matrix_rows"][0]["signal"])
                self.assertIn(expected_signal, panel_text)
                expected_target_label = "Target role" if case[0]["locale"] != "es" else "Rol objetivo"
                self.assertIn(expected_target_label, panel_text)
                self.assertEqual(
                    count,
                    len(re.findall(r'class="[^"]*\blearning-decision-card\b[^"]*"', panel.group(0))),
                )
                self.assertTrue(
                    "bounded learning hypothesis" in panel_text or "hipótesis acotada" in panel_text
                )
                self.assertNotRegex(panel.group(0), r"<(?:button|input|select|textarea|form)\b")
                self.assertNotRegex(panel.group(0), r'<a href="https?://')
                for forbidden in (
                    *(
                        value
                        for vacancy in case[2]["vacancies"]
                        for value in (vacancy["vacancy_id"], vacancy["employer_id"], vacancy["source_url"])
                    ),
                    *(
                        evidence_id
                        for row in case[4]["decisions"]
                        for evidence_id in row["source_gap_ids"]
                    ),
                    case[4]["source_market_snapshot"],
                    case[4]["source_dossier_snapshot"],
                    case[4]["source_research_snapshot"],
                ):
                    self.assertNotIn(forbidden, panel.group(0))
                self.assertLess(
                    rendered.index('class="section-block learning-decision"'),
                    rendered.index('class="gap-closure-route"'),
                )

    def test_learning_cards_reference_shared_boundary_before_options_in_es_and_en(self) -> None:
        for locale, research_name, dossier_name in (
            ("es", "complete-five-es.json", "scenario-a-es.json"),
            ("en", "limited-four-en.json", "scenario-c-en.json"),
        ):
            with self.subTest(locale=locale):
                case = learning_case(
                    research_name,
                    dossier_name,
                    count=5 if locale == "es" else 3,
                    decision_count=3,
                )
                rendered = self.renderer.render_dossier_html(
                    case[0],
                    case[1],
                    market_research=case[2],
                    market_alignment=case[3],
                    learning_decision=case[4],
                )
                panel = re.search(
                    r'<section class="section-block learning-decision".*?</section>',
                    rendered,
                    re.DOTALL,
                )
                self.assertIsNotNone(panel)
                boundary = '<p id="learning-decision-boundary" class="learning-decision-boundary">'
                self.assertEqual(1, panel.group(0).count(boundary))
                self.assertEqual(1, rendered.count('id="learning-decision-boundary"'))
                self.assertLess(
                    panel.group(0).index(boundary),
                    panel.group(0).index('class="dossier-grid learning-decision-grid"'),
                )
                cards = re.findall(
                    r'<article class="card span-4 learning-decision-card" '
                    r'aria-labelledby="[^"]+" aria-describedby="([^"]+)">',
                    panel.group(0),
                )
                self.assertEqual(
                    ["learning-decision-boundary"] * 3,
                    cards,
                )
                audit = DossierDOMAudit()
                audit.feed(rendered)
                self.assertEqual(set(), set(audit.references) - set(audit.ids))
                self.assertNotRegex(panel.group(0), r'<(?:button|input|select|textarea|form)\b')
                self.assertNotRegex(panel.group(0), r'<a href="https?://')

    def test_learning_panel_has_one_decide_now_internal_anchor_and_rejects_invalid_bundle_before_output(self) -> None:
        case = learning_case("complete-five-es.json", "scenario-a-es.json", count=3)
        rendered = self.renderer.render_dossier_html(
            case[0],
            case[1],
            market_research=case[2],
            market_alignment=case[3],
            learning_decision=case[4],
        )
        references, _described_by, decide_region = decide_now_region(rendered)
        self.assertIn("learning-decision-title", references)
        self.assertEqual(1, decide_region.count('href="#learning-decision-title"'))
        for field, unsafe_text in (
            ("option_name", "file:///Users/private/profile.json"),
            ("option_name", "Enroll now: example course"),
            ("target_role", "candidate name Example Person Senior SRE"),
            ("decision_basis", "Guaranteed interview preparation"),
            ("option_name", "Buy this course"),
            ("next_action_gate", "exact authorization required before Send a message"),
            ("target_role", "example.com/profile"),
            ("provider_or_owner", "ID-12345"),
            ("option_name", "Compra este curso"),
            ("decision_basis", "Te ayuda a conseguir empleo"),
            ("option_name", "case-123456"),
            ("option_name", "case-123"),
            ("provider_or_owner", "private-id-x"),
            ("option_name", "ID-1"),
            ("provider_or_owner", "account-id-xy"),
            ("decision_basis", "foo.ai/profile"),
            ("decision_basis", "foo.xyz/profile"),
            ("option_name", "Ensures an interview"),
            ("option_name", "Esta opción garantiza contratación"),
            ("option_name", "This gets an interview"),
            ("option_name", "Enroll"),
            ("option_name", "Candidate Kevin"),
            ("target_role", "Kevin Ríos"),
        ):
            with self.subTest(field=field, unsafe_text=unsafe_text):
                invalid = copy.deepcopy(case[4])
                invalid["decisions"][0][field] = unsafe_text
                with self.assertRaises(self.renderer.DossierValidationError) as raised:
                    self.renderer.render_dossier_html(
                        case[0],
                        case[1],
                        market_research=case[2],
                        market_alignment=case[3],
                        learning_decision=invalid,
                    )
                self.assertNotIn(unsafe_text, "\n".join(raised.exception.errors))
        for field, unsafe_text in (
            ("unknowns", "You are assured a job"),
            ("unknowns", "See E-001 CAP-001"),
        ):
            with self.subTest(provider_field=field, unsafe_text=unsafe_text):
                invalid = copy.deepcopy(case[4])
                invalid["decisions"][1]["provider_source"][field] = unsafe_text
                with self.assertRaises(self.renderer.DossierValidationError):
                    self.renderer.render_dossier_html(
                        case[0],
                        case[1],
                        market_research=case[2],
                        market_alignment=case[3],
                        learning_decision=invalid,
                    )
        for invalid in ({}, "not-a-learning-mapping"):
            with self.subTest(invalid=type(invalid).__name__):
                with self.assertRaises(self.renderer.DossierValidationError):
                    self.renderer.render_dossier_html(
                        case[0],
                        case[1],
                        market_research=case[2],
                        market_alignment=case[3],
                        learning_decision=invalid,
                    )

    def test_learning_cards_explain_proof_to_cost_before_action_boundary(self) -> None:
        for locale, research_name, dossier_name in (
            ("es", "complete-five-es.json", "scenario-a-es.json"),
            ("en", "limited-four-en.json", "scenario-c-en.json"),
        ):
            with self.subTest(locale=locale):
                case = learning_case(
                    research_name,
                    dossier_name,
                    count=5 if locale == "es" else 3,
                    decision_count=3,
                )
                rendered = self.renderer.render_dossier_html(
                    case[0],
                    case[1],
                    market_research=case[2],
                    market_alignment=case[3],
                    learning_decision=case[4],
                )
                panel = re.search(
                    r'<section class="section-block learning-decision".*?</section>',
                    rendered,
                    re.DOTALL,
                )
                self.assertIsNotNone(panel)
                panel_text = visible_text(panel.group(0))
                for expected in (
                    "Base de la decisión" if locale == "es" else "Decision basis",
                    "Costo y tiempo" if locale == "es" else "Cost and time",
                    "Señal esperada" if locale == "es" else "Expected signal",
                ):
                    self.assertIn(expected, panel_text)
                self.assertLess(
                    panel_text.index("Base de la decisión" if locale == "es" else "Decision basis"),
                    panel_text.index("Costo y tiempo" if locale == "es" else "Cost and time"),
                )
                self.assertLess(
                    panel_text.index("Costo y tiempo" if locale == "es" else "Cost and time"),
                    panel_text.index("Señal esperada" if locale == "es" else "Expected signal"),
                )
                self.assertRegex(
                    panel_text,
                    r"(?:México|Mexico) eligibility and preparation time are not stated",
                )
                self.assertIn("2026-08-13", panel_text)
                self.assertNotRegex(panel.group(0), r"<a href=\"https?://")
                self.assertNotRegex(panel.group(0), r"<(?:button|input|select|textarea|form)\b")

    def test_learning_proof_to_cost_groups_are_named_and_aria_referenced(self) -> None:
        for locale, research_name, dossier_name in (
            ("es", "complete-five-es.json", "scenario-a-es.json"),
            ("en", "limited-four-en.json", "scenario-c-en.json"),
        ):
            with self.subTest(locale=locale):
                case = learning_case(
                    research_name,
                    dossier_name,
                    count=5 if locale == "es" else 3,
                    decision_count=3,
                )
                rendered = self.renderer.render_dossier_html(
                    case[0],
                    case[1],
                    market_research=case[2],
                    market_alignment=case[3],
                    learning_decision=case[4],
                )
                expected = "Prueba y costo" if locale == "es" else "Proof and cost"
                self.assertEqual(
                    3,
                    rendered.count('class="learning-decision-proof" role="group" aria-labelledby='),
                )
                groups = re.findall(
                    r'<div class="learning-decision-proof" role="group" aria-labelledby="([^"]+)">(.*?)</div>',
                    rendered,
                    re.DOTALL,
                )
                self.assertEqual(3, len(groups))
                self.assertEqual(3, len({group_id for group_id, _body in groups}))
                for rank, (group_id, body) in enumerate(groups, start=1):
                    self.assertEqual(f"learning-decision-proof-title-{rank}", group_id)
                    self.assertIn(
                        f'<h4 id="learning-decision-proof-title-{rank}">{expected}</h4>',
                        body,
                    )

    def test_learning_card_proof_to_cost_fields_remain_absent_without_provider_source(self) -> None:
        case = learning_case(
            "complete-five-es.json", "scenario-a-es.json", count=5, decision_count=3
        )
        rendered = self.renderer.render_dossier_html(
            case[0],
            case[1],
            market_research=case[2],
            market_alignment=case[3],
            learning_decision=case[4],
        )
        cards = re.findall(
            r'<article class="card span-4 learning-decision-card".*?</article>',
            rendered,
            re.DOTALL,
        )
        self.assertEqual(3, len(cards))
        self.assertNotIn("Fuente oficial", visible_text(cards[0]))
        self.assertIn("Fuente oficial", visible_text(cards[1]))

    def test_learning_panel_uses_dynamic_one_to_five_sample_counts(self) -> None:
        for count in range(1, 6):
            with self.subTest(count=count):
                case = learning_case(
                    "complete-five-es.json", "scenario-a-es.json", count=count
                )
                rendered = self.renderer.render_dossier_html(
                    case[0],
                    case[1],
                    market_research=case[2],
                    market_alignment=case[3],
                    learning_decision=case[4],
                )
                panel = re.search(
                    r'<section class="section-block learning-decision".*?</section>',
                    rendered,
                    re.DOTALL,
                )
                self.assertIsNotNone(panel)
                self.assertIn(f"N={count}", visible_text(panel.group(0)))

    def test_learning_decision_styles_cover_responsive_print_dark_forced_colors_and_motion(self) -> None:
        css = (REPO_ROOT / "plugins" / "professional-growth-coach" / "assets" / "career-market-learning-dossier-v1.css").read_text(encoding="utf-8")
        for contract in (
            ".learning-decision-card",
            "@media (max-width: 640px)",
            "@media screen and (prefers-color-scheme: dark)",
            "@media print",
            "@media (forced-colors: active)",
            "@media (prefers-reduced-motion: reduce)",
            "background: Canvas",
            "color: CanvasText",
            "background: Highlight",
            "color: HighlightText",
        ):
            with self.subTest(contract=contract):
                self.assertIn(contract, css)

    def test_limited_market_composition_uses_dynamic_n_without_padding(self) -> None:
        for count in (1, 2, 3, 4):
            with self.subTest(count=count):
                dossier, market, research, alignment = build_limited_market_case(count)
                rendered = self.renderer.render_dossier_html(
                    dossier,
                    market,
                    market_research=research,
                    market_alignment=alignment,
                )
                self.assertEqual(count, rendered.count('class="vacancy-alignment-card"'))
                self.assertEqual(count, rendered.count('class="vacancy-alignment-progress"'))
                self.assertEqual(count, rendered.count('class="market-vacancy-key-item"'))
                self.assertEqual(
                    [f"{row['occurrences']}/{count}" for row in market["recurrence_rows"]],
                    re.findall(r'class="recurrence-fraction">([^<]+)</span>', rendered),
                )
                for index in range(1, count + 1):
                    self.assertIn(f'id="market-matrix-col-v{index}"', rendered)
                self.assertNotIn(f'id="market-matrix-col-v{count + 1}"', rendered)
                self.assertNotIn("Synthetic test limit.", rendered)
                self.assertEqual(
                    1,
                    rendered.count(
                        "The bounded search ended before five vacancies were gathered."
                    ),
                )

    def test_limited_market_summary_is_described_by_its_sample_limitation(self) -> None:
        es_dossier, _market, es_research, _alignment = market_case(
            "complete-five-es.json", "scenario-a-es.json"
        )
        es_research["employers"] = es_research["employers"][:3]
        es_research["vacancies"] = es_research["vacancies"][:3]
        es_research["state"] = "limited_market_evidence"
        es_research["search_limit"] = {
            "bounded_queries_run": 12,
            "limit_reason": "bounded_search_exhausted",
            "distinct_employer_search_exhausted": False,
            "limitation": "Synthetic test limit.",
        }
        es_alignment = market_alignment(es_research, es_dossier)
        scripts = str(SCRIPTS)
        if scripts not in sys.path:
            sys.path.insert(0, scripts)
        from build_career_market_learning_dossier import build_market_dossier

        limited_cases = (
            (
                "es",
                "Limitación de la muestra",
                (
                    es_dossier,
                    build_market_dossier(es_research, es_dossier, es_alignment),
                    es_research,
                    es_alignment,
                ),
            ),
            ("en", "Sample limitation", build_limited_market_case(3)),
        )
        opening = (
            '<section class="section-block market-summary" '
            'aria-labelledby="market-context-title" '
            'aria-describedby="market-sample-limitation">'
        )
        for locale, limitation_label, case in limited_cases:
            with self.subTest(locale=locale):
                dossier, market, research, alignment = case
                rendered = self.renderer.render_dossier_html(
                    dossier,
                    market,
                    market_research=research,
                    market_alignment=alignment,
                )
                self.assertEqual(1, rendered.count(opening))
                self.assertEqual(1, rendered.count('id="market-sample-limitation"'))
                limitation = re.search(
                    r'<p id="market-sample-limitation".*?</p>',
                    rendered,
                    re.DOTALL,
                )
                self.assertIsNotNone(limitation)
                self.assertIn(limitation_label, visible_text(limitation.group(0)))
                self.assertLess(
                    rendered.index('id="market-sample-limitation"'),
                    rendered.index('class="market-learning-state"'),
                )
                self.assertLess(
                    rendered.index('id="market-sample-limitation"'),
                    rendered.index('class="market-vacancy-section"'),
                )
                audit = DossierDOMAudit()
                audit.feed(rendered)
                self.assertEqual(set(), set(audit.references) - set(audit.ids))

        complete = market_case("complete-five-es.json", "scenario-a-es.json")
        unavailable = market_case("unavailable-es.json", "scenario-a-es.json")
        for state, case in (("complete", complete), ("unavailable", unavailable)):
            with self.subTest(state=state):
                dossier, market, research, alignment = case
                rendered = self.renderer.render_dossier_html(
                    dossier,
                    market,
                    market_research=research,
                    market_alignment=alignment,
                )
                self.assertNotIn("market-sample-limitation", rendered)
        self.assertNotIn(
            "market-sample-limitation",
            self.renderer.render_dossier_html(complete[0]),
        )

    def test_validated_unavailable_market_bundle_is_distinct_from_legacy_placeholder(self) -> None:
        dossier, market, research, alignment = market_case(
            "unavailable-es.json", "scenario-a-es.json"
        )
        legacy = self.renderer.render_dossier_html(dossier)
        rendered = self.renderer.render_dossier_html(
            dossier,
            market,
            market_research=research,
            market_alignment=alignment,
        )

        self.assertIn(COPY_MARKET_PLACEHOLDER_ES, legacy)
        self.assertNotIn("Synthetic test unavailability.", legacy)
        self.assertNotIn(COPY_MARKET_PLACEHOLDER_ES, rendered)
        self.assertNotIn("Synthetic test unavailability.", rendered)
        self.assertEqual(
            1,
            rendered.count(
                "La búsqueda acotada no produjo vacantes verificables para esta muestra."
            ),
        )
        self.assertEqual(1, rendered.count('class="card market-unavailable-card span-12"'))
        self.assertEqual(1, rendered.count('aria-labelledby="market-context-title"'))
        self.assertEqual(0, rendered.count('class="vacancy-alignment-progress"'))
        self.assertEqual(0, rendered.count('class="recurrence-row"'))
        self.assertNotIn('<table class="market-matrix">', rendered)
        unavailable_region = re.findall(
            r'<section class="section-block market-summary" aria-labelledby="market-context-title">(.*?)</section>',
            rendered,
            re.DOTALL,
        )
        self.assertEqual(1, len(unavailable_region))
        self.assertNotIn("<section", unavailable_region[0])
        self.assertNotRegex(visible_text(unavailable_region[0]), r"\b\d+(?:\.\d+)?%\b")
        for forbidden in (
            market["source_research_snapshot"],
            market["source_executive_dossier_snapshot"],
        ):
            self.assertNotIn(forbidden, rendered)

    def test_unavailable_market_exposes_one_localized_safe_next_step(self) -> None:
        cases = (
            ("es", "Siguiente paso seguro: reunir una vacante fechada y verificable antes de reabrir la revisión."),
            ("en", "Safe next step: bring one dated, verifiable vacancy before reopening the review."),
        )
        for locale, copy in cases:
            with self.subTest(locale=locale):
                dossier, market, research, alignment = market_case(
                    "unavailable-es.json", "scenario-a-es.json" if locale == "es" else "scenario-c-en.json"
                )
                if locale == "en":
                    market["locale"] = "en"
                    market["search_summary"]["locale"] = "en"
                    research["locale"] = "en"
                    from dossier_snapshot import snapshot_for_dossier
                    from validate_target_vacancy_research import snapshot_for_market_dossier

                    dossier_snapshot = snapshot_for_dossier(dossier)
                    research_snapshot = snapshot_for_market_dossier(research)
                    market["source_executive_dossier_snapshot"] = dossier_snapshot
                    market["source_research_snapshot"] = research_snapshot
                    alignment["research_snapshot"] = research_snapshot
                    alignment["executive_dossier_snapshot"] = dossier_snapshot
                rendered = self.renderer.render_dossier_html(
                    dossier, market, market_research=research, market_alignment=alignment
                )
                unavailable_region = re.findall(
                    r'<section class="section-block market-summary" aria-labelledby="market-context-title">(.*?)</section>',
                    rendered,
                    re.DOTALL,
                )
                self.assertEqual(1, len(unavailable_region))
                region = unavailable_region[0]
                self.assertEqual(1, region.count('class="market-next-safe-action"'))
                self.assertEqual(1, region.count(copy))
                self.assertLess(
                    region.index('class="market-next-safe-action"'),
                    region.index('class="market-learning-state"'),
                )
                self.assertNotIn("href=", region)
                self.assertNotIn("authorize", region.casefold())
                self.assertNotIn("autoriza", region.casefold())

    def test_market_learning_state_is_disclosed_without_changing_legacy_placeholder(self) -> None:
        cases = (
            ("complete-five-es.json", "scenario-a-es.json", "Evaluación de aprendizaje: no evaluada en este incremento de mercado; no se recomienda curso ni certificación."),
            ("limited-four-en.json", "scenario-c-en.json", "Learning evaluation: not evaluated in this market increment; no course or certification recommendation is made."),
            ("unavailable-es.json", "scenario-a-es.json", "Evaluación de aprendizaje: no evaluada en este incremento de mercado; no se recomienda curso ni certificación."),
        )
        for market_name, dossier_name, copy in cases:
            with self.subTest(market=market_name):
                dossier, market, research, alignment = market_case(market_name, dossier_name)
                rendered = self.renderer.render_dossier_html(
                    dossier, market, market_research=research, market_alignment=alignment
                )
                self.assertEqual(1, rendered.count('class="market-learning-state"'))
                self.assertEqual(1, rendered.count(copy))
                self.assertNotIn("learning_state", rendered)
                self.assertNotIn("learning_decisions", rendered)
        dossier, *_ = market_case("complete-five-es.json", "scenario-a-es.json")
        legacy = self.renderer.render_dossier_html(dossier)
        self.assertNotIn("market-learning-state", legacy)

    def test_market_summary_exposes_localized_research_as_of_date(self) -> None:
        cases = (
            (
                "es",
                market_case("complete-five-es.json", "scenario-a-es.json"),
                "Corte de evidencia",
            ),
            (
                "en",
                build_limited_market_case(3),
                "Evidence as of",
            ),
        )
        for locale, case, label in cases:
            with self.subTest(locale=locale):
                dossier, market, research, alignment = case
                rendered = self.renderer.render_dossier_html(
                    dossier,
                    market,
                    market_research=research,
                    market_alignment=alignment,
                )
                panel = re.search(
                    r'<section class="section-block market-summary".*?</section>',
                    rendered,
                    re.DOTALL,
                )
                self.assertIsNotNone(panel)
                marker = (
                    '<p id="market-evidence-as-of" class="market-summary-as-of">'
                    f'<span class="label">{label}</span>'
                    '<time datetime="2026-08-13">2026-08-13</time></p>'
                )
                self.assertEqual(1, rendered.count('id="market-evidence-as-of"'))
                self.assertIn(marker, panel.group(0))
                self.assertLess(
                    panel.group(0).index(marker),
                    panel.group(0).index('class="market-learning-state"'),
                )
                audit = DossierDOMAudit()
                audit.feed(rendered)
                self.assertEqual(set(), set(audit.references) - set(audit.ids))
                self.assertNotRegex(panel.group(0), r'<(?:button|input|select|textarea|form)\b')
                self.assertNotRegex(panel.group(0), r'<a href="https?://')

        dossier, market, research, alignment = market_case(
            "unavailable-es.json", "scenario-a-es.json"
        )
        unavailable = self.renderer.render_dossier_html(
            dossier,
            market,
            market_research=research,
            market_alignment=alignment,
        )
        self.assertNotIn("market-evidence-as-of", unavailable)
        self.assertNotIn("market-evidence-as-of", self.renderer.render_dossier_html(dossier))

    def test_market_inputs_are_all_or_none_and_trusted_composition_rejects_source_mutation(self) -> None:
        dossier, market, research, alignment = market_case(
            "complete-five-es.json", "scenario-a-es.json"
        )
        values = {
            "market_dossier": market,
            "market_research": research,
            "market_alignment": alignment,
        }
        names = tuple(values)
        for mask in range(1, 7):
            kwargs = {
                name: values[name] if mask & (1 << index) else None
                for index, name in enumerate(names)
            }
            with self.subTest(partial=tuple(name for name, value in kwargs.items() if value is not None)):
                with self.assertRaises(self.renderer.DossierValidationError):
                    self.renderer.render_dossier_html(dossier, **kwargs)

        mutations = []
        changed_research = copy.deepcopy(research)
        changed_research["vacancies"][0]["title"] = "Changed fixture role"
        mutations.append((market, changed_research, alignment, "Changed fixture role"))
        changed_alignment = copy.deepcopy(alignment)
        changed_alignment["research_snapshot"] = "snap-market-sha256-" + "0" * 64
        mutations.append((market, research, changed_alignment, "0" * 64))
        for field, value in (
            ("source_research_snapshot", "snap-market-sha256-" + "1" * 64),
            ("source_executive_dossier_snapshot", "snap-dossier-sha256-" + "2" * 64),
        ):
            changed_market = copy.deepcopy(market)
            changed_market[field] = value
            mutations.append((changed_market, research, alignment, value))
        changed_market = copy.deepcopy(market)
        changed_market["matrix_rows"][0]["evidence_ids"] = ["E-999"]
        mutations.append((changed_market, research, alignment, "E-999"))
        changed_market = copy.deepcopy(market)
        changed_market["matrix_rows"][0]["cells"][1]["requirements"][0]["source_paraphrase"] = "Changed paraphrase."
        mutations.append((changed_market, research, alignment, "Changed paraphrase."))
        changed_market = copy.deepcopy(market)
        changed_market["vacancies"][0]["employer"] = "Changed employer"
        mutations.append((changed_market, research, alignment, "Changed employer"))

        for changed_market, changed_research, changed_alignment, sentinel in mutations:
            with self.subTest(sentinel=sentinel):
                with self.assertRaises(self.renderer.DossierValidationError) as context:
                    self.renderer.render_dossier_html(
                        dossier,
                        changed_market,
                        market_research=changed_research,
                        market_alignment=changed_alignment,
                    )
                self.assertNotIn(sentinel, "\n".join(context.exception.errors))


    def test_shipped_fixtures_have_complete_resolved_noninteractive_dom(self) -> None:
        for name in ("scenario-a-es.json", "scenario-c-en.json"):
            with self.subTest(name=name):
                dossier = json.loads((V2_FIXTURE_ROOT / name).read_text(encoding="utf-8"))
                rendered = self.renderer.render_dossier_html(dossier)
                audit = DossierDOMAudit()
                audit.feed(rendered)

                self.assertEqual(audit.tag_counts.get("h1"), 1)
                self.assertEqual(audit.tag_counts.get("main"), 1)
                self.assertEqual(audit.tag_counts.get("footer"), 1)
                self.assertEqual(len(audit.ids), len(set(audit.ids)))
                self.assertEqual(set(audit.references) - set(audit.ids), set())
                self.assertEqual(audit.classes.count("section-coverage-row"), 17)
                self.assertEqual(audit.classes.count("coach-priority-card"), 3)
                self.assertEqual(audit.classes.count("market-unavailable-card"), 1)
                self.assertNotIn('data-priority-card="true"', rendered)
                self.assertNotIn('class="timebox"', rendered)
                skip_links = [
                    attrs for tag, attrs in audit.start_tags
                    if tag == "a" and "skip-link" in (attrs.get("class") or "").split()
                ]
                self.assertEqual(len(skip_links), 1)
                self.assertEqual(skip_links[0].get("href"), "#main-content")
                main_targets = [attrs for tag, attrs in audit.start_tags if tag == "main"]
                self.assertEqual(len(main_targets), 1)
                self.assertEqual(main_targets[0].get("id"), "main-content")
                self.assertEqual(main_targets[0].get("tabindex"), "-1")
                self.assertEqual(audit.heading_levels[0], 1)
                self.assertEqual(set(audit.heading_levels), {1, 2, 3, 4})
                self.assertTrue(
                    all(
                        next_level <= level + 1
                        for level, next_level in zip(audit.heading_levels, audit.heading_levels[1:])
                    )
                )
                templates = re.findall(
                    r'<section class="coach-template"[^>]*>(.*?)</section>',
                    rendered,
                    re.DOTALL,
                )
                self.assertEqual(len(templates), 3)
                for template in templates:
                    self.assertNotRegex(
                        template,
                        r"<(?:a|button|input|select|textarea)\b",
                    )

    def test_chat_summary_asks_exactly_one_first_pending_authorization_question(self) -> None:
        summary = self.renderer.build_chat_summary(make_v2_dossier("es"))
        self.assertIn(
            "¿Autorizas inspeccionar en modo solo lectura la sección Nombre durante esta sesión?",
            summary,
        )
        self.assertNotIn("Certificaciones", summary)
        self.assertEqual(summary.count("¿Autorizas inspeccionar"), 1)
        self.assertNotIn(make_v2_dossier("es")["questions"][0]["question"], summary)
        self.assertLessEqual(len(summary.split()), 180)

        english = json.loads(
            (V2_FIXTURE_ROOT / "scenario-c-en.json").read_text(encoding="utf-8")
        )
        summary = self.renderer.build_chat_summary(english)
        self.assertIn(
            "Do you authorize read-only inspection of the Banner section during this session?",
            summary,
        )
        self.assertEqual(summary.count("Do you authorize read-only inspection"), 1)
        self.assertNotIn(
            "Do you authorize read-only inspection of the Name section during this session?",
            summary,
        )
        self.assertNotIn("Certifications", summary)
        self.assertLessEqual(len(summary.split()), 180)

    def test_chat_summary_executes_every_localized_section_question(self) -> None:
        renderer = load_renderer()
        for locale, questions in renderer.AUTHORIZATION_QUESTIONS.items():
            for section, expected in questions.items():
                with self.subTest(locale=locale, section=section):
                    dossier = make_v2_dossier(locale)
                    for row in dossier["section_coverage"]:
                        request = row.get("inspection_request")
                        if isinstance(request, dict):
                            row["reason"] = "inspection_declined"
                            request["decision"] = "declined_for_session"
                    target = next(row for row in dossier["section_coverage"] if row["section"] == section)
                    scope = dossier["evidence_scope"]
                    scope["inspected_sections"] = [name for name in scope["inspected_sections"] if name != section]
                    target.update({
                        "availability": "unavailable",
                        "evidence_state": "unknown",
                        "reason": "authorization_required",
                        "inspection_request": {
                            "access_type": "read_only_visible_section_inspection",
                            "decision": "pending_response",
                            "scope": "current_session_only",
                            "carry_forward": False,
                        },
                    })
                    summary = renderer.build_chat_summary(dossier)
                    matches = [question for question in questions.values() if question in summary]
                    self.assertEqual(matches, [expected])
                    self.assertEqual(summary.count(expected), 1)

    def test_chat_summary_declined_and_failed_requests_keep_the_fallback_question(self) -> None:
        renderer = load_renderer()
        for locale in renderer.AUTHORIZATION_QUESTIONS:
            with self.subTest(locale=locale):
                dossier = make_v2_dossier(locale)
                for row in dossier["section_coverage"]:
                    request = row.get("inspection_request")
                    if isinstance(request, dict):
                        row["reason"] = "inspection_declined"
                        request["decision"] = "declined_for_session"
                failed = next(row for row in dossier["section_coverage"] if row["section"] == "featured")
                failed["reason"] = "authorized_inspection_failed"
                failed["inspection_request"]["decision"] = "authorized_inspection_failed"
                summary = renderer.build_chat_summary(dossier)
                self.assertIn(dossier["questions"][0]["question"], summary)
                self.assertFalse(any(question in summary for question in renderer.AUTHORIZATION_QUESTIONS[locale].values()))

    def test_chat_summary_retains_v1_behavior_when_no_inspection_request_is_pending(self) -> None:
        dossier = make_v2_dossier("en")
        for row in dossier["section_coverage"]:
            request = row.get("inspection_request")
            if isinstance(request, dict) and request["decision"] == "pending_response":
                row["reason"] = "inspection_declined"
                request["decision"] = "declined_for_session"
        summary = self.renderer.build_chat_summary(dossier)
        self.assertNotIn("Do you authorize read-only inspection", summary)
        self.assertIn(dossier["questions"][0]["question"], summary)

    def test_shipped_fixtures_are_valid_and_project_deep_equal_to_v1_sources(self) -> None:
        for name in ("scenario-a-es.json", "scenario-c-en.json"):
            with self.subTest(name=name):
                source = load_v1_fixture(name)
                dossier = json.loads((V2_FIXTURE_ROOT / name).read_text(encoding="utf-8"))
                self.assertEqual(self.validator.validate_dossier(dossier), [])
                self.assertEqual(self.validator.project_v2_to_v1(dossier), source)

    def test_shipped_fixture_ledger_uses_the_required_pending_and_declined_matrix(self) -> None:
        for name in ("scenario-a-es.json", "scenario-c-en.json"):
            with self.subTest(name=name):
                dossier = json.loads((V2_FIXTURE_ROOT / name).read_text(encoding="utf-8"))
                evidence_sections = {
                    record["profile_section"]
                    for record in dossier["evidence"]
                    if record["profile_section"] is not None
                }
                rows = {row["section"]: row for row in dossier["section_coverage"]}
                self.assertEqual(rows["featured"]["reason"], "authorization_required")
                self.assertEqual(rows["featured"]["inspection_request"]["decision"], "pending_response")
                self.assertEqual(rows["certifications"]["reason"], "inspection_declined")
                self.assertEqual(rows["certifications"]["inspection_request"]["decision"], "declined_for_session")
                self.assertEqual(dossier["analytics"]["state"], "not_requested")
                for section in CANONICAL_PROFILE_SECTIONS:
                    if section in evidence_sections or section == "certifications":
                        continue
                    self.assertEqual(rows[section]["availability"], "unavailable")
                    self.assertEqual(rows[section]["reason"], "authorization_required")
                    self.assertEqual(rows[section]["inspection_request"]["decision"], "pending_response")

    def test_writer_keeps_the_v2_artifact_private(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "dossier-v2.html"
            receipt = self.renderer.write_dossier_html(
                V2_FIXTURE_ROOT / "scenario-a-es.json", output
            )
            self.assertEqual(stat.S_IMODE(output.stat().st_mode), 0o600)
            self.assertEqual(receipt.artifact_type, "text/html")


    def test_writer_loads_complete_market_group_once_and_keeps_output_private(self) -> None:
        dossier, market, research, alignment = market_case(
            "complete-five-es.json", "scenario-a-es.json"
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = {}
            for name, value in (
                ("dossier", dossier),
                ("market", market),
                ("research", research),
                ("alignment", alignment),
            ):
                path = root / f"{name}.json"
                path.write_text(json.dumps(value), encoding="utf-8")
                paths[name] = path
            output = root / "dossier-with-market.html"
            receipt = self.renderer.write_dossier_html(
                paths["dossier"],
                output,
                market_dossier_path=paths["market"],
                market_research_path=paths["research"],
                market_alignment_path=paths["alignment"],
            )

            self.assertTrue(receipt.artifact_path.is_absolute())
            self.assertEqual(0o600, stat.S_IMODE(output.stat().st_mode))
            self.assertEqual(5, output.read_text(encoding="utf-8").count('class="vacancy-alignment-card"'))
            with self.assertRaises(FileExistsError):
                self.renderer.write_dossier_html(
                    paths["dossier"],
                    output,
                    market_dossier_path=paths["market"],
                    market_research_path=paths["research"],
                    market_alignment_path=paths["alignment"],
                )
            receipt = self.renderer.write_dossier_html(
                paths["dossier"],
                output,
                market_dossier_path=paths["market"],
                market_research_path=paths["research"],
                market_alignment_path=paths["alignment"],
                force=True,
            )
            self.assertTrue(receipt.artifact_path.is_absolute())
            self.assertTrue(os.path.samefile(output, receipt.artifact_path))

    def test_v3_writer_is_atomic_private_and_bypasses_public_recapture(self) -> None:
        arguments = semantic_v3_case("proof", "es")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths: dict[str, Path] = {}
            for name, value in arguments.items():
                if value is None:
                    continue
                path = root / f"{name}.json"
                path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
                paths[name] = path
            output = root / "v3.html"
            with mock.patch.object(
                self.renderer,
                "bounded_plain_snapshot",
                wraps=self.renderer.bounded_plain_snapshot,
            ) as snapshot, mock.patch.object(
                self.renderer,
                "_render_dossier_html_from_snapshot",
                wraps=self.renderer._render_dossier_html_from_snapshot,
            ) as internal_render, mock.patch.object(
                self.renderer,
                "render_dossier_html",
                side_effect=AssertionError("v3 writer must not recapture through public render"),
            ) as public_render:
                receipt = self.renderer.write_dossier_html(
                    paths["dossier"],
                    output,
                    market_dossier_path=paths["market_dossier"],
                    market_research_path=paths["market_research"],
                    learning_decision_path=paths["learning_decision"],
                    gap_response_path=paths["gap_response"],
                    gap_assessment_path=paths["gap_assessment"],
                    next_action_eligibility_path=paths["next_action_eligibility"],
                )
            self.assertEqual(1, snapshot.call_count)
            self.assertEqual(1, internal_render.call_count)
            public_render.assert_not_called()
            self.assertTrue(receipt.artifact_path.is_absolute())
            self.assertTrue(os.path.samefile(output, receipt.artifact_path))
            self.assertEqual(0o600, stat.S_IMODE(output.stat().st_mode))
            self.assertIn('class="card span-12 weekly-decision"', output.read_text(encoding="utf-8"))

    def test_v3_writer_hostile_loaded_values_are_captured_once_without_echo(self) -> None:
        arguments = semantic_v3_case("proof", "es")
        sentinel = "writer-v3-private-sentinel"
        names = (
            "dossier",
            "market_dossier",
            "market_research",
            "learning_decision",
            "gap_response",
            "gap_assessment",
            "next_action_eligibility",
        )
        wrapped = {
            name: OnePassMapping(arguments[name], sentinel)
            for name in names
        }

        def checked_internal(group: object) -> str:
            self.assertIs(type(group), dict)
            self.assertTrue(all(not isinstance(value, OnePassMapping) for value in group.values()))
            return "<html><body>safe v3</body></html>"

        def checked_summary(dossier: object) -> str:
            self.assertIs(type(dossier), dict)
            return "safe summary"

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "hostile.html"
            with mock.patch.object(
                self.renderer,
                "_load_plain_mapping",
                side_effect=[wrapped[name] for name in names],
            ) as loader, mock.patch.object(
                self.renderer,
                "bounded_plain_snapshot",
                wraps=self.renderer.bounded_plain_snapshot,
            ) as snapshot, mock.patch.object(
                self.renderer,
                "_render_dossier_html_from_snapshot",
                side_effect=checked_internal,
            ) as internal_render, mock.patch.object(
                self.renderer,
                "build_chat_summary",
                side_effect=checked_summary,
            ):
                self.renderer.write_dossier_html(
                    Path("dossier.json"),
                    output,
                    market_dossier_path=Path("market.json"),
                    market_research_path=Path("research.json"),
                    learning_decision_path=Path("learning.json"),
                    gap_response_path=Path("response.json"),
                    gap_assessment_path=Path("assessment.json"),
                    next_action_eligibility_path=Path("eligibility.json"),
                )
            self.assertEqual(1, snapshot.call_count)
            self.assertEqual(1, internal_render.call_count)
            self.assertEqual(len(names), loader.call_count)
            self.assertTrue(all(value.items_calls == 1 for value in wrapped.values()))
            self.assertNotIn(sentinel, output.read_text(encoding="utf-8"))

    def test_v3_writer_and_cli_reject_partial_or_crossed_groups_without_output(self) -> None:
        arguments = semantic_v3_case("proof", "es")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths: dict[str, Path] = {}
            for name, value in arguments.items():
                if value is None:
                    continue
                path = root / f"{name}.json"
                path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
                paths[name] = path
            field_paths = {
                "gap_response_path": paths["gap_response"],
                "gap_assessment_path": paths["gap_assessment"],
                "next_action_eligibility_path": paths["next_action_eligibility"],
                "learning_decision_path": paths["learning_decision"],
            }
            names = tuple(field_paths)
            for mask in range(1, (1 << len(names)) - 1):
                output = root / f"partial-{mask}.html"
                selected = {
                    name: field_paths[name] if mask & (1 << index) else None
                    for index, name in enumerate(names)
                }
                with self.subTest(mask=mask), self.assertRaises(
                    self.renderer.DossierValidationError
                ):
                    self.renderer.write_dossier_html(
                        paths["dossier"],
                        output,
                        market_dossier_path=paths["market_dossier"],
                        market_research_path=paths["market_research"],
                        **selected,
                    )
                self.assertFalse(output.exists())

            crossed = semantic_v3_case("selection_required", "es")
            crossed_path = root / "crossed-eligibility.json"
            crossed_path.write_text(
                json.dumps(crossed["next_action_eligibility"], ensure_ascii=False),
                encoding="utf-8",
            )
            crossed_output = root / "crossed.html"
            with self.assertRaises(self.renderer.DossierValidationError):
                self.renderer.write_dossier_html(
                    paths["dossier"],
                    crossed_output,
                    market_dossier_path=paths["market_dossier"],
                    market_research_path=paths["market_research"],
                    learning_decision_path=paths["learning_decision"],
                    gap_response_path=paths["gap_response"],
                    gap_assessment_path=paths["gap_assessment"],
                    next_action_eligibility_path=crossed_path,
                )
            self.assertFalse(crossed_output.exists())

            cli_output = root / "cli-partial.html"
            result = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(RENDERER_PATH),
                    str(paths["dossier"]),
                    "--output",
                    str(cli_output),
                    "--market-dossier",
                    str(paths["market_dossier"]),
                    "--market-research",
                    str(paths["market_research"]),
                    "--learning-decision",
                    str(paths["learning_decision"]),
                    "--gap-response",
                    str(paths["gap_response"]),
                ],
                cwd=root,
                capture_output=True,
                text=True,
                check=False,
                timeout=60,
            )
            self.assertEqual(2, result.returncode)
            self.assertFalse(cli_output.exists())
            self.assertNotIn(str(paths["gap_response"]), result.stderr)
            self.assertNotIn("Traceback", result.stderr)

    def test_writer_rejects_partial_market_path_group_before_creating_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "partial.html"
            with self.assertRaises(self.renderer.DossierValidationError):
                self.renderer.write_dossier_html(
                    V2_FIXTURE_ROOT / "scenario-a-es.json",
                    output,
                    market_dossier_path=MARKET_FIXTURE_ROOT / "complete-five-es.json",
                )
            self.assertFalse(output.exists())

    def test_writer_and_cli_reject_invalid_learning_before_creating_an_artifact(self) -> None:
        dossier, market, research, alignment, bundle = learning_case(
            "complete-five-es.json", "scenario-a-es.json", count=3
        )
        bundle["decisions"][0]["option_name"] = "Enroll now: example course"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = {}
            for name, value in (
                ("dossier", dossier),
                ("market", market),
                ("research", research),
                ("alignment", alignment),
                ("learning", bundle),
            ):
                path = root / f"{name}.json"
                path.write_text(json.dumps(value), encoding="utf-8")
                paths[name] = path
            writer_output = root / "writer.html"
            with self.assertRaises(self.renderer.DossierValidationError):
                self.renderer.write_dossier_html(
                    paths["dossier"], writer_output,
                    market_dossier_path=paths["market"],
                    market_research_path=paths["research"],
                    market_alignment_path=paths["alignment"],
                    learning_decision_path=paths["learning"],
                )
            self.assertFalse(writer_output.exists())
            cli_output = root / "cli.html"
            result = subprocess.run(
                [
                    sys.executable, "-B", str(RENDERER_PATH), str(paths["dossier"]),
                    "--market-dossier", str(paths["market"]),
                    "--market-research", str(paths["research"]),
                    "--market-alignment", str(paths["alignment"]),
                    "--learning-decision", str(paths["learning"]),
                    "--output", str(cli_output),
                ],
                cwd=root, capture_output=True, text=True, check=False, timeout=20,
            )
            self.assertEqual(2, result.returncode)
            self.assertFalse(cli_output.exists())

class ExecutiveCareerDossierV2LoadAndCliTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.validator = load_validator()

    def test_loader_uses_fixed_errors_for_malformed_private_inputs(self) -> None:
        cases = ((b'{"locale":"es","locale":"en"}', "duplicate JSON key"), (b'\xff', "v2 dossier must be valid UTF-8 JSON"), (b'[]', "v2 dossier must be a JSON object"))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for index, (raw, message) in enumerate(cases):
                with self.subTest(message=message):
                    path = root / f"case-{index}.json"
                    path.write_bytes(raw)
                    with self.assertRaisesRegex(self.validator.DossierLoadError, message):
                        self.validator.load_dossier(path)

    def test_loader_rejects_depth_size_fifo_and_symlinks(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            deep = root / "deep.json"; deep.write_text('{"a":' + "[" * 14 + "0" + "]" * 14 + "}", encoding="utf-8")
            with self.assertRaisesRegex(self.validator.DossierLoadError, "maximum nesting depth"):
                self.validator.load_dossier(deep)
            oversized = root / "large.json"; oversized.write_bytes(b" " * (256 * 1024 + 1))
            with self.assertRaisesRegex(self.validator.DossierLoadError, "256 KiB"):
                self.validator.load_dossier(oversized)
            target = root / "target.json"; target.write_text("{}", encoding="utf-8")
            link = root / "link.json"; link.symlink_to(target)
            with self.assertRaisesRegex(self.validator.DossierLoadError, "symlink"):
                self.validator.load_dossier(link)
            linked_parent = root / "linked-parent"; linked_parent.symlink_to(root, target_is_directory=True)
            with self.assertRaisesRegex(self.validator.DossierLoadError, "cannot read v2 dossier"):
                self.validator.load_dossier(linked_parent / "target.json")
            fifo = root / "input.fifo"; os.mkfifo(fifo)
            with self.assertRaisesRegex(self.validator.DossierLoadError, "cannot read v2 dossier"):
                self.validator.load_dossier(fifo)

    def test_cli_returns_bounded_non_echoing_diagnostics(self) -> None:
        for sentinel in ("person@example.test", "https://example.test/private", "/private/path.json", "line\nbreak", "ansi\x1b[31m", "bidi\u202evalue"):
            with self.subTest(sentinel=repr(sentinel)):
                dossier = make_v2_dossier()
                dossier[sentinel] = "bad"
                with tempfile.TemporaryDirectory() as directory:
                    path = Path(directory) / "invalid.json"
                    path.write_text(json.dumps(dossier), encoding="utf-8")
                    result = subprocess.run([sys.executable, "-B", str(VALIDATOR_PATH), str(path)], cwd=REPO_ROOT, text=True, capture_output=True, check=False)
                self.assertEqual(result.returncode, 2)
                self.assertTrue(result.stderr)
                self.assertLessEqual(len(result.stderr.encode("utf-8")), 16 * 1024)
                self.assertNotIn("Traceback", result.stderr)
                self.assertNotIn(sentinel, result.stderr)

    def test_cli_rejects_row_request_and_template_attacks_without_traceback(self) -> None:
        mutations = (
            ("row", "session_id", "opaque-session-value"),
            ("request", "authorization_granted", True),
            ("template", "field_keys", [{"x": "y"}]),
            ("template", "field_keys", [["context"]]),
        )
        for boundary, key, value in mutations:
            with self.subTest(boundary=boundary, key=key):
                dossier = make_v2_dossier()
                if boundary == "row":
                    dossier["section_coverage"][10][key] = value
                elif boundary == "request":
                    dossier["section_coverage"][10]["inspection_request"][key] = value
                else:
                    dossier["priorities"][0]["client_template"][key] = value
                with tempfile.TemporaryDirectory() as directory:
                    path = Path(directory) / "invalid.json"
                    path.write_text(json.dumps(dossier), encoding="utf-8")
                    result = subprocess.run([sys.executable, "-B", str(VALIDATOR_PATH), str(path)], cwd=REPO_ROOT, text=True, capture_output=True, check=False)
                self.assertEqual(result.returncode, 2)
                self.assertNotIn("Traceback", result.stderr)
                self.assertLessEqual(len(result.stderr.encode("utf-8")), 16 * 1024)

    def test_cli_rejects_unsafe_new_coaching_prose_with_fixed_non_echoing_diagnostics(self) -> None:
        for field, value, diagnostic in UNSAFE_COACHING_PROSE:
            with self.subTest(field=field, diagnostic=diagnostic):
                dossier = make_v2_dossier()
                dossier["priorities"][0][field] = value
                with tempfile.TemporaryDirectory() as directory:
                    path = Path(directory) / "unsafe.json"
                    path.write_text(json.dumps(dossier), encoding="utf-8")
                    result = subprocess.run(
                        [sys.executable, "-B", str(VALIDATOR_PATH), str(path)],
                        cwd=REPO_ROOT,
                        text=True,
                        capture_output=True,
                        check=False,
                    )
                self.assertEqual(result.returncode, 2)
                self.assertIn(f"priorities[0].{field} {diagnostic}", result.stderr)
                self.assertNotIn("Traceback", result.stderr)
                self.assertNotIn(value, result.stderr)
                self.assertLessEqual(len(result.stderr.encode("utf-8")), 16 * 1024)

    def test_cli_decoder_recursion_and_truncation_are_bounded(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            recursive = root / "recursive.json"
            recursive.write_text("[" * 1200 + "0" + "]" * 1200, encoding="utf-8")
            result = subprocess.run([sys.executable, "-B", str(VALIDATOR_PATH), str(recursive)], cwd=REPO_ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(result.returncode, 2)
            self.assertNotIn("Traceback", result.stderr)
            invalid = make_v2_dossier()
            invalid["section_coverage"] = [None] * 700
            path = root / "many-errors.json"
            path.write_text(json.dumps(invalid), encoding="utf-8")
            result = subprocess.run([sys.executable, "-B", str(VALIDATOR_PATH), str(path)], cwd=REPO_ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(result.returncode, 2)
            self.assertLessEqual(len(result.stderr.encode("utf-8")), 16 * 1024)
            self.assertIn("validation diagnostics truncated; additional errors omitted", result.stderr)

    def test_cli_accepts_a_valid_v2_dossier(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "valid.json"
            path.write_text(json.dumps(make_v2_dossier()), encoding="utf-8")
            result = subprocess.run([sys.executable, "-B", str(VALIDATOR_PATH), str(path)], cwd=REPO_ROOT, text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")

    def test_renderer_cli_accepts_all_market_flags_and_emits_one_private_receipt_line(self) -> None:
        dossier, _market, research, alignment = market_case(
            "complete-five-es.json", "scenario-a-es.json"
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            alignment_path = root / "alignment.json"
            alignment_path.write_text(json.dumps(alignment), encoding="utf-8")
            output = root / "rendered.html"
            result = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(RENDERER_PATH),
                    str(V2_FIXTURE_ROOT / "scenario-a-es.json"),
                    "--output",
                    str(output),
                    "--market-dossier",
                    str(MARKET_FIXTURE_ROOT / "complete-five-es.json"),
                    "--market-research",
                    str(RESEARCH_FIXTURE_ROOT / "complete-five-es.json"),
                    "--market-alignment",
                    str(alignment_path),
                ],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual(1, len(result.stdout.splitlines()))
            receipt = json.loads(result.stdout)
            self.assertTrue(Path(receipt["artifact_path"]).is_absolute())
            self.assertTrue(os.path.samefile(output, receipt["artifact_path"]))
            self.assertEqual(0o600, stat.S_IMODE(output.stat().st_mode))
            self.assertEqual(5, output.read_text(encoding="utf-8").count('class="vacancy-alignment-card"'))

            partial = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(RENDERER_PATH),
                    str(V2_FIXTURE_ROOT / "scenario-a-es.json"),
                    "--output",
                    str(root / "partial.html"),
                    "--market-research",
                    str(RESEARCH_FIXTURE_ROOT / "complete-five-es.json"),
                ],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(2, partial.returncode)
            self.assertFalse((root / "partial.html").exists())
            self.assertNotIn("Traceback", partial.stderr)

    def test_renderer_cli_accepts_complete_v3_group_and_writes_mode_600(self) -> None:
        arguments = semantic_v3_case("proof", "es")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths: dict[str, Path] = {}
            for name, value in arguments.items():
                if value is None:
                    continue
                path = root / f"{name}.json"
                path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
                paths[name] = path
            output = root / "v3-cli.html"
            result = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(RENDERER_PATH),
                    str(paths["dossier"]),
                    "--output",
                    str(output),
                    "--market-dossier",
                    str(paths["market_dossier"]),
                    "--market-research",
                    str(paths["market_research"]),
                    "--learning-decision",
                    str(paths["learning_decision"]),
                    "--gap-response",
                    str(paths["gap_response"]),
                    "--gap-assessment",
                    str(paths["gap_assessment"]),
                    "--next-action-eligibility",
                    str(paths["next_action_eligibility"]),
                ],
                cwd=root,
                text=True,
                capture_output=True,
                check=False,
                timeout=180,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual(1, len(result.stdout.splitlines()))
            self.assertEqual(0o600, stat.S_IMODE(output.stat().st_mode))
            self.assertIn(
                'class="card span-12 weekly-decision"',
                output.read_text(encoding="utf-8"),
            )
