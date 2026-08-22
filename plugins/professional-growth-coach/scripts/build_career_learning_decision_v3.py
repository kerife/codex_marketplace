#!/usr/bin/env python3
"""Build zero or one v3 learning decision from recomputed eligibility."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any


def _sibling(name: str) -> Any:
    path = Path(__file__).with_name(name)
    specification = importlib.util.spec_from_file_location(f"_pgc_{path.stem}", path)
    if specification is None or specification.loader is None:
        raise RuntimeError("required learning v3 dependency is unavailable")
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


_snapshot = _sibling("semantic_provenance_snapshot.py")
_eligibility_builder = _sibling("build_career_next_action_eligibility_v1.py")
_eligibility_validator = _sibling("validate_career_next_action_eligibility_v1.py")
_alignment = _sibling("derive_candidate_market_alignment_v2.py")
_projector = _sibling("project_career_learning_decision_v3.py")

bounded_plain_snapshot = _snapshot.bounded_plain_snapshot
LEARNING_ACTIONS = _projector.LEARNING_ACTIONS
SCHEMA_VERSION = "career-learning-decision-v3"
_PRIVACY_BOUNDARY = "identity_free_structured_provenance_only"
_OUTCOME_BOUNDARY = "not_an_interview_offer_salary_or_roi_prediction"
_SOURCE_FIELDS = frozenset(
    {
        "research",
        "executive_dossier",
        "market_dossier",
        "gap_response",
        "gap_assessment",
        "eligibility",
        "provider_research",
    }
)


def _canonical_json(value: Mapping[str, object]) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _snapshot_for_frozen_eligibility(value: Mapping[str, object]) -> str:
    digest = hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()
    return f"snap-next-action-eligibility-v1-sha256-{digest}"


def _state(value: object) -> str:
    states = {
        "complete": "complete",
        "limited_market_evidence": "limited",
        "market_evidence_unavailable": "unavailable",
    }
    result = states.get(value) if isinstance(value, str) else None
    if result is None:
        raise ValueError("career learning decision v3 is invalid")
    return result


def _validated_group(
    frozen_group: Mapping[str, object],
) -> tuple[
    Mapping[str, object],
    Mapping[str, object],
    Mapping[str, object],
    Mapping[str, object],
    Mapping[str, object],
    Mapping[str, object],
    Mapping[str, object] | None,
    Mapping[str, object],
]:
    if set(frozen_group) != _SOURCE_FIELDS:
        raise ValueError("career learning decision v3 is invalid")
    eligibility_group = {
        "value": frozen_group["eligibility"],
        "research": frozen_group["research"],
        "executive_dossier": frozen_group["executive_dossier"],
        "market_dossier": frozen_group["market_dossier"],
        "gap_response": frozen_group["gap_response"],
        "gap_assessment": frozen_group["gap_assessment"],
        "provider_research": frozen_group["provider_research"],
    }
    if _eligibility_validator._validate_career_next_action_eligibility_from_frozen(
        eligibility_group
    ):
        raise ValueError("career learning decision v3 is invalid")
    source_group = {
        "research": frozen_group["research"],
        "executive_dossier": frozen_group["executive_dossier"],
        "market_dossier": frozen_group["market_dossier"],
        "gap_response": frozen_group["gap_response"],
        "gap_assessment": frozen_group["gap_assessment"],
        "provider_research": frozen_group["provider_research"],
    }
    recomputed = _eligibility_builder._project_eligibility_from_frozen(source_group)
    supplied = frozen_group["eligibility"]
    if not isinstance(supplied, Mapping) or _canonical_json(supplied) != _canonical_json(
        recomputed
    ):
        raise ValueError("career learning decision v3 is invalid")
    validated = _eligibility_builder._validated_group(source_group)
    alignment = _alignment.derive_candidate_market_alignment_v2(
        validated.research, validated.dossier
    )
    return (
        validated.research,
        validated.dossier,
        validated.market,
        validated.response,
        validated.assessment,
        supplied,
        validated.provider,
        alignment,
    )


def _project_bundle(
    research: Mapping[str, object],
    dossier: Mapping[str, object],
    market: Mapping[str, object],
    response: Mapping[str, object],
    assessment: Mapping[str, object],
    eligibility: Mapping[str, object],
    provider: Mapping[str, object] | None,
    alignment: Mapping[str, object],
) -> dict[str, object]:
    projected = _projector.project_career_learning_decision_v3(
        str(research["locale"]),
        eligibility,
        alignment,
        research,
        market,
        dossier,
        provider,
    )
    decisions = [] if projected is None else [projected]
    return {
        "schema_version": SCHEMA_VERSION,
        "locale": research["locale"],
        "as_of_date": research["as_of_date"],
        "state": _state(market.get("state")),
        "source_research_snapshot": eligibility["source_research_snapshot"],
        "source_dossier_snapshot": eligibility["source_dossier_snapshot"],
        "source_alignment_snapshot": eligibility["source_alignment_snapshot"],
        "source_market_snapshot": eligibility["source_market_snapshot"],
        "source_provider_research_snapshot": eligibility[
            "source_provider_research_snapshot"
        ],
        "source_gap_response_snapshot": eligibility["source_gap_response_snapshot"],
        "source_gap_assessment_snapshot": eligibility[
            "source_gap_assessment_snapshot"
        ],
        "source_next_action_eligibility_snapshot": _snapshot_for_frozen_eligibility(
            eligibility
        ),
        "decisions": decisions,
        "privacy_boundary": _PRIVACY_BOUNDARY,
        "no_external_action": True,
        "outcome_boundary": _OUTCOME_BOUNDARY,
    }


def _project_learning_v3_from_frozen(
    frozen_group: Mapping[str, object],
) -> dict[str, object]:
    """Project the complete bundle only from one captured built-in group."""
    return _project_bundle(*_validated_group(frozen_group))


def build_career_learning_decision_v3(
    research: object,
    executive_dossier: object,
    market_dossier: object,
    gap_response: object,
    gap_assessment: object,
    eligibility: object,
    provider_research: object | None = None,
) -> dict[str, object]:
    """Capture once and project only the independently recomputed action."""
    try:
        frozen = bounded_plain_snapshot(
            {
                "research": research,
                "executive_dossier": executive_dossier,
                "market_dossier": market_dossier,
                "gap_response": gap_response,
                "gap_assessment": gap_assessment,
                "eligibility": eligibility,
                "provider_research": provider_research,
            }
        )
        return _project_learning_v3_from_frozen(frozen)
    except Exception:
        raise ValueError("career learning decision v3 is invalid") from None
