"""Routing and client-delivery contract for private vacancy packets."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "professional-growth-coach"
SKILLS = PLUGIN / "skills"
ROOT_SKILL = SKILLS / "professional-growth-coach" / "SKILL.md"
ROUTING = SKILLS / "professional-growth-coach" / "references" / "routing.md"
ASSET_SKILL = SKILLS / "optimize-career-assets" / "SKILL.md"
ASSET_WORKFLOW = (
    SKILLS / "optimize-career-assets" / "references" / "asset-workflow.md"
)
README = PLUGIN / "README.md"
STATIC_CHECKER = PLUGIN / "tests" / "run_static_checks.py"
TEXTUAL_ASSET_FIXTURE = ROOT / "tests" / "evals" / "with-skill" / "assets.md"

COMPOSITE_MEMBERS = (
    "eligibility",
    "research",
    "executive_dossier",
    "market_dossier",
    "gap_response",
    "gap_assessment",
    "provider_research",
    "candidate_fact_matrix",
    "source_group",
)
RECEIPT_FIELDS = (
    "artifact_type",
    "schema_version",
    "locale",
    "readiness_state",
    "vacancy_id",
    "output_path",
    "private_draft",
    "external_action_authorized",
)
CLIENT_SECTIONS = (
    "private_packet_summary",
    "readiness_decision",
    "verified_local_artifact",
    "approval_boundary",
)


def section(document: str, heading: str) -> str:
    try:
        return document.split(heading, 1)[1].split("\n## ", 1)[0]
    except IndexError as error:
        raise AssertionError(f"missing contract section: {heading}") from error


def exact_fenced_lines(document: str, marker: str) -> tuple[str, ...]:
    try:
        remainder = document.split(marker, 1)[1]
        fenced = remainder.split("```text\n", 1)[1].split("\n```", 1)[0]
    except IndexError as error:
        raise AssertionError(f"missing exact fenced contract after: {marker}") from error
    return tuple(line for line in fenced.splitlines() if line)


def load_static_checker():
    specification = importlib.util.spec_from_file_location(
        "private_packet_routing_static_checks", STATIC_CHECKER
    )
    if specification is None or specification.loader is None:
        raise AssertionError("static checker is unavailable")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


class PrivateVacancyApplicationPacketRoutingTests(unittest.TestCase):
    def test_packet_route_preserves_recruiter_precedence_and_eligibility_authority(self) -> None:
        """Break caught: packet routing bypasses recruiter routes or trusts a second selector."""

        routing = ROUTING.read_text(encoding="utf-8")
        packet = section(routing, "## Private vacancy application packet routing")
        headings = (
            "## Private recruiter-practice routing",
            "## Private recruiter-reply triage routing",
            "## Private vacancy application packet routing",
        )

        positions = tuple(routing.index(heading) for heading in headings)
        self.assertEqual(tuple(sorted(positions)), positions)
        self.assertIn("ordinary recruiter-reply", packet)
        self.assertIn("remain higher-precedence", packet)
        self.assertIn("`prepare_private_vacancy_packet`", packet)
        self.assertIn("recompute", packet.casefold())
        self.assertIn("`optimize-career-assets`", packet)
        self.assertIn("no second vacancy selector", packet.casefold())

    def test_packet_route_requires_the_complete_composite_without_fallback(self) -> None:
        """Break caught: routing requires a caller packet or falls through on missing evidence."""

        routing = ROUTING.read_text(encoding="utf-8")
        packet = section(routing, "## Private vacancy application packet routing")

        for member in COMPOSITE_MEMBERS:
            with self.subTest(member=member):
                self.assertIn(f"`{member}`", packet)
        self.assertNotIn("Require one supplied packet JSON", packet)
        self.assertIn("require no caller-supplied packet JSON", packet)
        self.assertIn(
            "`build_validated_private_vacancy_application_packet_v1`", packet
        )
        self.assertIn("only the missing identity-free private evidence", packet)
        self.assertIn("do not fall through", packet.casefold())
        self.assertIn("no packet", packet.casefold())
        self.assertIn("no external action", packet.casefold())

    def test_execution_proof_uses_one_source_group_and_exact_writer_receipts(self) -> None:
        """Break caught: JSON, HTML, or receipt can come from crossed source captures."""

        workflow = ASSET_WORKFLOW.read_text(encoding="utf-8")
        exact_flow = exact_fenced_lines(
            workflow, "The exact one-capture in-process workflow is:"
        )
        self.assertEqual(
            (
                "validated_packet = build_validated_private_vacancy_application_packet_v1(complete_source_group)",
                "json_receipt = write_private_vacancy_application_packet_v1(validated_packet, private_json_output)",
                "html_receipt = write_private_vacancy_application_packet_html_v1(validated_packet, private_html_output)",
            ),
            exact_flow,
        )
        self.assertNotIn("<packet-json>", workflow)
        self.assertIn("captures the complete composite exactly once", workflow)
        self.assertIn("same opaque validated snapshot", workflow)
        self.assertIn("same captured composite source group", workflow)
        self.assertIn(
            "validated packet JSON, rendered HTML, and their exact receipts",
            workflow,
        )
        self.assertEqual(
            RECEIPT_FIELDS,
            exact_fenced_lines(
                workflow,
                "Each successful writer returns a receipt containing exactly:",
            ),
        )
        self.assertIn("`private_draft=true`", workflow)
        self.assertIn("`external_action_authorized=false`", workflow)
        self.assertIn("a mismatch is not execution proof", workflow.casefold())

    def test_client_delivery_has_only_four_identity_free_sections_and_localized_end(self) -> None:
        """Break caught: the private artifact chat leaks internal contract material."""

        routing = ROUTING.read_text(encoding="utf-8")
        packet = section(routing, "## Private vacancy application packet routing")
        self.assertEqual(
            CLIENT_SECTIONS,
            exact_fenced_lines(packet, "The client delivery contains exactly:"),
        )
        self.assertIn("verified absolute local Markdown link", packet)
        self.assertIn("No se realiza ninguna acción externa.", packet)
        self.assertIn("No external action is performed.", packet)
        for forbidden in (
            "`candidate_id`",
            "router contract",
            "`module_execution_packet`",
            "internal fact IDs",
            "source IDs",
            "snapshot IDs",
            "source bindings",
            "raw source prose",
            "receipt JSON",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertIn(forbidden, packet)
        self.assertIn("include none of", packet.casefold())

    def test_versioned_asset_contract_replaces_identity_bearing_prose_packet(self) -> None:
        """Break caught: asset coaching hand-authors the retired identity-bearing packet."""

        skill = ASSET_SKILL.read_text(encoding="utf-8")
        workflow = ASSET_WORKFLOW.read_text(encoding="utf-8")
        combined = f"{skill}\n{workflow}"
        self.assertIn("private-vacancy-application-packet-v1.schema.json", combined)
        self.assertIn("candidate-fact-matrix-v1.schema.json", combined)
        self.assertIn("eligibility remains the sole", combined.casefold())
        self.assertIn("legacy textual `application_claim_review_matrix`", combined)
        self.assertNotIn(
            "Include `candidate_id`, `target_vacancy_id`, `packet_goal`",
            skill,
        )

        checker = load_static_checker()
        raw_output = TEXTUAL_ASSET_FIXTURE.read_text(encoding="utf-8")
        self.assertEqual(
            [], checker.validate_application_claim_review_matrix_quality(raw_output)
        )

    def test_readme_lists_private_packet_entry_points_without_authorization(self) -> None:
        """Break caught: users cannot find the versioned private packet workflow safely."""

        readme = README.read_text(encoding="utf-8")
        for entry_point in (
            "candidate-fact-matrix-v1.schema.json",
            "private-vacancy-application-packet-v1.schema.json",
            "build_private_vacancy_application_packet_v1.py",
            "validate_private_vacancy_application_packet_v1.py",
            "build_validated_private_vacancy_application_packet_v1",
            "write_private_vacancy_application_packet_v1.py",
            "render_private_vacancy_application_packet_v1.py",
        ):
            with self.subTest(entry_point=entry_point):
                self.assertIn(entry_point, readme)
        normalized_readme = " ".join(readme.casefold().split())
        self.assertIn("does not authorize an application", normalized_readme)
        self.assertIn("No external action is performed.", readme)


if __name__ == "__main__":
    unittest.main()
