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
        for locale, heading, score_label, later_request, do_not_share in (
            ("en", "Practice checkpoint", "Score before response", "Respond only in a later explicit request.", "Do not send, share, or publish this response."),
            ("es", "Punto de práctica", "Puntuación antes de responder", "Responde solo en una solicitud posterior explícita.", "No envíes, compartas ni publiques esta respuesta."),
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
                self.assertEqual(1, output.count("<dd>unknown</dd>"))
                self.assertIn(f"<dt>{score_label}</dt><dd>unknown</dd>", output)
                self.assertIn(later_request, output)
                self.assertIn(do_not_share, output)
                for raw_enum in ("ready", "advance", "clarify", "pause", "stop"):
                    self.assertNotIn(f'<p class="board-state">{raw_enum}</p>', output.lower())
                    self.assertNotIn(f"<h3>{raw_enum}</h3>", output.lower())
                    self.assertNotIn(f"<strong>{raw_enum}</strong>", output.lower())

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


if __name__ == "__main__":
    unittest.main()
