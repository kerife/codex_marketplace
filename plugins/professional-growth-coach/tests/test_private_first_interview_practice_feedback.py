import copy
from concurrent.futures import ThreadPoolExecutor
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "private-first-interview-conversion-board-v1" / "accepted-en.json"
SCHEMA = ROOT / "schemas" / "private-first-interview-practice-feedback-v1.schema.json"
sys.path.insert(0, str(ROOT / "scripts"))

from validate_json_schema_subset import validate_schema_instance
import build_private_first_interview_conversion_board_v2 as board_builder
import build_private_first_interview_practice_feedback as feedback_builder
import build_private_first_interview_practice_handoff as handoff_builder
import private_first_interview_source_bundle as source_bundle
import private_first_interview_practice_handoff_identity as handoff_identity
import render_private_first_interview_practice as proof_renderer
import render_recruiter_practice_session as session_renderer
import validate_private_first_interview_conversion_board_v2 as board_validator
import validate_recruiter_practice_session as session_validator


def _source():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))["source_group"]


def _feedback_result(handoff, answer):
    try:
        feedback_builder.build_private_first_interview_practice_feedback(handoff, answer)
    except ValueError:
        return False
    return True


class PrivateFirstInterviewPracticeFeedbackTests(unittest.TestCase):
    def _handoff(self, *, locale="en"):
        bundle = source_bundle.issue_validated_private_first_interview_source_bundle(
            _source(), provenance_state="synthetic_fixture"
        )
        board = board_builder.build_private_first_interview_conversion_board_v2(
            bundle, locale=locale, as_of_date="2026-08-26"
        )
        return handoff_builder.build_private_first_interview_practice_handoff(board)

    def test_answer_projects_to_ephemeral_categorical_feedback(self):
        feedback = feedback_builder.build_private_first_interview_practice_feedback(
            self._handoff(locale="es"),
            "Durante el incidente, implementé un cambio y observé una reducción del tiempo.",
        )
        session = feedback.session
        self.assertEqual("feedback_available", session["state"])
        self.assertEqual("categorical", session["feedback"]["score_state"])
        self.assertEqual("unknown", session["feedback"]["score"])
        self.assertEqual("OBS-001", session["observed_answer"]["id"])
        self.assertEqual("ephemeral", session["observed_answer"]["storage"])
        self.assertEqual(["solid"], [row["label"] for row in session["feedback"]["observations"]])
        self.assertEqual([], session_validator.validate_session(session))

    def test_feedback_uses_one_closed_signal_without_echoing_answer_or_provenance(self):
        answer = "When the alert fired, I redesigned the handoff and reduced review time."
        feedback = feedback_builder.build_private_first_interview_practice_feedback(self._handoff(), answer)
        rendered = session_renderer.render_session_html(feedback.session)
        self.assertNotIn(answer, rendered)
        self.assertNotIn("snap-practice-board", rendered)
        self.assertNotRegex(rendered, r"\b(?:Q|R|F|OBS|RB)-\d{3}\b")
        self.assertEqual(1, rendered.count('class="feedback-item feedback-item--'))
        self.assertIn("Keep this structure", rendered)

    def test_weak_answer_receives_do_not_assert_without_numeric_score(self):
        feedback = feedback_builder.build_private_first_interview_practice_feedback(
            self._handoff(), "I think I can help."
        )
        observation = feedback.session["feedback"]["observations"]
        self.assertEqual(["do_not_assert"], [row["label"] for row in observation])
        self.assertEqual("unknown", feedback.session["feedback"]["score"])

    def test_negated_action_and_result_are_not_marked_solid(self):
        for locale, answer in (
            ("en", "I implemented nothing and observed no result."),
            ("es", "No implementé nada y no observé ningún resultado."),
        ):
            with self.subTest(locale=locale):
                feedback = feedback_builder.build_private_first_interview_practice_feedback(
                    self._handoff(locale=locale), answer
                )
                self.assertEqual(
                    ["confirm"],
                    [row["label"] for row in feedback.session["feedback"]["observations"]],
                )

    def test_uncertain_action_and_result_are_not_marked_solid(self):
        for locale, answer in (
            ("en", "I think I implemented a change, but I am not sure of the result."),
            ("es", "Creo que implementé un cambio, pero no estoy seguro del resultado."),
        ):
            with self.subTest(locale=locale):
                feedback = feedback_builder.build_private_first_interview_practice_feedback(
                    self._handoff(locale=locale), answer
                )
                self.assertEqual(
                    ["confirm"],
                    [row["label"] for row in feedback.session["feedback"]["observations"]],
                )

    def test_only_exact_awaiting_handoff_is_accepted(self):
        with self.assertRaisesRegex(ValueError, "private first-interview practice feedback is unavailable"):
            feedback_builder.build_private_first_interview_practice_feedback({}, "A bounded answer.")
        handoff = self._handoff()
        session_json, proof_binding = handoff_identity.payload(handoff)
        session = json.loads(session_json)
        session["state"] = "feedback_available"
        forged = handoff_identity.issue_validated_private_first_interview_practice_handoff(
            json.dumps(session, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
            proof_binding,
        )
        with self.assertRaisesRegex(ValueError, "private first-interview practice feedback is unavailable"):
            feedback_builder.build_private_first_interview_practice_feedback(forged, "A bounded answer.")

    def test_unsafe_answer_and_stale_binding_fail_without_echo(self):
        handoff = self._handoff()
        with self.assertRaisesRegex(ValueError, "private first-interview practice feedback is unavailable"):
            feedback_builder.build_private_first_interview_practice_feedback(
                handoff, "Contact me at candidate@example.com to apply for the interview."
            )
        session_json, _ = handoff_identity.payload(handoff)
        forged = handoff_identity.issue_validated_private_first_interview_practice_handoff(
            session_json, "snap-practice-board-sha256-" + "0" * 64
        )
        with self.assertRaisesRegex(ValueError, "private first-interview practice feedback is unavailable"):
            feedback_builder.build_private_first_interview_practice_feedback(forged, "A bounded answer.")

    def test_same_handoff_is_single_use(self):
        handoff = self._handoff()
        feedback_builder.build_private_first_interview_practice_feedback(
            handoff, "I implemented a change and observed a result."
        )
        with self.assertRaisesRegex(ValueError, "private first-interview practice feedback is unavailable"):
            feedback_builder.build_private_first_interview_practice_feedback(
                handoff, "I implemented a different change and observed another result."
            )

    def test_invalid_answer_does_not_consume_handoff(self):
        handoff = self._handoff()
        with self.assertRaisesRegex(ValueError, "private first-interview practice feedback is unavailable"):
            feedback_builder.build_private_first_interview_practice_feedback(handoff, "Contact me at candidate@example.com.")
        feedback = feedback_builder.build_private_first_interview_practice_feedback(
            handoff, "I implemented a change and observed a result."
        )
        self.assertEqual("feedback_available", feedback.session["state"])

    def test_concurrent_calls_allow_exactly_one_feedback_projection(self):
        handoff = self._handoff()
        answers = (
            "I implemented a change and observed a result.",
            "I redesigned the process and improved the outcome.",
        )
        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(
                executor.map(
                    lambda answer: _feedback_result(handoff, answer),
                    answers,
                )
            )
        self.assertEqual([True], [result for result in results if result is True])
        self.assertEqual(1, sum(result is False for result in results))

    def test_feedback_wrapper_schema_is_closed(self):
        feedback = feedback_builder.build_private_first_interview_practice_feedback(
            self._handoff(), "I implemented a change and observed a result."
        )
        session = feedback.session
        wrapper = {
            "feedback_version": "private-first-interview-practice-feedback-v1",
            "feedback_kind": "private_first_interview_practice_feedback",
            "session": session,
            "proof_binding": session["handoff_context"]["source_snapshot"],
        }
        errors = validate_schema_instance(
            wrapper, json.loads(SCHEMA.read_text(encoding="utf-8"))
        )
        self.assertEqual([], errors)

    def test_proof_renderer_accepts_exact_handoff_and_feedback_only(self):
        handoff = self._handoff()
        rendered_handoff = proof_renderer.render_private_first_interview_practice_handoff(handoff)
        self.assertIn("This question came from a private first-interview board", rendered_handoff)
        feedback = feedback_builder.build_private_first_interview_practice_feedback(
            handoff, "I implemented a change and observed a result."
        )
        rendered_feedback = proof_renderer.render_private_first_interview_practice_feedback(feedback)
        self.assertIn("Feedback on the answer", rendered_feedback)

    def test_proof_renderer_rejects_raw_or_mismatched_handoff(self):
        handoff = self._handoff()
        session_json, _ = handoff_identity.payload(handoff)
        forged = handoff_identity.issue_validated_private_first_interview_practice_handoff(
            session_json, "snap-practice-board-sha256-" + "0" * 64
        )
        with self.assertRaisesRegex(ValueError, "private first-interview practice renderer is unavailable"):
            proof_renderer.render_private_first_interview_practice_handoff(forged)
        with self.assertRaisesRegex(ValueError, "private first-interview practice renderer is unavailable"):
            proof_renderer.render_private_first_interview_practice_handoff(handoff.session)


if __name__ == "__main__":
    unittest.main()
