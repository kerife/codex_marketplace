"""Contracts for the optional career-learning-decision-v1 bundle.

These tests intentionally start red while the schema and validator are absent.
The existing career-market-learning-dossier-v1 fixture is kept as the source
artifact so this contract cannot silently alter the v1 learning placeholder.
"""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "plugins" / "professional-growth-coach" / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(ROOT / "plugins" / "professional-growth-coach" / "tests"))

from dossier_snapshot import snapshot_for_dossier  # noqa: E402
from validate_private_schema_conformance import (  # noqa: E402
    validate_schema_instance,
)
from validate_target_vacancy_research import (  # noqa: E402
    snapshot_for_market_dossier,
)


RESEARCH_ROOT = ROOT / "tests" / "evals" / "with-skill" / "fixtures" / "target-vacancy-research"
DOSSIER_ROOT = ROOT / "tests" / "evals" / "with-skill" / "fixtures" / "executive-career-dossier-v2"
MARKET_ROOT = ROOT / "tests" / "evals" / "with-skill" / "fixtures" / "career-market-learning-dossier"


def _load_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"fixture is not an object: {path}")
    return value


def _source_rows() -> list[dict[str, object]]:
    return [
        {
            "provider": "HashiCorp",
            "option": "Terraform Associate 004",
            "source_title": "HashiCorp Certified: Terraform Associate",
            "source_date": "2026-08-13",
            "source_state": "active",
            "url": "https://developer.hashicorp.com/certifications/infrastructure-automation",
            "geography": "unknown: official page does not establish Mexico eligibility",
            "availability": "active: online proctored exam listed",
            "current_cost": "unknown: official page does not state the current fee",
            "currency": "unknown: no verified currency",
            "tax": "unknown: tax treatment is not stated",
            "duration": "provider duration unknown: official page does not state exam duration",
            "prerequisite": "provider-verified: basic terminal skills and cloud architecture understanding",
            "renewal": "provider-verified: credential expires after two years",
            "maintenance": "provider-verified: renew by passing a current exam",
            "unknowns": "preparation time and Mexico eligibility are not stated",
        },
        {
            "provider": "CNCF",
            "option": "Certified Argo Project Associate",
            "source_title": "Certified Argo Project Associate",
            "source_date": "2026-08-13",
            "source_state": "active",
            "url": "https://www.cncf.io/training/certification/capa/",
            "geography": "unknown: official page does not establish Mexico eligibility",
            "availability": "active: online proctored exam listed",
            "current_cost": "unknown: official page does not state the current fee",
            "currency": "unknown: no verified currency",
            "tax": "unknown: tax treatment is not stated",
            "duration": "provider duration unknown: official page does not state exam duration",
            "prerequisite": "unknown: official page does not state prerequisites",
            "renewal": "unknown: official page does not state renewal",
            "maintenance": "unknown: official page does not state maintenance",
            "unknowns": "exam duration, prerequisites, renewal, maintenance, and Mexico eligibility are not stated",
        },
    ]


def _decision(
    rank: int,
    option_type: str,
    option_name: str,
    *,
    gap_type: str = "proof",
    decision: str = "do_now",
    source_gap_ids: list[str] | None = None,
    vacancy_ids: list[str] | None = None,
    provider_source: dict[str, object] | None = None,
) -> dict[str, object]:
    return {
        "decision_rank": rank,
        "target_role": "Senior SRE / Platform Engineer",
        "gap_type": gap_type,
        "option_type": option_type,
        "option_name": option_name,
        "provider_or_owner": "candidate-owned proof project" if provider_source is None else provider_source["provider"],
        "source_gap_ids": source_gap_ids or ["E-004"],
        "vacancy_ids": vacancy_ids or ["V-001", "V-002"],
        "market_evidence_state": "current dated vacancy evidence",
        "cost_time_band": "unknown: candidate effort and current cost require separate confirmation",
        "expected_signal_boundary": "bounded hypothesis: creates inspectable evidence without promising a hiring outcome",
        "portfolio_or_no_learning_alternative": "Build one bounded Terraform and observability proof artifact before buying another credential.",
        "overbuying_risk": "Avoid certificate collecting and splitting time before one higher-signal artifact is complete.",
        "decision": decision,
        "decision_basis": "Terraform and observability recur in current vacancy evidence; a proof artifact may signal more than a standalone credential.",
        "next_action_gate": "Review and exact authorization required before enrollment, purchase, exam scheduling, publication, sharing, or external messaging.",
        "outcome_boundary": "not_an_interview_offer_salary_or_roi_prediction",
        "draft_only": True,
        "no_external_action": True,
        "provider_source": provider_source,
    }


