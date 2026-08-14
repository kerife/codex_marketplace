#!/usr/bin/env python3
"""Validate closed, identity-free current-vacancy research snapshots."""
from __future__ import annotations

import argparse
import calendar
import datetime as dt
import hashlib
import importlib.util
import json
import re
import sys
import unicodedata
from collections.abc import Mapping
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit


def _sibling(name: str) -> Any:
    path = Path(__file__).with_name(name)
    specification = importlib.util.spec_from_file_location(f"_pgc_{path.stem}", path)
    if specification is None or specification.loader is None:
        raise RuntimeError("required research validator dependency is unavailable")
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


_loader = _sibling("private_input_loader.py")
_prose = _sibling("private_prose_safety.py")
_linkedin_safety = _sibling("validate_linkedin_client_report.py")

PrivateInputError = _loader.PrivateInputError
read_bounded_bytes = _loader.read_bounded_bytes
format_bounded_diagnostics = _prose.format_bounded_diagnostics
contains_unicode_controls = _prose.contains_unicode_controls
validate_secondary_source_url = _linkedin_safety.validate_secondary_source_url

SCHEMA_VERSION = "target-vacancy-research-v1"
TOP_FIELDS = frozenset({"schema_version", "research_kind", "locale", "as_of_date", "search_scope", "state", "search_limit", "employers", "vacancies", "privacy_boundary", "no_external_action"})
SEARCH_SCOPE_FIELDS = frozenset({"geography_scope", "target_role_families", "maximum_vacancies", "distinct_employers_preferred", "official_sources_first", "linkedin_jobs_backup_allowed", "no_eligibility_inference"})
SEARCH_LIMIT_FIELDS = frozenset({"bounded_queries_run", "limit_reason", "distinct_employer_search_exhausted", "limitation"})
EMPLOYER_FIELDS = frozenset({"employer_id", "display_name", "qualification_type", "qualification_observation", "official_source_title", "official_source_url", "source_date", "access_date"})
VACANCY_FIELDS = frozenset({"vacancy_id", "duplicate_fingerprint", "employer_id", "title", "role_family", "location", "arrangement", "geographic_compatibility", "source_kind", "source_url", "official_referrer_url", "source_state", "access_date", "publication_date", "freshness_status", "eligibility_gates", "requirements"})
REQUIREMENT_FIELDS = frozenset({"requirement_id", "signal", "importance", "source_paraphrase"})
GATE_FIELDS = frozenset({"gate", "state", "observed_condition"})
STATES = {"complete", "limited_market_evidence", "market_evidence_unavailable"}
ROLE_FAMILIES = {"site_reliability_engineering", "platform_engineering", "devops_engineering"}
SOURCE_KINDS = {"official_employer", "employer_operated_ats", "linkedin_jobs_backup"}
GATES = {"work_authorization", "country_geography", "work_arrangement", "language", "seniority", "experience_floor", "employment_arrangement"}
EMAIL = re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")
PHONE = re.compile(r"(?:^|\s)\+?\d[\d .()_-]{6,}\d(?:$|\s)")
HTML = re.compile(r"<\s*/?\s*(?:script|style|html|body|div|span|iframe|[a-z][a-z0-9-]*)\b", re.I)
UNKNOWN_INFERENCE = re.compile(r"(?:infer(?:red|ring)|inferid[oa]|inferencia)", re.I)
UNKNOWN_CONCLUSION = re.compile(r"\b(?:pass(?:ed)?|eligible|approved|qualif(?:y|ied)|aprobado|aprobada|elegible|cumple|califica|puede\s+trabajar)\b", re.I)
WORK_AUTHORIZATION_TARGET = r"(?:work\s+authori[sz]ation|eligibility|autorizacion\s+de\s+trabajo|elegibilidad(?:\s+laboral)?)"
UNKNOWN_GATE_STATUS_PREDICATES = {
    "pass": r"(?:confirm(?:s|ed)?|verif(?:y|ies|ied)|authori[sz](?:e|es|ed)|allow(?:s|ed)?|permit(?:s|ted)?|grant(?:s|ed)?|confirma|confirmo|confirmad[oa]|verifica|verifico|verificad[oa]|autoriza|autorizo|autorizad[oa]|permite|permitio|permitid[oa])",
    "blocked": r"(?:block(?:s|ed)?|den(?:y|ies|ied)|restrict(?:s|ed)?|prohibit(?:s|ed)?|ineligible|disqualif(?:y|ies|ied)|bloquea|bloqueo|bloquead[oa]|deniega|denego|denegad[oa]|restringe|restringio|restringid[oa]|prohibe|prohibio|prohibid[oa])",
}
UNKNOWN_GATE_NEUTRAL_REQUIREMENT = (
    re.compile(rf"(?:the\s+)?(?:listing|posting|role|vacancy)\s+(?:confirms?|confirmed|verif(?:y|ies|ied))\s+(?:that\s+)?(?:the\s+)?{WORK_AUTHORIZATION_TARGET}\s+(?:is|was)\s+(?:required|necessary)"),
    re.compile(rf"(?:la\s+)?(?:vacante|oferta|publicacion|posicion)\s+(?:confirma|confirmo|verifica|verifico)\s+que\s+(?:se\s+requiere\s+(?:la\s+)?{WORK_AUTHORIZATION_TARGET}|(?:la\s+)?{WORK_AUTHORIZATION_TARGET}\s+(?:es|era|resulta)\s+(?:requerid[oa]|necesari[oa]|obligatori[oa]))"),
)
UNKNOWN_GATE_STATUS_RELATIONS = {
    state: (
        re.compile(rf"\b{predicate}\b\s+(?:(?:the|la|el)\s+)?{WORK_AUTHORIZATION_TARGET}\b"),
        re.compile(rf"\b{WORK_AUTHORIZATION_TARGET}\b\s+(?:is|was|has\s+been|remains?|became|fue|ha\s+sido|queda|quedo|esta|se\s+considera)\s+\b{predicate}\b"),
    ) for state, predicate in UNKNOWN_GATE_STATUS_PREDICATES.items()
}
UNKNOWN_GATE_CANDIDATE_RELATIONS = {
    "pass": re.compile(rf"\b{UNKNOWN_GATE_STATUS_PREDICATES['pass']}\b\s+(?:that\s+|que\s+)?(?:(?:the|la|el)\s+)?(?:candidate|applicant|candidat[oa]|persona\s+candidata)\s+(?:is|was|es|era)\s+(?:eligible|elegible)\b"),
    "blocked": re.compile(rf"\b{UNKNOWN_GATE_STATUS_PREDICATES['blocked']}\b\s+(?:that\s+|que\s+)?(?:(?:the|la|el)\s+)?(?:candidate|applicant|candidat[oa]|persona\s+candidata)\s+(?:is|was|es|era)\s+(?:ineligible|inelegible)\b"),
}
CANDIDATE_REFERENCE = re.compile(r"\b(?:candidate|candidato(?:a)?|applicant|persona\s+candidata)\b", re.I)
PERSON_NAME = re.compile(r"\b[A-ZÁÉÍÓÚÑ][a-záéíóúñ]{1,}\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]{1,}\b")


