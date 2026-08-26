import copy
import hashlib
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "private-first-interview-source-bundle-v1.schema.json"
FIXTURE = (
    ROOT
    / "tests"
    / "fixtures"
    / "private-first-interview-conversion-board-v1"
    / "accepted-en.json"
)
sys.path.insert(0, str(ROOT / "scripts"))

from private_first_interview_conversion_board_identity import (
    ValidatedPrivateFirstInterviewConversionBoard,
)
from validate_json_schema_subset import validate_schema_instance
import build_private_first_interview_conversion_board_v1 as v1_builder
import private_first_interview_source_bundle as source_bundle


SOURCE_KINDS = [
    "recruiter_outreach_lab",
    "quality_gate",
    "first_interview_7_day_plan",
    "weekly_coach_plan",
    "decision_ladder",
    "plan_days",
    "daily_review_logs",
]


def synthetic_source() -> dict[str, object]:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))["source_group"]


class PrivateFirstInterviewSourceBundleTests(unittest.TestCase):
    def test_synthetic_bundle_is_exact_immutable_and_has_only_bounded_metadata(self):
        first = source_bundle.issue_validated_private_first_interview_source_bundle(
            synthetic_source(), provenance_state="synthetic_fixture"
        )
        second = source_bundle.issue_validated_private_first_interview_source_bundle(
            copy.deepcopy(synthetic_source()), provenance_state="synthetic_fixture"
        )

        self.assertIs(
            type(first), source_bundle.ValidatedPrivateFirstInterviewSourceBundle
        )
        self.assertFalse(hasattr(first, "source_group"))
        self.assertFalse(hasattr(first, "source_group_json"))
        with self.assertRaisesRegex(AttributeError, "source bundle is immutable"):
            first.provenance_state = "upstream_attested"

        first_metadata = source_bundle.metadata(first)
        self.assertEqual(
            {
                "source_contract": "private-first-interview-source-bundle-v1",
                "provenance_state": "synthetic_fixture",
                "source_digest": synthetic_source()["source_snapshot"],
                "source_kinds": SOURCE_KINDS,
            },
            first_metadata,
        )
        self.assertEqual(first_metadata, source_bundle.metadata(second))
        first_metadata["source_kinds"].append("forged")
        self.assertEqual(SOURCE_KINDS, source_bundle.metadata(first)["source_kinds"])

    def test_provenance_states_are_distinct_and_v1_adapter_never_upgrades(self):
        fixture = source_bundle.issue_validated_private_first_interview_source_bundle(
            synthetic_source(), provenance_state="synthetic_fixture"
        )
        v1_proof = v1_builder.build_private_first_interview_conversion_board_v1(
            synthetic_source()
        )
        self.assertIs(type(v1_proof), ValidatedPrivateFirstInterviewConversionBoard)
        composed = source_bundle.adapt_v1_private_first_interview_proof(v1_proof)

        self.assertEqual("synthetic_fixture", source_bundle.metadata(fixture)["provenance_state"])
        self.assertEqual("composition_only", source_bundle.metadata(composed)["provenance_state"])
        self.assertEqual(
            source_bundle.metadata(fixture)["source_digest"],
            source_bundle.metadata(composed)["source_digest"],
        )

    def test_upstream_attestation_is_unavailable_in_this_release(self):
        with self.assertRaisesRegex(ValueError, "source bundle is unavailable"):
            source_bundle.issue_validated_private_first_interview_source_bundle(
                synthetic_source(), provenance_state="upstream_attested"
            )
        self.assertFalse(hasattr(source_bundle, "_issue_upstream_attested_private"))
        upstream_metadata = {
            "source_contract": "private-first-interview-source-bundle-v1",
            "provenance_state": "upstream_attested",
            "source_digest": synthetic_source()["source_snapshot"],
            "source_kinds": SOURCE_KINDS,
        }
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.assertNotEqual([], validate_schema_instance(upstream_metadata, schema))
        fixture = source_bundle.issue_validated_private_first_interview_source_bundle(
            synthetic_source(), provenance_state="synthetic_fixture"
        )
        self.assertEqual("synthetic_fixture", source_bundle.metadata(fixture)["provenance_state"])

    def test_issuer_rejects_invalid_or_unsafe_inputs_without_echoing_them(self):
        unsafe = "candidate Maria Brown secret material"
        wrong_shape = synthetic_source()
        wrong_shape["first_interview_7_day_plan"].pop("objective")
        self._rebind_snapshot(wrong_shape)
        oversized = synthetic_source()
        oversized["first_interview_7_day_plan"]["fact_summary"] = "x" * 4097
        self._rebind_snapshot(oversized)
        cyclic = synthetic_source()
        cyclic["cycle"] = cyclic
        cases = (
            ("unknown provenance", synthetic_source(), "composition_only"),
            ("raw non-mapping", ["not", "a", "mapping"], "synthetic_fixture"),
            ("unsafe prose", self._with_unsafe_prose(unsafe), "synthetic_fixture"),
            ("wrong shape", wrong_shape, "synthetic_fixture"),
            ("oversized", oversized, "synthetic_fixture"),
            ("cyclic", cyclic, "synthetic_fixture"),
        )
        for label, value, state in cases:
            with self.subTest(label=label):
                with self.assertRaisesRegex(ValueError, "source bundle is unavailable") as raised:
                    source_bundle.issue_validated_private_first_interview_source_bundle(
                        value, provenance_state=state
                    )
                self.assertNotIn(unsafe, str(raised.exception))

    def test_payload_and_v1_adapter_require_exact_proof_identity(self):
        class ForgedBundle:
            source_group = synthetic_source()

        class ForgedV1:
            source_group = synthetic_source()

        with self.assertRaisesRegex(TypeError, "source bundle is unavailable"):
            source_bundle._payload_json(ForgedBundle())
        with self.assertRaisesRegex(TypeError, "source bundle is unavailable"):
            source_bundle.metadata(ForgedBundle())
        with self.assertRaisesRegex(TypeError, "source bundle is unavailable"):
            source_bundle.adapt_v1_private_first_interview_proof(ForgedV1())
        with self.assertRaisesRegex(TypeError, "source bundle is unavailable"):
            source_bundle.adapt_v1_private_first_interview_proof(synthetic_source())

    def test_invalid_digest_in_an_issued_proof_fails_closed(self):
        issued = source_bundle.issue_validated_private_first_interview_source_bundle(
            synthetic_source(), provenance_state="synthetic_fixture"
        )
        object.__setattr__(
            issued,
            "_ValidatedPrivateFirstInterviewSourceBundle__metadata_json",
            json.dumps(
                {
                    "source_contract": "private-first-interview-source-bundle-v1",
                    "provenance_state": "synthetic_fixture",
                    "source_digest": "not-a-digest",
                    "source_kinds": SOURCE_KINDS,
                }
            ),
        )
        with self.assertRaisesRegex(ValueError, "source bundle is unavailable"):
            source_bundle.metadata(issued)

    @staticmethod
    def _with_unsafe_prose(value: str) -> dict[str, object]:
        source = synthetic_source()
        source["first_interview_7_day_plan"]["fact_summary"] = value
        PrivateFirstInterviewSourceBundleTests._rebind_snapshot(source)
        return source

    @staticmethod
    def _rebind_snapshot(source: dict[str, object]) -> None:
        without_snapshot = dict(source)
        without_snapshot.pop("source_snapshot")
        source["source_snapshot"] = (
            "snap-private-first-interview-v1-sha256-"
            + hashlib.sha256(
                json.dumps(
                    without_snapshot,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            ).hexdigest()
        )
