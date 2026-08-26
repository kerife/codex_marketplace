import copy
import importlib.util
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "render_recruiter_practice_session.py"
spec = importlib.util.spec_from_file_location("practice_renderer", SCRIPT)
renderer = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = renderer
spec.loader.exec_module(renderer)

VALIDATOR_SCRIPT = ROOT / "scripts" / "validate_recruiter_practice_session.py"
validator_spec = importlib.util.spec_from_file_location("practice_validator", VALIDATOR_SCRIPT)
validator = importlib.util.module_from_spec(validator_spec)
assert validator_spec.loader is not None
sys.modules[validator_spec.name] = validator
validator_spec.loader.exec_module(validator)


class RecruiterPracticeRendererTests(unittest.TestCase):
    def test_invalid_utf8_input_is_reported_without_traceback(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.json"
            path.write_bytes(b"\xff")

            result = subprocess.run(
                [sys.executable, "-B", str(VALIDATOR_SCRIPT), str(path)],
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.returncode, 3)
        self.assertEqual(result.stderr, "session input is not valid JSON\n")
        self.assertNotIn("Traceback", result.stderr)

    def _feedback_session(self, observations):
        return {
            "schema_version": "recruiter-practice-session-v1",
            "session_kind": "private_recruiter_practice",
            "locale": "es",
            "state": "feedback_available",
            "safe_context": {"stage": "recruiter_screen", "vacancy_state": "safe_summary_provided", "summary": "Contexto"},
            "requirement": {"id": "R-001", "summary": "Liderazgo", "fact_ids": ["F-001"]},
            "question": {"id": "Q-001", "kind": "proof_example", "text": "¿Cómo lo hiciste?", "requirement_id": "R-001", "fact_ids": ["F-001"]},
            "facts": [{"id": "F-001", "state": "verified", "summary": "Resultado confirmado"}],
            "observed_answer": {"id": "OBS-001", "text": "Hice la acción y observé el resultado.", "storage": "ephemeral"},
            "rubric": {"id": "RB-001", "criterion": "Conecta acción y resultado observado."},
            "feedback": {"score": "unknown", "score_state": "categorical", "observations": observations},
            "delivery": {"draft_only": True, "external_actions_authorized": False, "local_save_mode": "disabled", "raw_answer_retained": False},
        }

    def _observation(self, label):
        return {"label": label, "statement": "Observación acotada.", "source_refs": ["OBS-001", "RB-001"]}

    def test_feedback_taxonomy_accepts_canonical_order(self):
        session = self._feedback_session([self._observation(label) for label in ("solid", "confirm", "do_not_assert")])
        self.assertEqual(validator.validate_session(session), [])

    def test_feedback_taxonomy_rejects_duplicate_or_reversed_labels(self):
        duplicate = self._feedback_session([self._observation(label) for label in ("solid", "solid")])
        reversed_order = self._feedback_session([self._observation(label) for label in ("confirm", "solid")])
        self.assertTrue(any("must be unique" in error for error in validator.validate_session(duplicate)))
        self.assertTrue(any("canonical order" in error for error in validator.validate_session(reversed_order)))

    def test_feedback_renderer_uses_closed_kind_aware_copy_without_private_prose(self):
        for locale in ("es", "en"):
            for kind in renderer.QUESTION_KINDS:
                for label in renderer.FEEDBACK_LABELS:
                    session = self._feedback_session([
                        {**self._observation(label), "statement": "PRIVATE-FEEDBACK-SENTINEL"},
                    ])
                    session["locale"] = locale
                    session["question"]["kind"] = kind
                    session["facts"][0]["state"] = (
                        "verified" if kind == "proof_example" else "candidate_reported"
                    )
                    with self.subTest(locale=locale, kind=kind, label=label):
                        rendered = renderer.render_session_html(session)
                        feedback = rendered.split(
                            '<section class="practice-feedback"', 1
                        )[1].split("</section>", 1)[0]
                        self.assertIn(
                            renderer._feedback_description(locale, kind, label), feedback
                        )
                        self.assertNotIn("PRIVATE-FEEDBACK-SENTINEL", rendered)

    def test_mixed_feedback_labels_render_decision_after_feedback_without_private_ids(self):
        session = self._feedback_session([
            self._observation(label)
            for label in ("solid", "confirm", "do_not_assert")
        ])
        rendered = renderer.render_session_html(session)
        self.assertLess(
            rendered.index('<section class="practice-feedback"'),
            rendered.index('<section class="practice-decision"'),
        )
        self.assertLess(
            rendered.index('<section class="practice-decision"'),
            rendered.index('<section class="practice-evidence"'),
        )
        self.assertEqual(rendered.count("<dt>"), 3)
        self.assertEqual(rendered.count("<dd>"), 3)
        decision = rendered.split('<section class="practice-decision"', 1)[1].split(
            "</section>", 1
        )[0]
        self.assertIn("No afirmar todavía", decision)
        self.assertIn(renderer._decision_action("es", "do_not_assert"), decision)
        self.assertNotIn(renderer._decision_action("es", "solid"), decision)
        self.assertNotIn(renderer._decision_action("es", "confirm"), decision)
        self.assertNotIn("practice-next-action--feedback_available", rendered)
        self.assertEqual(rendered.count("href="), 1)
        self.assertNotRegex(rendered, r"\b(?:Q|R|F|C|E|OBS|RB)-\d{3}\b")

    def test_decision_field_labels_are_exact_in_both_locales(self):
        expected_labels = {
            "es": (
                "Señal prioritaria",
                "Objetivo de esta respuesta",
                "Decisión antes de volver a practicar",
            ),
            "en": (
                "Governing feedback",
                "Target for this answer",
                "Decision before rehearsing again",
            ),
        }
        for locale, labels in expected_labels.items():
            session = self._feedback_session([self._observation("solid")])
            session["locale"] = locale
            with self.subTest(locale=locale):
                rendered = renderer.render_session_html(session)
                decision = rendered.split(
                    '<section class="practice-decision"', 1
                )[1].split("</section>", 1)[0]
                self.assertEqual(re.findall(r"<dt>([^<]+)</dt>", decision), list(labels))

    def test_question_kind_is_closed_and_required(self):
        session = self._feedback_session([])
        session["state"] = "awaiting_answer"
        session["observed_answer"] = None
        session["feedback"] = {"score": "unknown", "score_state": "unknown", "observations": []}
        session["question"]["kind"] = "free_form"
        errors = validator.validate_session(session)
        self.assertTrue(any("question.kind" in error for error in errors))

    def test_question_kind_requires_semantically_matching_fact_state(self):
        session = self._feedback_session([])
        session["state"] = "awaiting_answer"
        session["observed_answer"] = None
        session["feedback"] = {"score": "unknown", "score_state": "unknown", "observations": []}
        session["question"]["kind"] = "proof_example"
        session["facts"][0]["state"] = "candidate_reported"
        errors = validator.validate_session(session)
        self.assertTrue(any("proof_example requires verified fact" in error for error in errors))

        session["question"]["kind"] = "eligibility_boundary"
        session["facts"][0]["state"] = "verified"
        errors = validator.validate_session(session)
        self.assertFalse(any("eligibility_boundary requires" in error for error in errors))

    def test_prompt_includes_rehearsal_scaffold_for_first_screen_answer(self):
        session = {
            "schema_version": "recruiter-practice-session-v1",
            "session_kind": "private_recruiter_practice",
            "locale": "es",
            "state": "awaiting_answer",
            "safe_context": {"stage": "recruiter_screen", "vacancy_state": "safe_summary_provided", "summary": "Contexto"},
            "requirement": {"id": "R-001", "summary": "Liderazgo", "fact_ids": ["F-001"]},
            "question": {"id": "Q-001", "kind": "proof_example", "text": "¿Cómo lo hiciste?", "requirement_id": "R-001", "fact_ids": ["F-001"]},
            "facts": [{"id": "F-001", "state": "verified", "summary": "Resultado confirmado"}],
            "observed_answer": None,
            "rubric": {"id": "RB-001", "criterion": "Conecta acción y resultado observado."},
            "feedback": {"score": "unknown", "score_state": "unknown", "observations": []},
            "delivery": {"draft_only": True, "external_actions_authorized": False, "local_save_mode": "disabled", "raw_answer_retained": False},
        }
        rendered = renderer.render_session_html(session)
        self.assertIn("Propósito de la pregunta", rendered)
        self.assertIn("Presenta una evidencia confirmada", rendered)
        self.assertIn("Estructura de respuesta", rendered)
        self.assertIn("Contexto de la evidencia", rendered)
        self.assertIn("Acción técnica concreta", rendered)
        self.assertIn("Impacto observado directo", rendered)
        self.assertNotIn("Contexto breve", rendered)
        self.assertIn('class="practice-rehearsal-hint"', rendered)

        self.assertIn('aria-labelledby="rehearsal-title"', rendered)
        self.assertIn("Siguiente paso", rendered)
        self.assertIn("Responde con contexto breve, acción concreta y resultado observado", rendered)
        self.assertIn("No se guarda tu respuesta", rendered)

        expected_steps = {
            "screen_opening": "Puente a la conversación",
            "proof_example": "Impacto observado directo",
            "eligibility_boundary": "Pregunta abierta",
            "compensation_boundary": "Pregunta de compensación",
            "missing_detail": "Detalle faltante",
        }
        for kind, expected_step in expected_steps.items():
            candidate = copy.deepcopy(session)
            candidate["question"]["kind"] = kind
            with self.subTest(kind=kind):
                self.assertIn(expected_step, renderer.render_session_html(candidate))

        sourced = copy.deepcopy(session)
        sourced["handoff_context"] = {
            "source": "executive_career_dossier",
            "source_snapshot": "snap-dossier-sha256-873fb8cf4957d72c0aa06a15b253716a3d0397d45997073adb0b8e486decfa25",
            "question_rank": 1,
            "question_id": "Q-001",
            "requirement_id": "R-001",
            "fact_ids": ["F-001"],
            "claim_ids": ["C-001"],
            "evidence_ids": ["E-001"],
            "draft_only": True,
            "external_actions_authorized": False,
        }
        sourced_html = renderer.render_session_html(sourced)
        self.assertLess(
            sourced_html.index('<section class="practice-next-action'),
            sourced_html.index('<section class="practice-rehearsal"'),
        )
        self.assertIn("Lista para responder", sourced_html)
        self.assertIn(
            "Regresa a la conversación privada de Codex que originó esta práctica",
            sourced_html,
        )

    def test_progress_track_marks_the_current_practice_step(self):
        expected_current = {
            "ready_to_practice": "prepare",
            "awaiting_answer": "answer",
            "feedback_available": "review",
        }
        for state, current in expected_current.items():
            session = self._feedback_session(
                [self._observation("solid")]
                if state == "feedback_available"
                else []
            )
            session["locale"] = "en"
            session["state"] = state
            if state != "feedback_available":
                session["observed_answer"] = None
                session["feedback"] = {
                    "score": "unknown",
                    "score_state": "unknown",
                    "observations": [],
                }
            rendered = renderer.render_session_html(session)
            progress = rendered.split('<nav class="practice-progress"', 1)[1].split("</nav>", 1)[0]
            self.assertEqual(1, progress.count('aria-current="step"'))
            self.assertIn(f'data-step="{current}" aria-current="step"', progress)
            self.assertIn('aria-label="Practice progress"', rendered)

    def test_awaiting_answer_shows_private_reentry_capsule_only_before_final_feedback(self):
        awaiting = self._feedback_session([])
        awaiting["state"] = "awaiting_answer"
        awaiting["observed_answer"] = None
        awaiting["feedback"] = {"score": "unknown", "score_state": "unknown", "observations": []}
        awaiting["handoff_context"] = {
            "source": "executive_career_dossier",
            "source_snapshot": "snap-dossier-sha256-" + "a" * 64,
            "question_rank": 1,
            "question_id": "Q-001",
            "requirement_id": "R-001",
            "fact_ids": ["F-001"],
            "claim_ids": ["C-001"],
            "evidence_ids": ["E-001"],
            "draft_only": True,
            "external_actions_authorized": False,
        }
        rendered = renderer.render_session_html(awaiting)
        self.assertIn('class="practice-reentry-capsule"', rendered)
        self.assertIn("responde con contexto breve, acción concreta y resultado observado", rendered)
        independent = copy.deepcopy(awaiting)
        independent.pop("handoff_context")
        self.assertNotIn('class="practice-reentry-capsule"', renderer.render_session_html(independent))
        final = copy.deepcopy(awaiting)
        final["schema_version"] = "recruiter-practice-session-v2"
        final["ui_locale"] = "en"
        final["content_locale"] = "en"
        final.pop("locale")
        final["handoff_context"]["source"] = "private_first_interview_conversion_board"
        final["handoff_context"]["source_snapshot"] = "snap-practice-board-sha256-" + "b" * 64
        final["handoff_context"].pop("claim_ids")
        final["handoff_context"].pop("evidence_ids")
        final["handoff_context"]["attempt"] = 2
        final["handoff_context"]["final_attempt"] = True
        self.assertNotIn('class="practice-reentry-capsule"', renderer.render_session_html(final))

    def test_next_action_forced_colors_uses_explicit_system_color_surface_in_both_locales(self):
        session = {
            "schema_version": "recruiter-practice-session-v1",
            "session_kind": "private_recruiter_practice",
            "locale": "es",
            "state": "awaiting_answer",
            "safe_context": {"stage": "recruiter_screen", "vacancy_state": "safe_summary_provided", "summary": "Contexto"},
            "requirement": {"id": "R-001", "summary": "Liderazgo", "fact_ids": ["F-001"]},
            "question": {"id": "Q-001", "kind": "proof_example", "text": "¿Cómo lo hiciste?", "requirement_id": "R-001", "fact_ids": ["F-001"]},
            "facts": [{"id": "F-001", "state": "verified", "summary": "Resultado confirmado"}],
            "observed_answer": None,
            "rubric": {"id": "RB-001", "criterion": "Conecta acción y resultado observado."},
            "feedback": {"score": "unknown", "score_state": "unknown", "observations": []},
            "delivery": {"draft_only": True, "external_actions_authorized": False, "local_save_mode": "disabled", "raw_answer_retained": False},
        }
        expected_heading = {"es": "Siguiente paso", "en": "Next step"}
        for locale, heading in expected_heading.items():
            localized = copy.deepcopy(session)
            localized["locale"] = locale
            with self.subTest(locale=locale):
                rendered = renderer.render_session_html(localized)
                self.assertIn(heading, rendered)
                self.assertRegex(
                    rendered,
                    r"(?s)@media \(forced-colors: active\).*?\.recruiter-practice-document \.practice-next-action \{[^}]*background: Canvas;[^}]*color: CanvasText;[^}]*border-color: CanvasText;",
                )
                self.assertRegex(
                    rendered,
                    r"(?s)@media \(forced-colors: active\).*?\.recruiter-practice-document \.practice-next-action h2 \{[^}]*color: CanvasText;",
                )
                self.assertRegex(
                    rendered,
                    r"(?s)@media \(forced-colors: active\).*?\.recruiter-practice-document \.practice-next-action--ready_to_practice,\s+\.recruiter-practice-document \.practice-next-action--awaiting_answer \{[^}]*border-left-color: CanvasText;",
                )

    def test_sourced_session_hides_provenance_and_raw_answer_material(self):
        sourced = self._feedback_session([self._observation("confirm")])
        sourced["observed_answer"]["text"] = "SOURCE-RAW-ANSWER-SENTINEL"
        sourced["feedback"]["observations"][0]["statement"] = "SOURCE-RAW-FEEDBACK-SENTINEL"
        sourced["handoff_context"] = {
            "source": "executive_career_dossier",
            "source_snapshot": "snap-dossier-sha256-873fb8cf4957d72c0aa06a15b253716a3d0397d45997073adb0b8e486decfa25",
            "question_rank": 1,
            "question_id": "Q-001",
            "requirement_id": "R-001",
            "fact_ids": ["F-001"],
            "claim_ids": ["C-001"],
            "evidence_ids": ["E-001"],
            "draft_only": True,
            "external_actions_authorized": False,
        }

        rendered = renderer.render_session_html(sourced)

        for omitted in (
            "snap-dossier-sha256-873fb8cf4957d72c0aa06a15b253716a3d0397d45997073adb0b8e486decfa25",
            "Q-001",
            "R-001",
            "F-001",
            "C-001",
            "E-001",
            "OBS-001",
            "RB-001",
            "SOURCE-RAW-ANSWER-SENTINEL",
            "SOURCE-RAW-FEEDBACK-SENTINEL",
        ):
            with self.subTest(omitted=omitted):
                self.assertNotIn(omitted, rendered)

    def test_sourced_practice_prioritizes_next_step_before_origin_receipt(self):
        session = self._feedback_session([])
        session["schema_version"] = "recruiter-practice-session-v2"
        session["ui_locale"] = "en"
        session["content_locale"] = "en"
        session.pop("locale")
        session["state"] = "awaiting_answer"
        session["observed_answer"] = None
        session["feedback"] = {"score": "unknown", "score_state": "unknown", "observations": []}
        session["handoff_context"] = {
            "source": "private_first_interview_conversion_board",
            "source_snapshot": "snap-practice-board-sha256-" + "1" * 64,
            "question_rank": 1,
            "question_id": "Q-001",
            "requirement_id": "R-001",
            "fact_ids": ["F-001"],
            "draft_only": True,
            "external_actions_authorized": False,
        }
        rendered = renderer.render_session_html(session)
        self.assertLess(
            rendered.index('<section class="practice-next-action'),
            rendered.index('<aside class="practice-handoff'),
        )
        self.assertLess(
            rendered.index('<section class="practice-rehearsal'),
            rendered.index('<aside class="practice-handoff'),
        )

    def test_sourced_feedback_keeps_origin_receipt_after_review(self):
        session = self._feedback_session([self._observation("solid")])
        session["schema_version"] = "recruiter-practice-session-v2"
        session["ui_locale"] = "en"
        session["content_locale"] = "en"
        session.pop("locale")
        session["handoff_context"] = {
            "source": "private_first_interview_conversion_board",
            "source_snapshot": "snap-practice-board-sha256-" + "2" * 64,
            "question_rank": 1,
            "question_id": "Q-001",
            "requirement_id": "R-001",
            "fact_ids": ["F-001"],
            "draft_only": True,
            "external_actions_authorized": False,
        }
        rendered = renderer.render_session_html(session)
        self.assertLess(
            rendered.index('<section class="practice-feedback'),
            rendered.index('<aside class="practice-handoff'),
        )
        self.assertLess(
            rendered.index('<section class="practice-decision'),
            rendered.index('<aside class="practice-handoff'),
        )

    def test_employment_continuity_boundary_is_visible_for_every_practice_state(self):
        expected = {
            "en": "This analysis evaluates professional options; it does not recommend resigning, leaving a job, or stopping your job search; you decide what comes next.",
            "es": "Este análisis evalúa opciones profesionales; no recomienda renunciar, dejar un empleo ni abandonar tu búsqueda; tú decides qué sigue.",
        }
        for locale in ("en", "es"):
            for state in ("ready_to_practice", "awaiting_answer", "feedback_available"):
                session = self._feedback_session(
                    [self._observation("solid"), self._observation("confirm"), self._observation("do_not_assert")]
                )
                session["locale"] = locale
                session["state"] = state
                if state != "feedback_available":
                    session["observed_answer"] = None
                    session["feedback"] = {
                        "score": "unknown",
                        "score_state": "unknown",
                        "observations": [],
                    }
                with self.subTest(locale=locale, state=state):
                    rendered = renderer.render_session_html(session)
                    self.assertEqual(rendered.count(expected[locale]), 1)
                    self.assertIn('class="practice-footer practice-shell"', rendered)
                    self.assertNotIn("no-print", rendered.split("practice-footer", 1)[1])


if __name__ == "__main__":
    unittest.main()
