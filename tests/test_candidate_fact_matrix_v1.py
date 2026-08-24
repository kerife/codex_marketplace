"""Behavioral contract for the structural candidate fact matrix."""

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

REQUIREMENT_SIGNALS = (
    "authentication",
    "certificate_management",
    "incident_response",
    "key_rotation",
    "kubernetes",
    "linux",
    "observability",
    "python",
    "terraform",
)
ELIGIBILITY_GATE_SIGNALS = (
    "work_authorization",
    "country_geography",
    "work_arrangement",
    "language",
    "seniority",
    "experience_floor",
    "employment_arrangement",
)


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
                "fact_type": "experience",
                "source_ordinals": [1, 2],
                "signal_bindings": [
                    {"kind": "eligibility_gate", "signal": "language"},
                    {"kind": "requirement", "signal": "incident_response"},
                    {"kind": "requirement", "signal": "kubernetes"},
                ],
                "signal_relation": "supports",
                "conflict_state": "clear",
                "confidentiality": "usable",
            },
            {
                "fact_type": "credential",
                "source_ordinals": [3],
                "signal_bindings": [
                    {"kind": "requirement", "signal": "certificate_management"},
                    {"kind": "requirement", "signal": "key_rotation"},
                ],
                "signal_relation": "supports",
                "conflict_state": "clear",
                "confidentiality": "review_required",
            },
        ],
    }


def build(group: object | None = None) -> dict[str, object]:
    try:
        return BUILDER.build_candidate_fact_matrix_v1(
            source_group() if group is None else group
        )
    except ValueError as error:
        raise AssertionError(
            f"expected the structural candidate fact group to build: {error}"
        ) from None


class OneShotMapping(Mapping[str, object]):
    """Mapping that proves a capture boundary does not reread caller state."""

    def __init__(self, value: dict[str, object]) -> None:
        self._value = value
        self.reads = 0

    def __iter__(self):
        return iter(self._value)

    def __len__(self) -> int:
        return len(self._value)

    def __getitem__(self, key: str) -> object:
        return self._value[key]

    def items(self):
        self.reads += 1
        if self.reads > 1:
            raise RuntimeError("review-sensitive reread")
        return self._value.items()


