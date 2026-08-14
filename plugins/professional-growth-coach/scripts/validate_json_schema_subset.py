"""Dependency-free validator for the JSON Schema subset used by this plugin."""

from __future__ import annotations

import datetime as dt
import hashlib
import re
from collections.abc import Mapping

from private_prose_safety import safe_diagnostic_field_name


MAX_SCHEMA_VALIDATION_DEPTH = 64
SCHEMA_DEPTH_ERROR = "schema validation exceeds safe depth limit"
MAX_SCHEMA_EVALUATIONS = 4_096
SCHEMA_EVALUATION_LIMIT_ERROR = "schema validation exceeds safe evaluation limit"
SCHEMA_KEYWORD_INVALID_ERROR = "schema keyword is invalid"
SCHEMA_PATTERN_INVALID_ERROR = "schema pattern is invalid"
MAX_SCHEMA_PATTERN_LENGTH = 1_024
SCHEMA_PATTERN_COMPLEXITY_ERROR = "pattern exceeds safe complexity limit"
_NESTED_QUANTIFIER = re.compile(
    r"\((?:[^()\\]|\\.)*(?:[+*]|\{\d+,\})(?:[^()\\]|\\.)*\)"
    r"(?:[+*]|\{\d+(?:,\d*)?\})"
)
_MAX_LITERAL_PATTERN_VARIANTS = 256
_MAX_LITERAL_PATTERN_TOKENS = 1_024
_MAX_JSON_EQUALITY_EVALUATIONS = MAX_SCHEMA_EVALUATIONS


_SUPPORTED_TYPES = frozenset(
    {"object", "array", "string", "boolean", "integer", "number", "null"}
)


def _group_spans(pattern: str) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    stack: list[int] = []
    escaped = False
    in_character_class = False
    for index, character in enumerate(pattern):
        if escaped:
            escaped = False
            continue
        if character == "\\":
            escaped = True
            continue
        if character == "[" and not in_character_class:
            in_character_class = True
            continue
        if character == "]" and in_character_class:
            in_character_class = False
            continue
        if in_character_class:
            continue
        if character == "(":
            stack.append(index)
        elif character == ")" and stack:
            spans.append((stack.pop(), index))
    return spans


def _is_repeated_group(pattern: str, closing_index: int) -> bool:
    suffix = pattern[closing_index + 1 :]
    return bool(
        suffix.startswith(("+", "*"))
        or re.match(r"\{\d+(?:,\d*)?\}", suffix)
    )


def _contains_unbounded_quantifier(fragment: str) -> bool:
    escaped = False
    in_character_class = False
    for index, character in enumerate(fragment):
        if escaped:
            escaped = False
            continue
        if character == "\\":
            escaped = True
            continue
        if character == "[" and not in_character_class:
            in_character_class = True
            continue
        if character == "]" and in_character_class:
            in_character_class = False
            continue
        if in_character_class:
            continue
        if character in "+*" or (
            character == "{" and re.match(r"\{\d+,\}", fragment[index:])
        ):
            return True
    return False


def _strip_group_extension(fragment: str) -> str:
    extension = re.match(r"^\?(?:[aiLmsux-]+)?:", fragment)
    return fragment[extension.end() :] if extension else fragment


def _strip_redundant_groups(fragment: str) -> str:
    value = _strip_group_extension(fragment)
    while value.startswith("(") and any(
        start == 0 and end == len(value) - 1 for start, end in _group_spans(value)
    ):
        value = _strip_group_extension(value[1:-1])
    return value


def _top_level_alternatives(fragment: str) -> list[str]:
    alternatives: list[str] = []
    start = 0
    depth = 0
    escaped = False
    in_character_class = False
    for index, character in enumerate(fragment):
        if escaped:
            escaped = False
            continue
        if character == "\\":
            escaped = True
            continue
        if character == "[" and not in_character_class:
            in_character_class = True
            continue
        if character == "]" and in_character_class:
            in_character_class = False
            continue
        if in_character_class:
            continue
        if character == "(":
            depth += 1
        elif character == ")" and depth:
            depth -= 1
        elif character == "|" and depth == 0:
            alternatives.append(fragment[start:index])
            start = index + 1
    alternatives.append(fragment[start:])
    return alternatives


