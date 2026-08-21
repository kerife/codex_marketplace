"""Keep Superdesign raw CSS dumps synchronized with shipped assets."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
THEME = ROOT / ".superdesign" / "init" / "theme.md"
LAYOUTS = ROOT / ".superdesign" / "init" / "layouts.md"
PAGES = ROOT / ".superdesign" / "init" / "pages.md"
ROUTES = ROOT / ".superdesign" / "init" / "routes.md"
COMPONENTS = ROOT / ".superdesign" / "init" / "components.md"
EXTRACTABLE = ROOT / ".superdesign" / "init" / "extractable-components.md"
DESIGN_SYSTEM = ROOT / ".superdesign" / "design-system.md"
ASSETS = ROOT / "plugins" / "professional-growth-coach" / "assets"
ASSET_NAMES = (
    "career-market-learning-dossier-v1.css",
    "executive-career-dossier-v1.css",
    "executive-career-dossier-v2.css",
    "recruiter-practice-session-v1.css",
    "private-recruiter-reply-triage-v1.css",
    "private-recruiter-followthrough-checkpoint-v1.css",
    "private-recruiter-conversion-outcome-v1.css",
)
EXPECTED_THEME_ASSET_NAMES = {
    "career-market-learning-dossier-v1.css",
    "executive-career-dossier-v1.css",
    "executive-career-dossier-v2.css",
    "recruiter-practice-session-v1.css",
    "private-recruiter-reply-triage-v1.css",
    "private-recruiter-followthrough-checkpoint-v1.css",
    "private-recruiter-conversion-outcome-v1.css",
}
HTML_ASSET_NAMES = (
    "executive-career-dossier-v1.html",
    "recruiter-practice-session-v1.html",
    "private-recruiter-reply-triage-v1.html",
    "private-recruiter-followthrough-checkpoint-v1.html",
    "private-recruiter-conversion-outcome-v1.html",
)
EXPECTED_LAYOUT_SOURCES = {
    f"plugins/professional-growth-coach/assets/{name}" for name in HTML_ASSET_NAMES
}


def _theme_asset_names() -> set[str]:
    text = THEME.read_text(encoding="utf-8")
    return set(
        re.findall(
            r"^### `plugins/professional-growth-coach/assets/([^`]+\.css)`$",
            text,
            re.MULTILINE,
        )
    )


def _theme_dump(name: str) -> str:
    text = THEME.read_text(encoding="utf-8")
    heading = f"### `plugins/professional-growth-coach/assets/{name}`"
    start = text.index(heading)
    fence_start = text.index("```css\n", start) + len("```css\n")
    fence_end = text.index("\n```", fence_start)
    return text[fence_start:fence_end] + "\n"


def _layout_sources() -> dict[str, bytes]:
    text = LAYOUTS.read_text(encoding="utf-8")
    sources = re.findall(
        r"^Source: `([^`]+\.html)`$.*?\n```html\n(.*?)\n```",
        text,
        re.MULTILINE | re.DOTALL,
    )
    return {source: (dump + "\n").encode("utf-8") for source, dump in sources}


class SuperdesignThemeAssetParityTests(unittest.TestCase):
    def test_compact_facts_keep_one_column_through_640px(self):
        for name, selector in (
            ("private-recruiter-followthrough-checkpoint-v1.css", ".checkpoint-facts"),
            ("private-recruiter-conversion-outcome-v1.css", ".outcome-facts"),
        ):
            with self.subTest(name=name):
                css = (ASSETS / name).read_text(encoding="utf-8")
                match = re.search(
                    rf"@media \(min-width:\s*([^)]+)\)\s*\{{\s*{re.escape(selector)}\s*\{{\s*grid-template-columns:\s*1fr 1fr;",
                    css,
                )
                self.assertIsNotNone(match)
                breakpoint = match.group(1).strip()
                self.assertEqual(breakpoint, "641px")

    def test_theme_dump_set_covers_every_shipped_css_asset(self):
        self.assertEqual(
            _theme_asset_names(),
            EXPECTED_THEME_ASSET_NAMES,
        )
        self.assertEqual(set(ASSET_NAMES), EXPECTED_THEME_ASSET_NAMES)
        self.assertEqual(
            {path.name for path in ASSETS.glob("*.css")},
            EXPECTED_THEME_ASSET_NAMES,
        )

    def test_private_css_dumps_match_shipped_assets(self):
        for name in ASSET_NAMES:
            with self.subTest(name=name):
                self.assertEqual((ASSETS / name).read_text(encoding="utf-8"), _theme_dump(name))

    def test_private_html_layout_dumps_match_shipped_assets(self):
        layout_sources = _layout_sources()
        self.assertEqual(set(layout_sources), EXPECTED_LAYOUT_SOURCES)
        for source in sorted(EXPECTED_LAYOUT_SOURCES):
            with self.subTest(source=source):
                self.assertEqual((ROOT / source).read_bytes(), layout_sources[source])

    def test_compact_receipt_layouts_keep_employment_boundary_token(self):
        layout_sources = _layout_sources()
        for source in (
            "plugins/professional-growth-coach/assets/private-recruiter-followthrough-checkpoint-v1.html",
            "plugins/professional-growth-coach/assets/private-recruiter-conversion-outcome-v1.html",
        ):
            with self.subTest(source=source):
                self.assertIn(b"{{EMPLOYMENT_BOUNDARY}}", layout_sources[source])

    def test_superdesign_maps_describe_current_v2_composition(self):
        pages = PAGES.read_text(encoding="utf-8")
        routes = ROUTES.read_text(encoding="utf-8")
        components = COMPONENTS.read_text(encoding="utf-8")
        extractable = EXTRACTABLE.read_text(encoding="utf-8")
        self.assertIn("render_executive_career_dossier_v2.py", pages)
        self.assertIn("executive-career-dossier-v2.css", pages)
        self.assertIn("career-market-learning-dossier-v1.schema.json", pages)
        self.assertIn("career-learning-decision-v1.schema.json", pages)
        self.assertIn("career-market-learning-dossier-v2.schema.json", pages)
        self.assertIn("career-learning-decision-v2.schema.json", pages)
        self.assertIn("render_executive_career_dossier_v2.py", routes)
        self.assertIn("DecisionTrace", routes)
        self.assertIn("LearningSignalRoute", routes)
        self.assertIn("CoachPriorityCard and DecisionTrace", components)
        self.assertIn("MarketEvidence and LearningDecision", components)
        self.assertIn("## DecisionTrace", extractable)
        self.assertIn("## LearningDecision", extractable)

    def test_design_system_documents_unavailable_market_safe_next_step(self):
        text = DESIGN_SYSTEM.read_text(encoding="utf-8")
        start = text.index("A validated unavailable")
        paragraph = text[start : text.index("\n\n", start)]
        self.assertRegex(paragraph, r"(?i)safe next step")
        self.assertRegex(paragraph, r"(?i)locali[sz]ed")
        self.assertRegex(paragraph, r"(?i)no external action")

    def test_design_system_documents_learning_boundary_before_cards_and_aria(self):
        text = DESIGN_SYSTEM.read_text(encoding="utf-8")
        self.assertIn(
            "The learning decision boundary appears before the cards, and every learning "
            "card references the shared boundary with `aria-describedby`.",
            " ".join(text.split()),
        )

    def test_design_system_documents_safe_semantic_v2_route_contract(self):
        text = " ".join(DESIGN_SYSTEM.read_text(encoding="utf-8").split())
        for contract in (
            "validated public term label",
            "localized support state",
            "vacancy ordinals",
            "recurrence",
            "no internal IDs",
            "mobile, print, dark, and forced-colors",
        ):
            with self.subTest(contract=contract):
                self.assertIn(contract, text)


if __name__ == "__main__":
    unittest.main()
