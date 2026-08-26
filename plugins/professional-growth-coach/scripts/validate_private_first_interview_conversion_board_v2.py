#!/usr/bin/env python3
"""Validate the sanitized, source-bundle-bound interview board v2."""

from __future__ import annotations

import datetime as dt
import hashlib
import importlib.util
import json
import os
import re
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any


_MISMATCH = "private first-interview conversion board does not match validated sources"
_MAX_INPUT_BYTES = 512 * 1024
_DATE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
_STATES = ("ready", "clarify", "pause", "stop")
_RISK_TOPICS = ("production", "compensation", "eligibility", "availability", "confidentiality")


def _sibling(name: str) -> Any:
    path = Path(__file__).with_name(name)
    origin = os.path.realpath(os.fspath(path))
    direct_name = {
        "private_first_interview_source_bundle.py": "private_first_interview_source_bundle",
        "validate_private_first_interview_conversion_board_v1.py": "validate_private_first_interview_conversion_board_v1",
        "private_first_interview_conversion_board_identity.py": "private_first_interview_conversion_board_identity",
        "private_first_interview_conversion_board_v2_identity.py": "private_first_interview_conversion_board_v2_identity",
    }.get(name)
    if direct_name:
        existing = sys.modules.get(direct_name)
        if existing is not None:
            return existing
        module_name = direct_name
    else:
        module_name = "_pgc_private_first_interview_v2_" + hashlib.sha256(
            origin.encode("utf-8")
        ).hexdigest()
    existing = sys.modules.get(module_name)
    if existing is not None:
        return existing
    specification = importlib.util.spec_from_file_location(module_name, path)
    if specification is None or specification.loader is None:
        raise RuntimeError(_MISMATCH)
    module = importlib.util.module_from_spec(specification)
    sys.modules[module_name] = module
    specification.loader.exec_module(module)
    return module


_schema_validation = _sibling("validate_json_schema_subset.py")
_source_bundle = _sibling("private_first_interview_source_bundle.py")
_v1 = _sibling("validate_private_first_interview_conversion_board_v1.py")
_identity = _sibling("private_first_interview_conversion_board_v2_identity.py")
_SCHEMA_PATH = Path(__file__).parents[1] / "schemas" / "private-first-interview-conversion-board-v2.schema.json"
ValidatedPrivateFirstInterviewConversionBoardV2 = _identity.ValidatedPrivateFirstInterviewConversionBoardV2


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(_MISMATCH)
        value[key] = item
    return value


def _json_object(payload: str) -> dict[str, object]:
    if not isinstance(payload, str) or len(payload.encode("utf-8")) > _MAX_INPUT_BYTES:
        raise ValueError(_MISMATCH)
    value = json.loads(payload, object_pairs_hook=_unique_object)
    if not isinstance(value, dict):
        raise ValueError(_MISMATCH)
    return value


def _schema() -> dict[str, object]:
    value = _json_object(_SCHEMA_PATH.read_text(encoding="utf-8"))
    return value


def _valid_locale_and_date(locale: object, as_of_date: object) -> bool:
    if locale not in {"en", "es"} or not isinstance(as_of_date, str):
        return False
    if _DATE.fullmatch(as_of_date) is None:
        return False
    try:
        dt.date.fromisoformat(as_of_date)
    except ValueError:
        return False
    return True


def _fixed_boundary() -> tuple[dict[str, object], dict[str, object]]:
    return (
        {
            "artifact_state": "private_draft",
            "allowed_next_step": "manual_private_review",
            "prohibited_actions": [
                "message", "connect", "apply", "schedule", "calendar_create", "publish",
                "share", "upload", "submit", "export", "external_edit", "purchase", "enroll",
            ],
            "authorization_required": True,
        },
        {
            "draft_only": True,
            "external_actions_authorized": False,
            "no_message_action": True,
            "no_calendar_action": True,
            "raw_event_retained": False,
            "raw_reply_retained": False,
            "raw_answer_retained": False,
            "local_save_mode": "disabled",
            "candidate_review_required": True,
        },
    )


