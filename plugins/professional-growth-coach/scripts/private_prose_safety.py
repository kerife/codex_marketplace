"""Unicode safety checks for private prose."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Mapping, Sequence


MAX_DIAGNOSTIC_BYTES = 16_384
DIAGNOSTIC_TRUNCATION_MARKER = "validation diagnostics truncated; additional errors omitted\n"


_SUSPICIOUS_DIAGNOSTIC_FIELD = re.compile(
    r"@|://|~[\\/]|[.]{1,2}[\\/]|"
    r"(?:www\.|linkedin\.com/)|"
    r"(?<![A-Za-z])\+?\d[\d .()_-]{6,}\d|"
    r"(?:token|secret|password|credential|api[_-]?key|access[_-]?key|auth|cookie|private)",
    re.IGNORECASE,
)
_ABSOLUTE_DIAGNOSTIC_PATH = re.compile(r"^(?:/|[A-Za-z]:[\\/]|\\\\|//)")
_IDENTITY_TOKEN = re.compile(r"[^\W\d_]{2,}(?:['’][^\W\d_]{2,})*|[^\W\d_](?:\.)?", re.UNICODE)
_CANDIDATE_MARKERS = frozenset({"candidate", "applicant", "candidato", "candidata"})
_ROLE_TITLE_HEADS = frozenset({"architect", "developer", "engineer", "engineering", "manager", "specialist", "sre"})
_IDENTITY_LABELS = frozenset({"identity", "identidad", "name", "named", "nombre", "perfil", "profile", "llamado", "llamada"})
_ROLE_PRODUCT_TERMS = frozenset({"acquisition", "architect", "career", "careers", "cloud", "developer", "development", "devops", "engineer", "engineering", "experience", "index", "infrastructure", "jobs", "management", "manager", "operations", "platform", "portal", "product", "products", "reliability", "role", "search", "service", "services", "site", "software", "specialist", "sre", "success", "systems", "talent", "team", "workflow", "automation"})
_ROLE_TITLE_TECHNICAL_MODIFIERS = _ROLE_PRODUCT_TERMS | frozenset({"analytics", "api", "architecture", "data", "gateway", "journey", "mesh", "principal", "security"})
_PUBLIC_RESEARCH_TERMS = frozenset({"evidence", "free", "match", "material", "only", "reference", "references", "reported", "supplied"})
_SAFE_STANDALONE_TERMS = _ROLE_PRODUCT_TERMS | _PUBLIC_RESEARCH_TERMS
_CANDIDATE_SINGLE_NAME_EXCLUSIONS = frozenset(
    {
        "senior", "junior", "lead", "staff", "principal", "architect",
        "developer", "engineer", "engineering", "manager", "specialist", "sre",
    }
)


def contains_unmarked_candidate_identity(value: object) -> bool:
    """Reject short candidate-name forms that lack the usual two-token marker."""
    if isinstance(value, Mapping):
        return any(contains_unmarked_candidate_identity(item) for item in value.values())
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(contains_unmarked_candidate_identity(item) for item in value)
    if not isinstance(value, str):
        return False
    candidate_match = re.search(
        r"\b(?:candidate|applicant|candidato|candidata)\s+([^\W\d_]{2,})\b",
        value,
        re.IGNORECASE | re.UNICODE,
    )
    if candidate_match:
        token = unicodedata.normalize("NFKC", candidate_match.group(1)).casefold()
        if token not in _CANDIDATE_SINGLE_NAME_EXCLUSIONS and token not in _SAFE_STANDALONE_TERMS:
            return True
    for match in re.finditer(
        r"\b([^\W\d_]{2,})\s+([^\W\d_]{2,})\b", value, re.UNICODE
    ):
        first, second = match.groups()
        if not first[0].isupper() or not second[0].isupper():
            continue
        if not any(ord(character) > 127 for character in second):
            continue
        normalized = {
            unicodedata.normalize("NFKC", token).casefold()
            for token in (first, second)
        }
        if normalized.isdisjoint(_SAFE_STANDALONE_TERMS | _CANDIDATE_SINGLE_NAME_EXCLUSIONS):
            return True
    return False


def _candidate_identity_tokens(value: str) -> list[str]:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    normalized = re.sub(r"\bpersona\s+candidata\b", " candidate ", normalized)
    normalized = re.sub(r"\b(candidate|applicant|candidato|candidata)['’]s\b", r"\1 ", normalized)
    return _IDENTITY_TOKEN.findall(normalized)


def _looks_like_name_pair(tokens: Sequence[str]) -> bool:
    if len(tokens) != 2:
        return False
    normalized = [token.rstrip(".") for token in tokens]
    return all(token and token not in _SAFE_STANDALONE_TERMS and token not in _IDENTITY_LABELS and (len(token) == 1 or len(token.replace("'", "").replace("’", "")) >= 2) for token in normalized)


def _is_role_shaped_title(tokens: Sequence[str], marker_index: int) -> bool:
    suffix = tokens[marker_index + 1:]
    modifiers = [token.rstrip(".") for token in suffix[:-1]]
    return (
        marker_index == 0
        and bool(modifiers)
        and suffix[-1].rstrip(".") in _ROLE_TITLE_HEADS
        and not any(token in _IDENTITY_LABELS for token in suffix)
        and all(token in _ROLE_TITLE_TECHNICAL_MODIFIERS for token in modifiers)
    )


def contains_candidate_identity(value: object, *, vacancy_title: bool = False) -> bool:
    """Detect an explicit candidate marker adjacent to a normalized name pair."""
    if isinstance(value, Mapping):
        return any(contains_candidate_identity(item, vacancy_title=vacancy_title) for item in value.values())
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(contains_candidate_identity(item, vacancy_title=vacancy_title) for item in value)
    if not isinstance(value, str):
        return False
    tokens = _candidate_identity_tokens(value)
    for index, token in enumerate(tokens):
        if token not in _CANDIDATE_MARKERS:
            continue
        if vacancy_title and index + 1 < len(tokens) and tokens[index + 1] in _IDENTITY_LABELS:
            return True
        before = tokens[max(0, index - 2):index]
        after_start = index + 1
        has_identity_label = False
        while after_start < len(tokens) and tokens[after_start] in _IDENTITY_LABELS:
            has_identity_label = True
            after_start += 1
        after = tokens[after_start:after_start + 2]
        if _looks_like_name_pair(before):
            return True
        if vacancy_title and not has_identity_label and index == 0 and tokens[after_start:] and tokens[-1].rstrip(".") in _ROLE_TITLE_HEADS:
            if _is_role_shaped_title(tokens, index):
                continue
            return True
        if _looks_like_name_pair(after):
            if vacancy_title and not has_identity_label and _is_role_shaped_title(tokens, index):
                continue
            return True
    return False


def target_research_contains_candidate_identity(value: object) -> bool:
    """Scan only public prose and URL scalars allowed by target research."""
    if not isinstance(value, Mapping):
        return False
    strict_scalars: list[object] = []
    vacancy_titles: list[object] = []
    if isinstance(value.get("search_limit"), Mapping):
        strict_scalars.append(value["search_limit"].get("limitation"))
    for employer in value.get("employers", ()):
        if isinstance(employer, Mapping):
            strict_scalars.extend(employer.get(field) for field in ("display_name", "qualification_observation", "official_source_title", "official_source_url"))
    for vacancy in value.get("vacancies", ()):
        if not isinstance(vacancy, Mapping):
            continue
        vacancy_titles.append(vacancy.get("title"))
        strict_scalars.extend(vacancy.get(field) for field in ("location", "source_url", "official_referrer_url"))
        for collection, field in ((vacancy.get("eligibility_gates", ()), "observed_condition"), (vacancy.get("requirements", ()), "source_paraphrase")):
            if isinstance(collection, Sequence) and not isinstance(collection, (str, bytes, bytearray)):
                strict_scalars.extend(item.get(field) for item in collection if isinstance(item, Mapping))
    return any(contains_candidate_identity(scalar) for scalar in strict_scalars) or any(contains_candidate_identity(title, vacancy_title=True) for title in vacancy_titles)


def contains_unicode_controls(value: object) -> bool:
    """Return whether string text contains a Unicode control or format character."""
    if not isinstance(value, str):
        return False
    normalized = unicodedata.normalize("NFKC", value)
    return any(unicodedata.category(character) in {"Cc", "Cf"} for character in normalized)


def is_safe_prose_text(value: object) -> bool:
    """Return whether text is a string without Unicode controls or format characters."""
    return isinstance(value, str) and not contains_unicode_controls(value)


def safe_diagnostic_field_name(value: str) -> str:
    """Redact contact-, path-, and credential-shaped keys in diagnostics."""
    classification = unicodedata.normalize("NFKC", value)
    prefix = 0
    while prefix < len(classification) and (
        classification[prefix].isspace()
        or unicodedata.category(classification[prefix])
        in {"Cc", "Cf", "Cs", "Zl", "Zp"}
    ):
        prefix += 1
    classification = classification[prefix:]
    if _SUSPICIOUS_DIAGNOSTIC_FIELD.search(
        classification
    ) or _ABSOLUTE_DIAGNOSTIC_PATH.match(classification):
        return "<redacted-field>"
    return "".join(
        f"\\u{ord(character):04x}"
        if unicodedata.category(character) in {"Cc", "Cf", "Cs", "Zl", "Zp"}
        else character
        for character in value
    )


def format_bounded_diagnostics(
    errors: Sequence[str], *, max_bytes: int = MAX_DIAGNOSTIC_BYTES
) -> str:
    """Render diagnostics without exceeding a UTF-8 byte budget.

    Complete diagnostic lines are retained when they fit; otherwise a stable
    marker is emitted so callers can distinguish truncation from a clean result.
    The helper never slices an encoded line, preserving UTF-8 boundaries.
    """
    marker_bytes = len(DIAGNOSTIC_TRUNCATION_MARKER.encode("utf-8"))
    if max_bytes < marker_bytes:
        raise ValueError("diagnostic byte budget is smaller than truncation marker")
    lines: list[str] = []
    used_bytes = 0
    for error in errors:
        line = f"{error}\n"
        line_bytes = len(line.encode("utf-8"))
        if used_bytes + line_bytes <= max_bytes:
            lines.append(line)
            used_bytes += line_bytes
            continue
        while lines and used_bytes + marker_bytes > max_bytes:
            used_bytes -= len(lines.pop().encode("utf-8"))
        return "".join(lines) + DIAGNOSTIC_TRUNCATION_MARKER
    return "".join(lines)
