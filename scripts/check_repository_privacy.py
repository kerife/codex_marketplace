#!/usr/bin/env python3
"""Scan tracked evaluation evidence without emitting matched private values."""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
import unicodedata
from collections import Counter
from functools import lru_cache
from pathlib import Path
from typing import Callable, Iterator, NamedTuple
from urllib.parse import unquote


TEXT_SUFFIXES = frozenset(
    {".csv", ".html", ".json", ".md", ".tsv", ".txt", ".yaml", ".yml"}
)
STAGED_RELEASE_ARTIFACT_ROOTS = frozenset(
    {Path(".professional-growth-coach-artifacts"), Path(".superpowers")}
)
MAX_STAGED_ARTIFACT_BYTES = 1024 * 1024
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PRIVATE_VACANCY_PACKET_SOURCE_INVENTORY_PATHS = (
    Path("plugins/professional-growth-coach/schemas/candidate-fact-matrix-v1.schema.json"),
    Path("plugins/professional-growth-coach/schemas/private-vacancy-application-packet-v1.schema.json"),
    Path("plugins/professional-growth-coach/scripts/build_candidate_fact_matrix_v1.py"),
    Path("plugins/professional-growth-coach/scripts/validate_candidate_fact_matrix_v1.py"),
    Path("plugins/professional-growth-coach/scripts/build_private_vacancy_application_packet_v1.py"),
    Path("plugins/professional-growth-coach/scripts/validate_private_vacancy_application_packet_v1.py"),
    Path("plugins/professional-growth-coach/scripts/write_private_vacancy_application_packet_v1.py"),
    Path("plugins/professional-growth-coach/scripts/render_private_vacancy_application_packet_v1.py"),
    Path("plugins/professional-growth-coach/scripts/private_vacancy_packet_identity.py"),
    Path("plugins/professional-growth-coach/assets/private-vacancy-application-packet-v1.html"),
    Path("plugins/professional-growth-coach/assets/private-vacancy-application-packet-v1.css"),
    Path("tests/test_candidate_fact_matrix_v1.py"),
    Path("tests/test_private_vacancy_application_packet_v1.py"),
    Path("tests/test_write_private_vacancy_application_packet_v1.py"),
    Path("tests/test_render_private_vacancy_application_packet_v1.py"),
    Path("tests/test_private_vacancy_application_packet_routing.py"),
)
PRIVATE_FIRST_INTERVIEW_BOARD_SOURCE_INVENTORY_PATHS = (
    Path("plugins/professional-growth-coach/schemas/private-first-interview-conversion-board-v1.schema.json"),
    Path("plugins/professional-growth-coach/scripts/private_first_interview_conversion_board_identity.py"),
    Path("plugins/professional-growth-coach/scripts/validate_private_first_interview_conversion_board_v1.py"),
    Path("plugins/professional-growth-coach/scripts/build_private_first_interview_conversion_board_v1.py"),
    Path("plugins/professional-growth-coach/scripts/write_private_first_interview_conversion_board_v1.py"),
    Path("plugins/professional-growth-coach/scripts/render_private_first_interview_conversion_board_v1.py"),
    Path("plugins/professional-growth-coach/assets/private-first-interview-conversion-board-v1.html"),
    Path("plugins/professional-growth-coach/assets/private-first-interview-conversion-board-v1.css"),
    Path("plugins/professional-growth-coach/tests/test_private_first_interview_conversion_board_v1.py"),
    Path("plugins/professional-growth-coach/tests/test_render_private_first_interview_conversion_board_v1.py"),
    Path("plugins/professional-growth-coach/tests/fixtures/private-first-interview-conversion-board-v1/accepted-es.json"),
    Path("plugins/professional-growth-coach/tests/fixtures/private-first-interview-conversion-board-v1/accepted-en.json"),
    Path("plugins/professional-growth-coach/schemas/private-first-interview-source-bundle-v1.schema.json"),
    Path("plugins/professional-growth-coach/schemas/private-first-interview-conversion-board-v2.schema.json"),
    Path("plugins/professional-growth-coach/scripts/private_first_interview_source_bundle.py"),
    Path("plugins/professional-growth-coach/scripts/private_first_interview_conversion_board_v2_identity.py"),
    Path("plugins/professional-growth-coach/scripts/validate_private_first_interview_conversion_board_v2.py"),
    Path("plugins/professional-growth-coach/scripts/build_private_first_interview_conversion_board_v2.py"),
    Path("plugins/professional-growth-coach/scripts/write_private_first_interview_conversion_board_v2.py"),
    Path("plugins/professional-growth-coach/scripts/render_private_first_interview_conversion_board_v2.py"),
    Path("plugins/professional-growth-coach/assets/private-first-interview-conversion-board-v2.html"),
    Path("plugins/professional-growth-coach/assets/private-first-interview-conversion-board-v2.css"),
    Path("plugins/professional-growth-coach/tests/test_private_first_interview_source_bundle.py"),
    Path("plugins/professional-growth-coach/tests/test_private_first_interview_conversion_board_v2.py"),
    Path("plugins/professional-growth-coach/tests/test_write_private_first_interview_conversion_board_v2.py"),
    Path("plugins/professional-growth-coach/tests/test_render_private_first_interview_conversion_board_v2.py"),
    Path("plugins/professional-growth-coach/tests/fixtures/private-first-interview-conversion-board-v2/accepted-es.json"),
    Path("plugins/professional-growth-coach/tests/fixtures/private-first-interview-conversion-board-v2/accepted-en.json"),
)
PRIVATE_FIRST_INTERVIEW_BOARD_V2_ARTIFACT_PATHS = frozenset(
    {
        Path("plugins/professional-growth-coach/schemas/private-first-interview-conversion-board-v2.schema.json"),
        Path("plugins/professional-growth-coach/tests/fixtures/private-first-interview-conversion-board-v2/accepted-es.json"),
        Path("plugins/professional-growth-coach/tests/fixtures/private-first-interview-conversion-board-v2/accepted-en.json"),
    }
)
DOSSIER_SOURCE_INVENTORY_PATHS = (
    Path("plugins/professional-growth-coach/schemas/executive-career-dossier-v1.schema.json"),
    Path("plugins/professional-growth-coach/scripts/validate_executive_career_dossier.py"),
    Path("plugins/professional-growth-coach/scripts/render_executive_career_dossier.py"),
    Path("plugins/professional-growth-coach/assets/executive-career-dossier-v1.html"),
    Path("plugins/professional-growth-coach/assets/executive-career-dossier-v1.css"),
    Path("tests/test_executive_career_dossier.py"),
    Path("plugins/professional-growth-coach/schemas/candidate-gap-response-v1.schema.json"),
    Path("plugins/professional-growth-coach/schemas/candidate-gap-assessment-v1.schema.json"),
    Path("plugins/professional-growth-coach/schemas/career-next-action-eligibility-v1.schema.json"),
    Path("plugins/professional-growth-coach/schemas/career-learning-decision-v3.schema.json"),
    Path("plugins/professional-growth-coach/scripts/semantic_provenance_snapshot.py"),
    Path("plugins/professional-growth-coach/scripts/build_candidate_gap_response_v1.py"),
    Path("plugins/professional-growth-coach/scripts/validate_candidate_gap_response_v1.py"),
    Path("plugins/professional-growth-coach/scripts/build_candidate_gap_assessment_v1.py"),
    Path("plugins/professional-growth-coach/scripts/validate_candidate_gap_assessment_v1.py"),
    Path("plugins/professional-growth-coach/scripts/build_career_next_action_eligibility_v1.py"),
    Path("plugins/professional-growth-coach/scripts/validate_career_next_action_eligibility_v1.py"),
    Path("plugins/professional-growth-coach/scripts/project_career_learning_decision_v3.py"),
    Path("plugins/professional-growth-coach/scripts/build_career_learning_decision_v3.py"),
    Path("plugins/professional-growth-coach/scripts/validate_career_learning_decision_v3.py"),
    Path("plugins/professional-growth-coach/scripts/render_executive_career_dossier_v2.py"),
    Path("plugins/professional-growth-coach/assets/career-learning-eligibility-v1.css"),
    Path("plugins/professional-growth-coach/tests/fixtures/vacancy-first-smoke/sources.json"),
    Path("plugins/professional-growth-coach/skills/professional-growth-coach/SKILL.md"),
    Path("plugins/professional-growth-coach/skills/professional-growth-coach/references/routing.md"),
    Path("plugins/professional-growth-coach/skills/recommend-career-learning/SKILL.md"),
    Path("plugins/professional-growth-coach/skills/recommend-career-learning/references/learning-roi.md"),
    Path("plugins/professional-growth-coach/README.md"),
    Path("docs/release-validation.md"),
    Path("scripts/verify_installed_plugin_release.py"),
    Path("scripts/run_installed_learning_eligibility_v3_smokes.py"),
    Path("plugins/professional-growth-coach/tests/run_static_checks.py"),
    *PRIVATE_VACANCY_PACKET_SOURCE_INVENTORY_PATHS,
    *PRIVATE_FIRST_INTERVIEW_BOARD_SOURCE_INVENTORY_PATHS,
)
INVENTORY_PATHS = (
    Path("docs/superpowers/plans/2026-08-05-job-search-coach-plugin.md"),
    Path("docs/superpowers/plans/2026-08-07-linkedin-client-report-v2.md"),
    Path("tests/evals/final/installed-smoke-test.md"),
    Path("tests/evals/baseline/linkedin.md"),
    Path("tests/evals/with-skill/linkedin.md"),
)
MARKER_PATHS = (
    Path("tests/evals/baseline/linkedin.md"),
    Path("tests/evals/with-skill/linkedin.md"),
    Path("tests/evals/final/installed-smoke-test.md"),
    Path("tests/evals/final/cycle-1.md"),
    Path("tests/evals/final/cycle-2.md"),
)
MARKER_DIRECTORIES = (
    Path("tests/evals/final/cycle-1"),
    Path("tests/evals/final/cycle-2"),
)

