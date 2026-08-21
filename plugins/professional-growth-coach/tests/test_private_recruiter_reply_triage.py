import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
REPOSITORY_CONTEXT = (
    (ROOT.parent.parent / "tests" / "evals" / "with-skill" / "fixtures").is_dir()
    and (ROOT.parent.parent / "scripts" / "check_repository_privacy.py").is_file()
)
FIXTURE = (
    ROOT.parent.parent
    / "tests"
    / "evals"
    / "with-skill"
    / "fixtures"
    / "private-recruiter-reply-triage"
    / "clarify-en.json"
)
sys.path.insert(0, str(SCRIPTS))


def _load_script(name: str):
    path = SCRIPTS / f"{name}.py"
    specification = importlib.util.spec_from_file_location(name, path)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


validator = _load_script("validate_private_recruiter_reply_triage")
renderer = _load_script("render_private_recruiter_reply_triage")


class PrivateRecruiterReplyTriageIdentityTests(unittest.TestCase):
    def setUp(self):
        if not REPOSITORY_CONTEXT and self._testMethodName != "test_invalid_utf8_input_is_reported_without_traceback":
            self.skipTest("repository conformance requires repository context")

    def test_invalid_utf8_input_is_reported_without_traceback(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.json"
            path.write_bytes(b"\xff")

            result = subprocess.run(
                [sys.executable, "-B", str(SCRIPTS / "validate_private_recruiter_reply_triage.py"), str(path)],
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.returncode, 3)
        self.assertEqual(result.stderr, "triage input is not valid JSON\n")
        self.assertNotIn("Traceback", result.stderr)

    def test_direct_validator_rejects_deep_and_cyclic_mappings(self):
        baseline = json.loads(FIXTURE.read_text(encoding="utf-8"))
        deep = {}
        cursor = deep
        for _ in range(40):
            nested = {}
            cursor["nested"] = nested
            cursor = nested
        deep_triage = copy.deepcopy(baseline)
        deep_triage["unsupported"] = deep
        self.assertIn("nesting exceeds safe limit", "\n".join(validator.validate_triage(deep_triage)))

        cyclic_triage = copy.deepcopy(baseline)
        cyclic = {}
        cyclic["self"] = cyclic
        cyclic_triage["unsupported"] = cyclic
        self.assertIn("nesting exceeds safe limit", "\n".join(validator.validate_triage(cyclic_triage)))

    def test_cli_caps_many_unknown_field_diagnostics(self):
        triage = json.loads(FIXTURE.read_text(encoding="utf-8"))
        triage.update({f"unknown_field_{index:04d}_long": True for index in range(1200)})
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "unknown-fields.json"
            path.write_text(json.dumps(triage), encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(SCRIPTS / "validate_private_recruiter_reply_triage.py"),
                    str(path),
                ],
                capture_output=True,
                text=True,
            )
        self.assertEqual(result.returncode, 2)
        self.assertLessEqual(len(result.stderr.encode("utf-8")), 16_384)
        self.assertIn("validation diagnostics truncated; additional errors omitted\n", result.stderr)
        self.assertNotIn("unknown_field_1199_long", result.stderr)

    def test_cli_preserves_short_diagnostic_output(self):
        triage = json.loads(FIXTURE.read_text(encoding="utf-8"))
        triage["extra"] = True
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "extra.json"
            path.write_text(json.dumps(triage), encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(SCRIPTS / "validate_private_recruiter_reply_triage.py"),
                    str(path),
                ],
                capture_output=True,
                text=True,
            )
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stderr, "session has unsupported fields: extra\n")

    def test_unknown_fact_reference_rejects_without_echoing_private_value(self):
        triage = json.loads(FIXTURE.read_text(encoding="utf-8"))
        sentinel = "person@example.com"
        triage["question"]["fact_ids"] = [sentinel]

        errors = validator.validate_triage(triage)

        self.assertIn(
            "question.fact_ids references unknown identifier",
            errors,
        )
        self.assertNotIn(sentinel, "\n".join(errors))
        with self.assertRaises(renderer.TriageValidationError) as raised:
            renderer.render_triage_html(triage)
        self.assertNotIn(sentinel, str(raised.exception))

    def test_suspicious_unsupported_field_names_are_redacted(self):
        baseline = json.loads(FIXTURE.read_text(encoding="utf-8"))
        for sentinel in (
            "person@example.invalid",
            "/Users/synthetic/private-case.json",
            "token_sk_live_SYNTHETIC",
        ):
            with self.subTest(sentinel=sentinel):
                triage = copy.deepcopy(baseline)
                triage[sentinel] = "synthetic"

                errors = validator.validate_triage(triage)

                self.assertIn(
                    "session has unsupported fields: <redacted-field>",
                    errors,
                )
                self.assertNotIn(sentinel, "\n".join(errors))

    def test_candidate_identity_markers_are_rejected_before_render(self):
        baseline = json.loads(FIXTURE.read_text(encoding="utf-8"))
        mutations = {
            "safe_context.summary": (("safe_context", "summary"), "Candidate name: John Smith"),
            "facts[0].summary": (("facts", 0, "summary"), "Candidate name: John Smith"),
            "question.text": (
                ("question", "text"),
                "Which question should Candidate name: John Smith answer?",
            ),
            "blocked_claims[0]": (("blocked_claims", 0), "Candidate name: John Smith"),
        }
        sentinel = "Candidate name: John Smith"
        for path, (location, replacement) in mutations.items():
            triage = copy.deepcopy(baseline)
            target = triage
            for component in location[:-1]:
                target = target[component]
            target[location[-1]] = replacement
            with self.subTest(path=path):
                errors = validator.validate_triage(triage)
                self.assertTrue(
                    any("forbidden identity prose" in error for error in errors),
                    errors,
                )
                with self.assertRaises(renderer.TriageValidationError) as raised:
                    renderer.render_triage_html(triage)
                self.assertNotIn(sentinel, str(raised.exception))

    def test_candidate_identity_alias_is_rejected_in_v1_and_v2_handoff_without_echo(self):
        baseline = json.loads((FIXTURE.parent / "ready-en.json").read_text(encoding="utf-8"))
        sentinel = "Candidate identity: Alex Example"
        locations = (
            ("safe_context", "summary"),
            ("handoff", "packet", "context_summary"),
            ("handoff", "reentry_packet", "context_summary"),
        )

        for schema_version in (validator.SCHEMA_VERSION, validator.V2_SCHEMA_VERSION):
            for location in locations:
                triage = copy.deepcopy(baseline)
                if schema_version == validator.V2_SCHEMA_VERSION:
                    triage["schema_version"] = schema_version
                    triage["ui_locale"] = "en"
                    triage["content_locale"] = "en"
                    del triage["locale"]
                target = triage
                for component in location[:-1]:
                    target = target[component]
                target[location[-1]] = sentinel
                if schema_version == validator.V2_SCHEMA_VERSION:
                    snapshot = validator.snapshot_for_triage(triage)
                    triage["handoff"]["packet"]["source_snapshot"] = snapshot
                    triage["handoff"]["reentry_packet"]["source_snapshot"] = snapshot

                with self.subTest(schema_version=schema_version, location=location):
                    errors = validator.validate_triage(triage)
                    self.assertIn("session contains forbidden identity prose", errors)
                    self.assertNotIn(sentinel, "\n".join(errors))
                    with self.assertRaises(renderer.TriageValidationError) as raised:
                        renderer.render_triage_html(triage)
                    self.assertNotIn(sentinel, str(raised.exception))

    def test_spanish_candidate_identity_marker_is_rejected(self):
        triage = json.loads(
            (
                FIXTURE.parent / "clarify-es.json"
            ).read_text(encoding="utf-8")
        )
        triage["safe_context"]["summary"] = "Nombre del candidato: Juan Pérez"
        errors = validator.validate_triage(triage)
        self.assertTrue(any("forbidden identity prose" in error for error in errors), errors)
        with self.assertRaises(renderer.TriageValidationError):
            renderer.render_triage_html(triage)


if __name__ == "__main__":
    unittest.main()
