"""Shared privacy guard for dossier-to-practice projected text."""

from __future__ import annotations

import re
import unicodedata

from private_prose_safety import is_safe_prose_text


_FORBIDDEN_TEXT = re.compile(
    r"(?<![A-Z0-9+.-])(?:[A-Z][A-Z0-9+.-]*):(?=//|[^\s])|"
    r"\bwww\.|"
    r"(?<![A-Z0-9_])(?:~[/\\]|\.\.?[/\\]|"
    r"/(?:users|home|private|tmp|var|etc|opt|volumes|workspace|root|usr|bin|sbin|lib|lib64|system|library|applications|mnt|srv)(?:[/\\]|$)|"
    r"//[^\s/]+(?:[/\\]|$)|"
    r"[A-Z]:[/\\]|\\\\[^\s\\]+\\[^\s\\]+)|"
    r"\b(?:candidate\s+name|nombre\s+del\s+candidat[oa]|name|contact|contacto|"
    r"tel[eé]fono(?:\s+de\s+contacto)?|phone|email|correo|recruiter\s+name|"
    r"nombre\s+del\s+reclutador)\s*[:=]|"
    r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b|"
    r"(?<!\d)(?:\+\d{1,3}[\s.-])?(?:\(?\d{2,4}\)?[\s.-])"
    r"\d{3,4}[\s.-]\d{3,4}(?!\d)|"
    r"\b(?:raw\s+(?:profile|vacancy|job\s+description|reply|source|cv|resume)|"
    r"texto\s+crudo\s+del\s+(?:perfil|puesto|mensaje|origen)|"
    r"perfil\s+de\s+linkedin|linkedin\s+profile|curriculum\s+vitae|resume)\b|"
    r"\b(?:browser(?:[_-]session)?|session|sesi[oó]n)[_-]?"
    r"(?:id|identifier|token)\s*[:=]|"
    r"\b(?:browser|session|sesi[oó]n)[_-][A-Z0-9_-]{3,}\b|"
    r"\b(?:sha(?:1|256|512)|md5|hash)\s*[:=]|"
    r"\b[A-F0-9]{32,128}\b",
    re.IGNORECASE,
)

_FORBIDDEN_NAME = re.compile(
    r"\b(?i:(?:candidate|candidat[oa]|recruiter|reclutador[ae]?)\s+"
    r"(?:name\s+|nombre\s+)?)"
    r"[A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑa-záéíóúñ'-]+\s+"
    r"[A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑa-záéíóúñ'-]+\b|"
    r"\b(?i:(?:mr|mrs|ms|dr|sr|sra|srta)\.?)\s+"
    r"[A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑa-záéíóúñ'-]+\s+"
    r"[A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑa-záéíóúñ'-]+\b"
)

_FORBIDDEN_CONTROL = re.compile(r"[\u0000-\u001f\u007f-\u009f\u200b-\u200d\u2060\ufeff]")

_SENTENCE_START = re.compile(r"(?:^|[:.!?]\s+)")
_UNICODE_WORD = re.compile(r"[^\W\d_]+(?:['’\-][^\W\d_]+)*", re.UNICODE)
_NAME_PARTICLES = frozenset(
    {"da", "das", "de", "del", "do", "dos", "la", "las", "los", "van", "von", "y"}
)
_ROLE_OR_DOMAIN_QUALIFIERS = frozenset(
    {
        "account", "cloud", "customer", "data", "engineering", "enterprise",
        "finance", "lead", "marketing", "operations", "people", "platform",
        "principal", "product", "program", "project", "sales", "security",
        "senior", "software", "solutions", "staff", "strategy", "talent",
        "technical", "ui", "user", "ux",
    }
)
# A capitalized noun phrase ending in one of these domain/organization heads is
# a technical subject, not a person name. This avoids phrase-by-phrase exceptions.
_NON_PERSON_SUBJECT_HEADS = frozenset(
    {
        "automation", "cloud", "company", "corporation", "database",
        "engineering", "infrastructure", "operations", "organization",
        "platform", "product", "program", "project", "reliability", "response",
        "security", "service", "services", "software", "system", "systems",
        "team", "technology",
    }
)
_MAX_IDENTITY_SCAN_CHARS = 4_096


def _sentence_subject_words(value: str, start: int) -> tuple[str, ...]:
    significant: list[str] = []
    has_predicate = False
    cursor = start
    for _ in range(7):
        word_match = _UNICODE_WORD.match(value, cursor)
        if word_match is None:
            break
        word = word_match.group(0)
        folded = word.casefold()
        if folded in _NAME_PARTICLES and significant:
            pass
        elif word[0].isupper():
            significant.append(word)
            if len(significant) > 4:
                return ()
        else:
            has_predicate = True
            break
        separator = re.match(r"\s+", value[word_match.end() :])
        if separator is None:
            break
        cursor = word_match.end() + separator.end()
    return tuple(significant) if has_predicate else ()


def _looks_like_person_subject(words: tuple[str, ...]) -> bool:
    if not 2 <= len(words) <= 4:
        return False
    folded = tuple(word.casefold() for word in words)
    return (
        folded[0] not in _ROLE_OR_DOMAIN_QUALIFIERS
        and folded[-1] not in _NON_PERSON_SUBJECT_HEADS
    )


def is_safe_handoff_text(value: object, maximum: int) -> bool:
    """Return whether text is bounded, non-empty, and safe to project."""
    if not is_safe_prose_text(value) or _FORBIDDEN_CONTROL.search(value):
        return False
    normalized = unicodedata.normalize("NFKC", value)
    return (
        bool(normalized.strip())
        and len(normalized) <= maximum
        and _FORBIDDEN_TEXT.search(normalized) is None
        and _FORBIDDEN_NAME.search(normalized) is None
    )


def has_unlabelled_person_intro(value: object) -> bool:
    """Return whether prose begins a sentence with an ordinary person name."""
    if not isinstance(value, str):
        return False
    normalized = unicodedata.normalize("NFKC", value)
    if len(normalized) > _MAX_IDENTITY_SCAN_CHARS:
        return True
    return any(
        _looks_like_person_subject(
            _sentence_subject_words(normalized, sentence_start.end())
        )
        for sentence_start in _SENTENCE_START.finditer(normalized)
    )


def is_identity_free_handoff_text(value: object, maximum: int) -> bool:
    """Return whether projected source-fact prose contains no bare person intro."""
    return is_safe_handoff_text(value, maximum) and not has_unlabelled_person_intro(value)
