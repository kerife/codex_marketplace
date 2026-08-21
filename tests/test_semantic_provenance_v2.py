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
PROVIDER_FIXTURES = (
    ROOT / "tests" / "evals" / "with-skill" / "fixtures" / "career-learning-provider-research"
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
MARKET_V2_BUILDER = load_sibling("build_career_market_learning_dossier_v2.py")
MARKET_V2_VALIDATOR = load_sibling("validate_career_market_learning_dossier_v2.py")
RESEARCH = load_sibling("validate_target_vacancy_research.py")
DOSSIER_SNAPSHOT = load_sibling("dossier_snapshot.py")
PROVIDER_VALIDATOR = load_sibling("validate_career_learning_provider_research.py")
LEARNING_V2_PROJECTION = load_sibling("project_career_learning_decision_v2.py")
LEARNING_V2_BUILDER = load_sibling("build_career_learning_decision_v2.py")
LEARNING_V2_VALIDATOR = load_sibling("validate_career_learning_decision_v2.py")


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


class CareerMarketLearningDossierV2Tests(unittest.TestCase):
    def complete_sources(self) -> tuple[dict[str, object], dict[str, object]]:
        return (
            load_json(RESEARCH_FIXTURES / "complete-five-es.json"),
            load_json(DOSSIER_FIXTURES / "scenario-a-es.json"),
        )

    def source_pair(self, research_name: str, dossier_name: str) -> tuple[dict[str, object], dict[str, object]]:
        return (
            load_json(RESEARCH_FIXTURES / research_name),
            load_json(DOSSIER_FIXTURES / dossier_name),
        )

    def test_market_v2_recomputes_alignment_and_rejects_reference_tampering(self):
        research, dossier = self.complete_sources()
        market = MARKET_V2_BUILDER.build_market_dossier_v2(research, dossier)
        self.assertEqual([], MARKET_V2_VALIDATOR.validate_market_dossier_v2(market, research, dossier))
        terraform = next(row for row in market["matrix_rows"] if row["signal"] == "terraform")
        self.assertEqual(
            {
                "signal": "terraform",
                "support_state": "candidate_reported_match",
                "claim_ids": ["C-002"],
                "evidence_ids": ["E-004"],
                "requirement_ids": ["V-003-R-01"],
                "vacancy_ids": ["V-003"],
            },
            {field: terraform[field] for field in ("signal", "support_state", "claim_ids", "evidence_ids", "requirement_ids", "vacancy_ids")},
        )

    def test_market_v2_rejects_all_binding_array_mutations_from_a_multi_id_source(self):
        research, dossier = self.complete_sources()
        research["vacancies"][0]["requirements"][0]["signal"] = "terraform"
        dossier["requested_technology_terms"][0]["claim_ids"] = ["C-001", "C-002"]
        market = MARKET_V2_BUILDER.build_market_dossier_v2(research, dossier)
        terraform = next(row for row in market["matrix_rows"] if row["signal"] == "terraform")
        self.assertEqual(
            {
                "claim_ids": ["C-001", "C-002"],
                "evidence_ids": ["E-001", "E-002", "E-004"],
                "requirement_ids": ["V-001-R-01", "V-003-R-01"],
                "vacancy_ids": ["V-001", "V-003"],
            },
            {field: terraform[field] for field in ("claim_ids", "evidence_ids", "requirement_ids", "vacancy_ids")},
        )
        substitutions = {
            "claim_ids": "C-003",
            "evidence_ids": "E-003",
            "requirement_ids": "V-002-R-01",
            "vacancy_ids": "V-002",
        }
        for field, replacement in substitutions.items():
            originals = terraform[field]
            mutations = {
                "duplicate": originals + [originals[0]],
                "reorder": list(reversed(originals)),
                "delete": originals[:-1],
                "substitute": [replacement, *originals[1:]],
            }
            for name, altered_ids in mutations.items():
                with self.subTest(field=field, mutation=name):
                    altered = copy.deepcopy(market)
                    next(row for row in altered["matrix_rows"] if row["signal"] == "terraform")[field] = altered_ids
                    errors = MARKET_V2_VALIDATOR.validate_market_dossier_v2(altered, research, dossier)
                    self.assertEqual(["market dossier does not match validated sources"], errors)

    def test_market_v2_public_boundaries_do_not_echo_copy_failures(self):
        research, dossier = self.complete_sources()
        market = MARKET_V2_BUILDER.build_market_dossier_v2(research, dossier)
        sentinel = "copy-failure-sentinel"

        class CopyBomb(dict[str, object]):
            def __deepcopy__(self, memo: dict[int, object]):
                raise RuntimeError(sentinel)

        with self.assertRaisesRegex(ValueError, r"^market dossier v2 is invalid$") as raised:
            MARKET_V2_BUILDER.build_market_dossier_v2(CopyBomb(research), dossier)
        self.assertNotIn(sentinel, str(raised.exception))
        errors = MARKET_V2_VALIDATOR.validate_market_dossier_v2(CopyBomb(market), research, dossier)
        self.assertEqual(["market dossier does not match validated sources"], errors)
        self.assertNotIn(sentinel, "\n".join(errors))

    def test_market_v2_complete_scores_order_and_snapshot_are_deterministic(self):
        research, dossier = self.complete_sources()
        market = MARKET_V2_BUILDER.build_market_dossier_v2(research, dossier)

        self.assertEqual("career-market-learning-dossier-v2", market["schema_version"])
        self.assertRegex(market["source_alignment_snapshot"], r"^snap-alignment-sha256-[0-9a-f]{64}$")
        self.assertEqual(
            [
                ("V-003", 4, 4, 4, 100, 100),
                ("V-001", 0, 4, 0, 0, 0),
                ("V-002", 0, 4, 0, 0, 0),
                ("V-004", 0, 2, 0, 0, 0),
                ("V-005", 0, 0, 0, 0, 0),
            ],
            [
                tuple(card[field] for field in ("vacancy_id", "earned_points", "maximum_points", "known_points", "alignment_percent", "evidence_coverage_percent"))
                for card in market["vacancies"]
            ],
        )
        self.assertEqual(
            sorted(market["matrix_rows"], key=lambda row: row["signal"]),
            market["matrix_rows"],
        )
        self.assertEqual(
            MARKET_V2_BUILDER.snapshot_for_market_dossier_v2(market),
            MARKET_V2_BUILDER.snapshot_for_market_dossier_v2(copy.deepcopy(market)),
        )

    def test_market_v2_rejects_ordering_and_shape_tampering(self):
        research, dossier = self.complete_sources()
        market = MARKET_V2_BUILDER.build_market_dossier_v2(research, dossier)
        mutations: list[dict[str, object]] = []
        reordered = copy.deepcopy(market); reordered["matrix_rows"].reverse(); mutations.append(reordered)
        deleted = copy.deepcopy(market); deleted["matrix_rows"].pop(); mutations.append(deleted)
        duplicated = copy.deepcopy(market); duplicated["matrix_rows"].append(copy.deepcopy(duplicated["matrix_rows"][0])); mutations.append(duplicated)
        synthetic_alignment = copy.deepcopy(market); synthetic_alignment["alignment"] = ALIGNMENT_V2.derive_candidate_market_alignment_v2(research, dossier); mutations.append(synthetic_alignment)
        for altered in mutations:
            with self.subTest(altered=altered["matrix_rows"][:1]):
                self.assertEqual(
                    ["market dossier does not match validated sources"],
                    MARKET_V2_VALIDATOR.validate_market_dossier_v2(altered, research, dossier),
                )

    def test_market_v2_rejects_stale_and_crossed_sources(self):
        research, dossier = self.complete_sources()
        market = MARKET_V2_BUILDER.build_market_dossier_v2(research, dossier)
        stale = copy.deepcopy(research)
        stale["vacancies"][0]["title"] = "Stale public vacancy title"
        _, other_dossier = self.source_pair("complete-five-es.json", "scenario-c-en.json")
        for sources in ((stale, dossier), (research, other_dossier)):
            with self.subTest(locale=sources[1]["locale"]):
                self.assertEqual(
                    ["market dossier does not match validated sources"],
                    MARKET_V2_VALIDATOR.validate_market_dossier_v2(market, *sources),
                )

    def test_market_v2_unavailable_has_no_candidate_support(self):
        research, dossier = self.source_pair("unavailable-es.json", "scenario-a-es.json")
        market = MARKET_V2_BUILDER.build_market_dossier_v2(research, dossier)
        expected_alignment = ALIGNMENT_V2.derive_candidate_market_alignment_v2(research, dossier)
        self.assertEqual(
            ALIGNMENT_V2.snapshot_for_alignment_v2(expected_alignment),
            market["source_alignment_snapshot"],
        )
        self.assertEqual([], market["vacancies"])
        self.assertEqual([], market["matrix_rows"])
        self.assertEqual([], market["recurrence_rows"])
        self.assertEqual([], MARKET_V2_VALIDATOR.validate_market_dossier_v2(market, research, dossier))


class CareerLearningProviderResearchTests(unittest.TestCase):
    def provider_fixture(self, name: str) -> dict[str, object]:
        return load_json(PROVIDER_FIXTURES / name)

    def assert_invalid_without_echo(self, value: object, sentinel: str) -> None:
        errors = PROVIDER_VALIDATOR.validate_provider_research(value)
        self.assertTrue(errors)
        rendered = "\n".join(errors)
        self.assertNotIn(sentinel, rendered)
        self.assertLessEqual(len(rendered.encode("utf-8")), 16_384)

    def test_provider_research_is_independent_closed_and_snapshot_bound(self):
        provider = self.provider_fixture("complete-es.json")
        self.assertEqual([], PROVIDER_VALIDATOR.validate_provider_research(provider))
        self.assertRegex(
            PROVIDER_VALIDATOR.snapshot_for_provider_research(provider),
            r"\Asnap-provider-sha256-[0-9a-f]{64}\Z",
        )
        terraform = next(row for row in provider["options"] if row["option_id"] == "LP-001")
        self.assertEqual(["terraform"], terraform["covered_signals"])
        argo = next(row for row in provider["options"] if row["option_id"] == "LP-002")
        self.assertEqual([], argo["covered_signals"])

    def test_provider_research_rejects_caller_semantics_and_private_values_without_echo(self):
        provider = self.provider_fixture("complete-es.json")
        for field, value in (
            ("provider", "Synthetic Candidate"),
            ("url", "https://www.cncf.io/terraform-course"),
            ("coverage_basis", "caller_claim"),
        ):
            with self.subTest(field=field):
                altered = copy.deepcopy(provider)
                altered["options"][0][field] = value
                self.assert_invalid_without_echo(altered, str(value))

    def test_provider_research_rejects_empty_and_nonempty_url_userinfo_without_echo(self):
        provider = self.provider_fixture("complete-es.json")
        sentinel = "provider-userinfo-sentinel"
        for name, url in (
            ("empty username", "https://@developer.hashicorp.com/terraform/tutorials"),
            ("empty username and password", "https://:@developer.hashicorp.com/terraform/tutorials"),
            ("nonempty userinfo", f"https://{sentinel}@developer.hashicorp.com/terraform/tutorials"),
        ):
            with self.subTest(name=name):
                altered = copy.deepcopy(provider)
                altered["options"][0]["url"] = url
                self.assert_invalid_without_echo(altered, sentinel)

    def test_provider_research_requires_strict_iso_dates_without_echo(self):
        provider = self.provider_fixture("complete-es.json")
        sentinel = "provider-date-sentinel"
        invalid_values: tuple[object, ...] = (
            "20260821",
            "2026-W34-5",
            "2026-02-30",
            {sentinel: True},
        )
        for field in ("as_of_date", "source_date", "access_date"):
            for value in invalid_values:
                with self.subTest(field=field, value=repr(value)):
                    altered = copy.deepcopy(provider)
                    target = altered if field == "as_of_date" else altered["options"][0]
                    target[field] = value
                    self.assert_invalid_without_echo(altered, sentinel)

    def test_provider_research_rejects_private_url_components_after_decoding_without_echo(self):
        provider = self.provider_fixture("complete-es.json")
        sentinel = "provider-url-component-sentinel"
        cases = (
            ("direct contact path", f"https://developer.hashicorp.com/contact-{sentinel}@example.invalid"),
            ("encoded contact path", f"https://developer.hashicorp.com/contact-{sentinel}%40example.invalid"),
            ("direct person query", f"https://developer.hashicorp.com/?person=Jane Smith {sentinel}"),
            ("encoded person query", f"https://developer.hashicorp.com/?person=Jane%20Smith%20{sentinel}"),
            ("direct local path", f"https://developer.hashicorp.com/Users/{sentinel}"),
            ("encoded local path", f"https://developer.hashicorp.com/%55sers/{sentinel}"),
            ("html encoded contact fragment", f"https://developer.hashicorp.com/#contact-{sentinel}%26%2364%3Bexample.invalid"),
        )
        for name, url in cases:
            with self.subTest(name=name):
                altered = copy.deepcopy(provider)
                altered["options"][0]["url"] = url
                self.assert_invalid_without_echo(altered, sentinel)

    def test_provider_research_rejects_closed_structure_and_semantic_mutations(self):
        provider = self.provider_fixture("complete-es.json")
        sentinel = "provider-malicious-sentinel"
        cases: list[tuple[str, object]] = []

        duplicate = copy.deepcopy(provider)
        duplicate["options"][1]["option_id"] = "LP-001"
        cases.append(("duplicate option id", duplicate))
        unsorted = copy.deepcopy(provider)
        unsorted["options"][0]["covered_signals"] = ["terraform", "ansible"]
        cases.append(("unsorted signals", unsorted))
        repeated = copy.deepcopy(provider)
        repeated["options"][0]["covered_signals"] = ["terraform", "terraform"]
        cases.append(("duplicate signals", repeated))
        bad_signal = copy.deepcopy(provider)
        bad_signal["options"][0]["covered_signals"] = [sentinel]
        cases.append(("invalid signal", bad_signal))
        future = copy.deepcopy(provider)
        future["options"][0]["source_date"] = "2099-01-01"
        cases.append(("future date", future))
        non_https = copy.deepcopy(provider)
        non_https["options"][0]["url"] = f"http://{sentinel}.invalid"
        cases.append(("non https", non_https))
        userinfo = copy.deepcopy(provider)
        userinfo["options"][0]["url"] = f"https://{sentinel}@developer.hashicorp.com/learn"
        cases.append(("credential url", userinfo))
        host_mismatch = copy.deepcopy(provider)
        host_mismatch["options"][0]["url"] = f"https://{sentinel}.invalid/terraform"
        cases.append(("wrong official host", host_mismatch))
        unknown_provider = copy.deepcopy(provider)
        unknown_provider["options"][0]["provider"] = sentinel
        cases.append(("unreviewed provider", unknown_provider))
        state = copy.deepcopy(provider)
        state["state"] = "unavailable"
        cases.append(("unavailable root with options", state))
        unavailable_coverage = copy.deepcopy(provider)
        unavailable_coverage["options"][0]["source_state"] = "unavailable"
        unavailable_coverage["options"][0]["availability"] = "unavailable"
        cases.append(("unavailable option coverage", unavailable_coverage))
        bad_basis = copy.deepcopy(provider)
        bad_basis["options"][0]["coverage_basis"] = sentinel
        cases.append(("coverage basis", bad_basis))
        arbitrary = copy.deepcopy(provider)
        arbitrary["options"][0][sentinel] = True
        cases.append(("arbitrary field", arbitrary))
        controls = copy.deepcopy(provider)
        controls["options"][0]["option"] = f"Safe {chr(0x202e)} {sentinel}"
        cases.append(("raw control", controls))
        surrogate = copy.deepcopy(provider)
        surrogate["options"][0]["source_title"] = f"Safe {chr(0xD800)} {sentinel}"
        cases.append(("lone surrogate", surrogate))
        contact = copy.deepcopy(provider)
        contact["options"][0]["unknowns"] = f"contact {sentinel}@example.invalid"
        cases.append(("contact data", contact))
        person = copy.deepcopy(provider)
        person["options"][0]["option"] = f"Jane Smith {sentinel}"
        cases.append(("personal data", person))
        huge = copy.deepcopy(provider)
        huge["options"][0]["duration"] = sentinel * 600
        cases.append(("huge text", huge))
        large_list = copy.deepcopy(provider)
        large_list["options"] = [copy.deepcopy(provider["options"][0]) for _ in range(151)]
        cases.append(("huge list", large_list))
        cyclic: dict[str, object] = {"marker": sentinel}
        cyclic["cycle"] = cyclic
        cases.append(("cycle", cyclic))
        deep: object = {"marker": sentinel}
        for _ in range(80):
            deep = {"child": deep}
        cases.append(("depth", deep))

        for name, altered in cases:
            with self.subTest(name=name):
                self.assert_invalid_without_echo(altered, sentinel)

    def test_provider_research_accepts_limited_and_unavailable_closed_states(self):
        for name in ("limited-en.json", "unavailable-es.json"):
            with self.subTest(name=name):
                self.assertEqual(
                    [], PROVIDER_VALIDATOR.validate_provider_research(self.provider_fixture(name))
                )


class CareerLearningDecisionV2Tests(unittest.TestCase):
    def complete_v2_sources(self) -> tuple[dict[str, object], ...]:
        research = load_json(RESEARCH_FIXTURES / "complete-five-es.json")
        dossier = load_json(DOSSIER_FIXTURES / "scenario-a-es.json")
        market = MARKET_V2_BUILDER.build_market_dossier_v2(research, dossier)
        provider = load_json(PROVIDER_FIXTURES / "complete-es.json")
        return research, market, dossier, provider

    @staticmethod
    def request(code: str, rank: int = 1, provider_id: str | None = None) -> dict[str, object]:
        return {
            "decision_rank": rank,
            "decision_code": code,
            "source_signals": ["terraform"],
            "provider_option_id": provider_id,
        }

    @staticmethod
    def route(locale: str) -> dict[str, object]:
        return {
            "signal": "terraform",
            "term_label": "Terraform",
            "support_state": "candidate_reported_match",
            "recurrence": "1/5",
            "vacancy_ordinals": ["V3"],
        }

    @staticmethod
    def provider_option() -> dict[str, object]:
        provider = load_json(PROVIDER_FIXTURES / "complete-es.json")
        return copy.deepcopy(provider["options"][0])

    def test_projection_pins_complete_es_and_en_objects_for_all_five_codes(self):
        shared = {
            "es": {
                "source_signals": ["terraform"],
                "signal_routes": [self.route("es")],
                "cost_time_band": "No evaluado; requiere confirmación separada.",
                "expected_signal_boundary": "Hipótesis acotada: una señal inspectable no predice entrevista, oferta, salario ni retorno de inversión.",
                "portfolio_or_no_learning_alternative": "Completa primero una prueba acotada y usa la evidencia existente antes de comprar formación.",
                "overbuying_risk": "Evita acumular credenciales o dividir el tiempo antes de completar una prueba de mayor señal.",
                "next_action_gate": "Revisión y autorización exacta obligatorias antes de inscripción, compra, programación de examen, publicación, difusión o mensajería externa.",
                "outcome_boundary": "not_an_interview_offer_salary_or_roi_prediction",
                "draft_only": True,
                "no_external_action": True,
            },
            "en": {
                "source_signals": ["terraform"],
                "signal_routes": [self.route("en")],
                "cost_time_band": "Not evaluated; separate confirmation is required.",
                "expected_signal_boundary": "Bounded hypothesis: an inspectable signal predicts neither an interview, offer, salary, nor return on investment.",
                "portfolio_or_no_learning_alternative": "Complete one bounded proof first and use existing evidence before buying learning.",
                "overbuying_risk": "Avoid collecting credentials or splitting time before one higher-signal proof is complete.",
                "next_action_gate": "Review and exact authorization are required before enrollment, purchase, exam scheduling, publication, sharing, or external messaging.",
                "outcome_boundary": "not_an_interview_offer_salary_or_roi_prediction",
                "draft_only": True,
                "no_external_action": True,
            },
        }
        expected_rules = {
            ("es", "build_bounded_proof"): {
                "gap_type": "proof", "option_type": "portfolio_project", "decision": "do_now",
                "option_name": "Prueba acotada de Terraform", "provider_or_owner": "candidate_owned",
                "decision_basis": "Prioriza una prueba acotada antes de comprar formación; la ruta estructurada de evidencia es la base completa de esta decisión preliminar.",
            },
            ("en", "build_bounded_proof"): {
                "gap_type": "proof", "option_type": "portfolio_project", "decision": "do_now",
                "option_name": "Bounded Terraform proof", "provider_or_owner": "candidate_owned",
                "decision_basis": "Prioritize one bounded proof before buying learning; the structured evidence route is the complete basis for this draft decision.",
            },
            ("es", "run_validation_lab"): {
                "gap_type": "experience", "option_type": "lab", "decision": "do_now",
                "option_name": "Laboratorio de validación de Terraform", "provider_or_owner": "candidate_owned",
                "decision_basis": "Usa un laboratorio acotado para comprobar la señal documentada; la ruta estructurada de evidencia es la base completa de esta decisión preliminar.",
            },
            ("en", "run_validation_lab"): {
                "gap_type": "experience", "option_type": "lab", "decision": "do_now",
                "option_name": "Terraform validation lab", "provider_or_owner": "candidate_owned",
                "decision_basis": "Use a bounded lab to test the documented signal; the structured evidence route is the complete basis for this draft decision.",
            },
            ("es", "research_provider_option"): {
                "gap_type": "knowledge", "option_type": "course", "decision": "research_first",
                "option_name": "Terraform course", "provider_or_owner": "HashiCorp",
                "decision_basis": "Investiga esta opción verificada de proveedor antes de comprar; su vínculo estructurado de señal no predice resultados laborales.",
            },
            ("en", "research_provider_option"): {
                "gap_type": "knowledge", "option_type": "course", "decision": "research_first",
                "option_name": "Terraform course", "provider_or_owner": "HashiCorp",
                "decision_basis": "Research this verified provider option before buying; its structured signal binding does not predict employment outcomes.",
            },
            ("es", "defer_learning_purchase"): {
                "gap_type": "low_return", "option_type": "no_learning_yet", "decision": "defer",
                "option_name": "Aplazar compra de formación para Terraform", "provider_or_owner": "candidate_owned",
                "decision_basis": "Aplaza la compra hasta completar una prueba acotada; la ruta estructurada de evidencia no demuestra retorno de inversión.",
            },
            ("en", "defer_learning_purchase"): {
                "gap_type": "low_return", "option_type": "no_learning_yet", "decision": "defer",
                "option_name": "Defer learning purchase for Terraform", "provider_or_owner": "candidate_owned",
                "decision_basis": "Defer the purchase until one bounded proof is complete; the structured evidence route does not establish return on investment.",
            },
            ("es", "run_role_search_experiment"): {
                "gap_type": "terminology", "option_type": "role_search", "decision": "research_first",
                "option_name": "Experimento de búsqueda para Terraform", "provider_or_owner": "candidate_owned",
                "decision_basis": "Prueba una búsqueda acotada de roles antes de elegir formación; la ruta estructurada de evidencia no demuestra elegibilidad ni contratación.",
            },
            ("en", "run_role_search_experiment"): {
                "gap_type": "terminology", "option_type": "role_search", "decision": "research_first",
                "option_name": "Role-search experiment for Terraform", "provider_or_owner": "candidate_owned",
                "decision_basis": "Run a bounded role search before choosing learning; the structured evidence route does not establish eligibility or hiring.",
            },
        }
        for (locale, code), rule_fields in expected_rules.items():
            with self.subTest(locale=locale, code=code):
                provider_id = "LP-001" if code == "research_provider_option" else None
                request = self.request(code, provider_id=provider_id)
                expected = {
                    "decision_rank": 1,
                    "decision_code": code,
                    "provider_option_id": provider_id,
                    **shared[locale],
                    **rule_fields,
                }
                actual = LEARNING_V2_PROJECTION.project_decision_v2(
                    locale,
                    request,
                    [self.route(locale)],
                    self.provider_option() if provider_id else None,
                )
                self.assertEqual(expected, actual)

    def test_learning_v2_accepts_only_four_input_fields_and_exact_terraform_route(self):
        sources = self.complete_v2_sources()
        result = LEARNING_V2_BUILDER.build_learning_bundle_v2(
            *sources, [self.request("build_bounded_proof")]
        )
        row = result["decisions"][0]
        self.assertEqual(["C-002"], row["claim_ids"])
        self.assertEqual(["E-004"], row["source_evidence_ids"])
        self.assertEqual(["V-003-R-01"], row["requirement_ids"])
        self.assertEqual(["V-003"], row["vacancy_ids"])
        self.assertEqual(["devops_engineering"], row["target_role_families"])
        self.assertEqual(
            [{
                "signal": "terraform", "term_label": "Terraform",
                "support_state": "candidate_reported_match", "recurrence": "1/5",
                "vacancy_ordinals": ["V3"],
            }],
            row["signal_routes"],
        )
        self.assertRegex(
            LEARNING_V2_VALIDATOR.snapshot_for_learning_bundle_v2(result),
            r"^snap-learning-v2-sha256-[0-9a-f]{64}$",
        )
        self.assertEqual(
            [], LEARNING_V2_VALIDATOR.validate_learning_bundle_v2(result, *sources)
        )

    def test_multi_signal_routes_preserve_per_signal_vacancy_attribution_and_exact_unions(self):
        research, _market, dossier, provider = self.complete_v2_sources()
        dossier["requested_technology_terms"].append({"term": "Python", "claim_ids": ["C-001"]})
        dossier["claims"][0]["paraphrase"] = "Python supports a concrete professional proposition."
        dossier["evidence"][0]["paraphrase"] = "Python is present in the supplied material."
        dossier["evidence"][1]["paraphrase"] = "Python scope is available for bounded review."
        market = MARKET_V2_BUILDER.build_market_dossier_v2(research, dossier)
        request = {
            "decision_rank": 1,
            "decision_code": "build_bounded_proof",
            "source_signals": ["python", "terraform"],
            "provider_option_id": None,
        }
        result = LEARNING_V2_BUILDER.build_learning_bundle_v2(
            research, market, dossier, provider, [request]
        )
        row = result["decisions"][0]
        self.assertEqual(["C-001", "C-002"], row["claim_ids"])
        self.assertEqual(["E-001", "E-002", "E-004"], row["source_evidence_ids"])
        self.assertEqual(["V-001-R-01", "V-003-R-01"], row["requirement_ids"])
        self.assertEqual(["V-001", "V-003"], row["vacancy_ids"])
        self.assertEqual(["devops_engineering", "site_reliability_engineering"], row["target_role_families"])
        self.assertEqual(
            [("python", ["V1"]), ("terraform", ["V3"])],
            [(route["signal"], route["vacancy_ordinals"]) for route in row["signal_routes"]],
        )
        reordered = copy.deepcopy(request)
        reordered["source_signals"] = ["terraform", "python"]
        with self.assertRaisesRegex(ValueError, r"^learning decision v2 is invalid$"):
            LEARNING_V2_BUILDER.build_learning_bundle_v2(
                research, market, dossier, provider, [reordered]
            )

    def test_quantum_semantics_provider_displacement_and_caller_output_fields_fail_closed(self):
        sources = self.complete_v2_sources()
        bad_rows = [
            {"decision_rank": 1, "decision_code": "build_bounded_proof", "source_signals": ["quantum_computing"], "provider_option_id": None},
            {"decision_rank": 1, "decision_code": "research_provider_option", "source_signals": ["terraform"], "provider_option_id": "LP-002"},
            {"decision_rank": 1, "decision_code": "research_provider_option", "source_signals": ["terraform"], "provider_option_id": None},
            {"decision_rank": 1, "decision_code": "build_bounded_proof", "source_signals": ["terraform"], "provider_option_id": "LP-001"},
        ]
        for field in ("option_name", "decision_basis", "overbuying_risk", "cost_time_band", "next_action_gate"):
            row = self.request("build_bounded_proof")
            row[field] = "Quantum computing changes everything"
            bad_rows.append(row)
        for row in bad_rows:
            with self.subTest(row=row):
                with self.assertRaisesRegex(ValueError, r"^learning decision v2 is invalid$") as raised:
                    LEARNING_V2_BUILDER.build_learning_bundle_v2(*sources, [row])
                self.assertNotIn("Quantum", str(raised.exception))

    def test_source_signal_order_duplicates_unknown_support_and_rank_shape_fail_closed(self):
        sources = self.complete_v2_sources()
        bad_requests = [
            {"decision_rank": 1, "decision_code": "build_bounded_proof", "source_signals": ["terraform", "python"], "provider_option_id": None},
            {"decision_rank": 1, "decision_code": "build_bounded_proof", "source_signals": ["terraform", "terraform"], "provider_option_id": None},
            {"decision_rank": 1, "decision_code": "build_bounded_proof", "source_signals": ["python"], "provider_option_id": None},
            {"decision_rank": 2, "decision_code": "build_bounded_proof", "source_signals": ["terraform"], "provider_option_id": None},
        ]
        for request in bad_requests:
            with self.subTest(request=request):
                with self.assertRaisesRegex(ValueError, r"^learning decision v2 is invalid$"):
                    LEARNING_V2_BUILDER.build_learning_bundle_v2(*sources, [request])

    def test_validator_recomputes_every_provenance_route_semantic_and_snapshot_field(self):
        sources = self.complete_v2_sources()
        result = LEARNING_V2_BUILDER.build_learning_bundle_v2(
            *sources,
            [
                self.request("build_bounded_proof", 1),
                self.request("research_provider_option", 2, "LP-001"),
            ],
        )
        mutations: list[dict[str, object]] = []
        for field, replacement in (
            ("claim_ids", ["C-001"]),
            ("source_evidence_ids", ["E-001"]),
            ("requirement_ids", ["V-001-R-01"]),
            ("vacancy_ids", ["V-001"]),
            ("target_role_families", ["platform_engineering"]),
            ("decision_basis", "Changed basis"),
            ("cost_time_band", "Changed cost"),
        ):
            altered = copy.deepcopy(result)
            altered["decisions"][0][field] = replacement
            mutations.append(altered)
        crossed_route = copy.deepcopy(result)
        crossed_route["decisions"][0]["signal_routes"][0]["vacancy_ordinals"] = ["V1"]
        mutations.append(crossed_route)
        for root_field in (
            "source_research_snapshot", "source_dossier_snapshot", "source_alignment_snapshot",
            "source_market_snapshot", "source_provider_research_snapshot",
        ):
            altered = copy.deepcopy(result)
            altered[root_field] = "snap-learning-v2-sha256-" + "0" * 64
            mutations.append(altered)
        omitted = copy.deepcopy(result)
        del omitted["source_provider_research_snapshot"]
        mutations.append(omitted)
        for altered in mutations:
            with self.subTest(keys=set(altered)):
                self.assertEqual(
                    ["learning decision does not match validated sources"],
                    LEARNING_V2_VALIDATOR.validate_learning_bundle_v2(altered, *sources),
                )

    def test_validator_rejects_stale_crossed_sources_and_provider_coverage_changes(self):
        sources = self.complete_v2_sources()
        result = LEARNING_V2_BUILDER.build_learning_bundle_v2(
            *sources, [self.request("research_provider_option", provider_id="LP-001")]
        )
        stale_research = copy.deepcopy(sources[0])
        stale_research["vacancies"][0]["title"] = "Stale public vacancy"
        changed_provider = copy.deepcopy(sources[3])
        changed_provider["options"][0]["covered_signals"] = []
        cases = [
            (stale_research, sources[1], sources[2], sources[3]),
            (sources[0], sources[1], load_json(DOSSIER_FIXTURES / "scenario-c-en.json"), sources[3]),
            (sources[0], sources[1], sources[2], changed_provider),
        ]
        for crossed in cases:
            with self.subTest():
                self.assertEqual(
                    ["learning decision does not match validated sources"],
                    LEARNING_V2_VALIDATOR.validate_learning_bundle_v2(result, *crossed),
                )

    def test_builder_and_validator_are_total_and_do_not_echo_malformed_values(self):
        sources = self.complete_v2_sources()
        sentinel = "learning-malicious-sentinel"
        cycle: dict[str, object] = {"marker": sentinel}
        cycle["cycle"] = cycle
        oversized = [self.request("build_bounded_proof") for _ in range(151)]
        unicode_edge = self.request("build_bounded_proof")
        unicode_edge["source_signals"] = [f"terraform{chr(0xD800)}{sentinel}"]
        for malformed in (cycle, oversized, [unicode_edge]):
            with self.subTest(kind=type(malformed).__name__):
                with self.assertRaisesRegex(ValueError, r"^learning decision v2 is invalid$") as raised:
                    LEARNING_V2_BUILDER.build_learning_bundle_v2(*sources, malformed)
                self.assertNotIn(sentinel, str(raised.exception))
                errors = LEARNING_V2_VALIDATOR.validate_learning_bundle_v2(
                    malformed, *sources
                )
                self.assertEqual(["learning decision does not match validated sources"], errors)
                self.assertNotIn(sentinel, "\n".join(errors))

    def test_unavailable_market_accepts_only_absent_or_empty_requests(self):
        research = load_json(RESEARCH_FIXTURES / "unavailable-es.json")
        dossier = load_json(DOSSIER_FIXTURES / "scenario-a-es.json")
        market = MARKET_V2_BUILDER.build_market_dossier_v2(research, dossier)
        provider = load_json(PROVIDER_FIXTURES / "unavailable-es.json")
        for requests in (None, []):
            with self.subTest(requests=requests):
                result = LEARNING_V2_BUILDER.build_learning_bundle_v2(
                    research, market, dossier, provider, requests
                )
                self.assertEqual("unavailable", result["state"])
                self.assertEqual([], result["decisions"])
                self.assertEqual(
                    [],
                    LEARNING_V2_VALIDATOR.validate_learning_bundle_v2(
                        result, research, market, dossier, provider
                    ),
                )
        with self.assertRaisesRegex(ValueError, r"^learning decision v2 is invalid$"):
            LEARNING_V2_BUILDER.build_learning_bundle_v2(
                research, market, dossier, provider, [self.request("build_bounded_proof")]
            )

    def test_limited_en_goldens_recompute_from_the_named_committed_source(self):
        source_path = DOSSIER_FIXTURES / "scenario-c-market-en.json"
        self.assertTrue(
            source_path.is_file(),
            "the limited EN provenance source must be a committed fixture",
        )
        research = load_json(RESEARCH_FIXTURES / "limited-four-en.json")
        dossier = load_json(source_path)
        provider = load_json(PROVIDER_FIXTURES / "limited-en.json")
        market = load_json(
            ROOT / "tests/evals/with-skill/fixtures/career-market-learning-dossier-v2/limited-four-en.json"
        )
        learning = load_json(
            ROOT / "tests/evals/with-skill/fixtures/career-learning-decision-v2/limited-en.json"
        )
        source_snapshot = DOSSIER_SNAPSHOT.snapshot_for_dossier(dossier)
        self.assertEqual(source_snapshot, market["source_executive_dossier_snapshot"])
        self.assertEqual(source_snapshot, learning["source_dossier_snapshot"])
        self.assertEqual(
            market, MARKET_V2_BUILDER.build_market_dossier_v2(research, dossier)
        )
        self.assertEqual(
            [], MARKET_V2_VALIDATOR.validate_market_dossier_v2(market, research, dossier)
        )
        requests = [
            {
                field: row[field]
                for field in (
                    "decision_rank", "decision_code", "source_signals", "provider_option_id"
                )
            }
            for row in learning["decisions"]
        ]
        self.assertEqual(
            learning,
            LEARNING_V2_BUILDER.build_learning_bundle_v2(
                research, market, dossier, provider, requests
            ),
        )
        self.assertEqual(
            [],
            LEARNING_V2_VALIDATOR.validate_learning_bundle_v2(
                learning, research, market, dossier, provider
            ),
        )


if __name__ == "__main__":
    unittest.main()
