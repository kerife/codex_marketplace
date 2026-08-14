#!/usr/bin/env python3
"""Independently validate derived career market learning dossiers."""

from __future__ import annotations

import copy
import re
from collections.abc import Mapping

from dossier_snapshot import snapshot_for_dossier
from private_prose_safety import contains_unicode_controls
from validate_executive_career_dossier_v2 import validate_dossier
from validate_target_vacancy_research import (
    snapshot_for_market_dossier,
    validate_research,
)


SUPPORT_NUMERATORS = {
    "verified_match": 2,
    "candidate_reported_match": 2,
    "adjacent_evidence": 1,
    "explicit_gap": 0,
    "unknown": 0,
}
IMPORTANCE_WEIGHTS = {"must_have": 2, "preferred": 1, "responsibility_only": 0}
TOP_FIELDS = frozenset(
    {
        "schema_version",
        "locale",
        "as_of_date",
        "state",
        "source_research_snapshot",
        "source_executive_dossier_snapshot",
        "search_summary",
        "vacancies",
        "matrix_rows",
        "recurrence_rows",
        "learning_state",
        "learning_decisions",
        "methodology_boundaries",
        "privacy_boundary",
        "no_external_action",
    }
)
SUMMARY_FIELDS = frozenset(
    {
        "locale",
        "as_of_date",
        "state",
        "vacancy_count",
        "maximum_vacancies",
        "bounded_queries_run",
        "limit_reason",
        "limitation",
    }
)
CARD_FIELDS = frozenset(
    {
        "vacancy_id",
        "employer_id",
        "employer",
        "title",
        "role_family",
        "location",
        "arrangement",
        "geographic_compatibility",
        "source_kind",
        "source_url",
        "official_referrer_url",
        "source_state",
        "access_date",
        "publication_date",
        "freshness_status",
        "earned_points",
        "maximum_points",
        "known_points",
        "alignment_percent",
        "evidence_coverage_percent",
        "interpretation",
        "qualitative_band",
    }
)
MATRIX_FIELDS = frozenset({"signal", "support_state", "evidence_ids", "cells"})
CELL_FIELDS = frozenset({"vacancy_id", "required", "requirements"})
REQUIREMENT_FIELDS = frozenset({"requirement_id", "importance", "source_paraphrase"})
RECURRENCE_FIELDS = frozenset(
    {"signal", "occurrences", "sample_size", "display_fraction", "support_state", "evidence_ids"}
)
METHODOLOGY_BOUNDARIES = [
    "directional_documented_evidence_not_hiring_fit",
    "no_keyword_or_prose_match_inference",
    "no_sample_wide_score",
    "unknown_preserved_separately_from_explicit_gap",
]
STATES = {"complete", "limited_market_evidence", "market_evidence_unavailable"}
BANDS = {
    "insufficient_evidence",
    "higher_documented_alignment",
    "moderate_documented_alignment",
    "lower_documented_alignment",
}
_DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}\Z")
_VACANCY_ID = re.compile(r"V-[0-9]{3}\Z")
_EMPLOYER_ID = re.compile(r"EMP-[0-9]{3}\Z")
_REQUIREMENT_ID = re.compile(r"V-[0-9]{3}-R-[0-9]{2}\Z")
_EVIDENCE_ID = re.compile(r"E-[0-9]{3}\Z")
_MARKET_SNAPSHOT = re.compile(r"snap-market-sha256-[0-9a-f]{64}\Z")
_DOSSIER_SNAPSHOT = re.compile(r"snap-dossier-sha256-[0-9a-f]{64}\Z")
_EMAIL = re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")
_PHONE = re.compile(r"(?:^|\s)\+?\d[\d .()_-]{6,}\d(?:$|\s)")
_HTML = re.compile(r"<\s*/?\s*(?:script|style|html|body|div|span|iframe)\b", re.I)


def _bounded(errors: list[str]) -> list[str]:
    return sorted(set(errors))[:40]


def _closed(
    value: object, fields: frozenset[str], diagnostic: str, errors: list[str]
) -> Mapping[str, object] | None:
    if not isinstance(value, Mapping):
        errors.append(diagnostic)
        return None
    try:
        keys = set(value)
    except (TypeError, ValueError, RecursionError):
        errors.append(diagnostic)
        return None
    if keys != fields:
        errors.append(diagnostic)
    return value