def _bundle(*, count: int = 3, state: str = "evaluated") -> dict[str, object]:
    research = _load_json(RESEARCH_ROOT / "complete-five-es.json")
    dossier = _load_json(DOSSIER_ROOT / "scenario-a-es.json")
    market = _load_json(MARKET_ROOT / "complete-five-es.json")
    decisions = [
        _decision(1, "portfolio_project", "Terraform production-pattern proof repo"),
        _decision(2, "course", "Terraform Associate study path", gap_type="knowledge", provider_source=_source_rows()[0]),
        _decision(3, "certification", "Certified Argo Project Associate", gap_type="experience", decision="defer", provider_source=_source_rows()[1]),
        _decision(4, "lab", "Observability incident-response lab", gap_type="proof", decision="research_first"),
        _decision(5, "no_learning_yet", "Finish one public-safe proof artifact", gap_type="low_return", decision="omit"),
    ][:count]
    if state == "unavailable":
        decisions = []
    return {
        "schema_version": "career-learning-decision-v1",
        "locale": market["locale"],
        "as_of_date": market["as_of_date"],
        "source_market_snapshot": snapshot_for_dossier(market),
        "source_dossier_snapshot": market["source_executive_dossier_snapshot"],
        "source_research_snapshot": snapshot_for_market_dossier(research),
        "state": state,
        "decisions": decisions,
        "privacy_boundary": "public_vacancy_metadata_and_identity_free_evidence_references_only",
        "no_external_action": True,
        "outcome_boundary": "not_an_interview_offer_salary_or_roi_prediction",
    }


