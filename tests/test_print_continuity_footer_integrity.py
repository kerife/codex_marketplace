"""Print keeps the employment-continuity footer attached to each artifact."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "plugins" / "professional-growth-coach" / "assets"
FOOTERS = {
    "executive-career-dossier-v1.css": ".footer",
    "recruiter-practice-session-v1.css": ".practice-footer",
    "private-recruiter-reply-triage-v1.css": ".triage-footer",
    "private-recruiter-conversion-outcome-v1.css": ".outcome-footer",
    "private-recruiter-followthrough-checkpoint-v1.css": ".checkpoint-footer",
}


class PrintContinuityFooterIntegrityTests(unittest.TestCase):
    def test_market_print_restores_table_semantics_and_keeps_key_cards_and_recurrence_atomic(self) -> None:
        css = (ASSETS / "career-market-learning-dossier-v1.css").read_text(encoding="utf-8")
        print_css = css[css.index("@media print"):css.index("@media (forced-colors: active)")]
        for contract in (
            ".market-summary-card",
            ".market-vacancy-key",
            ".market-matrix-row",
            ".vacancy-alignment-card",
            ".recurrence-row",
            "display: table-header-group",
            "display: table-row-group",
            "display: table-row",
            "display: table-cell",
            "break-inside: avoid",
            "page-break-inside: avoid",
        ):
            with self.subTest(contract=contract):
                self.assertIn(contract, print_css)
        self.assertRegex(
            print_css,
            r"\.market-vacancy-key\s*\{[^}]*break-after:\s*avoid;[^}]*page-break-after:\s*avoid;",
        )
        for selector in (".market-summary-card", ".market-vacancy-key"):
            with self.subTest(selector=selector):
                self.assertRegex(
                    print_css,
                    rf"{re.escape(selector)}\s*\{{[^}}]*break-inside:\s*avoid;[^}}]*page-break-inside:\s*avoid;",
                )
        self.assertNotRegex(
            print_css,
            r"\.market-matrix-group\s*\{[^}]*break-inside:\s*avoid;",
        )

    def test_dossier_v2_rows_and_coaching_cards_remain_atomic_in_print(self) -> None:
        css = (ASSETS / "executive-career-dossier-v2.css").read_text(encoding="utf-8")
        print_css = css[css.index("@media print"):css.index("@media (forced-colors: active)")]
        for selector in (".section-coverage-row", ".coach-priority-card", ".coach-template", ".market-unavailable-card"):
            with self.subTest(selector=selector):
                self.assertIn(selector, print_css)
        self.assertIn("break-inside: avoid", print_css)
        self.assertIn("page-break-inside: avoid", print_css)
        base_css = (ASSETS / "executive-career-dossier-v1.css").read_text(encoding="utf-8")
        self.assertIn("@page { size: auto; margin: 14mm; }", base_css)

    def test_print_keeps_each_continuity_footer_atomic(self) -> None:
        for name, selector in FOOTERS.items():
            with self.subTest(name=name):
                css = (ASSETS / name).read_text(encoding="utf-8")
                start = css.index("@media print")
                print_css = css[start:]
                next_media = re.search(r"\n@media ", print_css[len("@media print") :])
                if next_media:
                    print_css = print_css[: len("@media print") + next_media.start()]
                footer_rule = re.search(
                    rf"{re.escape(selector)}\s*\{{(?P<rule>[^}}]*)\}}",
                    print_css,
                )
                self.assertIsNotNone(footer_rule, f"missing print footer rule: {name}")
                rule = footer_rule.group("rule")
                self.assertIn("break-inside: avoid", rule)
                self.assertIn("page-break-inside: avoid", rule)


if __name__ == "__main__":
    unittest.main()
