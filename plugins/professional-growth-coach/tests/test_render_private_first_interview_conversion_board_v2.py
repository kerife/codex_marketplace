import copy
import hashlib
import json
import sys
import unittest
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "private-first-interview-conversion-board-v1" / "accepted-en.json"
sys.path.insert(0, str(ROOT / "scripts"))

import build_private_first_interview_conversion_board_v2 as builder
import private_first_interview_source_bundle as source_bundle
import render_private_first_interview_conversion_board_v2 as renderer


class _Parser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
        self.attrs = []

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)
        self.attrs.append((tag, dict(attrs)))


def _source():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))["source_group"]


def _rebind_snapshot(source):
    without_snapshot = dict(source)
    without_snapshot.pop("source_snapshot")
    source["source_snapshot"] = "snap-private-first-interview-v1-sha256-" + hashlib.sha256(
        json.dumps(without_snapshot, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


class PrivateFirstInterviewBoardV2RendererTests(unittest.TestCase):
    def _proof(self, locale="en", source=None):
        bundle = source_bundle.issue_validated_private_first_interview_source_bundle(
            _source() if source is None else source, provenance_state="synthetic_fixture"
        )
        return builder.build_private_first_interview_conversion_board_v2(
            bundle, locale=locale, as_of_date="2026-08-26"
        )

    def test_requires_the_exact_v2_proof(self):
        with self.assertRaisesRegex(renderer.PrivateFirstInterviewConversionBoardV2RenderError, "validated private board is required"):
            renderer.render_private_first_interview_conversion_board_v2(self._proof().artifact)

    def test_semantic_document_has_localized_decision_cockpit_and_trust_strip_before_ladder_and_sequence(self):
        for locale, trust, cockpit, decide_now in (
            ("en", "Synthetic test source", "Decision cockpit", "Decide now"),
            ("es", "Fuente sintética de prueba", "Centro de decisión", "Decide ahora"),
        ):
            with self.subTest(locale=locale):
                output = renderer.render_private_first_interview_conversion_board_v2(self._proof(locale))
                parsed = _Parser()
                parsed.feed(output)
                self.assertEqual(1, parsed.tags.count("h1"))
                self.assertIn(("main", {"id": "main-content", "class": "board-shell", "tabindex": "-1", "aria-labelledby": "board-heading"}), parsed.attrs)
                self.assertIn('class="skip-link" href="#main-content"', output)
                self.assertEqual(1, output.count('class="board-decision board-decision-cockpit"'))
                self.assertIn(cockpit, output)
                self.assertIn(decide_now, output)
                self.assertEqual(1, output.count('class="board-trust-strip"'))
                decision_section = '<section class="board-decision board-decision-cockpit"'
                trust_section = '<section class="board-trust-strip"'
                ladder_section = '<section class="board-ladder"'
                sequence_section = '<section class="board-sequence"'
                self.assertLess(output.index(decision_section), output.index(trust_section))
                self.assertLess(output.index(trust_section), output.index(ladder_section))
                self.assertLess(output.index(trust_section), output.index(sequence_section))
                self.assertLess(output.index(ladder_section), output.index(sequence_section))
                self.assertIn(trust, output)
                self.assertIn("Original text is not stored" if locale == "en" else "Texto original no almacenado", output)
                self.assertIn("Manual review required" if locale == "en" else "Revisión manual requerida", output)
                for forbidden in ("<form", "<button", "<script", "http://", "https://", "source_digest", "source_group", "record_id"):
                    self.assertNotIn(forbidden, output.lower())
                self.assertIn("noindex,nofollow,noarchive", output)
                self.assertIn('name="referrer" content="no-referrer"', output)
                self.assertIn("Content-Security-Policy", output)

    def test_localized_practice_gate_preserves_the_exact_rehearsal_question_without_exposing_enums(self):
        for locale, heading, score_label, score_value, later_request, do_not_share in (
            ("en", "Practice checkpoint", "Score before response", "Undetermined", "Respond only in a later explicit request.", "Do not send, share, or publish this response."),
            ("es", "Punto de práctica", "Puntuación antes de responder", "No determinada", "Responde solo en una solicitud posterior explícita.", "No envíes, compartas ni publiques esta respuesta."),
        ):
            with self.subTest(locale=locale):
                proof = self._proof(locale)
                rehearsal = proof.artifact["rehearsal"]
                output = renderer.render_private_first_interview_conversion_board_v2(proof)
                decision_section = '<section class="board-decision board-decision-cockpit"'
                trust_section = '<section class="board-trust-strip"'
                ladder_section = '<section class="board-ladder"'
                practice_section = '<section class="board-practice-gate"'
                sequence_section = '<section class="board-sequence"'
                self.assertEqual(1, output.count(practice_section))
                self.assertLess(output.index(decision_section), output.index(trust_section))
                self.assertLess(output.index(trust_section), output.index(ladder_section))
                self.assertLess(output.index(ladder_section), output.index(practice_section))
                self.assertLess(output.index(practice_section), output.index(sequence_section))
                self.assertIn(heading, output)
                self.assertIn(rehearsal["question"], output)
                self.assertIn(rehearsal["response_structure"], output)
                self.assertEqual(1, output.count(rehearsal["question"]))
                self.assertEqual(1, output.count(f"<dd>{score_value}</dd>"))
                self.assertIn(f"<dt>{score_label}</dt><dd>{score_value}</dd>", output)
                self.assertIn(later_request, output)
                self.assertIn(do_not_share, output)
                for raw_enum in ("ready", "advance", "clarify", "pause", "stop"):
                    self.assertNotIn(f'<p class="board-state">{raw_enum}</p>', output.lower())
                    self.assertNotIn(f"<h3>{raw_enum}</h3>", output.lower())
                    self.assertNotIn(f"<strong>{raw_enum}</strong>", output.lower())

    def test_ready_board_shows_private_reentry_capsule_but_blocked_states_do_not(self):
        for locale, title, instruction in (
            ("en", "How to continue privately", "Your answer is used once and is not saved."),
            ("es", "Cómo continuar en privado", "La respuesta se usa una sola vez y no se guarda."),
        ):
            with self.subTest(locale=locale):
                ready = self._proof(locale)
                output = renderer.render_private_first_interview_conversion_board_v2(ready)
                self.assertIn('class="board-reentry-capsule"', output)
                self.assertIn(title, output)
                self.assertIn(instruction, output)
                blocked_source = copy.deepcopy(_source())
                blocked_source["first_interview_7_day_plan"]["state"] = "pause"
                _rebind_snapshot(blocked_source)
                blocked = self._proof(locale, source=blocked_source)
                blocked_output = renderer.render_private_first_interview_conversion_board_v2(blocked)
                self.assertNotIn('class="board-reentry-capsule"', blocked_output)

    def test_ready_reentry_capsule_exposes_a_localized_three_step_private_recipe(self):
        for locale, labels in (
            ("en", ("Brief context", "Concrete action", "Observed result")),
            ("es", ("Contexto breve", "Acción concreta", "Resultado observado")),
        ):
            with self.subTest(locale=locale):
                output = renderer.render_private_first_interview_conversion_board_v2(self._proof(locale))
                self.assertIn('class="board-reentry-recipe"', output)
                for label in labels:
                    self.assertIn(label, output)

    def test_localizes_closed_enums_in_visible_board_copy(self):
        expected = {
            "es": {
                "topics": ("Producción", "Compensación", "Elegibilidad", "Disponibilidad", "Confidencialidad"),
                "quality": ("Fuerte", "Mixta", "No determinada"),
                "score": "<dt>Puntuación antes de responder</dt><dd>No determinada</dd>",
                "allowed": "Siguiente paso permitido:</strong> Revisión privada manual",
                "authorization": "Autorización requerida:</strong> Sí",
                "actions": ("Enviar mensaje", "Conectar", "Postularse", "Programar", "Crear evento de calendario", "Publicar", "Compartir", "Subir", "Enviar", "Exportar", "Editar externamente", "Comprar", "Inscribirse"),
            },
            "en": {
                "topics": ("Production", "Compensation", "Eligibility", "Availability", "Confidentiality"),
                "quality": ("Strong", "Mixed", "Undetermined"),
                "score": "<dt>Score before response</dt><dd>Undetermined</dd>",
                "allowed": "Allowed next step:</strong> Manual private review",
                "authorization": "Authorization required:</strong> Yes",
                "actions": ("Send message", "Connect", "Apply", "Schedule", "Create calendar event", "Publish", "Share", "Upload", "Submit", "Export", "Edit externally", "Purchase", "Enroll"),
            },
        }
        for locale, labels in expected.items():
            with self.subTest(locale=locale):
                output = renderer.render_private_first_interview_conversion_board_v2(self._proof(locale))
                for label in labels["topics"] + labels["quality"] + labels["actions"]:
                    self.assertIn(label, output)
                self.assertIn(labels["score"], output)
                self.assertIn(labels["allowed"], output)
                self.assertIn(labels["authorization"], output)
                self.assertNotIn("<h3>production</h3>", output)
                self.assertNotIn("<strong>strong</strong>", output)
                self.assertNotIn("manual_private_review", output)
                self.assertNotIn("calendar_create", output)
                self.assertNotIn("external_edit", output)

    def test_localizes_weak_signal_quality(self):
        for locale, expected in (("es", "Débil"), ("en", "Weak")):
            with self.subTest(locale=locale):
                proof = self._proof(locale)
                artifact = copy.deepcopy(proof.artifact)
                artifact["daily_reviews"][0]["signal_quality"] = "weak"
                output = renderer._render_artifact(artifact)
                self.assertIn(f"· {expected}", output)

    def test_unknown_visible_enum_fails_closed_without_echo(self):
        proof = self._proof()
        artifact = copy.deepcopy(proof.artifact)
        artifact["risk_checks"][0]["topic"] = "untrusted_topic"
        with self.assertRaisesRegex(renderer.PrivateFirstInterviewConversionBoardV2RenderError, "private board artifact is unavailable"):
            renderer._render_artifact(artifact)
        self.assertNotIn("untrusted_topic", renderer._render_artifact(proof.artifact))

    def test_unknown_closed_enum_fields_fail_closed_without_echo(self):
        cases = (
            ("risk_checks", 0, "topic", "unknown_topic"),
            ("daily_reviews", 0, "signal_quality", "unknown_quality"),
            ("rehearsal", None, "pre_response_score", "unknown_score"),
            ("approval_boundary", None, "allowed_next_step", "unknown_step"),
            ("approval_boundary", None, "authorization_required", "unknown_authorization"),
            ("approval_boundary", None, "prohibited_actions", ["unknown_action"]),
        )
        for section, index, field, value in cases:
            with self.subTest(field=field):
                artifact = copy.deepcopy(self._proof().artifact)
                target = artifact[section] if index is None else artifact[section][index]
                target[field] = value
                with self.assertRaisesRegex(renderer.PrivateFirstInterviewConversionBoardV2RenderError, "private board artifact is unavailable"):
                    renderer._render_artifact(artifact)
                self.assertNotIn(str(value), renderer.render_private_first_interview_conversion_board_v2(self._proof()))

    def test_dark_decision_surface_keeps_light_copy_legible(self):
        css = Path(renderer.CSS_PATH).read_text(encoding="utf-8")
        self.assertIn(".board-decision { background: #173e30; }", css)

    def test_long_board_exposes_localized_section_navigation_and_stop_only_safe_destinations(self):
        for locale, nav_label, links in (
            ("es", "Ir a una sección", ("Decisión", "Procedencia", "Escalera", "Práctica", "Secuencia", "Pruebas", "Riesgos", "Plan", "Revisión", "Límite privado")),
            ("en", "Jump to a section", ("Decision", "Provenance", "Ladder", "Practice", "Sequence", "Proof", "Risks", "Plan", "Review", "Private boundary")),
        ):
            with self.subTest(locale=locale):
                output = renderer.render_private_first_interview_conversion_board_v2(self._proof(locale))
                self.assertIn('<nav class="board-section-nav" aria-labelledby="section-nav-label">', output)
                self.assertIn(f'<p id="section-nav-label" class="board-section-nav-label">{nav_label}</p>', output)
                for link in links:
                    self.assertIn(link, output)
                self.assertLess(output.index('<nav class="board-section-nav"'), output.index('<section class="board-ladder"'))

                stop_source = copy.deepcopy(_source())
                for name in ("recruiter_outreach_lab", "quality_gate", "first_interview_7_day_plan", "weekly_coach_plan"):
                    stop_source[name]["state"] = "stop"
                for check in stop_source["quality_gate"]["checks"]:
                    check["state"] = "stop"
                _rebind_snapshot(stop_source)
                stop_output = renderer.render_private_first_interview_conversion_board_v2(self._proof(locale, source=stop_source))
                self.assertIn('href="#decision-heading"', stop_output)
                self.assertIn('href="#trust-heading"', stop_output)
                self.assertIn('href="#approval-heading"', stop_output)
                self.assertNotIn('href="#practice-gate-heading"', stop_output)
                self.assertNotIn('href="#risks-heading"', stop_output)

    def test_section_navigation_covers_every_destination_and_focus_target(self):
        output = renderer.render_private_first_interview_conversion_board_v2(self._proof("en"))
        targets = ("decision-heading", "trust-heading", "ladder-heading", "practice-gate-heading", "sequence-heading", "proof-heading", "risks-heading", "week-heading", "reviews-heading", "approval-heading")
        for target in targets:
            with self.subTest(target=target):
                self.assertIn(f'href="#{target}"', output)
                self.assertIn(f'<h2 id="{target}" tabindex="-1">', output)
        css = Path(renderer.CSS_PATH).read_text(encoding="utf-8")
        self.assertIn("min-height: 44px", css)

    def test_section_navigation_highlights_the_fragment_destination_without_script(self):
        output = renderer.render_private_first_interview_conversion_board_v2(self._proof("en"))
        css = Path(renderer.CSS_PATH).read_text(encoding="utf-8")
        self.assertIn('href="#proof-heading"', output)
        self.assertIn('<h2 id="proof-heading" tabindex="-1">', output)
        self.assertIn("h2:target", css)
        self.assertIn("outline:", css)
        self.assertNotIn("<script", output.lower())

    def test_practice_gate_escapes_rehearsal_copy_and_stop_omits_it(self):
        proof = self._proof()
        artifact = proof.artifact
        artifact["rehearsal"]["question"] = "<script>unsafe()</script>"
        artifact["rehearsal"]["response_structure"] = "<img src=x onerror=unsafe()>"
        rendered = renderer._render_artifact(artifact)
        self.assertNotIn("<script>unsafe", rendered)
        self.assertNotIn("<img src=x", rendered)
        self.assertIn("&lt;script&gt;unsafe()&lt;/script&gt;", rendered)
        self.assertIn("&lt;img src=x onerror=unsafe()&gt;", rendered)

        stop_source = _source()
        for name in ("recruiter_outreach_lab", "quality_gate", "first_interview_7_day_plan", "weekly_coach_plan"):
            stop_source[name]["state"] = "stop"
        for check in stop_source["quality_gate"]["checks"]:
            check["state"] = "stop"
        _rebind_snapshot(stop_source)
        stop_output = renderer.render_private_first_interview_conversion_board_v2(self._proof(source=stop_source))
        self.assertNotIn('<section class="board-practice-gate"', stop_output)

    def test_practice_gate_invites_later_response_only_for_ready_state(self):
        cases = (
            ("ready", "Respond only in a later explicit request."),
            ("clarify", "Clarify before practicing."),
            ("pause", "Practice is paused."),
        )
        for state, expected in cases:
            with self.subTest(state=state):
                proof = self._proof()
                artifact_json, source_json, metadata_json = builder._validator._identity._validation_payload_json(proof)
                artifact = copy.deepcopy(json.loads(artifact_json))
                artifact["decision"][0]["state"] = state
                forged = builder._validator._identity._issue_validated_private_first_interview_conversion_board_v2(
                    json.dumps(artifact, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
                    source_json,
                    metadata_json,
                )
                output = renderer._render_artifact(artifact)
                self.assertIn(f'data-board-state="{state}"', output)
                self.assertIn(expected, output)
                if state != "ready":
                    self.assertNotIn("later explicit request", output)

    def test_composition_only_trust_copy_is_distinct_and_no_provenance_value_leaks(self):
        source = _source()
        source["source_snapshot"] = "snap-private-first-interview-v1-sha256-" + "a" * 64
        # Use an exact v1 adapter to exercise the sole non-fixture trust state.
        import build_private_first_interview_conversion_board_v1 as v1_builder
        v1_source = _source()
        v1_proof = v1_builder.build_private_first_interview_conversion_board_v1(v1_source)
        bundle = source_bundle.adapt_v1_private_first_interview_proof(v1_proof)
        proof = builder.build_private_first_interview_conversion_board_v2(bundle, as_of_date="2026-08-26")
        output = renderer.render_private_first_interview_conversion_board_v2(proof)
        self.assertIn("Composition provenance; review source", output)
        self.assertNotIn(proof.artifact["source_provenance"]["source_digest"], output)
        self.assertNotIn("composition_only", output)

    def test_escapes_visible_values_and_stop_keeps_trust_and_boundary_only(self):
        proof = self._proof()
        artifact = proof.artifact
        artifact["week"][0]["private_action"] = "<script>alert('x')</script>"
        rendered = renderer._render_artifact(artifact)
        self.assertNotIn("<script>alert", rendered)
        self.assertIn("&lt;script&gt;alert(&#x27;x&#x27;)&lt;/script&gt;", rendered)

        stop_source = _source()
        for name in ("recruiter_outreach_lab", "quality_gate", "first_interview_7_day_plan", "weekly_coach_plan"):
            stop_source[name]["state"] = "stop"
        for check in stop_source["quality_gate"]["checks"]:
            check["state"] = "stop"
        _rebind_snapshot(stop_source)
        stop_output = renderer.render_private_first_interview_conversion_board_v2(self._proof(source=stop_source))
        self.assertIn("board-decision", stop_output)
        self.assertIn("board-trust-strip", stop_output)
        self.assertIn("board-approval-boundary", stop_output)
        for section in ("board-sequence", "board-proof", "board-risks", "board-rehearsal", "board-week", "board-ladder", "board-reviews"):
            self.assertNotIn(f'<section class="{section}"', stop_output)

    def test_css_and_template_hold_required_offline_and_accessibility_hooks(self):
        css = (ROOT / "assets" / "private-first-interview-conversion-board-v2.css").read_text(encoding="utf-8")
        for hook in (
            "@media (max-width: 640px)", "@media (min-width: 641px) and (max-width: 900px)",
            "@media print", "prefers-color-scheme: dark", "forced-colors: active",
            "prefers-reduced-motion: reduce", "main:focus-visible", "minmax(",
            ".board-trust-strip", ".board-approval-boundary", "grid-template-columns: 1fr",
            ".board-decision-cockpit", ".board-cockpit-prompt", ".board-practice-gate",
            '[data-board-state="ready"]', '[data-board-state="clarify"]', '[data-board-state="pause"]',
        ):
            self.assertIn(hook, css)
        print_block = css.split("@media print", 1)[1].split("@media (prefers-reduced-motion", 1)[0]
        for token in (
            "--paper: #fff", "--surface: #fff", "--ink: #000", "--muted: #536158",
            "--forest: #000", "--coral: #000", "--gold: #000", "color-scheme: light",
            ".board-cockpit-prompt { background: var(--paper); border-color: var(--line); }",
        ):
            self.assertIn(token, print_block)
        template = (ROOT / "assets" / "private-first-interview-conversion-board-v2.html").read_text(encoding="utf-8")
        for token in ("{{LANG}}", "{{TITLE}}", "{{INLINE_CSS}}", "{{SKIP}}", "{{HEADER}}", "{{MAIN}}", "{{FOOTER}}"):
            self.assertEqual(1, template.count(token))
        self.assertNotIn("<script", template.lower())
        self.assertNotIn("<form", template.lower())
        self.assertNotRegex(template, r"https?://")

    def test_forced_colors_section_links_have_system_focus_indicator(self):
        css = (ROOT / "assets" / "private-first-interview-conversion-board-v2.css").read_text(encoding="utf-8")
        forced_colors_block = css.split("@media (forced-colors: active)", 1)[1]
        self.assertIn(".board-section-nav a:focus-visible", forced_colors_block)
        self.assertIn("outline: 2px solid Highlight", forced_colors_block)
        self.assertIn("outline-offset", forced_colors_block)

    def test_print_keeps_repeated_review_cards_atomic(self):
        css = (ROOT / "assets" / "private-first-interview-conversion-board-v2.css").read_text(encoding="utf-8")
        print_block = css.split("@media print", 1)[1].split("@media (prefers-reduced-motion", 1)[0]
        card_selectors = (
            ".board-sequence li",
            ".board-proof-card",
            ".board-risk-card",
            ".board-day",
            ".board-branch",
            ".board-review",
            ".board-reentry-recipe li",
        )
        for selector in card_selectors:
            with self.subTest(selector=selector):
                self.assertIn(selector, print_block)
        self.assertIn("break-inside: avoid", print_block)
        self.assertIn("page-break-inside: avoid", print_block)


if __name__ == "__main__":
    unittest.main()