def _literal_atom_choices(
    fragment: str, index: int
) -> tuple[list[tuple[str, ...]], int] | None:
    character = fragment[index]
    if character == "\\":
        if index + 1 >= len(fragment) or fragment[index + 1].isalnum():
            return None
        return [(fragment[index + 1],)], index + 2
    if character == "[":
        choices: list[tuple[str, ...]] = []
        cursor = index + 1
        if cursor >= len(fragment) or fragment[cursor] == "^":
            return None
        while cursor < len(fragment) and fragment[cursor] != "]":
            if fragment[cursor] == "\\":
                cursor += 1
                if cursor >= len(fragment) or fragment[cursor].isalnum():
                    return None
                token = fragment[cursor]
            elif fragment[cursor] == "-":
                return None
            else:
                token = fragment[cursor]
            choice = (token,)
            if choice not in choices:
                choices.append(choice)
            cursor += 1
        if cursor >= len(fragment) or not choices:
            return None
        return choices, cursor + 1
    if character.isalnum() or character in " _-'":
        return [(character,)], index + 1
    return None


def _character_class_language(
    pattern: str, index: int
) -> tuple[tuple[str, frozenset[str] | None], int] | None:
    """Return a bounded language descriptor for one simple regex atom."""
    character = pattern[index]
    if character == "\\":
        if index + 1 >= len(pattern):
            return None
        escaped = pattern[index + 1]
        if escaped in "dws":
            return (escaped, None), index + 2
        if escaped.isalnum():
            return ("unknown", None), index + 2
        return ("finite", frozenset({escaped})), index + 2
    if character == "[":
        cursor = index + 1
        unknown = False
        if cursor < len(pattern) and pattern[cursor] == "^":
            unknown = True
            cursor += 1
        characters: set[str] = set()
        while cursor < len(pattern) and pattern[cursor] != "]":
            if pattern[cursor] == "\\":
                if cursor + 1 >= len(pattern):
                    return None
                escaped = pattern[cursor + 1]
                if escaped in "dws" or escaped.isalnum():
                    unknown = True
                    cursor += 2
                    continue
                start = escaped
                cursor += 2
            else:
                start = pattern[cursor]
                cursor += 1
            if (
                cursor + 1 < len(pattern)
                and pattern[cursor] == "-"
                and pattern[cursor + 1] != "]"
            ):
                end = pattern[cursor + 1]
                if ord(end) < ord(start) or ord(end) - ord(start) > 256:
                    unknown = True
                else:
                    characters.update(
                        chr(code) for code in range(ord(start), ord(end) + 1)
                    )
                cursor += 2
            else:
                characters.add(start)
            if len(characters) > 256:
                unknown = True
                characters.clear()
        if cursor >= len(pattern):
            return None
        if unknown or not characters:
            return ("unknown", None), cursor + 1
        return ("finite", frozenset(characters)), cursor + 1
    if character == ".":
        return ("unknown", None), index + 1
    if character in "^$|(){}+*?":
        return None
    return ("finite", frozenset({character})), index + 1


def _quantifier(
    pattern: str, index: int
) -> tuple[int, bool] | None:
    if index >= len(pattern):
        return None
    if pattern[index] in "+*":
        return (
            index + 1 + (index + 1 < len(pattern) and pattern[index + 1] == "?"),
            True,
        )
    if pattern[index] == "?":
        return (
            index + 1 + (index + 1 < len(pattern) and pattern[index + 1] == "?"),
            False,
        )
    match = re.match(r"\{\d+(?:,\d*)?\}", pattern[index:])
    if match is None:
        return None
    text = match.group(0)
    end = index + len(text)
    if end < len(pattern) and pattern[end] == "?":
        end += 1
    return end, text.endswith(",}")


def _languages_overlap(
    left: tuple[str, frozenset[str] | None],
    right: tuple[str, frozenset[str] | None],
) -> bool:
    left_kind, left_characters = left
    right_kind, right_characters = right
    if left_kind == "unknown" or right_kind == "unknown":
        return True
    if left_kind == right_kind and left_kind in {"d", "w", "s"}:
        return True
    if left_kind in {"d", "w", "s"} and right_kind in {"d", "w", "s"}:
        return {left_kind, right_kind} == {"d", "w"}
    finite = left_characters if left_kind == "finite" else right_characters
    category = right_kind if left_kind == "finite" else left_kind
    if finite is None:
        return True
    if category == "finite":
        return bool(finite & (right_characters or frozenset()))
    predicate = {
        "d": str.isdigit,
        "w": lambda value: value.isalnum() or value == "_",
        "s": str.isspace,
    }[category]
    return any(predicate(character) for character in finite)