RULES = {
    "EMAIL_ADDRESS": re.compile(
        r"(?i)(?<![a-z0-9._%+-])[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}(?![a-z0-9.-])"
    ),
    "PHONE_NUMBER": re.compile(
        r"(?<![a-z0-9])(?:\+\d[\s().-]*(?:\d[\s().-]*){9,}\d|"
        r"(?:\d[\s().-]*){2,}[\s().-]+(?:\d[\s().-]*){6,}\d)(?![a-z0-9])",
        re.I,
    ),
    "LINKEDIN_PROFILE_URL": re.compile(
        r"(?i)(?<![a-z0-9.-])(?:https?://)?(?:[a-z]{2,3}\.)?"
        r"linkedin\.com/(?:in|pub)/[^\s\]\[<>()]+"
    ),
    "LOCAL_USER_PATH": re.compile(
        r"(?i)(?:/Users/[^/\s]+/|/home/[^/\s]+/|[A-Z]:\\Users\\[^\\\s]+\\)"
    ),
    "RAW_PROFILE_MATERIAL": re.compile(
        r"(?i)\b(?:raw[_ -]?profile|profile[_ -]?(?:dump|export|payload|transcript|text)|"
        r"about_text|experience_text|headline_text)\b\s*[:=]"
    ),
    "SECRET_ASSIGNMENT": re.compile(
        r"(?i)\bauthorization\b[\"']?\s*:\s*[\"']?"
        r"(?:Bearer|Basic)\s+[^\s;,\"']{8,}"
    ),
}
HANDLE_PATTERN = re.compile(r"(?i)(?<![a-z0-9._%+-])@[a-z][a-z0-9._-]{2,}(?![a-z0-9._-])")
ANALYTICS_LABEL = (
    r"(?:profile[ _-]?views?|profile[ _-]?view[ _-]?count|search[ _-]?appearances?|"
    r"post[ _-]?impressions?|social[ _-]?selling[ _-]?index|follower[ _-]?count|"
    r"private[ _-]?analytics?|visitas?\s+al\s+perfil|apariciones?\s+en\s+b[uú]squedas?)"
)
ANALYTICS_VALUE_PATTERNS = (
    re.compile(rf"(?is)\b{ANALYTICS_LABEL}\b.{{0,160}}?\b\d[\d,.%]*\b"),
    re.compile(rf"(?is)\b\d[\d,.%]*\b.{{0,160}}?\b{ANALYTICS_LABEL}\b"),
    re.compile(
        rf"(?is)[\"']?\b{ANALYTICS_LABEL}\b[\"']?\s*[:=]\s*[\"']?"
        r"(?!unknown\b|not[_ -]?observed\b|none\b)[^\s;,]{2,}"
    ),
)
MARKDOWN_TRUE_MARKER = re.compile(r"(?m)^no_real_profile_mapping: true$")
ASSIGNMENT_PATTERN = re.compile(
    r"(?im)[\"']?([a-z][a-z0-9 _-]{1,79})[\"']?\s*[:=]\s*"
    r"[\"']?([^\n;,\"'}]{1,160})"
)
SAFE_PLACEHOLDER_VALUES = frozenset({"none", "unknown", "not_observed", "not observed"})
NON_RECORD_SCHEMA_PATH = Path(
    "tests/evals/with-skill/fixtures/linkedin-report-v2/schema.json"
)
DOSSIER_SCHEMA_VERSION = "executive-career-dossier-v1"
DOSSIER_VALIDATOR_PATH = (
    Path(__file__).resolve().parents[1]
    / "plugins/professional-growth-coach/scripts/validate_executive_career_dossier.py"
)
DOSSIER_V2_SCHEMA_VERSION = "executive-career-dossier-v2"
DOSSIER_V2_VALIDATOR_PATH = (
    Path(__file__).resolve().parents[1]
    / "plugins/professional-growth-coach/scripts/validate_executive_career_dossier_v2.py"
)
TARGET_RESEARCH_SCHEMA_VERSION = "target-vacancy-research-v1"
MARKET_DOSSIER_SCHEMA_VERSION = "career-market-learning-dossier-v1"
MARKET_DOSSIER_V2_SCHEMA_VERSION = "career-market-learning-dossier-v2"
MARKET_DOSSIER_V2_PRIVACY_BOUNDARY = (
    "public_vacancy_metadata_and_identity_free_evidence_references_only"
)
MARKET_SCRIPTS_ROOT = (
    REPOSITORY_ROOT / "plugins/professional-growth-coach/scripts"
)
CAREER_NEXT_ACTION_ELIGIBILITY_CONDITIONS = (
    "unavailable",
    "selection_required",
    "insufficient_recurrence",
    "gap_unknown",
    "supported",
    "provider_choice",
    "provider_evidence",
    "experience",
    "proof",
    "practice",
    "terminology",
    "knowledge",
)
CAREER_NEXT_ACTION_ELIGIBILITY_SOURCE_PATHS = frozenset(
    Path(
        "tests/evals/with-skill/fixtures/career-next-action-eligibility-v1/"
        f"{condition}-{locale}/sources.json"
    )
    for condition in CAREER_NEXT_ACTION_ELIGIBILITY_CONDITIONS
    for locale in ("es", "en")
)
CAREER_LEARNING_V3_SOURCE_PATHS = frozenset(
    Path(
        "tests/evals/with-skill/fixtures/career-learning-decision-v3/"
        f"{condition}/sources.json"
    )
    for condition in (
        "knowledge-en",
        "proof-es",
        "selection-required-es",
        "unavailable-es",
    )
)
CAREER_NEXT_ACTION_ELIGIBILITY_SOURCE_FIELDS = frozenset(
    {
        "research",
        "executive_dossier",
        "market_dossier",
        "gap_response",
        "gap_assessment",
        "provider_research",
    }
)
CAREER_LEARNING_V3_SOURCE_FIELDS = (
    CAREER_NEXT_ACTION_ELIGIBILITY_SOURCE_FIELDS | {"eligibility"}
)
PRIVATE_VACANCY_PACKET_SCENARIOS = (
    "ready-es",
    "ready-en",
    "revise-missing-es",
    "revise-review-en",
    "stop-constraint-es",
    "stop-constraint-en",
)
PRIVATE_VACANCY_PACKET_SOURCE_PATHS = frozenset(
    Path(
        "tests/evals/with-skill/fixtures/private-vacancy-application-packet-v1/"
        f"{scenario}/sources.json"
    )
    for scenario in PRIVATE_VACANCY_PACKET_SCENARIOS
)
PRIVATE_VACANCY_PACKET_FIXTURE_PATHS = frozenset(
    path.with_name(name)
    for path in PRIVATE_VACANCY_PACKET_SOURCE_PATHS
    for name in (
        "sources.json",
        "candidate-fact-matrix.json",
        "application-packet.json",
    )
)
PRIVATE_VACANCY_PACKET_SOURCE_SHA256 = {
    Path(
        "tests/evals/with-skill/fixtures/private-vacancy-application-packet-v1/"
        "ready-es/sources.json"
    ): "cd3993dcd94c910c300280063da8ed7846bfd3d6abf77365c2c2d03c74a143ee",
    Path(
        "tests/evals/with-skill/fixtures/private-vacancy-application-packet-v1/"
        "ready-en/sources.json"
    ): "f89598f5349a029eac02097c91c016c06d123203ba41b4e04f96c1d6c14900e1",
    Path(
        "tests/evals/with-skill/fixtures/private-vacancy-application-packet-v1/"
        "revise-missing-es/sources.json"
    ): "f8298e5fca2619d7cee1fb9950021d70f55b4a02497486105370498c553f8433",
    Path(
        "tests/evals/with-skill/fixtures/private-vacancy-application-packet-v1/"
        "revise-review-en/sources.json"
    ): "95047ea58b3c3084699c4a304ce98ebc40ae8203b04bf76039d09ee69ae44220",
    Path(
        "tests/evals/with-skill/fixtures/private-vacancy-application-packet-v1/"
        "stop-constraint-es/sources.json"
    ): "33eb5814815250de9b1403f88efad9fdc9f057ba2f4ed398f105b30bef71751b",
    Path(
        "tests/evals/with-skill/fixtures/private-vacancy-application-packet-v1/"
        "stop-constraint-en/sources.json"
    ): "ea0c4bbaa15ee2aaf749501cbb4f669e9dadd3fe05cf9b08b69a48a262a6cc96",
}
PRIVATE_VACANCY_PACKET_SOURCE_FIELDS = frozenset(
    {"eligibility_group", "candidate_fact_group"}
)
PRIVATE_VACANCY_PACKET_ELIGIBILITY_FIELDS = frozenset(
    CAREER_NEXT_ACTION_ELIGIBILITY_SOURCE_FIELDS | {"eligibility"}
)
PRIVATE_VACANCY_PACKET_FACT_FIELDS = frozenset(
    {"candidate_fact_matrix", "source_group"}
)
MARKET_DOSSIER_V2_SYNTHETIC_SOURCES = {
    Path(
        "tests/evals/with-skill/fixtures/"
        "career-market-learning-dossier-v2/complete-five-es.json"
    ): (
        Path("target-vacancy-research/complete-five-es.json"),
        Path("executive-career-dossier-v2/scenario-a-es.json"),
    ),
    Path(
        "tests/evals/with-skill/fixtures/"
        "career-market-learning-dossier-v2/limited-four-en.json"
    ): (
        Path("target-vacancy-research/limited-four-en.json"),
        Path("executive-career-dossier-v2/scenario-c-market-en.json"),
    ),
}
CANDIDATE_IDENTITY_POLICY_PATH = MARKET_SCRIPTS_ROOT / "private_prose_safety.py"
RECRUITER_PRACTICE_SCHEMA_VERSION = "recruiter-practice-session-v1"
RECRUITER_PRACTICE_VALIDATOR_PATH = (
    Path(__file__).resolve().parents[1]
    / "plugins/professional-growth-coach/scripts/validate_recruiter_practice_session.py"
)
PUBLIC_MARKET_ROW_SCHEMAS = frozenset(
    {
        frozenset(
            {
                "market_public_source_row",
                "source_id",
                "source_url",
                "role_family",
                "geography_bucket",
                "observation_date",
                "compensation_bucket",
                "no_real_profile_mapping",
            }
        ),
        frozenset(
            {
                "geography",
                "currency",
                "seniority",
                "source_date",
                "sample_context",
                "range",
                "demand_signals",
                "recurring_requirements",
                "confidence",
                "warning",
            }
        ),
        frozenset(
            {
                "geography",
                "currency",
                "seniority",
                "source_date",
                "source_state",
                "compensation_observation",
                "sample_context",
                "range",
                "demand_signals",
                "recurring_requirements",
                "confidence",
                "warning",
            }
        ),
        frozenset(
            {
                "geography",
                "currency",
                "seniority",
                "as_of_date",
                "source_date",
                "source_age_days",
                "freshness_window_days",
                "freshness_status",
                "source_state",
                "compensation_observation",
                "compensation_components",
                "component_gaps",
                "employer_or_publisher",
                "source_id",
                "independent_observation_id",
                "comparable_group_id",
                "comparability_status",
                "comparability_check",
                "range_method",
                "conversion_basis",
                "sample_context",
                "range",
                "demand_signals",
                "recurring_requirements",
                "confidence",
                "warning",
            }
        ),
    }
)


