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


if __name__ == "__main__":
    unittest.main()