def _transparent_group_boundaries(
    fragment: str,
) -> tuple[
    tuple[tuple[str, frozenset[str] | None], ...],
    tuple[tuple[str, frozenset[str] | None], ...],
]:
    """Expose unbounded atom languages at transparent group boundaries."""
    value = _strip_group_extension(fragment)
    alternatives = _top_level_alternatives(value)
    if len(alternatives) > 1:
        # Alternation changes the group language rather than transparently
        # wrapping one sequence. Repeated alternations are handled separately
        # by the bounded structural-language analysis.
        return (), ()

    group_ends = dict(_group_spans(value))
    tokens: list[
        tuple[
            tuple[tuple[str, frozenset[str] | None], ...],
            tuple[tuple[str, frozenset[str] | None], ...],
        ]
    ] = []
    index = 0
    while index < len(value):
        if value[index] in "^$":
            index += 1
            continue
        if value[index] == "(" and index in group_ends:
            closing = group_ends[index]
            repeat = _quantifier(value, closing + 1)
            if repeat is None:
                tokens.append(
                    _transparent_group_boundaries(value[index + 1 : closing])
                )
                index = closing + 1
            else:
                tokens.append(((), ()))
                index = repeat[0]
            continue
        atom = _character_class_language(value, index)
        if atom is None:
            index += 1
            continue
        language, atom_end = atom
        repeat = _quantifier(value, atom_end)
        if repeat is not None and repeat[1]:
            tokens.append(((language,), (language,)))
            index = repeat[0]
        else:
            tokens.append(((), ()))
            index = repeat[0] if repeat is not None else atom_end
    if not tokens:
        return (), ()
    return tokens[0][0], tokens[-1][1]


def _has_adjacent_ambiguous_quantified_atoms(pattern: str) -> bool:
    previous: tuple[tuple[str, frozenset[str] | None], ...] = ()
    group_ends = dict(_group_spans(pattern))
    index = 0
    while index < len(pattern):
        if pattern[index] == "(" and index in group_ends:
            closing = group_ends[index]
            body = pattern[index + 1 : closing]
            if _has_adjacent_ambiguous_quantified_atoms(body):
                return True
            repeat = _quantifier(pattern, closing + 1)
            if repeat is None:
                leading, trailing = _transparent_group_boundaries(body)
                if any(
                    _languages_overlap(left, right)
                    for left in previous
                    for right in leading
                ):
                    return True
                previous = trailing
                index = closing + 1
            else:
                previous = ()
                index = repeat[0]
            continue
        atom = _character_class_language(pattern, index)
        if atom is None:
            previous = ()
            index += 1
            continue
        language, atom_end = atom
        repeat = _quantifier(pattern, atom_end)
        if repeat is None:
            previous = ()
            index = atom_end
            continue
        repeat_end, unbounded = repeat
        if unbounded:
            if any(_languages_overlap(left, language) for left in previous):
                return True
            previous = (language,)
        else:
            previous = ()
        index = repeat_end
    return False


def _has_oversized_quantifier(pattern: str) -> bool:
    escaped = False
    in_character_class = False
    for index, character in enumerate(pattern):
        if escaped:
            escaped = False
            continue
        if character == "\\":
            escaped = True
            continue
        if character == "[" and not in_character_class:
            in_character_class = True
            continue
        if character == "]" and in_character_class:
            in_character_class = False
            continue
        if in_character_class or character != "{":
            continue
        match = re.match(r"\{(\d+)(?:,(\d*))?\}", pattern[index:])
        if match is None:
            continue
        for digits in match.groups():
            if digits is None or digits == "":
                continue
            normalized = digits.lstrip("0") or "0"
            limit = str(_MAX_LITERAL_PATTERN_TOKENS)
            if len(normalized) > len(limit) or (
                len(normalized) == len(limit) and normalized > limit
            ):
                return True
    return False


def _bounded_repeat(
    fragment: str, index: int
) -> tuple[int, int, int] | None:
    if index < len(fragment) and fragment[index] == "?":
        return 0, 1, index + 1
    match = re.match(r"\{(\d+)(?:,(\d+))?\}", fragment[index:])
    if match is None:
        return 1, 1, index
    minimum = int(match.group(1))
    maximum = int(match.group(2) or match.group(1))
    if maximum < minimum or maximum > _MAX_LITERAL_PATTERN_TOKENS:
        return None
    return minimum, maximum, index + match.end()


