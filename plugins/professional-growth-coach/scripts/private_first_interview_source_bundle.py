#!/usr/bin/env python3
"""Issue opaque, source-bound proof bundles for the private interview board."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any


_UNAVAILABLE = "source bundle is unavailable"
_CONTRACT = "private-first-interview-source-bundle-v1"
_PROVENANCE_STATES = frozenset({"synthetic_fixture", "composition_only"})
_DIGEST_PATTERN = re.compile(r"^snap-private-first-interview-v1-sha256-[0-9a-f]{64}$")
_SOURCE_KINDS = (
    "recruiter_outreach_lab",
    "quality_gate",
    "first_interview_7_day_plan",
    "weekly_coach_plan",
    "decision_ladder",
    "plan_days",
    "daily_review_logs",
)
_CONSTRUCTOR_TOKEN = object()
def _sibling(name: str) -> Any:
    path = Path(__file__).with_name(name)
    origin = os.path.realpath(os.fspath(path))
    direct_name = {
        "validate_private_first_interview_conversion_board_v1.py": "validate_private_first_interview_conversion_board_v1",
        "private_first_interview_conversion_board_identity.py": "private_first_interview_conversion_board_identity",
    }.get(name)
    if direct_name:
        existing = sys.modules.get(direct_name)
        if existing is not None:
            return existing
        module_name = direct_name
    else:
        module_name = "_pgc_private_first_interview_source_bundle_" + hashlib.sha256(
            origin.encode("utf-8")
        ).hexdigest()
    existing = sys.modules.get(module_name)
    if existing is not None:
        return existing
    specification = importlib.util.spec_from_file_location(module_name, path)
    if specification is None or specification.loader is None:
        raise RuntimeError(_UNAVAILABLE)
    module = importlib.util.module_from_spec(specification)
    sys.modules[module_name] = module
    specification.loader.exec_module(module)
    return module


_snapshot = _sibling("semantic_provenance_snapshot.py")
_v1_validator = _sibling("validate_private_first_interview_conversion_board_v1.py")


class ValidatedPrivateFirstInterviewSourceBundle:
    """Immutable source payload with a deliberately metadata-only public boundary."""

    __slots__ = ("__source_group_json", "__metadata_json")

    def __new__(
        cls,
        token: object = None,
        source_group_json: str = "",
        metadata_json: str = "",
    ):
        if token is not _CONSTRUCTOR_TOKEN:
            raise TypeError(_UNAVAILABLE)
        return super().__new__(cls)

    def __init__(
        self,
        token: object = None,
        source_group_json: str = "",
        metadata_json: str = "",
    ) -> None:
        if token is not _CONSTRUCTOR_TOKEN:
            raise TypeError(_UNAVAILABLE)
        object.__setattr__(
            self,
            "_ValidatedPrivateFirstInterviewSourceBundle__source_group_json",
            source_group_json,
        )
        object.__setattr__(
            self,
            "_ValidatedPrivateFirstInterviewSourceBundle__metadata_json",
            metadata_json,
        )

    def __setattr__(self, name: str, value: object) -> None:
        raise AttributeError("source bundle is immutable")


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _metadata_for(source_group: Mapping[str, object], provenance_state: str) -> dict[str, object]:
    digest = source_group.get("source_snapshot")
    if not isinstance(digest, str):
        raise ValueError(_UNAVAILABLE)
    return {
        "source_contract": _CONTRACT,
        "provenance_state": provenance_state,
        "source_digest": digest,
        "source_kinds": list(_SOURCE_KINDS),
    }


def _capture_validated_source(source_group: Mapping[str, object]) -> dict[str, object]:
    if not _v1_validator._source_group_shape(source_group):
        raise ValueError(_UNAVAILABLE)
    if _v1_validator._unsafe_source_text(source_group):
        raise ValueError(_UNAVAILABLE)
    proof = _v1_validator.validate_private_first_interview_conversion_board_v1(
        source_group
    )
    return proof.source_group


def _bundle_from_source(
    source_group: Mapping[str, object], *, provenance_state: str
) -> ValidatedPrivateFirstInterviewSourceBundle:
    validated_source = _capture_validated_source(source_group)
    return ValidatedPrivateFirstInterviewSourceBundle(
        _CONSTRUCTOR_TOKEN,
        _canonical_json(validated_source),
        _canonical_json(_metadata_for(validated_source, provenance_state)),
    )


def issue_validated_private_first_interview_source_bundle(
    source_group: object, *, provenance_state: str
) -> ValidatedPrivateFirstInterviewSourceBundle:
    """Issue a synthetic fixture bundle from one bounded source snapshot."""
    try:
        if provenance_state != "synthetic_fixture":
            raise ValueError(_UNAVAILABLE)
        frozen = _snapshot.bounded_plain_snapshot(source_group)
        return _bundle_from_source(frozen, provenance_state="synthetic_fixture")
    except Exception:
        raise ValueError(_UNAVAILABLE) from None


def adapt_v1_private_first_interview_proof(
    validated_v1: object,
) -> ValidatedPrivateFirstInterviewSourceBundle:
    """Wrap only an exact, revalidated v1 proof without claiming attestation."""
    try:
        if type(validated_v1) is not _v1_validator.ValidatedPrivateFirstInterviewConversionBoard:
            raise TypeError(_UNAVAILABLE)
        artifact = _v1_validator._revalidate_validated_private_first_interview_conversion_board(
            validated_v1
        )
        source_group = artifact.get("source_group")
        frozen = _snapshot.bounded_plain_snapshot(source_group)
        return _bundle_from_source(frozen, provenance_state="composition_only")
    except TypeError:
        raise TypeError(_UNAVAILABLE) from None
    except Exception:
        raise ValueError(_UNAVAILABLE) from None


def _payload_json(value: object) -> tuple[str, str]:
    """Return private canonical payloads only for this exact proof class."""
    if type(value) is not ValidatedPrivateFirstInterviewSourceBundle:
        raise TypeError(_UNAVAILABLE)
    try:
        source_group_json = value._ValidatedPrivateFirstInterviewSourceBundle__source_group_json
        metadata_json = value._ValidatedPrivateFirstInterviewSourceBundle__metadata_json
        if not isinstance(source_group_json, str) or not isinstance(metadata_json, str):
            raise ValueError(_UNAVAILABLE)
        parsed = json.loads(metadata_json)
        if not _metadata_is_valid(parsed):
            raise ValueError(_UNAVAILABLE)
        return source_group_json, metadata_json
    except (AttributeError, TypeError):
        raise TypeError(_UNAVAILABLE) from None
    except Exception:
        raise ValueError(_UNAVAILABLE) from None


def _metadata_is_valid(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    digest = value.get("source_digest")
    return (
        set(value) == {
            "source_contract",
            "provenance_state",
            "source_digest",
            "source_kinds",
        }
        and value["source_contract"] == _CONTRACT
        and value["provenance_state"] in _PROVENANCE_STATES
        and isinstance(digest, str)
        and _DIGEST_PATTERN.fullmatch(digest) is not None
        and value["source_kinds"] == list(_SOURCE_KINDS)
    )


def metadata(value: object) -> dict[str, object]:
    """Return a fresh bounded metadata copy for trusted v2 validation."""
    try:
        _, metadata_json = _payload_json(value)
        parsed = json.loads(metadata_json)
        if not _metadata_is_valid(parsed):
            raise ValueError(_UNAVAILABLE)
        return parsed
    except TypeError:
        raise TypeError(_UNAVAILABLE) from None
    except Exception:
        raise ValueError(_UNAVAILABLE) from None
