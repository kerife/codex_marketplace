"""Behavioral contract for the vacancy-bound private application packet."""

from __future__ import annotations

import copy
import importlib.util
import inspect
import json
import sys
import tempfile
import unittest
from collections.abc import Mapping
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "professional-growth-coach"
SCRIPTS = PLUGIN / "scripts"
SCHEMA = PLUGIN / "schemas" / "private-vacancy-application-packet-v1.schema.json"
FIXTURES = ROOT / "tests" / "evals" / "with-skill" / "fixtures"
PACKET_FIXTURES = FIXTURES / "private-vacancy-application-packet-v1"
SCENARIOS = (
    "ready-es",
    "ready-en",
    "revise-missing-es",
    "revise-review-en",
    "stop-constraint-es",
    "stop-constraint-en",
)


def load_script(name: str):
    path = SCRIPTS / name
    specification = importlib.util.spec_from_file_location(
        f"private_vacancy_packet_test_{path.stem}", path
    )
    if specification is None or specification.loader is None:
        raise AssertionError("private vacancy packet module is unavailable")
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


MARKET_BUILDER = load_script("build_career_market_learning_dossier_v2.py")
RESPONSE_BUILDER = load_script("build_candidate_gap_response_v1.py")
ASSESSMENT_BUILDER = load_script("build_candidate_gap_assessment_v1.py")
ELIGIBILITY_BUILDER = load_script("build_career_next_action_eligibility_v1.py")
FACT_BUILDER = load_script("build_candidate_fact_matrix_v1.py")
PACKET_BUILDER = load_script("build_private_vacancy_application_packet_v1.py")
PACKET_VALIDATOR = load_script("validate_private_vacancy_application_packet_v1.py")


def load_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError("fixture root must be an object")
    return value


def canonical_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )


def requirement(
    signal: str,
    ordinal: int,
    *,
    importance: str = "must_have",
) -> dict[str, object]:
    return {
        "requirement_id": f"V-003-R-{ordinal:02d}",
        "signal": signal,
        "importance": importance,
        "source_paraphrase": "Synthetic public requirement.",
    }


def gate(token: str = "country_geography") -> dict[str, object]:
    return {
        "gate": token,
        "state": "pass",
        "observed_condition": "Synthetic public condition.",
    }


def build_eligibility_group(
    *,
    locale: str = "es",
    requirements: list[dict[str, object]] | None = None,
    gates: list[dict[str, object]] | None = None,
    relation: str = "supported",
    provider: bool = False,
) -> dict[str, object]:
    research_name = "complete-five-es.json" if locale == "es" else "limited-four-en.json"
    dossier_name = "scenario-a-es.json" if locale == "es" else "scenario-c-market-en.json"
    research = load_json(FIXTURES / "target-vacancy-research" / research_name)
    dossier = load_json(FIXTURES / "executive-career-dossier-v2" / dossier_name)
    # Keep the selected signal recurrent for ordinary packet cases. A provider
    # can coexist with packet authority only through the existing one-of-N
    # recurrence rule, so provider cases deliberately retain one occurrence.
    research["vacancies"][0]["requirements"][0]["signal"] = (
        "python" if provider else "terraform"
    )
    selected = next(
        row for row in research["vacancies"] if row["vacancy_id"] == "V-003"
    )
    selected["requirements"] = copy.deepcopy(
        requirements or [requirement("terraform", 1)]
    )
    if not any(row["signal"] == "terraform" for row in selected["requirements"]):
        selected["requirements"].append(
            requirement("terraform", len(selected["requirements"]) + 1, importance="responsibility_only")
        )
    selected["eligibility_gates"] = copy.deepcopy(gates or [gate()])
    provider_value = None
    if provider:
        provider_name = "complete-es.json" if locale == "es" else "limited-en.json"
        provider_value = load_json(
            FIXTURES / "career-learning-provider-research" / provider_name
        )
    market = MARKET_BUILDER.build_market_dossier_v2(research, dossier)
    market_rows = market["vacancies"]
    selected_index = next(
        index
        for index, row in enumerate(market_rows)
        if row["vacancy_id"] == "V-003"
    )
    effective_relation = "knowledge_gap" if provider else relation
    response = RESPONSE_BUILDER.build_candidate_gap_response_v1(
        research,
        market,
        {
            "selected_vacancy_ordinal": f"V{selected_index + 1}",
            "selected_signal": "terraform",
            "relation": effective_relation,
            "selected_provider_ordinal": None,
        },
        provider_value,
    )
    assessment = ASSESSMENT_BUILDER.build_candidate_gap_assessment_v1(
        research, dossier, market, response, provider_value
    )
    eligibility = ELIGIBILITY_BUILDER.build_career_next_action_eligibility_v1(
        research, dossier, market, response, assessment, provider_value
    )
    return {
        "eligibility": eligibility,
        "research": research,
        "executive_dossier": dossier,
        "market_dossier": market,
        "gap_response": response,
        "gap_assessment": assessment,
        "provider_research": provider_value,
    }


