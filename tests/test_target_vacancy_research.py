"""Contract tests for synthetic, identity-free vacancy-research fixtures.

The fixture employers and RFC documentation URLs in this module are test data
only. They must never be treated as production market evidence.
"""
from __future__ import annotations

import contextlib
import copy
import importlib.util
import io
import json
import os
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "plugins/professional-growth-coach/scripts"
FIXTURES = ROOT / "tests/evals/with-skill/fixtures/target-vacancy-research"
STATE_COUNTS = {
    "complete": {5},
    "limited_market_evidence": {1, 2, 3, 4},
    "market_evidence_unavailable": {0},
}


def load_validator() -> object:
    path = SCRIPTS / "validate_target_vacancy_research.py"
    specification = importlib.util.spec_from_file_location(
        "validate_target_vacancy_research", path
    )
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def load_fixture(name: str) -> dict[str, object]:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class TargetVacancyResearchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.validator = load_validator()

    def test_sample_states_match_closed_count_contract(self) -> None:
        cases = (
            ("complete-five-es.json", "complete", 5),
            ("limited-four-en.json", "limited_market_evidence", 4),
            ("unavailable-es.json", "market_evidence_unavailable", 0),
        )
        for fixture_name, state, count in cases:
            with self.subTest(fixture=fixture_name):
                value = load_fixture(fixture_name)
                self.assertEqual([], self.validator.validate_research(value))
                self.assertEqual(value["state"], state)
                self.assertIn(count, STATE_COUNTS[state])
                vacancies = value["vacancies"]
                self.assertEqual(len(vacancies), count)
                self.assertEqual(len({row["vacancy_id"] for row in vacancies}), count)
                self.assertEqual(
                    len({row["duplicate_fingerprint"] for row in vacancies}), count
                )
                self.assertTrue(
                    all(row["access_date"] == value["as_of_date"] for row in vacancies)
                )

    def complete(self) -> dict[str, object]:
        return load_fixture("complete-five-es.json")

    def assert_invalid(self, value: object, diagnostic: str) -> list[str]:
        errors = self.validator.validate_research(value)
        self.assertIn(diagnostic, errors)
        return errors

    def test_state_counts_reject_extra_and_insufficient_postings(self) -> None:
        cases = []
        six = self.complete()
        extra = copy.deepcopy(six["vacancies"][4])
        extra.update({"vacancy_id": "V-006", "duplicate_fingerprint": "fixture-fingerprint-006", "employer_id": "EMP-006"})
        six["vacancies"].append(extra)
        cases.append(six)
        limited_five = self.complete()
        limited_five["state"] = "limited_market_evidence"
        limited_five["search_limit"]["limit_reason"] = "bounded_search_exhausted"
        cases.append(limited_five)
        complete_four = self.complete()
        complete_four["vacancies"].pop()
        cases.append(complete_four)
        for value in cases:
            with self.subTest(state=value["state"], count=len(value["vacancies"])):
                self.assert_invalid(value, "state does not match vacancy count")

    def test_canonical_vacancy_and_employer_identifier_sequences_are_required(self) -> None:
        invalid_vacancy = self.complete()
        invalid_vacancy["vacancies"][4]["vacancy_id"] = "V-999"
        invalid_vacancy["vacancies"][4]["requirements"][0]["requirement_id"] = "V-999-R-01"
        self.assert_invalid(invalid_vacancy, "vacancy IDs must use the canonical sequence")
        invalid_employer = self.complete()
        invalid_employer["employers"][4]["employer_id"] = "EMP-999"
        invalid_employer["vacancies"][4]["employer_id"] = "EMP-999"
        self.assert_invalid(invalid_employer, "employer IDs must use the canonical sequence")

    def test_rejects_duplicate_vacancy_fingerprint_requirement_and_signal(self) -> None:
        mutations = []
        duplicate_vacancy = self.complete()
        duplicate_vacancy["vacancies"][1]["vacancy_id"] = "V-001"
        mutations.append((duplicate_vacancy, "vacancies have duplicate vacancy IDs"))
        duplicate_fingerprint = self.complete()
        duplicate_fingerprint["vacancies"][1]["duplicate_fingerprint"] = "fixture-fingerprint-001"
        mutations.append((duplicate_fingerprint, "vacancies have duplicate fingerprints"))
        duplicate_requirement = self.complete()
        duplicate_requirement["vacancies"][1]["requirements"][0]["requirement_id"] = "V-001-R-01"
        mutations.append((duplicate_requirement, "requirements have duplicate IDs"))
        duplicate_signal = self.complete()
        duplicate_signal["vacancies"][0]["requirements"].append(copy.deepcopy(duplicate_signal["vacancies"][0]["requirements"][0]))
        duplicate_signal["vacancies"][0]["requirements"][1]["requirement_id"] = "V-001-R-02"
        mutations.append((duplicate_signal, "vacancy requirements have duplicate signals"))
        for value, diagnostic in mutations:
            with self.subTest(diagnostic=diagnostic):
                self.assert_invalid(value, diagnostic)

    def test_repeated_employers_require_exhaustion_and_distinct_fingerprints(self) -> None:
        repeated = self.complete()
        repeated["vacancies"][1]["employer_id"] = "EMP-001"
        self.assert_invalid(repeated, "repeated employers require exhausted search")
        repeated["search_limit"]["distinct_employer_search_exhausted"] = True
        self.assertEqual([], self.validator.validate_research(repeated))
        repeated["vacancies"][1]["duplicate_fingerprint"] = "fixture-fingerprint-001"
        self.assert_invalid(repeated, "vacancies have duplicate fingerprints")

    def test_rejects_state_dates_and_invalid_current_freshness(self) -> None:
        cases = []
        non_active = self.complete()
        non_active["vacancies"][0]["source_state"] = "closed"
        cases.append((non_active, "included vacancy source must be active"))
        mismatched_access = self.complete()
        mismatched_access["vacancies"][0]["access_date"] = "2026-08-12"
        cases.append((mismatched_access, "included vacancy access date must match as_of_date"))
        future_publication = self.complete()
        future_publication["vacancies"][0]["publication_date"] = "2026-08-14"
        cases.append((future_publication, "publication date cannot be after as_of_date"))
        current_without_date = self.complete()
        current_without_date["vacancies"][0]["publication_date"] = None
        cases.append((current_without_date, "current freshness requires a publication date"))
        for value, diagnostic in cases:
            with self.subTest(diagnostic=diagnostic):
                self.assert_invalid(value, diagnostic)

    def test_employer_qualification_evidence_must_be_current(self) -> None:
        headcount_boundary = self.complete()
        headcount_boundary["employers"][0]["source_date"] = "2025-02-13"
        self.assertEqual([], self.validator.validate_research(headcount_boundary))

        stale_headcount = self.complete()
        stale_headcount["employers"][0]["source_date"] = "2025-02-12"
        self.assert_invalid(stale_headcount, "employer qualification evidence is stale")

        current_membership = load_fixture("limited-four-en.json")
        self.assertEqual([], self.validator.validate_research(current_membership))

        stale_membership = load_fixture("limited-four-en.json")
        stale_membership["employers"][0]["source_date"] = "2026-08-12"
        self.assert_invalid(stale_membership, "employer qualification evidence is stale")

    def test_source_kind_url_rules_reject_unsafe_or_mismatched_sources(self) -> None:
        cases = []
        backup_host = self.complete()
        backup_host["vacancies"][0].update({"source_kind": "linkedin_jobs_backup", "source_url": "https://example.com/jobs/synthetic"})
        cases.append(backup_host)
        backup_path = self.complete()
        backup_path["vacancies"][0].update({"source_kind": "linkedin_jobs_backup", "source_url": "https://linkedin.com/company/synthetic"})
        cases.append(backup_path)
        for source_url in (
            "https://linkedin.com/jobs/synthetic",
            "https://localhost/careers/synthetic",
            "https://127.0.0.1/careers/synthetic",
            "https://user:pass@example.com/careers/synthetic",
            "https://example.com:bad/careers/synthetic",
            "http://example.com/careers/synthetic",
            "file:///careers/synthetic",
        ):
            value = self.complete()
            value["vacancies"][0]["source_url"] = source_url
            cases.append(value)
        for value in cases:
            with self.subTest(source_kind=value["vacancies"][0]["source_kind"]):
                self.assert_invalid(value, "source URL violates source-kind policy")

    def test_official_and_ats_sources_reject_linkedin_subdomains(self) -> None:
        for source_url in (
            "https://www.linkedin.com/jobs/synthetic",
            "https://jobs.linkedin.com/jobs/synthetic",
        ):
            with self.subTest(source_url=source_url):
                value = self.complete()
                value["vacancies"][0]["source_url"] = source_url
                self.assert_invalid(value, "source URL violates source-kind policy")

    def test_distinct_employer_rule_uses_normalized_employer_identity(self) -> None:
        value = self.complete()
        value["employers"][1].update({
            "display_name": " fixture   employer a ",
            "official_source_url": "https://example.com/careers/a/",
        })
        self.assert_invalid(value, "employers have duplicate normalized identities")
        self.assert_invalid(value, "repeated employers require exhausted search")
        source_alias = self.complete()
        source_alias["employers"][1]["official_source_url"] = "https://www.rfc-editor.org/rfc/rfc2606"
        self.assert_invalid(source_alias, "repeated employers require exhausted search")

    def test_target_and_repeated_employer_limit_flags_are_enforced(self) -> None:
        incomplete_target = self.complete()
        incomplete_target["vacancies"].pop()
        incomplete_target["search_limit"]["limit_reason"] = "target_reached"
        self.assert_invalid(incomplete_target, "target_reached requires five vacancies")
        repeated_without_flag = self.complete()
        repeated_without_flag["vacancies"][1]["employer_id"] = "EMP-001"
        repeated_without_flag["search_limit"]["distinct_employer_search_exhausted"] = False
        self.assert_invalid(repeated_without_flag, "repeated employers require exhausted search")

    def test_eligibility_is_closed_and_unknown_cannot_infer_pass(self) -> None:
        invalid_state = self.complete()
        invalid_state["vacancies"][0]["eligibility_gates"][0]["state"] = "eligible"
        self.assert_invalid(invalid_state, "eligibility gate state is invalid")
        inferred_unknown = self.complete()
        inferred_unknown["vacancies"][0]["eligibility_gates"][0].update({"state": "unknown", "observed_condition": "Inferred pass for Mexico."})
        self.assert_invalid(inferred_unknown, "unknown eligibility gate cannot infer a pass conclusion")

    def test_unknown_eligibility_rejects_equivalent_english_and_spanish_conclusions(self) -> None:
        for observation in (
            "Pass is inferred from the remote listing.",
            "The candidate is eligible to work in Mexico.",
            "Se considera elegible para trabajar en México.",
            "Aprobado por inferencia de la vacante.",
        ):
            with self.subTest(observation=observation):
                value = self.complete()
                value["vacancies"][0]["eligibility_gates"][0].update({
                    "state": "unknown", "observed_condition": observation,
                })
                self.assert_invalid(value, "unknown eligibility gate cannot infer a pass conclusion")

    def test_unknown_eligibility_rejects_confirmed_or_blocked_authorization_conclusions(self) -> None:
        for observation in (
            "Work authorization was confirmed by the listing.",
            "The listing confirmed the candidate is eligible.",
            "La vacante confirmó la autorización de trabajo.",
            "La autorización de trabajo fue confirmada por la vacante.",
            "La vacante bloqueó la elegibilidad laboral.",
            "La elegibilidad quedó bloqueada por la vacante.",
        ):
            with self.subTest(observation=observation):
                value = self.complete()
                value["vacancies"][0]["eligibility_gates"][0].update({
                    "state": "unknown", "observed_condition": observation,
                })
                self.assert_invalid(
                    value, "unknown eligibility gate cannot contain an eligibility conclusion"
                )

    def test_unknown_work_authorization_rejects_present_tense_conclusions_without_echo(self) -> None:
        for observation in (
            "La vacante confirma la autorización de trabajo.",
            "La vacante bloquea la autorización de trabajo.",
            "The listing confirms work authorization.",
            "The listing blocks work authorization.",
        ):
            with self.subTest(observation=observation):
                value = self.complete()
                value["vacancies"][0]["eligibility_gates"][0].update({
                    "gate": "work_authorization", "state": "unknown",
                    "observed_condition": observation,
                })
                errors = self.assert_invalid(
                    value, "unknown eligibility gate cannot contain an eligibility conclusion"
                )
                self.assertNotIn(observation, "\n".join(errors))

    def test_unknown_work_authorization_clause_state_matrix(self) -> None:
        conclusions = (
            "The listing confirms work authorization.",
            "The listing verifies work authorization.",
            "The listing authorizes work authorization.",
            "The listing permits work authorization.",
            "The listing blocks work authorization.",
            "The listing denies work authorization.",
            "The listing restricts work authorization.",
            "The listing prohibits work authorization.",
            "La vacante confirma la autorización de trabajo.",
            "La vacante verifica la autorización de trabajo.",
            "La vacante autoriza la autorización de trabajo.",
            "La vacante permite la autorización de trabajo.",
            "La vacante bloquea la autorización de trabajo.",
            "La vacante deniega la autorización de trabajo.",
            "La vacante restringe la autorización de trabajo.",
            "La vacante prohíbe la autorización de trabajo.",
        )
        neutral_requirements = (
            "The listing confirms that work authorization is required.",
            "The listing verifies that work authorization is required.",
            "La vacante confirma que se requiere autorización de trabajo.",
            "La vacante verifica que la autorización de trabajo es requerida.",
        )
        for observation in conclusions:
            with self.subTest(classification="conclusion", observation=observation):
                value = self.complete()
                value["vacancies"][0]["eligibility_gates"][0].update({
                    "gate": "work_authorization", "state": "unknown",
                    "observed_condition": observation,
                })
                errors = self.assert_invalid(
                    value, "unknown eligibility gate cannot contain an eligibility conclusion"
                )
                self.assertNotIn(observation, "\n".join(errors))
        for observation in neutral_requirements:
            with self.subTest(classification="requirement", observation=observation):
                value = self.complete()
                value["vacancies"][0]["eligibility_gates"][0].update({
                    "gate": "work_authorization", "state": "unknown",
                    "observed_condition": observation,
                })
                self.assertEqual([], self.validator.validate_research(value))

    def test_unknown_work_authorization_cli_diagnostic_is_fixed_and_does_not_echo(self) -> None:
        observation = "The listing prohibits work authorization."
        value = self.complete()
        value["vacancies"][0]["eligibility_gates"][0].update({
            "gate": "work_authorization", "state": "unknown",
            "observed_condition": observation,
        })
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "research.json"
            path.write_text(json.dumps(value), encoding="utf-8")
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                self.assertEqual(2, self.validator._cli([str(path)]))
            rendered = stderr.getvalue()
            self.assertIn(
                "unknown eligibility gate cannot contain an eligibility conclusion",
                rendered,
            )
            self.assertNotIn(observation, rendered)
            self.assertNotIn("Traceback", rendered)
            self.assertLessEqual(len(rendered.encode("utf-8")), 16 * 1024)

    def test_unknown_eligibility_allows_only_factual_requirement_descriptions(self) -> None:
        for observation in (
            "The role requires work authorization.",
            "La vacante requiere autorización de trabajo.",
        ):
            with self.subTest(observation=observation):
                value = self.complete()
                value["vacancies"][0]["eligibility_gates"][0].update({
                    "gate": "work_authorization", "state": "unknown",
                    "observed_condition": observation,
                })
                self.assertEqual([], self.validator.validate_research(value))

    def test_privacy_controls_and_closed_fields_do_not_echo_untrusted_values(self) -> None:
        cases = []
        raw_html = self.complete()
        raw_html["vacancies"][0]["title"] = "<script>unsafe</script>"
        cases.append(raw_html)
        candidate_identity = self.complete()
        candidate_identity["vacancies"][0]["eligibility_gates"][0]["observed_condition"] = "Candidate email person@example.com."
        cases.append(candidate_identity)
        controls = self.complete()
        controls["vacancies"][0]["title"] = "Synthetic\u0000 title"
        cases.append(controls)
        extra = self.complete()
        extra["untrusted_secret_key"] = "https://untrusted.invalid/private"
        cases.append(extra)
        for value in cases:
            with self.subTest(value=value):
                errors = self.assert_invalid(value, "research contains forbidden private or raw content") if value is not extra else self.assert_invalid(value, "research has unsupported fields")
                rendered = "\n".join(errors)
                self.assertLessEqual(len(rendered.encode("utf-8")), 16 * 1024)
                self.assertNotIn("person@example.com", rendered)
                self.assertNotIn("untrusted.invalid", rendered)
                self.assertNotIn("Traceback", rendered)

    def test_candidate_specific_name_is_rejected_without_echo(self) -> None:
        for field in ("observed_condition", "source_paraphrase"):
            with self.subTest(field=field):
                value = self.complete()
                target = value["vacancies"][0]["eligibility_gates"][0] if field == "observed_condition" else value["vacancies"][0]["requirements"][0]
                target[field] = "Jane Doe is located in Mexico."
                errors = self.assert_invalid(value, "research contains forbidden private or raw content")
                self.assertNotIn("Jane Doe", "\n".join(errors))

    def test_example_fixture_urls_are_rejected_outside_the_synthetic_fixture_boundary(self) -> None:
        value = self.complete()
        value["vacancies"][0]["source_url"] = "https://example.com/careers/a"
        self.assert_invalid(value, "source URL violates source-kind policy")

    def test_fixture_employer_labels_do_not_bypass_example_com_source_validation(self) -> None:
        value = self.complete()
        value["vacancies"][0]["source_url"] = "https://example.com/careers/not-the-fixture"
        self.assert_invalid(value, "source URL violates source-kind policy")

    def test_validation_is_total_for_malformed_and_recursive_values(self) -> None:
        malformed = self.complete()
        malformed["search_scope"]["target_role_families"] = [{}]
        self.assertTrue(self.validator.validate_research(malformed))
        deeply_nested = self.complete()
        nested: object = []
        for _ in range(1_100):
            nested = [nested]
        deeply_nested["vacancies"][0]["eligibility_gates"] = nested
        self.assertTrue(self.validator.validate_research(deeply_nested))
        recursive = self.complete()
        recursive["self"] = recursive
        self.assertTrue(self.validator.validate_research(recursive))
        with tempfile.TemporaryDirectory() as directory:
            typed_path = Path(directory) / "typed.json"
            typed_value = self.complete()
            typed_value["search_scope"]["target_role_families"] = [{}]
            typed_path.write_text(json.dumps(typed_value), encoding="utf-8")
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                self.assertEqual(2, self.validator._cli([str(typed_path)]))
            self.assertNotIn("Traceback", stderr.getvalue())

    def test_loader_cli_snapshot_and_schema_contract(self) -> None:
        value = self.complete()
        digest = self.validator.canonical_research_snapshot(value)
        self.assertEqual(
            "85efa33d3d58256da22fe860d35c40933d02109873483096a7bbf6f4aa405729",
            digest,
        )
        self.assertEqual(
            f"snap-market-sha256-{digest}", self.validator.snapshot_for_market_dossier(value)
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "research.json"
            path.write_text(json.dumps(value), encoding="utf-8")
            self.assertEqual(value, self.validator.load_research(path))
            self.assertEqual(0, self.validator._cli([str(path)]))

    def test_loader_and_cli_reject_untrusted_inputs_without_tracebacks(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cases = {
                "duplicate.json": '{"x": 1, "x": 2}',
                "malformed.json": "{not json",
                "deep.json": "[" * 14 + "]" * 14,
                "large.json": "{" + '\"x\":\"' + ("x" * (256 * 1024)) + '\"}',
            }
            for name, contents in cases.items():
                with self.subTest(name=name):
                    path = root / name
                    path.write_text(contents, encoding="utf-8")
                    with self.assertRaises(self.validator.ResearchLoadError):
                        self.validator.load_research(path)
                    stderr = io.StringIO()
                    with contextlib.redirect_stderr(stderr):
                        self.assertEqual(2, self.validator._cli([str(path)]))
                    self.assertNotIn("Traceback", stderr.getvalue())
            target = root / "target.json"
            target.write_text(json.dumps(self.complete()), encoding="utf-8")
            link = root / "link.json"
            os.symlink(target, link)
            with self.assertRaises(self.validator.ResearchLoadError):
                self.validator.load_research(link)
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                self.assertEqual(2, self.validator._cli([str(link)]))
            self.assertNotIn("Traceback", stderr.getvalue())