class CandidateFactMatrixV1Tests(unittest.TestCase):
    def assert_rejected(self, group: object) -> None:
        """Break caught: invalid private structure escapes the generic builder boundary."""
        with self.assertRaises(ValueError) as caught:
            BUILDER.build_candidate_fact_matrix_v1(group)
        self.assertEqual("candidate fact matrix is invalid", str(caught.exception))
        self.assertNotIn("review-sensitive", str(caught.exception))

    def test_builder_projects_exact_structural_rows_and_weakest_evidence(self) -> None:
        """Break caught: structural fields, IDs, or evidence minima drift from captured input."""
        artifact = build()
        self.assertEqual(
            {
                "schema_version",
                "locale",
                "case_scope",
                "signal_vocabulary",
                "sources",
                "facts",
                "source_snapshot",
            },
            set(artifact),
        )
        self.assertEqual("candidate-fact-matrix-v1", artifact["schema_version"])
        self.assertEqual("single_candidate", artifact["case_scope"])
        self.assertEqual("candidate-claim-signal-v1", artifact["signal_vocabulary"])
        self.assertEqual(["FS-001", "FS-002", "FS-003"], [row["source_id"] for row in artifact["sources"]])
        self.assertEqual(["F-001", "F-002"], [row["fact_id"] for row in artifact["facts"]])
        self.assertEqual("candidate_reported", artifact["facts"][0]["evidence_state"])
        self.assertEqual("inferred", artifact["facts"][1]["evidence_state"])
        self.assertEqual(["FS-001", "FS-002"], artifact["facts"][0]["source_ids"])
        self.assertEqual(
            {
                "fact_id",
                "fact_type",
                "evidence_state",
                "source_ids",
                "signal_bindings",
                "signal_relation",
                "conflict_state",
                "confidentiality",
            },
            set(artifact["facts"][0]),
        )
        self.assertEqual(
            {"kind", "signal"}, set(artifact["facts"][0]["signal_bindings"][0])
        )
        self.assertNotIn("fact_text", json.dumps(artifact, ensure_ascii=False))
        self.assertTrue(artifact["source_snapshot"].startswith("snap-candidate-facts-sha256-"))

    def test_builder_preserves_source_and_fact_order_and_requires_kind_then_signal_order(self) -> None:
        """Break caught: projection reorders facts or accepts unordered typed bindings."""
        group = source_group()
        group["facts"] = list(reversed(group["facts"]))
        artifact = build(group)
        self.assertEqual(["credential", "experience"], [row["fact_type"] for row in artifact["facts"]])
        self.assertEqual(
            [
                {"kind": "eligibility_gate", "signal": "language"},
                {"kind": "requirement", "signal": "incident_response"},
                {"kind": "requirement", "signal": "kubernetes"},
            ],
            artifact["facts"][1]["signal_bindings"],
        )

        unordered = source_group()
        unordered["facts"][0]["signal_bindings"] = list(
            reversed(unordered["facts"][0]["signal_bindings"])
        )
        self.assert_rejected(unordered)

    def test_builder_accepts_only_the_exact_typed_signal_catalogs(self) -> None:
        """Break caught: a catalog token is lost or an open/crossed token becomes bindable."""
        for kind, catalog in (
            ("requirement", REQUIREMENT_SIGNALS),
            ("eligibility_gate", ELIGIBILITY_GATE_SIGNALS),
        ):
            for signal in catalog:
                with self.subTest(kind=kind, signal=signal):
                    group = source_group()
                    group["facts"] = [
                        {
                            "fact_type": "constraint" if kind == "eligibility_gate" else "skill",
                            "source_ordinals": [1],
                            "signal_bindings": [{"kind": kind, "signal": signal}],
                            "signal_relation": "supports",
                            "conflict_state": "clear",
                            "confidentiality": "usable",
                        }
                    ]
                    self.assertEqual(
                        [{"kind": kind, "signal": signal}],
                        build(group)["facts"][0]["signal_bindings"],
                    )

        for kind, signal in (
            ("requirement", "language"),
            ("eligibility_gate", "terraform"),
            ("requirement", "review_sensitive_signal"),
        ):
            with self.subTest(kind=kind, signal=signal):
                group = source_group()
                group["facts"][0]["signal_bindings"] = [{"kind": kind, "signal": signal}]
                self.assert_rejected(group)

    def test_builder_rejects_duplicate_open_crossed_or_malformed_bindings(self) -> None:
        """Break caught: typed binding closure, pair uniqueness, or domain separation weakens."""
        mutations = (
            lambda value: value["facts"][0].update(
                {"signal_bindings": [
                    {"kind": "requirement", "signal": "kubernetes"},
                    {"signal": "kubernetes", "kind": "requirement"},
                ]}
            ),
            lambda value: value["facts"][0].update(
                {"signal_bindings": [{"kind": "requirement", "signal": "kubernetes", "note": "review-sensitive"}]}
            ),
            lambda value: value["facts"][0].update(
                {"signal_bindings": [{"kind": "review-sensitive", "signal": "kubernetes"}]}
            ),
            lambda value: value["facts"][0].update(
                {"signal_bindings": ["review-sensitive"]}
            ),
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                group = source_group()
                mutation(group)
                self.assert_rejected(group)

    def test_builder_allows_zero_bindings_only_for_forbidden_unknown_facts(self) -> None:
        """Break caught: an unbound usable fact enters the matrix or a forbidden fact can bind."""
        forbidden = source_group()
        forbidden["facts"][0]["confidentiality"] = "forbidden"
        forbidden["facts"][0]["signal_bindings"] = []
        forbidden["facts"][0]["signal_relation"] = "unknown"
        self.assertEqual([], build(forbidden)["facts"][0]["signal_bindings"])

        for confidentiality, bindings, relation in (
            ("usable", [], "unknown"),
            ("review_required", [], "unknown"),
            ("forbidden", [{"kind": "requirement", "signal": "kubernetes"}], "unknown"),
            ("forbidden", [], "supports"),
        ):
            with self.subTest(confidentiality=confidentiality, relation=relation):
                group = source_group()
                group["facts"][0].update(
                    {
                        "confidentiality": confidentiality,
                        "signal_bindings": bindings,
                        "signal_relation": relation,
                    }
                )
                self.assert_rejected(group)

    def test_builder_rejects_source_evidence_upgrades_and_nonconstraint_contradictions(self) -> None:
        """Break caught: unverified source types gain verified status or ordinary facts contradict."""
        for source_type in (
            "cv",
            "professional_profile",
            "portfolio",
            "interview_notes",
            "candidate_statement",
        ):
            with self.subTest(source_type=source_type):
                upgraded = source_group()
                upgraded["sources"][1] = {
                    "source_type": source_type,
                    "evidence_state": "verified",
                }
                self.assert_rejected(upgraded)

        contradiction = source_group()
        contradiction["facts"][0]["signal_relation"] = "contradicts"
        self.assert_rejected(contradiction)
        allowed = source_group()
        allowed["facts"][0]["fact_type"] = "constraint"
        allowed["facts"][0]["signal_relation"] = "contradicts"
        self.assertEqual("contradicts", build(allowed)["facts"][0]["signal_relation"])

    def test_builder_rejects_fact_text_and_every_unknown_or_narrative_field_without_echo(self) -> None:
        """Break caught: caller prose or private-data fields enter input at any depth."""
        mutations = (
            lambda value: value.update({"candidate_id": "review-sensitive"}),
            lambda value: value["sources"][0].update({"email": "review-sensitive"}),
            lambda value: value["facts"][0].update({"fact_text": "review-sensitive"}),
            lambda value: value["facts"][0].update({"private_analytics": "review-sensitive"}),
            lambda value: value["facts"][0]["signal_bindings"][0].update(
                {"narrative": "review-sensitive"}
            ),
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                group = source_group()
                mutation(group)
                self.assert_rejected(group)

        legacy = source_group()
        for row in legacy["facts"]:
            row["fact_text"] = "review-sensitive"
            row["signals"] = [
                binding["signal"] for binding in row.pop("signal_bindings")
            ]
        self.assert_rejected(legacy)

    def test_builder_rejects_bounds_duplicates_ordering_and_unknown_ordinals(self) -> None:
        """Break caught: bounds, canonical uniqueness, or source-reference order weakens."""
        mutations = (
            lambda value: value.update({"sources": []}),
            lambda value: value.update({"facts": []}),
            lambda value: value["sources"].append(copy.deepcopy(value["sources"][0])),
            lambda value: value["facts"].append(copy.deepcopy(value["facts"][0])),
            lambda value: value["facts"][0].update({"source_ordinals": [2, 1]}),
            lambda value: value["facts"][0].update({"source_ordinals": [1, 1]}),
            lambda value: value["facts"][0].update({"source_ordinals": [4]}),
            lambda value: value.update({"captured_at": "2026-08-24T12:30:45+00:00"}),
            lambda value: value.update({"locale": "fr"}),
            lambda value: value.update({"sources": value["sources"] * 51}),
            lambda value: value.update({"facts": value["facts"] * 51}),
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                group = source_group()
                mutation(group)
                self.assert_rejected(group)

    def test_builder_validator_and_snapshot_capture_each_caller_mapping_once(self) -> None:
        """Break caught: validation rereads mutable caller mappings after the detached capture."""
        builder_group = OneShotMapping(source_group())
        artifact = build(builder_group)
        self.assertEqual(1, builder_group.reads)

        snapshot_group = OneShotMapping(source_group())
        self.assertEqual(
            artifact["source_snapshot"],
            BUILDER.snapshot_for_candidate_fact_matrix_v1(snapshot_group),
        )
        self.assertEqual(1, snapshot_group.reads)

        validator_value = OneShotMapping(copy.deepcopy(artifact))
        validator_group = OneShotMapping(source_group())
        self.assertEqual(
            [], VALIDATOR.validate_candidate_fact_matrix_v1(validator_value, validator_group)
        )
        self.assertEqual(1, validator_value.reads)
        self.assertEqual(1, validator_group.reads)

    def test_builder_detaches_mutable_inputs_and_rejects_recursive_and_exception_mappings(self) -> None:
        """Break caught: capture retains caller mutability or leaks an exceptional traversal."""
        group = source_group()
        artifact = build(group)
        group["facts"][0]["signal_bindings"][0]["signal"] = "review-sensitive"
        self.assertNotIn("review-sensitive", json.dumps(artifact, ensure_ascii=False))

        recursive = source_group()
        recursive["facts"].append(recursive)
        self.assert_rejected(recursive)

        class ExplodingMapping(Mapping[str, object]):
            def __iter__(self):
                raise RuntimeError("review-sensitive")

            def __len__(self) -> int:
                return 1

            def __getitem__(self, key: str) -> object:
                raise RuntimeError("review-sensitive")

            def items(self):
                raise RuntimeError("review-sensitive")

        self.assert_rejected(ExplodingMapping())

    def test_loader_rejects_duplicate_keys_and_artifact_fact_text_without_echo(self) -> None:
        """Break caught: ambiguous JSON or narrative artifact fields bypass structural loading."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            duplicate = root / "duplicate.json"
            duplicate.write_text(
                '{"schema_version":"candidate-fact-matrix-v1","schema_version":"review-sensitive"}',
                encoding="utf-8",
            )
            with self.assertRaises(VALIDATOR.CandidateFactMatrixLoadError) as caught:
                VALIDATOR.load_candidate_fact_matrix_v1(duplicate)
            self.assertEqual("cannot load candidate fact matrix", str(caught.exception))

            narrative = build()
            narrative["facts"][0]["fact_text"] = "review-sensitive"
            narrative_path = root / "narrative.json"
            narrative_path.write_text(json.dumps(narrative), encoding="utf-8")
            with self.assertRaises(VALIDATOR.CandidateFactMatrixLoadError) as caught:
                VALIDATOR.load_candidate_fact_matrix_v1(narrative_path)
            self.assertEqual("cannot load candidate fact matrix", str(caught.exception))

    def test_schema_closes_structural_rows_catalogs_and_conditionals(self) -> None:
        """Break caught: schema permits prose, open signals, crossed kinds, or vacuous facts."""
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(
            [
                "schema_version",
                "locale",
                "case_scope",
                "signal_vocabulary",
                "sources",
                "facts",
                "source_snapshot",
            ],
            schema["required"],
        )
        self.assertEqual(
            {"const": "candidate-claim-signal-v1"},
            schema["properties"]["signal_vocabulary"],
        )
        self.assertFalse(schema["properties"]["sources"]["items"]["additionalProperties"])
        fact_schema = schema["properties"]["facts"]["items"]
        self.assertFalse(fact_schema["additionalProperties"])
        self.assertEqual(
            {
                "fact_id",
                "fact_type",
                "evidence_state",
                "source_ids",
                "signal_bindings",
                "signal_relation",
                "conflict_state",
                "confidentiality",
            },
            set(fact_schema["properties"]),
        )
        bindings = fact_schema["properties"]["signal_bindings"]
        self.assertEqual((0, 20, True), (bindings["minItems"], bindings["maxItems"], bindings["uniqueItems"]))
        self.assertEqual(2, len(bindings["items"]["oneOf"]))
        self.assertEqual(
            ["requirement", "eligibility_gate"],
            [branch["properties"]["kind"]["const"] for branch in bindings["items"]["oneOf"]],
        )
        self.assertEqual(
            [list(REQUIREMENT_SIGNALS), list(ELIGIBILITY_GATE_SIGNALS)],
            [branch["properties"]["signal"]["enum"] for branch in bindings["items"]["oneOf"]],
        )
        self.assertEqual(20, schema["properties"]["sources"]["maxItems"])
        self.assertEqual(100, schema["properties"]["facts"]["maxItems"])
        self.assertGreaterEqual(len(fact_schema["allOf"]), 2)

    def test_validator_recomputes_the_complete_artifact_and_raw_snapshot(self) -> None:
        """Break caught: validator accepts any tampered projection or crossed raw source group."""
        group = source_group()
        artifact = build(group)
        self.assertEqual([], VALIDATOR.validate_candidate_fact_matrix_v1(artifact, group))

        mutations = (
            lambda value: value.update({"signal_vocabulary": "review-sensitive"}),
            lambda value: value["sources"][0].update({"captured_at": "2026-08-24T12:30:46Z"}),
            lambda value: value["facts"][0].update({"fact_id": "F-099"}),
            lambda value: value["facts"][0]["signal_bindings"][0].update(
                {"signal": "work_authorization"}
            ),
            lambda value: value.update(
                {"source_snapshot": "snap-candidate-facts-sha256-" + "0" * 64}
            ),
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                tampered = copy.deepcopy(artifact)
                mutation(tampered)
                self.assertEqual(
                    ["candidate fact matrix does not match validated sources"],
                    VALIDATOR.validate_candidate_fact_matrix_v1(tampered, group),
                )

        for field, value in (
            ("locale", "en"),
            ("captured_at", "2026-08-24T12:30:46Z"),
        ):
            with self.subTest(field=field):
                crossed = copy.deepcopy(group)
                crossed[field] = value
                self.assertEqual(
                    ["candidate fact matrix does not match validated sources"],
                    VALIDATOR.validate_candidate_fact_matrix_v1(artifact, crossed),
                )


if __name__ == "__main__":
    unittest.main()