def _validator():
    path = SCRIPTS / "validate_career_learning_decision.py"
    spec = importlib.util.spec_from_file_location("career_learning_validator", path)
    if spec is None or spec.loader is None:
        raise AssertionError("learning validator module is unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class CareerLearningDecisionContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.research = _load_json(RESEARCH_ROOT / "complete-five-es.json")
        cls.dossier = _load_json(DOSSIER_ROOT / "scenario-a-es.json")
        cls.market = _load_json(MARKET_ROOT / "complete-five-es.json")
        cls.schema = json.loads(
            (ROOT / "plugins" / "professional-growth-coach" / "schemas" / "career-learning-decision-v1.schema.json").read_text(encoding="utf-8")
        )
        cls.validator = _validator()

    def test_schema_accepts_evaluated_three_to_five_rows_and_closed_provider_source(self) -> None:
        value = _bundle(count=3)
        self.assertEqual([], validate_schema_instance(value, self.schema))
        self.assertEqual([], self.validator.validate_learning_bundle(value, self.market, self.dossier, self.research))
        for count in (4, 5):
            with self.subTest(count=count):
                self.assertEqual([], self.validator.validate_learning_bundle(_bundle(count=count), self.market, self.dossier, self.research))

    def test_absent_optional_bundle_is_valid_and_loader_reports_missing_without_echo(self) -> None:
        self.assertEqual([], self.validator.validate_learning_bundle(None, self.market, self.dossier, self.research))
        missing = ROOT / "tests" / "tmp-learning-bundle-does-not-exist.json"
        with self.assertRaises(self.validator.LearningBundleLoadError) as captured:
            self.validator.load_learning_bundle(missing)
        self.assertNotIn(str(missing), str(captured.exception))

    def test_schema_accepts_unavailable_empty_bundle_but_rejects_zero_market_evaluated(self) -> None:
        unavailable = _bundle(state="unavailable")
        self.assertEqual([], self.validator.validate_learning_bundle(unavailable, self.market, self.dossier, self.research))
        zero_market = _load_json(MARKET_ROOT / "unavailable-es.json")
        self.assertTrue(self.validator.validate_learning_bundle(_bundle(state="evaluated"), zero_market, self.dossier, self.research))

    def test_validator_rejects_row_count_rank_and_closed_enum_mutations(self) -> None:
        valid = _bundle(count=3)
        mutations = []
        mutations.append({**valid, "decisions": valid["decisions"][:2]})
        mutations.append({**valid, "decisions": valid["decisions"] + [_decision(4, "lab", "extra"), _decision(5, "lab", "extra2"), _decision(6, "lab", "extra3")]})
        duplicate = copy.deepcopy(valid); duplicate["decisions"][1]["decision_rank"] = 1; mutations.append(duplicate)
        invalid_option = copy.deepcopy(valid); invalid_option["decisions"][0]["option_type"] = "bootcamp"; mutations.append(invalid_option)
        invalid_gap = copy.deepcopy(valid); invalid_gap["decisions"][0]["gap_type"] = "skill"; mutations.append(invalid_gap)
        invalid_decision = copy.deepcopy(valid); invalid_decision["decisions"][0]["decision"] = "enroll"; mutations.append(invalid_decision)
        for value in mutations:
            with self.subTest(value=value.get("decisions", [])[:1]):
                self.assertTrue(self.validator.validate_learning_bundle(value, self.market, self.dossier, self.research))

    def test_validator_rejects_stale_snapshots_and_unbound_references(self) -> None:
        valid = _bundle(count=3)
        mutations = []
        stale = copy.deepcopy(valid); stale["source_market_snapshot"] = "snap-market-sha256-" + "0" * 64; mutations.append(stale)
        stale_research = copy.deepcopy(valid); stale_research["source_research_snapshot"] = "snap-market-sha256-" + "0" * 64; mutations.append(stale_research)
        bad_vacancy = copy.deepcopy(valid); bad_vacancy["decisions"][0]["vacancy_ids"] = ["V-999"]; mutations.append(bad_vacancy)
        bad_evidence = copy.deepcopy(valid); bad_evidence["decisions"][0]["source_gap_ids"] = ["E-999"]; mutations.append(bad_evidence)
        for value in mutations:
            self.assertTrue(self.validator.validate_learning_bundle(value, self.market, self.dossier, self.research))

    def test_validator_rejects_provider_metadata_gaps_and_action_or_identity_content(self) -> None:
        valid = _bundle(count=3)
        mutations = []
        for field in ("source_date", "url", "source_title", "geography", "availability", "current_cost", "currency", "tax", "duration", "prerequisite", "renewal", "maintenance", "unknowns"):
            bad = copy.deepcopy(valid); bad["decisions"][1]["provider_source"].pop(field); mutations.append(bad)
        bad = copy.deepcopy(valid); bad["decisions"][1]["provider_source"]["url"] = "http://example.invalid"; mutations.append(bad)
        bad = copy.deepcopy(valid); bad["decisions"][1]["provider_source"]["source_date"] = "2026-08-21"; mutations.append(bad)
        bad = copy.deepcopy(valid); bad["decisions"][1]["next_action_gate"] = "Enroll now"; mutations.append(bad)
        bad = copy.deepcopy(valid); bad["decisions"][0]["option_name"] = "kevinriosferrer@example.invalid"; mutations.append(bad)
        bad = copy.deepcopy(valid); bad["decisions"][0]["unexpected"] = True; mutations.append(bad)
        for value in mutations:
            self.assertTrue(self.validator.validate_learning_bundle(value, self.market, self.dossier, self.research))

    def test_validator_rejects_cycles_without_echoing_private_value(self) -> None:
        value = _bundle(count=3)
        private = "private-person@example.invalid"
        value["decisions"][0]["option_name"] = private
        value["decisions"][0]["cycle"] = value["decisions"][0]
        errors = self.validator.validate_learning_bundle(value, self.market, self.dossier, self.research)
        self.assertTrue(errors)
        self.assertNotIn(private, "\n".join(errors))

    def test_validator_is_total_for_unhashable_json_shaped_values(self) -> None:
        valid = _bundle(count=3)
        mutations = []
        bad = copy.deepcopy(valid); bad["decisions"][0]["source_gap_ids"] = [{}]; mutations.append(bad)
        bad = copy.deepcopy(valid); bad["decisions"][0]["vacancy_ids"] = [{}]; mutations.append(bad)
        bad = copy.deepcopy(valid); bad["decisions"][0]["option_type"] = {}; mutations.append(bad)
        bad = copy.deepcopy(valid); bad["decisions"][0]["gap_type"] = []; mutations.append(bad)
        bad = copy.deepcopy(valid); bad["decisions"][0]["decision"] = {}; mutations.append(bad)
        bad = copy.deepcopy(valid); bad["decisions"][0]["decision_rank"] = {}; mutations.append(bad)
        for value in mutations:
            with self.subTest(value=value["decisions"][0]):
                try:
                    errors = self.validator.validate_learning_bundle(value, self.market, self.dossier, self.research)
                except Exception as error:  # pragma: no cover - regression guard
                    self.fail(f"validator raised on malformed JSON-shaped value: {type(error).__name__}")
                self.assertTrue(errors)

    def test_schema_and_validator_enforce_state_specific_decision_counts(self) -> None:
        evaluated_empty = _bundle(count=3)
        evaluated_empty["decisions"] = []
        unavailable_nonempty = _bundle(state="unavailable")
        unavailable_nonempty["decisions"] = [_decision(1, "lab", "A bounded lab")]
        for value in (evaluated_empty, unavailable_nonempty):
            with self.subTest(state=value["state"]):
                self.assertTrue(validate_schema_instance(value, self.schema))
                self.assertTrue(self.validator.validate_learning_bundle(value, self.market, self.dossier, self.research))

    def test_validator_rejects_local_paths_and_profile_urls_in_text(self) -> None:
        valid = _bundle(count=3)
        for field, value in (
            ("option_name", "file:///Users/private/profile.json"),
            ("decision_basis", "https://www.linkedin.com/in/example-profile"),
            ("provider_or_owner", "/private/tmp/candidate-notes"),
        ):
            with self.subTest(field=field):
                bad = copy.deepcopy(valid)
                bad["decisions"][0][field] = value
                errors = self.validator.validate_learning_bundle(bad, self.market, self.dossier, self.research)
                self.assertTrue(errors)
                self.assertNotIn(value, "\n".join(errors))

    def test_validator_requires_active_official_provider_source(self) -> None:
        valid = _bundle(count=3)
        mutations = []
        bad_url = copy.deepcopy(valid)
        bad_url["decisions"][1]["provider_source"]["url"] = "https://example.invalid/not-official"
        mutations.append(bad_url)
        bad_state = copy.deepcopy(valid)
        bad_state["decisions"][1]["provider_source"]["source_state"] = "unknown"
        mutations.append(bad_state)
        bad_domain = copy.deepcopy(valid)
        bad_domain["decisions"][1]["provider_source"]["provider"] = "HashiCorp"
        bad_domain["decisions"][1]["provider_source"]["url"] = "https://example.com/course"
        mutations.append(bad_domain)
        for value in mutations:
            self.assertTrue(self.validator.validate_learning_bundle(value, self.market, self.dossier, self.research))

    def test_market_v1_placeholder_remains_not_evaluated_and_empty(self) -> None:
        self.assertEqual("not_evaluated", self.market["learning_state"])
        self.assertEqual([], self.market["learning_decisions"])


if __name__ == "__main__":
    unittest.main()
