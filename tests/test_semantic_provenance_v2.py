"""Contracts for the closed candidate/market alignment v2 derivation."""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
import unittest
from collections.abc import Mapping
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "plugins" / "professional-growth-coach" / "scripts"
RESEARCH_FIXTURES = (
    ROOT / "tests" / "evals" / "with-skill" / "fixtures" / "target-vacancy-research"
)
DOSSIER_FIXTURES = (
    ROOT / "tests" / "evals" / "with-skill" / "fixtures" / "executive-career-dossier-v2"
)


def load_sibling(name: str):
    path = SCRIPTS / name
    specification = importlib.util.spec_from_file_location(f"semantic_v2_{path.stem}", path)
    if specification is None or specification.loader is None:
        raise AssertionError(f"cannot load sibling module: {path.name}")
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


ALIGNMENT_V2 = load_sibling("derive_candidate_market_alignment_v2.py")
RESEARCH = load_sibling("validate_target_vacancy_research.py")
DOSSIER_SNAPSHOT = load_sibling("dossier_snapshot.py")


def load_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError("fixture must be an object")
    return value


class CandidateMarketAlignmentV2Tests(unittest.TestCase):
    def complete_sources(self) -> tuple[dict[str, object], dict[str, object]]:
        return (
            load_json(RESEARCH_FIXTURES / "complete-five-es.json"),
            load_json(DOSSIER_FIXTURES / "scenario-a-es.json"),
        )

    def test_v2_normalization_is_exact_and_rejects_invalid_punctuation(self):
        accepted = {
            "Terraform": "terraform",
            "  Google Cloud  ": "google_cloud",
            "Site-Reliability": "site_reliability",
            "terra": "terra",
        }
        for raw, expected in accepted.items():
            with self.subTest(raw=raw):
                self.assertEqual(expected, ALIGNMENT_V2.normalize_signal_term(raw))
        for raw in ("C++", "node.js", "site/reliability", "", None, 7):
            with self.subTest(raw=raw):
                with self.assertRaisesRegex(ValueError, "technology term is invalid"):
                    ALIGNMENT_V2.normalize_signal_term(raw)

    def test_observability_cannot_borrow_verified_headline_evidence(self):
        research, dossier = self.complete_sources()
        alignment = ALIGNMENT_V2.derive_candidate_market_alignment_v2(research, dossier)
        row = next(item for item in alignment["signal_bindings"] if item["signal"] == "observability")
        self.assertEqual("unknown", row["support_state"])
        self.assertEqual([], row["claim_ids"])
        self.assertEqual([], row["evidence_ids"])

    def test_normalized_terra_does_not_bind_the_distinct_terraform_signal(self):
        research, dossier = self.complete_sources()
        dossier["requested_technology_terms"][0]["term"] = "terra"

        alignment = ALIGNMENT_V2.derive_candidate_market_alignment_v2(research, dossier)
        row = next(item for item in alignment["signal_bindings"] if item["signal"] == "terraform")

        self.assertEqual("unknown", row["support_state"])
        self.assertEqual([], row["claim_ids"])
        self.assertEqual([], row["evidence_ids"])
        self.assertEqual(["V-003-R-01"], row["requirement_ids"])
        self.assertEqual(["V-003"], row["vacancy_ids"])

    def test_complete_fixture_derives_only_terraform_support(self):
        research, dossier = self.complete_sources()
        result = ALIGNMENT_V2.derive_candidate_market_alignment_v2(research, dossier)
        supported = [
            (row["signal"], row["support_state"], row["claim_ids"], row["evidence_ids"])
            for row in result["signal_bindings"]
            if row["support_state"] != "unknown"
        ]
        self.assertEqual([("terraform", "candidate_reported_match", ["C-002"], ["E-004"])], supported)
        self.assertEqual(sorted(result["signal_bindings"], key=lambda row: row["signal"]), result["signal_bindings"])

    def test_complete_fixture_has_the_exact_market_and_candidate_unions(self):
        research, dossier = self.complete_sources()

        self.assertEqual(
            {
                "schema_version": "candidate-market-alignment-v2",
                "research_snapshot": RESEARCH.snapshot_for_market_dossier(research),
                "executive_dossier_snapshot": DOSSIER_SNAPSHOT.snapshot_for_dossier(dossier),
                "signal_bindings": [
                    {
                        "signal": "kubernetes",
                        "support_state": "unknown",
                        "claim_ids": [],
                        "evidence_ids": [],
                        "requirement_ids": ["V-002-R-01"],
                        "vacancy_ids": ["V-002"],
                    },
                    {
                        "signal": "linux",
                        "support_state": "unknown",
                        "claim_ids": [],
                        "evidence_ids": [],
                        "requirement_ids": ["V-005-R-01"],
                        "vacancy_ids": ["V-005"],
                    },
                    {
                        "signal": "observability",
                        "support_state": "unknown",
                        "claim_ids": [],
                        "evidence_ids": [],
                        "requirement_ids": ["V-004-R-01"],
                        "vacancy_ids": ["V-004"],
                    },
                    {
                        "signal": "python",
                        "support_state": "unknown",
                        "claim_ids": [],
                        "evidence_ids": [],
                        "requirement_ids": ["V-001-R-01"],
                        "vacancy_ids": ["V-001"],
                    },
                    {
                        "signal": "terraform",
                        "support_state": "candidate_reported_match",
                        "claim_ids": ["C-002"],
                        "evidence_ids": ["E-004"],
                        "requirement_ids": ["V-003-R-01"],
                        "vacancy_ids": ["V-003"],
                    },
                ],
                "privacy_boundary": "identity_free_structured_provenance_only",
            },
            ALIGNMENT_V2.derive_candidate_market_alignment_v2(research, dossier),
        )

    def test_invalid_source_shapes_fail_closed_without_echoing_sentinels(self):
        research, dossier = self.complete_sources()
        sentinel = "alignment-malicious-sentinel"
        cases: list[tuple[str, object, object]] = []

        duplicate_term = copy.deepcopy(dossier)
        duplicate_term["requested_technology_terms"].append(
            {"term": " Terraform ", "claim_ids": ["C-002"]}
        )
        cases.append(("duplicate normalized term", research, duplicate_term))

        missing_claim = copy.deepcopy(dossier)
        missing_claim["requested_technology_terms"][0]["claim_ids"] = ["C-999"]
        cases.append(("missing claim", research, missing_claim))

        missing_evidence = copy.deepcopy(dossier)
        missing_evidence["claims"][1]["evidence_ids"] = ["E-999"]
        cases.append(("missing evidence", research, missing_evidence))

        cyclic = {"marker": sentinel}
        cyclic["cycle"] = cyclic
        cases.append(("cyclic mapping", cyclic, dossier))

        depth_overflow: object = {"marker": sentinel}
        for _ in range(80):
            depth_overflow = {"child": depth_overflow}
        cases.append(("depth overflow", depth_overflow, dossier))

        oversized = copy.deepcopy(research)
        oversized["vacancies"] = [copy.deepcopy(research["vacancies"][0]) for _ in range(151)]
        cases.append(("oversized list", oversized, dossier))

        lone_surrogate = copy.deepcopy(dossier)
        lone_surrogate["requested_technology_terms"][0]["term"] = f"terraform{chr(0xD800)}{sentinel}"
        cases.append(("lone surrogate", research, lone_surrogate))

        for name, malformed_research, malformed_dossier in cases:
            with self.subTest(name=name):
                with self.assertRaisesRegex(ValueError, r"^alignment input is invalid$") as raised:
                    ALIGNMENT_V2.derive_candidate_market_alignment_v2(
                        malformed_research, malformed_dossier
                    )
                self.assertNotIn(sentinel, str(raised.exception))

    def test_wide_mapping_is_rejected_without_eager_scalar_enqueuing(self):
        class WideMapping(Mapping[str, object]):
            def __getitem__(self, key: str) -> object:
                raise KeyError(key)

            def __iter__(self):
                return iter(())

            def __len__(self) -> int:
                return ALIGNMENT_V2._MAX_NODES + 1

            def values(self):
                for index in range(ALIGNMENT_V2._MAX_NODES):
                    yield index
                raise AssertionError("wide input was eagerly traversed")

        self.assertFalse(ALIGNMENT_V2._safe_tree(WideMapping()))

    def test_inferred_evidence_remains_unknown_without_exposing_candidate_ids(self):
        research, dossier = self.complete_sources()
        dossier["evidence"][3]["state"] = "inferred"
        dossier["claims"][1]["state"] = "inferred"

        def lower_referenced_state(value: object) -> None:
            if isinstance(value, dict):
                if (
                    "E-004" in value.get("evidence_ids", [])
                    and value.get("evidence_state") == "candidate_reported"
                ):
                    value["evidence_state"] = "inferred"
                for nested in value.values():
                    lower_referenced_state(nested)
            elif isinstance(value, list):
                for nested in value:
                    lower_referenced_state(nested)

        lower_referenced_state(dossier)

        result = ALIGNMENT_V2.derive_candidate_market_alignment_v2(research, dossier)
        row = next(item for item in result["signal_bindings"] if item["signal"] == "terraform")

        self.assertEqual(
            {
                "signal": "terraform",
                "support_state": "unknown",
                "claim_ids": [],
                "evidence_ids": [],
                "requirement_ids": ["V-003-R-01"],
                "vacancy_ids": ["V-003"],
            },
            row,
        )

    def test_alignment_snapshot_rejects_reordered_or_duplicated_ids(self):
        research, dossier = self.complete_sources()
        canonical = ALIGNMENT_V2.derive_candidate_market_alignment_v2(research, dossier)
        self.assertRegex(
            ALIGNMENT_V2.snapshot_for_alignment_v2(canonical),
            r"^snap-alignment-sha256-[0-9a-f]{64}$",
        )
        cases = []
        duplicated = copy.deepcopy(canonical)
        duplicated["signal_bindings"][4]["claim_ids"] = ["C-002", "C-002"]
        cases.append(("duplicate claim ids", duplicated))
        duplicate_evidence = copy.deepcopy(canonical)
        duplicate_evidence["signal_bindings"][4]["evidence_ids"] = ["E-004", "E-004"]
        cases.append(("duplicate evidence ids", duplicate_evidence))
        duplicate_requirements = copy.deepcopy(canonical)
        duplicate_requirements["signal_bindings"][4]["requirement_ids"] = [
            "V-003-R-01",
            "V-003-R-01",
        ]
        cases.append(("duplicate requirement ids", duplicate_requirements))
        duplicate_vacancies = copy.deepcopy(canonical)
        duplicate_vacancies["signal_bindings"][4]["vacancy_ids"] = ["V-003", "V-003"]
        cases.append(("duplicate vacancy ids", duplicate_vacancies))
        reordered = copy.deepcopy(canonical)
        reordered["signal_bindings"] = list(reversed(reordered["signal_bindings"]))
        cases.append(("reordered bindings", reordered))
        for name, malformed in cases:
            with self.subTest(name=name):
                with self.assertRaisesRegex(ValueError, r"^alignment is invalid$"):
                    ALIGNMENT_V2.snapshot_for_alignment_v2(malformed)

    def test_alignment_snapshot_rejects_a_real_reordered_requirement_id_array(self):
        research, dossier = self.complete_sources()
        research["vacancies"][0]["requirements"][0]["signal"] = "terraform"
        canonical = ALIGNMENT_V2.derive_candidate_market_alignment_v2(research, dossier)
        terraform = next(
            row for row in canonical["signal_bindings"] if row["signal"] == "terraform"
        )
        self.assertEqual(["V-001-R-01", "V-003-R-01"], terraform["requirement_ids"])

        reordered = copy.deepcopy(canonical)
        target = next(
            row for row in reordered["signal_bindings"] if row["signal"] == "terraform"
        )
        target["requirement_ids"] = list(reversed(target["requirement_ids"]))

        with self.assertRaisesRegex(ValueError, r"^alignment is invalid$"):
            ALIGNMENT_V2.snapshot_for_alignment_v2(reordered)


if __name__ == "__main__":
    unittest.main()
