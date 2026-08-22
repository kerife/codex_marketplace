#!/usr/bin/env python3
"""Validate closed, public-only career learning provider research."""

from __future__ import annotations

import copy
import datetime as dt
import html
import hashlib
import importlib.util
import ipaddress
import json
import re
import sys
import unicodedata
from collections.abc import Mapping
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit


def _sibling(name: str) -> Any:
    path = Path(__file__).with_name(name)
    specification = importlib.util.spec_from_file_location(f"_pgc_{path.stem}", path)
    if specification is None or specification.loader is None:
        raise RuntimeError("required provider research dependency is unavailable")
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


_loader = _sibling("private_input_loader.py")
_prose = _sibling("private_prose_safety.py")

PrivateInputError = _loader.PrivateInputError
read_bounded_bytes = _loader.read_bounded_bytes
contains_candidate_identity = _prose.contains_candidate_identity
contains_candidate_like_name = _prose.contains_candidate_like_name
contains_obfuscated_candidate_identity = _prose.contains_obfuscated_candidate_identity
contains_unicode_controls = _prose.contains_unicode_controls
contains_unmarked_candidate_identity = _prose.contains_unmarked_candidate_identity

SCHEMA_VERSION = "career-learning-provider-research-v1"
_MAX_DEPTH = 32
_MAX_NODES = 10_000
_MAX_LIST_ITEMS = 150
_MAX_ERRORS = 64
_MAX_INPUT_BYTES = 256 * 1024
_MAX_TEXT = 500
_SIGNAL = re.compile(r"[a-z][a-z0-9_]{1,63}\Z")
_OPTION_ID = re.compile(r"LP-[0-9]{3}\Z")
_DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}\Z")
_EMAIL = re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")
_PHONE = re.compile(r"(?:^|\s)\+?\d[\d .()_-]{6,}\d(?:$|\s)")
_HTML = re.compile(r"<\s*/?\s*(?:script|style|html|body|div|span|iframe|[a-z][a-z0-9-]*)\b", re.I)
_LOCAL_PATH = re.compile(
    r"(?:^|[\s?&#=;\"'])(?:"
    r"~[\\/]|"
    r"/{1,2}(?:Users|private|var|tmp|home|root)(?:[\\/]|$)|"
    r"[A-Za-z]:[\\/](?:Users(?:[\\/]|$))?|"
    r"\\\\[^\\/\s]+[\\/][^\\/\s]+"
    r")",
    re.I,
)
_LOCAL_PATH_SEGMENT = re.compile(
    r"(?:^|[\\/])(?:Users|private|var|tmp|home|root)(?:[\\/]|$)", re.I
)
_LOCAL_FILE_URI = re.compile(
    r"(?:^|[\s?&#=;\"'])file\s*:(?:[\\/]){2,}", re.I
)
_ROOT_FIELDS = frozenset(
    {"schema_version", "locale", "as_of_date", "state", "options", "privacy_boundary", "no_external_action"}
)
_OPTION_FIELDS = frozenset(
    {
        "option_id", "option_type", "provider", "option", "source_title", "source_date",
        "access_date", "source_state", "url", "geography", "availability", "current_cost",
        "currency", "tax", "duration", "prerequisite", "renewal", "maintenance", "unknowns",
        "covered_signals", "coverage_basis",
    }
)
_TEXT_FIELDS = (
    "provider", "option", "source_title", "geography", "current_cost", "currency", "tax",
    "duration", "prerequisite", "renewal", "maintenance", "unknowns",
)
_OFFICIAL_PROVIDER_HOSTS = {
    "HashiCorp": frozenset({"developer.hashicorp.com"}),
    "Argo Project": frozenset({"argo-cd.readthedocs.io"}),
}
_OPTION_TYPES = frozenset({"course", "certification"})
_SOURCE_STATES = frozenset({"active", "unknown", "unavailable"})
_AVAILABILITY = frozenset({"available", "unknown", "unavailable"})
_COVERAGE_BASES = frozenset(
    {"exact_technology_title", "explicit_curriculum", "explicit_exam_objective"}
)


class ProviderResearchLoadError(ValueError):
    """Raised for safe, deterministic provider-research input failures."""


