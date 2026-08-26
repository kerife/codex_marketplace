from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = PLUGIN_ROOT / "scripts" / "validate_design_tokens.py"


def load_checker():
    spec = importlib.util.spec_from_file_location("validate_design_tokens", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class DesignTokenContractTests(unittest.TestCase):
    def test_dossier_family_includes_the_v2_extension(self):
        checker = load_checker()

        self.assertIn(
            "assets/executive-career-dossier-v2.css",
            checker.FAMILY_ASSETS["dossier"],
        )

    def test_practice_family_includes_learning_proof_sprint_surface(self):
        checker = load_checker()

        self.assertIn(
            "assets/learning-proof-sprint-v1.css",
            checker.FAMILY_ASSETS["practice_triage"],
        )

    def test_practice_family_includes_private_first_interview_board_surface(self):
        checker = load_checker()

        self.assertIn(
            "assets/private-first-interview-conversion-board-v1.css",
            checker.FAMILY_ASSETS["practice_triage"],
        )

    def test_practice_family_includes_sanitized_private_first_interview_board_v2_surface(self):
        checker = load_checker()

        self.assertIn(
            "assets/private-first-interview-conversion-board-v2.css",
            checker.FAMILY_ASSETS["practice_triage"],
        )

    def test_canonical_assets_pass_their_declared_family_allowlist(self):
        checker = load_checker()

        self.assertEqual([], checker.validate_palette_assets(PLUGIN_ROOT))

    def test_unapproved_color_is_rejected_without_echoing_css(self):
        checker = load_checker()

        errors = checker.validate_css_text(
            ".artifact { color: #123456; }",
            "practice_triage",
            "synthetic.css",
        )

        self.assertEqual(
            ["practice_triage synthetic.css uses unapproved color #123456"],
            errors,
        )

    def test_family_mismatch_is_rejected(self):
        checker = load_checker()

        errors = checker.validate_css_text(
            ".artifact { color: #315bd6; }",
            "practice_triage",
            "synthetic.css",
        )

        self.assertEqual(
            ["practice_triage synthetic.css uses unapproved color #315bd6"],
            errors,
        )

    def test_three_digit_hex_is_normalized_and_declared(self):
        checker = load_checker()

        self.assertEqual([], checker.validate_css_text(".x { color: #fff; }", "compact_receipt", "synthetic.css"))


if __name__ == "__main__":
    unittest.main()
