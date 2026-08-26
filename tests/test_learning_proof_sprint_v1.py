"""RED/GREEN contract tests for the private learning-proof sprint v1."""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "professional-growth-coach"
SCRIPTS = PLUGIN / "scripts"
SCHEMA = PLUGIN / "schemas" / "learning-proof-sprint-v1.schema.json"


def load_script(name: str):
    path = SCRIPTS / name
    specification = importlib.util.spec_from_file_location(
        f"learning_proof_sprint_test_{path.stem}", path
    )
    if specification is None or specification.loader is None:
        raise AssertionError("learning proof sprint module is unavailable")
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


BUILDER = load_script("build_learning_proof_sprint_v1.py")
VALIDATOR = load_script("validate_learning_proof_sprint_v1.py")
WRITER = load_script("write_learning_proof_sprint_v1.py")


_DECISION_PATH = ROOT / "tests" / "evals" / "with-skill" / "fixtures" / "career-learning-decision-v3" / "proof-es" / "learning.json"
_FACT_PATH = ROOT / "tests" / "evals" / "with-skill" / "fixtures" / "private-vacancy-application-packet-v1" / "ready-es" / "candidate-fact-matrix.json"
_FACT_EN_PATH = ROOT / "tests" / "evals" / "with-skill" / "fixtures" / "private-vacancy-application-packet-v1" / "ready-en" / "candidate-fact-matrix.json"


def source_group(*, locale: str = "es") -> dict[str, object]:
    decision = json.loads(_DECISION_PATH.read_text(encoding="utf-8"))
    facts = json.loads((_FACT_PATH if locale == "es" else _FACT_EN_PATH).read_text(encoding="utf-8"))
    decision["locale"] = locale
    return {"decision": decision, "candidate_fact_matrix": facts}


