#!/usr/bin/env python3
"""Validate the optional, identity-free career learning decision bundle."""

from __future__ import annotations

import datetime as dt
import importlib.util
import json
import re
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


def _sibling(name: str) -> Any:
    path = Path(__file__).with_name(name)
    spec = importlib.util.spec_from_file_location(f"_pgc_learning_{path.stem}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("learning dependency is unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_schema = _sibling("validate_json_schema_subset.py")
_loader = _sibling("private_input_loader.py")
_prose = _sibling("private_prose_safety.py")
_snapshot = _sibling("dossier_snapshot.py")
_research = _sibling("validate_target_vacancy_research.py")

SCHEMA = json.loads(
    (Path(__file__).resolve().parents[1] / "schemas" / "career-learning-decision-v1.schema.json").read_text(
        encoding="utf-8"
    )
)

class LearningBundleLoadError(ValueError):
    """A bounded learning bundle load failed without exposing input details."""

DECISION_FIELDS = frozenset(
    {
        "decision_rank",
        "target_role",
        "gap_type",
        "option_type",
        "option_name",
        "provider_or_owner",
        "source_gap_ids",
        "vacancy_ids",
        "market_evidence_state",
        "cost_time_band",
        "expected_signal_boundary",
        "portfolio_or_no_learning_alternative",
        "overbuying_risk",
        "decision",
        "decision_basis",
        "next_action_gate",
        "outcome_boundary",
        "draft_only",
        "no_external_action",
        "provider_source",
    }
)
PROVIDER_FIELDS = frozenset(
    {
        "provider",
        "option",
        "source_title",
        "source_date",
        "source_state",
        "url",
        "geography",
        "availability",
        "current_cost",
        "currency",
        "tax",
        "duration",
        "prerequisite",
        "renewal",
        "maintenance",
        "unknowns",
    }
)
TOP_FIELDS = frozenset(
    {
        "schema_version",
        "locale",
        "as_of_date",
        "source_market_snapshot",
        "source_dossier_snapshot",
        "source_research_snapshot",
        "state",
        "decisions",
        "privacy_boundary",
        "no_external_action",
        "outcome_boundary",
    }
)
_DATE_RE = re.compile(r"\A[0-9]{4}-[0-9]{2}-[0-9]{2}\Z")
_EVIDENCE_RE = re.compile(r"\AE-[0-9]{3}\Z")
_VACANCY_RE = re.compile(r"\AV-[0-9]{3}\Z")
_EMAIL_RE = re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")
_PHONE_RE = re.compile(r"(?:^|\s)\+?\d[\d .()_-]{6,}\d(?:$|\s)")
_HTML_RE = re.compile(r"<\s*/?\s*(?:script|style|html|body|div|span|iframe)\b", re.I)
_LOCAL_PATH_RE = re.compile(r"(?:file://|(?:^|\s)(?:/Users/|/private/|/tmp/|~/|[A-Za-z]:[\\/]))", re.I)
_PROFILE_URL_RE = re.compile(r"https?://(?:www\.)?linkedin\.com/(?:in|pub|profile|company)/", re.I)
_GENERIC_URL_RE = re.compile(
    r"\b(?:(?:https?://|www\.)\S+|(?:[a-z0-9-]+\.)+(?:com|org|net|io|dev|app|edu|gov|mx)(?:[/?#][^\s]*)?)",
    re.I,
)
_RAW_IDENTIFIER_RE = re.compile(
    r"\b(?:(?:profile|user)[ _-]?id|id[-_: ]?\d{3,}|[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\b",
    re.I,
)
_UNSAFE_ACTION_RE = re.compile(
    r"\b(?:"
    r"enroll\s+now|purchase\s+now|buy\s+(?:this\s+)?course|sign\s+up\s+now|apply\s+now"
    r"|(?:schedule|book)\s+(?:an?\s+)?(?:exam|interview)|contact\s+provider|publish\s+this\s+project|please\s+enroll"
    r"|(?:this\s+)?gets?\s+interviews?"
    r"|helps?\s+you\s+get\s+hired"
    r"|get\s+hired\s+faster"
    r"|land\s+an?\s+interview"
    r"|secure\s+an?\s+offer"
    r"|lead\s+to\s+an?\s+offer"
    r"|you\s+will\s+be\s+hired"
    r"|increase\s+your\s+salary"
    r"|hiring\s+success"
    r"|job\s+placement"
    r"|offer\s+after\s+completion"
    r"|employer\s+will\s+contact\s+you"
    r"|will\s+get|guarantee[sd]?|interview\s+probability|offer\s+probability|salary\s+increase|time[- ]to[- ]hire|return\s+on\s+investment"
    r")\b",
    re.I,
)
_SAFE_CANDIDATE_CONTEXT_RE = re.compile(
    r"\bcandidate(?:[- ]owned|[- ]safe| effort)\b", re.I
)
_MAX_NODES = 4096
_MAX_DEPTH = 64
_OFFICIAL_PROVIDER_DOMAINS = {
    "amazon": ("amazon.com", "aws.amazon.com"),
    "aws": ("amazon.com", "aws.amazon.com"),
    "cncf": ("cncf.io",),
    "coursera": ("coursera.org",),
    "datadog": ("datadoghq.com",),
    "edx": ("edx.org",),
    "google": ("google.com", "cloud.google.com"),
    "harvard": ("harvard.edu",),
    "hashicorp": ("hashicorp.com",),
    "kubernetes": ("kubernetes.io",),
    "linux foundation": ("linuxfoundation.org",),
    "linuxfoundation": ("linuxfoundation.org",),
    "microsoft": ("microsoft.com",),
    "red hat": ("redhat.com",),
    "redhat": ("redhat.com",),
    "terraform": ("hashicorp.com",),
}


def _bounded(errors: list[str]) -> list[str]:
    return sorted(set(errors))[:40]


def _closed(value: object, fields: frozenset[str], message: str, errors: list[str]) -> Mapping[str, object] | None:
    if not isinstance(value, Mapping):
        errors.append(message)
        return None
    try:
        keys = set(value)
    except (TypeError, ValueError, RecursionError):
        errors.append(message)
        return None
    if keys != fields:
        errors.append(message)
    return value


def _text(value: object, maximum: int = 1000) -> bool:
    return (
        isinstance(value, str)
        and 0 < len(value) <= maximum
        and not _EMAIL_RE.search(value)
        and not _HTML_RE.search(value)
        and not _LOCAL_PATH_RE.search(value)
        and not _PROFILE_URL_RE.search(value)
        and not _GENERIC_URL_RE.search(value)
        and not _RAW_IDENTIFIER_RE.search(value)
    )


def _text_has_identity_action_or_outcome_risk(value: object) -> bool:
    """Reject unsafe copy while retaining established candidate-owned technical phrasing."""
    if not isinstance(value, str):
        return True
    identity_candidate = _SAFE_CANDIDATE_CONTEXT_RE.sub("safe technical context", value)
    return bool(
        _prose.contains_candidate_identity(identity_candidate)
        or _UNSAFE_ACTION_RE.search(value)
    )


def _ids(value: object, pattern: re.Pattern[str], *, minimum: int = 1, maximum: int = 20) -> bool:
    if not isinstance(value, list) or not minimum <= len(value) <= maximum:
        return False
    seen: list[str] = []
    for item in value:
        if not isinstance(item, str) or pattern.fullmatch(item) is None or item in seen:
            return False
        seen.append(item)
    return True


def _unique(values: list[object]) -> bool:
    """Return whether values are unique without hashing malformed JSON values."""
    for index, value in enumerate(values):
        if any(value == prior for prior in values[:index]):
            return False
    return True


def _official_provider_url(provider: object, url: object) -> bool:
    if not isinstance(provider, str) or not isinstance(url, str):
        return False
    parsed = urlparse(url)
    host = (parsed.hostname or "").casefold().rstrip(".")
    try:
        port = parsed.port
    except ValueError:
        return False
    if parsed.scheme != "https" or not host or parsed.username or parsed.password or port:
        return False
    normalized_provider = re.sub(r"[^a-z0-9]+", " ", provider.casefold()).strip()
    domains = _OFFICIAL_PROVIDER_DOMAINS.get(normalized_provider)
    if domains is None:
        return False
    return any(host == domain or host.endswith("." + domain) for domain in domains)


def _date(value: object) -> bool:
    if not isinstance(value, str) or not _DATE_RE.fullmatch(value):
        return False
    try:
        dt.date.fromisoformat(value)
    except ValueError:
        return False
    return True


def _graph_flags(value: object) -> tuple[bool, bool]:
    """Return (cycle, over_limit) using bounded iterative traversal."""
    active: set[int] = set()
    stack: list[tuple[object, int, bool]] = [(value, 0, False)]
    nodes = 0
    cycle = False
    while stack:
        current, depth, leaving = stack.pop()
        if isinstance(current, (Mapping, list)):
            identifier = id(current)
            if leaving:
                active.discard(identifier)
                continue
            if identifier in active:
                cycle = True
                continue
            nodes += 1
            if nodes > _MAX_NODES or depth > _MAX_DEPTH:
                return cycle, True
            active.add(identifier)
            stack.append((current, depth, True))
            children = list(current.values()) if isinstance(current, Mapping) else list(current)
            stack.extend((child, depth + 1, False) for child in reversed(children))
    return cycle, False


def _private_or_unsafe_text(value: object) -> bool:
    cycle, over_limit = _graph_flags(value)
    if cycle or over_limit:
        return True
    stack: list[object] = [value]
    seen: set[int] = set()
    while stack:
        current = stack.pop()
        if isinstance(current, Mapping):
            identifier = id(current)
            if identifier in seen:
                continue
            seen.add(identifier)
            stack.extend(current.values())
        elif isinstance(current, list):
            identifier = id(current)
            if identifier in seen:
                continue
            seen.add(identifier)
            stack.extend(current)
        elif isinstance(current, str):
            phone_match = any(
                not _DATE_RE.fullmatch(match.group().strip())
                for match in _PHONE_RE.finditer(current)
            )
            if _prose.contains_unicode_controls(current) or _EMAIL_RE.search(current) or phone_match or _HTML_RE.search(current):
                return True
    return False


def _snapshot_errors(
    root: Mapping[str, object], market: Mapping[str, object], dossier: Mapping[str, object], research: Mapping[str, object], errors: list[str]
) -> None:
    try:
        expected_market = _snapshot.snapshot_for_dossier(market)
        expected_dossier = _snapshot.snapshot_for_dossier(dossier)
        expected_research = _research.snapshot_for_market_dossier(research)
    except (AttributeError, KeyError, RecursionError, TypeError, ValueError):
        errors.append("learning source snapshots are unavailable")
        return
    if root.get("source_market_snapshot") != expected_market:
        errors.append("learning market snapshot is stale")
    if root.get("source_dossier_snapshot") != expected_dossier:
        errors.append("learning dossier snapshot is stale")
    if root.get("source_research_snapshot") != expected_research:
        errors.append("learning research snapshot is stale")
    if root.get("locale") != market.get("locale") or root.get("locale") != dossier.get("locale") or root.get("locale") != research.get("locale"):
        errors.append("learning locale must match validated sources")
    dossier_date = dossier.get("evidence_as_of")
    if root.get("as_of_date") != market.get("as_of_date") or root.get("as_of_date") != research.get("as_of_date") or not _date(dossier_date) or dossier_date > root.get("as_of_date", ""):
        errors.append("learning date must match validated sources")


def _source_metadata(
    value: object, *, as_of_date: str, errors: list[str]
) -> None:
    source = _closed(value, PROVIDER_FIELDS, "provider source has invalid closed structure", errors)
    if source is None:
        return
    for field in ("provider", "option", "source_title", "geography", "availability", "current_cost", "currency", "tax", "duration", "prerequisite", "renewal", "maintenance", "unknowns"):
        if not _text(source.get(field)):
            errors.append("provider source has invalid metadata")
    if not _date(source.get("source_date")) or source.get("source_date") > as_of_date:
        errors.append("provider source date is invalid")
    if not isinstance(source.get("source_state"), str) or source.get("source_state") not in {"active", "unknown", "unavailable"}:
        errors.append("provider source state is invalid")
    if not isinstance(source.get("url"), str) or not _official_provider_url(source.get("provider"), source.get("url")) or len(source["url"]) > 500:
        errors.append("provider source URL is invalid")
    if source.get("source_state") != "active":
        errors.append("course or certification requires an active official provider source")
    if source.get("source_state") == "unavailable":
        for field in ("source_title", "current_cost", "currency", "duration", "prerequisite", "renewal", "maintenance"):
            if not isinstance(source.get(field), str) or not source[field].startswith("unknown:"):
                errors.append("unavailable provider source fields must be unknown")


def _validate_decisions(
    root: Mapping[str, object], market: Mapping[str, object], dossier: Mapping[str, object], research: Mapping[str, object], errors: list[str]
) -> None:
    decisions = root.get("decisions")
    if not isinstance(decisions, list):
        errors.append("learning decisions must be an array")
        return
    state = root.get("state")
    if state == "unavailable":
        if decisions:
            errors.append("unavailable learning bundle must not contain decisions")
        return
    if state != "evaluated":
        return
    vacancy_rows = research.get("vacancies") if isinstance(research, Mapping) else None
    evidence_rows = dossier.get("evidence") if isinstance(dossier, Mapping) else None
    vacancy_ids = [row.get("vacancy_id") for row in vacancy_rows or [] if isinstance(row, Mapping)]
    evidence_ids = [row.get("id") for row in evidence_rows or [] if isinstance(row, Mapping)]
    if not isinstance(vacancy_rows, list) or not vacancy_rows:
        errors.append("evaluated learning requires a non-empty market sample")
    if not 3 <= len(decisions) <= 5:
        errors.append("evaluated learning requires three to five decisions")
    ranks: list[object] = []
    option_types: list[str] = []
    for item in decisions:
        row = _closed(item, DECISION_FIELDS, "learning decision has invalid closed structure", errors)
        if row is None:
            continue
        ranks.append(row.get("decision_rank"))
        if isinstance(row.get("option_type"), str) and row["option_type"] not in option_types:
            option_types.append(row["option_type"])
        if type(row.get("decision_rank")) is not int or not 1 <= row["decision_rank"] <= 5:
            errors.append("learning decision rank is invalid")
        for field in ("target_role", "option_name", "provider_or_owner", "market_evidence_state", "cost_time_band", "expected_signal_boundary", "portfolio_or_no_learning_alternative", "overbuying_risk", "decision_basis", "next_action_gate"):
            if not _text(row.get(field)):
                errors.append("learning decision text is invalid")
            elif _text_has_identity_action_or_outcome_risk(row[field]):
                errors.append("learning decision contains forbidden identity, action, or outcome content")
        if not isinstance(row.get("gap_type"), str) or row["gap_type"] not in {"knowledge", "proof", "experience", "terminology", "low_return"}:
            errors.append("learning decision gap type is invalid")
        option_type = row.get("option_type")
        if not isinstance(option_type, str) or option_type not in {"course", "certification", "portfolio_project", "lab", "role_search", "no_learning_yet"}:
            errors.append("learning decision option type is invalid")
        if not isinstance(row.get("decision"), str) or row["decision"] not in {"do_now", "defer", "omit", "research_first"}:
            errors.append("learning decision outcome is invalid")
        if not _ids(row.get("source_gap_ids"), _EVIDENCE_RE, maximum=20) or any(item not in evidence_ids for item in row.get("source_gap_ids", [])):
            errors.append("learning decision evidence references are unbound")
        if not _ids(row.get("vacancy_ids"), _VACANCY_RE, maximum=5) or any(item not in vacancy_ids for item in row.get("vacancy_ids", [])):
            errors.append("learning decision vacancy references are unbound")
        if row.get("outcome_boundary") != "not_an_interview_offer_salary_or_roi_prediction" or row.get("draft_only") is not True or row.get("no_external_action") is not True:
            errors.append("learning decision action boundary is invalid")
        if not isinstance(row.get("expected_signal_boundary"), str) or not row["expected_signal_boundary"].startswith("bounded hypothesis"):
            errors.append("learning decision signal must be bounded")
        if not isinstance(row.get("next_action_gate"), str) or "exact authorization" not in row["next_action_gate"]:
            errors.append("learning decision gate must require exact authorization")
        provider_source = row.get("provider_source")
        if isinstance(option_type, str) and option_type in {"course", "certification"}:
            if not isinstance(provider_source, Mapping):
                errors.append("course or certification requires official provider source")
            else:
                _source_metadata(provider_source, as_of_date=str(root.get("as_of_date", "")), errors=errors)
        elif provider_source is not None:
            errors.append("non-provider learning option must not include provider source")
    if not _unique(ranks) or ranks != list(range(1, len(decisions) + 1)):
        errors.append("learning decision ranks must be unique and ordered")
    if not any(option_type in {"course", "certification"} for option_type in option_types):
        errors.append("learning decisions require a course or certification option")
    if not any(option_type in {"portfolio_project", "lab", "role_search", "no_learning_yet"} for option_type in option_types):
        errors.append("learning decisions require a proof or no-learning alternative")


def validate_learning_bundle(
    value: object,
    market: Mapping[str, object],
    dossier: Mapping[str, object],
    research: Mapping[str, object],
) -> list[str]:
    """Return bounded, identity-safe diagnostics for an optional bundle."""
    if value is None:
        return []
    cycle, over_limit = _graph_flags(value)
    if cycle:
        return ["learning bundle contains cyclic data"]
    if over_limit:
        return ["learning bundle exceeds safe size limit"]
    errors: list[str] = []
    if not isinstance(value, Mapping):
        return ["learning bundle must be an object"]
    root = _closed(value, TOP_FIELDS, "learning bundle has invalid closed structure", errors)
    if root is None:
        return _bounded(errors)
    schema_errors = _schema.validate_schema_instance(value, SCHEMA)
    if schema_errors:
        errors.append("learning bundle schema validation failed")
    if root.get("schema_version") != "career-learning-decision-v1":
        errors.append("learning bundle has invalid schema version")
    if not isinstance(root.get("state"), str) or root.get("state") not in {"evaluated", "unavailable"}:
        errors.append("learning bundle state is invalid")
    if root.get("privacy_boundary") != "public_vacancy_metadata_and_identity_free_evidence_references_only" or root.get("no_external_action") is not True or root.get("outcome_boundary") != "not_an_interview_offer_salary_or_roi_prediction":
        errors.append("learning bundle privacy or action boundary is invalid")
    _snapshot_errors(root, market, dossier, research, errors)
    if root.get("state") == "evaluated" and isinstance(market, Mapping) and market.get("state") == "market_evidence_unavailable":
        errors.append("evaluated learning is unavailable for a zero-vacancy market")
    if _private_or_unsafe_text(value):
        errors.append("learning bundle contains forbidden private or control content")
    _validate_decisions(root, market, dossier, research, errors)
    return _bounded(errors)


def load_learning_bundle(path: Path) -> dict[str, object]:
    """Load a bounded JSON object without echoing paths or input values."""
    try:
        raw = _loader.read_bounded_bytes(path, 256 * 1024).decode("utf-8")
        value = json.loads(raw)
    except (_loader.PrivateInputError, UnicodeDecodeError, json.JSONDecodeError, OSError, TypeError, ValueError) as error:
        raise LearningBundleLoadError("learning bundle is unavailable") from error
    if not isinstance(value, dict):
        raise LearningBundleLoadError("learning bundle must be an object")
    return value


if __name__ == "__main__":  # pragma: no cover
    import argparse

    parser = argparse.ArgumentParser(description="Validate a career learning decision bundle")
    parser.add_argument("bundle", type=Path)
    arguments = parser.parse_args()
    try:
        loaded = load_learning_bundle(arguments.bundle)
    except LearningBundleLoadError:
        print("learning bundle is unavailable", file=sys.stderr)
        raise SystemExit(2)
    print("learning bundle loaded; source-bound validation requires market inputs")