class ResearchLoadError(ValueError):
    """Raised for safe, deterministic research-input failures."""


def _closed(value: object, fields: frozenset[str], errors: list[str], diagnostic: str) -> Mapping[str, object] | None:
    if not isinstance(value, Mapping):
        errors.append(diagnostic)
        return None
    if set(value) - fields:
        errors.append("research has unsupported fields")
    if fields - set(value):
        errors.append(diagnostic)
    return value


def _date(value: object) -> dt.date | None:
    if not isinstance(value, str):
        return None
    try:
        return dt.date.fromisoformat(value)
    except ValueError:
        return None


def _months_before(value: dt.date, months: int) -> dt.date:
    month_index = value.year * 12 + value.month - 1 - months
    year, zero_based_month = divmod(month_index, 12)
    month = zero_based_month + 1
    return dt.date(year, month, min(value.day, calendar.monthrange(year, month)[1]))


def _valid_text(value: object) -> bool:
    return isinstance(value, str) and 0 < len(value) <= 500


def _public_https_url(value: object) -> bool:
    try:
        return not validate_secondary_source_url(value)
    except (TypeError, ValueError):
        return False


def _source_url_is_allowed(kind: object, value: object) -> bool:
    if not _public_https_url(value) or not isinstance(value, str):
        return False
    try:
        parsed = urlsplit(value)
    except ValueError:
        return False
    host = (parsed.hostname or "").casefold().rstrip(".")
    path = parsed.path.casefold()
    linkedin_host = host == "linkedin.com" or host.endswith(".linkedin.com")
    if kind == "linkedin_jobs_backup":
        return host == "linkedin.com" and path.startswith("/jobs/")
    return kind in {"official_employer", "employer_operated_ats"} and not linkedin_host


