#!/usr/bin/env python3
"""Build one closed, identity-free learning proof sprint from validated sources."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any


_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))


def _sibling(name: str) -> Any:
    path = Path(__file__).with_name(name)
    module_name = path.stem if path.stem == "private_prose_safety" else f"_pgc_{path.stem}"
    specification = importlib.util.spec_from_file_location(module_name, path)
    if specification is None or specification.loader is None:
        raise RuntimeError("learning proof sprint dependency is unavailable")
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


_snapshot = _sibling("semantic_provenance_snapshot.py")
_prose_safety = _sibling("private_prose_safety.py")

SCHEMA_VERSION = "learning-proof-sprint-v1"
SNAPSHOT_PREFIX = "snap-learning-proof-sprint-sha256-"
PRIVACY_BOUNDARY = "candidate-owned-private-draft"
OUTCOME_BOUNDARY = "not_an_interview_offer_salary_or_roi_prediction"
REVIEW_MODEL = "daily_private_review_then_final_candidate_review"
PUBLICATION_GATE = (
    "exact_action_and_target_authorization_after_ownership_secrets_"
    "confidentiality_and_public_disclosure_review"
)
AUTHORIZATION_GATE = (
    "exact_action_and_target_authorization_before_publication_sharing_"
    "upload_or_message"
)

_INPUT_FIELDS = frozenset({"decision", "candidate_fact_matrix"})
_DECISION_SCHEMA_PATH = Path(__file__).parents[1] / "schemas" / "career-learning-decision-v3.schema.json"
_FACT_SCHEMA_PATH = Path(__file__).parents[1] / "schemas" / "candidate-fact-matrix-v1.schema.json"
_ARTIFACT_SCHEMA_PATH = Path(__file__).parents[1] / "schemas" / "learning-proof-sprint-v1.schema.json"
_SCHEMA_VALIDATION = _sibling("validate_json_schema_subset.py")
_ASSETS = ("linkedin", "application_packet", "interview")
_CANONICAL_TERMS = {
    "kubernetes": "Kubernetes",
    "linux": "Linux",
    "observability": "Observability",
    "python": "Python",
    "terraform": "Terraform",
}
_HANDOFFS = {
    "linkedin": "optimize-professional-profile",
    "application_packet": "optimize-career-assets",
    "interview": "prepare-role-interviews",
}
_EMAIL = re.compile(r"\b[^\s@]+@[^\s@]+\.[A-Za-z]{2,}\b")
_PHONE = re.compile(r"(?<![A-Za-z0-9])\+?\d[\d .()_-]{6,}\d(?![A-Za-z0-9])")
_HTML = re.compile(r"</?[A-Za-z][^>]{0,100}>")
_URL = re.compile(r"(?:https?://|www\.|file://)", re.IGNORECASE)
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
_SAFE_SNAPSHOT = re.compile(
    r"^snap-(?:alignment|dossier|gap-assessment-v1|gap-response-v1|market-dossier-v2|"
    r"next-action-eligibility-v1|market|candidate-facts|learning-proof-sprint)-sha256-"
    r"[0-9a-f]{64}$"
)
_IMPERATIVE_EXTERNAL_ACTION = re.compile(
    r"\b(?:send|submit|apply|publish|share|upload|message|connect|enroll|purchase|"
    r"register|schedule)\s+(?:now|immediately|the|this|a|an|it|application|"
    r"message|artifact|repo|repository|exam|ahora|inmediatamente|la|el|un|una|"
    r"solicitud|mensaje|artefacto|repositorio|examen|project|course|vacancy|"
    r"interview)\b|"
    r"\b(?:publica|publicar|env[ií]a|enviar|comparte|compartir|sube|subir)\s+"
    r"(?:ahora|inmediatamente|ya|el|la|un|una|este|esta|proyecto|artefacto|"
    r"repositorio|solicitud|mensaje)\b|"
    r"\b(?:aplica|aplicar)\s+(?:a|al)\s+(?:ahora|ya|la|el|una|un|vacante|"
    r"posición|puesto)\b|"
    r"\b(?:inscr[ií]bete|inscribirse)\s+(?:ahora|ya|al|en|curso|formación)\b|"
    r"\b(?:agenda|agendar)\s+(?:ahora|ya|la|una|entrevista|reunión)\b|"
    r"\b(?:publica|publicar|env[ií]a|enviar|comparte|compartir|sube|subir|"
    r"aplica|aplicar|inscr[ií]bete|inscribirse|agenda|agendar)"
    r"(?:\s+\S+){0,2}\s+(?:ahora|ya|inmediatamente)\b",
    re.IGNORECASE,
)
_OUTCOME_PROMISE = re.compile(
    r"\b(?:guarantee[sd]?|will get|likely to get|interview probability|"
    r"offer probability|salary increase|time-to-hire|ROI prediction|"
    r"aument(?:a|ar|ará)\s+(?:tu|el)\s+salario|mejora(?:r)?\s+(?:tu|el)\s+salario|"
    r"(?:increase|improve)\s+(?:your|the)\s+salary|probabilidad\s+de\s+entrevista|"
    r"entrevista(?:s)?\s+garantizada(?:s)?|"
    r"oferta(?:s)?\s+garantizada(?:s)?)\b",
    re.IGNORECASE,
)


def _schema(path: Path) -> Mapping[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, Mapping):
        raise ValueError("learning proof sprint is invalid")
    return value


def _validate_source_input(value: object) -> Mapping[str, object]:
    """Accept only one validated v3 proof decision plus one fact matrix.

    The caller cannot supply sprint rows.  They are derived below from these
    two closed source artifacts, which keeps vacancy/fact selectors source-bound.
    """
    if not isinstance(value, Mapping) or set(value) != _INPUT_FIELDS:
        raise ValueError("learning proof sprint is invalid")
    decision = value.get("decision")
    facts = value.get("candidate_fact_matrix")
    if (
        not isinstance(decision, Mapping)
        or _SCHEMA_VALIDATION.validate_schema_instance(decision, _schema(_DECISION_SCHEMA_PATH))
        or decision.get("locale") not in {"es", "en"}
        or decision.get("no_external_action") is not True
        or decision.get("outcome_boundary") != OUTCOME_BOUNDARY
        or _unsafe_tree(decision)
    ):
        raise ValueError("learning proof sprint is invalid")
    decisions = decision.get("decisions")
    if not isinstance(decisions, list) or len(decisions) != 1:
        raise ValueError("learning proof sprint is invalid")
    row = decisions[0]
    if (
        not isinstance(row, Mapping)
        or row.get("decision_code") != "build_bounded_proof"
        or row.get("gap_type") != "proof"
        or row.get("option_type") != "portfolio_project"
        or row.get("decision") != "do_now"
        or row.get("draft_only") is not True
        or row.get("no_external_action") is not True
        or row.get("outcome_boundary") != OUTCOME_BOUNDARY
    ):
        raise ValueError("learning proof sprint is invalid")
    if (
        not isinstance(facts, Mapping)
        or _SCHEMA_VALIDATION.validate_schema_instance(facts, _schema(_FACT_SCHEMA_PATH))
        or facts.get("locale") != decision.get("locale")
        or facts.get("case_scope") != "single_candidate"
        or _unsafe_tree(facts)
    ):
        raise ValueError("learning proof sprint is invalid")
    signals = row.get("source_signals")
    routes = row.get("signal_routes")
    requirements = row.get("requirement_ids")
    vacancies = row.get("vacancy_ids")
    if (
        not isinstance(signals, list) or len(signals) != 1 or not isinstance(signals[0], str)
        or not isinstance(routes, list) or len(routes) != 1 or not isinstance(routes[0], Mapping)
        or routes[0].get("signal") != signals[0]
        or not isinstance(requirements, list) or not requirements
        or not isinstance(vacancies, list) or len(vacancies) < 2
    ):
        raise ValueError("learning proof sprint is invalid")
    signal = signals[0]
    if _CANONICAL_TERMS.get(signal) != routes[0].get("term_label"):
        raise ValueError("learning proof sprint is invalid")
    all_facts = facts.get("facts", [])
    if not isinstance(all_facts, list):
        raise ValueError("learning proof sprint is invalid")
    fact_ids = [fact.get("fact_id") for fact in all_facts if isinstance(fact, Mapping)]
    if len(fact_ids) != len(all_facts) or len(fact_ids) != len(set(fact_ids)):
        raise ValueError("learning proof sprint is invalid")
    matching_facts = []
    for fact in all_facts:
        if not isinstance(fact, Mapping):
            continue
        bindings = fact.get("signal_bindings")
        if (
            isinstance(bindings, list)
            and any(isinstance(binding, Mapping) and binding.get("signal") == signal for binding in bindings)
            and fact.get("signal_relation") == "supports"
            and fact.get("conflict_state") == "clear"
            and fact.get("confidentiality") == "usable"
        ):
            matching_facts.append(fact)
    if not matching_facts:
        raise ValueError("learning proof sprint is invalid")
    if len(matching_facts) > 20:
        raise ValueError("learning proof sprint is invalid")
    return value


def _source_signal(source: Mapping[str, object]) -> tuple[Mapping[str, object], Mapping[str, object], str, str]:
    decision = source["decision"]
    facts = source["candidate_fact_matrix"]
    assert isinstance(decision, Mapping) and isinstance(facts, Mapping)
    row = decision["decisions"][0]
    assert isinstance(row, Mapping)
    signal = row["source_signals"][0]
    term = _CANONICAL_TERMS.get(
        str(signal), "señal objetivo" if decision["locale"] == "es" else "target signal"
    )
    return decision, row, str(signal), term


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _source_snapshot(group: Mapping[str, object]) -> str:
    digest = hashlib.sha256(_canonical_json(group).encode("utf-8")).hexdigest()
    return f"{SNAPSHOT_PREFIX}{digest}"


def _unsafe_text(value: object) -> bool:
    if not isinstance(value, str):
        return False
    return bool(
        _prose_safety.contains_unicode_controls(value)
        or _EMAIL.search(value)
        or _PHONE.search(value)
        or _HTML.search(value)
        or _URL.search(value)
        or _SECRET_ASSIGNMENT.search(value)
        or _BEARER.search(value)
        or _PEM.search(value)
        or _OPAQUE_SECRET.search(value)
        or _IMPERATIVE_EXTERNAL_ACTION.search(value)
        or _OUTCOME_PROMISE.search(value)
    )


def _unsafe_tree(value: object) -> bool:
    if isinstance(value, Mapping):
        return any(_unsafe_tree(item) for item in value.values())
    if isinstance(value, list):
        return any(_unsafe_tree(item) for item in value)
    if isinstance(value, str) and (
        re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value)
        or _SAFE_SNAPSHOT.fullmatch(value) is not None
    ):
        return False
    return _unsafe_text(value)


def _project_from_frozen(group: Mapping[str, object]) -> dict[str, object]:
    source = _validate_source_input(group)
    decision, row, signal, term = _source_signal(source)
    facts = source["candidate_fact_matrix"]
    assert isinstance(facts, Mapping)
    fact_ids = sorted(
        str(fact["fact_id"])
        for fact in facts["facts"]
        if isinstance(fact, Mapping)
        and any(
            isinstance(binding, Mapping) and binding.get("signal") == signal
            for binding in fact.get("signal_bindings", [])
        )
        and fact.get("signal_relation") == "supports"
        and fact.get("conflict_state") == "clear"
        and fact.get("confidentiality") == "usable"
    )
    candidate_id = "candidate-owned"
    vacancy_ids = list(row["vacancy_ids"])
    requirement_ids = list(row["requirement_ids"])
    source_decision = (
        "Decisión validada de prueba acotada basada en evidencia de vacante."
        if decision["locale"] == "es"
        else "Validated bounded-proof decision from vacancy-first evidence."
    )
    plan = {
        "plan_id": "LPS-PLAN-001",
        "kind": "learning_proof_sprint_plan",
        "candidate_id": candidate_id,
        "source_decision": source_decision,
        "sprint_goal": f"Produce a private reviewable proof artifact for {term}.",
        "target_gap": f"Demonstrable proof gap in {term}.",
        "deliverable": f"Candidate-owned {term} artifact with README, checks, decisions, and limitations.",
        "vacancy_ids": vacancy_ids,
        "candidate_fact_ids": fact_ids,
        "review_model": REVIEW_MODEL,
        "publication_gate": PUBLICATION_GATE,
        "outcome_boundary": OUTCOME_BOUNDARY,
        "draft_only": True,
        "no_external_action": True,
    }
    day_templates = (
        ("Frame the bounded scenario and evidence boundary.", "README scope and synthetic scenario.", "Candidate can name the requirement and supported fact without adding experience.", "Synthetic inputs only; no employer code, customer data, URLs, or credentials."),
        ("Build the smallest reproducible check for the signal.", "Reproducible check and observed result.", "The check maps to at least one supplied vacancy requirement.", "Keep the exercise local and isolated; do not import confidential material."),
        ("Document the decision and the rejected alternatives.", "Decision notes and tradeoff record.", "A reviewer can distinguish observed facts from bounded inference.", "Keep unknown scope explicit and avoid production ownership language."),
        ("Exercise the failure or limitation path.", "Failure note, rollback or limitation record.", "The artifact states what was not tested and why.", "No customer impact, employer system, secret, or outcome claim."),
        ("Package the private review handoff.", "Final README, evidence index, and review checklist.", "A candidate review can approve, revise, or omit each downstream claim.", "Remain private until ownership, confidentiality, disclosure, and exact authorization review."),
    )
    days = []
    for number, (goal, piece, proof, risk) in enumerate(day_templates, 1):
        days.append({
            "day_id": f"LPS-DAY-{number:03d}",
            "kind": "learning_proof_sprint_day",
            "candidate_id": candidate_id,
            "day_number": number,
            "daily_goal": goal,
            "artifact_piece": piece,
            "proof_check": proof,
            "risk_check": risk,
            "acceptance_test": "A private reviewer can inspect the stated boundary and reproduce the stated check.",
            "candidate_timebox": "2_hours",
            "owner": "candidate_with_coach_review" if number in {3, 5} else "candidate",
            "measurement_signal": f"day_{number}_ready_for_private_review",
            "next_safe_action": "Continue the private draft; no publication, upload, sharing, messaging, or scheduling.",
            "draft_only": True,
            "no_external_action": True,
        })
    handoff_copy = {
        "linkedin": ("README scope and decision notes", "Prepare a private profile-copy draft.", "Candidate-built artifact shows bounded reasoning.", "Do not claim production ownership or hiring impact.", "Ownership, secrets, confidentiality, public disclosure, and final copy review.", "Production ownership, employer material, private data, and outcome claims."),
        "application_packet": ("README, checks, limitation record, and decision notes", "Prepare one vacancy-specific proof bullet.", "Candidate-owned artifact aligns to supplied requirements.", "Do not replace work history or imply employer deployment.", "Truthfulness, ownership, link safety, and vacancy-specific claim review.", "Production outage ownership, private impact, compensation, and payback claims."),
        "interview": ("Scenario, action, result boundary, and decision notes", "Prepare a private troubleshooting proof story.", "Candidate can explain the lab scope and limitations.", "State clearly that this is candidate-owned practice.", "Fact grounding, red-line claims, and answer practice.", "Production incident command, SLO ownership, customer systems, and interview outcomes."),
    }
    reuse = []
    for number, asset in enumerate(_ASSETS, 1):
        artifacts, goal, safe, boundary, review, blocked = handoff_copy[asset]
        reuse.append({
            "reuse_id": f"LPS-REUSE-{number:03d}",
            "kind": "learning_evidence_reuse_map",
            "candidate_id": candidate_id,
            "target_asset": asset,
            "source_sprint_artifacts": artifacts.split(", "),
            "reuse_goal": goal,
            "safe_claim": safe,
            "proof_boundary": boundary,
            "required_review": review,
            "blocked_claims": blocked,
            "handoff_module": _HANDOFFS[asset],
            "acceptance_test": "The downstream draft cites the artifact boundary and keeps external action disabled.",
            "authorization_gate": AUTHORIZATION_GATE,
            "outcome_boundary": OUTCOME_BOUNDARY,
            "draft_only": True,
            "no_external_action": True,
        })
    projected = {
        "schema_version": SCHEMA_VERSION,
        "locale": decision["locale"],
        "case_scope": "single_candidate",
        "plan": plan,
        "days": days,
        "reuse_map": reuse,
        "source_snapshot": _source_snapshot(source),
        "privacy_boundary": PRIVACY_BOUNDARY,
        "outcome_boundary": OUTCOME_BOUNDARY,
        "draft_only": True,
        "no_external_action": True,
    }
    if _SCHEMA_VALIDATION.validate_schema_instance(projected, _schema(_ARTIFACT_SCHEMA_PATH)):
        raise ValueError("learning proof sprint is invalid")
    return projected


def build_learning_proof_sprint_v1(source_group: object) -> dict[str, object]:
    """Capture one bounded source group and project a deterministic sprint."""
    try:
        frozen = _snapshot.bounded_plain_snapshot(source_group)
        return _project_from_frozen(frozen)
    except Exception:
        raise ValueError("learning proof sprint is invalid") from None


def snapshot_for_learning_proof_sprint_v1(source_group: object) -> str:
    """Return the canonical raw-input binding for one valid sprint source group."""
    try:
        frozen = _snapshot.bounded_plain_snapshot(source_group)
        return _source_snapshot(_validate_source_input(frozen))
    except Exception:
        raise ValueError("learning proof sprint is invalid") from None
