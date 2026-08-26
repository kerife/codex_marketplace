import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = (
    ROOT
    / "tests"
    / "fixtures"
    / "private-first-interview-conversion-board-v1"
    / "accepted-en.json"
)
SCHEMA_PATH = ROOT / "schemas" / "private-first-interview-conversion-board-v2.schema.json"
sys.path.insert(0, str(ROOT / "scripts"))

from validate_json_schema_subset import validate_schema_instance
from private_first_interview_conversion_board_identity import (
    ValidatedPrivateFirstInterviewConversionBoard,
)
from private_first_interview_conversion_board_v2_identity import (
    ValidatedPrivateFirstInterviewConversionBoardV2,
)
import validate_private_first_interview_conversion_board_v1 as validate_v1
import write_private_first_interview_conversion_board_v1 as write_v1
import private_first_interview_source_bundle as source_bundle
import build_private_first_interview_conversion_board_v1 as build_v1
import validate_private_first_interview_conversion_board_v2 as validate_v2
import build_private_first_interview_conversion_board_v2 as build_v2


def synthetic_source() -> dict[str, object]:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))["source_group"]


def issue_fixture_bundle() -> source_bundle.ValidatedPrivateFirstInterviewSourceBundle:
    return source_bundle.issue_validated_private_first_interview_source_bundle(
        synthetic_source(), provenance_state="synthetic_fixture"
    )


def rebind_snapshot(source: dict[str, object]) -> None:
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


