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

_SENTENCE_START = re.compile(
    r"(?:^|[:.!?;]\s+|[\r\n]+[ \t]*(?:[-*•‣◦▪][ \t]*)?)"
)
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
        "actions", "analysis", "automation", "cloud", "cluster", "company",
        "corporation", "database", "engine", "engineering", "enterprise",
        "infrastructure", "integration", "intelligence", "kernel", "learning",
        "management",
        "objectives", "operations", "organization", "platform", "processing",
        "product", "program", "project", "recovery", "reliability", "replication",
        "response", "security", "service", "services", "software", "streams",
        "system", "systems", "team", "technology", "trust",
    }
)
_TECHNICAL_ORGANIZATION_PREFIXES = frozenset(
    {"amazon", "apache", "argo", "google", "microsoft"}
)
_TECHNICAL_COMPOUND_SUFFIXES = ("database", "engine", "manager", "platform", "server")
_MAX_IDENTITY_SCAN_CHARS = 4_096
_MAX_SUBJECT_WORDS = 12
_MAX_SIGNIFICANT_NAME_WORDS = 8
_OPENING_SUBJECT_PUNCTUATION = frozenset({"'", '"', "‘", "“", "«", "‹", "(", "[", "{"})
_CLOSING_SUBJECT_PUNCTUATION = frozenset({"'", '"', "’", "”", "»", "›", ")", "]", "}"})
_SUBJECT_LABEL_PUNCTUATION = frozenset({":", "—", "–"})
_SUBJECT_BULLETS = frozenset({"-", "*", "•", "‣", "◦", "▪"})
_UNCASED_NAME_SCRIPTS = (
    "ARABIC",
    "CJK UNIFIED IDEOGRAPH",
    "HANGUL",
    "HIRAGANA",
    "KATAKANA",
)


def _is_uncased_name_token(word: str) -> bool:
    parts = re.split(r"['’\-]", word)
    return 1 <= len(word) <= 32 and all(
        part
        and all(
            any(
                script in unicodedata.name(character, "")
                for script in _UNCASED_NAME_SCRIPTS
            )
            for character in part
        )
        for part in parts
    )


def _is_compact_east_asian_name(word: str) -> bool:
    return 2 <= len(word) <= 4 and all(
        any(
            script in unicodedata.name(character, "")
            for script in (
                "CJK UNIFIED IDEOGRAPH",
                "HANGUL",
                "HIRAGANA",
                "KATAKANA",
            )
        )
        for character in word
    )


def _is_acronym_token(word: str) -> bool:
    letters = tuple(character for character in word if character.isalpha())
    return 2 <= len(letters) <= 8 and all(
        character.isupper() for character in letters
    )


def _is_mixed_case_technical_token(word: str) -> bool:
    if "'" in word or "’" in word or "-" in word:
        return False
    if re.fullmatch(r"Mc[A-Z][a-z]+", word) or re.fullmatch(
        r"Mac[A-Z][a-z]+", word
    ):
        return False
    letters = tuple(character for character in word if character.isalpha())
    return (
        len(letters) >= 3
        and letters[0].isupper()
        and any(character.islower() for character in letters)
        and any(character.isupper() for character in letters[1:])
    )


def _is_compound_technical_token(word: str) -> bool:
    folded = word.casefold()
    return any(
        folded != suffix and folded.endswith(suffix)
        for suffix in _TECHNICAL_COMPOUND_SUFFIXES
    )


def _is_cased_name_token(word: str) -> bool:
    return word[0].isupper() or (
        len(word) >= 3
        and word[0].casefold() in {"d", "l"}
        and word[1] in {"'", "’"}
        and word[2].isupper()
    )


def _skip_subject_opening_punctuation(value: str, cursor: int) -> int:
    while cursor < len(value) and value[cursor].isspace():
        cursor += 1
    while cursor < len(value) and value[cursor] == ">":
        cursor += 1
        while cursor < len(value) and value[cursor] in " \t":
            cursor += 1
    while cursor < len(value) and value[cursor] in _OPENING_SUBJECT_PUNCTUATION:
        cursor += 1
    if cursor < len(value) and value[cursor] in _SUBJECT_BULLETS:
        cursor += 1
        while cursor < len(value) and value[cursor] in " \t":
            cursor += 1
    return cursor


def _subject_separator(value: str, cursor: int) -> tuple[int, bool]:
    while cursor < len(value) and value[cursor] in _CLOSING_SUBJECT_PUNCTUATION:
        cursor += 1
    if cursor < len(value) and value[cursor] in _SUBJECT_LABEL_PUNCTUATION:
        cursor += 1
        separator = re.match(r"\s*", value[cursor:])
        return cursor + separator.end(), True
    if cursor < len(value) and value[cursor] == ",":
        cursor += 1
    separator = re.match(r"\s+", value[cursor:])
    if separator is None:
        return cursor, False
    return cursor + separator.end(), False


def _sentence_subject_words(value: str, start: int) -> tuple[str, ...]:
    significant: list[str] = []
    has_predicate = False
    cursor = _skip_subject_opening_punctuation(value, start)
    for _ in range(_MAX_SUBJECT_WORDS):
        word_match = _UNICODE_WORD.match(value, cursor)
        if word_match is None:
            break
        word = word_match.group(0)
        folded = word.casefold()
        if folded in _NAME_PARTICLES and significant:
            pass
        elif _is_cased_name_token(word) or _is_uncased_name_token(word):
            significant.append(word)
            if len(significant) > _MAX_SIGNIFICANT_NAME_WORDS:
                return ()
        else:
            has_predicate = True
            break
        cursor, is_label = _subject_separator(value, word_match.end())
        if is_label:
            has_predicate = True
        if cursor == word_match.end():
            break
    return tuple(significant) if has_predicate else ()


def _looks_like_person_subject(words: tuple[str, ...]) -> bool:
    if len(words) == 1:
        return _is_compact_east_asian_name(words[0]) or (
            any(separator in words[0] for separator in ("'", "’", "-"))
            and _is_uncased_name_token(words[0])
        )
    if len(words) < 2:
        return False
    folded = tuple(word.casefold() for word in words)
    if (
        _is_acronym_token(words[0])
        or any(_is_mixed_case_technical_token(word) for word in words)
        or folded[0] in _TECHNICAL_ORGANIZATION_PREFIXES
        or _is_compound_technical_token(words[-1])
    ):
        return False
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
