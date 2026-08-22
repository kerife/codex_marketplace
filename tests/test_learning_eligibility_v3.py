"""Task 1 contracts for the vacancy-first candidate gap response boundary."""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
import tempfile
import unittest
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "plugins" / "professional-growth-coach" / "scripts"
FIXTURES = ROOT / "tests" / "evals" / "with-skill" / "fixtures"


def load_sibling(name: str):
    path = SCRIPTS / name
    specification = importlib.util.spec_from_file_location(
        f"learning_v3_{path.stem}", path
    )
    if specification is None or specification.loader is None:
        raise AssertionError(f"cannot load sibling module: {path.name}")
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


RESPONSE_BUILDER = load_sibling("build_candidate_gap_response_v1.py")
RESPONSE_VALIDATOR = load_sibling("validate_candidate_gap_response_v1.py")
SNAPSHOT = load_sibling("semantic_provenance_snapshot.py")
MARKET_BUILDER = load_sibling("build_career_market_learning_dossier_v2.py")


def load_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError("fixture must be an object")
    return value


@dataclass(frozen=True)
class Sources:
    research: dict[str, object]
    market: dict[str, object]
    provider: dict[str, object] | None = None


def recurrent_sources(*, locale: str = "es", provider: bool = False) -> Sources:
    if locale == "es":
        research_name = "complete-five-es.json"
        dossier_name = "scenario-a-es.json"
    else:
        research_name = "limited-four-en.json"
        dossier_name = "scenario-c-market-en.json"
    research = load_json(FIXTURES / "target-vacancy-research" / research_name)
    dossier = load_json(FIXTURES / "executive-career-dossier-v2" / dossier_name)
    research["vacancies"][0]["requirements"][0]["signal"] = "terraform"
    market = MARKET_BUILDER.build_market_dossier_v2(research, dossier)
    provider_value = None
    if provider:
        provider_name = "complete-es.json" if locale == "es" else "limited-en.json"
        provider_value = load_json(
            FIXTURES / "career-learning-provider-research" / provider_name
        )
    return Sources(research, market, provider_value)


def unavailable_sources() -> Sources:
    return Sources(
        load_json(
            FIXTURES
            / "target-vacancy-research"
            / "unavailable-es.json"
        ),
        load_json(
            FIXTURES
            / "career-market-learning-dossier-v2"
            / "unavailable-es.json"
        ),
    )


def response_payload(
    *,
    relation: object = "proof_gap",
    provider_ordinal: object = None,
) -> dict[str, object]:
    return {
        "selected_vacancy_ordinal": "V2",
        "selected_signal": "terraform",
        "relation": relation,
        "selected_provider_ordinal": provider_ordinal,
    }


