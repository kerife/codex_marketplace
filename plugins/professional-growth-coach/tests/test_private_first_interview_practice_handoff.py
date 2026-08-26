import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "private-first-interview-conversion-board-v1" / "accepted-en.json"
SCHEMA = ROOT / "schemas" / "private-first-interview-practice-handoff-v1.schema.json"
sys.path.insert(0, str(ROOT / "scripts"))

from validate_json_schema_subset import validate_schema_instance
import build_private_first_interview_conversion_board_v2 as board_builder
import private_first_interview_source_bundle as source_bundle
import validate_recruiter_practice_session as session_validator
import validate_private_first_interview_conversion_board_v2 as board_validator
import render_recruiter_practice_session as session_renderer
import build_private_first_interview_practice_handoff as handoff_builder


def _source():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))["source_group"]


class PrivateFirstInterviewPracticeHandoffTests(unittest.TestCase):
    def _proof(self, *, locale="en", source=None):
        bundle = source_bundle.issue_validated_private_first_interview_source_bundle(
            _source() if source is None else source, provenance_state="synthetic_fixture"
        )
        return board_builder.build_private_first_interview_conversion_board_v2(
            bundle, locale=locale, as_of_date="2026-08-26"
        )

    def test_ready_board_projects_to_one_awaiting_answer_session(self):
        handoff = handoff_builder.build_private_first_interview_practice_handoff(self._proof(locale="es"))
        session = handoff.session
        self.assertEqual("recruiter-practice-session-v2", session["schema_version"])
        self.assertEqual("awaiting_answer", session["state"])
        self.assertIsNone(session["observed_answer"])
        self.assertEqual("unknown", session["feedback"]["score"])
        self.assertEqual("unknown", session["feedback"]["score_state"])
        self.assertEqual([], session_validator.validate_session(session))
        self.assertEqual(1, session["handoff_context"]["question_rank"])
        self.assertEqual("private_first_interview_conversion_board", session["handoff_context"]["source"])
        self.assertIn(self._proof(locale="es").artifact["rehearsal"]["response_structure"], session["rubric"]["criterion"])

    def test_handoff_schema_accepts_the_closed_projection(self):
        handoff = handoff_builder.build_private_first_interview_practice_handoff(self._proof())
        session = handoff.session
        wrapper = {
            "handoff_version": "private-first-interview-practice-handoff-v1",
            "handoff_kind": "private_first_interview_practice_handoff",
            "session": session,
            "proof_binding": session["handoff_context"]["source_snapshot"],
        }
        errors = validate_schema_instance(wrapper, json.loads(SCHEMA.read_text(encoding="utf-8")))
        self.assertEqual([], errors)

    def test_installed_style_session_render_keeps_board_origin_private(self):
        handoff = handoff_builder.build_private_first_interview_practice_handoff(self._proof())
        rendered = session_renderer.render_session_html(handoff.session)
        self.assertIn("This question came from a private first-interview board", rendered)
        self.assertIn('practice-handoff--board', rendered)
        self.assertNotIn("snap-practice-board", rendered)
        self.assertNotRegex(rendered, r"\b(?:Q|R|F|RB)-\d{3}\b")

    def test_only_exact_validated_board_proof_is_accepted(self):
        for candidate in (self._proof().artifact, {"state": "ready"}, object()):
            with self.subTest(candidate=type(candidate).__name__):
                with self.assertRaisesRegex(ValueError, "private first-interview practice handoff is unavailable"):
                    handoff_builder.build_private_first_interview_practice_handoff(candidate)

    def test_non_ready_board_state_fails_closed_without_session(self):
        for state in ("clarify", "pause", "stop"):
            proof = self._proof()
            artifact_json, source_json, metadata_json = board_validator._identity._validation_payload_json(proof)
            artifact = json.loads(artifact_json)
            artifact["decision"][0]["state"] = state
            forged = board_validator._identity._issue_validated_private_first_interview_conversion_board_v2(
                json.dumps(artifact, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
                source_json,
                metadata_json,
            )
            with self.subTest(state=state):
                with self.assertRaisesRegex(ValueError, "private first-interview practice handoff is unavailable"):
                    handoff_builder.build_private_first_interview_practice_handoff(forged)


if __name__ == "__main__":
    unittest.main()
