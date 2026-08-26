import copy
import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "private-first-interview-conversion-board-v1"
SCHEMA_PATH = ROOT / "schemas" / "private-first-interview-conversion-board-v1.schema.json"
sys.path.insert(0, str(ROOT / "scripts"))
from validate_json_schema_subset import validate_schema_instance
from private_first_interview_conversion_board_identity import (
    ValidatedPrivateFirstInterviewConversionBoard,
)
import validate_private_first_interview_conversion_board_v1 as board_validator


class PrivateFirstInterviewConversionBoardContractTests(unittest.TestCase):
    def _load_fixture(self, locale):
        return json.loads((FIXTURES / f"accepted-{locale}.json").read_text(encoding="utf-8"))

    def _assert_valid(self, value):
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        errors = validate_schema_instance(value, schema)
        if len({row["day"] for row in value.get("week", [])}) != 7:
            errors.append("week days must be unique")
        if len({row["day"] for row in value.get("daily_reviews", [])}) != 7:
            errors.append("daily review days must be unique")
        if len({row["branch"] for row in value.get("decision_ladder", [])}) != 4:
            errors.append("decision branches must be unique")
        source_group = value.get("source_group", {})
        if isinstance(source_group, dict):
            if len({row.get("day") for row in source_group.get("plan_days", [])}) != 7:
                errors.append("source plan days must be unique")
            if len({row.get("day") for row in source_group.get("daily_review_logs", [])}) != 7:
                errors.append("source daily review days must be unique")
            if len({row.get("branch") for row in source_group.get("decision_ladder", [])}) != 4:
                errors.append("source decision branches must be unique")
        self.assertEqual([], errors)

    def test_accepted_es_and_en_fixtures_have_closed_cardinalities(self):
        for locale in ("es", "en"):
            with self.subTest(locale=locale):
                value = self._load_fixture(locale)
                self.assertEqual("private-first-interview-conversion-board-v1", value["schema_version"])
                self.assertEqual(locale, value["locale"])
                self._assert_valid(value)
                self.assertEqual(1, len(value["decision"]))
                self.assertEqual(7, len(value["week"]))
                self.assertEqual(4, len(value["decision_ladder"]))
                self.assertEqual(7, len(value["daily_reviews"]))
                self.assertEqual(
                    list(range(1, 8)), [row["day"] for row in value["week"]]
                )
                self.assertEqual(
                    ["advance", "clarify", "pause", "stop"],
                    [row["branch"] for row in value["decision_ladder"]],
                )
                self.assertEqual(
                    list(range(1, 8)), [row["day"] for row in value["daily_reviews"]]
                )

    def test_missing_section_is_rejected(self):
        value = self._load_fixture("en")
        value.pop("risk_checks")
        with self.assertRaises(AssertionError):
            self._assert_valid(value)

    def test_duplicate_day_is_rejected(self):
        value = self._load_fixture("en")
        value["week"][1]["day"] = value["week"][0]["day"]
        with self.assertRaises(AssertionError):
            self._assert_valid(value)

    def test_duplicate_source_plan_day_is_rejected(self):
        value = self._load_fixture("en")
        value["source_group"]["plan_days"][1]["day"] = value["source_group"]["plan_days"][0]["day"]
        self.assertTrue(validate_schema_instance(value, json.loads(SCHEMA_PATH.read_text())))
        with self.assertRaises(AssertionError):
            self._assert_valid(value)

    def test_duplicate_source_review_day_is_rejected(self):
        value = self._load_fixture("en")
        value["source_group"]["daily_review_logs"][1]["day"] = value["source_group"]["daily_review_logs"][0]["day"]
        self.assertTrue(validate_schema_instance(value, json.loads(SCHEMA_PATH.read_text())))
        with self.assertRaises(AssertionError):
            self._assert_valid(value)

    def test_extra_branch_is_rejected(self):
        value = self._load_fixture("en")
        value["decision_ladder"].append(copy.deepcopy(value["decision_ladder"][-1]))
        with self.assertRaises(AssertionError):
            self._assert_valid(value)

    def test_private_booleans_are_immutable(self):
        value = self._load_fixture("en")
        for field, changed in (
            ("draft_only", False),
            ("external_actions_authorized", True),
            ("no_message_action", False),
            ("no_calendar_action", False),
            ("raw_event_retained", True),
            ("raw_reply_retained", True),
            ("raw_answer_retained", True),
            ("candidate_review_required", False),
        ):
            with self.subTest(field=field):
                bad = copy.deepcopy(value)
                bad["delivery"][field] = changed
                with self.assertRaises(AssertionError):
                    self._assert_valid(bad)

    def test_fixtures_are_synthetic_and_contain_no_external_surface(self):
        def strings(value):
            if isinstance(value, dict):
                for key, item in value.items():
                    yield from strings(key)
                    yield from strings(item)
            elif isinstance(value, list):
                for item in value:
                    yield from strings(item)
            elif isinstance(value, str):
                yield value

        for locale in ("es", "en"):
            with self.subTest(locale=locale):
                text = "\n".join(strings(self._load_fixture(locale))).lower()
                self.assertNotIn("http://", text)
                self.assertNotIn("https://", text)
                self.assertNotIn("@", text)
                self.assertNotIn("raw recruiter", text)
                self.assertNotIn("raw candidate", text)

    def test_validator_accepts_raw_source_group_and_issues_exact_identity(self):
        value = self._load_fixture("en")
        proof = board_validator.validate_private_first_interview_conversion_board_v1(
            value["source_group"]
        )
        self.assertIs(type(proof), ValidatedPrivateFirstInterviewConversionBoard)
        self.assertEqual(value["source_group"], proof.source_group)
        self.assertEqual("private-first-interview-conversion-board-v1", proof.artifact["schema_version"])

    def test_validator_accepts_checked_in_es_and_en_composites(self):
        for locale in ("es", "en"):
            with self.subTest(locale=locale):
                value = self._load_fixture(locale)
                proof = board_validator.validate_private_first_interview_conversion_board_v1(value)
                self.assertEqual(value, proof.artifact)

    def test_source_crossing_and_projection_mutation_fail_closed(self):
        value = self._load_fixture("en")
        crossed = copy.deepcopy(value)
        crossed["source_group"]["group_id"] = "group-synthetic-crossed"
        with self.assertRaisesRegex(ValueError, "does not match validated sources"):
            board_validator.validate_private_first_interview_conversion_board_v1(crossed)

        changed_projection = copy.deepcopy(value)
        changed_projection["decision"][0]["objective"] = "caller supplied final row"
        with self.assertRaisesRegex(ValueError, "does not match validated sources"):
            board_validator.validate_private_first_interview_conversion_board_v1(changed_projection)

    def test_source_snapshot_is_content_bound(self):
        source = self._load_fixture("en")["source_group"]
        source["source_snapshot"] = source["source_snapshot"][:-1] + "0"
        with self.assertRaisesRegex(ValueError, "does not match validated sources"):
            board_validator.validate_private_first_interview_conversion_board_v1(source)

    def test_stop_state_suppresses_tracking_detail(self):
        source = copy.deepcopy(self._load_fixture("en")["source_group"])
        for name in (
            "recruiter_outreach_lab",
            "quality_gate",
            "first_interview_7_day_plan",
            "weekly_coach_plan",
        ):
            source[name]["state"] = "stop"
        for check in source["quality_gate"]["checks"]:
            check["state"] = "stop"
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
        proof = board_validator.validate_private_first_interview_conversion_board_v1(source)
        artifact = proof.artifact
        self.assertEqual("stop", artifact["decision"][0]["state"])
        for section in (
            "sequence",
            "proof_cards",
            "risk_checks",
            "rehearsal",
            "week",
            "decision_ladder",
            "daily_reviews",
        ):
            self.assertNotIn(section, artifact)

    def test_source_mutation_after_validation_does_not_mutate_frozen_proof(self):
        source = self._load_fixture("en")["source_group"]
        proof = board_validator.validate_private_first_interview_conversion_board_v1(source)
        source["plan_days"][0]["action"] = "changed after validation"
        self.assertEqual("Review role context privately", proof.source_group["plan_days"][0]["action"])
        self.assertEqual("Review role context privately", proof.artifact["week"][0]["private_action"])

    def test_validator_rejects_unsafe_prose_pii_secret_url_html_and_control_text(self):
        cases = (
            ("https://example.invalid/private",),
            ("candidate Maria Brown",),
            ("secret credential value",),
            ("<script>alert(1)</script>",),
            ("send this calendar event",),
            ("fit score probability guarantee salary",),
            ("unsafe\u200bcontrol",),
        )
        for (payload,) in cases:
            with self.subTest(payload=payload):
                source = self._load_fixture("en")["source_group"]
                source["first_interview_7_day_plan"]["fact_summary"] = payload
                with self.assertRaisesRegex(ValueError, "does not match validated sources"):
                    board_validator.validate_private_first_interview_conversion_board_v1(source)

    def test_forged_or_duck_typed_proof_is_not_accepted(self):
        class Forged:
            artifact = self._load_fixture("en")

        with self.assertRaises(TypeError):
            board_validator._identity._validation_payload_json(Forged())

    def test_duplicate_keys_are_rejected_during_proof_revalidation(self):
        value = self._load_fixture("en")
        source_json = json.dumps(value["source_group"], ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        duplicate_json = '{"schema_version":"private-first-interview-conversion-board-v1","schema_version":"forged"}'
        forged = board_validator._identity._issue_validated_private_first_interview_conversion_board(
            duplicate_json, source_json
        )
        with self.assertRaisesRegex(ValueError, "does not match validated sources"):
            board_validator._revalidate_validated_private_first_interview_conversion_board(forged)


if __name__ == "__main__":
    unittest.main()