def _repeat_literal_choices(
    choices: list[tuple[str, ...]], minimum: int, maximum: int
) -> list[tuple[str, ...]] | None:
    repeated: list[tuple[str, ...]] = []
    current: list[tuple[str, ...]] = [()]
    if minimum == 0:
        repeated.append(())
    for count in range(1, maximum + 1):
        current = [prefix + choice for prefix in current for choice in choices]
        if (
            len(current) > _MAX_LITERAL_PATTERN_VARIANTS
            or any(len(tokens) > _MAX_LITERAL_PATTERN_TOKENS for tokens in current)
        ):
            return None
        if count >= minimum:
            repeated.extend(current)
            if len(repeated) > _MAX_LITERAL_PATTERN_VARIANTS:
                return None
    return repeated


def _literal_bounded_variants(fragment: str) -> list[tuple[str, ...]] | None:
    variants: list[tuple[str, ...]] = [()]
    value = _strip_group_extension(fragment)
    index = 0
    while index < len(value):
        atom = _literal_atom_choices(value, index)
        if atom is None:
            return None
        choices, index = atom
        repeat = _bounded_repeat(value, index)
        if repeat is None:
            return None
        minimum, maximum, index = repeat
        repeated_choices = _repeat_literal_choices(choices, minimum, maximum)
        if repeated_choices is None:
            return None
        variants = [
            prefix + choice for prefix in variants for choice in repeated_choices
        ]
        if (
            len(variants) > _MAX_LITERAL_PATTERN_VARIANTS
            or any(len(tokens) > _MAX_LITERAL_PATTERN_TOKENS for tokens in variants)
        ):
            return None
    return variants


def _has_ambiguous_literal_paths(fragment: str) -> bool:
    alternatives = _top_level_alternatives(_strip_redundant_groups(fragment))
    variants: list[tuple[str, ...]] = []
    for alternative in alternatives:
        alternative_variants = _literal_bounded_variants(alternative)
        if alternative_variants is None:
            return True
        variants.extend(alternative_variants)
        if len(variants) > _MAX_LITERAL_PATTERN_VARIANTS:
            return True
    return any(
        not left or (len(left) <= len(right) and right[: len(left)] == left)
        for left_index, left in enumerate(variants)
        for right_index, right in enumerate(variants)
        if left_index != right_index
    )


def _pattern_has_structural_redos_risk(pattern: str) -> bool:
    if _has_adjacent_ambiguous_quantified_atoms(pattern):
        return True
    for opening, closing in _group_spans(pattern):
        if not _is_repeated_group(pattern, closing):
            continue
        body = pattern[opening + 1 : closing]
        if (
            _contains_unbounded_quantifier(body)
            or _has_ambiguous_literal_paths(body)
        ):
            return True
    return False


def _fingerprint_token(digest: object, token: str) -> None:
    encoded = token.encode("utf-8", errors="backslashreplace")
    digest.update(len(encoded).to_bytes(8, "big"))
    digest.update(encoded)


def _json_fingerprint(value: object, budget: list[int] | None = None) -> bytes | None:
    """Create a bounded, recursion-free fingerprint for JSON-like graphs."""
    if budget is None:
        budget = [_MAX_JSON_EQUALITY_EVALUATIONS]
    digest = hashlib.sha256()
    pending: list[tuple[str, object]] = [("value", value)]
    active: set[int] = set()
    while pending:
        action, current = pending.pop()
        if action == "end":
            active.remove(id(current))
            _fingerprint_token(digest, "]")
            continue
        if budget[0] <= 0:
            return None
        budget[0] -= 1
        if isinstance(current, bool):
            _fingerprint_token(digest, f"bool:{int(current)}")
            continue
        if isinstance(current, (int, float)):
            try:
                numerator, denominator = current.as_integer_ratio()
                _fingerprint_token(digest, f"number:{numerator}/{denominator}")
            except (OverflowError, ValueError):
                _fingerprint_token(
                    digest,
                    f"number-special:{type(current).__name__}:{current!r}",
                )
            continue
        if current is None:
            _fingerprint_token(digest, "null")
            continue
        if isinstance(current, str):
            _fingerprint_token(digest, "string")
            _fingerprint_token(digest, current)
            continue
        if isinstance(current, (list, Mapping)):
            identity = id(current)
            if identity in active:
                _fingerprint_token(digest, "cycle")
                continue
            pending_entries = len(current) if isinstance(current, list) else 2 * len(current)
            if pending_entries > budget[0]:
                return None
            active.add(identity)
            _fingerprint_token(
                digest,
                f"{type(current).__module__}.{type(current).__qualname__}:{len(current)}[",
            )
            pending.append(("end", current))
            if isinstance(current, list):
                pending.extend(("value", item) for item in reversed(current))
            else:
                if not all(isinstance(key, str) for key in current):
                    return None
                for key in reversed(sorted(current)):
                    pending.append(("value", current[key]))
                    pending.append(("value", key))
            continue
        _fingerprint_token(
            digest,
            f"{type(current).__module__}.{type(current).__qualname__}:{current!r}",
        )
    return digest.digest()