class LearningProofSprintV1Tests(unittest.TestCase):
    def assert_rejected(self, value: object) -> None:
        with self.assertRaises(ValueError) as caught:
            BUILDER.build_learning_proof_sprint_v1(value)
        self.assertEqual("learning proof sprint is invalid", str(caught.exception))

    def test_builder_projects_one_plan_five_days_three_reuse_rows_and_derived_ids(self) -> None:
        artifact = BUILDER.build_learning_proof_sprint_v1(source_group())
        self.assertEqual(
            {
                "schema_version",
                "locale",
                "case_scope",
                "plan",
                "days",
                "reuse_map",
                "source_snapshot",
                "privacy_boundary",
                "outcome_boundary",
                "draft_only",
                "no_external_action",
            },
            set(artifact),
        )
        self.assertEqual("learning-proof-sprint-v1", artifact["schema_version"])
        self.assertEqual("single_candidate", artifact["case_scope"])
        self.assertEqual("LPS-PLAN-001", artifact["plan"]["plan_id"])
        self.assertEqual("learning_proof_sprint_plan", artifact["plan"]["kind"])
        self.assertEqual(
            ["LPS-DAY-001", "LPS-DAY-002", "LPS-DAY-003", "LPS-DAY-004", "LPS-DAY-005"],
            [row["day_id"] for row in artifact["days"]],
        )
        self.assertEqual(
            ["LPS-REUSE-001", "LPS-REUSE-002", "LPS-REUSE-003"],
            [row["reuse_id"] for row in artifact["reuse_map"]],
        )
        self.assertEqual("candidate-owned-private-draft", artifact["privacy_boundary"])
        self.assertEqual("not_an_interview_offer_salary_or_roi_prediction", artifact["outcome_boundary"])
        self.assertTrue(artifact["draft_only"])
        self.assertTrue(artifact["no_external_action"])

    def test_builder_rejects_missing_or_extra_required_sources_and_wrong_cardinality(self) -> None:
        for field in ("decision", "candidate_fact_matrix"):
            value = source_group()
            del value[field]
            with self.subTest(field=field):
                self.assert_rejected(value)
        extra = source_group()
        extra["review_sensitive"] = "not allowed"
        self.assert_rejected(extra)
        extra_nested = source_group()
        extra_nested["decision"]["review_sensitive"] = "not allowed"
        self.assert_rejected(extra_nested)

    def test_builder_binds_snapshot_and_validator_rejects_mutation(self) -> None:
        source = source_group()
        artifact = BUILDER.build_learning_proof_sprint_v1(source)
        validated = VALIDATOR.validate_learning_proof_sprint_v1(artifact, source)
        self.assertEqual(artifact, validated.artifact)
        mutated_source = copy.deepcopy(source)
        mutated_source["decision"]["decisions"][0]["option_name"] = "changed after capture"
        with self.assertRaisesRegex(ValueError, "learning proof sprint does not match validated sources"):
            VALIDATOR.validate_learning_proof_sprint_v1(artifact, mutated_source)
        mutated_artifact = copy.deepcopy(artifact)
        mutated_artifact["days"][0]["day_id"] = "LPS-DAY-999"
        with self.assertRaisesRegex(ValueError, "learning proof sprint does not match validated sources"):
            VALIDATOR.validate_learning_proof_sprint_v1(mutated_artifact, source)

    def test_builder_localizes_es_and_en_without_allowing_locale_drift(self) -> None:
        self.assertEqual("es", BUILDER.build_learning_proof_sprint_v1(source_group(locale="es"))["locale"])
        self.assertEqual("en", BUILDER.build_learning_proof_sprint_v1(source_group(locale="en"))["locale"])
        invalid = source_group(locale="fr")
        self.assert_rejected(invalid)
        mismatched = source_group(locale="es")
        mismatched["candidate_fact_matrix"]["locale"] = "en"
        self.assert_rejected(mismatched)

    def test_builder_rejects_privacy_and_external_action_leaks(self) -> None:
        mutations = (
            lambda value: value["decision"]["decisions"][0].update({"option_name": "email candidate@example.com now"}),
            lambda value: value["decision"]["decisions"][0].update({"option_name": "https://private.example/repo"}),
            lambda value: value["candidate_fact_matrix"]["facts"][0].update({"confidentiality": "forbidden"}),
            lambda value: value["decision"]["decisions"][0].update({"decision_basis": "publish now and get an interview"}),
            lambda value: value["decision"]["decisions"][0].update({"next_action_gate": "send the application now"}),
            lambda value: value["decision"]["decisions"][0]["signal_routes"][0].update({"term_label": "Ana García"}),
            lambda value: value["decision"]["decisions"][0]["signal_routes"][0].update({"term_label": "snap-password:secret"}),
            lambda value: value["decision"]["decisions"][0]["signal_routes"][0].update({"term_label": "aumentará tu salario"}),
            lambda value: value["decision"]["decisions"][0].update({"decision_basis": "publicar proyecto"}),
            lambda value: value["decision"]["decisions"][0].update({"decision_basis": "aplicar a la vacante"}),
            lambda value: value["decision"]["decisions"][0].update({"decision_basis": "subir proyecto"}),
            lambda value: value["decision"]["decisions"][0].update({"decision_basis": "inscribirse al curso"}),
            lambda value: value["decision"]["decisions"][0].update({"decision_basis": "agendar entrevista"}),
            lambda value: value["decision"]["decisions"][0].update({"decision_basis": "mejora tu salario"}),
            lambda value: value["decision"]["decisions"][0].update({"decision_basis": "publish project"}),
            lambda value: value["decision"]["decisions"][0].update({"decision_basis": "increase your salary"}),
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                value = source_group()
                mutation(value)
                self.assert_rejected(value)

    def test_builder_rejects_contract_constant_or_boolean_drift(self) -> None:
        for field, bad in (
            ("decision_code", "run_validation_lab"),
            ("gap_type", "knowledge"),
            ("outcome_boundary", "interview likely"),
            ("draft_only", False),
            ("no_external_action", False),
        ):
            value = source_group()
            value["decision"]["decisions"][0][field] = bad
            with self.subTest(field=field):
                self.assert_rejected(value)
        value = source_group()
        value["decision"]["decisions"][0]["source_signals"] = ["unknown_signal"]
        self.assert_rejected(value)

    def test_builder_rejects_crossed_signal_route_and_duplicate_or_excess_facts(self) -> None:
        crossed = source_group()
        crossed["decision"]["decisions"][0]["signal_routes"][0]["signal"] = "kubernetes"
        self.assert_rejected(crossed)
        duplicate = source_group()
        duplicate["candidate_fact_matrix"]["facts"].append(copy.deepcopy(duplicate["candidate_fact_matrix"]["facts"][0]))
        self.assert_rejected(duplicate)
        excessive = source_group()
        for number in range(2, 22):
            row = copy.deepcopy(excessive["candidate_fact_matrix"]["facts"][0])
            row["fact_id"] = f"F-{number:03d}"
            excessive["candidate_fact_matrix"]["facts"].append(row)
        self.assert_rejected(excessive)

    def test_builder_does_not_reread_mutable_input_after_capture(self) -> None:
        class OneShot(dict):
            reads = 0

            def items(self):
                self.reads += 1
                if self.reads > 1:
                    raise RuntimeError("review-sensitive reread")
                return super().items()

        value = OneShot(source_group())
        artifact = BUILDER.build_learning_proof_sprint_v1(value)
        self.assertEqual("learning-proof-sprint-v1", artifact["schema_version"])

    def test_schema_is_closed_and_writer_requires_opaque_proof(self) -> None:
        self.assertTrue(SCHEMA.is_file())
        source = source_group()
        artifact = BUILDER.build_learning_proof_sprint_v1(source)
        validated = VALIDATOR.validate_learning_proof_sprint_v1(artifact, source)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "learning-proof-sprint.json"
            receipt = WRITER.write_learning_proof_sprint_v1(validated, output, force=True)
            self.assertEqual(0o600, output.stat().st_mode & 0o777)
            self.assertEqual("learning-proof-sprint-v1", receipt.schema_version)
            self.assertTrue(receipt.private_draft)
            self.assertFalse(receipt.external_action_authorized)
            self.assertEqual(artifact, json.loads(output.read_text(encoding="utf-8")))
            with self.assertRaises(WRITER.LearningProofSprintWriteError):
                WRITER.write_learning_proof_sprint_v1(artifact, output, force=True)


if __name__ == "__main__":
    unittest.main()