def _int(value: object, minimum: int = 0, maximum: int | None = None) -> bool:
    return (
        type(value) is int
        and value >= minimum
        and (maximum is None or value <= maximum)
    )


def _text(value: object, maximum: int = 500) -> bool:
    return isinstance(value, str) and 0 < len(value) <= maximum


def _ids(value: object) -> bool:
    return (
        isinstance(value, list)
        and len(value) <= 20
        and all(isinstance(item, str) and _EVIDENCE_ID.fullmatch(item) for item in value)
        and len(value) == len(set(value))
    )


def _private_content(value: object, stack: set[int] | None = None, depth: int = 0) -> bool:
    if depth > 16:
        return True
    if stack is None:
        stack = set()
    if isinstance(value, Mapping) or isinstance(value, list):
        identifier = id(value)
        if identifier in stack:
            return True
        stack.add(identifier)
        try:
            nested_values = value.values() if isinstance(value, Mapping) else value
            return any(_private_content(item, stack, depth + 1) for item in nested_values)
        finally:
            stack.remove(identifier)
    if not isinstance(value, str):
        return False
    phone_match = any(
        not _DATE.fullmatch(match.group().strip()) for match in _PHONE.finditer(value)
    )
    return bool(
        contains_unicode_controls(value)
        or _EMAIL.search(value)
        or phone_match
        or _HTML.search(value)
    )