def _enum_values_unique(enum: list[object], budget: list[int]) -> bool | None:
    fingerprints: dict[bytes, object] = {}
    for option in enum:
        fingerprint = _json_fingerprint(option, budget)
        if fingerprint is None:
            return None
        if fingerprint in fingerprints:
            equal = _json_equal(option, fingerprints[fingerprint], budget)
            if equal is None:
                return None
            # A duplicate or a digest collision both fail closed without an
            # attacker-controlled quadratic collision bucket.
            return False
        fingerprints[fingerprint] = option
    return True


def _keyword_shapes_valid(schema: Mapping[str, object]) -> bool:
    if "properties" in schema and not isinstance(schema["properties"], Mapping):
        return False
    if "required" in schema:
        required = schema["required"]
        if (
            not isinstance(required, list)
            or not all(isinstance(field, str) for field in required)
            or len(required) != len(set(required))
        ):
            return False
    if "enum" in schema:
        enum = schema["enum"]
        if (
            not isinstance(enum, list)
            or not enum
            or len(enum) > MAX_SCHEMA_EVALUATIONS
        ):
            return False
    if "type" in schema:
        expected = schema["type"]
        if isinstance(expected, str):
            if expected not in _SUPPORTED_TYPES:
                return False
        elif (
            not isinstance(expected, list)
            or not expected
            or not all(
                isinstance(option, str) and option in _SUPPORTED_TYPES
                for option in expected
            )
            or len(expected) != len(set(expected))
        ):
            return False
    for keyword in ("minimum", "maximum"):
        if keyword in schema:
            value = schema[keyword]
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                return False
    for keyword in ("minLength", "maxLength", "minItems", "maxItems"):
        if keyword in schema:
            value = schema[keyword]
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                return False
    if "pattern" in schema and not isinstance(schema["pattern"], str):
        return False
    if "additionalProperties" in schema and not isinstance(
        schema["additionalProperties"], bool
    ):
        return False
    if "uniqueItems" in schema and not isinstance(schema["uniqueItems"], bool):
        return False
    if "format" in schema and schema["format"] != "date":
        return False
    if "$ref" in schema and not isinstance(schema["$ref"], str):
        return False
    return True


def _pattern_error(pattern: str) -> str | None:
    if (
        len(pattern) > MAX_SCHEMA_PATTERN_LENGTH
        or _has_oversized_quantifier(pattern)
        or _NESTED_QUANTIFIER.search(pattern)
        or _pattern_has_structural_redos_risk(pattern)
    ):
        return SCHEMA_PATTERN_COMPLEXITY_ERROR
    try:
        re.compile(pattern)
    except (re.error, OverflowError):
        return SCHEMA_PATTERN_INVALID_ERROR
    return None


def _safe_diagnostic_field_name(value: object) -> str:
    return safe_diagnostic_field_name(str(value))


def _pointer(root: Mapping[str, object], reference: str) -> Mapping[str, object]:
    if reference == "#":
        return root
    if not reference.startswith("#/"):
        raise ValueError("unsupported schema reference")
    value: object = root
    for part in reference[2:].split("/"):
        if re.search(r"~(?:[^01]|$)", part):
            raise ValueError("invalid JSON Pointer escape")
        value = value[part.replace("~1", "/").replace("~0", "~")]  # type: ignore[index]
    return value  # type: ignore[return-value]