FACT_SOURCES = [
    {"source_type": "verified_record", "evidence_state": "verified"},
    {"source_type": "cv", "evidence_state": "candidate_reported"},
    {"source_type": "portfolio", "evidence_state": "inferred"},
    {"source_type": "candidate_statement", "evidence_state": "unknown"},
]


def fact(
    signal: str,
    *,
    evidence: str = "verified",
    kind: str = "requirement",
    fact_type: str = "experience",
    relation: str = "supports",
    conflict: str = "clear",
    confidentiality: str = "usable",
) -> dict[str, object]:
    source_ordinal = {
        "verified": 1,
        "candidate_reported": 2,
        "inferred": 3,
        "unknown": 4,
    }[evidence]
    return {
        "fact_type": fact_type,
        "source_ordinals": [source_ordinal],
        "signal_bindings": [{"kind": kind, "signal": signal}],
        "signal_relation": relation,
        "conflict_state": conflict,
        "confidentiality": confidentiality,
    }


def forbidden_fact() -> dict[str, object]:
    return {
        "fact_type": "portfolio_evidence",
        "source_ordinals": [3],
        "signal_bindings": [],
        "signal_relation": "unknown",
        "conflict_state": "clear",
        "confidentiality": "forbidden",
    }


def build_fact_group(
    facts: list[dict[str, object]], *, locale: str = "es"
) -> dict[str, object]:
    source_group = {
        "locale": locale,
        "captured_at": "2026-08-24T12:30:45Z",
        "sources": copy.deepcopy(FACT_SOURCES),
        "facts": copy.deepcopy(facts),
    }
    matrix = FACT_BUILDER.build_candidate_fact_matrix_v1(source_group)
    return {"candidate_fact_matrix": matrix, "source_group": source_group}


def composite_group(
    *,
    locale: str = "es",
    requirements: list[dict[str, object]] | None = None,
    gates: list[dict[str, object]] | None = None,
    facts: list[dict[str, object]] | None = None,
    relation: str = "supported",
    provider: bool = False,
) -> dict[str, object]:
    return {
        "eligibility_group": build_eligibility_group(
            locale=locale,
            requirements=requirements,
            gates=gates,
            relation=relation,
            provider=provider,
        ),
        "candidate_fact_group": build_fact_group(
            facts or [fact("terraform")], locale=locale
        ),
    }


def build_packet(group: object | None = None) -> dict[str, object]:
    return PACKET_BUILDER.build_private_vacancy_application_packet_v1(
        composite_group() if group is None else group
    )


def scenario_source_group(name: str) -> dict[str, object]:
    locale = "en" if name.endswith("-en") else "es"
    if name.startswith("ready-"):
        facts = [fact("terraform")]
    elif name == "revise-missing-es":
        facts = [forbidden_fact()]
    elif name == "revise-review-en":
        facts = [
            fact("terraform"),
            fact(
                "terraform",
                relation="unknown",
                confidentiality="review_required",
                fact_type="constraint",
            ),
        ]
    elif name.startswith("stop-constraint-"):
        facts = [
            fact("terraform"),
            fact(
                "country_geography",
                kind="eligibility_gate",
                fact_type="constraint",
                relation="contradicts",
            ),
        ]
    else:
        raise AssertionError(f"unknown scenario: {name}")
    return composite_group(locale=locale, facts=facts)


