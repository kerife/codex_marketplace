import copy
import hashlib
import json
import re
import sys
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "private-first-interview-conversion-board-v1"
sys.path.insert(0, str(ROOT / "scripts"))
import build_private_first_interview_conversion_board_v1 as builder
import validate_private_first_interview_conversion_board_v1 as validator
import render_private_first_interview_conversion_board_v1 as renderer


class _Parser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
        self.attrs = []
        self.text = []

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)
        self.attrs.append((tag, dict(attrs)))

    def handle_startendtag(self, tag, attrs):
        self.tags.append(tag)
        self.attrs.append((tag, dict(attrs)))

    def handle_data(self, data):
        self.text.append(data)


class PrivateFirstInterviewBoardRendererTests(unittest.TestCase):
    def _proof(self, locale="en"):
        value = json.loads((FIXTURES / f"accepted-{locale}.json").read_text(encoding="utf-8"))
        return validator.validate_private_first_interview_conversion_board_v1(value["source_group"])

    def _render(self, locale="en"):
        return renderer.render_private_first_interview_conversion_board_v1(self._proof(locale))

    def test_renderer_accepts_only_exact_validator_identity(self):
        with self.assertRaises(renderer.PrivateFirstInterviewConversionBoardRenderError):
            renderer.render_private_first_interview_conversion_board_v1(self._proof("en").artifact)

    def test_es_and_en_have_semantic_structure_and_decision_first(self):
        for locale in ("es", "en"):
            with self.subTest(locale=locale):
                output = self._render(locale)
                parsed = _Parser()
                parsed.feed(output)
                self.assertEqual(1, parsed.tags.count("h1"))
                self.assertGreaterEqual(parsed.tags.count("h2"), 5)
                self.assertEqual(1, sum(1 for tag, attrs in parsed.attrs if tag == "main" and attrs.get("id") == "main-content"))
                self.assertIn(("main", {"id": "main-content", "class": "board-shell", "tabindex": "-1"}), parsed.attrs)
                self.assertIn('class="skip-link" href="#main-content"', output)
                self.assertLess(output.index("board-decision"), output.index("board-sequence"))
                self.assertEqual(4, output.count('class="board-branch"'))
                self.assertEqual(7, output.count('class="board-day"'))
                self.assertEqual(7, output.count('class="board-review"'))
                self.assertIn("noindex,nofollow,noarchive", output)
                self.assertIn('name="referrer" content="no-referrer"', output)
                self.assertIn("Content-Security-Policy", output)
                self.assertNotIn("<form", output.lower())
                self.assertNotIn("<button", output.lower())
                self.assertNotIn("<script", output.lower())
                self.assertNotIn("http://", output.lower())
                self.assertNotIn("https://", output.lower())
                self.assertIn("private", output.lower())
                self.assertIn("manual_private_review", output)
                self.assertRegex(output, r"(?i)(message|mensaje).*(schedule|agenda).*(apply|aplica)")

    def test_source_values_are_escaped_and_internal_values_are_not_echoed(self):
        proof = self._proof()
        artifact = proof.artifact
        artifact["week"][0]["private_action"] = "<script>alert('x')</script>"
        rendered = renderer._render_artifact(artifact)
        self.assertNotIn("<script>alert", rendered)
        self.assertIn("&lt;script&gt;alert(&#x27;x&#x27;)&lt;/script&gt;", rendered)
        for secret in (artifact["source_group"]["group_id"], artifact["source_group"]["source_snapshot"]):
            self.assertNotIn(secret, rendered)
        self.assertNotIn("source_group", rendered)
        self.assertNotIn("snapshot", rendered.lower())
        self.assertNotIn("record_id", rendered)

    def test_stop_state_renders_boundary_but_suppresses_detail(self):
        source = copy.deepcopy(self._proof().source_group)
        for name in ("recruiter_outreach_lab", "quality_gate", "first_interview_7_day_plan", "weekly_coach_plan"):
            source[name]["state"] = "stop"
        for check in source["quality_gate"]["checks"]:
            check["state"] = "stop"
        without_snapshot = dict(source)
        without_snapshot.pop("source_snapshot")
        source["source_snapshot"] = "snap-private-first-interview-v1-sha256-" + hashlib.sha256(
            json.dumps(without_snapshot, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        rendered = renderer.render_private_first_interview_conversion_board_v1(validator.validate_private_first_interview_conversion_board_v1(source))
        self.assertIn("board-decision", rendered)
        self.assertIn("board-boundary", rendered)
        self.assertIn("manual_private_review", rendered)
        self.assertIn("message", rendered)
        for section in ("board-sequence", "board-proof", "board-risks", "board-rehearsal", "board-week", "board-ladder", "board-reviews"):
            self.assertNotIn(f'<section class="{section}"', rendered)

    def test_css_has_visual_mode_hooks_and_template_is_closed(self):
        css = (ROOT / "assets" / "private-first-interview-conversion-board-v1.css").read_text(encoding="utf-8")
        for hook in ("@media (max-width: 640px)", "@media print", "prefers-color-scheme: dark", "forced-colors: active", "prefers-reduced-motion: reduce"):
            self.assertIn(hook, css)
        template = (ROOT / "assets" / "private-first-interview-conversion-board-v1.html").read_text(encoding="utf-8")
        self.assertEqual(1, template.count("{{LANG}}"))
        self.assertEqual(1, template.count("{{INLINE_CSS}}"))
        self.assertNotIn("<script", template.lower())
        self.assertNotIn("<form", template.lower())
        self.assertNotRegex(template, r"https?://")


if __name__ == "__main__":
    unittest.main()