def _preflight_schema(
    schema: object,
    root: Mapping[str, object],
    *,
    _depth: int = 0,
    budget: list[int],
    active_schema_nodes: set[int] | None = None,
    checked_schema_nodes: set[int] | None = None,
) -> list[str]:
    """Validate the complete supported schema grammar before instance traversal."""
    if _depth > MAX_SCHEMA_VALIDATION_DEPTH:
        return [SCHEMA_DEPTH_ERROR]
    if budget[0] <= 0:
        return [SCHEMA_EVALUATION_LIMIT_ERROR]
    budget[0] -= 1
    if not isinstance(schema, Mapping):
        return ["schema branch is invalid"]
    if active_schema_nodes is None:
        active_schema_nodes = set()
    if checked_schema_nodes is None:
        checked_schema_nodes = set()
    schema_identity = id(schema)
    if schema_identity in active_schema_nodes:
        return [SCHEMA_EVALUATION_LIMIT_ERROR]
    if schema_identity in checked_schema_nodes:
        return []
    if not _keyword_shapes_valid(schema):
        return [SCHEMA_KEYWORD_INVALID_ERROR]
    if "enum" in schema:
        unique = _enum_values_unique(schema["enum"], budget)
        if unique is None:
            return [SCHEMA_EVALUATION_LIMIT_ERROR]
        if not unique:
            return [SCHEMA_KEYWORD_INVALID_ERROR]
    if "pattern" in schema:
        pattern_error = _pattern_error(schema["pattern"])
        if pattern_error is not None:
            if pattern_error == SCHEMA_PATTERN_COMPLEXITY_ERROR:
                return [f"$: {pattern_error}"]
            return [pattern_error]

    properties = schema.get("properties", {})
    definitions = schema.get("$defs", {})
    if not isinstance(properties, Mapping) or not isinstance(definitions, Mapping):
        return ["schema branch is invalid"]
    if not all(isinstance(name, str) for name in (*properties, *definitions)):
        return ["schema branch is invalid"]

    child_schemas: list[object] = [*properties.values(), *definitions.values()]
    for combinator in ("oneOf", "anyOf", "allOf"):
        if combinator not in schema:
            continue
        branches = schema[combinator]
        if (
            not isinstance(branches, list)
            or not branches
            or any(not isinstance(branch, Mapping) for branch in branches)
        ):
            return ["schema branch is invalid"]
        child_schemas.extend(branches)
    for branch_name in ("items", "contains", "if", "then", "else", "not"):
        if branch_name in schema:
            branch = schema[branch_name]
            if not isinstance(branch, Mapping):
                return ["schema branch is invalid"]
            child_schemas.append(branch)

    if "$ref" in schema:
        try:
            target = _pointer(root, schema["$ref"])
        except (KeyError, TypeError, AttributeError, IndexError, ValueError):
            return ["schema reference is invalid"]
        if not isinstance(target, Mapping):
            return ["schema reference is invalid"]

    active_schema_nodes.add(schema_identity)
    try:
        for child_schema in child_schemas:
            child_errors = _preflight_schema(
                child_schema,
                root,
                _depth=_depth + 1,
                budget=budget,
                active_schema_nodes=active_schema_nodes,
                checked_schema_nodes=checked_schema_nodes,
            )
            if child_errors:
                return child_errors
    finally:
        active_schema_nodes.remove(schema_identity)
    checked_schema_nodes.add(schema_identity)
    return []


def _type_ok(value: object, expected: object) -> bool:
    if isinstance(expected, list):
        return any(_type_ok(value, option) for option in expected)
    if not isinstance(expected, str):
        return True
    return {
        "object": isinstance(value, Mapping),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "boolean": isinstance(value, bool),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "number": isinstance(value, (int, float)) and not isinstance(value, bool),
        "null": value is None,
    }.get(expected, True)


def _json_equal(
    left: object, right: object, budget: list[int] | None = None
) -> bool | None:
    """Compare JSON graphs iteratively; return ``None`` on bounded exhaustion."""
    if budget is None:
        budget = [_MAX_JSON_EQUALITY_EVALUATIONS]
    pending = [(left, right)]
    seen: set[tuple[int, int]] = set()
    while pending:
        if budget[0] <= 0:
            return None
        budget[0] -= 1
        current_left, current_right = pending.pop()
        if isinstance(current_left, bool) or isinstance(current_right, bool):
            if not (
                isinstance(current_left, bool)
                and isinstance(current_right, bool)
                and current_left == current_right
            ):
                return False
            continue
        if isinstance(current_left, (int, float)) and isinstance(
            current_right, (int, float)
        ):
            if current_left != current_right:
                return False
            continue
        if current_left is current_right:
            continue
        if type(current_left) is not type(current_right):
            return False
        if isinstance(current_left, list):
            if len(current_left) != len(current_right):
                return False
            pair = (id(current_left), id(current_right))
            if pair in seen:
                continue
            seen.add(pair)
            pending.extend(zip(current_left, current_right))
            continue
        if isinstance(current_left, Mapping):
            if set(current_left) != set(current_right):
                return False
            pair = (id(current_left), id(current_right))
            if pair in seen:
                continue
            seen.add(pair)
            pending.extend(
                (current_left[key], current_right[key]) for key in current_left
            )
            continue
        if current_left != current_right:
            return False
    return True


