"""Behavioral contracts for the pure five-vacancy market dossier builder."""

from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "plugins" / "professional-growth-coach" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from build_career_market_learning_dossier import (  # noqa: E402
    alignment_score,
    build_market_dossier,
    recurrence_rows,
    rounded_percent,
)
from dossier_snapshot import snapshot_for_dossier  # noqa: E402
from validate_executive_career_dossier_v2 import validate_dossier  # noqa: E402
from validate_career_market_learning_dossier import validate_market_dossier  # noqa: E402
from validate_target_vacancy_research import (  # noqa: E402
    snapshot_for_market_dossier,
    validate_research,
)


RESEARCH_FIXTURES = (
    ROOT / "tests" / "evals" / "with-skill" / "fixtures" / "target-vacancy-research"
)
DOSSIER_FIXTURES = (
    ROOT / "tests" / "evals" / "with-skill" / "fixtures" / "executive-career-dossier-v2"
)
MARKET_DOSSIER_FIXTURES = (
    ROOT / "tests" / "evals" / "with-skill" / "fixtures" / "career-market-learning-dossier"
)


def load_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("fixture must be an object")
    return value


def source_pair(research_name: str, dossier_name: str) -> tuple[dict[str, object], dict[str, object]]:
    return (
        load_json(RESEARCH_FIXTURES / research_name),
        load_json(DOSSIER_FIXTURES / dossier_name),
    )


def alignment_for(
    research: dict[str, object],
    dossier: dict[str, object],
    states: dict[str, tuple[str, list[str]]] | None = None,
) -> dict[str, object]:
    configured = states or {
        "python": ("verified_match", ["E-001"]),
        "kubernetes": ("candidate_reported_match", ["E-003"]),
        "terraform": ("adjacent_evidence", ["E-004"]),
        "observability": ("unknown", []),
        "linux": ("explicit_gap", ["E-003"]),
    }
    signals = {
        requirement["signal"]
        for vacancy in research["vacancies"]
        for requirement in vacancy["requirements"]
    }
    return {
        "schema_version": "candidate-market-alignment-v1",
        "research_snapshot": snapshot_for_market_dossier(research),
        "executive_dossier_snapshot": snapshot_for_dossier(dossier),
        "signal_bindings": [
            {
                "signal": signal,
                "support_state": configured[signal][0],
                "evidence_ids": configured[signal][1],
            }
            for signal in sorted(signals)
        ],
        "privacy_boundary": "identity_free_evidence_references_only",
    }