def _rounded_percent(numerator: int, denominator: int) -> int:
    return (100 * numerator + denominator // 2) // denominator if denominator else 0


def _band(alignment_percent: int, coverage_percent: int) -> str:
    if coverage_percent < 50:
        return "insufficient_evidence"
    if alignment_percent >= 75:
        return "higher_documented_alignment"
    if alignment_percent >= 50:
        return "moderate_documented_alignment"
    return "lower_documented_alignment"


def _validate_summary(root: Mapping[str, object], errors: list[str]) -> Mapping[str, object] | None:
    summary = _closed(root.get("search_summary"), SUMMARY_FIELDS, "search summary has invalid closed structure", errors)
    if summary is None:
        return None
    if summary.get("locale") not in {"es", "en"} or summary.get("locale") != root.get("locale"):
        errors.append("search summary locale must match dossier locale")
    if not isinstance(summary.get("as_of_date"), str) or not _DATE.fullmatch(summary["as_of_date"]) or summary.get("as_of_date") != root.get("as_of_date"):
        errors.append("search summary date must match dossier date")
    if summary.get("state") not in STATES or summary.get("state") != root.get("state"):
        errors.append("search summary state must match dossier state")
    if not _int(summary.get("vacancy_count"), 0, 5) or summary.get("maximum_vacancies") != 5:
        errors.append("search summary vacancy counts are invalid")
    if not _int(summary.get("bounded_queries_run"), 0, 1000):
        errors.append("search summary query count is invalid")
    if summary.get("limit_reason") not in {"target_reached", "bounded_search_exhausted", "market_evidence_unavailable"} or not _text(summary.get("limitation")):
        errors.append("search summary limit is invalid")
    return summary


def _validate_cards(root: Mapping[str, object], errors: list[str]) -> tuple[list[Mapping[str, object]], list[str]]:
    raw = root.get("vacancies")
    if not isinstance(raw, list) or len(raw) > 5:
        errors.append("vacancy cards are invalid")
        return [], []
    cards: list[Mapping[str, object]] = []
    identifiers: list[str] = []
    for item in raw:
        card = _closed(item, CARD_FIELDS, "vacancy card has invalid closed structure", errors)
        if card is None:
            continue
        identifier = card.get("vacancy_id")
        if not isinstance(identifier, str) or not _VACANCY_ID.fullmatch(identifier):
            errors.append("vacancy card has invalid identifier")
        else:
            identifiers.append(identifier)
        if not isinstance(card.get("employer_id"), str) or not _EMPLOYER_ID.fullmatch(card["employer_id"]):
            errors.append("vacancy card has invalid employer identifier")
        for field in ("employer", "title", "location"):
            if not _text(card.get(field)):
                errors.append("vacancy card has invalid public metadata")
        if card.get("role_family") not in {"site_reliability_engineering", "platform_engineering", "devops_engineering"}:
            errors.append("vacancy card has invalid role family")
        if card.get("arrangement") not in {"onsite", "hybrid", "remote", "flexible"}:
            errors.append("vacancy card has invalid arrangement")
        if card.get("geographic_compatibility") not in {"explicit_mexico", "stated_remote_unknown_eligibility"}:
            errors.append("vacancy card has invalid geography")
        if card.get("source_kind") not in {"official_employer", "employer_operated_ats", "linkedin_jobs_backup"}:
            errors.append("vacancy card has invalid source kind")
        source_url = card.get("source_url")
        referrer = card.get("official_referrer_url")
        if not isinstance(source_url, str) or not source_url.startswith("https://") or len(source_url) > 500:
            errors.append("vacancy card has invalid source URL")
        if referrer is not None and (not isinstance(referrer, str) or not referrer.startswith("https://") or len(referrer) > 500):
            errors.append("vacancy card has invalid referrer URL")
        if card.get("source_state") != "active" or card.get("freshness_status") not in {"current", "unknown"}:
            errors.append("vacancy card has invalid source state")
        if not isinstance(card.get("access_date"), str) or not _DATE.fullmatch(card["access_date"]) or card.get("access_date") != root.get("as_of_date"):
            errors.append("vacancy card access date must match dossier date")
        publication = card.get("publication_date")
        if publication is not None and (not isinstance(publication, str) or not _DATE.fullmatch(publication)):
            errors.append("vacancy card has invalid publication date")
        for field in ("earned_points", "maximum_points", "known_points", "alignment_percent", "evidence_coverage_percent"):
            if not _int(card.get(field), 0, 10000 if field.endswith("points") else 100):
                errors.append("vacancy card has invalid calculated field")
        if card.get("interpretation") != "directional_documented_evidence_not_hiring_fit" or card.get("qualitative_band") not in BANDS:
            errors.append("vacancy card has invalid interpretation")
        cards.append(card)
    if len(identifiers) != len(set(identifiers)):
        errors.append("vacancy card identifiers must be unique")
    if identifiers != [f"V-{index:03d}" for index in range(1, len(identifiers) + 1)]:
        # Cards are score-sorted, so only the set—not the display order—is canonical.
        if set(identifiers) != {f"V-{index:03d}" for index in range(1, len(identifiers) + 1)}:
            errors.append("vacancy card identifiers must form the canonical sequence")
    return cards, identifiers


def _validate_matrix(
    root: Mapping[str, object], vacancy_ids: list[str], errors: list[str]
) -> tuple[list[Mapping[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    raw = root.get("matrix_rows")
    if not isinstance(raw, list) or len(raw) > 150:
        errors.append("matrix rows are invalid")
        return [], [], []
    rows: list[Mapping[str, object]] = []
    bindings: list[dict[str, object]] = []
    vacancies = [{"vacancy_id": vacancy_id, "requirements": []} for vacancy_id in vacancy_ids]
    signals: list[str] = []
    for item in raw:
        row = _closed(item, MATRIX_FIELDS, "matrix row has invalid closed structure", errors)
        if row is None:
            continue
        signal = row.get("signal")
        state = row.get("support_state")
        identifiers = row.get("evidence_ids")
        if not _text(signal, 120):
            errors.append("matrix row has invalid signal")
            continue
        signals.append(signal)
        if state not in SUPPORT_NUMERATORS or not _ids(identifiers):
            errors.append("matrix row has invalid binding")
            continue
        if (state == "unknown") != (len(identifiers) == 0):
            errors.append("matrix row has incompatible evidence IDs")
        bindings.append({"signal": signal, "support_state": state, "evidence_ids": list(identifiers)})
        cells = row.get("cells")
        if not isinstance(cells, list) or len(cells) != len(vacancy_ids):
            errors.append("matrix row cells must match vacancy count")
            continue
        cell_ids: list[object] = []
        for index, item_cell in enumerate(cells):
            cell = _closed(item_cell, CELL_FIELDS, "matrix cell has invalid closed structure", errors)
            if cell is None:
                continue
            cell_ids.append(cell.get("vacancy_id"))
            requirements = cell.get("requirements")
            if type(cell.get("required")) is not bool or not isinstance(requirements, list) or len(requirements) > 30:
                errors.append("matrix cell has invalid requirement state")
                continue
            if cell["required"] != bool(requirements):
                errors.append("matrix cell required flag must match source requirements")
            for requirement_value in requirements:
                requirement = _closed(requirement_value, REQUIREMENT_FIELDS, "matrix requirement has invalid closed structure", errors)
                if requirement is None:
                    continue
                requirement_id = requirement.get("requirement_id")
                expected_vacancy_id = vacancy_ids[index] if index < len(vacancy_ids) else ""
                if not isinstance(requirement_id, str) or not _REQUIREMENT_ID.fullmatch(requirement_id) or not requirement_id.startswith(f"{expected_vacancy_id}-R-"):
                    errors.append("matrix requirement has invalid identifier")
                if requirement.get("importance") not in IMPORTANCE_WEIGHTS or not _text(requirement.get("source_paraphrase")):
                    errors.append("matrix requirement has invalid source data")
                if index < len(vacancies):
                    vacancies[index]["requirements"].append(
                        {"signal": signal, "importance": requirement.get("importance")}
                    )
        if cell_ids != vacancy_ids:
            errors.append("matrix cell order must match vacancy card order")
        rows.append(row)
    if len(signals) != len(set(signals)) or signals != sorted(signals):
        errors.append("matrix signals must be unique and ordered")
    if not vacancy_ids and rows:
        errors.append("matrix rows must be empty without vacancies")
    return rows, bindings, vacancies


def _score(requirements: list[dict[str, object]], bindings: list[dict[str, object]]) -> tuple[int, int, int]:
    by_signal = {binding["signal"]: binding for binding in bindings}
    earned = maximum = known = 0
    for requirement in requirements:
        binding = by_signal.get(requirement.get("signal"))
        weight = IMPORTANCE_WEIGHTS.get(requirement.get("importance"))
        if binding is None or weight is None:
            continue
        maximum += 2 * weight
        earned += SUPPORT_NUMERATORS[binding["support_state"]] * weight
        if binding["support_state"] != "unknown":
            known += 2 * weight
    return earned, maximum, known


def _validate_derived(
    cards: list[Mapping[str, object]],
    bindings: list[dict[str, object]],
    vacancies: list[dict[str, object]],
    root: Mapping[str, object],
    errors: list[str],
) -> None:
    expected_order: list[tuple[int, str]] = []
    for card, vacancy in zip(cards, vacancies, strict=False):
        earned, maximum, known = _score(vacancy["requirements"], bindings)
        alignment = _rounded_percent(earned, maximum)
        coverage = _rounded_percent(known, maximum)
        expected = {
            "earned_points": earned,
            "maximum_points": maximum,
            "known_points": known,
            "alignment_percent": alignment,
            "evidence_coverage_percent": coverage,
            "qualitative_band": _band(alignment, coverage),
        }
        if any(card.get(field) != value for field, value in expected.items()):
            errors.append("vacancy calculated fields must match matrix evidence")
        if isinstance(card.get("vacancy_id"), str):
            expected_order.append((alignment, card["vacancy_id"]))
    actual_ids = [card.get("vacancy_id") for card in cards]
    ordered_ids = [identifier for _, identifier in sorted(expected_order, key=lambda item: (-item[0], item[1]))]
    if actual_ids != ordered_ids:
        errors.append("vacancy cards must use calculated score order")

    raw_recurrence = root.get("recurrence_rows")
    if not isinstance(raw_recurrence, list):
        errors.append("recurrence rows are invalid")
        return
    expected_rows: list[dict[str, object]] = []
    sample_size = len(vacancies)
    if sample_size:
        for binding in bindings:
            signal = binding["signal"]
            occurrences = sum(
                any(requirement.get("signal") == signal for requirement in vacancy["requirements"])
                for vacancy in vacancies
            )
            expected_rows.append(
                {
                    "signal": signal,
                    "occurrences": occurrences,
                    "sample_size": sample_size,
                    "display_fraction": f"{occurrences}/{sample_size}",
                    "support_state": binding["support_state"],
                    "evidence_ids": binding["evidence_ids"],
                }
            )
        expected_rows.sort(key=lambda row: (-row["occurrences"], row["signal"]))
    if raw_recurrence != expected_rows:
        errors.append("recurrence rows must match matrix source data and dynamic sample size")


def _validate_recurrence_shape(root: Mapping[str, object], errors: list[str]) -> None:
    rows = root.get("recurrence_rows")
    if not isinstance(rows, list) or len(rows) > 150:
        errors.append("recurrence rows are invalid")
        return
    for item in rows:
        row = _closed(item, RECURRENCE_FIELDS, "recurrence row has invalid closed structure", errors)
        if row is None:
            continue
        if not _text(row.get("signal"), 120) or row.get("support_state") not in SUPPORT_NUMERATORS or not _ids(row.get("evidence_ids")):
            errors.append("recurrence row has invalid binding")
        if not _int(row.get("occurrences"), 0, 5) or not _int(row.get("sample_size"), 1, 5) or not _text(row.get("display_fraction"), 16):
            errors.append("recurrence row has invalid count")


def _validate_market_dossier_structure(value: object) -> list[str]:
    """Check only closed output structure and internal arithmetic consistency."""
    if not isinstance(value, Mapping):
        return ["market dossier must be an object"]
    try:
        errors: list[str] = []
        root = _closed(value, TOP_FIELDS, "market dossier has invalid closed structure", errors)
        if root is None:
            return _bounded(errors)
        if root.get("schema_version") != "career-market-learning-dossier-v1":
            errors.append("market dossier has invalid schema version")
        if root.get("locale") not in {"es", "en"}:
            errors.append("market dossier has invalid locale")
        if not isinstance(root.get("as_of_date"), str) or not _DATE.fullmatch(root["as_of_date"]):
            errors.append("market dossier has invalid as-of date")
        if root.get("state") not in STATES:
            errors.append("market dossier has invalid state")
        research_snapshot = root.get("source_research_snapshot")
        dossier_snapshot = root.get("source_executive_dossier_snapshot")
        if not isinstance(research_snapshot, str) or not _MARKET_SNAPSHOT.fullmatch(research_snapshot):
            errors.append("market dossier has invalid research snapshot")
        if not isinstance(dossier_snapshot, str) or not _DOSSIER_SNAPSHOT.fullmatch(dossier_snapshot):
            errors.append("market dossier has invalid dossier snapshot")
        summary = _validate_summary(root, errors)
        cards, vacancy_ids = _validate_cards(root, errors)
        _, bindings, vacancies = _validate_matrix(root, vacancy_ids, errors)
        _validate_recurrence_shape(root, errors)
        _validate_derived(cards, bindings, vacancies, root, errors)
        if summary is not None:
            count = len(cards)
            if summary.get("vacancy_count") != count:
                errors.append("search summary count must match vacancy cards")
            state_contract = {
                "complete": count == 5,
                "limited_market_evidence": 1 <= count <= 4,
                "market_evidence_unavailable": count == 0,
            }
            if state_contract.get(root.get("state")) is not True:
                errors.append("market dossier state and vacancy count are inconsistent")
            if summary.get("limit_reason") == "target_reached" and count != 5:
                errors.append("target_reached requires five vacancy cards")
        if root.get("learning_state") != "not_evaluated" or root.get("learning_decisions") != []:
            errors.append("market dossier learning placeholder is invalid")
        if root.get("methodology_boundaries") != METHODOLOGY_BOUNDARIES:
            errors.append("market dossier methodology boundaries are invalid")
        if root.get("privacy_boundary") != "public_vacancy_metadata_and_identity_free_evidence_references_only" or root.get("no_external_action") is not True:
            errors.append("market dossier privacy or action boundary is invalid")
        if _private_content(root):
            errors.append("market dossier contains forbidden private or control content")
        return _bounded(errors)
    except (AttributeError, KeyError, RecursionError, TypeError, ValueError):
        return ["market dossier has malformed structure"]


def _validated_binding_map(
    research: Mapping[str, object],
    executive_dossier: Mapping[str, object],
    alignment: object,
    errors: list[str],
) -> dict[str, Mapping[str, object]]:
    fields = {
        "schema_version",
        "research_snapshot",
        "executive_dossier_snapshot",
        "signal_bindings",
        "privacy_boundary",
    }
    if not isinstance(alignment, Mapping) or set(alignment) != fields:
        errors.append("alignment source has invalid closed structure")
        return {}
    if alignment.get("schema_version") != "candidate-market-alignment-v1" or alignment.get("privacy_boundary") != "identity_free_evidence_references_only":
        errors.append("alignment source has invalid contract fields")
    if alignment.get("research_snapshot") != snapshot_for_market_dossier(research):
        errors.append("alignment source research snapshot is stale")
    if alignment.get("executive_dossier_snapshot") != snapshot_for_dossier(executive_dossier):
        errors.append("alignment source dossier snapshot is stale")
    bindings = alignment.get("signal_bindings")
    if not isinstance(bindings, list) or len(bindings) > 150:
        errors.append("alignment source bindings are invalid")
        return {}
    result: dict[str, Mapping[str, object]] = {}
    for item in bindings:
        if not isinstance(item, Mapping) or set(item) != MATRIX_FIELDS - {"cells"}:
            errors.append("alignment source binding has invalid closed structure")
            continue
        signal = item.get("signal")
        state = item.get("support_state")
        identifiers = item.get("evidence_ids")
        if not _text(signal, 120) or signal in result or state not in SUPPORT_NUMERATORS or not _ids(identifiers):
            errors.append("alignment source binding is invalid")
            continue
        if (state == "unknown") != (len(identifiers) == 0):
            errors.append("alignment source binding has incompatible evidence IDs")
        result[signal] = item
    vacancies = research.get("vacancies")
    evidence = executive_dossier.get("evidence")
    if not isinstance(vacancies, list) or not isinstance(evidence, list):
        errors.append("market validation sources have malformed structure")
        return result
    expected_signals = {
        requirement["signal"]
        for vacancy in vacancies
        for requirement in vacancy["requirements"]
    }
    if set(result) != expected_signals:
        errors.append("alignment source bindings must cover research signals exactly")
    evidence_states = {
        row["id"]: row["state"]
        for row in evidence
        if isinstance(row, Mapping) and isinstance(row.get("id"), str)
    }
    allowed_states = {
        "verified_match": {"verified"},
        "candidate_reported_match": {"candidate_reported"},
        "adjacent_evidence": {"verified", "candidate_reported"},
        "explicit_gap": {"verified", "candidate_reported"},
        "unknown": set(),
    }
    for binding in result.values():
        state = binding["support_state"]
        if any(evidence_states.get(identifier) not in allowed_states[state] for identifier in binding["evidence_ids"]):
            errors.append("alignment source evidence state is incompatible")
    return result


def _expected_market_dossier(
    research: Mapping[str, object],
    alignment: Mapping[str, object],
    bindings: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    employers = {row["employer_id"]: row["display_name"] for row in research["employers"]}
    cards: list[dict[str, object]] = []
    for vacancy in research["vacancies"]:
        requirements = [
            {"signal": requirement["signal"], "importance": requirement["importance"]}
            for requirement in vacancy["requirements"]
        ]
        earned, maximum, known = _score(requirements, list(bindings.values()))
        alignment_percent = _rounded_percent(earned, maximum)
        coverage_percent = _rounded_percent(known, maximum)
        card = {
            field: copy.deepcopy(vacancy[field])
            for field in (
                "vacancy_id",
                "employer_id",
                "title",
                "role_family",
                "location",
                "arrangement",
                "geographic_compatibility",
                "source_kind",
                "source_url",
                "official_referrer_url",
                "source_state",
                "access_date",
                "publication_date",
                "freshness_status",
            )
        }
        card.update(
            {
                "employer": employers[vacancy["employer_id"]],
                "earned_points": earned,
                "maximum_points": maximum,
                "known_points": known,
                "alignment_percent": alignment_percent,
                "evidence_coverage_percent": coverage_percent,
                "interpretation": "directional_documented_evidence_not_hiring_fit",
                "qualitative_band": _band(alignment_percent, coverage_percent),
            }
        )
        cards.append(card)
    cards.sort(key=lambda row: (-row["alignment_percent"], row["vacancy_id"]))
    vacancy_order = [card["vacancy_id"] for card in cards]
    vacancy_by_id = {vacancy["vacancy_id"]: vacancy for vacancy in research["vacancies"]}
    matrix_rows: list[dict[str, object]] = []
    for signal in sorted(bindings):
        binding = bindings[signal]
        cells = []
        for vacancy_id in vacancy_order:
            source_requirements = [
                {
                    "requirement_id": requirement["requirement_id"],
                    "importance": requirement["importance"],
                    "source_paraphrase": requirement["source_paraphrase"],
                }
                for requirement in vacancy_by_id[vacancy_id]["requirements"]
                if requirement["signal"] == signal
            ]
            cells.append(
                {
                    "vacancy_id": vacancy_id,
                    "required": bool(source_requirements),
                    "requirements": source_requirements,
                }
            )
        matrix_rows.append(
            {
                "signal": signal,
                "support_state": binding["support_state"],
                "evidence_ids": list(binding["evidence_ids"]),
                "cells": cells,
            }
        )
    sample_size = len(research["vacancies"])
    recurrence: list[dict[str, object]] = []
    if sample_size:
        for signal, binding in bindings.items():
            occurrences = sum(
                any(requirement["signal"] == signal for requirement in vacancy["requirements"])
                for vacancy in research["vacancies"]
            )
            recurrence.append(
                {
                    "signal": signal,
                    "occurrences": occurrences,
                    "sample_size": sample_size,
                    "display_fraction": f"{occurrences}/{sample_size}",
                    "support_state": binding["support_state"],
                    "evidence_ids": list(binding["evidence_ids"]),
                }
            )
        recurrence.sort(key=lambda row: (-row["occurrences"], row["signal"]))
    limit = research["search_limit"]
    return {
        "schema_version": "career-market-learning-dossier-v1",
        "locale": research["locale"],
        "as_of_date": research["as_of_date"],
        "state": research["state"],
        "source_research_snapshot": alignment["research_snapshot"],
        "source_executive_dossier_snapshot": alignment["executive_dossier_snapshot"],
        "search_summary": {
            "locale": research["locale"],
            "as_of_date": research["as_of_date"],
            "state": research["state"],
            "vacancy_count": len(cards),
            "maximum_vacancies": research["search_scope"]["maximum_vacancies"],
            "bounded_queries_run": limit["bounded_queries_run"],
            "limit_reason": limit["limit_reason"],
            "limitation": limit["limitation"],
        },
        "vacancies": cards,
        "matrix_rows": matrix_rows,
        "recurrence_rows": recurrence,
        "learning_state": "not_evaluated",
        "learning_decisions": [],
        "methodology_boundaries": list(METHODOLOGY_BOUNDARIES),
        "privacy_boundary": "public_vacancy_metadata_and_identity_free_evidence_references_only",
        "no_external_action": True,
    }


def validate_market_dossier(
    value: object,
    research: object,
    executive_dossier: object,
    alignment: object,
) -> list[str]:
    """Validate exact provenance and derivation against all trusted source artifacts."""
    try:
        value_copy, research_copy, dossier_copy, alignment_copy = copy.deepcopy(
            (value, research, executive_dossier, alignment)
        )
    except (RecursionError, TypeError, ValueError):
        return ["market validation inputs have malformed structure"]
    errors = _validate_market_dossier_structure(value_copy)
    research_is_valid = isinstance(research_copy, Mapping) and not validate_research(
        research_copy
    )
    dossier_is_valid = isinstance(dossier_copy, Mapping) and not validate_dossier(
        dossier_copy
    )
    if not research_is_valid:
        errors.append("research source validation failed")
    if not dossier_is_valid:
        errors.append("dossier source validation failed")
    if not research_is_valid or not dossier_is_valid:
        return _bounded(errors)
    if research_copy.get("locale") != dossier_copy.get("locale"):
        errors.append("research and dossier source locales must match")
        return _bounded(errors)
    binding_errors: list[str] = []
    bindings = _validated_binding_map(
        research_copy, dossier_copy, alignment_copy, binding_errors
    )
    errors.extend(binding_errors)
    if not binding_errors:
        expected = _expected_market_dossier(
            research_copy, alignment_copy, bindings
        )
        if value_copy != expected:
            errors.append("market dossier must exactly match validated source inputs")
    return _bounded(errors)
