#!/usr/bin/env python3
"""Build one deterministic, vacancy-bound private application packet."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any


def _sibling(name: str) -> Any:
    path = Path(__file__).with_name(name)
    specification = importlib.util.spec_from_file_location(f"_pgc_{path.stem}", path)
    if specification is None or specification.loader is None:
        raise RuntimeError("private vacancy packet dependency is unavailable")
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


_snapshot = _sibling("semantic_provenance_snapshot.py")
_eligibility_validator = _sibling("validate_career_next_action_eligibility_v1.py")
_fact_validator = _sibling("validate_candidate_fact_matrix_v1.py")
_research_validator = _sibling("validate_target_vacancy_research.py")
_prose_safety = _sibling("private_prose_safety.py")

SCHEMA_VERSION = "private-vacancy-application-packet-v1"
_SOURCE_FIELDS = frozenset({"eligibility_group", "candidate_fact_group"})
_ELIGIBILITY_FIELDS = frozenset(
    {
        "eligibility",
        "research",
        "executive_dossier",
        "market_dossier",
        "gap_response",
        "gap_assessment",
        "provider_research",
    }
)
_FACT_FIELDS = frozenset({"candidate_fact_matrix", "source_group"})
_REQUIREMENT_CATALOG = frozenset(
    {
        "authentication",
        "certificate_management",
        "incident_response",
        "key_rotation",
        "kubernetes",
        "linux",
        "observability",
        "python",
        "terraform",
    }
)
_GATE_CATALOG = frozenset(
    {
        "work_authorization",
        "country_geography",
        "work_arrangement",
        "language",
        "seniority",
        "experience_floor",
        "employment_arrangement",
    }
)
_EVIDENCE_ORDER = {"unknown": 0, "inferred": 1, "candidate_reported": 2, "verified": 3}
_PRIORITY = {
    "must_have": "required",
    "preferred": "preferred",
    "responsibility_only": "contextual",
}
_PROHIBITED_ACTIONS = [
    "external_edit",
    "upload",
    "export",
    "share",
    "submit",
    "publish",
    "message",
    "connect",
    "apply",
    "schedule",
    "calendar_create",
    "purchase",
    "enroll",
]
_EMAIL = re.compile(r"\b[^\s@]+@[^\s@]+\.[A-Za-z]{2,}\b")
_PHONE = re.compile(r"(?<![A-Za-z0-9])\+?\d[\d .()_-]{6,}\d(?![A-Za-z0-9])")
_HTML = re.compile(r"</?[A-Za-z][^>]{0,100}>")
_URL = re.compile(r"(?:https?://|www\.)", re.IGNORECASE)
_PRIVATE_ANALYTICS = re.compile(
    r"\b(?:profile views?|search appearances?|conversion rate|inbound contacts?|"
    r"visualizaciones?|apariciones? en b[uú]squedas?|tasa de conversi[oó]n)\b",
    re.IGNORECASE,
)
_SECRET_ASSIGNMENT = re.compile(
    r"\b(?:password|passwd|api[ _-]?key|access[ _-]?key|refresh[ _-]?token|"
    r"bearer[ _-]?token|client[ _-]?secret|private[ _-]?key)\s*[:=]\s*\S+",
    re.IGNORECASE,
)
_BEARER = re.compile(r"\bBearer\s+[A-Za-z0-9._~+/-]{8,}", re.IGNORECASE)
_PEM = re.compile(r"-----BEGIN(?: [A-Z0-9]+)* PRIVATE KEY-----", re.IGNORECASE)
_OPAQUE_SECRET = re.compile(
    r"\b(?:gh[pousr]_|sk-|AKIA|xox[baprs]-)[A-Za-z0-9._~+/-]{8,}",
    re.IGNORECASE,
)


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
_FACT_TYPE_LABELS = {
    "es": {
        "skill": "habilidad",
        "experience": "experiencia",
        "outcome": "resultado",
        "credential": "credencial",
        "portfolio_evidence": "evidencia de portafolio",
        "work_preference": "preferencia laboral",
        "constraint": "restricción",
    },
    "en": {
        "skill": "skill",
        "experience": "experience",
        "outcome": "outcome",
        "credential": "credential",
        "portfolio_evidence": "portfolio evidence",
        "work_preference": "work preference",
        "constraint": "constraint",
    },
}
_COPY = {
    "es": {
        "readiness": {
            "ready_for_manual_authorization": (
                "Listo para revisión manual privada",
                "Los requisitos obligatorios tienen afirmaciones respaldadas; cualquier acción externa sigue sin autorización.",
            ),
            "revise_first": (
                "Revisar antes de autorizar",
                "Falta evidencia utilizable o hay afirmaciones que deben revisarse u omitirse antes de una revisión privada final.",
            ),
            "stop": (
                "Detener preparación",
                "Una restricción verificada y vigente contradice una condición exacta de la vacante.",
            ),
        },
        "unsupported": {
            "missing_evidence": "Verificar evidencia privada o eliminar la afirmación.",
            "conflicting_evidence": "Resolver el conflicto privado antes de usar la afirmación.",
            "review_required": "Revisar la evidencia privada y confirmar su alcance.",
        },
        "review": {
            "use_high": "Usar solo tras la revisión manual privada.",
            "use_medium": "Usar con la etiqueta de evidencia reportada y revisión manual.",
            "revise_low": "Revisar la evidencia antes de redactar una afirmación.",
            "revise_unknown": "Resolver la evidencia conflictiva antes de redactar.",
            "omit_unknown": "Omitir hasta obtener evidencia utilizable.",
        },
        "handoff": {
            "available": "Indica la etapa de entrevista antes de entrar manualmente a la preparación.",
            "suppressed": "La preparación de entrevista permanece suprimida.",
        },
        "draft_templates": {
            "cv_bullets": "Evidencia privada de {fact_type} respalda {signal}; revisar antes de usar.",
            "recruiter_summary": "Resumen privado: {signals}, con evidencia de {fact_type}; revisar antes de usar.",
            "message_angle": "Ángulo privado: destacar {signal} con evidencia de {fact_type}; no enviar sin autorización.",
        },
    },
    "en": {
        "readiness": {
            "ready_for_manual_authorization": (
                "Ready for private manual review",
                "Required items have supported claims; every external action remains unauthorized.",
            ),
            "revise_first": (
                "Revise before authorization",
                "Usable evidence is missing or claims must be revised or omitted before final private review.",
            ),
            "stop": (
                "Stop preparation",
                "A verified current constraint contradicts an exact vacancy condition.",
            ),
        },
        "unsupported": {
            "missing_evidence": "Verify private evidence or remove the claim.",
            "conflicting_evidence": "Resolve the private conflict before using the claim.",
            "review_required": "Review the private evidence and confirm its scope.",
        },
        "review": {
            "use_high": "Use only after private manual review.",
            "use_medium": "Use with candidate-reported evidence labeling and manual review.",
            "revise_low": "Review the evidence before drafting a claim.",
            "revise_unknown": "Resolve conflicting evidence before drafting.",
            "omit_unknown": "Omit until usable evidence exists.",
        },
        "handoff": {
            "available": "State the interview stage before manually entering interview preparation.",
            "suppressed": "Interview preparation remains suppressed.",
        },
        "draft_templates": {
            "cv_bullets": "Private {fact_type} evidence supports {signal}; review before use.",
            "recruiter_summary": "Private summary: {signals}, supported by {fact_type} evidence; review before use.",
            "message_angle": "Private angle: highlight {signal} with {fact_type} evidence; do not send without authorization.",
        },
    },
}


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _digest(prefix: str, value: object) -> str:
    digest = hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()
    return f"{prefix}{digest}"


def _unsafe_visible_text(value: object) -> bool:
    if isinstance(value, Mapping):
        return any(_unsafe_visible_text(item) for item in value.values())
    if isinstance(value, list):
        return any(_unsafe_visible_text(item) for item in value)
    if not isinstance(value, str):
        return False
    return bool(
        _prose_safety.contains_unicode_controls(value)
        or _EMAIL.search(value)
        or _PHONE.search(value)
        or _HTML.search(value)
        or _URL.search(value)
        or _PRIVATE_ANALYTICS.search(value)
        or _SECRET_ASSIGNMENT.search(value)
        or _BEARER.search(value)
        or _PEM.search(value)
        or _OPAQUE_SECRET.search(value)
    )


def _validated_sources(
    frozen_group: Mapping[str, object],
) -> tuple[Mapping[str, object], Mapping[str, object], Mapping[str, object], Mapping[str, object]]:
    if set(frozen_group) != _SOURCE_FIELDS:
        raise ValueError("private vacancy application packet is invalid")
    eligibility_group = frozen_group["eligibility_group"]
    fact_group = frozen_group["candidate_fact_group"]
    if (
        not isinstance(eligibility_group, Mapping)
        or set(eligibility_group) != _ELIGIBILITY_FIELDS
        or not isinstance(fact_group, Mapping)
        or set(fact_group) != _FACT_FIELDS
    ):
        raise ValueError("private vacancy application packet is invalid")
    eligibility = eligibility_group["eligibility"]
    research = eligibility_group["research"]
    matrix = fact_group["candidate_fact_matrix"]
    raw_facts = fact_group["source_group"]
    if not all(isinstance(value, Mapping) for value in (eligibility, research, matrix, raw_facts)):
        raise ValueError("private vacancy application packet is invalid")
    if _eligibility_validator.validate_career_next_action_eligibility_v1(
        eligibility,
        research,
        eligibility_group["executive_dossier"],
        eligibility_group["market_dossier"],
        eligibility_group["gap_response"],
        eligibility_group["gap_assessment"],
        eligibility_group["provider_research"],
    ):
        raise ValueError("private vacancy application packet is invalid")
    if _fact_validator.validate_candidate_fact_matrix_v1(matrix, raw_facts):
        raise ValueError("private vacancy application packet is invalid")
    locale = eligibility.get("locale")
    if (
        locale not in _COPY
        or research.get("locale") != locale
        or matrix.get("locale") != locale
        or eligibility.get("as_of_date") != research.get("as_of_date")
        or eligibility.get("recommended_next_action") != "prepare_private_vacancy_packet"
        or _prose_safety.target_research_contains_candidate_identity(research)
    ):
        raise ValueError("private vacancy application packet is invalid")
    return eligibility_group, fact_group, eligibility, research


def _resolve_target(
    eligibility: Mapping[str, object], research: Mapping[str, object]
) -> tuple[Mapping[str, object], Mapping[str, object]]:
    selected_id = eligibility.get("selected_vacancy_id")
    vacancies = research.get("vacancies")
    employers = research.get("employers")
    if not isinstance(selected_id, str) or not isinstance(vacancies, list) or not isinstance(employers, list):
        raise ValueError("private vacancy application packet is invalid")
    matches = [
        row
        for row in vacancies
        if isinstance(row, Mapping)
        and row.get("vacancy_id") == selected_id
        and row.get("source_state") == "active"
    ]
    if len(matches) != 1:
        raise ValueError("private vacancy application packet is invalid")
    vacancy = matches[0]
    employer_matches = [
        row
        for row in employers
        if isinstance(row, Mapping) and row.get("employer_id") == vacancy.get("employer_id")
    ]
    requirements = vacancy.get("requirements")
    gates = vacancy.get("eligibility_gates")
    if (
        len(employer_matches) != 1
        or not isinstance(requirements, list)
        or not 1 <= len(requirements) <= 30
        or not isinstance(gates, list)
        or not 1 <= len(gates) <= 7
    ):
        raise ValueError("private vacancy application packet is invalid")
    gate_tokens = [row.get("gate") for row in gates if isinstance(row, Mapping)]
    if (
        len(gate_tokens) != len(gates)
        or any(token not in _GATE_CATALOG for token in gate_tokens)
        or len(gate_tokens) != len(set(gate_tokens))
    ):
        raise ValueError("private vacancy application packet is invalid")
    visible = {
        "vacancy_title": vacancy.get("title"),
        "organization_label": employer_matches[0].get("display_name"),
    }
    if any(not isinstance(value, str) or _unsafe_visible_text(value) for value in visible.values()):
        raise ValueError("private vacancy application packet is invalid")
    return vacancy, employer_matches[0]


def _matches(facts: list[Mapping[str, object]], signal: str) -> list[Mapping[str, object]]:
    if signal not in _REQUIREMENT_CATALOG:
        return []
    result: list[Mapping[str, object]] = []
    for row in facts:
        if row.get("confidentiality") == "forbidden" or row.get("conflict_state") == "superseded":
            continue
        bindings = row.get("signal_bindings")
        if isinstance(bindings, list) and any(
            isinstance(binding, Mapping)
            and binding.get("kind") == "requirement"
            and binding.get("signal") == signal
            for binding in bindings
        ):
            result.append(row)
    return result


def _admissible(row: Mapping[str, object]) -> bool:
    return (
        row.get("confidentiality") == "usable"
        and row.get("conflict_state") == "clear"
        and row.get("signal_relation") == "supports"
        and row.get("evidence_state") in {"verified", "candidate_reported"}
    )


def _coverage(matches: list[Mapping[str, object]]) -> tuple[str, str]:
    if not matches:
        return "missing", "unknown"
    supports = [row for row in matches if row.get("signal_relation") == "supports"]
    contradicts = [row for row in matches if row.get("signal_relation") == "contradicts"]
    if (
        any(row.get("conflict_state") == "conflicting" for row in matches)
        or any(row.get("evidence_state") == "verified" for row in contradicts)
        or (supports and contradicts)
    ):
        return "conflicting", "unknown"
    admissible = [row for row in matches if _admissible(row)]
    adverse = any(
        row.get("evidence_state") in {"inferred", "unknown"}
        or row.get("confidentiality") == "review_required"
        or row.get("signal_relation") == "unknown"
        for row in matches
    )
    if admissible and not adverse and all(
        row.get("evidence_state") == "verified"
        and row.get("confidentiality") == "usable"
        and row.get("conflict_state") == "clear"
        and row.get("signal_relation") == "supports"
        for row in matches
    ):
        return "supported", "high"
    if admissible and not adverse and all(
        row.get("evidence_state") in {"verified", "candidate_reported"}
        and row.get("confidentiality") == "usable"
        and row.get("conflict_state") == "clear"
        and row.get("signal_relation") == "supports"
        for row in matches
    ) and any(row.get("evidence_state") == "candidate_reported" for row in matches):
        return "supported", "medium"
    if admissible and adverse:
        return "partial", "low"
    if not admissible and (
        adverse
        or any(row.get("evidence_state") != "verified" for row in contradicts)
    ):
        return "review_required", "low"
    raise ValueError("private vacancy application packet is invalid")


def _weakest(rows: list[Mapping[str, object]]) -> str:
    return min(
        (str(row["evidence_state"]) for row in rows),
        key=lambda state: _EVIDENCE_ORDER[state],
    )


def _draft_text(
    locale: str,
    surface: str,
    fact_type: str,
    signals: list[str],
) -> str:
    template = _COPY[locale]["draft_templates"][surface]
    fact_label = _FACT_TYPE_LABELS[locale][fact_type]
    labels = [_SIGNAL_LABELS[locale][signal] for signal in signals]
    separator = ", " if locale == "en" else ", "
    return template.format(
        fact_type=fact_label,
        signal=labels[0],
        signals=separator.join(labels),
    )


def _project_requirement_rows(
    requirements: list[Mapping[str, object]], facts: list[Mapping[str, object]]
) -> tuple[list[dict[str, object]], dict[str, list[Mapping[str, object]]]]:
    rows: list[dict[str, object]] = []
    match_index: dict[str, list[Mapping[str, object]]] = {}
    for requirement in requirements:
        requirement_id = requirement.get("requirement_id")
        signal = requirement.get("signal")
        importance = requirement.get("importance")
        if (
            not isinstance(requirement_id, str)
            or not isinstance(signal, str)
            or importance not in _PRIORITY
        ):
            raise ValueError("private vacancy application packet is invalid")
        exact_matches = _matches(facts, signal)
        coverage, confidence = _coverage(exact_matches)
        match_index[requirement_id] = exact_matches
        rows.append(
            {
                "requirement_id": requirement_id,
                "signal": signal,
                "priority": _PRIORITY[importance],
                "fact_ids": [row["fact_id"] for row in exact_matches],
                "coverage": coverage,
                "confidence": confidence,
            }
        )
    return rows, match_index


def _project_drafts(
    locale: str,
    eligibility: Mapping[str, object],
    requirement_rows: list[dict[str, object]],
    match_index: Mapping[str, list[Mapping[str, object]]],
    facts: list[Mapping[str, object]],
) -> dict[str, list[dict[str, object]]]:
    supported = [row for row in requirement_rows if row["coverage"] == "supported"]
    first_fact = {
        row["requirement_id"]: next(
            fact_row
            for fact_row in match_index[row["requirement_id"]]
            if _admissible(fact_row)
        )
        for row in supported
    }
    cv_rows: list[dict[str, object]] = []
    for row in supported[:20]:
        selected_fact = first_fact[row["requirement_id"]]
        cv_rows.append(
            {
                "draft_id": f"D-CV-{len(cv_rows) + 1:03d}",
                "text": _draft_text(
                    locale,
                    "cv_bullets",
                    str(selected_fact["fact_type"]),
                    [str(row["signal"])],
                ),
                "fact_ids": [selected_fact["fact_id"]],
                "requirement_ids": [row["requirement_id"]],
                "evidence_state": selected_fact["evidence_state"],
            }
        )
    required_supported = [row for row in supported if row["priority"] == "required"][:5]
    recruiter_rows: list[dict[str, object]] = []
    if required_supported:
        selected = [first_fact[row["requirement_id"]] for row in required_supported]
        selected_ids = {row["fact_id"] for row in selected}
        selected_in_fact_order = [row for row in facts if row["fact_id"] in selected_ids]
        recruiter_rows.append(
            {
                "draft_id": "D-RS-001",
                "text": _draft_text(
                    locale,
                    "recruiter_summary",
                    str(selected[0]["fact_type"]),
                    [str(row["signal"]) for row in required_supported],
                ),
                "fact_ids": [row["fact_id"] for row in selected_in_fact_order],
                "requirement_ids": [row["requirement_id"] for row in required_supported],
                "evidence_state": _weakest(selected_in_fact_order),
            }
        )
    message_rows: list[dict[str, object]] = []
    if supported:
        selected_signal = eligibility.get("selected_signal")
        preferred = next(
            (row for row in supported if row["signal"] == selected_signal),
            None,
        )
        if preferred is None:
            preferred = next(
                (row for row in supported if row["priority"] == "required"),
                supported[0],
            )
        selected_fact = first_fact[preferred["requirement_id"]]
        message_rows.append(
            {
                "draft_id": "D-MA-001",
                "text": _draft_text(
                    locale,
                    "message_angle",
                    str(selected_fact["fact_type"]),
                    [str(preferred["signal"])],
                ),
                "fact_ids": [selected_fact["fact_id"]],
                "requirement_ids": [preferred["requirement_id"]],
                "evidence_state": selected_fact["evidence_state"],
            }
        )
    return {
        "cv_bullets": cv_rows,
        "recruiter_summary": recruiter_rows,
        "message_angle": message_rows,
    }


def _project_claim_review(
    locale: str,
    drafts: Mapping[str, list[dict[str, object]]],
    requirement_rows: list[dict[str, object]],
    match_index: Mapping[str, list[Mapping[str, object]]],
) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    for surface in ("cv_bullets", "recruiter_summary", "message_angle"):
        for draft in drafts[surface]:
            evidence = draft["evidence_state"]
            confidence = "high" if evidence == "verified" else "medium"
            result.append(
                {
                    "claim_id": f"C-{len(result) + 1:03d}",
                    "draft_id": draft["draft_id"],
                    "fact_ids": list(draft["fact_ids"]),
                    "requirement_ids": list(draft["requirement_ids"]),
                    "decision": "use",
                    "confidence": confidence,
                    "review_note": _COPY[locale]["review"][f"use_{confidence}"],
                }
            )
    for row in requirement_rows:
        if row["priority"] != "required" or row["coverage"] == "supported":
            continue
        coverage = row["coverage"]
        if coverage == "missing":
            decision, confidence = "omit", "unknown"
        elif coverage == "conflicting":
            decision, confidence = "revise", "unknown"
        else:
            decision, confidence = "revise", "low"
        result.append(
            {
                "claim_id": f"C-{len(result) + 1:03d}",
                "draft_id": None,
                "fact_ids": [
                    match["fact_id"]
                    for match in match_index[row["requirement_id"]][:5]
                ],
                "requirement_ids": [row["requirement_id"]],
                "decision": decision,
                "confidence": confidence,
                "review_note": _COPY[locale]["review"][f"{decision}_{confidence}"],
            }
        )
    return result


def _gate_blockers(
    vacancy: Mapping[str, object], facts: list[Mapping[str, object]]
) -> list[str]:
    gates = vacancy["eligibility_gates"]
    result: list[str] = []
    for gate_row in gates:
        token = gate_row["gate"]
        blocked = any(
            row.get("fact_type") == "constraint"
            and row.get("signal_relation") == "contradicts"
            and row.get("evidence_state") == "verified"
            and row.get("conflict_state") == "clear"
            and any(
                binding.get("kind") == "eligibility_gate"
                and binding.get("signal") == token
                for binding in row.get("signal_bindings", ())
                if isinstance(binding, Mapping)
            )
            for row in facts
        )
        if blocked:
            result.append(token)
    return result


def _project_private_vacancy_packet_from_frozen(
    frozen_group: Mapping[str, object],
) -> dict[str, object]:
    eligibility_group, fact_group, eligibility, research = _validated_sources(frozen_group)
    vacancy, employer = _resolve_target(eligibility, research)
    matrix = fact_group["candidate_fact_matrix"]
    facts_value = matrix.get("facts")
    requirements_value = vacancy.get("requirements")
    if (
        not isinstance(facts_value, list)
        or not all(isinstance(row, Mapping) for row in facts_value)
        or not isinstance(requirements_value, list)
        or not all(isinstance(row, Mapping) for row in requirements_value)
    ):
        raise ValueError("private vacancy application packet is invalid")
    facts = list(facts_value)
    requirements = list(requirements_value)
    locale = str(eligibility["locale"])
    requirement_rows, match_index = _project_requirement_rows(requirements, facts)
    unsupported: list[dict[str, object]] = []
    reason_by_coverage = {
        "missing": "missing_evidence",
        "conflicting": "conflicting_evidence",
        "partial": "review_required",
        "review_required": "review_required",
    }
    for row in requirement_rows:
        if row["coverage"] == "supported":
            continue
        reason = reason_by_coverage[row["coverage"]]
        unsupported.append(
            {
                "requirement_id": row["requirement_id"],
                "signal": row["signal"],
                "reason": reason,
                "next_private_step": _COPY[locale]["unsupported"][reason],
            }
        )
    drafts = _project_drafts(locale, eligibility, requirement_rows, match_index, facts)
    claims = _project_claim_review(locale, drafts, requirement_rows, match_index)
    blocking_gates = _gate_blockers(vacancy, facts)
    blocking_requirements = [
        row["requirement_id"]
        for row in requirement_rows
        if row["priority"] == "required" and row["coverage"] != "supported"
    ]
    has_required_requirement = any(
        row["priority"] == "required" for row in requirement_rows
    )
    if blocking_gates:
        readiness_state = "stop"
        drafts = {"cv_bullets": [], "recruiter_summary": [], "message_angle": []}
        claims = []
    elif (
        blocking_requirements
        or not has_required_requirement
        or any(row["decision"] in {"revise", "omit"} for row in claims)
        or not any(drafts.values())
        or not any(row["decision"] == "use" for row in claims)
    ):
        readiness_state = "revise_first"
    else:
        readiness_state = "ready_for_manual_authorization"
    headline, rationale = _COPY[locale]["readiness"][readiness_state]
    revision_claim_ids = [
        row["claim_id"] for row in claims if row["decision"] in {"revise", "omit"}
    ]
    supported_rows = [row for row in requirement_rows if row["coverage"] == "supported"]
    supported_fact_ids = {
        fact_row["fact_id"]
        for row in supported_rows
        for fact_row in match_index[row["requirement_id"]]
        if _admissible(fact_row)
    }
    available_handoff = readiness_state == "ready_for_manual_authorization"
    handoff = {
        "state": "available" if available_handoff else "suppressed",
        "interview_stage": "unknown",
        "vacancy_id": vacancy["vacancy_id"],
        "requirement_ids": [row["requirement_id"] for row in supported_rows]
        if available_handoff
        else [],
        "fact_ids": [row["fact_id"] for row in facts if row["fact_id"] in supported_fact_ids]
        if available_handoff
        else [],
        "next_private_step": _COPY[locale]["handoff"][
            "available" if available_handoff else "suppressed"
        ],
    }
    stop = readiness_state == "stop"
    eligibility_artifact = eligibility_group["eligibility"]
    matrix_artifact = fact_group["candidate_fact_matrix"]
    source_snapshot = {
        "eligibility": _eligibility_validator.snapshot_for_career_next_action_eligibility_v1(
            eligibility_artifact
        ),
        "target_vacancy_research": _research_validator.snapshot_for_market_dossier(
            research
        ),
        "candidate_fact_matrix": _digest(
            "snap-candidate-fact-matrix-v1-sha256-", matrix_artifact
        ),
        "aggregate": _digest(
            "snap-private-vacancy-packet-sources-v1-sha256-",
            [eligibility_artifact, research, matrix_artifact],
        ),
    }
    packet = {
        "schema_version": SCHEMA_VERSION,
        "locale": locale,
        "as_of_date": eligibility["as_of_date"],
        "target_binding": {
            "vacancy_id": vacancy["vacancy_id"],
            "vacancy_title": vacancy["title"],
            "organization_label": employer["display_name"],
            "eligibility_state": eligibility["state"],
            "next_safe_action": "prepare_private_vacancy_packet",
        },
        "readiness": {
            "state": readiness_state,
            "headline": headline,
            "rationale": rationale,
            "blocking_requirement_ids": blocking_requirements,
            "blocking_gate_tokens": blocking_gates,
            "revision_claim_ids": revision_claim_ids,
            "manual_review_required": True,
            "external_action_authorized": False,
        },
        "requirement_evidence": requirement_rows,
        "unsupported_or_missing_claims": unsupported,
        "draft_materials": drafts,
        "claim_review": claims,
        "first_interview_prep_handoff": handoff,
        "tracking_proposal": {
            "record_state": "not_proposed" if stop else "proposed",
            "event_kind": "none" if stop else "application_packet_drafted",
            "vacancy_id": vacancy["vacancy_id"],
            "outcome_state": "not_started" if stop else "draft_only",
            "manual_reentry_required": True,
            "auto_start": False,
        },
        "approval_boundary": {
            "artifact_state": "private_draft",
            "allowed_next_step": "manual_private_review",
            "prohibited_actions": list(_PROHIBITED_ACTIONS),
            "authorization_required": True,
        },
        "source_snapshot": source_snapshot,
    }
    if _unsafe_visible_text(
        {
            "target": packet["target_binding"],
            "readiness": packet["readiness"],
            "unsupported": packet["unsupported_or_missing_claims"],
            "drafts": packet["draft_materials"],
            "claims": packet["claim_review"],
            "handoff": packet["first_interview_prep_handoff"],
        }
    ):
        raise ValueError("private vacancy application packet is invalid")
    return packet


def build_private_vacancy_application_packet_v1(source_group: object) -> dict[str, object]:
    """Capture one composite once and emit its closed packet projection."""
    try:
        frozen = _snapshot.bounded_plain_snapshot(source_group)
        return _project_private_vacancy_packet_from_frozen(frozen)
    except Exception:
        raise ValueError("private vacancy application packet is invalid") from None
