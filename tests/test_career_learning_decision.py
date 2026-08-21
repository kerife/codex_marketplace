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

from dossier_snapshot import snapshot_for_dossier  # noqa: E402
from build_career_learning_decision import (  # noqa: E402
    build_learning_bundle,
    snapshot_for_learning_bundle,
)
from validate_json_schema_subset import (  # noqa: E402
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

    def test_validator_rejects_single_token_identity_labels_without_echo(self) -> None:
        for marker in (
            "Candidate: SyntheticAlias.",
            "Candidate—SyntheticAlias.",
            "Candidate：SyntheticAlias.",
            "Candidate - SyntheticAlias.",
            "Candidate, SyntheticAlias.",
            "Candidate; SyntheticAlias.",
            "Candidate-SyntheticAlias.",
            "Candidate-syntheticalias.",
            "Candidate_SyntheticAlias.",
            "Candidate.SyntheticAlias.",
            "Candidate · SyntheticAlias.",
            "Candidate’SyntheticAlias.",
            "Candidate's name: SyntheticAlias.",
            "Applicant # SyntheticAlias.",
            "Candidato: AliasSintetico.",
            "Candidata—AliasSintetico.",
        ):
            with self.subTest(marker=marker):
                value = _bundle(count=3)
                value["decisions"][0]["decision_basis"] = marker
                errors = self.validator.validate_learning_bundle(
                    value, self.market, self.dossier, self.research
                )
                self.assertTrue(errors)
                self.assertNotIn(marker, "\n".join(errors))
        safe = _bundle(count=3)
        safe["decisions"][0]["decision_basis"] = (
            "Candidate-owned proof remains a bounded private task before any purchase."
        )
        self.assertEqual(
            [],
            self.validator.validate_learning_bundle(
                safe, self.market, self.dossier, self.research
            ),
        )
        for marker in (
            "Candidate Synthetic Alias.",
            "Applicant Synthetic Alias.",
            "Synthetic Alias candidate requested a bounded proof.",
            "Synthetic Alias is the candidate for private review.",
            "Synthetic Q. Alias candidate requested a bounded proof.",
        ):
            with self.subTest(reverse_marker=marker):
                value = _bundle(count=3)
                value["decisions"][0]["decision_basis"] = marker
                errors = self.validator.validate_learning_bundle(
                    value, self.market, self.dossier, self.research
                )
                self.assertTrue(errors)
                self.assertNotIn(marker, "\n".join(errors))

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
        bad = copy.deepcopy(valid); bad["state"] = {}; mutations.append(bad)
        bad = copy.deepcopy(valid); bad["state"] = []; mutations.append(bad)
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

    def test_validator_rejects_identity_action_and_outcome_text_on_every_learning_decision_surface(self) -> None:
        cases = (
            ("option_name", "Enroll now: example course"),
            ("target_role", "Purchase now: Senior SRE"),
            ("provider_or_owner", "Schedule an exam now with Example Provider"),
            ("decision_basis", "Guaranteed interview preparation"),
            ("target_role", "candidate name Example Person Senior SRE"),
            ("provider_or_owner", "candidato nombre Ejemplo Persona"),
            ("option_name", "This credential will get an offer"),
            ("option_name", "Buy this course"),
            ("target_role", "Sign up now for Senior SRE"),
            ("provider_or_owner", "Apply now"),
            ("decision_basis", "Please enroll"),
            ("option_name", "Schedule interview"),
            ("provider_or_owner", "Book exam"),
            ("portfolio_or_no_learning_alternative", "Contact provider"),
            ("overbuying_risk", "Publish this project"),
            ("option_name", "This gets interviews"),
            ("decision_basis", "This helps you get hired"),
            ("target_role", "Get hired faster as a Senior SRE"),
            ("provider_or_owner", "Land an interview"),
            ("option_name", "Secure an offer"),
            ("decision_basis", "This may lead to an offer"),
            ("target_role", "You will be hired"),
            ("option_name", "Increase your salary"),
            ("decision_basis", "Hiring success"),
            ("option_name", "Job placement course"),
            ("decision_basis", "Offer after completion"),
            ("provider_or_owner", "Employer will contact you"),
            ("option_name", "https://github.com/example-user"),
            ("target_role", "example.com/profile"),
            ("provider_or_owner", "ID-12345"),
            ("decision_basis", "550e8400-e29b-41d4-a716-446655440000"),
            ("option_name", "profile_id"),
            ("provider_or_owner", "user id"),
            ("next_action_gate", "exact authorization required before Send a message"),
            ("decision_basis", "This improves your chances"),
            ("target_role", "This improves your chance of getting hired"),
            ("option_name", "This helps you land a role"),
            ("provider_or_owner", "Get a job"),
            ("portfolio_or_no_learning_alternative", "Find a job"),
            ("overbuying_risk", "Secure employment"),
            ("option_name", "Career advancement"),
            ("decision_basis", "Boost compensation"),
            ("target_role", "Hiring outcome"),
            ("option_name", "Ensures an interview"),
            ("decision_basis", "Ensures employment"),
            ("target_role", "Improves hiring odds"),
            ("provider_or_owner", "Boosts hiring prospects"),
            ("option_name", "Results in an offer"),
            ("portfolio_or_no_learning_alternative", "Leads to employment"),
            ("overbuying_risk", "Secure a job"),
            ("option_name", "Get an offer"),
            ("decision_basis", "Find employment"),
            ("target_role", "Will land a role"),
            ("provider_or_owner", "Makes you interview-ready"),
            ("option_name", "case-123456"),
            ("provider_or_owner", "private-id-7f3a2c"),
            ("decision_basis", "ID-12"),
            ("option_name", "https://foo.xyz"),
            ("option_name", "case-123"),
            ("provider_or_owner", "private-id-x"),
            ("decision_basis", "foo.xyz/profile"),
            ("option_name", "ID-1"),
            ("provider_or_owner", "account-id-xy"),
            ("decision_basis", "foo.ai/profile"),
            ("option_name", "foo.co.uk/profile"),
            ("target_role", "foo.tech/profile"),
            ("provider_or_owner", "foo.cloud/profile"),
            ("option_name", "Compra este curso"),
            ("target_role", "Inscríbete ahora"),
            ("provider_or_owner", "Aplica ahora"),
            ("decision_basis", "Programa el examen"),
            ("portfolio_or_no_learning_alternative", "Agenda entrevista"),
            ("overbuying_risk", "Contacta al proveedor"),
            ("option_name", "Publica este proyecto"),
            ("next_action_gate", "exact authorization required before Envía un mensaje"),
            ("option_name", "Esto consigue entrevistas"),
            ("decision_basis", "Te ayuda a conseguir empleo"),
            ("target_role", "Conseguirás trabajo"),
            ("provider_or_owner", "Obtén una oferta"),
            ("option_name", "Te contratarán"),
            ("decision_basis", "Aumenta tu salario"),
            ("target_role", "Éxito laboral"),
            ("option_name", "Oferta garantizada"),
            ("decision_basis", "Retorno de inversión"),
            ("option_name", "Garantiza empleo"),
            ("decision_basis", "Esta opción garantiza contratación"),
            ("target_role", "Asegura una entrevista"),
            ("provider_or_owner", "Asegura trabajo"),
            ("option_name", "Te conseguirá una oferta"),
            ("portfolio_or_no_learning_alternative", "Conseguir empleo al terminar"),
            ("overbuying_risk", "Mejora tus probabilidades"),
            ("option_name", "Aumenta tus posibilidades de contratación"),
            ("decision_basis", "Te dará trabajo"),
            ("target_role", "Resultado de contratación garantizado"),
            ("provider_or_owner", "Contratación asegurada"),
            ("option_name", "Éxito de entrevista"),
            ("decision_basis", "Obtendrás empleo"),
            ("target_role", "Te conseguirás un trabajo"),
            ("decision_basis", "You are assured a job"),
            ("option_name", "This credential leads to an interview"),
            ("provider_or_owner", "This gets an interview"),
            ("decision_basis", "This makes hiring likely"),
            ("option_name", "This results in hiring"),
            ("target_role", "Improves interview chances"),
            ("option_name", "Book your course"),
            ("decision_basis", "Enroll"),
            ("provider_or_owner", "Register now"),
            ("option_name", "Apply to this role"),
            ("next_action_gate", "exact authorization required before Send an email"),
            ("decision_basis", "Message the recruiter"),
            ("option_name", "Candidate Kevin"),
            ("target_role", "Kevin Ríos"),
        )
        for field, unsafe_text in cases:
            with self.subTest(field=field, unsafe_text=unsafe_text):
                invalid = _bundle(count=3)
                invalid["decisions"][0][field] = unsafe_text
                errors = self.validator.validate_learning_bundle(
                    invalid, self.market, self.dossier, self.research
                )
                self.assertTrue(errors)
                self.assertNotIn(unsafe_text, "\n".join(errors))

    def test_validator_keeps_safe_technical_learning_text_valid(self) -> None:
        valid = _bundle(count=3)
        valid["decisions"][0].update({
            "target_role": "Senior SRE / Platform Engineer",
            "option_name": "Node.js observability proof artifact",
            "provider_or_owner": "candidate-owned proof project",
            "decision_basis": "Evidence E-004 and V-001 support a bounded Terraform proof artifact before a purchase.",
            "portfolio_or_no_learning_alternative": "Build one GitHub Actions, Terraform, and account identity lab locally before any paid course.",
            "overbuying_risk": "Avoid collecting credentials before a bounded technical artifact is complete.",
            "market_evidence_state": "Evidencia fechada para un laboratorio de Terraform y observabilidad.",
            "cost_time_band": "unknown: private review of the technical effort requires confirmation.",
            "expected_signal_boundary": "bounded hypothesis: una prueba técnica visible no predice éxito laboral ni contratación, ni garantiza empleo.",
            "next_action_gate": "Revisa en privado; exact authorization is required before any external action.",
        })
        self.assertEqual(
            [], self.validator.validate_learning_bundle(
                valid, self.market, self.dossier, self.research
            )
        )

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

    def test_validator_guards_visible_provider_metadata_copy(self) -> None:
        valid = _bundle(count=3)
        for field, value in (
            ("unknowns", "You are assured a job"),
            ("option", "Enroll"),
            ("source_title", "This gets an interview"),
            ("geography", "Candidate Kevin"),
            ("unknowns", "See E-001 CAP-001"),
        ):
            with self.subTest(field=field, value=value):
                bad = copy.deepcopy(valid)
                bad["decisions"][1]["provider_source"][field] = value
                errors = self.validator.validate_learning_bundle(
                    bad, self.market, self.dossier, self.research
                )
                self.assertTrue(errors)
                self.assertNotIn(value, "\n".join(errors))

    def test_builder_binds_snapshots_orders_rows_and_preserves_provider_unknowns(self) -> None:
        decisions = _bundle(count=5)["decisions"]
        before = copy.deepcopy(decisions)
        result = build_learning_bundle(self.research, self.market, self.dossier, list(reversed(decisions)))
        self.assertEqual(before, decisions)
        self.assertEqual("career-learning-decision-v1", result["schema_version"])
        self.assertEqual("evaluated", result["state"])
        self.assertEqual([1, 2, 3, 4, 5], [row["decision_rank"] for row in result["decisions"]])
        self.assertEqual("unknown: official page does not establish Mexico eligibility", result["decisions"][1]["provider_source"]["geography"])
        self.assertEqual([], self.validator.validate_learning_bundle(result, self.market, self.dossier, self.research))
        self.assertEqual(snapshot_for_learning_bundle(result), snapshot_for_learning_bundle(copy.deepcopy(result)))

    def test_builder_returns_bounded_unavailable_result_for_zero_market(self) -> None:
        research = _load_json(RESEARCH_ROOT / "unavailable-es.json")
        market = _load_json(MARKET_ROOT / "unavailable-es.json")
        result = build_learning_bundle(research, market, self.dossier, [])
        self.assertEqual(("unavailable", []), (result["state"], result["decisions"]))
        self.assertEqual([], self.validator.validate_learning_bundle(result, market, self.dossier, research))

    def test_builder_rejects_invalid_row_counts_and_missing_project_or_certificate_alternative(self) -> None:
        decisions = _bundle(count=5)["decisions"]
        for value in (decisions[:2], decisions + [_decision(6, "lab", "Too many")]):
            with self.subTest(count=len(value)):
                with self.assertRaisesRegex(ValueError, "learning"):
                    build_learning_bundle(self.research, self.market, self.dossier, value)
        no_certificate = copy.deepcopy(decisions)
        no_certificate[1]["option_type"] = "lab"
        no_certificate[1]["provider_source"] = None
        no_certificate[2]["option_type"] = "lab"
        no_certificate[2]["provider_source"] = None
        with self.assertRaisesRegex(ValueError, "learning"):
            build_learning_bundle(self.research, self.market, self.dossier, no_certificate)

    def test_builder_rejects_unbound_recurrence_gap_and_malformed_or_cyclic_inputs(self) -> None:
        decisions = _bundle(count=3)["decisions"]
        unbound = copy.deepcopy(decisions)
        unbound[0]["source_gap_ids"] = ["E-999"]
        with self.assertRaisesRegex(ValueError, "learning"):
            build_learning_bundle(self.research, self.market, self.dossier, unbound)
        cyclic = copy.deepcopy(decisions)
        cyclic.append(cyclic)
        with self.assertRaisesRegex(ValueError, "learning"):
            build_learning_bundle(self.research, self.market, self.dossier, cyclic)
        with self.assertRaisesRegex(ValueError, "learning"):
            build_learning_bundle(self.research, self.market, self.dossier, None)

    def test_builder_rejects_identity_action_and_outcome_text_before_returning_a_bundle(self) -> None:
        cases = (
            ("option_name", "Enroll now: example course"),
            ("target_role", "candidate name Example Person Senior SRE"),
            ("decision_basis", "Guaranteed interview preparation"),
        )
        for field, unsafe_text in cases:
            with self.subTest(field=field, unsafe_text=unsafe_text):
                decisions = _bundle(count=3)["decisions"]
                decisions[0][field] = unsafe_text
                with self.assertRaisesRegex(ValueError, "learning"):
                    build_learning_bundle(
                        self.research, self.market, self.dossier, decisions
                    )

    def test_market_v1_placeholder_remains_not_evaluated_and_empty(self) -> None:
        self.assertEqual("not_evaluated", self.market["learning_state"])
        self.assertEqual([], self.market["learning_decisions"])


if __name__ == "__main__":
    unittest.main()
