"""Behavioral contract for the identity-free candidate fact matrix."""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
import tempfile
import unittest
from collections.abc import Mapping
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "plugins" / "professional-growth-coach" / "scripts"
SCHEMA = ROOT / "plugins" / "professional-growth-coach" / "schemas" / "candidate-fact-matrix-v1.schema.json"


def load_script(name: str):
    path = SCRIPTS / name
    specification = importlib.util.spec_from_file_location(
        f"candidate_fact_matrix_{path.stem}", path
    )
    if specification is None or specification.loader is None:
        raise AssertionError("candidate fact matrix module is unavailable")
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


BUILDER = load_script("build_candidate_fact_matrix_v1.py")
VALIDATOR = load_script("validate_candidate_fact_matrix_v1.py")


def source_group(*, locale: str = "es", captured_at: str = "2026-08-24T12:30:45Z") -> dict[str, object]:
    return {
        "locale": locale,
        "captured_at": captured_at,
        "sources": [
            {"source_type": "verified_record", "evidence_state": "verified"},
            {"source_type": "cv", "evidence_state": "candidate_reported"},
            {"source_type": "portfolio", "evidence_state": "inferred"},
        ],
        "facts": [
            {
                "fact_text": "Operated Kubernetes services with documented incident reviews.",
                "fact_type": "experience",
                "source_ordinals": [1, 2],
                "signals": ["incident_response", "kubernetes"],
                "signal_relation": "supports",
                "conflict_state": "clear",
                "confidentiality": "usable",
            },
            {
                "fact_text": "Certificate management and key rotation practice completed.",
                "fact_type": "credential",
                "source_ordinals": [3],
                "signals": ["certificate_management", "key_rotation"],
                "signal_relation": "supports",
                "conflict_state": "clear",
                "confidentiality": "review_required",
            },
        ],
    }


def build(group: object | None = None) -> dict[str, object]:
    return BUILDER.build_candidate_fact_matrix_v1(source_group() if group is None else group)