class PrivateFirstInterviewConversionBoardV2Tests(unittest.TestCase):
    def _proof(self, *, locale: str = "en", as_of_date: str = "2026-08-26"):
        return build_v2.build_private_first_interview_conversion_board_v2(
            issue_fixture_bundle(), locale=locale, as_of_date=as_of_date
        )

    def test_sanitized_projection_has_closed_shape_and_bounded_provenance(self):
        proof = self._proof()
        artifact = proof.artifact
        self.assertIs(type(proof), ValidatedPrivateFirstInterviewConversionBoardV2)
        self.assertEqual([], validate_schema_instance(artifact, json.loads(SCHEMA_PATH.read_text())))
        self.assertEqual("private-first-interview-conversion-board-v2", artifact["schema_version"])
        self.assertEqual(
            {
                "source_contract": "private-first-interview-source-bundle-v1",
                "provenance_state": "synthetic_fixture",
                "source_digest": synthetic_source()["source_snapshot"],
                "source_kinds": [
                    "recruiter_outreach_lab",
                    "quality_gate",
                    "first_interview_7_day_plan",
                    "weekly_coach_plan",
                    "decision_ladder",
                    "plan_days",
                    "daily_review_logs",
                ],
            },
            artifact["source_provenance"],
        )
        self.assertNotIn("source_group", artifact)
        self.assertNotIn("record_id", json.dumps(artifact))
        self.assertNotIn("fact_summary", json.dumps(artifact))
        self.assertEqual(1, len(artifact["decision"]))
        self.assertEqual(7, len(artifact["week"]))
        self.assertEqual(4, len(artifact["decision_ladder"]))
        self.assertEqual(7, len(artifact["daily_reviews"]))
        self.assertEqual(
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
            artifact["delivery"],
        )

    def test_mixed_v1_v2_loaders_share_the_v1_proof_identity(self):
        self.assertIs(source_bundle._v1_validator, validate_v1)
        self.assertIs(validate_v2._v1, validate_v1)
        v1_proof = build_v1.build_private_first_interview_conversion_board_v1(
            synthetic_source()
        )
        self.assertIs(type(v1_proof), ValidatedPrivateFirstInterviewConversionBoard)
        with tempfile.TemporaryDirectory() as directory:
            receipt = write_v1.write_private_first_interview_conversion_board_v1(
                v1_proof, Path(directory) / "v1-board.json"
            )
            self.assertTrue(receipt.output_path.is_file())
        bundle = source_bundle.adapt_v1_private_first_interview_proof(v1_proof)
        v2_proof = build_v2.build_private_first_interview_conversion_board_v2(
            bundle, as_of_date="2026-08-26"
        )
        self.assertEqual(
            "composition_only", v2_proof.artifact["source_provenance"]["provenance_state"]
        )

    def test_projection_does_not_copy_safe_source_prose(self):
        source = synthetic_source()
        source["plan_days"][0]["action"] = "Private source phrase that must not persist"
        source["daily_review_logs"][0]["observed_signal"] = "Distinct private review phrase"
        rebind_snapshot(source)
        bundle = source_bundle.issue_validated_private_first_interview_source_bundle(
            source, provenance_state="synthetic_fixture"
        )
        artifact = build_v2.build_private_first_interview_conversion_board_v2(
            bundle, as_of_date="2026-08-26"
        ).artifact
        rendered = json.dumps(artifact, ensure_ascii=False)
        self.assertNotIn("Private source phrase that must not persist", rendered)
        self.assertNotIn("Distinct private review phrase", rendered)

    def test_stop_state_suppresses_all_detail_sections(self):
        source = synthetic_source()
        for name in (
            "recruiter_outreach_lab",
            "quality_gate",
            "first_interview_7_day_plan",
            "weekly_coach_plan",
        ):
            source[name]["state"] = "stop"
        for check in source["quality_gate"]["checks"]:
            check["state"] = "stop"
        rebind_snapshot(source)
        bundle = source_bundle.issue_validated_private_first_interview_source_bundle(
            source, provenance_state="synthetic_fixture"
        )
        artifact = build_v2.build_private_first_interview_conversion_board_v2(
            bundle, as_of_date="2026-08-26"
        ).artifact
        self.assertEqual("stop", artifact["decision"][0]["state"])
        self.assertEqual(
            {
                "schema_version",
                "artifact_kind",
                "locale",
                "as_of_date",
                "source_provenance",
                "decision",
                "approval_boundary",
                "delivery",
            },
            set(artifact),
        )

    def test_only_exact_source_bundles_can_reach_projection(self):
        raw = synthetic_source()
        v1 = build_v1.build_private_first_interview_conversion_board_v1(raw)
        caller_artifact = {"source_provenance": source_bundle.metadata(issue_fixture_bundle())}

        class ForgedBundle:
            pass

        for candidate in (raw, v1, caller_artifact, ForgedBundle()):
            with self.subTest(candidate=type(candidate).__name__):
                with self.assertRaisesRegex(ValueError, "does not match validated sources"):
                    build_v2.build_private_first_interview_conversion_board_v2(
                        candidate, as_of_date="2026-08-26"
                    )

    def test_rehashed_raw_source_and_unsafe_confidential_prose_fail_before_projection(self):
        raw = synthetic_source()
        raw["plan_days"][0]["action"] = "Rehashed but caller-supplied"
        rebind_snapshot(raw)
        with self.assertRaisesRegex(ValueError, "does not match validated sources"):
            build_v2.build_private_first_interview_conversion_board_v2(
                raw, as_of_date="2026-08-26"
            )

        unsafe = synthetic_source()
        unsafe["first_interview_7_day_plan"]["fact_summary"] = "secret confidential text"
        rebind_snapshot(unsafe)
        with self.assertRaisesRegex(ValueError, "source bundle is unavailable") as raised:
            source_bundle.issue_validated_private_first_interview_source_bundle(
                unsafe, provenance_state="synthetic_fixture"
            )
        self.assertNotIn("secret confidential text", str(raised.exception))

    def test_unknown_locale_or_invalid_explicit_date_fail_closed(self):
        for locale, date in (("fr", "2026-08-26"), ("en", "not-a-date"), ("en", "2026-02-30")):
            with self.subTest(locale=locale, date=date):
                with self.assertRaisesRegex(ValueError, "does not match validated sources"):
                    build_v2.build_private_first_interview_conversion_board_v2(
                        issue_fixture_bundle(), locale=locale, as_of_date=date
                    )

    def test_revalidation_detects_duplicate_keys_and_tampered_proof_payloads(self):
        proof = self._proof()
        artifact_json, source_json, metadata_json = validate_v2._identity._validation_payload_json(proof)
        duplicate_json = '{"schema_version":"private-first-interview-conversion-board-v2","schema_version":"forged"}'
        forged = validate_v2._identity._issue_validated_private_first_interview_conversion_board_v2(
            duplicate_json, source_json, metadata_json
        )
        with self.assertRaisesRegex(ValueError, "does not match validated sources"):
            validate_v2._revalidate_validated_private_first_interview_conversion_board_v2(forged)

    def test_manually_allocated_exact_proof_is_not_issuer_validated(self):
        proof = self._proof()
        artifact_json, source_json, metadata_json = validate_v2._identity._validation_payload_json(proof)
        forged = object.__new__(ValidatedPrivateFirstInterviewConversionBoardV2)
        object.__setattr__(
            forged,
            "_ValidatedPrivateFirstInterviewConversionBoardV2__artifact_json",
            artifact_json,
        )
        object.__setattr__(
            forged,
            "_ValidatedPrivateFirstInterviewConversionBoardV2__source_group_json",
            source_json,
        )
        object.__setattr__(
            forged,
            "_ValidatedPrivateFirstInterviewConversionBoardV2__metadata_json",
            metadata_json,
        )
        with self.assertRaisesRegex(ValueError, "does not match validated sources"):
            validate_v2._revalidate_validated_private_first_interview_conversion_board_v2(forged)

        tampered = copy.deepcopy(proof.artifact)
        tampered["source_provenance"]["provenance_state"] = "upstream_attested"
        forged = validate_v2._identity._issue_validated_private_first_interview_conversion_board_v2(
            json.dumps(tampered, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
            source_json,
            metadata_json,
        )
        with self.assertRaisesRegex(ValueError, "does not match validated sources"):
            validate_v2._revalidate_validated_private_first_interview_conversion_board_v2(forged)


if __name__ == "__main__":
    unittest.main()