def _scan_privacy(value: object) -> bool:
    if isinstance(value, Mapping):
        return any(_scan_privacy(item) for item in value.values())
    if isinstance(value, list):
        return any(_scan_privacy(item) for item in value)
    if not isinstance(value, str):
        return False
    phone_match = any(not re.fullmatch(r"\d{4}-\d{2}-\d{2}", match.group().strip()) for match in PHONE.finditer(value))
    return bool(contains_unicode_controls(value) or EMAIL.search(value) or phone_match or HTML.search(value))


def _candidate_identity_in_gates(value: object) -> bool:
    if isinstance(value, Mapping):
        for field in ("observed_condition", "source_paraphrase"):
            observed = value.get(field)
            if isinstance(observed, str) and (CANDIDATE_REFERENCE.search(observed) or PERSON_NAME.search(observed)):
                return True
        return any(_candidate_identity_in_gates(item) for item in value.values())
    if isinstance(value, list):
        return any(_candidate_identity_in_gates(item) for item in value)
    return False


def _normalized_text(value: object) -> str | None:
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split()) if isinstance(value, str) else None


def _unknown_gate_clause_state(value: str) -> str:
    folded = unicodedata.normalize("NFKD", value).casefold()
    folded = "".join(character for character in folded if not unicodedata.combining(character))
    for clause in re.split(r"[.!?;]+", " ".join(folded.split())):
        if not clause or any(pattern.fullmatch(clause) for pattern in UNKNOWN_GATE_NEUTRAL_REQUIREMENT):
            continue
        for state, patterns in UNKNOWN_GATE_STATUS_RELATIONS.items():
            if any(pattern.search(clause) for pattern in patterns):
                return state
        for state, pattern in UNKNOWN_GATE_CANDIDATE_RELATIONS.items():
            if pattern.search(clause):
                return state
    return "unknown"


