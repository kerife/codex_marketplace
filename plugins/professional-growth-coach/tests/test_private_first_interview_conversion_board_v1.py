import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "private-first-interview-conversion-board-v1"
SCHEMA_PATH = ROOT / "schemas" / "private-first-interview-conversion-board-v1.schema.json"
sys.path.insert(0, str(ROOT / "scripts"))
from validate_json_schema_subset import validate_schema_instance


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


if __name__ == "__main__":
    unittest.main()
