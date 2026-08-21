"""Unicode safety checks for private prose."""

from __future__ import annotations

import html
import re
import unicodedata
from collections.abc import Mapping, Sequence
from urllib.parse import unquote, urlsplit


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
_ROLE_PRODUCT_TERMS = frozenset({"acquisition", "accessibility", "accountability", "architect", "architecture", "authentication", "authorization", "automation", "availability", "blue", "build", "career", "careers", "chain", "cloud", "collaboration", "compatibility", "computer", "configuration", "containerization", "developer", "development", "devops", "documentation", "engineer", "engineering", "experience", "experimentation", "incident", "index", "infrastructure", "internationalization", "implementation", "jobs", "kubernetes", "language", "learning", "localization", "machine", "maintainability", "management", "manager", "modernization", "natural", "open", "operator", "operations", "orchestration", "origin", "personalization", "platform", "portal", "processing", "product", "products", "professional", "productivity", "recommendation", "release", "reliability", "research", "response", "role", "scientist", "search", "service", "services", "site", "software", "source", "specialist", "sre", "standardization", "success", "supply", "sustainability", "systems", "talent", "team", "telecommunications", "transformation", "trust", "vision", "virtualization", "workflow", "zero"})
_ROLE_TITLE_TECHNICAL_MODIFIERS = _ROLE_PRODUCT_TERMS | frozenset({"analytics", "api", "architecture", "data", "gateway", "journey", "mesh", "principal", "security"})
_PUBLIC_RESEARCH_TERMS = frozenset({"evidence", "free", "match", "material", "only", "reference", "references", "reported", "supplied"})
_SAFE_STANDALONE_TERMS = _ROLE_PRODUCT_TERMS | _PUBLIC_RESEARCH_TERMS
_CANDIDATE_SINGLE_NAME_EXCLUSIONS = frozenset(
    {
        "senior", "junior", "lead", "staff", "principal", "architect",
        "developer", "engineer", "engineering", "manager", "specialist", "sre",
    }
)
_COMMON_GIVEN_NAMES = frozenset(
    {
        "alex", "alexander", "alicia", "amelia", "ana", "carlos", "david", "elodie", "emily", "franklin", "george", "jane", "jean",
        "john", "jordan", "juan", "jose", "joseph", "kevin", "luc", "luis",
        "margaret", "maria", "marco", "mary", "michael", "mike", "miguel", "natalie", "nina", "patrick", "rachel", "robert", "samuel", "samantha", "sarah", "sofia", "sophia", "thomas", "tony", "victoria", "zhang",
        "benjamin", "elizabeth", "isabel",
    }
)
_COMMON_SURNAME_TOKENS = frozenset(
    {
        "allende", "anderson", "brown", "franklin", "grant", "jackson",
        "jefferson", "miller", "warren",
    }
)
_SAFE_PUBLIC_RESEARCH_PHRASES = frozenset(
    {
        "jane street",
        "john deere",
        "johnstone engineer",
        "maria db engineer",
        "maria-db engineer",
        "mariadb engineer",
    }
)
_SAFE_PUBLIC_RESEARCH_ORGANIZATIONS = frozenset({"jane street", "john deere", "maria db", "mariadb"})
_SAFE_FIELD_PUBLIC_RESEARCH_ORGANIZATIONS = frozenset({"grant thornton", "brown university", "miller lite"})
_SAFE_FIELD_PUBLIC_RESEARCH_FIELDS = frozenset({"display_name", "qualification_observation", "official_source_title", "title"})
_ORGANIZATION_AND_LOCATION_TERMS = frozenset(
    {
        "aerospace", "angeles", "canada", "city", "cloud", "corp", "corporation",
        "employer", "fixture", "francisco", "global", "group", "inc", "international", "ltd", "llc",
        "los", "mexico", "module", "motors", "native", "new", "sachs", "solutions",
        "states", "terraform", "united", "york",
    }
)
_PERSON_NAME_STOPWORDS = (
    _SAFE_STANDALONE_TERMS
    | _CANDIDATE_SINGLE_NAME_EXCLUSIONS
    | _CANDIDATE_MARKERS
    | _ROLE_TITLE_TECHNICAL_MODIFIERS
    | _ORGANIZATION_AND_LOCATION_TERMS
)
_PROPER_NAME_PAIR = re.compile(
    r"^\s*([^\W\d_][^\W\d_.'’\-]{1,})\s+([^\W\d_][^\W\d_.'’\-]{1,})\s*$",
    re.UNICODE,
)
_NAME_SLUG_SEQUENCE = re.compile(r"^\s*([^\W\d_]+(?:-[^\W\d_]+)+)\s*$", re.UNICODE)
_OBFUSCATED_NAME_PAIR = re.compile(r"\b([^\W\d_]{2,})[._/+\\-]([^\W\d_]{2,})\b", re.IGNORECASE | re.UNICODE)
_LOWERCASE_NAME_PAIR = re.compile(r"\b([^\W\d_]{2,})\s+([^\W\d_]{2,})(?:['’]s)?\b", re.IGNORECASE | re.UNICODE)
_INITIAL_NAME_PAIR = re.compile(r"\b([^\W\d_])\.\s*([^\W\d_]{2,})\b", re.IGNORECASE | re.UNICODE)
_OBFUSCATED_EMAIL = re.compile(
    r"\b[^\s@\[]+\s*(?:\[at\]|\(at\)|\bat\b)\s*[^\s.\[]+\s*(?:\[dot\]|\(dot\)|\bdot\b)\s*[A-Za-z]{2,}\b",
    re.IGNORECASE,
)
_EMAIL_ADDRESS = re.compile(r"\b[^\s@]+@[^\s@]+\.[A-Za-z]{2,}\b")
_HTML_TAG = re.compile(r"</?[A-Za-z][^>]{0,80}>")
_CONTEXTUAL_ROLE_TAIL = re.compile(
    r"\b((?:[^\s]+\s+){0,2}[^\s]{4,})\s*[-_./+]?\s*"
    r"(architect|developer|engineer|manager|specialist|sre)\b",
    re.IGNORECASE,
)
_SAFE_COMPACT_ROLE_TERMS = frozenset(
    {
        "cloudnative", "devops", "googlecloud", "infrastructure", "kubernetes",
        "observability", "platform", "sitereliability", "terraform", "terraformmodule",
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


def contains_candidate_like_name(value: object) -> bool:
    """Reject a bounded set of common human-name shapes in public metadata."""
    if not isinstance(value, str):
        return False
    normalized = unicodedata.normalize("NFKC", value)
    for match in re.finditer(
        r"\b([A-ZÁÉÍÓÚÑ][a-záéíóúñ]{2,})\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]{2,})\b",
        normalized,
    ):
        if (
            match.group(1).casefold() in _COMMON_GIVEN_NAMES
            and match.group(2).casefold() not in _PERSON_NAME_STOPWORDS
        ):
            return True
    for match in re.finditer(r"\b([a-z][a-záéíóúñ]{2,})-([a-záéíóúñ]{2,})\b", normalized.casefold()):
        if match.group(1) in _COMMON_GIVEN_NAMES:
            return True
    pair = _PROPER_NAME_PAIR.fullmatch(normalized)
    if pair:
        tokens = {token.rstrip(".'’-").casefold() for token in pair.groups()}
        if tokens.isdisjoint(_PERSON_NAME_STOPWORDS):
            return True
    words = re.findall(r"[^\W\d_]+", normalized)
    for first, second in zip(words, words[1:]):
        if (
            first[0].isupper()
            and second[0].isupper()
            and first[1:].islower()
            and second[1:].islower()
            and {first.casefold(), second.casefold()}.isdisjoint(_PERSON_NAME_STOPWORDS)
        ):
            return True
    slug = _NAME_SLUG_SEQUENCE.fullmatch(normalized.casefold())
    if slug:
        parts = slug.group(1).split("-")
        for first, second in zip(parts, parts[1:]):
            if {first, second}.isdisjoint(_PERSON_NAME_STOPWORDS):
                return True
    return False


def contains_obfuscated_candidate_identity(value: object) -> bool:
    """Reject common-name forms hidden by URL encoding or username punctuation."""
    if not isinstance(value, str):
        return False
    normalized_source = unicodedata.normalize("NFKC", value)
    for _ in range(3):
        decoded = html.unescape(unquote(normalized_source, errors="replace"))
        if decoded == normalized_source:
            break
        normalized_source = unicodedata.normalize("NFKC", decoded)
    normalized = normalized_source.casefold()
    inspection_text = normalized
    if "://" in normalized:
        try:
            parsed = urlsplit(normalized)
        except ValueError:
            parsed = None
        if parsed is not None:
            inspection_text = f"{parsed.hostname or ''} {parsed.path} {parsed.query} {parsed.fragment}"
    stopwords = _PERSON_NAME_STOPWORDS | _ORGANIZATION_AND_LOCATION_TERMS
    obfuscation_hint = bool(
        re.search(r"%[0-9a-f]{2}|&#(?:x[0-9a-f]+|[0-9]+);|[A-Za-z]\d[A-Za-z]", value, re.IGNORECASE)
    )
    if _OBFUSCATED_EMAIL.search(inspection_text) or _EMAIL_ADDRESS.search(inspection_text):
        return True
    if _HTML_TAG.search(normalized_source):
        return True
    leet = inspection_text.translate(str.maketrans({"0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t"}))
    for candidate_text in (inspection_text, leet):
        for match in _CONTEXTUAL_ROLE_TAIL.finditer(candidate_text):
            prefix = match.group(1).casefold()
            parts = [part for part in re.split(r"[\s._/+\\-]+", prefix) if part]
            if any(part in _COMMON_GIVEN_NAMES for part in parts):
                return True
            if prefix in stopwords or prefix in _SAFE_COMPACT_ROLE_TERMS:
                continue
            if any(
                len(part) > len(surname) + 2
                and part.endswith(surname)
                and any(part.startswith(given) for given in _COMMON_GIVEN_NAMES)
                for part in parts
                for surname in _COMMON_SURNAME_TOKENS
            ):
                return True
            if len(parts) >= 2 and all(part not in stopwords and len(part) >= 4 for part in parts):
                return True
    for match in re.finditer(r"\b([^\W\d_]{2,})[._/+\\-]+([^\W\d_]{2,})\b", inspection_text, re.UNICODE):
        first, second = match.groups()
        if (
            first in _COMMON_GIVEN_NAMES
            and second not in stopwords
            or second in _COMMON_GIVEN_NAMES
            and first not in stopwords
            or second in _COMMON_SURNAME_TOKENS
            and first not in stopwords
            or obfuscation_hint
            and len(first) >= 4
            and len(second) >= 4
            and first not in stopwords
            and second not in stopwords
        ):
            return True
    for match in _LOWERCASE_NAME_PAIR.finditer(inspection_text):
        first, second = match.groups()
        if (
            first in _COMMON_GIVEN_NAMES and second not in stopwords
            or obfuscation_hint
            and len(first) >= 4
            and len(second) >= 4
            and first not in stopwords
            and second not in stopwords
        ):
            return True
    for match in _INITIAL_NAME_PAIR.finditer(inspection_text):
        _, second = match.groups()
        if second not in stopwords:
            return True
    if re.search(r"\b[A-ZÁÉÍÓÚÑ]{2,},\s*[A-ZÁÉÍÓÚÑ]{2,}\b", normalized_source):
        return True
    for match in _OBFUSCATED_NAME_PAIR.finditer(leet):
        first, second = match.groups()
        if (
            first in _COMMON_GIVEN_NAMES and second not in stopwords
            or second in _COMMON_SURNAME_TOKENS and first not in stopwords
        ):
            return True
    for match in _LOWERCASE_NAME_PAIR.finditer(leet):
        first, second = match.groups()
        if (
            first in _COMMON_GIVEN_NAMES and second not in stopwords
            or second in _COMMON_SURNAME_TOKENS and first not in stopwords
        ):
            return True
    for token in re.findall(r"\b[^\W\d_]{6,}\b", inspection_text, re.UNICODE):
        if token in stopwords:
            continue
        for given_name in _COMMON_GIVEN_NAMES:
            if token.startswith(given_name) and len(token) > len(given_name) + 2:
                remainder = token[len(given_name):]
                if remainder not in stopwords:
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
    strict_scalars: list[tuple[object, str]] = []
    vacancy_titles: list[tuple[object, str]] = []
    if isinstance(value.get("search_limit"), Mapping):
        strict_scalars.append((value["search_limit"].get("limitation"), "limitation"))
    for employer in value.get("employers", ()):
        if isinstance(employer, Mapping):
            strict_scalars.extend(
                (employer.get(field), field)
                for field in (
                    "display_name",
                    "qualification_observation",
                    "official_source_title",
                    "official_source_url",
                )
            )
    for vacancy in value.get("vacancies", ()):
        if not isinstance(vacancy, Mapping):
            continue
        vacancy_titles.append((vacancy.get("title"), "title"))
        strict_scalars.extend(
            (vacancy.get(field), field)
            for field in (
                "location",
                "duplicate_fingerprint",
                "source_url",
                "official_referrer_url",
            )
        )
        for collection, field in ((vacancy.get("eligibility_gates", ()), "observed_condition"), (vacancy.get("requirements", ()), "source_paraphrase")):
            if isinstance(collection, Sequence) and not isinstance(collection, (str, bytes, bytearray)):
                strict_scalars.extend((item.get(field), field) for item in collection if isinstance(item, Mapping))
    def unsafe(scalar: object, *, field: str, vacancy_title: bool = False) -> bool:
        if isinstance(scalar, str):
            normalized = " ".join(unicodedata.normalize("NFKC", scalar).casefold().split())
            if normalized in _SAFE_PUBLIC_RESEARCH_PHRASES or _safe_public_research_context(normalized, field=field):
                return False
        return (
            contains_candidate_identity(scalar, vacancy_title=vacancy_title)
            or contains_candidate_like_name(scalar)
            or contains_obfuscated_candidate_identity(scalar)
        )

    return any(unsafe(scalar, field=field) for scalar, field in strict_scalars) or any(
        unsafe(title, field=field, vacancy_title=True) for title, field in vacancy_titles
    )


def _safe_public_research_context(value: str, *, field: str | None = None) -> bool:
    """Allow known organization names with an explicitly technical suffix."""
    candidates = [value]
    if "://" in value:
        try:
            parsed = urlsplit(value)
        except ValueError:
            parsed = None
        if parsed is not None and parsed.hostname:
            host = parsed.hostname.casefold().removeprefix("www.")
            path_tokens = re.sub(r"[^a-z0-9]+", " ", parsed.path.casefold()).split()
            for organization in _SAFE_PUBLIC_RESEARCH_ORGANIZATIONS:
                if host.startswith(f"{organization.replace(' ', '')}.") and path_tokens and all(
                    token in _ROLE_PRODUCT_TERMS for token in path_tokens
                ):
                    return True
            candidates.append(f"{host} {parsed.path}")
    for candidate in candidates:
        compact = re.sub(r"[^a-z0-9]+", " ", candidate.casefold()).strip()
        organizations = _SAFE_PUBLIC_RESEARCH_ORGANIZATIONS
        if field in _SAFE_FIELD_PUBLIC_RESEARCH_FIELDS:
            organizations |= _SAFE_FIELD_PUBLIC_RESEARCH_ORGANIZATIONS
        for organization in organizations:
            organization_compact = organization.replace(" ", "")
            if compact == organization:
                return True
            if compact.startswith(f"{organization} "):
                suffix = compact[len(organization):].strip()
            elif compact.startswith(f"{organization_compact} "):
                suffix = compact[len(organization_compact):].strip()
            else:
                continue
            suffix_tokens = suffix.split()
            if suffix_tokens and all(token in _ROLE_PRODUCT_TERMS for token in suffix_tokens):
                return True
    return False


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
