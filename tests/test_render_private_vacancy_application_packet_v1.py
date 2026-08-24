"""Behavioral tests for the private vacancy application packet renderer."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import io
import json
import os
import re
import stat
import sys
import tempfile
import unittest
from collections.abc import Iterator, Mapping
from contextlib import redirect_stderr, redirect_stdout
from html.parser import HTMLParser
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "professional-growth-coach"
SCRIPTS = PLUGIN / "scripts"
ASSETS = PLUGIN / "assets"
FIXTURES = (
    ROOT
    / "tests"
    / "evals"
    / "with-skill"
    / "fixtures"
    / "private-vacancy-application-packet-v1"
)
SCENARIOS = (
    "ready-es",
    "ready-en",
    "revise-missing-es",
    "revise-review-en",
    "stop-constraint-es",
    "stop-constraint-en",
)


def load_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError("fixture root must be an object")
    return value


def load_module(path: Path, namespace: str):
    specification = importlib.util.spec_from_file_location(namespace, path)
    if specification is None or specification.loader is None:
        raise AssertionError(f"module is unavailable: {path.name}")
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


class OnePassMapping(Mapping[str, object]):
    """Permit one snapshot traversal and reject all later caller-object reads."""

    def __init__(self, value: Mapping[str, object], marker: str) -> None:
        self._value = dict(value)
        self.marker = marker
        self.items_calls = 0

    def items(self):
        self.items_calls += 1
        if self.items_calls != 1:
            raise RuntimeError(self.marker)
        return self._value.items()

    def __getitem__(self, key: str) -> object:
        raise RuntimeError(self.marker)

    def __iter__(self) -> Iterator[str]:
        raise RuntimeError(self.marker)

    def __len__(self) -> int:
        raise RuntimeError(self.marker)

    def get(self, key: str, default: object = None) -> object:
        raise RuntimeError(self.marker)

    def __deepcopy__(self, memo: object) -> object:
        raise RuntimeError(self.marker)

    def __str__(self) -> str:
        raise RuntimeError(self.marker)


class PacketDOMAudit(HTMLParser):
    """Collect structural HTML facts without depending on a browser library."""

    def __init__(self) -> None:
        super().__init__()
        self.ids: list[str] = []
        self.references: list[str] = []
        self.start_tags: list[tuple[str, dict[str, str | None]]] = []
        self.tag_counts: dict[str, int] = {}
        self.table_captions = 0
        self.table_heads = 0
        self.header_scopes: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        self.start_tags.append((tag, values))
        self.tag_counts[tag] = self.tag_counts.get(tag, 0) + 1
        identifier = values.get("id")
        if identifier:
            self.ids.append(identifier)
        for field in ("aria-labelledby", "aria-describedby"):
            references = values.get(field)
            if references:
                self.references.extend(references.split())
        if tag == "caption":
            self.table_captions += 1
        elif tag == "thead":
            self.table_heads += 1
        elif tag == "th" and values.get("scope"):
            self.header_scopes.append(str(values["scope"]))


class PrivateVacancyApplicationPacketRendererTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.validator = load_module(
            SCRIPTS / "validate_private_vacancy_application_packet_v1.py",
            "private_packet_renderer_test_validator",
        )
        cls.writer = load_module(
            SCRIPTS / "write_private_vacancy_application_packet_v1.py",
            "private_packet_renderer_test_writer",
        )
        cls.renderer = load_module(
            SCRIPTS / "render_private_vacancy_application_packet_v1.py",
            "private_packet_renderer_under_test",
        )
        cls.artifacts = {
            scenario: load_json(FIXTURES / scenario / "application-packet.json")
            for scenario in SCENARIOS
        }
        cls.sources = {
            scenario: load_json(FIXTURES / scenario / "sources.json")
            for scenario in SCENARIOS
        }
        cls.snapshots = {
            scenario: cls.validator.validate_private_vacancy_application_packet_v1(
                cls.artifacts[scenario], cls.sources[scenario]
            )
            for scenario in SCENARIOS
        }

    def test_renderer_accepts_only_the_same_package_opaque_snapshot_before_asset_reads(self) -> None:
        """Break caught: artifact mappings or a different package root bypass full validation."""
        snapshot = self.snapshots["ready-en"]
        self.assertIs(
            type(snapshot),
            self.renderer.ValidatedPrivateVacancyPacket,
        )
        rendered = self.renderer.render_private_vacancy_application_packet_v1(snapshot)
        self.assertIsInstance(rendered, str)

        marker = "review-sensitive-artifact-only-bypass"
        with patch.object(
            self.renderer.ASSET_LOADER,
            "read_private_asset",
            side_effect=RuntimeError(marker),
        ) as asset_read:
            for forged in (self.artifacts["ready-en"], {"artifact": marker}):
                with self.subTest(forged_type=type(forged).__name__):
                    with self.assertRaises(
                        self.renderer.PrivateVacancyApplicationPacketRenderError
                    ) as caught:
                        self.renderer.render_private_vacancy_application_packet_v1(forged)
                    self.assertEqual(
                        "cannot render private vacancy application packet",
                        str(caught.exception),
                    )
                    self.assertNotIn(marker, str(caught.exception))
        asset_read.assert_not_called()

    def test_ready_dom_has_exact_landmarks_aria_lists_definition_lists_and_claim_table(self) -> None:
        """Break caught: the ready document loses its semantic hierarchy or stable references."""
        document = self.renderer.render_private_vacancy_application_packet_v1(
            self.snapshots["ready-en"]
        )
        audit = PacketDOMAudit()
        audit.feed(document)

        self.assertEqual(1, audit.tag_counts.get("h1", 0))
        mains = [attrs for tag, attrs in audit.start_tags if tag == "main"]
        self.assertEqual(
            [{"id": "main-content", "class": "packet-shell", "tabindex": "-1", "aria-labelledby": "packet-title"}],
            mains,
        )
        self.assertEqual(len(audit.ids), len(set(audit.ids)))
        self.assertTrue(set(audit.references).issubset(set(audit.ids)))
        self.assertTrue(
            {
                "packet-readiness",
                "packet-context",
                "packet-requirements",
                "packet-unsupported",
                "packet-drafts",
                "packet-claim-review",
                "packet-handoff",
                "packet-tracking",
                "packet-approval",
            }.issubset(set(audit.ids))
        )
        self.assertEqual(1, audit.table_captions)
        self.assertEqual(1, audit.table_heads)
        self.assertIn("col", audit.header_scopes)
        self.assertIn("row", audit.header_scopes)
        self.assertGreaterEqual(audit.tag_counts.get("dl", 0), 3)
        self.assertGreaterEqual(audit.tag_counts.get("ol", 0), 2)
        self.assertGreaterEqual(audit.tag_counts.get("ul", 0), 2)
        self.assertEqual(1, document.count('class="packet-readiness '))
        self.assertEqual(3, len(re.findall(r'id="claim-row-\d+"', document)))

        claim_table = document.split("<tbody>", 1)[1].split("</tbody>", 1)[0]
        for surface in self.artifacts["ready-en"]["draft_materials"].values():
            for draft in surface:
                self.assertIn(draft["text"], claim_table)
        tracking = document.split('id="packet-tracking"', 1)[1].split("</section>", 1)[0]
        self.assertIn("Application packet drafted", tracking)
        self.assertIn("Proposed", tracking)
        self.assertIn("Manual recording required", tracking)

        for tag, attrs in audit.start_tags:
            classes = set((attrs.get("class") or "").split())
            if tag in {"section", "article"} and classes.intersection(
                {
                    "packet-readiness",
                    "packet-context",
                    "packet-requirements",
                    "packet-unsupported",
                    "packet-drafts",
                    "packet-claim-review",
                    "packet-handoff",
                    "packet-tracking",
                    "packet-approval",
                    "packet-requirement-card",
                }
            ):
                self.assertTrue(attrs.get("aria-labelledby"), (tag, attrs))

    def test_bilingual_copy_and_section_order_are_deterministic_without_raw_states(self) -> None:
        """Break caught: locale copy, decision cardinality, or the approved reading order drifts."""
        expected = {
            "ready-es": (
                "Paquete privado para vacante",
                "Listo para revisión manual privada",
                "Requisitos y evidencia",
                "Revisión de afirmaciones",
            ),
            "ready-en": (
                "Private vacancy application packet",
                "Ready for private manual review",
                "Requirements and evidence",
                "Claim review",
            ),
            "revise-missing-es": (
                "Paquete privado para vacante",
                "Revisar antes de autorizar",
                "Evidencia faltante o no respaldada",
                "Revisión de afirmaciones",
            ),
            "revise-review-en": (
                "Private vacancy application packet",
                "Revise before authorization",
                "Unsupported or missing evidence",
                "Claim review",
            ),
            "stop-constraint-es": (
                "Paquete privado para vacante",
                "Detener preparación",
                "Trabajo privado suprimido",
                "Límite de aprobación",
            ),
            "stop-constraint-en": (
                "Private vacancy application packet",
                "Stop preparation",
                "Private work is suppressed",
                "Approval boundary",
            ),
        }
        raw_states = (
            "ready_for_manual_authorization",
            "revise_first",
            "manual_private_review",
            "application_packet_drafted",
            "candidate_reported",
            "review_required",
            "draft_only",
            "not_proposed",
        )
        for scenario, phrases in expected.items():
            with self.subTest(scenario=scenario):
                first = self.renderer.render_private_vacancy_application_packet_v1(
                    self.snapshots[scenario]
                )
                second = self.renderer.render_private_vacancy_application_packet_v1(
                    self.snapshots[scenario]
                )
                self.assertEqual(first, second)
                self.assertTrue(all(phrase in first for phrase in phrases))
                self.assertEqual(1, first.count('class="packet-readiness '))
                self.assertNotIn("aria-live", first)
                for raw_state in raw_states:
                    self.assertNotIn(raw_state, first)

        ready = self.renderer.render_private_vacancy_application_packet_v1(
            self.snapshots["ready-en"]
        )
        ordered_ids = (
            'id="readiness-title"',
            'id="packet-context"',
            'id="packet-requirements"',
            'id="packet-unsupported"',
            'id="packet-drafts"',
            'id="packet-claim-review"',
            'id="packet-handoff"',
            'id="packet-tracking"',
            'id="packet-approval"',
        )
        positions = [ready.index(identifier) for identifier in ordered_ids]
        self.assertEqual(sorted(positions), positions)

    def test_stop_suppresses_drafts_claim_table_handoff_and_tracking_detail(self) -> None:
        """Break caught: stop leaks secondary preparation material or proposed actions."""
        for scenario in ("stop-constraint-es", "stop-constraint-en"):
            with self.subTest(scenario=scenario):
                document = self.renderer.render_private_vacancy_application_packet_v1(
                    self.snapshots[scenario]
                )
                artifact = self.artifacts[scenario]
                for identifier in (
                    'id="packet-drafts"',
                    'id="packet-claim-review"',
                    'id="packet-handoff"',
                    'id="packet-tracking"',
                ):
                    self.assertNotIn(identifier, document)
                self.assertIn('id="packet-suppressed"', document)
                self.assertNotIn("<table", document)
                self.assertNotIn("application_packet_drafted", document)
                self.assertNotIn("country_geography", document)
                for surface in artifact["draft_materials"].values():
                    for row in surface:
                        self.assertNotIn(row["text"], document)
                self.assertIn(
                    "No se realiza ninguna acción externa."
                    if scenario.endswith("-es")
                    else "No external action is performed.",
                    document,
                )

    def test_public_vacancy_metadata_is_escaped_and_all_other_dynamic_copy_is_closed(self) -> None:
        """Break caught: validated public display metadata is interpolated without HTML escaping."""
        helpers = load_module(
            ROOT / "tests" / "test_private_vacancy_application_packet_v1.py",
            "private_packet_renderer_contract_helpers",
        )
        group = helpers.composite_group()
        eligibility_group = group["eligibility_group"]
        research = eligibility_group["research"]
        dossier = eligibility_group["executive_dossier"]
        vacancy = next(row for row in research["vacancies"] if row["vacancy_id"] == "V-003")
        vacancy["title"] = "Fixture < 7 & Reliability"
        employer = next(
            row for row in research["employers"] if row["employer_id"] == vacancy["employer_id"]
        )
        employer["display_name"] = "R&D & Reliability"
        market = helpers.MARKET_BUILDER.build_market_dossier_v2(research, dossier)
        selected_index = next(
            index for index, row in enumerate(market["vacancies"]) if row["vacancy_id"] == "V-003"
        )
        response = helpers.RESPONSE_BUILDER.build_candidate_gap_response_v1(
            research,
            market,
            {
                "selected_vacancy_ordinal": f"V{selected_index + 1}",
                "selected_signal": "terraform",
                "relation": "supported",
                "selected_provider_ordinal": None,
            },
            None,
        )
        assessment = helpers.ASSESSMENT_BUILDER.build_candidate_gap_assessment_v1(
            research, dossier, market, response, None
        )
        eligibility = helpers.ELIGIBILITY_BUILDER.build_career_next_action_eligibility_v1(
            research, dossier, market, response, assessment, None
        )
        eligibility_group.update(
            {
                "market_dossier": market,
                "gap_response": response,
                "gap_assessment": assessment,
                "eligibility": eligibility,
            }
        )
        packet = helpers.PACKET_BUILDER.build_private_vacancy_application_packet_v1(group)
        snapshot = self.validator.validate_private_vacancy_application_packet_v1(packet, group)
        document = self.renderer.render_private_vacancy_application_packet_v1(snapshot)

        self.assertIn("Fixture &lt; 7 &amp; Reliability", document)
        self.assertIn("R&amp;D &amp; Reliability", document)
        self.assertNotIn("Fixture < 7 & Reliability", document)
        self.assertNotIn("R&D & Reliability", document)

    def test_html_omits_internal_ids_sources_snapshots_urls_controls_and_candidate_bindings(self) -> None:
        """Break caught: private provenance, source prose, or an action surface reaches HTML."""
        forbidden_fragments = (
            "source_snapshot",
            "snap-",
            "sha256",
            "V-003",
            "V-003-R-01",
            "F-001",
            "C-001",
            "D-CV-001",
            "verified_record",
            "candidate_statement",
            "signal_bindings",
            "Synthetic public requirement.",
            "/Users/",
            "file://",
            "http://",
            "https://",
        )
        forbidden_tags = ("script", "form", "button", "input", "select", "textarea", "img", "link")
        for scenario in SCENARIOS:
            with self.subTest(scenario=scenario):
                document = self.renderer.render_private_vacancy_application_packet_v1(
                    self.snapshots[scenario]
                )
                for fragment in forbidden_fragments:
                    self.assertNotIn(fragment, document)
                for tag in forbidden_tags:
                    self.assertNotRegex(document.casefold(), rf"<{tag}\b")
                self.assertNotRegex(document, r"(?:href|src)=[\"'](?:https?:|file:|//)")
                self.assertEqual(1, len(re.findall(r'href="#main-content"', document)))

    def test_security_metadata_and_css_cover_static_accessibility_presentation_contracts(self) -> None:
        """Break caught: offline policy, responsive modes, or print atomicity is removed."""
        document = self.renderer.render_private_vacancy_application_packet_v1(
            self.snapshots["ready-en"]
        )
        self.assertIn('<meta name="robots" content="noindex,nofollow,noarchive">', document)
        self.assertIn('<meta name="referrer" content="no-referrer">', document)
        self.assertIn("default-src &#x27;none&#x27;", document.replace("'", "&#x27;"))
        self.assertIn("style-src 'unsafe-inline'", document)
        self.assertIn("img-src 'none'", document)
        self.assertNotIn("script-src", document)

        css = (ASSETS / "private-vacancy-application-packet-v1.css").read_text(
            encoding="utf-8"
        )
        for token in (
            "--paper:",
            "--surface:",
            "--ink:",
            "--forest:",
            "--coral:",
            "--line:",
            "--sans:",
            ".private-vacancy-packet-document",
            "width: min(920px, calc(100% - 2rem))",
            "@media screen and (prefers-color-scheme: dark)",
            "@media (forced-colors: active)",
            "@media (prefers-reduced-motion: reduce)",
            "@media (max-width: 640px)",
            "@media print",
            "break-inside: avoid",
            "page-break-inside: avoid",
            "display: table-header-group",
            "position: fixed",
            "attr(data-print-private)",
            "attr(data-print-boundary)",
        ):
            self.assertIn(token, css)
        self.assertNotIn("1180px", css)
        self.assertNotIn("background-image", css)
        self.assertNotIn("url(", css.casefold())

    def test_shipped_assets_are_mirrored_and_resume_fingerprints_match_current_bytes(self) -> None:
        """Break caught: implementation assets drift from local design evidence or resume state."""
        template_path = ASSETS / "private-vacancy-application-packet-v1.html"
        css_path = ASSETS / "private-vacancy-application-packet-v1.css"
        template = template_path.read_text(encoding="utf-8")
        css = css_path.read_text(encoding="utf-8")
        layouts = (ROOT / ".superdesign" / "init" / "layouts.md").read_text(
            encoding="utf-8"
        )
        theme = (ROOT / ".superdesign" / "init" / "theme.md").read_text(
            encoding="utf-8"
        )
        self.assertIn(f"```html\n{template}```", layouts)
        self.assertIn(f"```css\n{css}```", theme)

        resume = load_json(ROOT / ".superdesign" / "resume.json")
        target = resume["targets"]["vacancy-application-packet"]
        self.assertEqual(
            "971e4b3b-dcab-4940-9b8e-36dd181cb3d1",
            target["projectId"],
        )
        self.assertEqual(
            "a7447bcf-574b-470f-8dad-13f193c54cc7",
            target["activeDraftId"],
        )
        self.assertEqual(
            1,
            target["drafts"][target["activeDraftId"]]["currentVersion"],
        )
        self.assertEqual(set(target["contextFiles"]), set(target["fingerprints"]))
        self.assertEqual(
            [
                ".superdesign/design-system.md",
                "plugins/professional-growth-coach/assets/private-recruiter-reply-triage-v1.html",
                "plugins/professional-growth-coach/assets/private-recruiter-reply-triage-v1.css",
                "plugins/professional-growth-coach/skills/optimize-career-assets/SKILL.md",
                "plugins/professional-growth-coach/skills/optimize-career-assets/references/asset-workflow.md",
            ],
            target["contextFiles"],
        )
        for relative_path in target["contextFiles"]:
            payload = (ROOT / relative_path).read_bytes()
            self.assertEqual(
                hashlib.sha256(payload).hexdigest(),
                target["fingerprints"][relative_path],
                relative_path,
            )

    def test_one_captured_snapshot_drives_json_html_html_write_and_receipt(self) -> None:
        """Break caught: JSON, HTML, and receipts are rebuilt from different caller captures."""
        marker = "review-sensitive-second-capture"
        packet = OnePassMapping(copy.deepcopy(self.artifacts["ready-es"]), marker)
        sources = OnePassMapping(copy.deepcopy(self.sources["ready-es"]), marker)
        snapshot = self.validator.validate_private_vacancy_application_packet_v1(
            packet, sources
        )
        self.assertEqual(1, packet.items_calls)
        self.assertEqual(1, sources.items_calls)

        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            json_output = directory / "packet.json"
            html_output = directory / "packet.html"
            json_receipt = self.writer.write_private_vacancy_application_packet_v1(
                snapshot, json_output
            )
            rendered = self.renderer.render_private_vacancy_application_packet_v1(snapshot)
            html_receipt = self.renderer.write_private_vacancy_application_packet_html_v1(
                snapshot, html_output
            )

            self.assertEqual(
                self.artifacts["ready-es"],
                json.loads(json_output.read_text(encoding="utf-8")),
            )
            self.assertEqual(rendered, html_output.read_text(encoding="utf-8"))
            self.assertEqual(json_output.resolve(), json_receipt.output_path)
            self.assertEqual(html_output.resolve(), html_receipt.output_path)
            for receipt in (json_receipt, html_receipt):
                self.assertEqual("private_vacancy_application_packet", receipt.artifact_type)
                self.assertEqual("private-vacancy-application-packet-v1", receipt.schema_version)
                self.assertEqual("es", receipt.locale)
                self.assertEqual("ready_for_manual_authorization", receipt.readiness_state)
                self.assertEqual("V-003", receipt.vacancy_id)
                self.assertTrue(receipt.private_draft)
                self.assertFalse(receipt.external_action_authorized)
            self.assertEqual(0o600, stat.S_IMODE(json_output.stat().st_mode))
            self.assertEqual(0o600, stat.S_IMODE(html_output.stat().st_mode))

        self.assertEqual(1, packet.items_calls)
        self.assertEqual(1, sources.items_calls)

    def test_html_cli_captures_once_emits_exact_receipt_and_fails_without_echo_or_partial_output(self) -> None:
        """Break caught: standalone rendering broadens receipts or leaks failed input state."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            packet_path = FIXTURES / "ready-en" / "application-packet.json"
            sources_path = FIXTURES / "ready-en" / "sources.json"
            output = directory / "packet.html"
            stdout = io.StringIO()
            stderr = io.StringIO()
            validate = self.renderer.validate_private_vacancy_application_packet_v1
            with patch.object(
                self.renderer,
                "validate_private_vacancy_application_packet_v1",
                wraps=validate,
            ) as validation, redirect_stdout(stdout), redirect_stderr(stderr):
                result = self.renderer._cli(
                    [
                        str(packet_path),
                        "--source-group",
                        str(sources_path),
                        "--output",
                        str(output),
                    ]
                )
            self.assertEqual(0, result)
            self.assertEqual("", stderr.getvalue())
            self.assertEqual(1, validation.call_count)
            receipt = json.loads(stdout.getvalue())
            self.assertEqual(
                [
                    "artifact_type",
                    "schema_version",
                    "locale",
                    "readiness_state",
                    "vacancy_id",
                    "output_path",
                    "private_draft",
                    "external_action_authorized",
                ],
                list(receipt),
            )
            self.assertEqual(str(output.resolve()), receipt["output_path"])
            self.assertTrue(output.is_file())
            self.assertEqual(0o600, stat.S_IMODE(output.stat().st_mode))

            marker = "review-sensitive-tampered-packet"
            tampered = copy.deepcopy(self.artifacts["ready-en"])
            tampered["readiness"]["headline"] = marker
            tampered_path = directory / "tampered.json"
            tampered_path.write_text(json.dumps(tampered), encoding="utf-8")
            failed_output = directory / "failed.html"
            stdout = io.StringIO()
            stderr = io.StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                result = self.renderer._cli(
                    [
                        str(tampered_path),
                        "--source-group",
                        str(sources_path),
                        "--output",
                        str(failed_output),
                    ]
                )
            self.assertEqual(2, result)
            self.assertEqual("", stdout.getvalue())
            self.assertEqual(
                "cannot render private vacancy application packet\n",
                stderr.getvalue(),
            )
            self.assertNotIn(marker, stderr.getvalue())
            self.assertFalse(failed_output.exists())

    def test_html_writer_preserves_existing_bytes_and_rejects_symbolic_link_targets(self) -> None:
        """Break caught: a failed HTML publish replaces an existing or linked private file."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            target = directory / "target.html"
            target.write_bytes(b"previous-private-bytes")
            link = directory / "packet.html"
            link.symlink_to(target)
            with self.assertRaises(
                self.renderer.PrivateVacancyApplicationPacketRenderError
            ) as caught:
                self.renderer.write_private_vacancy_application_packet_html_v1(
                    self.snapshots["ready-en"], link, force=True
                )
            self.assertEqual(
                "cannot render private vacancy application packet",
                str(caught.exception),
            )
            self.assertTrue(link.is_symlink())
            self.assertEqual(b"previous-private-bytes", target.read_bytes())
            self.assertEqual([], list(directory.glob(".packet.html.tmp-*")))

    def test_same_run_pins_historical_v1_v2_and_no_market_render_bytes(self) -> None:
        """Break caught: the new renderer changes any historical dossier composition byte."""
        history = load_module(
            ROOT / "tests" / "test_executive_career_dossier_v2.py",
            "private_packet_historical_renderer_helpers",
        )
        renderer = history.load_renderer()
        helper = history.ExecutiveCareerDossierV2RendererTests(methodName="runTest")
        renders = {
            "v1": renderer.render_dossier_html(**helper.v1_render_sources()),
            "v2": renderer.render_dossier_html(**helper.v2_render_sources()),
        }
        for generation, rendered in renders.items():
            with self.subTest(generation=generation):
                size, digest = history.HISTORICAL_COMPLETE_RENDER_SNAPSHOTS[generation]
                encoded = rendered.encode("utf-8")
                self.assertEqual(size, len(encoded))
                self.assertEqual(digest, hashlib.sha256(encoded).hexdigest())

        for fixture_name, (size, digest) in history.NO_MARKET_RENDER_SNAPSHOTS.items():
            with self.subTest(no_market=fixture_name):
                dossier = history.load_json_fixture(history.V2_FIXTURE_ROOT / fixture_name)
                encoded = renderer.render_dossier_html(dossier).encode("utf-8")
                self.assertEqual(size, len(encoded))
                self.assertEqual(digest, hashlib.sha256(encoded).hexdigest())


if __name__ == "__main__":
    unittest.main()