def _decode_json_escape_sequences(value: str) -> str:
    def replace_unicode(match: re.Match[str]) -> str:
        return chr(int(match.group(1), 16))

    value = re.sub(r"\\u([0-9a-fA-F]{4})", replace_unicode, value)
    return value.replace(r"\/", "/").replace(r"\\", "\\")


def normalize_and_decode(value: str) -> str:
    current = value
    for _ in range(3):
        normalized = unicodedata.normalize("NFKC", current)
        normalized = "".join(
            character
            for character in normalized
            if unicodedata.category(character) != "Cf"
        )
        decoded = _decode_json_escape_sequences(unquote(normalized))
        if decoded == current:
            return decoded
        current = decoded
    return current


def _json_scalars(value: object) -> Iterator[str]:
    if isinstance(value, dict):
        for key, nested in value.items():
            yield str(key)
            yield from _json_scalars(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _json_scalars(nested)
    elif isinstance(value, (str, int, float, bool)) or value is None:
        yield str(value)


def _json_scalar_values(value: object) -> Iterator[str]:
    if isinstance(value, dict):
        for nested in value.values():
            yield from _json_scalar_values(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _json_scalar_values(nested)
    elif isinstance(value, (str, int, float, bool)) or value is None:
        yield str(value)


def _bounded_scalar_scan_values(value: object) -> list[str]:
    return [
        f"{scalar}|validated_scalar_boundary"
        for scalar in _json_scalar_values(value)
    ]


def _json_leaf_assignments(value: object) -> Iterator[str]:
    if isinstance(value, dict):
        for key, nested in value.items():
            if isinstance(nested, (dict, list)):
                yield from _json_leaf_assignments(nested)
            else:
                yield json.dumps(str(key), ensure_ascii=False) + ": " + json.dumps(
                    nested,
                    ensure_ascii=False,
                )
    elif isinstance(value, list):
        for nested in value:
            if isinstance(nested, (dict, list)):
                yield from _json_leaf_assignments(nested)
            else:
                yield json.dumps(nested, ensure_ascii=False)


class _DuplicateJsonKeyError(ValueError):
    pass


class StagedArtifactReadError(ValueError):
    pass


class StagedArtifact(NamedTuple):
    path: Path
    mode: str
    stage: int
    object_id: str


def _unique_json_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateJsonKeyError("duplicate JSON key")
        result[key] = value
    return result


def _json_depth_is_bounded(value: object, maximum: int, depth: int = 0) -> bool:
    if depth > maximum:
        return False
    if isinstance(value, dict):
        return all(
            _json_depth_is_bounded(nested, maximum, depth + 1)
            for nested in value.values()
        )
    if isinstance(value, list):
        return all(
            _json_depth_is_bounded(nested, maximum, depth + 1)
            for nested in value
        )
    return True


@lru_cache(maxsize=1)
def _load_dossier_validator() -> Callable[[object], list[str]] | None:
    specification = importlib.util.spec_from_file_location(
        "job_search_coach_executive_career_dossier_privacy",
        DOSSIER_VALIDATOR_PATH,
    )
    if specification is None or specification.loader is None:
        return None
    module = importlib.util.module_from_spec(specification)
    try:
        specification.loader.exec_module(module)
    except Exception:
        return None
    validate = getattr(module, "validate_dossier", None)
    return validate if callable(validate) else None


def _safe_dossier_scan_value(text: str, value: object) -> dict[str, object] | None:
    if not isinstance(value, dict) or value.get("schema_version") != DOSSIER_SCHEMA_VERSION:
        return None
    analytics = value.get("analytics")
    privacy = value.get("privacy")
    if (
        not isinstance(analytics, dict)
        or analytics.get("state") != "not_requested"
        or not isinstance(privacy, dict)
        or privacy.get("raw_private_analytics_included") is not False
        or privacy.get("aggregate_analytics_included") is not False
        or len(text.encode("utf-8")) > 256 * 1024
        or not _json_depth_is_bounded(value, 12)
    ):
        return None
    try:
        validate = _load_dossier_validator()
        if validate is None:
            return None
        errors = validate(value)
    except Exception:
        return None
    if type(errors) is not list or any(type(error) is not str for error in errors) or errors:
        return None
    scan_value = copy.deepcopy(value)
    del scan_value["analytics"]["state"]
    del scan_value["privacy"]["raw_private_analytics_included"]
    del scan_value["privacy"]["aggregate_analytics_included"]
    return scan_value


@lru_cache(maxsize=1)
def _load_dossier_v2_contract() -> (
    tuple[Callable[[object], list[str]], Callable[[dict[str, object]], dict[str, object]]]
    | None
):
    """Load only the closed v2 validator/projector pair for privacy projection."""
    specification = importlib.util.spec_from_file_location(
        "canonical_executive_career_dossier_v2_privacy", DOSSIER_V2_VALIDATOR_PATH
    )
    if specification is None or specification.loader is None:
        return None
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    try:
        specification.loader.exec_module(module)
    except Exception:
        return None
    validate = getattr(module, "validate_dossier", None)
    project = getattr(module, "project_v2_to_v1", None)
    if not callable(validate) or not callable(project):
        return None
    return validate, project


def _safe_dossier_v2_scan_value(text: str, value: object) -> dict[str, object] | None:
    """Project only an unchanged, fully valid v2 value to the v1 scan contract."""
    if (
        not isinstance(value, dict)
        or value.get("schema_version") != DOSSIER_V2_SCHEMA_VERSION
        or len(text.encode("utf-8")) > 256 * 1024
        or not _json_depth_is_bounded(value, 12)
    ):
        return None
    before = copy.deepcopy(value)
    try:
        contract = _load_dossier_v2_contract()
        if contract is None:
            return None
        validate, project = contract
        errors = validate(value)
        if (
            type(errors) is not list
            or any(type(error) is not str for error in errors)
            or errors
        ):
            return None
        projected = project(value)
    except Exception:
        return None
    if value != before or not isinstance(projected, dict):
        return None
    return _safe_dossier_scan_value(text, projected)


@lru_cache(maxsize=1)
def _load_market_privacy_contract() -> dict[str, object] | None:
    previous_path = list(sys.path)
    sys.path.insert(0, str(MARKET_SCRIPTS_ROOT))
    modules: dict[str, object] = {}
    try:
        for name in (
            "validate_target_vacancy_research",
            "build_career_market_learning_dossier",
            "validate_career_market_learning_dossier",
            "build_career_market_learning_dossier_v2",
            "validate_career_market_learning_dossier_v2",
        ):
            path = MARKET_SCRIPTS_ROOT / f"{name}.py"
            specification = importlib.util.spec_from_file_location(
                f"job_search_coach_market_privacy_{name}", path
            )
            if specification is None or specification.loader is None:
                return None
            module = importlib.util.module_from_spec(specification)
            specification.loader.exec_module(module)
            modules[name] = module
    except Exception:
        return None
    finally:
        sys.path[:] = previous_path
    return modules


@lru_cache(maxsize=1)
def _load_candidate_identity_policy() -> Callable[[object], bool] | None:
    specification = importlib.util.spec_from_file_location(
        "job_search_coach_candidate_identity_privacy",
        CANDIDATE_IDENTITY_POLICY_PATH,
    )
    if specification is None or specification.loader is None:
        return None
    module = importlib.util.module_from_spec(specification)
    try:
        specification.loader.exec_module(module)
    except Exception:
        return None
    detector = getattr(module, "target_research_contains_candidate_identity", None)
    return detector if callable(detector) else None


def _safe_target_research_scan_value(
    text: str, value: object
) -> dict[str, object] | None:
    if (
        not isinstance(value, dict)
        or value.get("schema_version") != TARGET_RESEARCH_SCHEMA_VERSION
        or len(text.encode("utf-8")) > 256 * 1024
        or not _json_depth_is_bounded(value, 12)
    ):
        return None
    before = copy.deepcopy(value)
    contract = _load_market_privacy_contract()
    if contract is None:
        return None
    try:
        errors = contract["validate_target_vacancy_research"].validate_research(value)
    except Exception:
        return None
    if value != before or type(errors) is not list or errors:
        return None
    return {"validated_public_market_values": list(_json_scalars(value))}


def _market_fixture_alignment(
    research: dict[str, object], dossier: dict[str, object], contract: dict[str, object]
) -> dict[str, object]:
    fixture_states = {
        "python": ("verified_match", ["E-001"]),
        "kubernetes": ("candidate_reported_match", ["E-003"]),
        "terraform": ("adjacent_evidence", ["E-004"]),
        "observability": ("unknown", []),
        "linux": ("explicit_gap", ["E-003"]),
    }
    research_validator = contract["validate_target_vacancy_research"]
    builder = contract["build_career_market_learning_dossier"]
    signals = sorted(
        {
            requirement["signal"]
            for vacancy in research["vacancies"]
            for requirement in vacancy["requirements"]
        }
    )
    return {
        "schema_version": "candidate-market-alignment-v1",
        "research_snapshot": research_validator.snapshot_for_market_dossier(research),
        "executive_dossier_snapshot": builder.snapshot_for_dossier(dossier),
        "signal_bindings": [
            {
                "signal": signal,
                "support_state": fixture_states[signal][0],
                "evidence_ids": fixture_states[signal][1],
            }
            for signal in signals
        ],
        "privacy_boundary": "identity_free_evidence_references_only",
    }


def _safe_market_dossier_scan_value(
    path: Path, text: str, value: object
) -> dict[str, object] | None:
    expected_parent = Path(
        "tests/evals/with-skill/fixtures/career-market-learning-dossier"
    )
    if (
        path.parent != expected_parent
        or not isinstance(value, dict)
        or value.get("schema_version") != MARKET_DOSSIER_SCHEMA_VERSION
        or len(text.encode("utf-8")) > 256 * 1024
        or not _json_depth_is_bounded(value, 12)
    ):
        return None
    dossier_names = {
        "complete-five-es.json": "scenario-a-es.json",
        "limited-four-en.json": "scenario-c-en.json",
        "unavailable-es.json": "scenario-a-es.json",
    }
    dossier_name = dossier_names.get(path.name)
    contract = _load_market_privacy_contract()
    if dossier_name is None or contract is None:
        return None
    fixture_root = Path(__file__).resolve().parents[1] / "tests/evals/with-skill/fixtures"
    try:
        research = json.loads(
            (fixture_root / "target-vacancy-research" / path.name).read_text(
                encoding="utf-8"
            ),
            object_pairs_hook=_unique_json_object,
        )
        dossier = json.loads(
            (fixture_root / "executive-career-dossier-v2" / dossier_name).read_text(
                encoding="utf-8"
            ),
            object_pairs_hook=_unique_json_object,
        )
        alignment = _market_fixture_alignment(research, dossier, contract)
        builder = contract["build_career_market_learning_dossier"]
        validator = contract["validate_career_market_learning_dossier"]
        expected = builder.build_market_dossier(research, dossier, alignment)
        errors = validator.validate_market_dossier(value, research, dossier, alignment)
    except Exception:
        return None
    if value != expected or type(errors) is not list or errors:
        return None
    return {
        "schema_version": value["schema_version"],
        "state": value["state"],
        "privacy_boundary": value["privacy_boundary"],
        "no_external_action": value["no_external_action"],
    }


def _has_known_synthetic_market_provenance(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    employers = value.get("employers")
    vacancies = value.get("vacancies")
    if (
        not isinstance(employers, list)
        or not employers
        or not isinstance(vacancies, list)
        or not vacancies
    ):
        return False
    if any(
        not isinstance(employer, dict)
        or not isinstance(employer.get("display_name"), str)
        or not employer["display_name"].startswith("Fixture Employer ")
        or employer.get("qualification_observation") != "Synthetic test qualification."
        or employer.get("official_source_title") != "Synthetic careers index"
        or not isinstance(employer.get("official_source_url"), str)
        or not employer["official_source_url"].startswith(
            "https://www.rfc-editor.org/rfc/rfc"
        )
        for employer in employers
    ):
        return False
    for vacancy in vacancies:
        if (
            not isinstance(vacancy, dict)
            or not isinstance(vacancy.get("title"), str)
            or not vacancy["title"].startswith("Fixture ")
            or not isinstance(vacancy.get("source_url"), str)
            or not vacancy["source_url"].startswith(
                "https://www.rfc-editor.org/rfc/rfc"
            )
            or not isinstance(vacancy.get("requirements"), list)
            or not vacancy["requirements"]
        ):
            return False
        if any(
            not isinstance(requirement, dict)
            or requirement.get("source_paraphrase") != "Synthetic test requirement."
            for requirement in vacancy["requirements"]
        ):
            return False
    return True


@lru_cache(maxsize=1)
def _load_career_next_action_eligibility_builder() -> object | None:
    path = MARKET_SCRIPTS_ROOT / "build_career_next_action_eligibility_v1.py"
    specification = importlib.util.spec_from_file_location(
        "job_search_coach_eligibility_privacy", path
    )
    if specification is None or specification.loader is None:
        return None
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    previous_path = list(sys.path)
    sys.path.insert(0, str(MARKET_SCRIPTS_ROOT))
    try:
        specification.loader.exec_module(module)
    except Exception:
        return None
    finally:
        sys.path[:] = previous_path
    project = getattr(module, "_project_eligibility_from_frozen", None)
    return project if callable(project) else None


@lru_cache(maxsize=1)
def _load_career_learning_v3_builder() -> object | None:
    path = MARKET_SCRIPTS_ROOT / "build_career_learning_decision_v3.py"
    specification = importlib.util.spec_from_file_location(
        "job_search_coach_learning_v3_privacy", path
    )
    if specification is None or specification.loader is None:
        return None
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    previous_path = list(sys.path)
    sys.path.insert(0, str(MARKET_SCRIPTS_ROOT))
    try:
        specification.loader.exec_module(module)
    except Exception:
        return None
    finally:
        sys.path[:] = previous_path
    project = getattr(module, "_project_learning_v3_from_frozen", None)
    return project if callable(project) else None


def _has_known_synthetic_eligibility_provenance(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    research = value.get("research")
    if _has_known_synthetic_market_provenance(research):
        return True
    if not isinstance(research, dict):
        return False
    search_limit = research.get("search_limit")
    return (
        research.get("state") == "market_evidence_unavailable"
        and research.get("employers") == []
        and research.get("vacancies") == []
        and isinstance(search_limit, dict)
        and search_limit.get("limitation") == "Synthetic test unavailability."
    )


def _has_known_synthetic_private_packet_provenance(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    research = value.get("research")
    if not isinstance(research, dict):
        return False
    normalized = copy.deepcopy(research)
    vacancies = normalized.get("vacancies")
    if not isinstance(vacancies, list):
        return False
    for vacancy in vacancies:
        if not isinstance(vacancy, dict):
            return False
        requirements = vacancy.get("requirements")
        if not isinstance(requirements, list):
            return False
        for requirement in requirements:
            if not isinstance(requirement, dict):
                return False
            paraphrase = requirement.get("source_paraphrase")
            if paraphrase not in {
                "Synthetic test requirement.",
                "Synthetic public requirement.",
            }:
                return False
            requirement["source_paraphrase"] = "Synthetic test requirement."
    return _has_known_synthetic_market_provenance(normalized)


def _safe_career_next_action_eligibility_sources_scan_value(
    path: Path, text: str, value: object
) -> dict[str, object] | None:
    learning_v3_source = path in CAREER_LEARNING_V3_SOURCE_PATHS
    expected_fields = (
        CAREER_LEARNING_V3_SOURCE_FIELDS
        if learning_v3_source
        else CAREER_NEXT_ACTION_ELIGIBILITY_SOURCE_FIELDS
    )
    if (
        path not in CAREER_NEXT_ACTION_ELIGIBILITY_SOURCE_PATHS
        and not learning_v3_source
    ) or (
        not isinstance(value, dict)
        or set(value) != expected_fields
        or len(text.encode("utf-8")) > 256 * 1024
        or not _json_depth_is_bounded(value, 12)
        or not _has_known_synthetic_eligibility_provenance(value)
    ):
        return None
    before = copy.deepcopy(value)
    project = _load_career_next_action_eligibility_builder()
    if project is None:
        return None
    try:
        eligibility_sources = {
            field: value[field]
            for field in CAREER_NEXT_ACTION_ELIGIBILITY_SOURCE_FIELDS
        }
        projected = project(eligibility_sources)
        if learning_v3_source:
            expected = value["eligibility"]
            learning_project = _load_career_learning_v3_builder()
            if learning_project is None:
                return None
            projected_learning = learning_project(value)
            expected_learning_path = (
                Path(__file__).resolve().parents[1] / path.with_name("learning.json")
            )
            expected_learning_text = expected_learning_path.read_text(
                encoding="utf-8"
            )
            expected_learning = json.loads(
                expected_learning_text,
                object_pairs_hook=_unique_json_object,
            )
        else:
            expected_path = Path(__file__).resolve().parents[1] / path.with_name(
                "eligibility.json"
            )
            expected_text = expected_path.read_text(encoding="utf-8")
            expected = json.loads(
                expected_text,
                object_pairs_hook=_unique_json_object,
            )
            projected_learning = None
            expected_learning = None
            expected_learning_text = ""
    except Exception:
        return None
    if (
        value != before
        or not isinstance(projected, dict)
        or projected != expected
        or len(json.dumps(expected, ensure_ascii=False).encode("utf-8")) > 64 * 1024
        or not _json_depth_is_bounded(expected, 8)
        or (
            learning_v3_source
            and (
                not isinstance(projected_learning, dict)
                or projected_learning != expected_learning
                or len(expected_learning_text.encode("utf-8")) > 64 * 1024
                or not _json_depth_is_bounded(expected_learning, 8)
            )
        )
    ):
        return None
    research = value["research"]
    dossier = value["executive_dossier"]
    research_scan = _safe_target_research_scan_value(
        json.dumps(research, ensure_ascii=False), research
    )
    dossier_scan = _safe_dossier_v2_scan_value(
        json.dumps(dossier, ensure_ascii=False), dossier
    )
    if research_scan is None or dossier_scan is None:
        return None
    return {
        "validated_research": research_scan,
        "validated_executive_dossier": dossier_scan,
        "validated_market_values": _bounded_scalar_scan_values(
            value["market_dossier"]
        ),
        "validated_provider_values": _bounded_scalar_scan_values(
            value["provider_research"]
        ),
        "validated_gap_response_values": _bounded_scalar_scan_values(
            value["gap_response"]
        ),
        "validated_gap_assessment_values": _bounded_scalar_scan_values(
            value["gap_assessment"]
        ),
        "eligibility": projected,
    }


@lru_cache(maxsize=1)
def _load_private_vacancy_packet_privacy_contract() -> dict[str, object] | None:
    previous_path = list(sys.path)
    sys.path.insert(0, str(MARKET_SCRIPTS_ROOT))
    modules: dict[str, object] = {}
    try:
        for name in (
            "private_input_loader",
            "build_candidate_fact_matrix_v1",
            "build_private_vacancy_application_packet_v1",
        ):
            path = MARKET_SCRIPTS_ROOT / f"{name}.py"
            specification = importlib.util.spec_from_file_location(
                f"job_search_coach_private_packet_privacy_{name}", path
            )
            if specification is None or specification.loader is None:
                return None
            module = importlib.util.module_from_spec(specification)
            sys.modules[specification.name] = module
            specification.loader.exec_module(module)
            modules[name] = module
    except Exception:
        return None
    finally:
        sys.path[:] = previous_path
    reader = getattr(modules["private_input_loader"], "read_bounded_bytes", None)
    fact_builder = getattr(
        modules["build_candidate_fact_matrix_v1"],
        "build_candidate_fact_matrix_v1",
        None,
    )
    packet_builder = getattr(
        modules["build_private_vacancy_application_packet_v1"],
        "build_private_vacancy_application_packet_v1",
        None,
    )
    if not all(callable(value) for value in (reader, fact_builder, packet_builder)):
        return None
    return {
        "read_bounded_bytes": reader,
        "build_candidate_fact_matrix_v1": fact_builder,
        "build_private_vacancy_application_packet_v1": packet_builder,
    }


def _read_bounded_regular_text(path: Path, maximum: int) -> str | None:
    contract = _load_private_vacancy_packet_privacy_contract()
    if contract is None:
        return None
    try:
        raw = contract["read_bounded_bytes"](path, maximum)
        if type(raw) is not bytes:
            return None
        return raw.decode("utf-8")
    except Exception:
        return None


def _read_bounded_regular_json(path: Path, maximum: int) -> dict[str, object] | None:
    text = _read_bounded_regular_text(path, maximum)
    if text is None:
        return None
    try:
        value = json.loads(text, object_pairs_hook=_unique_json_object)
    except (UnicodeError, json.JSONDecodeError, ValueError):
        return None
    return value if isinstance(value, dict) else None


def _read_private_packet_fixture_json(
    path: Path, maximum: int
) -> dict[str, object] | None:
    return _read_bounded_regular_json(REPOSITORY_ROOT / path, maximum)


def _safe_private_vacancy_packet_sources_scan_value(
    path: Path, text: str, value: object
) -> list[dict[str, object]] | None:
    expected_digest = PRIVATE_VACANCY_PACKET_SOURCE_SHA256.get(path)
    if (
        expected_digest is None
        or hashlib.sha256(text.encode("utf-8")).hexdigest() != expected_digest
        or not isinstance(value, dict)
        or set(value) != PRIVATE_VACANCY_PACKET_SOURCE_FIELDS
        or len(text.encode("utf-8")) > 64 * 1024
        or not _json_depth_is_bounded(value, 12)
    ):
        return None
    eligibility_group = value.get("eligibility_group")
    fact_group = value.get("candidate_fact_group")
    if (
        not isinstance(eligibility_group, dict)
        or set(eligibility_group) != PRIVATE_VACANCY_PACKET_ELIGIBILITY_FIELDS
        or not isinstance(fact_group, dict)
        or set(fact_group) != PRIVATE_VACANCY_PACKET_FACT_FIELDS
        or not _has_known_synthetic_private_packet_provenance(eligibility_group)
    ):
        return None
    before = copy.deepcopy(value)
    contract = _load_private_vacancy_packet_privacy_contract()
    if contract is None:
        return None
    try:
        rebuilt_matrix = contract["build_candidate_fact_matrix_v1"](
            fact_group["source_group"]
        )
        rebuilt_packet = contract["build_private_vacancy_application_packet_v1"](
            value
        )
    except Exception:
        return None
    sibling_matrix = _read_private_packet_fixture_json(
        path.with_name("candidate-fact-matrix.json"), 64 * 1024
    )
    sibling_packet = _read_private_packet_fixture_json(
        path.with_name("application-packet.json"), 64 * 1024
    )
    if (
        value != before
        or rebuilt_matrix != fact_group.get("candidate_fact_matrix")
        or rebuilt_matrix != sibling_matrix
        or rebuilt_packet != sibling_packet
        or not isinstance(rebuilt_matrix, dict)
        or not isinstance(rebuilt_packet, dict)
        or not _json_depth_is_bounded(rebuilt_matrix, 8)
        or not _json_depth_is_bounded(rebuilt_packet, 10)
    ):
        return None
    research = eligibility_group.get("research")
    research_projection = _safe_target_research_scan_value(
        json.dumps(research, ensure_ascii=False), research
    )
    if research_projection is None:
        return None
    return [
        {"validated_candidate_fact_matrix": copy.deepcopy(rebuilt_matrix)},
        {"validated_public_target_research": research_projection},
        {"generated_private_packet": copy.deepcopy(rebuilt_packet)},
    ]


def _is_exact_synthetic_market_v2_fixture(
    path: Path, text: str, value: object
) -> bool:
    source_paths = MARKET_DOSSIER_V2_SYNTHETIC_SOURCES.get(path)
    if (
        source_paths is None
        or not isinstance(value, dict)
        or value.get("schema_version") != MARKET_DOSSIER_V2_SCHEMA_VERSION
        or value.get("privacy_boundary") != MARKET_DOSSIER_V2_PRIVACY_BOUNDARY
        or len(text.encode("utf-8")) > 256 * 1024
        or not _json_depth_is_bounded(value, 12)
    ):
        return False
    contract = _load_market_privacy_contract()
    if contract is None:
        return False
    fixture_root = Path(__file__).resolve().parents[1] / "tests/evals/with-skill/fixtures"
    before = copy.deepcopy(value)
    try:
        research = json.loads(
            (fixture_root / source_paths[0]).read_text(encoding="utf-8"),
            object_pairs_hook=_unique_json_object,
        )
        dossier = json.loads(
            (fixture_root / source_paths[1]).read_text(encoding="utf-8"),
            object_pairs_hook=_unique_json_object,
        )
        if not _has_known_synthetic_market_provenance(research):
            return False
        builder = contract["build_career_market_learning_dossier_v2"]
        validator = contract["validate_career_market_learning_dossier_v2"]
        expected = builder.build_market_dossier_v2(research, dossier)
        errors = validator.validate_market_dossier_v2(value, research, dossier)
    except Exception:
        return False
    return (
        value == before
        and value == expected
        and type(errors) is list
        and not errors
    )


@lru_cache(maxsize=1)
def _load_recruiter_practice_validator() -> Callable[[object], list[str]] | None:
    specification = importlib.util.spec_from_file_location(
        "job_search_coach_recruiter_practice_privacy",
        RECRUITER_PRACTICE_VALIDATOR_PATH,
    )
    if specification is None or specification.loader is None:
        return None
    module = importlib.util.module_from_spec(specification)
    previous_path = list(sys.path)
    sys.path.insert(0, str(RECRUITER_PRACTICE_VALIDATOR_PATH.parent))
    try:
        specification.loader.exec_module(module)
    except Exception:
        return None
    finally:
        sys.path[:] = previous_path
    validate = getattr(module, "validate_session", None)
    return validate if callable(validate) else None


def _safe_recruiter_practice_scan_value(
    text: str, value: object
) -> dict[str, object] | None:
    """Elide two validated schema markers, never session prose or other fields.

    The closed schema requires a false no-action guard and a fixed session-kind
    marker. They are classification metadata, not secrets. Any invalid session,
    changed marker, additional field, or prose continues through normal scans.
    """

    if (
        not isinstance(value, dict)
        or value.get("schema_version") != RECRUITER_PRACTICE_SCHEMA_VERSION
        or len(text.encode("utf-8")) > 64_000
        or not _json_depth_is_bounded(value, 12)
    ):
        return None
    delivery = value.get("delivery")
    if (
        not isinstance(delivery, dict)
        or delivery.get("external_actions_authorized") is not False
    ):
        return None
    try:
        validate = _load_recruiter_practice_validator()
        if validate is None:
            return None
        errors = validate(value)
    except Exception:
        return None
    if type(errors) is not list or any(type(error) is not str for error in errors) or errors:
        return None
    scan_value = copy.deepcopy(value)
    del scan_value["delivery"]["external_actions_authorized"]
    del scan_value["session_kind"]
    return scan_value


def _normalize_key(key: object) -> tuple[str, ...]:
    text = normalize_and_decode(str(key))
    text = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", text)
    return tuple(token for token in re.split(r"[^a-z0-9]+", text.casefold()) if token)


def _key_is_secret(tokens: tuple[str, ...]) -> bool:
    token_set = set(tokens)
    return bool(
        token_set & {"secret", "password", "passwd", "session", "cookie"}
        or ("token" in token_set and token_set & {"access", "refresh", "auth", "api", "bearer", "client"})
        or ("credential" in token_set and token_set & {"access", "auth", "api", "client", "login"})
        or ("key" in token_set and token_set & {"api", "private", "client", "access"})
    )


def _key_is_free_name(tokens: tuple[str, ...]) -> bool:
    token_set = set(tokens)
    return (
        "name" in token_set
        and bool(
            token_set
            & {
                "full", "display", "person", "candidate", "profile", "recruiter", "contact",
                "given", "family", "first", "last", "legal", "preferred", "middle",
            }
        )
    ) or bool(token_set & {"surname", "forename"}) or {"recruiter", "target"} <= token_set


def _key_is_private_analytics(tokens: tuple[str, ...]) -> bool:
    token_set = set(tokens)
    return bool(
        "analytics" in token_set
        or ({"profile"} <= token_set and bool(token_set & {"view", "views", "visit", "visits"}))
        or ({"search"} <= token_set and bool(token_set & {"appearance", "appearances", "result", "results"}))
        or ({"post", "impression"} <= token_set)
        or ({"post", "impressions"} <= token_set)
        or ({"follower"} <= token_set and bool(token_set & {"count", "total"}))
    )


def _key_dimension_families(key: object) -> set[str]:
    tokens = _normalize_key(key)
    token_set = set(tokens)
    families: set[str] = set()
    if (
        _key_is_free_name(tokens)
        or "handle" in token_set
        or bool(token_set & {"candidate", "subject", "person", "profile"} and token_set & {"id", "identifier", "reference", "ref"})
    ):
        families.add("identity")
    if token_set & {"employer", "employing", "company", "organization", "organisation", "org"}:
        families.add("employer")
    if token_set & {"title", "role", "position", "seniority"}:
        families.add("title")
    if token_set & {"location", "geography", "geographic", "region"}:
        families.add("location")
    if token_set & {"date", "time", "timestamp"} or tokens[-1:] == ("at",):
        families.add("date")
    if token_set & {"metric", "count", "scale", "scope", "range", "compensation"}:
        families.add("metric")
    return families


def _mapping_dimension_families(mapping: dict[str, object]) -> set[str]:
    families: set[str] = set()
    for key, nested in mapping.items():
        families.update(_key_dimension_families(key))
        if isinstance(nested, dict):
            families.update(_mapping_dimension_families(nested))
    return families


def _mapping_is_singling_out(mapping: dict[str, object]) -> bool:
    families = _mapping_dimension_families(mapping)
    non_identity_count = len(families - {"identity"})
    return non_identity_count >= 4 or ("identity" in families and non_identity_count >= 3)


def _walk_mappings(value: object) -> Iterator[dict[str, object]]:
    if isinstance(value, dict):
        yield value
        for nested in value.values():
            yield from _walk_mappings(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _walk_mappings(nested)


def _parse_semicolon_row(line: str) -> dict[str, str] | None:
    mapping: dict[str, str] = {}
    for part in line.strip().lstrip("- ").split("; "):
        if "=" not in part:
            return None
        key, value = part.split("=", 1)
        key = key.strip()
        if not re.fullmatch(r"[a-z_][a-z0-9_]*", key):
            return None
        if key in mapping:
            return None
        mapping[key] = value.strip().rstrip(".")
    return mapping or None


def _structured_text_singling_out(path: Path, text: str) -> int:
    count = 0
    for line in text.splitlines():
        mapping = _parse_semicolon_row(line)
        if mapping is None:
            continue
        keys = frozenset(mapping)
        if path == Path("tests/evals/with-skill/market.md") and keys in PUBLIC_MARKET_ROW_SCHEMAS:
            continue
        if _mapping_is_singling_out(mapping):
            count += 1
    return count


def has_true_non_mapping_marker(path: Path, text: str) -> bool:
    if path.suffix.lower() == ".json":
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            return False
        return isinstance(payload, dict) and payload.get("no_real_profile_mapping") is True
    marker_lines = [
        line
        for line in text.splitlines()
        if line.startswith("no_real_profile_mapping:")
    ]
    return marker_lines == ["no_real_profile_mapping: true"]


def validate_closed_vocabulary_artifact(
    path: Path,
    text: str,
    schema: dict[str, object],
) -> list[str]:
    """Validate the replacement LinkedIn artifact with an exact allowlist."""
    errors: list[str] = []
    if path.as_posix() != schema.get("artifact_path"):
        errors.append("CLOSED_VOCABULARY_PATH")
        return errors

    allowed_headings = tuple(schema.get("allowed_headings", ()))
    required_metadata = schema.get("required_metadata", {})
    required_contract_keys = tuple(schema.get("required_contract_keys", ()))
    if not isinstance(required_metadata, dict):
        return ["CLOSED_VOCABULARY_SCHEMA"]

    headings: list[str] = []
    metadata: dict[str, str] = {}
    contract_keys: list[str] = []
    row_pattern = re.compile(r"^- unknown: (.+)\.$")
    for line in text.splitlines():
        if not line:
            continue
        if line.startswith("#"):
            if line not in allowed_headings:
                errors.append("CLOSED_VOCABULARY_TOKEN")
            headings.append(line)
            continue
        if ": " in line and not line.startswith("- "):
            key, value = line.split(": ", 1)
            if required_metadata.get(key) != value or key in metadata:
                errors.append("CLOSED_VOCABULARY_TOKEN")
            metadata[key] = value
            continue
        row_match = row_pattern.fullmatch(line)
        if row_match is None:
            errors.append("CLOSED_VOCABULARY_TOKEN")
            continue
        mapping = _parse_semicolon_row(row_match.group(1))
        if mapping is None:
            errors.append("CLOSED_VOCABULARY_ROW")
            continue
        dynamic_keys = set(mapping) - {
            "candidate_id",
            "evidence_state",
            "scope_bucket",
            "target_id",
            "no_external_action",
            "draft_only",
        }
        if len(dynamic_keys) != 1:
            errors.append("CLOSED_VOCABULARY_ROW")
            continue
        contract_key = dynamic_keys.pop()
        expected_mapping = {
            "candidate_id": "JSC-CASE-ALPHA",
            contract_key: "unknown",
            "evidence_state": "unknown",
            "scope_bucket": "scope_bucket_unknown",
            "target_id": "JSC-TARGET-ALPHA",
            "no_external_action": "true",
            "draft_only": "true",
        }
        if mapping != expected_mapping or contract_key not in required_contract_keys:
            errors.append(f"{contract_key}: CLOSED_VOCABULARY_TOKEN")
        contract_keys.append(contract_key)

    if tuple(headings) != allowed_headings:
        errors.append("CLOSED_VOCABULARY_HEADINGS")
    if metadata != required_metadata:
        errors.append("CLOSED_VOCABULARY_METADATA")
    if tuple(contract_keys) != required_contract_keys:
        errors.append("CLOSED_VOCABULARY_CONTRACT_KEYS")
        for contract_key in required_contract_keys:
            if contract_keys.count(contract_key) != 1:
                errors.append(f"{contract_key}: CLOSED_VOCABULARY_CONTRACT_KEY")
    return sorted(set(errors))


def scan_text(path: Path, text: str) -> Counter[str]:
    corpus_parts = [normalize_and_decode(text)]
    parsed_json: object | None = None
    dossier_candidate: object | None = None
    structured_scan_value: object | None = None
    has_duplicate_json_key = False
    if path.suffix.lower() == ".json":
        try:
            parsed_json = json.loads(text)
        except (json.JSONDecodeError, ValueError):
            parsed_json = None
        try:
            dossier_candidate = json.loads(text, object_pairs_hook=_unique_json_object)
        except _DuplicateJsonKeyError:
            has_duplicate_json_key = True
            dossier_candidate = None
        except (json.JSONDecodeError, ValueError):
            dossier_candidate = None
        if parsed_json is not None:
            safe_scan_value = _safe_dossier_scan_value(text, dossier_candidate)
            if safe_scan_value is None:
                safe_scan_value = _safe_dossier_v2_scan_value(
                    text, dossier_candidate
                )
            if safe_scan_value is None:
                safe_scan_value = _safe_target_research_scan_value(
                    text, dossier_candidate
                )
            if safe_scan_value is None:
                safe_scan_value = _safe_market_dossier_scan_value(
                    path, text, dossier_candidate
                )
            if safe_scan_value is None:
                safe_scan_value = (
                    _safe_career_next_action_eligibility_sources_scan_value(
                        path, text, dossier_candidate
                    )
                )
            if safe_scan_value is None:
                safe_scan_value = _safe_private_vacancy_packet_sources_scan_value(
                    path, text, dossier_candidate
                )
            if safe_scan_value is None:
                safe_scan_value = _safe_recruiter_practice_scan_value(
                    text, dossier_candidate
                )
            if safe_scan_value is not None:
                structured_scan_value = safe_scan_value
                corpus_parts = [
                    normalize_and_decode(fragment)
                    for fragment in _json_leaf_assignments(safe_scan_value)
                ]
                corpus_parts.extend(
                    normalize_and_decode(scalar)
                    for scalar in _json_scalars(safe_scan_value)
                )
            else:
                structured_scan_value = parsed_json
                corpus_parts.append(
                    normalize_and_decode(
                        json.dumps(parsed_json, sort_keys=True, ensure_ascii=False)
                    )
                )
                corpus_parts.extend(
                    normalize_and_decode(scalar) for scalar in _json_scalars(parsed_json)
                )
    corpus = "\n".join(corpus_parts)
    violations: Counter[str] = Counter()
    if has_duplicate_json_key:
        violations["DUPLICATE_JSON_KEY"] = 1
    for rule_id, pattern in RULES.items():
        matches = list(pattern.finditer(corpus))
        if rule_id == "PHONE_NUMBER":
            matches = [
                match
                for match in matches
                if not re.search(r"(?i)codex\.\d+$", corpus[max(0, match.start() - 6):match.end()])
            ]
        count = len(matches)
        if count:
            violations[rule_id] = count
    if (
        isinstance(dossier_candidate, dict)
        and dossier_candidate.get("schema_version") == TARGET_RESEARCH_SCHEMA_VERSION
    ):
        candidate_identity_policy = _load_candidate_identity_policy()
        if candidate_identity_policy is None:
            violations["CANDIDATE_IDENTITY_POLICY_UNAVAILABLE"] = 1
        elif candidate_identity_policy(dossier_candidate):
            violations["CANDIDATE_IDENTITY"] = 1
    for key, raw_value in ASSIGNMENT_PATTERN.findall(corpus):
        value = raw_value.strip().casefold().replace("-", "_")
        if value in SAFE_PLACEHOLDER_VALUES:
            continue
        tokens = _normalize_key(key)
        if _key_is_secret(tokens):
            violations["SECRET_ASSIGNMENT"] += 1
        if _key_is_free_name(tokens):
            violations["NAME_FIELD"] += 1
        if _key_is_private_analytics(tokens):
            violations["PRIVATE_ANALYTICS_VALUE"] += 1
    handles = [
        match
        for match in HANDLE_PATTERN.findall(corpus)
        if not re.search(re.escape(match) + r"[a-z0-9.-]+\.[a-z]{2,}", corpus, re.I)
    ]
    if handles:
        violations["SOCIAL_HANDLE"] = len(handles)
    analytics_count = sum(len(pattern.findall(corpus)) for pattern in ANALYTICS_VALUE_PATTERNS)
    if analytics_count:
        violations["PRIVATE_ANALYTICS_VALUE"] = analytics_count
    structured_count = _structured_text_singling_out(path, normalize_and_decode(text))
    is_exact_non_record_schema = (
        path == NON_RECORD_SCHEMA_PATH
        and isinstance(parsed_json, dict)
        and isinstance(parsed_json.get("$schema"), str)
    )
    if structured_scan_value is not None and not is_exact_non_record_schema:
        json_structured_count = sum(
            _mapping_is_singling_out(mapping)
            for mapping in _walk_mappings(structured_scan_value)
        )
        structured_count += json_structured_count
    if structured_count and not _is_exact_synthetic_market_v2_fixture(
        path, text, dossier_candidate
    ):
        violations["SINGLING_OUT_STRUCTURED_COMBINATION"] = structured_count
    return violations


def validate_private_first_interview_v2_artifact(path: Path, text: str) -> Counter[str]:
    """Keep v2 persisted contracts free of the raw v1 source container."""

    violations: Counter[str] = Counter()
    if "source_group" in text or "source_group_json" in text:
        violations["PRIVATE_INTERVIEW_V2_RAW_SOURCE_FIELD"] += 1
        return violations
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        violations["PRIVATE_INTERVIEW_V2_INVALID_JSON"] += 1
        return violations
    if path.name.startswith("accepted-"):
        provenance = value.get("source_provenance") if isinstance(value, dict) else None
        if not (
            isinstance(value, dict)
            and value.get("schema_version") == "private-first-interview-conversion-board-v2"
            and isinstance(provenance, dict)
            and provenance.get("provenance_state") == "synthetic_fixture"
            and "source_digest" not in provenance
            and value.get("delivery", {}).get("external_actions_authorized") is False
        ):
            violations["PRIVATE_INTERVIEW_V2_FIXTURE_CONTRACT"] += 1
    return violations


def scan_repository_source_text(path: Path, text: str) -> Counter[str]:
    """Scan code/schema/assets with high-confidence rules that avoid test syntax."""

    corpus = normalize_and_decode(text)
    violations: Counter[str] = Counter()
    email_matches = list(RULES["EMAIL_ADDRESS"].finditer(corpus))
    non_placeholder_emails = [
        match.group(0)
        for match in email_matches
        if not match.group(0).casefold().endswith(".invalid")
        and not re.search(
            r"https?://[^\s/@:]+:$",
            corpus[max(0, match.start() - 80) : match.start()],
            re.I,
        )
    ]
    if non_placeholder_emails:
        violations["EMAIL_ADDRESS"] = len(non_placeholder_emails)

    profile_urls = RULES["LINKEDIN_PROFILE_URL"].findall(corpus)
    non_placeholder_urls = [
        url
        for url in profile_urls
        if not re.search(r"/in/(?:example|synthetic[-a-z0-9]*)\b", url, re.I)
    ]
    if non_placeholder_urls:
        violations["LINKEDIN_PROFILE_URL"] = len(non_placeholder_urls)

    local_paths = RULES["LOCAL_USER_PATH"].findall(corpus)
    if local_paths:
        violations["LOCAL_USER_PATH"] = len(local_paths)

    name_assignment = re.compile(
        r"(?im)\b(?:candidate[_ -]?name|display[_ -]?name|given[_ -]?name|"
        r"family[_ -]?name|legal[_ -]?name|nombre[_ -]?del[_ -]?candidato)\b"
        r"\s*[:=]\s*['\"]([^'\"\n]{2,160})['\"]"
    )
    names = [
        value
        for value in name_assignment.findall(corpus)
        if not re.search(r"\b(?:synthetic|example|placeholder|sentinel|sint[eé]tic[oa])\b", value, re.I)
    ]
    if names:
        violations["NAME_FIELD"] = len(names)

    raw_assignment = re.compile(
        r"(?im)\b(?:raw[_ -]?profile(?:[_ -]?(?:text|data|export))?|"
        r"headline[_ -]?text|about[_ -]?text|experience[_ -]?text)\b"
        r"\s*[:=]\s*['\"]([^'\"\n]{8,500})['\"]"
    )
    raw_values = [
        value
        for value in raw_assignment.findall(corpus)
        if not re.search(r"\b(?:synthetic|example|placeholder|copied profile text)\b", value, re.I)
    ]
    if raw_values:
        violations["RAW_PROFILE_MATERIAL"] = len(raw_values)
    return violations


def tracked_eval_paths(repo_root: Path) -> tuple[Path, ...]:
    result = subprocess.run(
        ["git", "ls-files", "tests/evals"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    return tuple(
        Path(line)
        for line in result.stdout.splitlines()
        if Path(line).suffix.lower() in TEXT_SUFFIXES
    )


def staged_release_artifact_snapshot(repo_root: Path) -> tuple[StagedArtifact, ...]:
    """Capture eligible staged paths and their exact blob OIDs in one Git snapshot."""

    result = subprocess.run(
        [
            "git", "diff", "--cached", "--raw", "-z", "--no-renames",
            "--diff-filter=ACMR", "--", *(root.as_posix() for root in STAGED_RELEASE_ARTIFACT_ROOTS),
        ],
        cwd=repo_root,
        capture_output=True,
        check=True,
    )
    parts = result.stdout.split(b"\0")
    records: list[StagedArtifact] = []
    index = 0
    while index + 1 < len(parts):
        metadata = parts[index]
        raw_path = parts[index + 1]
        index += 2
        if not metadata or not raw_path or not metadata.startswith(b":"):
            continue
        fields = metadata[1:].split()
        if len(fields) != 5:
            continue
        new_mode, object_id, status = fields[1], fields[3], fields[4]
        path = Path(raw_path.decode("utf-8", errors="surrogateescape"))
        if (
            status not in {b"A", b"C", b"M", b"R"}
            or new_mode not in {b"100644", b"100755"}
            or path.is_absolute()
            or ".." in path.parts
            or path.suffix.lower() not in TEXT_SUFFIXES
            or not any(path.is_relative_to(root) for root in STAGED_RELEASE_ARTIFACT_ROOTS)
        ):
            continue
        records.append(
            StagedArtifact(
                path=path,
                mode=new_mode.decode("ascii"),
                stage=0,
                object_id=object_id.decode("ascii", errors="strict"),
            )
        )
    return tuple(sorted(set(records)))


def staged_release_artifact_paths(repo_root: Path) -> tuple[Path, ...]:
    return tuple(record.path for record in staged_release_artifact_snapshot(repo_root))


def read_staged_release_artifact_text(
    repo_root: Path, artifact: StagedArtifact | Path
) -> str:
    """Read the immutable blob captured in the supplied staged snapshot record."""

    if isinstance(artifact, Path):
        matches = [
            record
            for record in staged_release_artifact_snapshot(repo_root)
            if record.path == artifact
        ]
        if len(matches) != 1:
            raise StagedArtifactReadError("staged artifact has no unique snapshot entry")
        artifact = matches[0]
    if artifact.mode not in {"100644", "100755"} or artifact.stage != 0:
        raise StagedArtifactReadError("staged artifact is not a regular stage-zero blob")
    object_id = artifact.object_id
    size_result = subprocess.run(
        ["git", "cat-file", "-s", object_id],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    try:
        size = int(size_result.stdout.strip())
    except ValueError as error:
        raise StagedArtifactReadError("staged artifact has invalid blob size") from error
    if size > MAX_STAGED_ARTIFACT_BYTES:
        raise StagedArtifactReadError("staged artifact exceeds scan size limit")
    blob_result = subprocess.run(
        ["git", "cat-file", "blob", object_id],
        cwd=repo_root,
        capture_output=True,
        check=True,
    )
    if len(blob_result.stdout) != size:
        raise StagedArtifactReadError("staged artifact blob size changed")
    try:
        return blob_result.stdout.decode("utf-8")
    except UnicodeDecodeError as error:
        raise StagedArtifactReadError("staged artifact is not UTF-8") from error


def scan_paths(
    repo_root: Path,
    staged_paths: tuple[Path, ...] | set[Path] | None = None,
) -> tuple[Path, ...]:
    staged_snapshot = (
        set(staged_release_artifact_paths(repo_root))
        if staged_paths is None
        else set(staged_paths)
    )
    return tuple(
        sorted(
            set(tracked_eval_paths(repo_root))
            | set(INVENTORY_PATHS)
            | set(DOSSIER_SOURCE_INVENTORY_PATHS)
            | set(PRIVATE_FIRST_INTERVIEW_BOARD_SOURCE_INVENTORY_PATHS)
            | staged_snapshot
        )
    )


def required_marker_paths(repo_root: Path) -> tuple[Path, ...]:
    paths = list(MARKER_PATHS)
    for directory in MARKER_DIRECTORIES:
        paths.extend(
            path.relative_to(repo_root)
            for path in sorted((repo_root / directory).iterdir())
            if path.is_file() and path.suffix.lower() in {".json", ".md"}
        )
    return tuple(paths)


def format_finding(path: Path, rule_id: str, count: int) -> str:
    return f"{path}: {rule_id}: count={count}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    arguments = parser.parse_args(argv)
    repo_root = arguments.repo_root.resolve()
    failures: Counter[tuple[Path, str]] = Counter()
    staged_snapshot = staged_release_artifact_snapshot(repo_root)
    staged_records = {record.path: record for record in staged_snapshot}
    staged_paths = set(staged_records)
    for path in scan_paths(repo_root, staged_paths):
        try:
            if path in staged_paths:
                text = read_staged_release_artifact_text(
                    repo_root, staged_records[path]
                )
            elif path in PRIVATE_VACANCY_PACKET_FIXTURE_PATHS:
                text = _read_bounded_regular_text(repo_root / path, 512 * 1024)
                if text is None:
                    raise StagedArtifactReadError(
                        "private packet fixture is not a bounded regular file"
                    )
            else:
                text = (repo_root / path).read_text(encoding="utf-8")
        except (OSError, UnicodeError, subprocess.CalledProcessError, StagedArtifactReadError):
            failures[(path, "SCAN_INPUT_UNREADABLE")] += 1
            continue
        violations = (
            scan_repository_source_text(path, text)
            if path in DOSSIER_SOURCE_INVENTORY_PATHS
            else scan_text(path, text)
        )
        if path in PRIVATE_FIRST_INTERVIEW_BOARD_V2_ARTIFACT_PATHS:
            violations.update(validate_private_first_interview_v2_artifact(path, text))
        for rule_id, count in violations.items():
            failures[(path, rule_id)] += count
        if path == Path("tests/evals/with-skill/linkedin.md"):
            schema_path = repo_root / "tests/fixtures/linkedin-closed-vocabulary.schema.json"
            try:
                schema = json.loads(schema_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                failures[(path, "CLOSED_VOCABULARY_SCHEMA")] += 1
            else:
                for rule_id in validate_closed_vocabulary_artifact(path, text, schema):
                    failures[(path, rule_id)] += 1
    current_snapshot = staged_release_artifact_snapshot(repo_root)
    if current_snapshot != staged_snapshot:
        failures[(Path(".git/index"), "STAGED_INDEX_CHANGED")] += 1
    for path in required_marker_paths(repo_root):
        text = (repo_root / path).read_text(encoding="utf-8")
        if not has_true_non_mapping_marker(path, text):
            failures[(path, "NON_MAPPING_MARKER")] += 1
    for (path, rule_id), count in sorted(failures.items()):
        print(format_finding(path, rule_id, count))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
