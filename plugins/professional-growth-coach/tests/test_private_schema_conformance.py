import copy
import datetime as dt
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_private_schema_conformance import (
    validate_checkpoint_for_test,
    validate_outcome_for_test,
    validate_private_fixture_semantics,
    validate_schema_instance,
)

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_CONTEXT = (
    (ROOT.parent.parent / "tests" / "evals" / "with-skill" / "fixtures").is_dir()
    and (ROOT.parent.parent / "scripts" / "check_repository_privacy.py").is_file()
)
REPOSITORY_ONLY_TESTS = {
    "test_career_learning_decision_schema_accepts_evaluated_and_unavailable_states",
    "test_career_learning_decision_v2_schema_accepts_closed_fixtures",
    "test_career_learning_provider_research_schema_accepts_closed_fixtures",
    "test_career_market_dossier_schemas_accept_closed_synthetic_states",
    "test_career_market_dossier_v2_schema_accepts_recomputed_fixtures",
    "test_candidate_market_alignment_v2_schema_accepts_derived_fixture",
    "test_candidate_gap_response_v1_schema_accepts_closed_public_states",
    "test_dependency_free_checker_rejects_nested_quantifier_patterns",
    "test_dossier_handoff_rejects_unlabelled_person_name_source_fact",
    "test_dossier_schema_prose_mutations_match_custom_unicode_boundary",
    "test_executive_dossier_v2_runtime_uses_the_schema_checker",
    "test_executive_dossier_v2_schema_accepts_ledger_and_closes_new_fields",
    "test_handoff_pair_rejects_an_unrelated_shape_valid_projection",
    "test_practice_question_rank_custom_validator_accepts_json_numeric_one",
    "test_practice_question_rank_custom_validator_matches_schema_for_boolean_values",
    "test_practice_schema_binds_source_to_snapshot_prefix",
    "test_practice_triage_handoff_question_kind_is_closed_and_required",
    "test_practice_v2_accepts_triage_content_bound_snapshot_and_v1_rejects_it",
    "test_practice_v2_schema_accepts_independent_ui_and_content_locales",
    "test_schema_prose_mutations_match_custom_unicode_boundary",
    "test_target_vacancy_research_schema_accepts_closed_synthetic_states",
    "test_triage_identifier_patterns_require_json_strings_in_v1_and_v2",
    "test_triage_schema_uses_canonical_screen_opening_scope",
    "test_triage_v2_schema_accepts_independent_ui_and_content_locales",
    "test_triage_v2_snapshot_binding_rejects_content_drift",
}
sys.path.insert(0, str(ROOT / "scripts"))
from build_dossier_recruiter_practice_handoff import build_handoff
from validate_dossier_recruiter_practice_handoff import validate_handoff
from private_prose_safety import is_safe_prose_text
from validate_private_recruiter_reply_triage import validate_triage
from validate_recruiter_practice_session import validate_session
from validate_target_vacancy_research import validate_research
from derive_candidate_market_alignment_v2 import derive_candidate_market_alignment_v2
from build_career_market_learning_dossier_v2 import build_market_dossier_v2
from validate_career_market_learning_dossier_v2 import validate_market_dossier_v2
from validate_career_learning_provider_research import validate_provider_research
from build_career_learning_decision_v2 import build_learning_bundle_v2
from validate_career_learning_decision_v2 import validate_learning_bundle_v2
from build_candidate_gap_response_v1 import build_candidate_gap_response_v1
from validate_candidate_gap_response_v1 import validate_candidate_gap_response_v1


def _load_v2_dossier_helper():
    path = ROOT.parent.parent / "tests" / "test_executive_career_dossier_v2.py"
    specification = importlib.util.spec_from_file_location("v2_dossier_test_helper", path)
    if specification is None or specification.loader is None:
        raise RuntimeError("v2 dossier test helper is unavailable")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def _load_learning_contract_helper():
    path = ROOT.parent.parent / "tests" / "test_career_learning_decision.py"
    specification = importlib.util.spec_from_file_location("learning_contract_test_helper", path)
    if specification is None or specification.loader is None:
        raise RuntimeError("learning contract test helper is unavailable")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


V2_READY_ES_SNAPSHOT = (
    "snap-triage-sha256-"
    "74720a33a8bfc5e085767831e741b7cce97d45b1bb2d76b47d3ee203a2b5d6e8"
)
V2_TRIAGE_PRACTICE_SNAPSHOT = (
    "snap-triage-sha256-"
    "85ad96e9cab8b222315a01a85d4a6f61f0d5a38650a1286773bc8e1664c15ebd"
)