def _normalized_source_url(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = urlsplit(value)
        host = (parsed.hostname or "").casefold().rstrip(".")
        return f"{host}{parsed.path.rstrip('/').casefold()}" if host else None
    except ValueError:
        return None


def _validate_scope(root: Mapping[str, object], errors: list[str]) -> None:
    scope = _closed(root.get("search_scope"), SEARCH_SCOPE_FIELDS, errors, "research has invalid search scope")
    if scope is None:
        return
    if scope.get("geography_scope") != "mexico_or_stated_remote":
        errors.append("research has invalid search scope")
    families = scope.get("target_role_families")
    if not isinstance(families, list) or len(families) != 3 or any(not isinstance(family, str) for family in families) or set(families) != ROLE_FAMILIES:
        errors.append("research has invalid search scope")
    for field, expected in (("maximum_vacancies", 5), ("distinct_employers_preferred", True), ("official_sources_first", True), ("linkedin_jobs_backup_allowed", True), ("no_eligibility_inference", True)):
        if scope.get(field) != expected:
            errors.append("research has invalid search scope")


def _validate_limit(root: Mapping[str, object], errors: list[str]) -> Mapping[str, object] | None:
    limit = _closed(root.get("search_limit"), SEARCH_LIMIT_FIELDS, errors, "research has invalid search limit")
    if limit is None:
        return None
    count = limit.get("bounded_queries_run")
    if not isinstance(count, int) or isinstance(count, bool) or not 0 <= count <= 1000:
        errors.append("research has invalid search limit")
    if limit.get("limit_reason") not in {"target_reached", "bounded_search_exhausted", "market_evidence_unavailable"} or not isinstance(limit.get("distinct_employer_search_exhausted"), bool) or not _valid_text(limit.get("limitation")):
        errors.append("research has invalid search limit")
    return limit


def _validate_employers(root: Mapping[str, object], as_of: dt.date | None, errors: list[str]) -> dict[str, str]:
    employers = root.get("employers")
    if not isinstance(employers, list) or len(employers) > 5:
        errors.append("research has invalid employers")
        return {}
    identifiers: set[str] = set(); identities: dict[str, str] = {}; names: dict[str, str] = {}; source_urls: dict[str, str] = {}
    for index, item in enumerate(employers):
        employer = _closed(item, EMPLOYER_FIELDS, errors, "research has invalid employer")
        if employer is None:
            continue
        identifier = employer.get("employer_id")
        if not isinstance(identifier, str) or not re.fullmatch(r"EMP-[0-9]{3}", identifier): errors.append("research has invalid employer")
        elif identifier in identifiers: errors.append("employers have duplicate IDs")
        else: identifiers.add(identifier)
        if employer.get("qualification_type") not in {"official_headcount", "official_index_membership"} or any(not _valid_text(employer.get(field)) for field in ("display_name", "qualification_observation", "official_source_title")):
            errors.append("research has invalid employer")
        if not _source_url_is_allowed("official_employer", employer.get("official_source_url")): errors.append("source URL violates source-kind policy")
        normalized_name, normalized_url = _normalized_text(employer.get("display_name")), _normalized_source_url(employer.get("official_source_url"))
        if normalized_name is not None and normalized_name in names: errors.append("employers have duplicate normalized identities")
        if normalized_url is not None and normalized_url in source_urls: errors.append("employers have duplicate normalized identities")
        identity = (names.get(normalized_name) if normalized_name is not None else None) or (source_urls.get(normalized_url) if normalized_url is not None else None) or f"employer-{index + 1}"
        if normalized_name is not None: names[normalized_name] = identity
        if normalized_url is not None: source_urls[normalized_url] = identity
        if isinstance(identifier, str) and normalized_name is not None: identities[identifier] = identity
        source_date, access_date = _date(employer.get("source_date")), _date(employer.get("access_date"))
        if source_date is None or access_date is None or (as_of is not None and (source_date > as_of or access_date != as_of)): errors.append("research has invalid employer dates")
        elif as_of is not None:
            qualification_type = employer.get("qualification_type")
            if (qualification_type == "official_headcount" and source_date < _months_before(as_of, 18)) or (qualification_type == "official_index_membership" and source_date != access_date):
                errors.append("employer qualification evidence is stale")
    if identifiers != {f"EMP-{index:03d}" for index in range(1, len(employers) + 1)}: errors.append("employer IDs must use the canonical sequence")
    return identities


def _validate_requirements(vacancy: Mapping[str, object], errors: list[str]) -> None:
    requirements, vacancy_id = vacancy.get("requirements"), vacancy.get("vacancy_id")
    if not isinstance(requirements, list) or not 1 <= len(requirements) <= 30:
        errors.append("research has invalid requirements"); return
    identifiers: set[str] = set(); signals: set[str] = set()
    for item in requirements:
        requirement = _closed(item, REQUIREMENT_FIELDS, errors, "research has invalid requirement")
        if requirement is None: continue
        identifier = requirement.get("requirement_id")
        if not isinstance(identifier, str) or not re.fullmatch(r"V-[0-9]{3}-R-[0-9]{2}", identifier) or (isinstance(vacancy_id, str) and not identifier.startswith(f"{vacancy_id}-R-")): errors.append("requirement ID must match its vacancy")
        elif identifier in identifiers: errors.append("requirements have duplicate IDs")
        else: identifiers.add(identifier)
        signal = requirement.get("signal")
        if not isinstance(signal, str) or not re.fullmatch(r"[a-z][a-z0-9_]{1,63}", signal): errors.append("requirement signal is invalid")
        elif signal in signals: errors.append("vacancy requirements have duplicate signals")
        else: signals.add(signal)
        if requirement.get("importance") not in {"must_have", "preferred", "responsibility_only"} or not _valid_text(requirement.get("source_paraphrase")): errors.append("research has invalid requirement")


def _validate_gates(vacancy: Mapping[str, object], errors: list[str]) -> None:
    gates = vacancy.get("eligibility_gates")
    if not isinstance(gates, list) or not 1 <= len(gates) <= len(GATES): errors.append("research has invalid eligibility gates"); return
    seen: set[str] = set()
    for item in gates:
        gate = _closed(item, GATE_FIELDS, errors, "research has invalid eligibility gate")
        if gate is None: continue
        kind, state, observed = gate.get("gate"), gate.get("state"), gate.get("observed_condition")
        if kind not in GATES or kind in seen: errors.append("research has invalid eligibility gate")
        elif isinstance(kind, str): seen.add(kind)
        if state not in {"pass", "blocked", "unknown"}: errors.append("eligibility gate state is invalid")
        if not _valid_text(observed): errors.append("research has invalid eligibility gate")
        elif state == "unknown" and _unknown_gate_clause_state(observed) != "unknown": errors.append("unknown eligibility gate cannot contain an eligibility conclusion")
        elif state == "unknown" and (UNKNOWN_INFERENCE.search(observed) or UNKNOWN_CONCLUSION.search(observed)): errors.append("unknown eligibility gate cannot infer a pass conclusion")


def _validate_vacancies(root: Mapping[str, object], as_of: dt.date | None, employer_identities: Mapping[str, str], limit: Mapping[str, object] | None, errors: list[str]) -> None:
    vacancies = root.get("vacancies")
    if not isinstance(vacancies, list) or len(vacancies) > 5: errors.append("research has invalid vacancies"); return
    vacancy_ids: set[str] = set(); fingerprints: set[str] = set(); employer_counts: dict[str, int] = {}; all_requirement_ids: set[str] = set()
    for item in vacancies:
        vacancy = _closed(item, VACANCY_FIELDS, errors, "research has invalid vacancy")
        if vacancy is None: continue
        identifier = vacancy.get("vacancy_id")
        if not isinstance(identifier, str) or not re.fullmatch(r"V-[0-9]{3}", identifier): errors.append("research has invalid vacancy")
        elif identifier in vacancy_ids: errors.append("vacancies have duplicate vacancy IDs")
        else: vacancy_ids.add(identifier)
        fingerprint = vacancy.get("duplicate_fingerprint")
        if not isinstance(fingerprint, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]{2,127}", fingerprint): errors.append("research has invalid vacancy")
        elif fingerprint in fingerprints: errors.append("vacancies have duplicate fingerprints")
        else: fingerprints.add(fingerprint)
        employer_id = vacancy.get("employer_id")
        if not isinstance(employer_id, str) or employer_id not in employer_identities: errors.append("vacancy must reference a listed employer")
        else:
            identity = employer_identities[employer_id]; employer_counts[identity] = employer_counts.get(identity, 0) + 1
        if any(not _valid_text(vacancy.get(field)) for field in ("title", "location")) or vacancy.get("role_family") not in ROLE_FAMILIES or vacancy.get("arrangement") not in {"onsite", "hybrid", "remote", "flexible"} or vacancy.get("geographic_compatibility") not in {"explicit_mexico", "stated_remote_unknown_eligibility"}: errors.append("research has invalid vacancy")
        if vacancy.get("source_state") != "active": errors.append("included vacancy source must be active")
        if vacancy.get("source_kind") not in SOURCE_KINDS or not _source_url_is_allowed(vacancy.get("source_kind"), vacancy.get("source_url")): errors.append("source URL violates source-kind policy")
        referrer = vacancy.get("official_referrer_url")
        if referrer is not None and not _source_url_is_allowed("official_employer", referrer): errors.append("source URL violates source-kind policy")
        access_date = _date(vacancy.get("access_date")); publication_date = _date(vacancy.get("publication_date")) if vacancy.get("publication_date") is not None else None
        if access_date is None or (as_of is not None and access_date != as_of): errors.append("included vacancy access date must match as_of_date")
        if vacancy.get("publication_date") is not None and publication_date is None: errors.append("research has invalid vacancy dates")
        if publication_date is not None and as_of is not None and publication_date > as_of: errors.append("publication date cannot be after as_of_date")
        if vacancy.get("freshness_status") not in {"current", "unknown"}: errors.append("research has invalid vacancy dates")
        if vacancy.get("freshness_status") == "current" and publication_date is None: errors.append("current freshness requires a publication date")
        _validate_requirements(vacancy, errors); _validate_gates(vacancy, errors)
        requirements = vacancy.get("requirements")
        if isinstance(requirements, list):
            for requirement in requirements:
                if isinstance(requirement, Mapping) and isinstance(requirement.get("requirement_id"), str):
                    requirement_id = requirement["requirement_id"]
                    if requirement_id in all_requirement_ids: errors.append("requirements have duplicate IDs")
                    all_requirement_ids.add(requirement_id)
    if any(count > 1 for count in employer_counts.values()) and (limit is None or limit.get("distinct_employer_search_exhausted") is not True): errors.append("repeated employers require exhausted search")
    if vacancy_ids != {f"V-{index:03d}" for index in range(1, len(vacancies) + 1)}: errors.append("vacancy IDs must use the canonical sequence")


def _validate_state_count(root: Mapping[str, object], limit: Mapping[str, object] | None, errors: list[str]) -> None:
    state, vacancies = root.get("state"), root.get("vacancies"); count = len(vacancies) if isinstance(vacancies, list) else -1
    valid = (state == "complete" and count == 5) or (state == "limited_market_evidence" and count in {1, 2, 3, 4}) or (state == "market_evidence_unavailable" and count == 0)
    if state not in STATES or not valid: errors.append("state does not match vacancy count")
    if limit is not None and limit.get("limit_reason") == "target_reached" and count != 5: errors.append("target_reached requires five vacancies")


def validate_research(value: object) -> list[str]:
    """Return fixed diagnostics without mutating the supplied snapshot."""
    if not isinstance(value, Mapping): return ["research must be an object"]
    try:
        errors: list[str] = []
        if set(value) - TOP_FIELDS: errors.append("research has unsupported fields")
        if TOP_FIELDS - set(value): errors.append("research is missing required fields")
        if value.get("schema_version") != SCHEMA_VERSION or value.get("research_kind") != "sre_platform_devops_current_vacancies" or value.get("locale") not in {"en", "es"} or value.get("privacy_boundary") != "public_vacancy_sources_and_identity_free_candidate_evidence_only" or value.get("no_external_action") is not True: errors.append("research has invalid contract fields")
        as_of = _date(value.get("as_of_date"))
        if as_of is None: errors.append("research has invalid as_of_date")
        _validate_scope(value, errors); limit = _validate_limit(value, errors); identities = _validate_employers(value, as_of, errors); _validate_vacancies(value, as_of, identities, limit, errors); _validate_state_count(value, limit, errors)
        if _scan_privacy(value) or _candidate_identity_in_gates(value): errors.append("research contains forbidden private or raw content")
        return sorted(set(errors))
    except (RecursionError, TypeError, ValueError):
        return ["research has malformed structure"]


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, nested in pairs:
        if key in result: raise ResearchLoadError("duplicate JSON key")
        result[key] = nested
    return result


def _assert_max_depth(value: object, maximum: int, depth: int = 0) -> None:
    if depth > maximum: raise ResearchLoadError("research exceeds maximum nesting depth")
    if isinstance(value, Mapping):
        for nested in value.values(): _assert_max_depth(nested, maximum, depth + 1)
    elif isinstance(value, list):
        for nested in value: _assert_max_depth(nested, maximum, depth + 1)


def load_research(path: Path) -> dict[str, object]:
    try:
        raw = read_bounded_bytes(path, 256 * 1024)
    except PrivateInputError as error:
        raise ResearchLoadError({"symlink": "research input must not be a symlink", "too_large": "research exceeds 256 KiB"}.get(error.reason, "cannot read research input")) from error
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object); _assert_max_depth(value, 12)
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError, ResearchLoadError) as error:
        if isinstance(error, ResearchLoadError): raise
        raise ResearchLoadError("research must be valid UTF-8 JSON") from error
    if not isinstance(value, dict): raise ResearchLoadError("research must be a JSON object")
    return value


def canonical_research_snapshot(value: Mapping[str, object]) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def snapshot_for_market_dossier(value: Mapping[str, object]) -> str:
    return f"snap-market-sha256-{canonical_research_snapshot(value)}"


def _cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a five-vacancy research snapshot.")
    parser.add_argument("research", type=Path)
    arguments = parser.parse_args(argv)
    try: research = load_research(arguments.research)
    except ResearchLoadError as error:
        print(str(error), file=sys.stderr); return 2
    errors = validate_research(research)
    if errors:
        sys.stderr.write(format_bounded_diagnostics(errors)); return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