class CareerMarketLearningDossierTests(unittest.TestCase):
    def test_integer_alignment_arithmetic_preserves_unknown_vs_gap(self) -> None:
        requirements = [
            {"signal": "one", "importance": "must_have"},
            {"signal": "two", "importance": "must_have"},
            {"signal": "three", "importance": "preferred"},
            {"signal": "four", "importance": "responsibility_only"},
        ]
        bindings = [
            {"signal": "one", "support_state": "verified_match", "evidence_ids": ["E-001"]},
            {"signal": "two", "support_state": "adjacent_evidence", "evidence_ids": ["E-002"]},
            {"signal": "three", "support_state": "unknown", "evidence_ids": []},
            {"signal": "four", "support_state": "explicit_gap", "evidence_ids": ["E-003"]},
        ]

        earned, maximum, known = alignment_score(requirements, bindings)
        self.assertEqual((6, 10, 8), (earned, maximum, known))
        self.assertEqual(60, rounded_percent(earned, maximum))
        self.assertEqual(80, rounded_percent(known, maximum))

        bindings[2] = {
            "signal": "three",
            "support_state": "explicit_gap",
            "evidence_ids": ["E-004"],
        }
        earned, maximum, known = alignment_score(requirements, bindings)
        self.assertEqual((6, 10, 10), (earned, maximum, known))
        self.assertEqual(60, rounded_percent(earned, maximum))
        self.assertEqual(100, rounded_percent(known, maximum))

    def test_recurrence_uses_dynamic_sample_size_without_sample_wide_score(self) -> None:
        vacancies = [
            {
                "vacancy_id": f"V-{index:03d}",
                "requirements": ([{"signal": "kubernetes", "importance": "must_have"}] if index <= 3 else []),
            }
            for index in range(1, 6)
        ]
        bindings = [
            {"signal": "kubernetes", "support_state": "verified_match", "evidence_ids": ["E-001"]}
        ]

        rows = recurrence_rows(vacancies, bindings)
        self.assertEqual(3, rows[0]["occurrences"])
        self.assertEqual(5, rows[0]["sample_size"])
        self.assertEqual("3/5", rows[0]["display_fraction"])
        self.assertNotIn("alignment_percent", rows[0])
        self.assertNotIn("sample_score", rows[0])

        rows = recurrence_rows(vacancies[:4], bindings)
        self.assertEqual((3, 4, "3/4"), (rows[0]["occurrences"], rows[0]["sample_size"], rows[0]["display_fraction"]))
        self.assertEqual([], recurrence_rows([], bindings))

    def test_builder_binds_exact_snapshots_scores_orders_and_does_not_mutate_inputs(self) -> None:
        research, dossier = source_pair("complete-five-es.json", "scenario-a-es.json")
        alignment = alignment_for(research, dossier)
        before = copy.deepcopy((research, dossier, alignment))

        result = build_market_dossier(research, dossier, alignment)

        self.assertEqual(before, (research, dossier, alignment))
        self.assertEqual([], validate_market_dossier(result, research, dossier, alignment))
        self.assertEqual("career-market-learning-dossier-v1", result["schema_version"])
        self.assertEqual(("es", "2026-08-13", "complete"), (result["locale"], result["as_of_date"], result["state"]))
        self.assertEqual(snapshot_for_market_dossier(research), result["source_research_snapshot"])
        self.assertEqual(snapshot_for_dossier(dossier), result["source_executive_dossier_snapshot"])
        self.assertEqual("not_evaluated", result["learning_state"])
        self.assertEqual([], result["learning_decisions"])
        self.assertIs(result["no_external_action"], True)
        self.assertEqual(
            sorted(result["vacancies"], key=lambda row: (-row["alignment_percent"], row["vacancy_id"])),
            result["vacancies"],
        )
        self.assertEqual([row["vacancy_id"] for row in result["vacancies"]], [cell["vacancy_id"] for cell in result["matrix_rows"][0]["cells"]])
        self.assertTrue(all("source_paraphrase" not in card for card in result["vacancies"]))
        self.assertEqual("directional_documented_evidence_not_hiring_fit", result["vacancies"][0]["interpretation"])

    def test_output_bands_use_coverage_gate_before_alignment_cut_points(self) -> None:
        research, dossier = source_pair("complete-five-es.json", "scenario-a-es.json")
        states = {
            "python": ("verified_match", ["E-001"]),
            "kubernetes": ("candidate_reported_match", ["E-003"]),
            "terraform": ("adjacent_evidence", ["E-004"]),
            "observability": ("unknown", []),
            "linux": ("explicit_gap", ["E-003"]),
        }
        result = build_market_dossier(research, dossier, alignment_for(research, dossier, states))
        by_id = {row["vacancy_id"]: row for row in result["vacancies"]}
        self.assertEqual((4, 4, 4, 100, 100, "higher_documented_alignment"), tuple(by_id["V-001"][field] for field in ("earned_points", "maximum_points", "known_points", "alignment_percent", "evidence_coverage_percent", "qualitative_band")))
        self.assertEqual("moderate_documented_alignment", by_id["V-003"]["qualitative_band"])
        self.assertEqual("insufficient_evidence", by_id["V-004"]["qualitative_band"])

    def test_zero_vacancy_state_has_no_rows_or_sample_score(self) -> None:
        research, dossier = source_pair("unavailable-es.json", "scenario-a-es.json")
        result = build_market_dossier(research, dossier, alignment_for(research, dossier))
        self.assertEqual(
            [],
            validate_market_dossier(
                result, research, dossier, alignment_for(research, dossier)
            ),
        )
        self.assertEqual([], result["vacancies"])
        self.assertEqual([], result["matrix_rows"])
        self.assertEqual([], result["recurrence_rows"])
        self.assertEqual(0, result["search_summary"]["vacancy_count"])
        self.assertNotIn("alignment_percent", result["search_summary"])
        self.assertNotIn("sample_score", result["search_summary"])

    def test_committed_state_fixtures_are_exact_reproducible_snapshots(self) -> None:
        cases = (
            ("complete-five-es.json", "scenario-a-es.json"),
            ("limited-four-en.json", "scenario-c-en.json"),
            ("unavailable-es.json", "scenario-a-es.json"),
        )
        for research_name, dossier_name in cases:
            with self.subTest(research=research_name):
                research, dossier = source_pair(research_name, dossier_name)
                expected = load_json(MARKET_DOSSIER_FIXTURES / research_name)
                self.assertEqual(
                    expected,
                    build_market_dossier(research, dossier, alignment_for(research, dossier)),
                )

    def test_complete_bounded_search_output_validates_when_task1_accepts_it(self) -> None:
        research, dossier = source_pair("complete-five-es.json", "scenario-a-es.json")
        research["search_limit"]["limit_reason"] = "bounded_search_exhausted"
        research["search_limit"]["limitation"] = "Bounded search completed with five vacancies."
        alignment = alignment_for(research, dossier)

        result = build_market_dossier(research, dossier, alignment)

        self.assertEqual("complete", result["state"])
        self.assertEqual("bounded_search_exhausted", result["search_summary"]["limit_reason"])
        self.assertEqual([], validate_market_dossier(result, research, dossier, alignment))

    def test_obfuscated_public_identity_cannot_reach_market_builder(self) -> None:
        research, dossier = source_pair("complete-five-es.json", "scenario-a-es.json")
        cases = (
            ("employers", 0, "display_name", "john.smith"),
            ("vacancies", 0, "title", "%6a%6f%68%6e%20%73%6d%69%74%68 engineer"),
            ("vacancies", 0, "duplicate_fingerprint", "johnsmith-engineer"),
            ("employers", 0, "display_name", "margaret%20thatcher"),
            ("vacancies", 0, "title", "rachel&#46;green engineer"),
            ("vacancies", 0, "duplicate_fingerprint", "rachelgreen-engineer"),
            ("vacancies", 0, "title", "alexander-hamilton engineer"),
            ("vacancies", 0, "title", "alexanderhamilton engineer"),
            ("vacancies", 0, "title", "al3xander-h4milton engineer"),
            ("vacancies", 0, "title", "samanthabrown"),
            ("vacancies", 0, "title", "patrickmiller engineer"),
            ("vacancies", 0, "location", "victoria.grant"),
            ("vacancies", 0, "duplicate_fingerprint", "thomasanderson-engineer"),
            (
                "vacancies",
                0,
                "source_url",
                "https://www.rfc-editor.org/rfc/rfc2606#fixture-v-001/margaret%20thatcher",
            ),
        )
        for collection, index, field, marker in cases:
            with self.subTest(field=field, marker=marker):
                mutated = copy.deepcopy(research)
                mutated[collection][index][field] = marker
                alignment = alignment_for(mutated, dossier)
                with self.assertRaises(ValueError) as raised:
                    build_market_dossier(mutated, dossier, alignment)
                self.assertNotIn(marker, str(raised.exception))

    def test_trusted_validator_rejects_cross_artifact_locale_mismatch(self) -> None:
        research, es_dossier = source_pair("complete-five-es.json", "scenario-a-es.json")
        _, en_dossier = source_pair("complete-five-es.json", "scenario-c-en.json")
        es_alignment = alignment_for(research, es_dossier)
        mismatched_alignment = alignment_for(research, en_dossier)
        artifact = build_market_dossier(research, es_dossier, es_alignment)
        artifact["source_executive_dossier_snapshot"] = mismatched_alignment[
            "executive_dossier_snapshot"
        ]

        self.assertEqual([], validate_dossier(en_dossier))
        self.assertEqual([], validate_research(research))
        with self.assertRaisesRegex(ValueError, "locale"):
            build_market_dossier(research, en_dossier, mismatched_alignment)
        self.assertTrue(
            validate_market_dossier(
                artifact, research, en_dossier, mismatched_alignment
            )
        )

    def test_builder_rejects_stale_snapshots_unknown_ids_and_incompatible_evidence(self) -> None:
        research, dossier = source_pair("complete-five-es.json", "scenario-a-es.json")
        valid = alignment_for(research, dossier)
        mutations = []
        stale_research = copy.deepcopy(valid); stale_research["research_snapshot"] = "snap-market-sha256-" + "0" * 64; mutations.append(stale_research)
        stale_dossier = copy.deepcopy(valid); stale_dossier["executive_dossier_snapshot"] = "snap-dossier-sha256-" + "0" * 64; mutations.append(stale_dossier)
        unknown_id = copy.deepcopy(valid); unknown_id["signal_bindings"][0]["evidence_ids"] = ["E-999"]; mutations.append(unknown_id)
        incompatible = copy.deepcopy(valid); incompatible["signal_bindings"][0].update({"support_state": "verified_match", "evidence_ids": ["E-003"]}); mutations.append(incompatible)
        missing_signal = copy.deepcopy(valid); missing_signal["signal_bindings"].pop(); mutations.append(missing_signal)
        duplicate_signal = copy.deepcopy(valid); duplicate_signal["signal_bindings"].append(copy.deepcopy(duplicate_signal["signal_bindings"][0])); mutations.append(duplicate_signal)
        unknown_with_evidence = copy.deepcopy(valid); unknown_with_evidence["signal_bindings"][0].update({"support_state": "unknown", "evidence_ids": ["E-001"]}); mutations.append(unknown_with_evidence)
        gap_without_evidence = copy.deepcopy(valid); gap_without_evidence["signal_bindings"][0].update({"support_state": "explicit_gap", "evidence_ids": []}); mutations.append(gap_without_evidence)
        for mutated in mutations:
            with self.subTest(mutated=mutated["signal_bindings"][:1]):
                with self.assertRaisesRegex(ValueError, "^(research|dossier|alignment|signal binding)"):
                    build_market_dossier(research, dossier, mutated)

    def test_builder_rejects_locale_mismatch_and_malformed_values_without_echo(self) -> None:
        research, dossier = source_pair("complete-five-es.json", "scenario-c-en.json")
        alignment = alignment_for(research, dossier)
        with self.assertRaisesRegex(ValueError, "locale"):
            build_market_dossier(research, dossier, alignment)

        private_value = "private-person@example.invalid\u0007"
        malformed = alignment_for(research, source_pair("complete-five-es.json", "scenario-a-es.json")[1])
        malformed["signal_bindings"][0]["signal"] = [private_value]
        with self.assertRaises(ValueError) as captured:
            build_market_dossier(research, source_pair("complete-five-es.json", "scenario-a-es.json")[1], malformed)
        self.assertNotIn(private_value, str(captured.exception))

    def test_validator_rejects_every_derived_mutation_order_and_state_coupling(self) -> None:
        research, dossier = source_pair("complete-five-es.json", "scenario-a-es.json")
        alignment = alignment_for(research, dossier)
        result = build_market_dossier(research, dossier, alignment)
        mutations: list[dict[str, object]] = []
        for field in ("earned_points", "maximum_points", "known_points", "alignment_percent", "evidence_coverage_percent"):
            bad = copy.deepcopy(result); bad["vacancies"][0][field] += 1; mutations.append(bad)
        bad = copy.deepcopy(result); bad["vacancies"][0]["qualitative_band"] = "lower_documented_alignment"; mutations.append(bad)
        bad = copy.deepcopy(result); bad["vacancies"].reverse(); mutations.append(bad)
        bad = copy.deepcopy(result); bad["matrix_rows"][0]["cells"].reverse(); mutations.append(bad)
        bad = copy.deepcopy(result); bad["matrix_rows"][0]["cells"][0]["required"] = not bad["matrix_rows"][0]["cells"][0]["required"]; mutations.append(bad)
        bad = copy.deepcopy(result); bad["recurrence_rows"][0]["occurrences"] += 1; mutations.append(bad)
        bad = copy.deepcopy(result); bad["recurrence_rows"][0]["sample_size"] = 4; mutations.append(bad)
        bad = copy.deepcopy(result); bad["recurrence_rows"][0]["display_fraction"] = "3/4"; mutations.append(bad)
        bad = copy.deepcopy(result); bad["recurrence_rows"].reverse(); mutations.append(bad)
        bad = copy.deepcopy(result); bad["locale"] = "en"; mutations.append(bad)
        bad = copy.deepcopy(result); bad["as_of_date"] = "2026-08-12"; mutations.append(bad)
        bad = copy.deepcopy(result); bad["state"] = "limited_market_evidence"; mutations.append(bad)
        bad = copy.deepcopy(result); bad["source_research_snapshot"] = "snap-market-sha256-" + "0" * 64; mutations.append(bad)
        bad = copy.deepcopy(result); bad["source_executive_dossier_snapshot"] = "snap-dossier-sha256-" + "0" * 64; mutations.append(bad)
        bad = copy.deepcopy(result); bad["learning_state"] = "evaluated"; mutations.append(bad)
        bad = copy.deepcopy(result); bad["learning_decisions"] = [{}]; mutations.append(bad)
        for mutated in mutations:
            with self.subTest(index=len(mutations)):
                self.assertTrue(validate_market_dossier(mutated, research, dossier, alignment))

    def test_trusted_validator_rejects_source_consistent_provenance_mutations(self) -> None:
        research, dossier = source_pair("complete-five-es.json", "scenario-a-es.json")
        alignment = alignment_for(research, dossier)
        result = build_market_dossier(research, dossier, alignment)
        mutations: list[
            tuple[str, dict[str, object], dict[str, object]]
        ] = []

        bad = copy.deepcopy(result)
        required_cell = next(
            cell
            for row in bad["matrix_rows"]
            for cell in row["cells"]
            if cell["requirements"]
        )
        required_cell["requirements"][0]["requirement_id"] = (
            required_cell["vacancy_id"] + "-R-99"
        )
        mutations.append(("requirement_id", bad, alignment))

        bad = copy.deepcopy(result)
        required_cell = next(
            cell
            for row in bad["matrix_rows"]
            for cell in row["cells"]
            if cell["requirements"]
        )
        required_cell["requirements"][0]["source_paraphrase"] = (
            "Different bounded public requirement paraphrase."
        )
        mutations.append(("source_paraphrase", bad, alignment))

        bad = copy.deepcopy(result)
        signal = bad["matrix_rows"][0]["signal"]
        bad["matrix_rows"][0]["evidence_ids"] = ["E-999"]
        next(row for row in bad["recurrence_rows"] if row["signal"] == signal)[
            "evidence_ids"
        ] = ["E-999"]
        bad_alignment = copy.deepcopy(alignment)
        next(
            binding
            for binding in bad_alignment["signal_bindings"]
            if binding["signal"] == signal
        )["evidence_ids"] = ["E-999"]
        mutations.append(("unknown_evidence_id", bad, bad_alignment))

        for field, prefix in (
            ("source_research_snapshot", "snap-market-sha256-"),
            ("source_executive_dossier_snapshot", "snap-dossier-sha256-"),
        ):
            bad = copy.deepcopy(result)
            bad[field] = prefix + "0" * 64
            bad_alignment = copy.deepcopy(alignment)
            alignment_field = (
                "research_snapshot"
                if field == "source_research_snapshot"
                else "executive_dossier_snapshot"
            )
            bad_alignment[alignment_field] = prefix + "0" * 64
            mutations.append((field, bad, bad_alignment))

        bad = copy.deepcopy(result)
        bad["vacancies"][0]["title"] = "Altered public vacancy title"
        mutations.append(("public_metadata", bad, alignment))

        for label, mutated, validation_alignment in mutations:
            with self.subTest(label=label):
                self.assertTrue(
                    validate_market_dossier(
                        mutated, research, dossier, validation_alignment
                    )
                )

    def test_validator_is_total_bounded_and_non_echoing_for_private_or_malformed_values(self) -> None:
        research, dossier = source_pair("complete-five-es.json", "scenario-a-es.json")
        alignment = alignment_for(research, dossier)
        result = build_market_dossier(research, dossier, alignment)
        sentinel = "private-person@example.invalid\u0007"
        private = copy.deepcopy(result)
        private["vacancies"][0]["employer"] = sentinel
        malformed = copy.deepcopy(result)
        malformed["matrix_rows"][0]["evidence_ids"] = [[sentinel]]
        recursive: dict[str, object] = {}
        recursive["self"] = recursive
        for value in (private, malformed, recursive, [sentinel]):
            errors = validate_market_dossier(value, research, dossier, alignment)
            self.assertTrue(errors)
            rendered = "\n".join(errors)
            self.assertLessEqual(len(rendered), 4096)
            self.assertNotIn(sentinel, rendered)


if __name__ == "__main__":
    unittest.main()