def _safe_tree(value: object) -> bool:
    pending: list[tuple[str, object, int]] = [("visit", value, 0)]
    active: set[int] = set()
    nodes = 0
    while pending:
        operation, current, depth = pending.pop()
        if operation == "leave":
            active.discard(id(current))
            continue
        if operation == "children":
            try:
                child = next(current)
            except StopIteration:
                continue
            except Exception:
                return False
            pending.append(("children", current, depth))
            pending.append(("visit", child, depth))
            continue
        nodes += 1
        if nodes > _MAX_NODES or depth > _MAX_DEPTH:
            return False
        if isinstance(current, str):
            if any(0xD800 <= ord(character) <= 0xDFFF for character in current):
                return False
            continue
        if current is None or isinstance(current, (bool, int, float)):
            continue
        if not isinstance(current, (Mapping, list)):
            return False
        identity = id(current)
        if identity in active:
            return False
        if isinstance(current, list) and len(current) > _MAX_LIST_ITEMS:
            return False
        try:
            children = iter(current.values() if isinstance(current, Mapping) else current)
        except Exception:
            return False
        active.add(identity)
        pending.append(("leave", current, depth))
        pending.append(("children", children, depth + 1))
    return True


def _bounded_plain_copy(value: object) -> dict[str, object] | None:
    if not _safe_tree(value) or not isinstance(value, Mapping):
        return None
    try:
        copied = copy.deepcopy(value)
    except Exception:
        return None
    return copied if isinstance(copied, dict) else None


def _date(value: object) -> dt.date | None:
    if not isinstance(value, str) or not _DATE.fullmatch(value):
        return None
    try:
        return dt.date.fromisoformat(value)
    except ValueError:
        return None


def _closed(value: object, fields: frozenset[str], errors: list[str], diagnostic: str) -> Mapping[str, object] | None:
    if not isinstance(value, Mapping):
        errors.append(diagnostic)
        return None
    try:
        keys = set(value)
    except Exception:
        errors.append(diagnostic)
        return None
    if keys - fields:
        errors.append("provider research has unsupported fields")
    if fields - keys:
        errors.append(diagnostic)
    return value


def _valid_text(value: object, *, provider: bool = False, strict_name: bool = False) -> bool:
    if not isinstance(value, str) or not 0 < len(value) <= _MAX_TEXT:
        return False
    inspection = _decoded_url_component(value)
    if inspection is None or len(inspection) > _MAX_TEXT:
        return False
    if (
        contains_unicode_controls(value)
        or contains_unicode_controls(inspection)
        or _contains_local_path(inspection)
        or _EMAIL.search(inspection)
        or _PHONE.search(inspection)
        or _HTML.search(inspection)
    ):
        return False
    if contains_candidate_identity(inspection) or contains_unmarked_candidate_identity(inspection):
        return False
    return provider or not (
        contains_obfuscated_candidate_identity(inspection)
        or (strict_name and contains_candidate_like_name(inspection))
    )


def _contains_local_path(value: str) -> bool:
    return bool(
        _LOCAL_PATH.search(value)
        or _LOCAL_PATH_SEGMENT.search(value)
        or _LOCAL_FILE_URI.search(value)
    )


def _decoded_url_component(value: object) -> str | None:
    if not isinstance(value, str) or len(value) > 2048:
        return None
    decoded = value
    for _ in range(3):
        next_value = html.unescape(unquote(decoded))
        if next_value == decoded:
            break
        decoded = next_value
    return unicodedata.normalize("NFKC", decoded)


def _safe_url_component(value: object) -> bool:
    decoded = _decoded_url_component(value)
    return (
        decoded is not None
        and (not decoded or _valid_text(decoded, strict_name=True))
        and not _contains_local_path(decoded)
    )


def _official_https_url(provider: object, value: object) -> bool:
    if not isinstance(provider, str) or provider not in _OFFICIAL_PROVIDER_HOSTS:
        return False
    if not isinstance(value, str) or len(value) > 2048 or contains_unicode_controls(value):
        return False
    try:
        parsed = urlsplit(value)
        port = parsed.port
        host = (parsed.hostname or "").casefold().rstrip(".")
    except ValueError:
        return False
    except Exception:
        return False
    try:
        ipaddress.ip_address(host)
        return False
    except ValueError:
        pass
    return (
        parsed.scheme == "https"
        and parsed.username is None
        and parsed.password is None
        and port is None
        and bool(host)
        and host in _OFFICIAL_PROVIDER_HOSTS[provider]
        and all(_safe_url_component(component) for component in (parsed.path, parsed.query, parsed.fragment))
    )


def _closed_structure_errors(root: Mapping[str, object]) -> list[str]:
    errors: list[str] = []
    root = _closed(root, _ROOT_FIELDS, errors, "provider research has invalid root structure")
    if root is None:
        return errors
    if root.get("schema_version") != SCHEMA_VERSION:
        errors.append("provider research has invalid schema version")
    if root.get("locale") not in {"es", "en"}:
        errors.append("provider research has invalid locale")
    if root.get("state") not in {"complete", "limited", "unavailable"}:
        errors.append("provider research has invalid state")
    if root.get("privacy_boundary") != "public_provider_metadata_only" or root.get("no_external_action") is not True:
        errors.append("provider research has invalid boundaries")
    options = root.get("options")
    if not isinstance(options, list) or len(options) > 20:
        errors.append("provider research has invalid options")
    elif root.get("state") in {"complete", "limited"} and not options:
        errors.append("provider research has invalid state")
    elif root.get("state") == "unavailable" and options:
        errors.append("provider research has invalid state")
    return errors