def _validate(
    value: object,
    schema: Mapping[str, object],
    root: Mapping[str, object],
    path: str,
    *,
    collect: bool = True,
    _depth: int = 0,
    budget: list[int] | None = None,
    active_ref_targets: set[int] | None = None,
) -> list[str]:
    if _depth > MAX_SCHEMA_VALIDATION_DEPTH:
        return [SCHEMA_DEPTH_ERROR]
    if budget is None:
        budget = [MAX_SCHEMA_EVALUATIONS]
    if active_ref_targets is None:
        active_ref_targets = set()
    if not isinstance(schema, Mapping):
        return ["schema branch is invalid"]
    if not _keyword_shapes_valid(schema):
        return [SCHEMA_KEYWORD_INVALID_ERROR]
    if "pattern" in schema:
        pattern_error = _pattern_error(schema["pattern"])
        if pattern_error is not None:
            if pattern_error == SCHEMA_PATTERN_COMPLEXITY_ERROR:
                return [f"{path}: {pattern_error}"]
            return [pattern_error]
    for combinator in ("oneOf", "anyOf", "allOf"):
        if combinator in schema:
            branches = schema[combinator]
            if not isinstance(branches, list) or any(
                not isinstance(branch, Mapping) for branch in branches
            ):
                return ["schema branch is invalid"]
    properties = schema.get("properties", {})
    if isinstance(properties, Mapping) and any(
        not isinstance(branch, Mapping) for branch in properties.values()
    ):
        return ["schema branch is invalid"]
    definitions = schema.get("$defs", {})
    if not isinstance(definitions, Mapping):
        return ["schema branch is invalid"]
    for branch_name in ("items", "contains", "if", "then", "else", "not"):
        if branch_name in schema and not isinstance(schema[branch_name], Mapping):
            return ["schema branch is invalid"]
    if budget[0] <= 0:
        return [SCHEMA_EVALUATION_LIMIT_ERROR]
    budget[0] -= 1
    errors: list[str] = []
    if "$ref" in schema:
        reference = schema["$ref"]
        if not isinstance(reference, str):
            return ["schema reference is invalid"]
        try:
            target = _pointer(root, reference)
        except (KeyError, TypeError, AttributeError, IndexError, ValueError):
            return ["schema reference is invalid"]
        if not isinstance(target, Mapping):
            return ["schema reference is invalid"]
        target_identity = id(target)
        if target_identity in active_ref_targets:
            return [SCHEMA_EVALUATION_LIMIT_ERROR]
        active_ref_targets.add(target_identity)
        try:
            errors.extend(
                _validate(
                    value,
                    target,
                    root,
                    path,
                    collect=collect,
                    _depth=_depth + 1,
                    budget=budget,
                    active_ref_targets=active_ref_targets,
                )
            )
        finally:
            active_ref_targets.remove(target_identity)
    if "type" in schema and not _type_ok(value, schema["type"]):
        return [f"{path}: type mismatch"]
    if "const" in schema:
        equal = _json_equal(value, schema["const"], budget)
        if equal is None:
            errors.append(SCHEMA_EVALUATION_LIMIT_ERROR)
        elif not equal:
            errors.append(f"{path}: const mismatch")
    if "enum" in schema:
        matched = False
        exhausted = False
        for option in schema["enum"]:
            equal = _json_equal(value, option, budget)
            if equal is None:
                exhausted = True
                break
            if equal:
                matched = True
                break
        if exhausted:
            errors.append(SCHEMA_EVALUATION_LIMIT_ERROR)
        elif not matched:
            errors.append(f"{path}: enum mismatch")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{path}: number below minimum")
        if "maximum" in schema and value > schema["maximum"]:
            errors.append(f"{path}: number above maximum")
    if "pattern" in schema and isinstance(value, str):
        if re.search(schema["pattern"], value) is None:
            errors.append(f"{path}: pattern mismatch")
    if isinstance(value, str):
        if "minLength" in schema and len(value) < schema["minLength"]:
            errors.append(f"{path}: string too short")
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            errors.append(f"{path}: string too long")
        if schema.get("format") == "date":
            try:
                dt.date.fromisoformat(value)
            except ValueError:
                errors.append(f"{path}: invalid date format")
    if isinstance(value, Mapping):
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            errors.extend(
                f"{path}: unsupported field {_safe_diagnostic_field_name(key)}"
                for key in value
                if key not in properties
            )
        for key in schema.get("required", []):
            if key not in value:
                errors.append(
                    f"{path}: missing required field {_safe_diagnostic_field_name(key)}"
                )
        for key, child_schema in properties.items():
            if key in value:
                safe_key = _safe_diagnostic_field_name(key)
                errors.extend(
                    _validate(
                        value[key],
                        child_schema,
                        root,
                        f"{path}.{safe_key}",
                        _depth=_depth + 1,
                        budget=budget,
                        active_ref_targets=active_ref_targets,
                    )
                )
    if isinstance(value, list):
        if "minItems" in schema and len(value) < schema["minItems"]:
            errors.append(f"{path}: too few items")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            errors.append(f"{path}: too many items")
        if schema.get("uniqueItems") and len({repr(item) for item in value}) != len(value):
            errors.append(f"{path}: duplicate items")
        if "items" in schema:
            for index, child in enumerate(value):
                errors.extend(
                    _validate(
                        child,
                        schema["items"],
                        root,
                        f"{path}[{index}]",
                        _depth=_depth + 1,
                        budget=budget,
                        active_ref_targets=active_ref_targets,
                    )
                )
        if "contains" in schema and not any(
            not _validate(
                child,
                schema["contains"],
                root,
                f"{path}[{index}]",
                _depth=_depth + 1,
                budget=budget,
                active_ref_targets=active_ref_targets,
            )
            for index, child in enumerate(value)
        ):
            errors.append(f"{path}: contains mismatch")
    for branch in schema.get("allOf", []):
        errors.extend(
            _validate(
                value,
                branch,
                root,
                path,
                _depth=_depth + 1,
                budget=budget,
                active_ref_targets=active_ref_targets,
            )
        )
    if "oneOf" in schema:
        matches = sum(
            not _validate(
                value,
                branch,
                root,
                path,
                _depth=_depth + 1,
                budget=budget,
                active_ref_targets=active_ref_targets,
            )
            for branch in schema["oneOf"]
        )
        if matches != 1:
            errors.append(f"{path}: oneOf mismatch")
    if "anyOf" in schema:
        if not any(
            not _validate(
                value,
                branch,
                root,
                path,
                _depth=_depth + 1,
                budget=budget,
                active_ref_targets=active_ref_targets,
            )
            for branch in schema["anyOf"]
        ):
            errors.append(f"{path}: anyOf mismatch")
    if "not" in schema and not _validate(
        value,
        schema["not"],
        root,
        path,
        _depth=_depth + 1,
        budget=budget,
        active_ref_targets=active_ref_targets,
    ):
        errors.append(f"{path}: not mismatch")
    if "if" in schema:
        condition_matches = (
            _validate(
                value,
                schema["if"],
                root,
                path,
                collect=False,
                _depth=_depth + 1,
                budget=budget,
                active_ref_targets=active_ref_targets,
            )
            == []
        )
        branch = schema.get("then", {}) if condition_matches else schema.get("else", {})
        if branch:
            errors.extend(
                _validate(
                    value,
                    branch,
                    root,
                    path,
                    _depth=_depth + 1,
                    budget=budget,
                    active_ref_targets=active_ref_targets,
                )
            )
    return errors


def validate_schema_instance(
    value: object, schema: Mapping[str, object]
) -> list[str]:
    """Return bounded schema errors for the supported keyword subset."""
    budget = [MAX_SCHEMA_EVALUATIONS]
    preflight_errors = _preflight_schema(schema, schema, budget=budget)
    if preflight_errors:
        return sorted(set(preflight_errors))
    errors = _validate(value, schema, schema, "$", budget=budget)
    if budget[0] <= 0:
        errors.append(SCHEMA_EVALUATION_LIMIT_ERROR)
    return sorted(set(errors))