def _project_from_frozen(
    source_group: Mapping[str, object], metadata: Mapping[str, object], *, locale: str, as_of_date: str
) -> dict[str, object]:
    if not _v1._source_group_shape(source_group) or _v1._unsafe_source_text(source_group):
        raise ValueError(_MISMATCH)
    if not _source_bundle._metadata_is_valid(metadata):
        raise ValueError(_MISMATCH)
    if metadata["source_digest"] != source_group["source_snapshot"]:
        raise ValueError(_MISMATCH)
    if not _valid_locale_and_date(locale, as_of_date):
        raise ValueError(_MISMATCH)

    localized = _v1._localized(locale)
    states = [
        source_group[name].get("state")
        for name in ("recruiter_outreach_lab", "quality_gate", "first_interview_7_day_plan", "weekly_coach_plan")
    ]
    current_state = next((state for state in _STATES[::-1] if state in states), "clarify")
    approval_boundary, delivery = _fixed_boundary()
    artifact: dict[str, object] = {
        "schema_version": "private-first-interview-conversion-board-v2",
        "artifact_kind": "private_first_interview_conversion_board",
        "locale": locale,
        "as_of_date": as_of_date,
        "source_provenance": dict(metadata),
        "decision": [{"state": current_state, **localized["decision"]}],
        "approval_boundary": approval_boundary,
        "delivery": delivery,
    }
    if current_state == "stop":
        return artifact

    stages = ("current_state", "private_preparation", "human_review", "authorization_gate")
    artifact["sequence"] = [
        {"stage": stage, "label": localized["sequence"][index][0], "description": localized["sequence"][index][1]}
        for index, stage in enumerate(stages)
    ]
    artifact["proof_cards"] = [
        {"vacancy_signal": signal, "evidence_summary": summary, "caveat": caveat}
        for signal, summary, caveat in localized["proof"]
    ]
    artifact["risk_checks"] = [
        {
            "topic": topic,
            "trigger_question": row[0],
            "safe_response_boundary": row[1],
            "confirmation_needed": row[2],
            "forbidden_claim": row[3],
        }
        for topic, row in zip(_RISK_TOPICS, localized["risk"])
    ]
    question, purpose, structure, wait_boundary, score = localized["rehearsal"]
    artifact["rehearsal"] = {
        "question": question,
        "purpose": purpose,
        "response_structure": structure,
        "wait_boundary": wait_boundary,
        "pre_response_score": score,
    }
    artifact["week"] = [
        {
            "day": index + 1,
            "private_action": row[0],
            "evidence_boundary": row[1],
            "review_checkpoint": row[2],
            "observable_signal": row[3],
            "fallback": row[4],
            "stop_rule": row[5],
        }
        for index, row in enumerate(localized["week"])
    ]
    artifact["decision_ladder"] = [
        {
            "branch": branch,
            "trigger": localized["branch_triggers"][index],
            "evidence_requirement": localized["branches"][index][0],
            "next_safe_action": localized["branches"][index][1],
            "blocked_action": localized["branches"][index][2],
            "measurement_label": localized["branches"][index][3],
            "review_question": localized["branches"][index][4],
            "script_boundary": localized["branches"][index][5],
        }
        for index, branch in enumerate(("advance", "clarify", "pause", "stop"))
    ]
    artifact["daily_reviews"] = [
        {
            "day": index + 1,
            "observed_signal": row[2],
            "signal_quality": row[0],
            "decision": row[1],
            "evidence_log": row[2],
            "next_safe_action": row[3],
            "metric_label": row[4],
            "confounder_note": row[5],
            "coach_question": row[6],
        }
        for index, row in enumerate(localized["daily"])
    ]
    return artifact


def _validated_bundle_payload(value: object) -> tuple[dict[str, object], dict[str, object]]:
    if type(value) is not _source_bundle.ValidatedPrivateFirstInterviewSourceBundle:
        raise TypeError(_MISMATCH)
    source_json, metadata_json = _source_bundle._payload_json(value)
    source_group = _json_object(source_json)
    metadata = _json_object(metadata_json)
    if not _v1._source_group_shape(source_group) or _v1._unsafe_source_text(source_group):
        raise ValueError(_MISMATCH)
    if not _source_bundle._metadata_is_valid(metadata):
        raise ValueError(_MISMATCH)
    if metadata["source_digest"] != source_group["source_snapshot"]:
        raise ValueError(_MISMATCH)
    return source_group, metadata


def _issue_from_bundle(value: object, *, locale: str, as_of_date: str) -> ValidatedPrivateFirstInterviewConversionBoardV2:
    source_group, metadata = _validated_bundle_payload(value)
    artifact = _project_from_frozen(source_group, metadata, locale=locale, as_of_date=as_of_date)
    if _schema_validation.validate_schema_instance(artifact, _schema()):
        raise ValueError(_MISMATCH)
    return _identity._issue_validated_private_first_interview_conversion_board_v2(
        _canonical_json(artifact), _canonical_json(source_group), _canonical_json(metadata)
    )


def _validate_proof(value: object, *, locale: str, as_of_date: str) -> ValidatedPrivateFirstInterviewConversionBoardV2:
    artifact = _revalidate_validated_private_first_interview_conversion_board_v2(value)
    if artifact["locale"] != locale or artifact["as_of_date"] != as_of_date:
        raise ValueError(_MISMATCH)
    artifact_json, source_json, metadata_json = _identity._validation_payload_json(value)
    return _identity._issue_validated_private_first_interview_conversion_board_v2(
        artifact_json, source_json, metadata_json
    )


def validate_private_first_interview_conversion_board_v2(
    source_bundle_or_artifact: object, *, locale: str = "en", as_of_date: str
) -> ValidatedPrivateFirstInterviewConversionBoardV2:
    """Validate an exact source bundle or revalidate an exact v2 proof."""
    try:
        if not _valid_locale_and_date(locale, as_of_date):
            raise ValueError(_MISMATCH)
        if type(source_bundle_or_artifact) is _source_bundle.ValidatedPrivateFirstInterviewSourceBundle:
            return _issue_from_bundle(source_bundle_or_artifact, locale=locale, as_of_date=as_of_date)
        if type(source_bundle_or_artifact) is ValidatedPrivateFirstInterviewConversionBoardV2:
            return _validate_proof(source_bundle_or_artifact, locale=locale, as_of_date=as_of_date)
        raise ValueError(_MISMATCH)
    except Exception:
        raise ValueError(_MISMATCH) from None


def _revalidate_validated_private_first_interview_conversion_board_v2(value: object) -> dict[str, object]:
    """Recompute the canonical sanitized projection for private consumers."""
    try:
        artifact_json, source_json, metadata_json = _identity._validation_payload_json(value)
        artifact = _json_object(artifact_json)
        source_group = _json_object(source_json)
        metadata = _json_object(metadata_json)
        if not _valid_locale_and_date(artifact.get("locale"), artifact.get("as_of_date")):
            raise ValueError(_MISMATCH)
        expected = _project_from_frozen(
            source_group,
            metadata,
            locale=artifact["locale"],
            as_of_date=artifact["as_of_date"],
        )
        if _schema_validation.validate_schema_instance(artifact, _schema()):
            raise ValueError(_MISMATCH)
        if _canonical_json(artifact) != _canonical_json(expected):
            raise ValueError(_MISMATCH)
        return expected
    except Exception:
        raise ValueError(_MISMATCH) from None