def regenerate_canonical_fixtures() -> None:
    """Rebuild all checked-in scenario files from source-tree production builders."""
    for name in SCENARIOS:
        directory = PACKET_FIXTURES / name
        directory.mkdir(parents=True, exist_ok=True)
        sources = scenario_source_group(name)
        matrix = sources["candidate_fact_group"]["candidate_fact_matrix"]
        packet = build_packet(sources)
        (directory / "sources.json").write_bytes(canonical_bytes(sources))
        (directory / "candidate-fact-matrix.json").write_bytes(
            canonical_bytes(matrix)
        )
        (directory / "application-packet.json").write_bytes(
            canonical_bytes(packet)
        )


class OneShotMapping(Mapping[str, object]):
    """Mapping that fails if a caller-controlled object is traversed twice."""

    def __init__(self, value: dict[str, object]) -> None:
        self._value = value
        self.reads = 0

    def __iter__(self):
        return iter(self._value)

    def __len__(self) -> int:
        return len(self._value)

    def __getitem__(self, key: str) -> object:
        return self._value[key]

    def items(self):
        self.reads += 1
        if self.reads > 1:
            raise RuntimeError("review-sensitive-secret-reread")
        return self._value.items()


class PrivateVacancyApplicationPacketV1Tests(unittest.TestCase):
    def assert_builder_rejected(self, group: object) -> None:
        """Break caught: invalid packet sources escape the generic build boundary."""
        with self.assertRaises(ValueError) as caught:
            PACKET_BUILDER.build_private_vacancy_application_packet_v1(group)
        self.assertEqual(
            "private vacancy application packet is invalid", str(caught.exception)
        )
        self.assertNotIn("review-sensitive", str(caught.exception))

    def assert_validator_rejected(self, value: object, group: object) -> None:
        """Break caught: a crossed artifact/source pair obtains a validated snapshot."""
        with self.assertRaises(ValueError) as caught:
            PACKET_VALIDATOR.validate_private_vacancy_application_packet_v1(
                value, group
            )
        self.assertEqual(
            "private vacancy application packet does not match validated sources",
            str(caught.exception),
        )
        self.assertNotIn("review-sensitive", str(caught.exception))

    def test_builder_projects_exact_target_rows_drafts_and_snapshot_bindings(self) -> None:
        """Break caught: packet fields, source joins, deterministic drafts, or bindings drift."""
        group = composite_group()
        packet = build_packet(group)
        self.assertEqual(
            {
                "schema_version",
                "locale",
                "as_of_date",
                "target_binding",
                "readiness",
                "requirement_evidence",
                "unsupported_or_missing_claims",
                "draft_materials",
                "claim_review",
                "first_interview_prep_handoff",
                "tracking_proposal",
                "approval_boundary",
                "source_snapshot",
            },
            set(packet),
        )
        self.assertEqual("private-vacancy-application-packet-v1", packet["schema_version"])
        self.assertEqual(
            {
                "vacancy_id",
                "vacancy_title",
                "organization_label",
                "eligibility_state",
                "next_safe_action",
            },
            set(packet["target_binding"]),
        )
        self.assertEqual("V-003", packet["target_binding"]["vacancy_id"])
        self.assertEqual("Fixture DevOps Role C", packet["target_binding"]["vacancy_title"])
        self.assertEqual("Fixture Employer C", packet["target_binding"]["organization_label"])
        self.assertEqual(
            "prepare_private_vacancy_packet",
            packet["target_binding"]["next_safe_action"],
        )
        self.assertEqual(
            {
                "requirement_id",
                "signal",
                "priority",
                "fact_ids",
                "coverage",
                "confidence",
            },
            set(packet["requirement_evidence"][0]),
        )
        self.assertEqual(
            ("V-003-R-01", "terraform", "required", ["F-001"], "supported", "high"),
            tuple(
                packet["requirement_evidence"][0][field]
                for field in (
                    "requirement_id",
                    "signal",
                    "priority",
                    "fact_ids",
                    "coverage",
                    "confidence",
                )
            ),
        )
        self.assertEqual(
            ["D-CV-001"],
            [row["draft_id"] for row in packet["draft_materials"]["cv_bullets"]],
        )
        self.assertEqual(
            ["D-RS-001"],
            [row["draft_id"] for row in packet["draft_materials"]["recruiter_summary"]],
        )
        self.assertEqual(
            ["D-MA-001"],
            [row["draft_id"] for row in packet["draft_materials"]["message_angle"]],
        )
        self.assertEqual(
            ["C-001", "C-002", "C-003"],
            [row["claim_id"] for row in packet["claim_review"]],
        )
        self.assertEqual(
            {
                "eligibility",
                "target_vacancy_research",
                "candidate_fact_matrix",
                "aggregate",
            },
            set(packet["source_snapshot"]),
        )
        self.assertRegex(
            packet["source_snapshot"]["eligibility"],
            r"^snap-next-action-eligibility-v1-sha256-[0-9a-f]{64}$",
        )
        self.assertRegex(
            packet["source_snapshot"]["target_vacancy_research"],
            r"^snap-market-sha256-[0-9a-f]{64}$",
        )
        self.assertRegex(
            packet["source_snapshot"]["candidate_fact_matrix"],
            r"^snap-candidate-fact-matrix-v1-sha256-[0-9a-f]{64}$",
        )
        self.assertRegex(
            packet["source_snapshot"]["aggregate"],
            r"^snap-private-vacancy-packet-sources-v1-sha256-[0-9a-f]{64}$",
        )
        self.assertNotIn("target_vacancy_selector", inspect.signature(
            PACKET_BUILDER.build_private_vacancy_application_packet_v1
        ).parameters)

    def test_all_six_coverage_rules_and_all_claim_decisions_are_total_and_ordered(self) -> None:
        """Break caught: a coverage branch overlaps, falls through, or emits wrong review rows."""
        requirements = [
            requirement("terraform", 1),
            requirement("kubernetes", 2),
            requirement("python", 3, importance="preferred"),
            requirement("linux", 4),
            requirement("observability", 5),
            requirement("authentication", 6),
        ]
        facts = [
            fact("terraform"),
            fact("terraform", fact_type="constraint", relation="contradicts"),
            fact("kubernetes"),
            fact("python", evidence="candidate_reported"),
            fact("linux"),
            fact("linux", fact_type="constraint", relation="unknown"),
            fact("observability", fact_type="constraint", relation="unknown"),
        ]
        packet = build_packet(composite_group(requirements=requirements, facts=facts))
        self.assertEqual(
            [
                ("conflicting", "unknown"),
                ("supported", "high"),
                ("supported", "medium"),
                ("partial", "low"),
                ("review_required", "low"),
                ("missing", "unknown"),
            ],
            [
                (row["coverage"], row["confidence"])
                for row in packet["requirement_evidence"]
            ],
        )
        self.assertEqual(
            ["C-005", "C-006", "C-007", "C-008"],
            packet["readiness"]["revision_claim_ids"],
        )
        self.assertEqual(
            ["use", "use", "use", "use", "revise", "revise", "revise", "omit"],
            [row["decision"] for row in packet["claim_review"]],
        )
        null_rows = [row for row in packet["claim_review"] if row["draft_id"] is None]
        self.assertEqual(4, len(null_rows))
        self.assertEqual(
            ["V-003-R-01", "V-003-R-04", "V-003-R-05", "V-003-R-06"],
            [row["requirement_ids"][0] for row in null_rows],
        )
        self.assertEqual([], null_rows[-1]["fact_ids"])

    def test_ready_state_is_non_vacuous_private_review_only(self) -> None:
        """Break caught: complete evidence authorizes action or readiness becomes vacuous."""
        packet = build_packet()
        readiness = packet["readiness"]
        self.assertEqual("ready_for_manual_authorization", readiness["state"])
        self.assertIs(readiness["manual_review_required"], True)
        self.assertIs(readiness["external_action_authorized"], False)
        self.assertEqual([], readiness["blocking_requirement_ids"])
        self.assertEqual([], readiness["blocking_gate_tokens"])
        self.assertEqual([], readiness["revision_claim_ids"])
        self.assertTrue(packet["draft_materials"]["cv_bullets"])
        self.assertTrue(all(row["decision"] == "use" for row in packet["claim_review"]))
        self.assertEqual("available", packet["first_interview_prep_handoff"]["state"])
        self.assertEqual("unknown", packet["first_interview_prep_handoff"]["interview_stage"])
        self.assertEqual("proposed", packet["tracking_proposal"]["record_state"])
        self.assertEqual("application_packet_drafted", packet["tracking_proposal"]["event_kind"])
        self.assertEqual(
            {
                "artifact_state": "private_draft",
                "allowed_next_step": "manual_private_review",
                "prohibited_actions": [
                    "external_edit",
                    "upload",
                    "export",
                    "share",
                    "submit",
                    "publish",
                    "message",
                    "connect",
                    "apply",
                    "schedule",
                    "calendar_create",
                    "purchase",
                    "enroll",
                ],
                "authorization_required": True,
            },
            packet["approval_boundary"],
        )

        optional_only = composite_group(
            requirements=[requirement("terraform", 1, importance="preferred")],
            facts=[forbidden_fact()],
        )
        optional_packet = build_packet(optional_only)
        self.assertEqual("revise_first", optional_packet["readiness"]["state"])
        self.assertEqual([], optional_packet["readiness"]["blocking_requirement_ids"])
        self.assertEqual([], optional_packet["claim_review"])
        self.assertEqual([], optional_packet["draft_materials"]["cv_bullets"])

    def test_stop_requires_exact_verified_clear_nonsuperseded_gate_constraint(self) -> None:
        """Break caught: uncertainty stops work, or a verified gate blocker fails to suppress drafts."""
        blocker = fact(
            "country_geography",
            kind="eligibility_gate",
            fact_type="constraint",
            relation="contradicts",
        )
        packet = build_packet(composite_group(facts=[fact("terraform"), blocker]))
        self.assertEqual("stop", packet["readiness"]["state"])
        self.assertEqual(["country_geography"], packet["readiness"]["blocking_gate_tokens"])
        self.assertEqual([], packet["readiness"]["revision_claim_ids"])
        self.assertEqual(
            {"cv_bullets": [], "recruiter_summary": [], "message_angle": []},
            packet["draft_materials"],
        )
        self.assertEqual([], packet["claim_review"])
        self.assertEqual("suppressed", packet["first_interview_prep_handoff"]["state"])
        self.assertEqual([], packet["first_interview_prep_handoff"]["requirement_ids"])
        self.assertEqual([], packet["first_interview_prep_handoff"]["fact_ids"])
        self.assertEqual("not_proposed", packet["tracking_proposal"]["record_state"])
        self.assertEqual("none", packet["tracking_proposal"]["event_kind"])
        self.assertEqual("not_started", packet["tracking_proposal"]["outcome_state"])

        for evidence, conflict in (
            ("candidate_reported", "clear"),
            ("verified", "conflicting"),
            ("verified", "superseded"),
        ):
            with self.subTest(evidence=evidence, conflict=conflict):
                nonblocker = fact(
                    "country_geography",
                    evidence=evidence,
                    kind="eligibility_gate",
                    fact_type="constraint",
                    relation="contradicts",
                    conflict=conflict,
                )
                result = build_packet(
                    composite_group(facts=[fact("terraform"), nonblocker])
                )
                self.assertEqual(
                    "ready_for_manual_authorization", result["readiness"]["state"]
                )
                self.assertEqual([], result["readiness"]["blocking_gate_tokens"])

    def test_signal_kinds_are_separate_and_unmapped_public_requirement_revises(self) -> None:
        """Break caught: a gate-only token becomes requirement evidence or caller text is echoed."""
        group = composite_group(
            requirements=[
                requirement("language", 1),
                requirement("terraform", 2, importance="responsibility_only"),
            ],
            gates=[gate("language")],
            facts=[
                fact(
                    "language",
                    kind="eligibility_gate",
                    fact_type="constraint",
                ),
                fact("terraform"),
            ],
        )
        packet = build_packet(group)
        language_row = packet["requirement_evidence"][0]
        self.assertEqual(([], "missing", "unknown"), (
            language_row["fact_ids"], language_row["coverage"], language_row["confidence"]
        ))
        self.assertEqual("revise_first", packet["readiness"]["state"])
        self.assertEqual(["V-003-R-01"], packet["readiness"]["blocking_requirement_ids"])
        self.assertNotIn(
            "Synthetic public requirement",
            json.dumps(packet, ensure_ascii=False),
        )

    def test_exact_matching_rejects_alias_substring_and_caller_derived_prose(self) -> None:
        """Break caught: aliases, substrings, or caller prose create affirmative claims."""
        group = composite_group(
            requirements=[
                requirement("terraform_enterprise", 1),
                requirement("terraform", 2, importance="responsibility_only"),
            ],
            facts=[fact("terraform")],
        )
        packet = build_packet(group)
        self.assertEqual("missing", packet["requirement_evidence"][0]["coverage"])
        self.assertEqual([], packet["requirement_evidence"][0]["fact_ids"])
        self.assertEqual("supported", packet["requirement_evidence"][1]["coverage"])

        alias_group = build_fact_group([fact("terraform")])
        alias_group["source_group"]["facts"][0]["signal_bindings"][0]["signal"] = "tf"
        crossed = composite_group()
        crossed["candidate_fact_group"] = alias_group
        self.assert_builder_rejected(crossed)

        caller_prose = composite_group()
        caller_prose["draft_text"] = "review-sensitive-secret"
        self.assert_builder_rejected(caller_prose)
        second_selector = composite_group()
        second_selector["target_vacancy_id"] = "review-sensitive-secret"
        self.assert_builder_rejected(second_selector)

    def test_nonpacket_eligibility_action_is_invalid_not_a_stop_packet(self) -> None:
        """Break caught: an unrelated next action is converted into a packet stop decision."""
        group = composite_group(
            relation="proof_gap",
            facts=[
                fact("terraform"),
                fact(
                    "country_geography",
                    kind="eligibility_gate",
                    fact_type="constraint",
                    relation="contradicts",
                ),
            ],
        )
        self.assertEqual(
            "build_bounded_proof",
            group["eligibility_group"]["eligibility"]["recommended_next_action"],
        )
        self.assert_builder_rejected(group)

    def test_provider_group_revalidates_and_projects_without_provider_copy(self) -> None:
        """Break caught: provider presence bypasses validation or leaks provider prose."""
        group = composite_group(provider=True)
        packet = build_packet(group)
        self.assertEqual("ready_for_manual_authorization", packet["readiness"]["state"])
        serialized = json.dumps(packet, ensure_ascii=False)
        provider = group["eligibility_group"]["provider_research"]
        self.assertIsNotNone(provider)
        self.assertNotIn(provider["options"][0]["option"], serialized)

    def test_validator_rejects_tampering_in_all_seven_and_two_source_values(self) -> None:
        """Break caught: any upstream or fact-group mutation survives full source recomputation."""
        group = composite_group(provider=True)
        packet = build_packet(group)
        validated = PACKET_VALIDATOR.validate_private_vacancy_application_packet_v1(
            packet, group
        )
        self.assertIsInstance(
            validated, PACKET_VALIDATOR.ValidatedPrivateVacancyPacket
        )

        eligibility_mutations = {
            "eligibility": lambda value: value.update(
                {"recommended_next_action": "build_bounded_proof"}
            ),
            "research": lambda value: value.update({"as_of_date": "2026-08-12"}),
            "executive_dossier": lambda value: value.update({"locale": "en"}),
            "market_dossier": lambda value: value.update({"as_of_date": "2026-08-12"}),
            "gap_response": lambda value: value.update({"relation": "unknown"}),
            "gap_assessment": lambda value: value["assessments"][0].update(
                {"relation": "unknown"}
            ),
            "provider_research": lambda value: value.update({"state": "unavailable"}),
        }
        for field, mutation in eligibility_mutations.items():
            with self.subTest(eligibility_field=field):
                crossed = copy.deepcopy(group)
                mutation(crossed["eligibility_group"][field])
                self.assert_validator_rejected(packet, crossed)

        matrix_tamper = copy.deepcopy(group)
        matrix_tamper["candidate_fact_group"]["candidate_fact_matrix"]["facts"][0][
            "fact_id"
        ] = "F-099"
        self.assert_validator_rejected(packet, matrix_tamper)
        raw_tamper = copy.deepcopy(group)
        raw_tamper["candidate_fact_group"]["source_group"]["captured_at"] = (
            "2026-08-24T12:30:46Z"
        )
        self.assert_validator_rejected(packet, raw_tamper)

        packet_tamper = copy.deepcopy(packet)
        packet_tamper["readiness"]["external_action_authorized"] = True
        self.assert_validator_rejected(packet_tamper, group)

    def test_builder_and_validator_capture_composites_once_and_snapshot_is_immutable(self) -> None:
        """Break caught: caller mappings are reread or a validated packet can be mutated."""
        raw_group = composite_group()
        one_shot = OneShotMapping(raw_group)
        packet = build_packet(one_shot)
        self.assertEqual(1, one_shot.reads)
        raw_group["candidate_fact_group"]["source_group"]["facts"][0][
            "signal_relation"
        ] = "unknown"
        self.assertEqual("supported", packet["requirement_evidence"][0]["coverage"])

        validator_group = OneShotMapping(composite_group())
        validator_value = OneShotMapping(copy.deepcopy(packet))
        validated = PACKET_VALIDATOR.validate_private_vacancy_application_packet_v1(
            validator_value, validator_group
        )
        self.assertEqual(1, validator_group.reads)
        self.assertEqual(1, validator_value.reads)
        first_copy = validated.artifact
        first_copy["locale"] = "en"
        self.assertEqual("es", validated.artifact["locale"])
        with self.assertRaises((AttributeError, TypeError)):
            validated.artifact_json = "{}"
        with self.assertRaises(TypeError):
            PACKET_VALIDATOR.ValidatedPrivateVacancyPacket()
        self.assertEqual(
            ["value", "source_group"],
            list(
                inspect.signature(
                    PACKET_VALIDATOR.validate_private_vacancy_application_packet_v1
                ).parameters
            ),
        )

    def test_builder_is_total_bounded_and_no_echo_for_hostile_mappings(self) -> None:
        """Break caught: recursive, oversized, or exception input leaks details or partial data."""
        recursive = composite_group()
        recursive["cycle"] = recursive
        self.assert_builder_rejected(recursive)

        oversized = composite_group()
        oversized.update({f"extra_{index}": index for index in range(151)})
        self.assert_builder_rejected(oversized)

        class ExplodingMapping(Mapping[str, object]):
            def __iter__(self):
                raise RuntimeError("review-sensitive-secret")

            def __len__(self) -> int:
                return 1

            def __getitem__(self, key: str) -> object:
                raise RuntimeError("review-sensitive-secret")

            def items(self):
                raise RuntimeError("review-sensitive-secret")

        self.assert_builder_rejected(ExplodingMapping())

    def test_loader_rejects_duplicate_json_and_has_no_artifact_only_validator(self) -> None:
        """Break caught: ambiguous JSON or artifact-only trust bypasses source validation."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "packet.json"
            path.write_text(
                '{"schema_version":"private-vacancy-application-packet-v1",'
                '"schema_version":"review-sensitive-secret"}',
                encoding="utf-8",
            )
            with self.assertRaises(
                PACKET_VALIDATOR.PrivateVacancyApplicationPacketLoadError
            ) as caught:
                PACKET_VALIDATOR.load_private_vacancy_application_packet_v1(path)
            self.assertEqual(
                "cannot load private vacancy application packet", str(caught.exception)
            )
        self.assertFalse(
            any(
                name.startswith("validate_")
                and name != "validate_private_vacancy_application_packet_v1"
                for name in vars(PACKET_VALIDATOR)
            )
        )

    def test_schema_is_closed_bounded_and_encodes_state_conditionals(self) -> None:
        """Break caught: schema opens rows, weakens bounds, or permits crossed state shapes."""
        schema = load_json(SCHEMA)
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(
            [
                "schema_version",
                "locale",
                "as_of_date",
                "target_binding",
                "readiness",
                "requirement_evidence",
                "unsupported_or_missing_claims",
                "draft_materials",
                "claim_review",
                "first_interview_prep_handoff",
                "tracking_proposal",
                "approval_boundary",
                "source_snapshot",
            ],
            schema["required"],
        )
        requirement_rows = schema["properties"]["requirement_evidence"]
        self.assertEqual((1, 30), (requirement_rows["minItems"], requirement_rows["maxItems"]))
        self.assertFalse(requirement_rows["items"]["additionalProperties"])
        self.assertEqual(100, requirement_rows["items"]["properties"]["fact_ids"]["maxItems"])
        self.assertEqual(20, schema["properties"]["draft_materials"]["properties"]["cv_bullets"]["maxItems"])
        self.assertEqual(60, schema["properties"]["claim_review"]["maxItems"])
        self.assertGreaterEqual(len(schema["allOf"]), 3)

    def test_canonical_scenarios_are_source_rebuilt_byte_for_byte_and_safe(self) -> None:
        """Break caught: a fixture is hand-edited, incomplete, crossed, or leaks source data."""
        expected_states = {
            "ready-es": "ready_for_manual_authorization",
            "ready-en": "ready_for_manual_authorization",
            "revise-missing-es": "revise_first",
            "revise-review-en": "revise_first",
            "stop-constraint-es": "stop",
            "stop-constraint-en": "stop",
        }
        self.assertEqual(set(SCENARIOS), {path.name for path in PACKET_FIXTURES.iterdir()})
        for name in SCENARIOS:
            with self.subTest(scenario=name):
                directory = PACKET_FIXTURES / name
                self.assertEqual(
                    {"sources.json", "candidate-fact-matrix.json", "application-packet.json"},
                    {path.name for path in directory.iterdir()},
                )
                expected_sources = scenario_source_group(name)
                fixture_sources = load_json(directory / "sources.json")
                self.assertEqual(expected_sources, fixture_sources)
                expected_matrix = FACT_BUILDER.build_candidate_fact_matrix_v1(
                    fixture_sources["candidate_fact_group"]["source_group"]
                )
                expected_packet = build_packet(fixture_sources)
                self.assertEqual(
                    canonical_bytes(expected_matrix),
                    (directory / "candidate-fact-matrix.json").read_bytes(),
                )
                self.assertEqual(
                    canonical_bytes(expected_packet),
                    (directory / "application-packet.json").read_bytes(),
                )
                self.assertEqual(expected_states[name], expected_packet["readiness"]["state"])
                generated = canonical_bytes(expected_matrix) + canonical_bytes(expected_packet)
                generated_lower = generated.lower()
                for forbidden in (
                    b"http://",
                    b"https://",
                    b"@",
                    b"password=",
                    b"api_key=",
                    b"<script",
                    b"private_analytics",
                ):
                    self.assertNotIn(forbidden, generated_lower)

    def test_copy_is_closed_localized_and_never_uses_candidate_prose(self) -> None:
        """Break caught: locale drifts or candidate-authored prose enters a draft template."""
        es = build_packet(composite_group(locale="es"))
        en = build_packet(composite_group(locale="en"))
        self.assertNotEqual(es["readiness"]["headline"], en["readiness"]["headline"])
        self.assertNotEqual(
            es["draft_materials"]["cv_bullets"][0]["text"],
            en["draft_materials"]["cv_bullets"][0]["text"],
        )
        for packet in (es, en):
            serialized = json.dumps(packet, ensure_ascii=False)
            self.assertNotIn("source_paraphrase", serialized)
            self.assertNotIn("Synthetic public requirement", serialized)
            self.assertNotIn("fact_text", serialized)


if __name__ == "__main__":
    unittest.main()