class PrivateSchemaConformanceTests(unittest.TestCase):
    def setUp(self):
        if not REPOSITORY_CONTEXT and self._testMethodName in REPOSITORY_ONLY_TESTS:
            self.skipTest("repository conformance requires repository context")

    def _schema(self, name):
        return json.loads((ROOT / "schemas" / name).read_text(encoding="utf-8"))

    def test_career_market_dossier_schemas_accept_closed_synthetic_states(self):
        alignment_schema = self._schema("candidate-market-alignment-v1.schema.json")
        valid_alignment = {
            "schema_version": "candidate-market-alignment-v1",
            "research_snapshot": "snap-market-sha256-" + "0" * 64,
            "executive_dossier_snapshot": "snap-dossier-sha256-" + "1" * 64,
            "signal_bindings": [
                {
                    "signal": "kubernetes",
                    "support_state": "verified_match",
                    "evidence_ids": ["E-004"],
                }
            ],
            "privacy_boundary": "identity_free_evidence_references_only",
        }
        self.assertEqual([], validate_schema_instance(valid_alignment, alignment_schema))
        bad_alignment = copy.deepcopy(valid_alignment)
        bad_alignment["signal_bindings"][0]["unexpected"] = True
        self.assertTrue(validate_schema_instance(bad_alignment, alignment_schema))
        unknown_with_evidence = copy.deepcopy(valid_alignment)
        unknown_with_evidence["signal_bindings"][0]["support_state"] = "unknown"
        self.assertTrue(validate_schema_instance(unknown_with_evidence, alignment_schema))
        verified_without_evidence = copy.deepcopy(valid_alignment)
        verified_without_evidence["signal_bindings"][0]["evidence_ids"] = []
        self.assertTrue(validate_schema_instance(verified_without_evidence, alignment_schema))

        dossier_schema = self._schema("career-market-learning-dossier-v1.schema.json")
        fixture_root = ROOT.parent.parent / "tests/evals/with-skill/fixtures/career-market-learning-dossier"
        for name in ("complete-five-es.json", "limited-four-en.json", "unavailable-es.json"):
            with self.subTest(name=name):
                value = json.loads((fixture_root / name).read_text(encoding="utf-8"))
                self.assertEqual([], validate_schema_instance(value, dossier_schema))
                with_snapshot_copies = copy.deepcopy(value)
                with_snapshot_copies["search_summary"]["source_research_snapshot"] = value[
                    "source_research_snapshot"
                ]
                with_snapshot_copies["search_summary"][
                    "source_executive_dossier_snapshot"
                ] = value["source_executive_dossier_snapshot"]
                self.assertTrue(
                    validate_schema_instance(with_snapshot_copies, dossier_schema)
                )
        invalid = json.loads((fixture_root / "complete-five-es.json").read_text(encoding="utf-8"))
        invalid["unexpected"] = True
        self.assertTrue(validate_schema_instance(invalid, dossier_schema))

    def test_candidate_market_alignment_v2_schema_accepts_derived_fixture(self):
        fixture_root = ROOT.parent.parent / "tests/evals/with-skill/fixtures"
        research = json.loads(
            (fixture_root / "target-vacancy-research/complete-five-es.json").read_text(
                encoding="utf-8"
            )
        )
        dossier = json.loads(
            (fixture_root / "executive-career-dossier-v2/scenario-a-es.json").read_text(
                encoding="utf-8"
            )
        )
        schema = self._schema("candidate-market-alignment-v2.schema.json")
        alignment = derive_candidate_market_alignment_v2(research, dossier)

        self.assertEqual([], validate_schema_instance(alignment, schema))
        with_extra_field = copy.deepcopy(alignment)
        with_extra_field["signal_bindings"][0]["unexpected"] = True
        self.assertTrue(validate_schema_instance(with_extra_field, schema))

    def test_career_market_dossier_v2_schema_accepts_recomputed_fixtures(self):
        fixture_root = ROOT.parent.parent / "tests/evals/with-skill/fixtures"
        dossier_schema = self._schema("career-market-learning-dossier-v2.schema.json")
        cases = (
            ("complete-five-es.json", "scenario-a-es.json"),
            ("limited-four-en.json", "scenario-c-market-en.json"),
            ("unavailable-es.json", "scenario-a-es.json"),
        )
        for research_name, dossier_name in cases:
            with self.subTest(research=research_name):
                research = json.loads((fixture_root / "target-vacancy-research" / research_name).read_text(encoding="utf-8"))
                dossier = json.loads((fixture_root / "executive-career-dossier-v2" / dossier_name).read_text(encoding="utf-8"))
                fixture = json.loads((fixture_root / "career-market-learning-dossier-v2" / research_name).read_text(encoding="utf-8"))
                self.assertEqual([], validate_schema_instance(fixture, dossier_schema))
                self.assertEqual(fixture, build_market_dossier_v2(research, dossier))
                self.assertEqual([], validate_market_dossier_v2(fixture, research, dossier))
        extra = copy.deepcopy(build_market_dossier_v2(research, dossier))
        extra["unexpected"] = True
        self.assertTrue(validate_schema_instance(extra, dossier_schema))

    def test_career_learning_decision_schema_accepts_evaluated_and_unavailable_states(self):
        helper = _load_learning_contract_helper()
        schema = self._schema("career-learning-decision-v1.schema.json")
        evaluated = helper._bundle(count=3)
        self.assertEqual([], validate_schema_instance(evaluated, schema))
        unavailable = helper._bundle(state="unavailable")
        self.assertEqual([], validate_schema_instance(unavailable, schema))

        unknown_field = copy.deepcopy(evaluated)
        unknown_field["decisions"][0]["unexpected"] = True
        self.assertTrue(validate_schema_instance(unknown_field, schema))
        missing_provider_field = copy.deepcopy(evaluated)
        del missing_provider_field["decisions"][1]["provider_source"]["source_title"]
        self.assertTrue(validate_schema_instance(missing_provider_field, schema))
        inactive_provider = copy.deepcopy(evaluated)
        inactive_provider["decisions"][1]["provider_source"]["source_state"] = "unknown"
        self.assertTrue(validate_schema_instance(inactive_provider, schema))

    def test_career_learning_provider_research_schema_accepts_closed_fixtures(self):
        schema = self._schema("career-learning-provider-research-v1.schema.json")
        fixture_root = ROOT.parent.parent / "tests/evals/with-skill/fixtures/career-learning-provider-research"
        for name in ("complete-es.json", "limited-en.json", "unavailable-es.json"):
            with self.subTest(name=name):
                value = json.loads((fixture_root / name).read_text(encoding="utf-8"))
                self.assertEqual([], validate_schema_instance(value, schema))
                self.assertEqual([], validate_provider_research(value))
        extra = json.loads((fixture_root / "complete-es.json").read_text(encoding="utf-8"))
        extra["options"][0]["unexpected"] = True
        self.assertTrue(validate_schema_instance(extra, schema))

    def test_career_learning_decision_v2_schema_accepts_closed_fixtures(self):
        schema = self._schema("career-learning-decision-v2.schema.json")
        fixture_root = ROOT.parent.parent / "tests/evals/with-skill/fixtures"
        for name in ("complete-es.json", "limited-en.json", "unavailable-es.json"):
            with self.subTest(name=name):
                value = json.loads(
                    (fixture_root / "career-learning-decision-v2" / name).read_text(encoding="utf-8")
                )
                self.assertEqual([], validate_schema_instance(value, schema))
        complete = json.loads(
            (fixture_root / "career-learning-decision-v2/complete-es.json").read_text(encoding="utf-8")
        )
        extra = copy.deepcopy(complete)
        extra["decisions"][0]["caller_basis"] = "not allowed"
        self.assertTrue(validate_schema_instance(extra, schema))
        mismatched_rule = copy.deepcopy(complete)
        mismatched_rule["decisions"][0]["gap_type"] = "knowledge"
        self.assertTrue(validate_schema_instance(mismatched_rule, schema))

        research = json.loads((fixture_root / "target-vacancy-research/complete-five-es.json").read_text(encoding="utf-8"))
        dossier = json.loads((fixture_root / "executive-career-dossier-v2/scenario-a-es.json").read_text(encoding="utf-8"))
        market = build_market_dossier_v2(research, dossier)
        provider = json.loads((fixture_root / "career-learning-provider-research/complete-es.json").read_text(encoding="utf-8"))
        requests = [
            {key: row[key] for key in ("decision_rank", "decision_code", "source_signals", "provider_option_id")}
            for row in complete["decisions"]
        ]
        self.assertEqual(complete, build_learning_bundle_v2(research, market, dossier, provider, requests))
        self.assertEqual([], validate_learning_bundle_v2(complete, research, market, dossier, provider))

    def test_candidate_gap_response_v1_schema_accepts_closed_public_states(self):
        schema = self._schema("candidate-gap-response-v1.schema.json")
        snapshot = "0" * 64
        base = {
            "schema_version": "candidate-gap-response-v1",
            "locale": "es",
            "as_of_date": "2026-08-13",
            "source_research_snapshot": f"snap-market-sha256-{snapshot}",
            "source_market_snapshot": f"snap-market-dossier-v2-sha256-{snapshot}",
            "source_provider_research_snapshot": None,
            "response_state": "selection_required",
            "selected_vacancy_ordinal": None,
            "selected_signal": None,
            "relation": None,
            "selected_provider_ordinal": None,
            "privacy_boundary": "identity_free_closed_candidate_response_only",
            "draft_only": True,
            "no_external_action": True,
        }
        cases = []
        unavailable = copy.deepcopy(base)
        unavailable["response_state"] = "unavailable"
        cases.append(unavailable)
        cases.append(copy.deepcopy(base))
        partial = copy.deepcopy(base)
        partial.update(
            {
                "response_state": "partial",
                "selected_vacancy_ordinal": "V2",
                "selected_signal": "terraform",
                "relation": "unknown",
            }
        )
        cases.append(partial)
        complete = copy.deepcopy(partial)
        complete.update({"response_state": "complete", "relation": "proof_gap"})
        cases.append(complete)
        knowledge = copy.deepcopy(complete)
        knowledge.update(
            {
                "relation": "knowledge_gap",
                "selected_provider_ordinal": "L1",
                "source_provider_research_snapshot": f"snap-provider-sha256-{snapshot}",
            }
        )
        cases.append(knowledge)
        for value in cases:
            with self.subTest(state=value["response_state"], relation=value["relation"]):
                self.assertEqual([], validate_schema_instance(value, schema))

        private_id = copy.deepcopy(complete)
        private_id["selected_vacancy_id"] = "V-003"
        self.assertTrue(validate_schema_instance(private_id, schema))
        crossed_state = copy.deepcopy(partial)
        crossed_state["response_state"] = "complete"
        self.assertTrue(validate_schema_instance(crossed_state, schema))

        fixture_root = ROOT.parent.parent / "tests/evals/with-skill/fixtures"
        research = json.loads(
            (fixture_root / "target-vacancy-research/complete-five-es.json").read_text(
                encoding="utf-8"
            )
        )
        research["vacancies"][0]["requirements"][0]["signal"] = "terraform"
        dossier = json.loads(
            (fixture_root / "executive-career-dossier-v2/scenario-a-es.json").read_text(
                encoding="utf-8"
            )
        )
        market = build_market_dossier_v2(research, dossier)
        built = build_candidate_gap_response_v1(
            research,
            market,
            {
                "selected_vacancy_ordinal": "V2",
                "selected_signal": "terraform",
                "relation": "proof_gap",
                "selected_provider_ordinal": None,
            },
        )
        self.assertEqual([], validate_schema_instance(built, schema))
        self.assertEqual(
            [], validate_candidate_gap_response_v1(built, research, market)
        )

    def test_target_vacancy_research_schema_accepts_closed_synthetic_states(self):
        schema = self._schema("target-vacancy-research-v1.schema.json")
        fixture_root = ROOT.parent.parent / "tests/evals/with-skill/fixtures/target-vacancy-research"
        for name in ("complete-five-es.json", "limited-four-en.json", "unavailable-es.json"):
            with self.subTest(name=name):
                value = json.loads((fixture_root / name).read_text(encoding="utf-8"))
                self.assertEqual([], validate_schema_instance(value, schema))
                self.assertEqual([], validate_research(value))
        invalid = json.loads((fixture_root / "complete-five-es.json").read_text(encoding="utf-8"))
        invalid["vacancies"][0]["unexpected"] = True
        self.assertTrue(validate_schema_instance(invalid, schema))

    def test_executive_dossier_v2_schema_accepts_ledger_and_closes_new_fields(self):
        helper = _load_v2_dossier_helper()
        dossier = helper.make_v2_dossier()
        schema = self._schema("executive-career-dossier-v2.schema.json")
        self.assertEqual([], validate_schema_instance(dossier, schema))
        validator = helper.load_validator()
        fixture_root = ROOT.parent.parent / "tests/evals/with-skill/fixtures/executive-career-dossier-v2"
        for name in ("scenario-a-es.json", "scenario-c-en.json", "scenario-c-market-en.json"):
            with self.subTest(name=name):
                fixture = json.loads((fixture_root / name).read_text(encoding="utf-8"))
                self.assertEqual([], validate_schema_instance(fixture, schema))
                self.assertEqual([], validator.validate_dossier(fixture))
        missing_ledger = copy.deepcopy(dossier)
        del missing_ledger["section_coverage"]
        self.assertTrue(validate_schema_instance(missing_ledger, schema))
        missing_request = copy.deepcopy(dossier)
        del missing_request["section_coverage"][2]["inspection_request"]
        self.assertTrue(validate_schema_instance(missing_request, schema))
        missing_priority = copy.deepcopy(dossier)
        del missing_priority["priorities"][0]["client_template"]
        self.assertTrue(validate_schema_instance(missing_priority, schema))
        inherited_v1 = copy.deepcopy(dossier)
        inherited_v1["focus"] = {}
        self.assertTrue(validate_schema_instance(inherited_v1, schema))
        for reason, decision in (
            ("authorization_required", "declined_for_session"),
            ("inspection_declined", "authorized_inspection_failed"),
            ("authorized_inspection_failed", "pending_response"),
        ):
            mismatched = copy.deepcopy(dossier)
            mismatched["section_coverage"][10]["reason"] = reason
            mismatched["section_coverage"][10]["inspection_request"]["decision"] = decision
            self.assertTrue(validate_schema_instance(mismatched, schema))

    def test_executive_dossier_v2_runtime_uses_the_schema_checker(self):
        helper = _load_v2_dossier_helper()
        validator = helper.load_validator()
        dossier = helper.make_v2_dossier()
        dossier["section_coverage"][0]["availability"] = "unsupported"
        errors = validator.validate_dossier(dossier)
        self.assertIn("v2 schema validation failed", errors)
        self.assertNotIn("unsupported", "\n".join(errors))

    def test_all_private_conversion_and_followthrough_fixtures_conform(self):
        cases = [
            ("private-recruiter-conversion-outcome-v1.schema.json", ROOT / "tests/fixtures/private-recruiter-conversion-outcome"),
            ("private-recruiter-followthrough-checkpoint-v1.schema.json", ROOT / "tests/fixtures/private-recruiter-followthrough-checkpoint"),
        ]
        for schema_name, directory in cases:
            schema = self._schema(schema_name)
            for path in directory.glob("*.json"):
                value = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual([], validate_schema_instance(value, schema), (schema_name, path.name))

    def test_mutations_fail_closed_for_date_closure_and_invariants(self):
        schema = self._schema("private-recruiter-followthrough-checkpoint-v1.schema.json")
        source = json.loads((ROOT / "tests/fixtures/private-recruiter-followthrough-checkpoint/accepted-en.json").read_text(encoding="utf-8"))
        mutations = []
        bad = copy.deepcopy(source); bad["observed_date"] = "2026-02-30"; mutations.append(bad)
        bad = copy.deepcopy(source); bad["unexpected"] = True; mutations.append(bad)
        bad = copy.deepcopy(source); bad["next_safe_action"] = "record_stop_decision"; mutations.append(bad)
        bad = copy.deepcopy(source); bad["next_measurement_event"] = "screen_prepared"; mutations.append(bad)
        for value in mutations:
            self.assertTrue(validate_schema_instance(value, schema), value)

    def test_conversion_mutations_fail_closed_for_date_closure_and_action(self):
        schema = self._schema("private-recruiter-conversion-outcome-v1.schema.json")
        source = json.loads((ROOT / "tests/fixtures/private-recruiter-conversion-outcome/screen-requested-en.json").read_text(encoding="utf-8"))
        mutations = []
        bad = copy.deepcopy(source); bad["event_date"] = "2026-02-30"; mutations.append(bad)
        bad = copy.deepcopy(source); bad["unexpected"] = True; mutations.append(bad)
        bad = copy.deepcopy(source); bad["next_safe_action"] = "record_stop_decision"; mutations.append(bad)
        for value in mutations:
            self.assertTrue(validate_schema_instance(value, schema), value)

    def test_semantic_validators_cover_all_private_fixtures(self):
        self.assertEqual([], validate_private_fixture_semantics(ROOT, as_of=dt.date(2026, 8, 9)))

    def test_triage_schema_uses_canonical_screen_opening_scope(self):
        schema = self._schema("private-recruiter-reply-triage-v1.schema.json")
        fixture = json.loads(
            (
                ROOT.parent.parent
                / "tests/evals/with-skill/fixtures/private-recruiter-reply-triage/ready-es.json"
            ).read_text(encoding="utf-8")
        )
        canonical = copy.deepcopy(fixture)
        canonical["handoff"]["packet"]["prep_scope"] = "screen_opening"
        canonical["handoff"]["reentry_packet"]["prep_scope"] = "screen_opening"
        self.assertEqual([], validate_schema_instance(canonical, schema))

        for field in ("packet", "reentry_packet"):
            with self.subTest(field=field):
                removed_alias = copy.deepcopy(canonical)
                removed_alias["handoff"][field]["prep_scope"] = "recruiter_screen_opening"
                self.assertIn(
                    f"$.handoff.{field}.prep_scope: enum mismatch",
                    validate_schema_instance(removed_alias, schema),
                )

    def test_triage_v2_schema_accepts_independent_ui_and_content_locales(self):
        fixture = json.loads(
            (ROOT.parent.parent / "tests/evals/with-skill/fixtures/private-recruiter-reply-triage/ready-es.json").read_text(encoding="utf-8")
        )
        fixture["schema_version"] = "private-recruiter-reply-triage-v2"
        fixture["ui_locale"] = "en"
        fixture["content_locale"] = "es"
        del fixture["locale"]
        fixture["handoff"]["packet"]["source_snapshot"] = V2_READY_ES_SNAPSHOT
        fixture["handoff"]["reentry_packet"]["source_snapshot"] = V2_READY_ES_SNAPSHOT
        schema = self._schema("private-recruiter-reply-triage-v2.schema.json")
        self.assertEqual([], validate_triage(fixture))
        self.assertEqual([], validate_schema_instance(fixture, schema))

        missing = copy.deepcopy(fixture)
        del missing["content_locale"]
        self.assertTrue(validate_schema_instance(missing, schema))

    def test_triage_v2_snapshot_binding_rejects_content_drift(self):
        fixture = json.loads(
            (ROOT.parent.parent / "tests/evals/with-skill/fixtures/private-recruiter-reply-triage/ready-es.json").read_text(encoding="utf-8")
        )
        fixture["schema_version"] = "private-recruiter-reply-triage-v2"
        fixture["ui_locale"] = "en"
        fixture["content_locale"] = "es"
        del fixture["locale"]
        fixture["handoff"]["packet"]["source_snapshot"] = V2_READY_ES_SNAPSHOT
        fixture["handoff"]["reentry_packet"]["source_snapshot"] = V2_READY_ES_SNAPSHOT
        self.assertEqual([], validate_triage(fixture))
        changed = "A different safe summary with altered role constraints."
        fixture["safe_context"]["summary"] = changed
        fixture["handoff"]["packet"]["context_summary"] = changed
        fixture["handoff"]["reentry_packet"]["context_summary"] = changed
        self.assertTrue(validate_triage(fixture))

    def test_triage_identifier_patterns_require_json_strings_in_v1_and_v2(self):
        source = json.loads(
            (ROOT.parent.parent / "tests/evals/with-skill/fixtures/private-recruiter-reply-triage/ready-en.json").read_text(encoding="utf-8")
        )
        versions = []
        v1 = (copy.deepcopy(source), self._schema("private-recruiter-reply-triage-v1.schema.json"))
        versions.append(v1)
        v2 = copy.deepcopy(source)
        v2["schema_version"] = "private-recruiter-reply-triage-v2"
        v2["ui_locale"] = "en"
        v2["content_locale"] = "es"
        del v2["locale"]
        versions.append((v2, self._schema("private-recruiter-reply-triage-v2.schema.json")))
        mutations = (
            ("facts", 0, "id"),
            ("question", "id"),
            ("question", "fact_ids", 0),
            ("handoff", "packet", "source_snapshot"),
            ("handoff", "packet", "fact_id"),
            ("handoff", "packet", "question_id"),
            ("handoff", "reentry_packet", "source_snapshot"),
            ("handoff", "reentry_packet", "fact_id"),
            ("handoff", "reentry_packet", "question_id"),
        )
        for version_index, (fixture, schema) in enumerate(versions):
            for path in mutations:
                with self.subTest(version=version_index, path=path):
                    mutated = copy.deepcopy(fixture)
                    target = mutated
                    for key in path[:-1]:
                        target = target[key]
                    target[path[-1]] = 123
                    self.assertTrue(validate_triage(mutated))
                    self.assertTrue(validate_schema_instance(mutated, schema))

    def test_practice_schema_binds_source_to_snapshot_prefix(self):
        schema = self._schema("recruiter-practice-session-v1.schema.json")
        fixture = json.loads((ROOT.parent.parent / "tests/evals/with-skill/fixtures/recruiter-practice-session/session-es.json").read_text(encoding="utf-8"))
        dossier_snapshot = copy.deepcopy(fixture)
        dossier_snapshot["handoff_context"]["source_snapshot"] = "snap-triage-001"
        self.assertTrue(validate_schema_instance(dossier_snapshot, schema), "dossier source must reject triage snapshot")
        triage_snapshot = copy.deepcopy(fixture)
        triage_snapshot["handoff_context"]["source"] = "private_recruiter_reply_triage"
        triage_snapshot["handoff_context"]["source_snapshot"] = "snap-dossier-001"
        triage_snapshot["handoff_context"]["question_kind"] = triage_snapshot["question"]["kind"]
        triage_snapshot["handoff_context"].pop("claim_ids")
        triage_snapshot["handoff_context"].pop("evidence_ids")
        self.assertTrue(validate_schema_instance(triage_snapshot, schema), "triage source must reject dossier snapshot")
        triage_snapshot["handoff_context"]["source_snapshot"] = "snap-triage-001"
        self.assertEqual([], validate_schema_instance(triage_snapshot, schema))

    def test_practice_triage_handoff_question_kind_is_closed_and_required(self):
        source = json.loads(
            (ROOT.parent.parent / "tests/evals/with-skill/fixtures/recruiter-practice-session/session-es.json").read_text(encoding="utf-8")
        )
        kinds = (
            "screen_opening",
            "proof_example",
            "eligibility_boundary",
            "compensation_boundary",
            "missing_detail",
        )
        for schema_name, snapshot in (
            ("recruiter-practice-session-v1.schema.json", "snap-triage-001"),
            ("recruiter-practice-session-v2.schema.json", V2_TRIAGE_PRACTICE_SNAPSHOT),
        ):
            schema = self._schema(schema_name)
            for kind in kinds:
                with self.subTest(schema=schema_name, kind=kind):
                    canonical = copy.deepcopy(source)
                    canonical["handoff_context"]["source"] = "private_recruiter_reply_triage"
                    canonical["handoff_context"]["source_snapshot"] = snapshot
                    canonical["handoff_context"]["question_kind"] = kind
                    canonical["question"]["kind"] = kind
                    canonical["handoff_context"].pop("claim_ids")
                    canonical["handoff_context"].pop("evidence_ids")
                    if schema_name.endswith("-v2.schema.json"):
                        canonical["schema_version"] = "recruiter-practice-session-v2"
                        canonical["ui_locale"] = "en"
                        canonical["content_locale"] = "es"
                        del canonical["locale"]
                    self.assertEqual([], validate_schema_instance(canonical, schema))
                    self.assertEqual([], validate_session(canonical))

                    missing = copy.deepcopy(canonical)
                    del missing["handoff_context"]["question_kind"]
                    self.assertTrue(validate_schema_instance(missing, schema))
                    self.assertTrue(validate_session(missing))

                    invalid = copy.deepcopy(canonical)
                    invalid["handoff_context"]["question_kind"] = "not-a-question-kind"
                    self.assertTrue(validate_schema_instance(invalid, schema))
                    self.assertTrue(validate_session(invalid))

            dossier = copy.deepcopy(source)
            if schema_name.endswith("-v2.schema.json"):
                dossier["schema_version"] = "recruiter-practice-session-v2"
                dossier["ui_locale"] = "en"
                dossier["content_locale"] = "es"
                del dossier["locale"]
            self.assertEqual([], validate_schema_instance(dossier, schema))

    def test_practice_v2_schema_accepts_independent_ui_and_content_locales(self):
        fixture = json.loads(
            (ROOT.parent.parent / "tests/evals/with-skill/fixtures/recruiter-practice-session/session-es.json").read_text(encoding="utf-8")
        )
        fixture["schema_version"] = "recruiter-practice-session-v2"
        fixture["ui_locale"] = "en"
        fixture["content_locale"] = "es"
        del fixture["locale"]

        self.assertEqual([], validate_session(fixture))
        self.assertEqual(
            [],
            validate_schema_instance(
                fixture,
                self._schema("recruiter-practice-session-v2.schema.json"),
            ),
        )

    def test_practice_v2_accepts_triage_content_bound_snapshot_and_v1_rejects_it(self):
        fixture = json.loads(
            (ROOT.parent.parent / "tests/evals/with-skill/fixtures/recruiter-practice-session/session-es.json").read_text(encoding="utf-8")
        )
        fixture["schema_version"] = "recruiter-practice-session-v2"
        fixture["ui_locale"] = "en"
        fixture["content_locale"] = "es"
        del fixture["locale"]
        fixture["handoff_context"]["source"] = "private_recruiter_reply_triage"
        fixture["handoff_context"]["source_snapshot"] = V2_TRIAGE_PRACTICE_SNAPSHOT
        fixture["handoff_context"]["question_kind"] = fixture["question"]["kind"]
        fixture["handoff_context"].pop("claim_ids")
        fixture["handoff_context"].pop("evidence_ids")
        schema = self._schema("recruiter-practice-session-v2.schema.json")
        self.assertEqual([], validate_session(fixture))
        self.assertEqual([], validate_schema_instance(fixture, schema))

        v1 = copy.deepcopy(fixture)
        v1["schema_version"] = "recruiter-practice-session-v1"
        v1["locale"] = "es"
        del v1["ui_locale"]
        del v1["content_locale"]
        self.assertTrue(validate_session(v1))
        self.assertTrue(validate_schema_instance(v1, self._schema("recruiter-practice-session-v1.schema.json")))

    def test_practice_question_rank_custom_validator_matches_schema_for_boolean_values(self):
        schema = self._schema("recruiter-practice-session-v1.schema.json")
        fixture = json.loads((ROOT.parent.parent / "tests/evals/with-skill/fixtures/recruiter-practice-session/session-es.json").read_text(encoding="utf-8"))
        for invalid_rank in (True, False):
            with self.subTest(question_rank=repr(invalid_rank)):
                mutated = copy.deepcopy(fixture)
                mutated["handoff_context"]["question_rank"] = invalid_rank
                self.assertTrue(validate_session(mutated))
                self.assertTrue(validate_schema_instance(mutated, schema))

        self.assertEqual([], validate_session(fixture))
        self.assertEqual([], validate_schema_instance(fixture, schema))

    def test_practice_question_rank_custom_validator_accepts_json_numeric_one(self):
        fixture = json.loads((ROOT.parent.parent / "tests/evals/with-skill/fixtures/recruiter-practice-session/session-es.json").read_text(encoding="utf-8"))
        fixture["handoff_context"]["question_rank"] = 1.0
        self.assertEqual([], validate_session(fixture))

    def test_schema_prose_mutations_match_custom_unicode_boundary(self):
        controls = ("\u200b", "\u202e", "\u2066", "\ufeff")
        cases = (
            (
                "private-recruiter-reply-triage-v1.schema.json",
                ROOT.parent.parent / "tests/evals/with-skill/fixtures/private-recruiter-reply-triage/ready-es.json",
                ("facts", 0, "summary"),
                validate_triage,
            ),
            (
                "recruiter-practice-session-v1.schema.json",
                ROOT.parent.parent / "tests/evals/with-skill/fixtures/recruiter-practice-session/session-es.json",
                ("facts", 0, "summary"),
                validate_session,
            ),
        )
        for schema_name, fixture_path, field_path, custom_validator in cases:
            schema = self._schema(schema_name)
            canonical = json.loads(fixture_path.read_text(encoding="utf-8"))
            self.assertEqual([], validate_schema_instance(canonical, schema))
            for control in controls:
                with self.subTest(schema=schema_name, code_point=f"U+{ord(control):04X}"):
                    mutated = copy.deepcopy(canonical)
                    target = mutated
                    for part in field_path[:-1]:
                        target = target[part]
                    target[field_path[-1]] = f"Safe prefix{control} hidden"
                    custom_errors = custom_validator(mutated)
                    schema_errors = validate_schema_instance(mutated, schema)
                    self.assertFalse(is_safe_prose_text(target[field_path[-1]]))
                    self.assertTrue(custom_errors)
                    self.assertTrue(schema_errors)
                    for error in custom_errors + schema_errors:
                        self.assertLess(len(error), 240)
                        self.assertNotIn(target[field_path[-1]], error)

    def test_dossier_schema_prose_mutations_match_custom_unicode_boundary(self):
        fixture = json.loads(
            (ROOT / "tests/fixtures/dossier-recruiter-practice-handoff/valid-es.json").read_text(
                encoding="utf-8"
            )
        )
        dossier = json.loads(
            (
                ROOT.parent.parent
                / "tests/evals/with-skill/fixtures/executive-career-dossier"
                / fixture["base_dossier_fixture"]
            ).read_text(encoding="utf-8")
        )
        dossier["screen_bridge"] = fixture["dossier_overrides"]["screen_bridge"]
        dossier["questions"][0]["linked_copy_category"] = fixture["dossier_overrides"]["question_linked_copy_category"]
        dossier["copy_blocks"][1].update(fixture["dossier_overrides"]["about_opening"])
        practice = json.loads(
            (
                ROOT.parent.parent
                / "tests/evals/with-skill/fixtures/recruiter-practice-session/session-es.json"
            ).read_text(encoding="utf-8")
        )
        handoff = build_handoff(dossier, fixture["vacancy"], fixture["source_snapshot"])
        schema = self._schema("dossier-recruiter-practice-handoff-v1.schema.json")
        self.assertEqual([], validate_schema_instance(handoff, schema))
        for control in ("\u200b", "\u202e", "\u2066", "\ufeff"):
            with self.subTest(code_point=f"U+{ord(control):04X}"):
                mutated = copy.deepcopy(handoff)
                mutated["dossier_projection"]["fact_summary"] = f"Safe prefix{control} hidden"
                custom_errors = validate_handoff(mutated, dossier, fixture["vacancy"], practice)
                schema_errors = validate_schema_instance(mutated, schema)
                self.assertFalse(is_safe_prose_text(mutated["dossier_projection"]["fact_summary"]))
                self.assertTrue(custom_errors)
                self.assertTrue(schema_errors)
                for error in custom_errors + schema_errors:
                    self.assertLess(len(error), 240)
                    self.assertNotIn(mutated["dossier_projection"]["fact_summary"], error)

    def test_dossier_handoff_rejects_unlabelled_person_name_source_fact(self):
        fixture = json.loads(
            (ROOT / "tests/fixtures/dossier-recruiter-practice-handoff/valid-es.json").read_text(
                encoding="utf-8"
            )
        )
        dossier = json.loads(
            (
                ROOT.parent.parent
                / "tests/evals/with-skill/fixtures/executive-career-dossier"
                / fixture["base_dossier_fixture"]
            ).read_text(encoding="utf-8")
        )
        dossier["screen_bridge"] = fixture["dossier_overrides"]["screen_bridge"]
        dossier["questions"][0]["linked_copy_category"] = fixture["dossier_overrides"]["question_linked_copy_category"]
        dossier["copy_blocks"][1].update(fixture["dossier_overrides"]["about_opening"])
        handoff = build_handoff(dossier, fixture["vacancy"], fixture["source_snapshot"])
        practice = json.loads(
            (
                ROOT.parent.parent
                / "tests/evals/with-skill/fixtures/recruiter-practice-session/session-es.json"
            ).read_text(encoding="utf-8")
        )
        target = "Ana López reports Terraform experience."
        mutated = copy.deepcopy(handoff)
        mutated["dossier_projection"]["fact_summary"] = target
        mutated["practice_projection"]["facts"][0]["summary"] = target
        custom_errors = validate_handoff(mutated, dossier, fixture["vacancy"], practice)
        schema_errors = validate_schema_instance(mutated, self._schema("dossier-recruiter-practice-handoff-v1.schema.json"))
        self.assertTrue(custom_errors)
        self.assertTrue(schema_errors)
        for error in custom_errors + schema_errors:
            self.assertLess(len(error), 240)
            self.assertNotIn(target, error)

    def test_handoff_pair_rejects_an_unrelated_shape_valid_projection(self):
        fixture = json.loads(
            (ROOT / "tests/fixtures/dossier-recruiter-practice-handoff/valid-es.json").read_text(
                encoding="utf-8"
            )
        )
        dossier = json.loads(
            (
                ROOT.parent.parent
                / "tests/evals/with-skill/fixtures/executive-career-dossier"
                / fixture["base_dossier_fixture"]
            ).read_text(encoding="utf-8")
        )
        dossier["screen_bridge"] = fixture["dossier_overrides"]["screen_bridge"]
        dossier["questions"][0]["linked_copy_category"] = fixture["dossier_overrides"]["question_linked_copy_category"]
        dossier["copy_blocks"][1].update(fixture["dossier_overrides"]["about_opening"])
        handoff = build_handoff(dossier, fixture["vacancy"], fixture["source_snapshot"])
        practice = json.loads(
            (
                ROOT.parent.parent / "tests/evals/with-skill/fixtures/recruiter-practice-session/session-es.json"
            ).read_text(encoding="utf-8")
        )

        unrelated = copy.deepcopy(handoff)
        projection = unrelated["practice_projection"]
        projection["handoff_context"].update(
            {
                "claim_ids": ["C-001"],
                "evidence_ids": ["E-001"],
            }
        )
        unrelated["dossier_projection"].update(
            {
                "claim_ids": ["C-001"],
                "evidence_ids": ["E-001"],
                "question_evidence_ids": ["E-001"],
                "source_fact_evidence_id": "E-001",
            }
        )
        practice.update(copy.deepcopy(projection))

        schema = self._schema("dossier-recruiter-practice-handoff-v1.schema.json")
        self.assertEqual([], validate_schema_instance(unrelated, schema))
        errors = validate_handoff(unrelated, dossier, fixture["vacancy"], practice)
        self.assertIn(
            "handoff.dossier_projection.claim_ids must match dossier source projection",
            errors,
        )
        self.assertIn(
            "handoff.practice_projection.handoff_context.claim_ids must match expected practice projection",
            errors,
        )

    def test_semantic_mutations_fail_closed_with_deterministic_errors(self):
        outcome = json.loads((ROOT / "tests/fixtures/private-recruiter-conversion-outcome/screen-requested-en.json").read_text(encoding="utf-8"))
        checkpoint = json.loads((ROOT / "tests/fixtures/private-recruiter-followthrough-checkpoint/accepted-en.json").read_text(encoding="utf-8"))
        receipt = outcome
        mutations = []
        bad = copy.deepcopy(outcome); bad["event_date"] = "2026-08-10"; mutations.append(("outcome", bad, "event_date"))
        bad = copy.deepcopy(checkpoint); bad["source_receipt"]["event_type"] = "stop_decision"; mutations.append(("checkpoint", bad, "source_receipt.event_type"))
        bad = copy.deepcopy(checkpoint); bad["delivery"]["external_actions_authorized"] = True; mutations.append(("checkpoint", bad, "delivery.external_actions_authorized"))
        bad = copy.deepcopy(outcome); bad["next_safe_action"] = "record_stop_decision"; mutations.append(("outcome", bad, "next_safe_action"))
        for kind, value, expected in mutations:
            if kind == "outcome":
                errors = validate_outcome_for_test(value, as_of=dt.date(2026, 8, 9))
            else:
                errors = validate_checkpoint_for_test(value, receipt, as_of=dt.date(2026, 8, 9))
            self.assertTrue(any(expected in error for error in errors), (kind, expected, errors))

    def test_dependency_free_checker_enforces_string_lengths_and_combinators(self):
        schema = {
            "type": "object",
            "properties": {
                "label": {"type": "string", "minLength": 2, "maxLength": 4},
                "mode": {
                    "oneOf": [{"const": "draft"}, {"const": "published"}],
                    "not": {"const": "blocked"},
                },
                "signal": {"anyOf": [{"const": "email"}, {"const": "screen"}]},
            },
            "required": ["label", "mode", "signal"],
        }
        self.assertEqual([], validate_schema_instance({"label": "ok", "mode": "draft", "signal": "email"}, schema))
        for value, expected in (
            ({"label": "x", "mode": "draft", "signal": "email"}, "string too short"),
            ({"label": "toolong", "mode": "draft", "signal": "email"}, "string too long"),
            ({"label": "ok", "mode": "other", "signal": "email"}, "oneOf mismatch"),
            ({"label": "ok", "mode": "blocked", "signal": "email"}, "not mismatch"),
            ({"label": "ok", "mode": "draft", "signal": "chat"}, "anyOf mismatch"),
        ):
            self.assertTrue(any(expected in error for error in validate_schema_instance(value, schema)), (value, expected))

    def test_dependency_free_checker_bounds_nested_combinator_evaluations(self):
        schema = {"const": "ok"}
        for _ in range(13):
            schema = {"oneOf": [schema, copy.deepcopy(schema)]}

        errors = validate_schema_instance("not-ok", schema)

        self.assertIn("schema validation exceeds safe evaluation limit", errors)

    def test_dependency_free_checker_bounds_cyclic_schema_references(self):
        schema = {"$defs": {}}
        schema["$defs"]["loop"] = {"$ref": "#/$defs/loop"}
        schema["$ref"] = "#/$defs/loop"

        errors = validate_schema_instance({}, schema)

        self.assertIn("schema validation exceeds safe evaluation limit", errors)

    def test_dependency_free_checker_rejects_missing_schema_references(self):
        errors = validate_schema_instance({}, {"$ref": "#/missing"})

        self.assertIn("schema reference is invalid", errors)

        errors = validate_schema_instance(
            {}, {"$defs": {"scalar": "not a schema"}, "$ref": "#/$defs/scalar"}
        )
        self.assertIn("schema reference is invalid", errors)

    def test_dependency_free_checker_rejects_non_object_combinator_branches(self):
        malformed_schemas = (
            {"oneOf": [None]},
            {"anyOf": ["invalid"]},
            {"allOf": [None]},
            {"if": None},
            {"not": None},
        )
        for schema in malformed_schemas:
            with self.subTest(schema=schema):
                errors = validate_schema_instance({}, schema)
                self.assertIn("schema branch is invalid", errors)

    def test_dependency_free_checker_rejects_malformed_keyword_shapes(self):
        malformed_schemas = (
            ({}, {"type": "object", "properties": None}),
            ({}, {"type": "object", "required": None}),
            ({}, {"enum": None}),
            (1, {"type": "number", "minimum": "a"}),
            ([1], {"type": "array", "minItems": "a"}),
        )
        for value, schema in malformed_schemas:
            with self.subTest(schema=schema):
                errors = validate_schema_instance(value, schema)
                self.assertIn("schema keyword is invalid", errors)

    def test_dependency_free_checker_rejects_complete_malformed_keyword_grammar(self):
        malformed_keywords = (
            ({}, {"type": "object", "required": [[]]}),
            ({}, {"type": "object", "required": ["missing", "missing"]}),
            (1, {"type": {}}),
            (1, {"type": []}),
            (1, {"type": ["integer", "unsupported"]}),
        )
        for value, schema in malformed_keywords:
            with self.subTest(schema=schema):
                try:
                    errors = validate_schema_instance(value, schema)
                except Exception as error:  # pragma: no cover - reports unsafe production
                    self.fail(f"validator raised {type(error).__name__}")
                self.assertEqual(
                    ["schema keyword is invalid"],
                    errors,
                )

        malformed_branches = (
            ([], {"type": "array", "items": None}),
            ([], {"type": "array", "contains": None}),
        )
        for value, schema in malformed_branches:
            with self.subTest(schema=schema):
                self.assertEqual(
                    ["schema branch is invalid"],
                    validate_schema_instance(value, schema),
                )

    def test_dependency_free_checker_preflights_the_complete_schema_grammar(self):
        malformed_keywords = (
            ({}, {"properties": {"absent": {"required": [[]]}}}, "schema keyword is invalid"),
            ({}, {"properties": {"absent": {"pattern": "["}}}, "schema pattern is invalid"),
            ({}, {"enum": []}, "schema keyword is invalid"),
            ({}, {"additionalProperties": "false"}, "schema keyword is invalid"),
            ([], {"uniqueItems": "false"}, "schema keyword is invalid"),
            ("2026-08-14", {"format": "datetime"}, "schema keyword is invalid"),
            ("2026-08-14", {"format": 1}, "schema keyword is invalid"),
        )
        for value, schema, expected in malformed_keywords:
            with self.subTest(schema=schema):
                try:
                    errors = validate_schema_instance(value, schema)
                except Exception as error:  # pragma: no cover - reports unsafe production
                    self.fail(f"validator raised {type(error).__name__}")
                self.assertEqual([expected], errors)

        malformed_branches = (
            ({}, {"$defs": {"unused": None}}),
            ({}, {"allOf": []}),
            ({}, {"oneOf": []}),
            ({}, {"anyOf": []}),
        )
        for value, schema in malformed_branches:
            with self.subTest(schema=schema):
                self.assertEqual(
                    ["schema branch is invalid"],
                    validate_schema_instance(value, schema),
                )

        safe_schemas = (
            ({}, {"type": "object", "properties": {"absent": {"required": ["field"]}}}),
            ({}, {"type": "object", "$defs": {"unused": {"type": "string"}}}),
            ({}, {"allOf": [{"type": "object"}]}),
            ({}, {"oneOf": [{"type": "object"}]}),
            ({}, {"anyOf": [{"type": "object"}]}),
            ({}, {"enum": [{}]}),
            ({}, {"additionalProperties": False}),
            ([], {"type": "array", "uniqueItems": False}),
            ("2026-08-14", {"type": "string", "format": "date"}),
        )
        for value, schema in safe_schemas:
            with self.subTest(schema=schema, control="safe"):
                self.assertEqual([], validate_schema_instance(value, schema))

    def test_dependency_free_checker_rejects_duplicate_enum_values_cycle_safely(self):
        cyclic_left = []
        cyclic_left.append(cyclic_left)
        cyclic_right = []
        cyclic_right.append(cyclic_right)
        duplicate_enums = (
            ["same", "same"],
            [{"nested": [1, 2]}, {"nested": [1, 2]}],
            [1, 1.0],
            [cyclic_left, cyclic_right],
        )
        for enum in duplicate_enums:
            with self.subTest(enum=enum):
                self.assertEqual(
                    ["schema keyword is invalid"],
                    validate_schema_instance(enum[0], {"enum": enum}),
                )

        self.assertEqual([], validate_schema_instance(True, {"enum": [True, 1]}))

    def test_dependency_free_checker_rejects_deep_duplicate_enum_without_recursion(self):
        def nested_value(depth):
            value = "leaf"
            for _ in range(depth):
                value = [value]
            return value

        def nested_mapping(depth):
            value = "leaf"
            for _ in range(depth):
                value = {"value": value}
            return value

        def nested_mixed(depth):
            value = "leaf"
            for index in range(depth):
                value = [value] if index % 2 else {"value": value}
            return value

        for duplicate in (
            [nested_value(600), nested_value(600)],
            [nested_mapping(600), nested_mapping(600)],
            [nested_mixed(600), nested_mixed(600)],
        ):
            with self.subTest(container=type(duplicate[0]).__name__):
                self.assertEqual(
                    ["schema keyword is invalid"],
                    validate_schema_instance(None, {"enum": duplicate}),
                )

    def test_dependency_free_checker_bounds_large_unique_enum_preflight(self):
        probe = (
            "import json,sys;"
            "sys.path.insert(0,sys.argv[1]);"
            "from validate_json_schema_subset import validate_schema_instance;"
            "enum=list(range(4000));"
            "print(json.dumps(validate_schema_instance(enum[0],{'enum':enum})))"
        )
        try:
            result = subprocess.run(
                [sys.executable, "-B", "-c", probe, str(ROOT / "scripts")],
                text=True,
                capture_output=True,
                check=False,
                timeout=1.0,
            )
        except subprocess.TimeoutExpired:
            self.fail("large unique enum preflight exceeded safe timeout")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual([], json.loads(result.stdout))

    def test_dependency_free_checker_bounds_compound_enum_preflight_work(self):
        probe = (
            "import json,sys;"
            "sys.path.insert(0,sys.argv[1]);"
            "from validate_json_schema_subset import validate_schema_instance;"
            "enum=[[index]*1024 for index in range(4096)];"
            "print(json.dumps(validate_schema_instance(None,{'enum':enum})))"
        )
        try:
            result = subprocess.run(
                [sys.executable, "-B", "-c", probe, str(ROOT / "scripts")],
                text=True,
                capture_output=True,
                check=False,
                timeout=1.0,
            )
        except subprocess.TimeoutExpired:
            self.fail("compound enum preflight exceeded safe timeout")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn(
            json.loads(result.stdout),
            (
                ["schema validation exceeds safe evaluation limit"],
                ["schema keyword is invalid"],
            ),
        )

        safe_enum = [[index, {"value": index}] for index in range(32)]
        self.assertEqual(
            [],
            validate_schema_instance(safe_enum[0], {"enum": safe_enum}),
        )

    def test_dependency_free_checker_rejects_invalid_regex_patterns(self):
        for pattern in ("[", "(?", r"\K"):
            with self.subTest(pattern=pattern):
                errors = validate_schema_instance("x", {"pattern": pattern})
                self.assertIn("schema pattern is invalid", errors)

    def test_dependency_free_checker_rejects_nested_unbounded_regex(self):
        errors = validate_schema_instance(
            "a" * 22 + "!", {"type": "string", "pattern": "(a+)+$"}
        )

        self.assertEqual(["$: pattern exceeds safe complexity limit"], errors)

    def test_dependency_free_checker_rejects_structural_redos_bypasses_within_timeout(self):
        probe = (
            "import json,sys;"
            "sys.path.insert(0,sys.argv[1]);"
            "from validate_json_schema_subset import validate_schema_instance;"
            "print(json.dumps(validate_schema_instance("
            "sys.argv[2],{'type':'string','pattern':sys.argv[3]})))"
        )
        cases = (
            ("((a+))+$", "a" * 26 + "!"),
            ("(a|aa)+$", "a" * 38 + "!"),
            ("(a|a)+$", "a" * 38 + "!"),
            ("(a?|a)+$", "a" * 30 + "!"),
            ("(a|[a])+$", "a" * 30 + "!"),
            ("([a]|a)+$", "a" * 30 + "!"),
            ("([ab]|a)+$", "a" * 30 + "!"),
        )
        for pattern, value in cases:
            with self.subTest(pattern=pattern):
                try:
                    result = subprocess.run(
                        [
                            sys.executable,
                            "-B",
                            "-c",
                            probe,
                            str(ROOT / "scripts"),
                            value,
                            pattern,
                        ],
                        text=True,
                        capture_output=True,
                        check=False,
                        timeout=0.75,
                    )
                except subprocess.TimeoutExpired:
                    self.fail("schema pattern validation exceeded safe timeout")
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertEqual(
                    ["$: pattern exceeds safe complexity limit"],
                    json.loads(result.stdout),
                )

        for pattern, value in (
            ("^(a|b)+$", "abba"),
            ("^((ab))+$", "abab"),
            ("^(?:ab?c)+$", "acabcac"),
            ("^(?:ab{2}c)+$", "abbcabbc"),
            ("^(?:ab{1,2}c)+$", "abcabbc"),
            ("^(?:[ab])+$", "abba"),
        ):
            with self.subTest(pattern=pattern, control="safe"):
                self.assertEqual(
                    [],
                    validate_schema_instance(
                        value, {"type": "string", "pattern": pattern}
                    ),
                )

    def test_dependency_free_checker_rejects_adjacent_quantified_atom_redos_within_timeout(self):
        probe = (
            "import json,sys;"
            "sys.path.insert(0,sys.argv[1]);"
            "from validate_json_schema_subset import validate_schema_instance;"
            "value=sys.argv[2]*int(sys.argv[3])+sys.argv[4];"
            "print(json.dumps(validate_schema_instance("
            "value,{'type':'string','pattern':sys.argv[5]})))"
        )
        unsafe_cases = (
            ("^a+a+a+$", "a", 3_000, "!"),
            ("^a+a+$", "a", 50_000, "!"),
            ("^a*a*$", "a", 50_000, "!"),
            ("^[a]+a+$", "a", 50_000, "!"),
            (r"^\d+[0-9]+$", "1", 50_000, "!"),
            (r"^[0\d]+\d+$", "1", 50_000, "!"),
            ("^" + ("a*" * 32) + "b$", "a", 2_000, "!"),
        )
        for pattern, character, count, suffix in unsafe_cases:
            with self.subTest(pattern=pattern):
                try:
                    result = subprocess.run(
                        [
                            sys.executable,
                            "-B",
                            "-c",
                            probe,
                            str(ROOT / "scripts"),
                            character,
                            str(count),
                            suffix,
                            pattern,
                        ],
                        text=True,
                        capture_output=True,
                        check=False,
                        timeout=0.75,
                    )
                except subprocess.TimeoutExpired:
                    self.fail("adjacent quantified atoms exceeded safe timeout")
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertEqual(
                    ["$: pattern exceeds safe complexity limit"],
                    json.loads(result.stdout),
                )

        safe_cases = (
            ("^a+b+$", "a" * 50_000 + "b"),
            ("^a*b*$", "a" * 50_000 + "b"),
            ("^[ab]+c+$", "a" * 50_000 + "c"),
            (r"^\d+[A-Z]+$", "1" * 50_000 + "Z"),
            (r"^\++a+$", "+" * 50_000 + "a"),
            ("^a{1,2}a{3,4}$", "aaaa"),
        )
        for pattern, value in safe_cases:
            with self.subTest(pattern=pattern, control="safe"):
                self.assertEqual(
                    [],
                    validate_schema_instance(
                        value, {"type": "string", "pattern": pattern}
                    ),
                )

    def test_dependency_free_checker_rejects_group_atom_overlap_within_timeout(self):
        probe = (
            "import json,sys;"
            "sys.path.insert(0,sys.argv[1]);"
            "from validate_json_schema_subset import validate_schema_instance;"
            "print(json.dumps(validate_schema_instance("
            "'a'*100000,{'type':'string','pattern':sys.argv[2]})))"
        )
        for pattern in ("^(?:a*)a*c$", "^a*(?:a*)c$"):
            with self.subTest(pattern=pattern):
                try:
                    result = subprocess.run(
                        [
                            sys.executable,
                            "-B",
                            "-c",
                            probe,
                            str(ROOT / "scripts"),
                            pattern,
                        ],
                        text=True,
                        capture_output=True,
                        check=False,
                        timeout=1.0,
                    )
                except subprocess.TimeoutExpired:
                    self.fail("quantified group/atom overlap exceeded safe timeout")
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertEqual(
                    ["$: pattern exceeds safe complexity limit"],
                    json.loads(result.stdout),
                )

        for pattern, value in (
            ("^(?:a*)b*c$", "a" * 100_000 + "c"),
            ("^a*(?:b*)c$", "a" * 100_000 + "c"),
        ):
            with self.subTest(pattern=pattern, control="safe-disjoint"):
                self.assertEqual(
                    [],
                    validate_schema_instance(
                        value, {"type": "string", "pattern": pattern}
                    ),
                )

    def test_dependency_free_checker_totalizes_oversized_quantifier_integers(self):
        digits = "9" * 400
        pattern = "a{" + digits + "}"

        self.assertEqual(
            ["$: pattern exceeds safe complexity limit"],
            validate_schema_instance("a", {"type": "string", "pattern": pattern}),
        )
        for literal_pattern in (r"\{" + digits + r"\}", "[{]" + digits + "[}]"):
            with self.subTest(control=literal_pattern[:3]):
                self.assertEqual(
                    [],
                    validate_schema_instance(
                        "{" + digits + "}",
                        {"type": "string", "pattern": literal_pattern},
                    ),
                )

    def test_dependency_free_checker_rejects_cyclic_json_values_without_recursion_error(self):
        value = []
        value.append(value)

        errors = validate_schema_instance(value, {"const": value})

        self.assertEqual([], errors)

    def test_dependency_free_checker_resolves_root_reference_and_rejects_bad_pointer_escapes(self):
        self.assertEqual(
            ["schema validation exceeds safe evaluation limit"],
            validate_schema_instance({}, {"$ref": "#"}),
        )
        malformed_pointer = {
            "$defs": {"~2escaped": {"const": "accepted-only-if-pointer-is-wrong"}},
            "$ref": "#/$defs/~2escaped",
        }
        self.assertEqual(
            ["schema reference is invalid"],
            validate_schema_instance("accepted-only-if-pointer-is-wrong", malformed_pointer),
        )

    def test_dependency_free_checker_applies_ref_sibling_keywords(self):
        schema = {
            "$defs": {"number": {"type": "integer"}},
            "$ref": "#/$defs/number",
            "minimum": 5,
        }

        self.assertEqual([], validate_schema_instance(5, schema))
        self.assertEqual(
            ["$: number below minimum"],
            validate_schema_instance(3, schema),
        )

    def test_dependency_free_checker_bounds_deep_values(self):
        value: object = "leaf"
        schema: object = {"type": "string"}
        for _ in range(80):
            value = {"nested": value}
            schema = {"type": "object", "properties": {"nested": schema}}

        self.assertEqual(
            ["schema validation exceeds safe depth limit"],
            validate_schema_instance(value, schema),
        )

    def test_dependency_free_checker_bounds_recursive_refs(self):
        schema = {"$defs": {"node": {"$ref": "#/$defs/node"}}, "$ref": "#/$defs/node"}

        self.assertEqual(
            ["schema validation exceeds safe evaluation limit"],
            validate_schema_instance("leaf", schema),
        )

    def test_dependency_free_checker_enforces_numeric_and_array_bounds(self):
        schema = {
            "type": "object",
            "properties": {
                "score": {"type": "number", "minimum": 1, "maximum": 5},
                "fact_ids": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": 2,
                    "uniqueItems": True,
                    "items": {"type": "string"},
                },
            },
            "required": ["score", "fact_ids"],
        }
        valid = {"score": 3.5, "fact_ids": ["F-1", "F-2"]}
        self.assertEqual([], validate_schema_instance(valid, schema))
        for value, expected in (
            ({"score": 0, "fact_ids": ["F-1"]}, "number below minimum"),
            ({"score": 6, "fact_ids": ["F-1"]}, "number above maximum"),
            ({"score": 3, "fact_ids": []}, "too few items"),
            ({"score": 3, "fact_ids": ["F-1", "F-2", "F-3"]}, "too many items"),
            ({"score": 3, "fact_ids": ["F-1", "F-1"]}, "duplicate items"),
        ):
            self.assertTrue(any(expected in error for error in validate_schema_instance(value, schema)), (value, expected))

    def test_schema_diagnostics_redact_sensitive_keys_and_escape_controls(self):
        schema = {"type": "object", "properties": {}, "additionalProperties": False}
        cases = (
            ("person@example.invalid", "<redacted-field>"),
            ("/Users/private-candidate/profile.json", "<redacted-field>"),
            ("ordinary\nINJECTED\x1b[31m", r"ordinary\u000aINJECTED\u001b[31m"),
            ("extra", "extra"),
        )
        for key, expected in cases:
            with self.subTest(key=key):
                errors = validate_schema_instance({key: "x"}, schema)
                self.assertEqual([f"$: unsupported field {expected}"], errors)
                self.assertNotIn("\nINJECTED", "\n".join(errors))

    def test_schema_diagnostics_do_not_echo_task_one_sentinels_in_keys_or_required_paths(self):
        sentinels = (
            ("/etc/passwd", "<redacted-field>"),
            ("/opt/data/profile.json", "<redacted-field>"),
            (r"D:\work\candidate\profile.json", "<redacted-field>"),
            (r"\\server\share\profile.json", "<redacted-field>"),
            (
                "ordinary\x1b[31mINJECTED\nLINE",
                r"ordinary\u001b[31mINJECTED\u000aLINE",
            ),
        )
        closed_schema = {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        }
        for sentinel, expected in sentinels:
            with self.subTest(sentinel=sentinel, location="instance"):
                errors = validate_schema_instance({sentinel: "x"}, closed_schema)
                self.assertEqual([f"$: unsupported field {expected}"], errors)
                self.assertNotIn(sentinel, "\n".join(errors))
                self.assertNotIn("\x1b", "\n".join(errors))

            with self.subTest(sentinel=sentinel, location="required"):
                required_schema = {"type": "object", "required": [sentinel]}
                errors = validate_schema_instance({}, required_schema)
                self.assertEqual([f"$: missing required field {expected}"], errors)
                self.assertNotIn(sentinel, "\n".join(errors))
                self.assertNotIn("\x1b", "\n".join(errors))

        for relative_key in (r"relative\profile.json", "foo/opt/data/profile.json"):
            with self.subTest(relative_key=relative_key):
                self.assertEqual(
                    [f"$: unsupported field {relative_key}"],
                    validate_schema_instance({relative_key: "x"}, closed_schema),
                )

    def test_schema_diagnostics_redact_prefixed_absolute_paths_without_echo(self):
        sentinels = (
            "  /etc/passwd",
            "\t/opt/data/profile.json",
            " \n" + r"D:\work\candidate\profile.json",
            "\u200b" + r"\\server\share\profile.json",
        )
        closed_schema = {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        }
        for sentinel in sentinels:
            with self.subTest(sentinel=sentinel, location="instance"):
                errors = validate_schema_instance({sentinel: "x"}, closed_schema)
                self.assertEqual(["$: unsupported field <redacted-field>"], errors)
                self.assertNotIn(sentinel, "\n".join(errors))

            with self.subTest(sentinel=sentinel, location="required"):
                errors = validate_schema_instance(
                    {}, {"type": "object", "required": [sentinel]}
                )
                self.assertEqual(["$: missing required field <redacted-field>"], errors)
                self.assertNotIn(sentinel, "\n".join(errors))

    def test_dependency_free_checker_enforces_strict_json_types_and_const(self):
        self.assertEqual(
            [], validate_schema_instance(1, {"type": "integer", "const": 1})
        )
        for value, schema in (
            (True, {"type": "integer", "const": 1}),
            (0, {"type": "boolean", "const": False}),
            (17, {"type": ["string", "null"]}),
        ):
            with self.subTest(value=value, schema=schema):
                self.assertTrue(validate_schema_instance(value, schema))

        for value in (None, "x"):
            with self.subTest(value=value):
                self.assertEqual(
                    [], validate_schema_instance(value, {"type": ["string", "null"]})
                )

    def test_dependency_free_checker_applies_pattern_only_to_strings(self):
        nullable_pattern = {"type": ["string", "null"], "pattern": "^CAP-[0-9]{3}$"}
        self.assertEqual([], validate_schema_instance(None, nullable_pattern))
        self.assertEqual([], validate_schema_instance("CAP-001", nullable_pattern))
        self.assertTrue(
            any(
                "pattern mismatch" in error
                for error in validate_schema_instance("E-001", nullable_pattern)
            )
        )

    def test_dependency_free_checker_uses_json_schema_pattern_search_semantics(self):
        self.assertEqual(
            [],
            validate_schema_instance(
                "prefix-abc-suffix", {"type": "string", "pattern": "abc"}
            ),
        )
        self.assertTrue(
            any(
                "pattern mismatch" in error
                for error in validate_schema_instance(
                    "prefix-CAP-001-suffix",
                    {"type": "string", "pattern": "^CAP-[0-9]{3}$"},
                )
            )
        )
        string_only_pattern = {"type": "string", "pattern": "^CAP-[0-9]{3}$"}
        self.assertTrue(
            any(
                "type mismatch" in error
                for error in validate_schema_instance(None, string_only_pattern)
            )
        )

    def test_dependency_free_checker_rejects_nested_quantifier_patterns(self):
        errors = validate_schema_instance(
            "a" * 25 + "!", {"type": "string", "pattern": "(a+)+$"}
        )
        self.assertEqual(["$: pattern exceeds safe complexity limit"], errors)
        self.assertEqual(
            [],
            validate_schema_instance(
                "prefix-abc-suffix", {"type": "string", "pattern": "(abc)+"}
            ),
        )

        schema = self._schema("executive-career-dossier-v1.schema.json")
        dossier = json.loads(
            (
                ROOT.parent.parent
                / "tests/evals/with-skill/fixtures/executive-career-dossier/scenario-a-es.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual([], validate_schema_instance(dossier, schema))

    def test_dependency_free_checker_enforces_contains_and_if_then_else(self):
        schema = {
            "type": "object",
            "properties": {
                "kind": {"type": "string"},
                "tags": {
                    "type": "array",
                    "contains": {"const": "priority"},
                },
                "note": {"type": "string"},
            },
            "required": ["kind", "tags", "note"],
            "if": {"properties": {"kind": {"const": "urgent"}}},
            "then": {"properties": {"note": {"const": "escalate"}}},
            "else": {"properties": {"note": {"const": "queue"}}},
        }
        self.assertEqual([], validate_schema_instance({"kind": "urgent", "tags": ["normal", "priority"], "note": "escalate"}, schema))
        self.assertEqual([], validate_schema_instance({"kind": "normal", "tags": ["priority"], "note": "queue"}, schema))
        for value, expected in (
            ({"kind": "urgent", "tags": ["normal"], "note": "escalate"}, "contains mismatch"),
            ({"kind": "urgent", "tags": ["priority"], "note": "queue"}, "const mismatch"),
            ({"kind": "normal", "tags": ["priority"], "note": "escalate"}, "const mismatch"),
        ):
            self.assertTrue(any(expected in error for error in validate_schema_instance(value, schema)), (value, expected))


if __name__ == "__main__":
    unittest.main()