class CandidateGapResponseV1Tests(unittest.TestCase):
    def test_response_persists_public_choice_without_private_ids(self):
        sources = recurrent_sources(locale="es")
        response = RESPONSE_BUILDER.build_candidate_gap_response_v1(
            sources.research,
            sources.market,
            {
                "selected_vacancy_ordinal": "V2",
                "selected_signal": "terraform",
                "relation": "proof_gap",
                "selected_provider_ordinal": None,
            },
        )
        self.assertEqual("candidate-gap-response-v1", response["schema_version"])
        self.assertEqual("complete", response["response_state"])
        self.assertEqual("V2", response["selected_vacancy_ordinal"])
        self.assertNotIn("V-003", json.dumps(response, sort_keys=True))
        self.assertEqual([], RESPONSE_VALIDATOR.validate_candidate_gap_response_v1(
            response, sources.research, sources.market
        ))

    def test_response_rejects_private_ids_free_prose_and_crossed_ordinals(self):
        sources = recurrent_sources(locale="es")
        cases = (
            {"selected_vacancy_id": "V-003", "selected_signal": "terraform", "relation": "proof_gap", "selected_provider_ordinal": None},
            {"selected_vacancy_ordinal": "V1", "selected_signal": "terraform", "relation": "proof_gap", "selected_provider_ordinal": None, "reason": "I need this"},
            {"selected_vacancy_ordinal": "V3", "selected_signal": "terraform", "relation": "proof_gap", "selected_provider_ordinal": None},
        )
        for payload in cases:
            with self.subTest(payload=sorted(payload)):
                with self.assertRaisesRegex(ValueError, "candidate gap response is invalid"):
                    RESPONSE_BUILDER.build_candidate_gap_response_v1(
                        sources.research, sources.market, payload
                    )

    def test_all_four_response_states_have_exact_nullability(self):
        available = recurrent_sources(locale="es")
        unavailable = unavailable_sources()
        cases = (
            (
                "unavailable",
                unavailable,
                None,
                (None, None, None, None),
            ),
            (
                "selection_required",
                available,
                None,
                (None, None, None, None),
            ),
            (
                "partial",
                available,
                response_payload(relation="unknown"),
                ("V2", "terraform", "unknown", None),
            ),
            (
                "complete",
                available,
                response_payload(),
                ("V2", "terraform", "proof_gap", None),
            ),
        )
        fields = (
            "selected_vacancy_ordinal",
            "selected_signal",
            "relation",
            "selected_provider_ordinal",
        )
        for expected_state, sources, payload, expected_values in cases:
            with self.subTest(state=expected_state):
                result = RESPONSE_BUILDER.build_candidate_gap_response_v1(
                    sources.research, sources.market, payload
                )
                self.assertEqual(expected_state, result["response_state"])
                self.assertEqual(expected_values, tuple(result[field] for field in fields))
                self.assertEqual(
                    [],
                    RESPONSE_VALIDATOR.validate_candidate_gap_response_v1(
                        result, sources.research, sources.market
                    ),
                )

    def test_all_seven_closed_relations_are_projected_without_classifying_prose(self):
        sources = recurrent_sources(locale="es")
        relations = (
            "supported",
            "proof_gap",
            "knowledge_gap",
            "practice_gap",
            "professional_experience_gap",
            "terminology_gap",
            "unknown",
        )
        for relation in relations:
            with self.subTest(relation=relation):
                result = RESPONSE_BUILDER.build_candidate_gap_response_v1(
                    sources.research,
                    sources.market,
                    response_payload(relation=relation),
                )
                self.assertEqual(
                    "partial" if relation == "unknown" else "complete",
                    result["response_state"],
                )
                self.assertEqual(relation, result["relation"])

    def test_public_response_accepts_both_closed_locales(self):
        for locale in ("es", "en"):
            with self.subTest(locale=locale):
                sources = recurrent_sources(locale=locale)
                result = RESPONSE_BUILDER.build_candidate_gap_response_v1(
                    sources.research, sources.market, response_payload()
                )
                self.assertEqual(locale, result["locale"])
                self.assertEqual(
                    [],
                    RESPONSE_VALIDATOR.validate_candidate_gap_response_v1(
                        result, sources.research, sources.market
                    ),
                )

    def test_ordinals_aliases_and_non_string_scalars_fail_closed(self):
        sources = recurrent_sources(locale="es")
        cases = (
            response_payload() | {"selected_vacancy_ordinal": "V0"},
            response_payload() | {"selected_vacancy_ordinal": "V6"},
            response_payload(relation="knowledge_gap", provider_ordinal="L0"),
            response_payload() | {"vacancy_ordinal": "V2"},
            response_payload() | {"selected_vacancy_ordinal": 2},
            response_payload() | {"selected_signal": True},
            response_payload() | {"relation": 7},
            response_payload() | {"selected_provider_ordinal": 1},
        )
        for payload in cases:
            with self.subTest(payload=payload):
                with self.assertRaisesRegex(
                    ValueError, r"^candidate gap response is invalid$"
                ):
                    RESPONSE_BUILDER.build_candidate_gap_response_v1(
                        sources.research, sources.market, payload
                    )

    def test_provider_is_bound_iff_snapshot_is_present_and_only_for_knowledge(self):
        sources = recurrent_sources(locale="es", provider=True)
        assert sources.provider is not None
        selected = RESPONSE_BUILDER.build_candidate_gap_response_v1(
            sources.research,
            sources.market,
            response_payload(relation="knowledge_gap", provider_ordinal="L1"),
            sources.provider,
        )
        self.assertRegex(selected["selected_provider_ordinal"], r"^L[1-9][0-9]*$")
        self.assertRegex(
            selected["source_provider_research_snapshot"],
            r"^snap-provider-sha256-[0-9a-f]{64}$",
        )
        self.assertNotIn("LP-001", json.dumps(selected, sort_keys=True))
        self.assertEqual(
            [],
            RESPONSE_VALIDATOR.validate_candidate_gap_response_v1(
                selected, sources.research, sources.market, sources.provider
            ),
        )

        no_choice = RESPONSE_BUILDER.build_candidate_gap_response_v1(
            sources.research,
            sources.market,
            response_payload(relation="knowledge_gap"),
            sources.provider,
        )
        self.assertIsNone(no_choice["selected_provider_ordinal"])
        self.assertIsNotNone(no_choice["source_provider_research_snapshot"])

        failures = (
            (response_payload(relation="proof_gap"), sources.provider),
            (response_payload(relation="unknown"), sources.provider),
            (response_payload(relation="knowledge_gap", provider_ordinal="L1"), None),
        )
        for payload, provider in failures:
            with self.subTest(relation=payload["relation"], provider=provider is not None):
                with self.assertRaisesRegex(
                    ValueError, r"^candidate gap response is invalid$"
                ):
                    RESPONSE_BUILDER.build_candidate_gap_response_v1(
                        sources.research, sources.market, payload, provider
                    )

    def test_provider_ordinal_uses_only_active_exact_signal_choices(self):
        sources = recurrent_sources(locale="es", provider=True)
        assert sources.provider is not None
        provider = copy.deepcopy(sources.provider)
        provider["options"][1]["covered_signals"] = ["terraform"]
        result = RESPONSE_BUILDER.build_candidate_gap_response_v1(
            sources.research,
            sources.market,
            response_payload(relation="knowledge_gap", provider_ordinal="L2"),
            provider,
        )
        self.assertEqual("L2", result["selected_provider_ordinal"])

        non_knowledge = copy.deepcopy(sources.provider)
        non_knowledge["options"][0]["covered_signals"] = ["kubernetes"]
        with self.assertRaisesRegex(ValueError, r"^candidate gap response is invalid$"):
            RESPONSE_BUILDER.build_candidate_gap_response_v1(
                sources.research,
                sources.market,
                response_payload(relation="knowledge_gap", provider_ordinal="L1"),
                non_knowledge,
            )

        inactive = copy.deepcopy(sources.provider)
        inactive["options"][0]["source_state"] = "unknown"
        inactive["options"][0]["availability"] = "unknown"
        with self.assertRaisesRegex(ValueError, r"^candidate gap response is invalid$"):
            RESPONSE_BUILDER.build_candidate_gap_response_v1(
                sources.research,
                sources.market,
                response_payload(relation="knowledge_gap", provider_ordinal="L1"),
                inactive,
            )

    def test_source_locale_date_state_and_snapshot_crossing_fail_closed(self):
        sources = recurrent_sources(locale="es", provider=True)
        assert sources.provider is not None
        cases: list[tuple[str, object, object, object | None]] = []
        wrong_locale = copy.deepcopy(sources.market)
        wrong_locale["locale"] = "en"
        cases.append(("market locale", sources.research, wrong_locale, None))
        wrong_date = copy.deepcopy(sources.market)
        wrong_date["as_of_date"] = "2026-08-12"
        cases.append(("market date", sources.research, wrong_date, None))
        wrong_state = copy.deepcopy(sources.market)
        wrong_state["state"] = "limited_market_evidence"
        cases.append(("market state", sources.research, wrong_state, None))
        wrong_summary_locale = copy.deepcopy(sources.market)
        wrong_summary_locale["search_summary"]["locale"] = "en"
        cases.append(
            ("market summary locale", sources.research, wrong_summary_locale, None)
        )
        wrong_summary_date = copy.deepcopy(sources.market)
        wrong_summary_date["search_summary"]["as_of_date"] = "2026-08-12"
        cases.append(
            ("market summary date", sources.research, wrong_summary_date, None)
        )
        wrong_summary_state = copy.deepcopy(sources.market)
        wrong_summary_state["search_summary"]["state"] = "limited_market_evidence"
        cases.append(
            ("market summary state", sources.research, wrong_summary_state, None)
        )
        stale_research = copy.deepcopy(sources.research)
        stale_research["vacancies"][0]["title"] = "Stale title"
        cases.append(("research snapshot", stale_research, sources.market, None))
        provider_locale = copy.deepcopy(sources.provider)
        provider_locale["locale"] = "en"
        cases.append(("provider locale", sources.research, sources.market, provider_locale))
        provider_date = copy.deepcopy(sources.provider)
        provider_date["as_of_date"] = "2026-08-14"
        cases.append(("provider date", sources.research, sources.market, provider_date))
        for name, research, market, provider in cases:
            with self.subTest(name=name):
                payload = response_payload(
                    relation="knowledge_gap" if provider is not None else "proof_gap"
                )
                with self.assertRaisesRegex(
                    ValueError, r"^candidate gap response is invalid$"
                ):
                    RESPONSE_BUILDER.build_candidate_gap_response_v1(
                        research, market, payload, provider
                    )

    def test_validator_rejects_wrong_fields_date_locale_and_crossed_sources(self):
        sources = recurrent_sources(locale="es")
        value = RESPONSE_BUILDER.build_candidate_gap_response_v1(
            sources.research, sources.market, response_payload()
        )
        other = recurrent_sources(locale="en")
        cases = []
        for field, replacement in (
            ("locale", "en"),
            ("as_of_date", "2026-08-12"),
            ("source_research_snapshot", "snap-market-sha256-" + "0" * 64),
            ("source_market_snapshot", "snap-market-dossier-v2-sha256-" + "0" * 64),
        ):
            malformed = copy.deepcopy(value)
            malformed[field] = replacement
            cases.append((field, malformed, sources.research, sources.market))
        extra = copy.deepcopy(value)
        extra["reason"] = "private-sentinel-free-prose"
        cases.append(("extra", extra, sources.research, sources.market))
        cases.append(("crossed", value, other.research, other.market))
        for name, malformed, research, market in cases:
            with self.subTest(name=name):
                errors = RESPONSE_VALIDATOR.validate_candidate_gap_response_v1(
                    malformed, research, market
                )
                self.assertEqual(
                    ["candidate gap response does not match validated sources"], errors
                )
                self.assertNotIn("private-sentinel", str(errors))

    def test_snapshot_limits_cycles_and_unsupported_scalars_are_generic(self):
        cycle: dict[str, object] = {}
        cycle["cycle"] = cycle
        depth: object = None
        for _ in range(34):
            depth = {"child": depth}
        too_many_nodes = {
            "rows": [[0 for _ in range(99)] for _ in range(101)]
        }
        cases = (
            cycle,
            depth,
            too_many_nodes,
            {"items": list(range(151))},
            {"text": "x" * 4097},
            {"text": chr(0xD800)},
            {"float": 1.5},
            {1: "non-string-key"},
        )
        for value in cases:
            with self.subTest(kind=type(value).__name__):
                with self.assertRaisesRegex(
                    ValueError, r"^semantic input group is invalid$"
                ) as raised:
                    SNAPSHOT.bounded_plain_snapshot(value)
                self.assertIsNone(raised.exception.__cause__)

        self.assertEqual(
            {"tuple": [1, "two", True, None]},
            SNAPSHOT.bounded_plain_snapshot({"tuple": (1, "two", True, None)}),
        )

    def test_exception_raising_mapping_fails_without_echo_and_deepcopy_is_unused(self):
        sentinel = "semantic-private-sentinel"

        class RaisingMapping(Mapping[str, object]):
            def __getitem__(self, key: str) -> object:
                raise RuntimeError(sentinel)

            def __iter__(self) -> Iterator[str]:
                raise RuntimeError(sentinel)

            def __len__(self) -> int:
                return 1

        class DeepcopyBomb(dict):
            def __deepcopy__(self, memo):
                raise RuntimeError(sentinel)

        with self.assertRaisesRegex(
            ValueError, r"^semantic input group is invalid$"
        ) as raised:
            SNAPSHOT.bounded_plain_snapshot(RaisingMapping())
        self.assertIsNone(raised.exception.__cause__)
        self.assertNotIn(sentinel, str(raised.exception))
        self.assertEqual(
            {"safe": {"value": 1}},
            SNAPSHOT.bounded_plain_snapshot(
                DeepcopyBomb({"safe": DeepcopyBomb({"value": 1})})
            ),
        )

    def test_builder_and_validator_use_only_the_single_captured_snapshot(self):
        sources = recurrent_sources(locale="es")
        sentinel = "private-toctou-sentinel"

        class OnePassMapping(Mapping[str, object]):
            def __init__(self, safe: dict[str, object]):
                self.safe = safe
                self.exhausted = False

            def __getitem__(self, key: str) -> object:
                if self.exhausted:
                    return sentinel
                return self.safe[key]

            def __iter__(self) -> Iterator[str]:
                if self.exhausted:
                    return iter((sentinel,))
                return iter(self.safe)

            def __len__(self) -> int:
                return len(self.safe)

            def items(self):
                if self.exhausted:
                    return iter(((sentinel, sentinel),))

                def captured():
                    try:
                        yield from self.safe.items()
                    finally:
                        self.exhausted = True

                return captured()

        research = OnePassMapping(sources.research)
        result = RESPONSE_BUILDER.build_candidate_gap_response_v1(
            research, sources.market, response_payload()
        )
        self.assertTrue(research.exhausted)
        self.assertNotIn(sentinel, json.dumps(result, sort_keys=True))

        response = OnePassMapping(result)
        self.assertEqual(
            [],
            RESPONSE_VALIDATOR.validate_candidate_gap_response_v1(
                response, sources.research, sources.market
            ),
        )
        self.assertTrue(response.exhausted)

    def test_builder_rejects_hostile_values_with_fixed_no_echo_diagnostic(self):
        sources = recurrent_sources(locale="es")
        sentinel = "candidate-gap-private-sentinel"
        cases: list[object] = []
        cyclic = response_payload()
        cyclic["cycle"] = cyclic
        cases.append(cyclic)
        cases.append(response_payload() | {"selected_signal": "x" * 4097 + sentinel})
        cases.append(response_payload() | {"selected_signal": chr(0xD800) + sentinel})
        for payload in cases:
            with self.subTest(kind=len(cases)):
                with self.assertRaisesRegex(
                    ValueError, r"^candidate gap response is invalid$"
                ) as raised:
                    RESPONSE_BUILDER.build_candidate_gap_response_v1(
                        sources.research, sources.market, payload
                    )
                self.assertIsNone(raised.exception.__cause__)
                self.assertNotIn(sentinel, str(raised.exception))

    def test_snapshot_and_bounded_loader_use_closed_canonical_contract(self):
        sources = recurrent_sources(locale="es")
        value = RESPONSE_BUILDER.build_candidate_gap_response_v1(
            sources.research, sources.market, response_payload()
        )
        self.assertRegex(
            RESPONSE_VALIDATOR.snapshot_for_candidate_gap_response_v1(value),
            r"^snap-gap-response-v1-sha256-[0-9a-f]{64}$",
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "response.json"
            path.write_text(json.dumps(value), encoding="utf-8")
            self.assertEqual(
                value, RESPONSE_VALIDATOR.load_candidate_gap_response_v1(path)
            )
            invalid = Path(directory) / "invalid.json"
            invalid.write_text("[]", encoding="utf-8")
            with self.assertRaisesRegex(
                RESPONSE_VALIDATOR.CandidateGapResponseLoadError,
                r"^cannot load candidate gap response$",
            ) as raised:
                RESPONSE_VALIDATOR.load_candidate_gap_response_v1(invalid)
            self.assertIsNone(raised.exception.__cause__)

    def test_v2_bounded_tree_delegates_without_changing_existing_json_semantics(self):
        v2 = load_sibling("build_career_learning_decision_v2.py")
        for value, expected in (
            ({"value": [1, "two", True, None]}, True),
            ({"value": "x" * 4097}, False),
            ({"value": chr(0xD800)}, False),
        ):
            with self.subTest(expected=expected):
                self.assertEqual(expected, v2._bounded_tree(value))


if __name__ == "__main__":
    unittest.main()
