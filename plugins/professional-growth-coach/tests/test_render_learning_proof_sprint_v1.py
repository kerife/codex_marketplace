from __future__ import annotations

import copy
import importlib.util
import stat
import sys
import tempfile
import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = PLUGIN_ROOT / "scripts" / "render_learning_proof_sprint_v1.py"


def load_renderer():
    spec = importlib.util.spec_from_file_location("learning_proof_sprint_renderer", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def sample_sprint(locale: str = "en") -> dict[str, object]:
    return {
        "schema_version": "learning-proof-sprint-v1",
        "artifact_kind": "learning_proof_sprint",
        "locale": locale,
        "plan": {
            "sprint_goal": "Produce a private GitOps troubleshooting artifact.",
            "target_gap": "Demonstrable Argo CD troubleshooting proof.",
            "deliverable": "README, runbook, rollback log, and decision notes.",
            "publication_gate": "Exact action and target authorization after ownership, secrets, confidentiality, and public-disclosure review.",
        },
        "days": [
            {
                "day_number": day,
                "daily_goal": f"Complete day {day} privately.",
                "artifact_piece": f"Artifact piece {day}.",
                "proof_check": f"Proof check {day}.",
                "risk_check": f"Risk check {day}; synthetic inputs only.",
                "acceptance_test": f"Reviewer can inspect day {day}.",
                "candidate_timebox": "2 hours",
                "owner": "candidate" if day < 3 else "candidate_with_coach_review",
                "measurement_signal": f"day_{day}_ready_for_review",
                "next_safe_action": "Continue private build; no publication.",
            }
            for day in range(1, 6)
        ],
        "handoffs": [
            {
                "target_asset": "linkedin",
                "source_sprint_artifacts": "README scope and decision notes",
                "reuse_goal": "Prepare a private profile-copy draft.",
                "safe_claim": "Candidate-built lab artifact shows troubleshooting reasoning.",
                "proof_boundary": "Do not claim production ownership or hiring impact.",
                "required_review": "Ownership, secrets, confidentiality, and public-disclosure review.",
                "blocked_claims": "Production ownership, employer material, and outcome claims.",
            },
            {
                "target_asset": "application_packet",
                "source_sprint_artifacts": "README, runbook, and rollback log",
                "reuse_goal": "Prepare one vacancy-specific proof bullet.",
                "safe_claim": "Candidate-owned lab aligned to supplied requirements.",
                "proof_boundary": "Do not replace work history or imply employer deployment.",
                "required_review": "Truthfulness, link safety, ownership, and vacancy mapping.",
                "blocked_claims": "Production outage ownership, private impact, and payback claims.",
            },
            {
                "target_asset": "interview",
                "source_sprint_artifacts": "Context-action-result summary and decision notes",
                "reuse_goal": "Prepare a private troubleshooting proof story.",
                "safe_claim": "Candidate can explain a lab scenario and its limitations.",
                "proof_boundary": "State that this is candidate-owned lab practice.",
                "required_review": "Fact grounding, red-line claims, and answer practice.",
                "blocked_claims": "Production incident command, SLO ownership, and interview outcomes.",
            },
        ],
        "delivery": {
            "draft_only": True,
            "no_external_action": True,
            "local_save_mode": "disabled",
        },
    }


class LearningProofSprintRendererTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.renderer = load_renderer()

    def validated_snapshot(self):
        source_path = Path(__file__).resolve().parents[3] / "tests" / "test_learning_proof_sprint_v1.py"
        spec = importlib.util.spec_from_file_location("learning_proof_sprint_contract_fixture_for_renderer", source_path)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        source = module.source_group(locale="en")
        artifact = self.renderer.VALIDATOR._builder.build_learning_proof_sprint_v1(source)
        return self.renderer.VALIDATOR.validate_learning_proof_sprint_v1(artifact, source)

    def test_render_shows_five_day_timeline_and_three_asset_handoffs(self):
        rendered = self.renderer._render_artifact_html(sample_sprint())

        self.assertEqual(5, rendered.count('class="sprint-day"'))
        self.assertEqual(3, rendered.count('class="sprint-handoff"'))
        for day in range(1, 6):
            self.assertIn(f"Day {day}", rendered)
        for asset in ("LinkedIn", "Application packet", "Interview"):
            self.assertIn(asset, rendered)
        self.assertIn('aria-labelledby="sprint-timeline-heading"', rendered)
        self.assertIn('aria-labelledby="sprint-handoffs-heading"', rendered)

    def test_render_escapes_candidate_text_and_does_not_emit_private_ids_or_scripts(self):
        sprint = sample_sprint()
        sprint["plan"]["sprint_goal"] = '<img src=x onerror="alert(1)"> & "quoted"'
        sprint["days"][0]["daily_goal"] = "</p><script>alert('x')</script>"
        rendered = self.renderer._render_artifact_html(sprint)

        self.assertIn("&lt;img src=x onerror=&quot;alert(1)&quot;&gt; &amp; &quot;quoted&quot;", rendered)
        self.assertIn("&lt;/p&gt;&lt;script&gt;alert(&#x27;x&#x27;)&lt;/script&gt;", rendered)
        self.assertNotIn("<script", rendered.lower())
        self.assertNotIn("<img", rendered.lower())
        self.assertNotIn("candidate_id", rendered)
        self.assertNotIn("schema_version", rendered)
        self.assertNotIn("javascript:", rendered.lower())
        self.assertNotIn("<form", rendered.lower())
        self.assertNotIn("<button", rendered.lower())

    def test_render_localizes_english_and_spanish_copy(self):
        english = self.renderer._render_artifact_html(sample_sprint("en"))
        spanish = self.renderer._render_artifact_html(sample_sprint("es"))

        self.assertIn('<html lang="en">', english)
        self.assertIn("Private learning proof sprint", english)
        self.assertIn("Next safe action", english)
        self.assertIn('<html lang="es">', spanish)
        self.assertIn("Sprint privado de prueba de aprendizaje", spanish)
        self.assertIn("Siguiente acción segura", spanish)
        self.assertNotIn("Private learning proof sprint", spanish)

    def test_render_contains_responsive_print_dark_forced_colors_and_reduced_motion_hooks(self):
        rendered = self.renderer._render_artifact_html(sample_sprint())

        for hook in (
            "@media (max-width: 640px)",
            "@media print",
            "prefers-color-scheme: dark",
            "forced-colors: active",
            "prefers-reduced-motion: reduce",
        ):
            self.assertIn(hook, rendered)
        self.assertIn("break-inside: avoid", rendered)
        self.assertIn("--forest: #8fc9b0", rendered)
        self.assertIn("background: Canvas", rendered)
        self.assertIn("animation: none !important", rendered)

    def test_render_rejects_wrong_day_or_handoff_counts_before_output(self):
        renderer = self.renderer
        for key, count in (("days", 4), ("handoffs", 2)):
            sprint = sample_sprint()
            sprint[key] = sprint[key][:count]
            with self.subTest(key=key):
                with self.assertRaises(renderer.LearningProofSprintRenderValidationError):
                    renderer._render_artifact_html(sprint)

    def test_render_accepts_built_artifact_shape_with_reuse_map_and_artifact_lists(self):
        sprint = sample_sprint()
        sprint.pop("handoffs")
        sprint["reuse_map"] = []
        for handoff in sample_sprint()["handoffs"]:
            row = copy.deepcopy(handoff)
            row["source_sprint_artifacts"] = [row["source_sprint_artifacts"], "release checklist"]
            sprint["reuse_map"].append(row)
        sprint["plan"].update(
            {
                "plan_id": "LPS-PLAN-001",
                "kind": "learning_proof_sprint_plan",
                "candidate_id": "learning-argo-831",
                "vacancy_ids": ["V-831"],
                "candidate_fact_ids": ["F-831"],
            }
        )
        rendered = self.renderer._render_artifact_html(sprint)
        self.assertIn("README scope and decision notes · release checklist", rendered)
        self.assertNotIn("learning-argo-831", rendered)
        self.assertNotIn("LPS-PLAN-001", rendered)

    def test_v1_entrypoint_requires_validator_issued_snapshot(self):
        with self.assertRaises(self.renderer.LearningProofSprintRenderValidationError):
            self.renderer.render_learning_proof_sprint_v1(sample_sprint())
        with self.assertRaises(self.renderer.LearningProofSprintRenderValidationError):
            self.renderer.render_learning_proof_sprint_html(sample_sprint())

        source_path = Path(__file__).resolve().parents[3] / "tests" / "test_learning_proof_sprint_v1.py"
        spec = importlib.util.spec_from_file_location("learning_proof_sprint_contract_fixture", source_path)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        builder = load_renderer().VALIDATOR._builder
        artifact = builder.build_learning_proof_sprint_v1(module.source_group(locale="en"))
        validated = load_renderer().VALIDATOR.validate_learning_proof_sprint_v1(
            artifact, module.source_group(locale="en")
        )
        rendered = self.renderer.render_learning_proof_sprint_v1(validated)
        self.assertIn("Private learning proof sprint", rendered)
        self.assertEqual(5, rendered.count('class="sprint-day"'))

    def test_render_is_deterministic_and_writes_private_artifact_without_overwrite(self):
        renderer = self.renderer
        sprint = sample_sprint()
        first = renderer._render_artifact_html(sprint)
        self.assertEqual(first, renderer._render_artifact_html(copy.deepcopy(sprint)))
        validated = self.validated_snapshot()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "sprint.html"
            receipt = renderer.write_learning_proof_sprint_html(validated, output)
            self.assertEqual("en", receipt.locale)
            self.assertEqual(0o600, stat.S_IMODE(output.stat().st_mode))
            with self.assertRaises(FileExistsError):
                renderer.write_learning_proof_sprint_html(validated, output)

    def test_public_writer_validates_before_creating_output(self):
        renderer = self.renderer
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "invalid.html"
            with self.assertRaises(renderer.LearningProofSprintRenderValidationError):
                renderer.write_learning_proof_sprint_html(sample_sprint(), output)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