class CandidateFactMatrixV1Tests(unittest.TestCase):
    def assert_rejected(self, group: object) -> None:
        """Break caught: invalid private input escapes the generic builder boundary."""
        with self.assertRaisesRegex(ValueError, "candidate fact matrix is invalid") as caught:
            build(group)
        self.assertNotIn("review-sensitive", str(caught.exception))

    def test_builder_projects_exact_closed_rows_and_weakest_evidence(self) -> None:
        """Break caught: IDs, closed projection, or evidence minimum drift from captured input."""
        artifact = build()
        self.assertEqual(
            {"schema_version", "locale", "case_scope", "sources", "facts", "source_snapshot"},
            set(artifact),
        )
        self.assertEqual("candidate-fact-matrix-v1", artifact["schema_version"])
        self.assertEqual("single_candidate", artifact["case_scope"])
        self.assertEqual(["FS-001", "FS-002", "FS-003"], [row["source_id"] for row in artifact["sources"]])
        self.assertEqual(["F-001", "F-002"], [row["fact_id"] for row in artifact["facts"]])
        self.assertEqual("candidate_reported", artifact["facts"][0]["evidence_state"])
        self.assertEqual("inferred", artifact["facts"][1]["evidence_state"])
        self.assertEqual(["FS-001", "FS-002"], artifact["facts"][0]["source_ids"])
        self.assertTrue(artifact["source_snapshot"].startswith("snap-candidate-facts-sha256-"))

    def test_builder_preserves_source_fact_and_lexicographic_signal_order(self) -> None:
        """Break caught: projection reorders authoritative source/fact rows or normalized signals."""
        group = source_group()
        group["facts"] = list(reversed(group["facts"]))
        group["facts"][0]["signals"] = ["certificate_management", "key_rotation"]
        artifact = build(group)
        self.assertEqual("Certificate management and key rotation practice completed.", artifact["facts"][0]["fact_text"])
        self.assertEqual(["certificate_management", "key_rotation"], artifact["facts"][0]["signals"])

    def test_builder_rejects_source_type_evidence_upgrades_and_constraint_only_contradictions(self) -> None:
        """Break caught: unverified source types gain verified status or ordinary facts contradict."""
        upgraded = source_group()
        upgraded["sources"][1]["evidence_state"] = "verified"
        self.assert_rejected(upgraded)
        contradiction = source_group()
        contradiction["facts"][0]["signal_relation"] = "contradicts"
        self.assert_rejected(contradiction)
        allowed = source_group()
        allowed["facts"][0]["fact_type"] = "constraint"
        allowed["facts"][0]["signal_relation"] = "contradicts"
        self.assertEqual("contradicts", build(allowed)["facts"][0]["signal_relation"])

    def test_builder_rejects_forbidden_fact_with_signal_or_non_unknown_relation(self) -> None:
        """Break caught: a forbidden fact can enter downstream signal matching."""
        group = source_group()
        group["facts"][0]["confidentiality"] = "forbidden"
        self.assert_rejected(group)
        group = source_group()
        group["facts"][0]["confidentiality"] = "forbidden"
        group["facts"][0]["signals"] = []
        group["facts"][0]["signal_relation"] = "unknown"
        self.assertEqual([], build(group)["facts"][0]["signals"])

    def test_builder_rejects_closed_contract_bounds_ordering_and_unknown_ordinals(self) -> None:
        """Break caught: malformed rows, unordered references, or unknown sources are accepted."""
        for mutation in (
            lambda value: value.update({"extra": "review-sensitive"}),
            lambda value: value["sources"][0].update({"source_id": "FS-900"}),
            lambda value: value["facts"][0].update({"source_ordinals": [2, 1]}),
            lambda value: value["facts"][0].update({"source_ordinals": [4]}),
            lambda value: value["facts"][0].update({"signals": ["kubernetes", "incident_response"]}),
            lambda value: value["facts"][0].update({"signals": ["kubernetes", "kubernetes"]}),
        ):
            with self.subTest(mutation=mutation):
                group = source_group()
                mutation(group)
                self.assert_rejected(group)

    def test_builder_rejects_identity_contact_urls_html_controls_and_authentication_secrets(self) -> None:
        """Break caught: prohibited private prose or secret material survives capture."""
        for prose in (
            "Candidate name: review-sensitive",
            "contact review-sensitive@example.invalid",
            "Call +52 55 5555 5555",
            "See https://example.invalid/private",
            "<b>review-sensitive</b>",
            "private analytics: 99 profile views",
            "password = review-sensitive",
            "Bearer abcdefgh",
            "line\nfeed",
        ):
            with self.subTest(prose=prose):
                group = source_group()
                group["facts"][0]["fact_text"] = prose
                self.assert_rejected(group)

    def test_builder_rejects_totalized_source_path_families_without_echo(self) -> None:
        """Break caught: one path family evades the source-location privacy boundary."""
        for prose in (
            "Evidence kept at /Users/example/private-cv.pdf.",
            r"Evidence kept at C:\Users\example\private-cv.pdf.",
            "Evidence kept at file:///private/example/private-cv.pdf.",
            "Evidence kept at source/private-cv.pdf.",
            "Document at /foo/private-cv.pdf",
            r"Document at source\\private-cv.pdf",
            r"Document at \server\share\private-cv.pdf",
            r"Document at \\server\share\private-cv.pdf",
        ):
            with self.subTest(prose=prose):
                group = source_group()
                group["facts"][0]["fact_text"] = prose
                self.assert_rejected(group)

    def test_builder_path_boundary_preserves_professional_vocabulary_and_versions(self) -> None:
        """Break caught: total path rejection blocks ordinary technical prose, certificates, or versions."""
        for prose in (
            "Authentication version 2.1 control practice.",
            "Kubernetes/Helm operations practice.",
            "AWS Certified Security - Specialty version 2024 preparation.",
        ):
            with self.subTest(prose=prose):
                group = source_group()
                group["facts"][0]["fact_text"] = prose
                self.assertEqual(prose, build(group)["facts"][0]["fact_text"])

    def test_builder_rejects_ordinary_candidate_identity_prose_without_labels(self) -> None:
        """Break caught: a candidate name pair reaches the fact matrix without an identity label."""
        group = source_group()
        group["facts"][0]["fact_text"] = "Alex Morgan led incident reviews."
        self.assert_rejected(group)

    def test_builder_rejects_c1_and_unicode_format_characters(self) -> None:
        """Break caught: non-ASCII control or format characters evade the prose boundary."""
        for prose in (
            "Evidence\u0085hidden",
            "Evidence\u200bhidden",
        ):
            with self.subTest(prose=prose):
                group = source_group()
                group["facts"][0]["fact_text"] = prose
                self.assert_rejected(group)

    def test_builder_preserves_safe_security_vocabulary_and_certificate_names(self) -> None:
        """Break caught: safety scanning rejects ordinary security terminology or qualifications."""
        group = source_group()
        group["facts"][0]["fact_text"] = "Authentication, certificate management, key rotation, and AWS Certified Security - Specialty practice."
        group["facts"][0]["signals"] = ["authentication", "certificate_management", "key_rotation"]
        artifact = build(group)
        self.assertIn("AWS Certified Security", artifact["facts"][0]["fact_text"])

    def test_validator_recomputes_complete_artifact_and_raw_snapshot(self) -> None:
        """Break caught: validator accepts a tampered projection or stale raw-source digest."""
        group = source_group()
        artifact = build(group)
        self.assertEqual([], VALIDATOR.validate_candidate_fact_matrix_v1(artifact, group))
        tampered = copy.deepcopy(artifact)
        tampered["facts"][0]["evidence_state"] = "verified"
        self.assertEqual(
            ["candidate fact matrix does not match validated sources"],
            VALIDATOR.validate_candidate_fact_matrix_v1(tampered, group),
        )
        crossed = copy.deepcopy(group)
        crossed["locale"] = "en"
        self.assertEqual(
            ["candidate fact matrix does not match validated sources"],
            VALIDATOR.validate_candidate_fact_matrix_v1(artifact, crossed),
        )

    def test_builder_detaches_mutable_inputs_and_rejects_recursive_oversized_and_exception_mappings(self) -> None:
        """Break caught: capture keeps caller mutability or accepts unsafe mapping traversals."""
        group = source_group()
        artifact = build(group)
        group["facts"][0]["fact_text"] = "changed after capture"
        self.assertNotIn("changed after capture", json.dumps(artifact, ensure_ascii=False))
        recursive: dict[str, object] = {"locale": "es", "captured_at": "2026-08-24T12:30:45Z", "sources": [], "facts": []}
        recursive["facts"].append(recursive)
        self.assert_rejected(recursive)
        oversized = source_group()
        oversized["facts"][0]["fact_text"] = "x" * 501
        self.assert_rejected(oversized)

        class ExplodingMapping(Mapping[str, object]):
            def __iter__(self):
                raise RuntimeError("review-sensitive")

            def __len__(self):
                return 1

            def __getitem__(self, key: str) -> object:
                raise RuntimeError("review-sensitive")

        self.assert_rejected(ExplodingMapping())

    def test_loader_rejects_duplicate_key_json_without_echoing_source_values(self) -> None:
        """Break caught: duplicate-key persisted JSON becomes an ambiguous source artifact."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "matrix.json"
            path.write_text('{"schema_version":"candidate-fact-matrix-v1","schema_version":"review-sensitive"}', encoding="utf-8")
            with self.assertRaisesRegex(VALIDATOR.CandidateFactMatrixLoadError, "cannot load candidate fact matrix") as caught:
                VALIDATOR.load_candidate_fact_matrix_v1(path)
        self.assertNotIn("review-sensitive", str(caught.exception))

    def test_schema_closes_rows_and_declares_contract_bounds(self) -> None:
        """Break caught: schema stops expressing the closed externally visible artifact contract."""
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(6, len(schema["required"]))
        self.assertFalse(schema["properties"]["sources"]["items"]["additionalProperties"])
        self.assertFalse(schema["properties"]["facts"]["items"]["additionalProperties"])
        self.assertEqual(20, schema["properties"]["sources"]["maxItems"])
        self.assertEqual(100, schema["properties"]["facts"]["maxItems"])


if __name__ == "__main__":
    unittest.main()