def _date_and_state_errors(root: Mapping[str, object]) -> list[str]:
    errors: list[str] = []
    as_of = _date(root.get("as_of_date"))
    if as_of is None:
        errors.append("provider research has invalid as-of date")
    options = root.get("options")
    if not isinstance(options, list):
        return errors
    for option in options:
        if not isinstance(option, Mapping):
            continue
        source_date = _date(option.get("source_date"))
        access_date = _date(option.get("access_date"))
        if source_date is None or access_date is None or as_of is None or source_date > access_date or access_date > as_of:
            errors.append("provider research has invalid source dates")
        source_state, availability = option.get("source_state"), option.get("availability")
        if source_state == "active" and availability != "available":
            errors.append("provider research has incompatible option state")
        elif source_state == "unknown" and availability != "unknown":
            errors.append("provider research has incompatible option state")
        elif source_state == "unavailable" and availability != "unavailable":
            errors.append("provider research has incompatible option state")
    return errors


def _option_errors(root: Mapping[str, object]) -> list[str]:
    errors: list[str] = []
    options = root.get("options")
    if not isinstance(options, list):
        return errors
    option_ids: set[str] = set()
    for item in options:
        option = _closed(item, _OPTION_FIELDS, errors, "provider research has invalid option")
        if option is None:
            continue
        option_id = option.get("option_id")
        if not isinstance(option_id, str) or not _OPTION_ID.fullmatch(option_id):
            errors.append("provider research has invalid option")
        elif option_id in option_ids:
            errors.append("provider research has duplicate option IDs")
        else:
            option_ids.add(option_id)
        if option.get("option_type") not in _OPTION_TYPES:
            errors.append("provider research has invalid option")
        provider = option.get("provider")
        if not _valid_text(provider, provider=True) or provider not in _OFFICIAL_PROVIDER_HOSTS:
            errors.append("provider research has unreviewed provider")
        for field in _TEXT_FIELDS:
            if not _valid_text(
                option.get(field),
                provider=field == "provider",
                strict_name=field in {"option", "source_title", "geography", "unknowns"},
            ):
                errors.append("provider research has unsafe public metadata")
                break
        if option.get("source_state") not in _SOURCE_STATES or option.get("availability") not in _AVAILABILITY:
            errors.append("provider research has invalid option state")
        if option.get("coverage_basis") not in _COVERAGE_BASES:
            errors.append("provider research has invalid coverage basis")
        if not _official_https_url(provider, option.get("url")):
            errors.append("provider research has invalid official source URL")
        signals = option.get("covered_signals")
        if (
            not isinstance(signals, list)
            or len(signals) > 20
            or any(not isinstance(signal, str) or not _SIGNAL.fullmatch(signal) for signal in signals)
            or signals != sorted(set(signals))
        ):
            errors.append("provider research has invalid covered signals")
        elif option.get("source_state") == "unavailable" and signals:
            errors.append("provider research has unavailable source coverage")
    return errors


def _bounded_unique_errors(errors: list[str]) -> list[str]:
    result: list[str] = []
    for error in errors:
        if error not in result:
            result.append(error)
        if len(result) >= _MAX_ERRORS:
            break
    return result


def validate_provider_research(value: object) -> list[str]:
    """Return no errors only for a bounded, closed public provider source."""
    root = _bounded_plain_copy(value)
    if root is None:
        return ["provider research is invalid"]
    errors = _closed_structure_errors(root)
    errors.extend(_date_and_state_errors(root))
    errors.extend(_option_errors(root))
    return _bounded_unique_errors(errors)


def _canonical_json(value: Mapping[str, object]) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def snapshot_for_provider_research(value: Mapping[str, object]) -> str:
    """Return the canonical snapshot for a valid provider research artifact."""
    if validate_provider_research(value):
        raise ValueError("provider research is invalid")
    digest = hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()
    return f"snap-provider-sha256-{digest}"


def load_provider_research(path: Path) -> dict[str, object]:
    """Load and validate bounded provider research without leaking path details."""
    try:
        raw = read_bounded_bytes(path, _MAX_INPUT_BYTES)
        value = json.loads(raw.decode("utf-8"))
    except (PrivateInputError, OSError, UnicodeDecodeError, json.JSONDecodeError):
        raise ProviderResearchLoadError("provider research input is unavailable") from None
    if not isinstance(value, dict) or validate_provider_research(value):
        raise ProviderResearchLoadError("provider research input is invalid")
    return value
