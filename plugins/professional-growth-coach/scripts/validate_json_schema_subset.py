"""Dependency-free validator for the JSON Schema subset used by this plugin."""

from __future__ import annotations

import datetime as dt
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
    r"\((?:[^()\\]|\\.)*(?:[+*]|\{\d+(?:,\d*)?\})(?:[^()\\]|\\.)*\)"
    r"(?:[+*]|\{\d+(?:,\d*)?\})"
)


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
        if character in "+*{":
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


def _literal_tokens(fragment: str) -> tuple[str, ...] | None:
    tokens: list[str] = []
    index = 0
    while index < len(fragment):
        character = fragment[index]
        if character == "\\":
            index += 1
            if index >= len(fragment) or fragment[index].isalnum():
                return None
            tokens.append(fragment[index])
        elif character.isalnum() or character in " _-'":
            tokens.append(character)
        else:
            return None
        index += 1
    return tuple(tokens)


def _literal_optional_variants(fragment: str) -> list[tuple[str, ...]] | None:
    variants: list[tuple[str, ...]] = [()]
    value = _strip_group_extension(fragment)
    index = 0
    while index < len(value):
        character = value[index]
        if character == "\\":
            index += 1
            if index >= len(value) or value[index].isalnum():
                return None
            token = value[index]
        elif character.isalnum() or character in " _-'":
            token = character
        else:
            return None
        optional = index + 1 < len(value) and value[index + 1] == "?"
        extended = [variant + (token,) for variant in variants]
        variants = variants + extended if optional else extended
        if len(variants) > 256:
            return None
        index += 2 if optional else 1
    return variants


def _has_ambiguous_optional_paths(fragment: str) -> bool:
    alternatives = _top_level_alternatives(_strip_redundant_groups(fragment))
    if not any("?" in alternative for alternative in alternatives):
        return False
    variants: list[tuple[str, ...]] = []
    for alternative in alternatives:
        alternative_variants = _literal_optional_variants(alternative)
        if alternative_variants is None:
            return True
        variants.extend(alternative_variants)
    return any(
        not left or (len(left) <= len(right) and right[: len(left)] == left)
        for left_index, left in enumerate(variants)
        for right_index, right in enumerate(variants)
        if left_index != right_index
    )


def _has_overlapping_literal_alternatives(fragment: str) -> bool:
    alternatives = _top_level_alternatives(_strip_redundant_groups(fragment))
    if len(alternatives) < 2:
        return False
    tokenized = [_literal_tokens(alternative) for alternative in alternatives]
    if any(tokens is None or not tokens for tokens in tokenized):
        return False
    return any(
        len(left) <= len(right) and right[: len(left)] == left
        for left_index, left in enumerate(tokenized)
        for right_index, right in enumerate(tokenized)
        if left_index != right_index
    )


def _pattern_has_structural_redos_risk(pattern: str) -> bool:
    for opening, closing in _group_spans(pattern):
        if not _is_repeated_group(pattern, closing):
            continue
        body = pattern[opening + 1 : closing]
        if (
            _contains_unbounded_quantifier(body)
            or _has_overlapping_literal_alternatives(body)
            or _has_ambiguous_optional_paths(body)
        ):
            return True
    return False


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
        if not isinstance(enum, list) or not enum:
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
        or _NESTED_QUANTIFIER.search(pattern)
        or _pattern_has_structural_redos_risk(pattern)
    ):
        return SCHEMA_PATTERN_COMPLEXITY_ERROR
    try:
        re.compile(pattern)
    except re.error:
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
    left: object, right: object, seen: set[tuple[int, int]] | None = None
) -> bool:
    """Compare JSON values without Python's bool/int equality quirk."""
    if seen is None:
        seen = set()
    if isinstance(left, bool) or isinstance(right, bool):
        return isinstance(left, bool) and isinstance(right, bool) and left == right
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return left == right
    if type(left) is not type(right):
        return False
    if isinstance(left, list) and isinstance(right, list):
        pair = (id(left), id(right))
        if pair in seen:
            return True
        seen.add(pair)
        return len(left) == len(right) and all(
            _json_equal(item, other, seen) for item, other in zip(left, right)
        )
    if isinstance(left, Mapping) and isinstance(right, Mapping):
        pair = (id(left), id(right))
        if pair in seen:
            return True
        seen.add(pair)
        return set(left) == set(right) and all(
            _json_equal(left[key], right[key], seen) for key in left
        )
    return left == right


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
    if "const" in schema and not _json_equal(value, schema["const"]):
        errors.append(f"{path}: const mismatch")
    if "enum" in schema and not any(
        _json_equal(value, option) for option in schema["enum"]
    ):
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
