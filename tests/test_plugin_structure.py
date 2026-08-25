"""Structural contract for the Professional Growth Coach plugin scaffold."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = REPO_ROOT / "plugins" / "professional-growth-coach"
MANIFEST_PATH = PLUGIN_ROOT / ".codex-plugin" / "plugin.json"
EXPECTED_SKILLS_PATH = PLUGIN_ROOT / "tests" / "fixtures" / "expected-skills.json"
RELEASE_REQUIREMENTS_PATH = REPO_ROOT / "requirements" / "release-validation.txt"
RELEASE_BOOTSTRAP_PATH = REPO_ROOT / "scripts" / "bootstrap_release_validation.sh"
RELEASE_RUNNER_PATH = REPO_ROOT / "scripts" / "run_release_validation.sh"
RELEASE_DOCUMENTATION_PATH = REPO_ROOT / "docs" / "release-validation.md"
INSTALLED_RELEASE_HELPER_PATH = REPO_ROOT / "scripts" / "verify_installed_plugin_release.py"
INSTALLED_SMOKE_HELPER_PATH = (
    REPO_ROOT / "scripts" / "run_installed_learning_eligibility_v3_smokes.py"
)
INSTALLED_SMOKE_SOURCES_PATH = (
    PLUGIN_ROOT / "tests" / "fixtures" / "vacancy-first-smoke" / "sources.json"
)
GITIGNORE_PATH = REPO_ROOT / ".gitignore"
MARKETPLACE_PATH = REPO_ROOT / ".agents" / "plugins" / "marketplace.json"
STATIC_CHECKER_PATH = PLUGIN_ROOT / "tests" / "run_static_checks.py"
DOSSIER_FIXTURE_PATH = (
    REPO_ROOT
    / "tests"
    / "evals"
    / "with-skill"
    / "fixtures"
    / "executive-career-dossier"
    / "scenario-a-es.json"
)
MARKET_DOSSIER_FIXTURE_PATH = DOSSIER_FIXTURE_PATH.with_name("scenario-market-en.json")
EXPECTED_MARKETPLACE_SHA256 = (
    "49622f84bd318518449979d029e3990da17aa0b2f944d06078b84a0b3b63ca12"
)
EXPECTED_RELEASE_REQUIREMENT = (
    "PyYAML==6.0.3 "
    "--hash=sha256:652cb6edd41e718550aad172851962662ff2681490a8a711af6a4d288dd96824\n"
)
EXPECTED_SKILL_VALIDATOR_SHA256 = (
    "6cc9dc3199c935916cf6f73fcbbbb0e3bb1b58c8f5109fefa499978908164f51"
)
EXPECTED_PLUGIN_VALIDATOR_SHA256 = (
    "ebda00d55d7518b127f675f062fb5c6e7a1ffdc0a99df1a55ac594400d7d3228"
)
EXPECTED_SKILLS: tuple[str, ...] = (
    "professional-growth-coach",
    "optimize-professional-profile",
    "explore-career-options",
    "research-professional-market",
    "optimize-career-assets",
    "prepare-role-interviews",
    "recommend-career-learning",
    "track-career-outcomes",
)
EXPECTED_STARTER_PROMPTS: tuple[str, ...] = (
    "Help me evaluate professional growth options using current evidence.",
    "Improve my professional positioning without taking external action.",
    "Prepare me for a growth or recruiter conversation.",
)
SKILL_NAME_PATTERN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
INSTALLABLE_VERSION_PATTERN = re.compile(
    r"^(?:0\.1\.0|0\.2\.0)(?:\+codex\.(?:\d{14}|local-\d{8}-\d{6}))?$"
)
PRIVATE_VACANCY_PACKET_SCENARIOS = (
    "ready-es",
    "ready-en",
    "revise-missing-es",
    "revise-review-en",
    "stop-constraint-es",
    "stop-constraint-en",
)
PRIVATE_VACANCY_PACKET_FIXTURE_PATHS = tuple(
    f"tests/evals/with-skill/fixtures/private-vacancy-application-packet-v1/{scenario}/{name}.json"
    for scenario in PRIVATE_VACANCY_PACKET_SCENARIOS
    for name in ("sources", "candidate-fact-matrix", "application-packet")
)
PRIVATE_VACANCY_PACKET_RELEASE_PATHS = (
    "schemas/candidate-fact-matrix-v1.schema.json",
    "schemas/private-vacancy-application-packet-v1.schema.json",
    "scripts/build_candidate_fact_matrix_v1.py",
    "scripts/validate_candidate_fact_matrix_v1.py",
    "scripts/build_private_vacancy_application_packet_v1.py",
    "scripts/validate_private_vacancy_application_packet_v1.py",
    "scripts/write_private_vacancy_application_packet_v1.py",
    "scripts/render_private_vacancy_application_packet_v1.py",
    "scripts/private_vacancy_packet_identity.py",
    "assets/private-vacancy-application-packet-v1.html",
    "assets/private-vacancy-application-packet-v1.css",
    "tests/test_candidate_fact_matrix_v1.py",
    "tests/test_private_vacancy_application_packet_v1.py",
    "tests/test_write_private_vacancy_application_packet_v1.py",
    "tests/test_render_private_vacancy_application_packet_v1.py",
    "tests/test_private_vacancy_application_packet_routing.py",
    *PRIVATE_VACANCY_PACKET_FIXTURE_PATHS,
)


def load_static_checker():
    specification = importlib.util.spec_from_file_location(
        "job_search_coach_static_checks", STATIC_CHECKER_PATH
    )
    if specification is None or specification.loader is None:
        raise RuntimeError(f"cannot load static checker: {STATIC_CHECKER_PATH}")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def load_repo_script(path: Path, name: str):
    specification = importlib.util.spec_from_file_location(name, path)
    if specification is None or specification.loader is None:
        raise RuntimeError(f"cannot load repository script: {path.name}")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


class JobSearchCoachPluginStructureTests(unittest.TestCase):
    def test_private_packet_skill_routing_surface_is_regular_and_versioned(self) -> None:
        """Break caught: routing points to a missing, linked, or unversioned contract."""

        paths = (
            PLUGIN_ROOT / "skills" / "professional-growth-coach" / "SKILL.md",
            PLUGIN_ROOT
            / "skills"
            / "professional-growth-coach"
            / "references"
            / "routing.md",
            PLUGIN_ROOT / "skills" / "optimize-career-assets" / "SKILL.md",
            PLUGIN_ROOT
            / "skills"
            / "optimize-career-assets"
            / "references"
            / "asset-workflow.md",
            PLUGIN_ROOT / "README.md",
            REPO_ROOT / "tests" / "test_private_vacancy_application_packet_routing.py",
        )
        for path in paths:
            with self.subTest(path=path.name):
                self.assertTrue(path.is_file(), path)
                self.assertFalse(path.is_symlink(), path)

        asset_contract = paths[2].read_text(encoding="utf-8")
        workflow = paths[3].read_text(encoding="utf-8")
        self.assertIn("private-vacancy-application-packet-v1.schema.json", asset_contract)
        self.assertIn("build_validated_private_vacancy_application_packet_v1", workflow)
        self.assertIn("write_private_vacancy_application_packet_v1", workflow)
        self.assertIn("write_private_vacancy_application_packet_html_v1", workflow)

    def test_private_snapshot_keeps_real_copied_bytes_after_originals_change(self) -> None:
        """Break caught: reopening either supplied root after capture changes imports."""

        smoke = load_repo_script(INSTALLED_SMOKE_HELPER_PATH, "installed_private_snapshot")
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "source"
            cache = root / "cache"
            for plugin in (source, cache):
                (plugin / "scripts").mkdir(parents=True)
                (plugin / "scripts" / "sample.py").write_text(
                    "VALUE = 'captured'\n", encoding="utf-8"
                )

            with smoke.capture_verified_private_snapshots(source, cache) as (
                snapshot_source,
                snapshot_cache,
            ):
                (source / "scripts" / "sample.py").write_text(
                    "VALUE = 'changed-source'\n", encoding="utf-8"
                )
                (cache / "scripts" / "sample.py").write_text(
                    "VALUE = 'changed-cache'\n", encoding="utf-8"
                )
                module = smoke.load_installed_product_modules(
                    snapshot_cache, ("sample",)
                )["sample"]
                self.assertEqual("captured", module.VALUE)
                self.assertEqual(
                    b"VALUE = 'captured'\n",
                    (snapshot_source / "scripts" / "sample.py").read_bytes(),
                )

    def test_private_snapshot_uses_private_modes_and_independent_files(self) -> None:
        """Break caught: snapshots exposing or hardlinking supplied-release files."""

        smoke = load_repo_script(INSTALLED_SMOKE_HELPER_PATH, "installed_private_modes")
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "source"
            cache = root / "cache"
            for plugin in (source, cache):
                target = plugin / "nested" / "artifact.txt"
                target.parent.mkdir(parents=True)
                target.write_bytes(b"captured bytes")

            with smoke.capture_verified_private_snapshots(source, cache) as (
                snapshot_source,
                snapshot_cache,
            ):
                for directory in (
                    snapshot_source.parent,
                    snapshot_source,
                    snapshot_source / "nested",
                    snapshot_cache,
                    snapshot_cache / "nested",
                ):
                    self.assertEqual(0o700, directory.stat().st_mode & 0o777)
                for original, captured in (
                    (source / "nested" / "artifact.txt", snapshot_source / "nested" / "artifact.txt"),
                    (cache / "nested" / "artifact.txt", snapshot_cache / "nested" / "artifact.txt"),
                ):
                    self.assertEqual(0o600, captured.stat().st_mode & 0o777)
                    self.assertNotEqual(original.stat().st_ino, captured.stat().st_ino)

    def test_private_snapshot_captures_every_file_in_a_shared_directory(self) -> None:
        """Break caught: a later inventory entry cannot reuse its private parent."""

        smoke = load_repo_script(INSTALLED_SMOKE_HELPER_PATH, "installed_private_shared_parent")
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "source"
            cache = root / "cache"
            for plugin in (source, cache):
                (plugin / "scripts").mkdir(parents=True)
                (plugin / "scripts" / "first.py").write_bytes(b"first")
                (plugin / "scripts" / "second.py").write_bytes(b"second")

            with smoke.capture_verified_private_snapshots(source, cache) as snapshots:
                self.assertEqual(
                    b"first", (snapshots[1] / "scripts" / "first.py").read_bytes()
                )
                self.assertEqual(
                    b"second", (snapshots[1] / "scripts" / "second.py").read_bytes()
                )

    def test_private_snapshot_removes_temporary_root_on_success_and_error(self) -> None:
        """Break caught: snapshot directories surviving either context-manager path."""

        smoke = load_repo_script(INSTALLED_SMOKE_HELPER_PATH, "installed_private_cleanup")
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "source"
            cache = root / "cache"
            for plugin in (source, cache):
                plugin.mkdir()
                (plugin / "artifact.txt").write_bytes(b"same")

            with smoke.capture_verified_private_snapshots(source, cache) as snapshots:
                successful_root = snapshots[0].parent
                self.assertTrue(successful_root.is_dir())
            self.assertFalse(successful_root.exists())

            with self.assertRaisesRegex(RuntimeError, "injected"):
                with smoke.capture_verified_private_snapshots(source, cache) as snapshots:
                    error_root = snapshots[0].parent
                    raise RuntimeError("injected")
            self.assertFalse(error_root.exists())

    def test_private_snapshot_rejects_unsafe_inputs_and_byte_drift_without_echo(self) -> None:
        """Break caught: unsafe or changed original bytes entering a private snapshot."""

        smoke = load_repo_script(INSTALLED_SMOKE_HELPER_PATH, "installed_private_rejection")
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "source"
            cache = root / "cache"
            source.mkdir()
            cache.mkdir()
            (source / "artifact.txt").write_bytes(b"same")
            (cache / "artifact.txt").write_bytes(b"same")
            (source / "escape.txt").symlink_to(root / "outside.txt")
            with self.assertRaisesRegex(smoke.InstalledSmokeError, "installed smoke failed") as caught:
                with smoke.capture_verified_private_snapshots(source, cache):
                    pass
            self.assertNotIn(str(source), str(caught.exception))

            (source / "escape.txt").unlink()
            os.mkfifo(source / "pipe")
            with self.assertRaisesRegex(smoke.InstalledSmokeError, "installed smoke failed") as caught:
                with smoke.capture_verified_private_snapshots(source, cache):
                    pass
            self.assertNotIn(str(source), str(caught.exception))
            (source / "pipe").unlink()
            original_inventory = smoke._snapshot_inventory

            def drifting_inventory(plugin: Path):
                inventory = original_inventory(plugin)
                if plugin == source:
                    (source / "artifact.txt").write_bytes(b"drift")
                return inventory

            smoke._snapshot_inventory = drifting_inventory
            try:
                with self.assertRaisesRegex(smoke.InstalledSmokeError, "installed smoke failed") as caught:
                    with smoke.capture_verified_private_snapshots(source, cache):
                        pass
            finally:
                smoke._snapshot_inventory = original_inventory
            self.assertNotIn(str(source), str(caught.exception))

    def test_installed_module_syntax_error_is_generic(self) -> None:
        """Break caught: product SyntaxError escapes the generic import boundary."""

        smoke = load_repo_script(INSTALLED_SMOKE_HELPER_PATH, "installed_syntax_generic")
        with tempfile.TemporaryDirectory() as temporary_directory:
            plugin = Path(temporary_directory) / "private-plugin"
            scripts = plugin / "scripts"
            scripts.mkdir(parents=True)
            (scripts / "broken.py").write_text("def broken(:\n", encoding="utf-8")
            with self.assertRaisesRegex(
                smoke.InstalledSmokeError, "installed smoke import boundary failed"
            ) as caught:
                smoke.load_installed_product_modules(plugin, ("broken",))
        self.assertNotIn(str(plugin), str(caught.exception))

    def test_installed_import_boundary_rejects_prior_path_preload_and_namespace_escape(self) -> None:
        """Break caught: controller import state supplies non-snapshot dependencies."""

        smoke = load_repo_script(INSTALLED_SMOKE_HELPER_PATH, "installed_import_escape")
        previous_path = list(sys.path)
        previous_modules = dict(sys.modules)
        try:
            with tempfile.TemporaryDirectory() as temporary_directory:
                root = Path(temporary_directory)
                plugin = root / "plugin"
                scripts = plugin / "scripts"
                external = root / "external"
                scripts.mkdir(parents=True)
                external.mkdir()
                (external / "path_dependency.py").write_text(
                    "VALUE = 'outside-path'\n", encoding="utf-8"
                )
                (scripts / "path_escape.py").write_text(
                    "from path_dependency import VALUE\n", encoding="utf-8"
                )
                (scripts / "preloaded_escape.py").write_text(
                    "from external import VALUE\n", encoding="utf-8"
                )
                (scripts / "namespace_escape.py").write_text(
                    "import importlib.machinery\n"
                    "import sys\n"
                    "import types\n"
                    "namespace = types.ModuleType('external_namespace')\n"
                    f"namespace.__path__ = [{str(external)!r}]\n"
                    "namespace.__spec__ = importlib.machinery.ModuleSpec(\n"
                    "    'external_namespace', loader=None, is_package=True\n"
                    ")\n"
                    f"namespace.__spec__.submodule_search_locations = [{str(external)!r}]\n"
                    "sys.modules['external_namespace'] = namespace\n",
                    encoding="utf-8",
                )
                sys.path.insert(0, str(external))
                preloaded = type(sys)("external")
                preloaded.VALUE = "outside-preload"
                preloaded.__file__ = str(external / "external.py")
                sys.modules["external"] = preloaded

                for module_name in (
                    "path_escape",
                    "preloaded_escape",
                    "namespace_escape",
                ):
                    with self.subTest(module=module_name):
                        with self.assertRaisesRegex(
                            smoke.InstalledSmokeError,
                            "installed smoke import boundary failed",
                        ) as caught:
                            smoke.load_installed_product_modules(
                                plugin, (module_name,)
                            )
                        self.assertNotIn(str(root), str(caught.exception))
        finally:
            sys.path[:] = previous_path
            sys.modules.clear()
            sys.modules.update(previous_modules)

    def test_installed_import_boundary_allows_stdlib_and_locked_site_packages(self) -> None:
        """Break caught: isolation drops stdlib or the locked environment's site path."""

        if importlib.util.find_spec("yaml") is None:
            self.skipTest("locked PyYAML is unavailable in this interpreter")
        smoke = load_repo_script(INSTALLED_SMOKE_HELPER_PATH, "installed_import_runtime")
        with tempfile.TemporaryDirectory() as temporary_directory:
            plugin = Path(temporary_directory) / "plugin"
            scripts = plugin / "scripts"
            scripts.mkdir(parents=True)
            (scripts / "runtime_dependency.py").write_text(
                "import json\n"
                "import yaml\n"
                "VALUE = json.loads('{\"answer\": 42}')[\"answer\"]\n"
                "YAML_VALUE = yaml.safe_load('answer: 42')[\"answer\"]\n",
                encoding="utf-8",
            )
            module = smoke.load_installed_product_modules(
                plugin, ("runtime_dependency",)
            )["runtime_dependency"]

        self.assertEqual(42, module.VALUE)
        self.assertEqual(42, module.YAML_VALUE)

    def test_installed_loader_restores_controller_import_state_after_success_and_error(self) -> None:
        """Break caught: a direct loader call leaks or replaces controller import state."""

        smoke = load_repo_script(INSTALLED_SMOKE_HELPER_PATH, "installed_import_restore")
        with tempfile.TemporaryDirectory() as temporary_directory:
            plugin = Path(temporary_directory) / "plugin"
            scripts = plugin / "scripts"
            scripts.mkdir(parents=True)
            (scripts / "success.py").write_text(
                "import fractions\nVALUE = fractions.Fraction(1, 2)\n",
                encoding="utf-8",
            )
            (scripts / "failure.py").write_text(
                "import unavailable_snapshot_dependency\n", encoding="utf-8"
            )
            for module_name, fails in (("success", False), ("failure", True)):
                with self.subTest(module=module_name):
                    previous_path = list(sys.path)
                    previous_modules = tuple(sys.modules.items())
                    if fails:
                        with self.assertRaisesRegex(
                            smoke.InstalledSmokeError,
                            "installed smoke import boundary failed",
                        ):
                            smoke.load_installed_product_modules(
                                plugin, (module_name,)
                            )
                    else:
                        loaded = smoke.load_installed_product_modules(
                            plugin, (module_name,)
                        )
                        self.assertEqual("1/2", str(loaded[module_name].VALUE))
                    self.assertEqual(previous_path, sys.path)
                    current_modules = tuple(sys.modules.items())
                    self.assertEqual(
                        tuple(name for name, _ in previous_modules),
                        tuple(name for name, _ in current_modules),
                    )
                    self.assertTrue(
                        all(
                            previous is current
                            for (_, previous), (_, current) in zip(
                                previous_modules, current_modules, strict=True
                            )
                        )
                    )

    def test_run_smokes_keeps_lazy_import_isolated_and_restores_controller_state(self) -> None:
        """Break caught: a post-load lazy import escapes during semantic execution."""

        smoke = load_repo_script(INSTALLED_SMOKE_HELPER_PATH, "installed_lazy_import")
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "source"
            cache = root / "cache"
            external = root / "external"
            external.mkdir()
            (external / "external.py").write_text(
                "VALUE = 'outside-lazy'\n", encoding="utf-8"
            )
            for plugin in (source, cache):
                shutil.copytree(
                    PLUGIN_ROOT,
                    plugin,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
                )
                with (plugin / "scripts" / "semantic_provenance_snapshot.py").open(
                    "a", encoding="utf-8"
                ) as stream:
                    stream.write(
                        "\ndef load_external_value():\n"
                        "    from external import VALUE\n"
                        "    return VALUE\n"
                    )

            original_matrix = smoke.run_installed_semantic_matrix
            original_subprocess = smoke.subprocess.run
            previous_path = list(sys.path)
            previous_modules = tuple(sys.modules.items())

            def semantic(snapshot_root: Path, modules: dict[str, object]):
                modules["semantic_provenance_snapshot"].load_external_value()
                return {
                    "matrix_version": "vacancy-first-installed-smoke-v1",
                    "accepted": 39,
                    "rejected": 9,
                    "accepted_cases": tuple(),
                    "rejected_cases": tuple(),
                    "accepted_groups": tuple(),
                    "rejected_groups": tuple(),
                }

            def static_subprocess(*args, **kwargs):
                return subprocess.CompletedProcess(
                    args[0], 0, stdout="repository conformance not bundled\n", stderr=""
                )

            sys.path.insert(0, str(external))
            expected_path = list(sys.path)
            expected_modules = tuple(sys.modules.items())
            smoke.run_installed_semantic_matrix = semantic
            smoke.subprocess.run = static_subprocess
            try:
                with self.assertRaisesRegex(
                    smoke.InstalledSmokeError, "installed smoke failed"
                ):
                    smoke.run_smokes(cache, source)
                self.assertEqual(expected_path, sys.path)
                current_modules = tuple(sys.modules.items())
                self.assertEqual(
                    tuple(name for name, _ in expected_modules),
                    tuple(name for name, _ in current_modules),
                )
                self.assertTrue(
                    all(
                        previous is current
                        for (_, previous), (_, current) in zip(
                            expected_modules, current_modules, strict=True
                        )
                    )
                )
            finally:
                smoke.run_installed_semantic_matrix = original_matrix
                smoke.subprocess.run = original_subprocess
                sys.path[:] = previous_path
                sys.modules.clear()
                sys.modules.update(dict(previous_modules))

    def test_run_smokes_routes_imports_reads_and_static_subprocess_to_snapshot(self) -> None:
        """Break caught: semantic execution reopening a mutable supplied cache root."""

        smoke = load_repo_script(INSTALLED_SMOKE_HELPER_PATH, "installed_private_routing")
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "source"
            cache = root / "cache"
            shutil.copytree(PLUGIN_ROOT, source, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            shutil.copytree(PLUGIN_ROOT, cache, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            original_capture = smoke.capture_verified_private_snapshots
            original_matrix = smoke.run_installed_semantic_matrix
            original_subprocess = smoke.subprocess.run
            observed: dict[str, object] = {}
            static_calls: list[
                tuple[Path, list[str], dict[str, str]]
            ] = []
            previous_path = list(sys.path)
            previous_modules = tuple(sys.modules.items())

            @contextmanager
            def mutate_after_capture(source_root: Path, cache_root: Path):
                with original_capture(source_root, cache_root) as snapshots:
                    for plugin in (source, cache):
                        (plugin / "schemas" / "candidate-gap-response-v1.schema.json").write_text(
                            "{}", encoding="utf-8"
                        )
                        (plugin / "tests" / "fixtures" / "vacancy-first-smoke" / "sources.json").write_text(
                            "{}", encoding="utf-8"
                        )
                    yield snapshots

            def semantic(snapshot_root: Path, modules: dict[str, object]) -> dict[str, object]:
                observed["semantic_root"] = snapshot_root
                observed["source_schema"] = smoke.load_installed_smoke_sources(snapshot_root)["schema_version"]
                self.assertTrue(
                    Path(modules["semantic_provenance_snapshot"].__file__).resolve().is_relative_to(
                        snapshot_root.resolve()
                    )
                )
                return {
                    "matrix_version": "vacancy-first-installed-smoke-v1",
                    "accepted": 39,
                    "rejected": 9,
                    "accepted_cases": tuple(),
                    "rejected_cases": tuple(),
                    "accepted_groups": tuple(),
                    "rejected_groups": tuple(),
                }

            def static_subprocess(*args, **kwargs):
                command = args[0]
                if command[-1].endswith("run_static_checks.py"):
                    static_calls.append((kwargs["cwd"], command, kwargs["env"]))
                return original_subprocess(*args, **kwargs)

            smoke.capture_verified_private_snapshots = mutate_after_capture
            smoke.run_installed_semantic_matrix = semantic
            smoke.subprocess.run = static_subprocess
            try:
                receipt = smoke.run_smokes(cache, source)
            finally:
                smoke.capture_verified_private_snapshots = original_capture
                smoke.run_installed_semantic_matrix = original_matrix
                smoke.subprocess.run = original_subprocess

        self.assertEqual(39, receipt["accepted"])
        self.assertEqual("vacancy-first-smoke-sources-v1", observed["source_schema"])
        self.assertEqual(1, len(static_calls))
        static_cwd, static_command, static_environment = static_calls[0]
        self.assertEqual(observed["semantic_root"], static_cwd)
        self.assertEqual(sys.executable, static_command[0])
        self.assertEqual(["-I", "-B"], static_command[1:3])
        self.assertEqual(
            {"PATH": os.defpath, "PYTHONDONTWRITEBYTECODE": "1"},
            static_environment,
        )
        self.assertNotIn("PYTHONPATH", static_environment)
        self.assertEqual(previous_path, sys.path)
        current_modules = tuple(sys.modules.items())
        self.assertEqual(
            tuple(name for name, _ in previous_modules),
            tuple(name for name, _ in current_modules),
        )
        self.assertTrue(
            all(
                previous is current
                for (_, previous), (_, current) in zip(
                    previous_modules, current_modules, strict=True
                )
            )
        )

    def test_exact_installed_cache_resolver_accepts_only_one_enabled_matching_row(self) -> None:
        helper = load_repo_script(INSTALLED_RELEASE_HELPER_PATH, "installed_release_helper")
        with tempfile.TemporaryDirectory() as temporary_directory:
            cache_family = Path(temporary_directory) / "cache-family"
            expected = cache_family / "professional-growth-coach" / "0.2.0+codex.20260822000000"
            expected.mkdir(parents=True)
            row = {
                "pluginId": "professional-growth-coach@codex-marketplace-public",
                "name": "professional-growth-coach",
                "marketplaceName": "codex-marketplace-public",
                "version": "0.2.0+codex.20260822000000",
                "installed": True,
                "enabled": True,
            }
            resolved = helper.resolve_exact_installed_cache(
                {"installed": [row], "available": []},
                "professional-growth-coach",
                "codex-marketplace-public",
                "0.2.0+codex.20260822000000",
                cache_family,
            )
        self.assertEqual(expected, resolved)

    def test_exact_installed_cache_resolver_rejects_ambiguous_or_unsafe_input(self) -> None:
        helper = load_repo_script(INSTALLED_RELEASE_HELPER_PATH, "installed_release_helper_bad")
        good = {
            "pluginId": "professional-growth-coach@codex-marketplace-public",
            "name": "professional-growth-coach",
            "marketplaceName": "codex-marketplace-public",
            "version": "0.2.0+codex.20260822000000",
            "installed": True,
            "enabled": True,
        }
        with tempfile.TemporaryDirectory() as temporary_directory:
            cache_family = Path(temporary_directory) / "cache-family"
            (cache_family / good["name"] / good["version"]).mkdir(parents=True)
            cases = (
                ("zero", {"installed": []}, good["name"], good["version"]),
                ("multiple", {"installed": [good, dict(good)]}, good["name"], good["version"]),
                ("disabled", {"installed": [{**good, "enabled": False}]}, good["name"], good["version"]),
                ("not-installed", {"installed": [{**good, "installed": False}]}, good["name"], good["version"]),
                ("wrong-version", {"installed": [good]}, good["name"], "0.2.0+codex.20260822000001"),
                ("plugin-traversal", {"installed": [good]}, "../professional-growth-coach", good["version"]),
                ("version-traversal", {"installed": [good]}, good["name"], "../latest"),
            )
            for label, plugin_list, plugin, version in cases:
                with self.subTest(case=label):
                    with self.assertRaisesRegex(
                        helper.ReleaseVerificationError,
                        "installed plugin resolution failed",
                    ) as caught:
                        helper.resolve_exact_installed_cache(
                            plugin_list,
                            plugin,
                            "codex-marketplace-public",
                            version,
                            cache_family,
                        )
                    self.assertNotIn(str(temporary_directory), str(caught.exception))

    def test_release_inventory_and_digest_are_sorted_exact_and_adversarial(self) -> None:
        helper = load_repo_script(INSTALLED_RELEASE_HELPER_PATH, "installed_release_inventory")
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory) / "release"
            root.mkdir()
            (root / "z.txt").write_bytes(b"z")
            (root / "a.txt").write_bytes(b"a")
            inventory = helper.release_inventory(root)
            a_digest = hashlib.sha256(b"a").hexdigest()
            z_digest = hashlib.sha256(b"z").hexdigest()
            self.assertEqual((('a.txt', a_digest), ('z.txt', z_digest)), inventory)
            expected = hashlib.sha256(
                b"a.txt\0" + a_digest.encode("ascii") + b"\n"
                + b"z.txt\0" + z_digest.encode("ascii") + b"\n"
            ).hexdigest()
            self.assertEqual(expected, helper.aggregate_release_digest(root))

            bytecode = root / "scripts" / "__pycache__"
            bytecode.mkdir(parents=True)
            (bytecode / "bad.pyc").write_bytes(b"bytecode")
            with self.assertRaisesRegex(
                helper.ReleaseVerificationError, "release inventory is invalid"
            ):
                helper.release_inventory(root)

            shutil.rmtree(bytecode)
            (root / "metadata.bin").write_bytes(
                b"/" + b"Users/synthetic-user/projects/job_search_coach/private.txt"
            )
            with self.assertRaisesRegex(
                helper.ReleaseVerificationError, "release inventory is invalid"
            ):
                helper.release_inventory(root)

    def test_release_parity_rejects_inventory_and_per_file_mismatch(self) -> None:
        helper = load_repo_script(INSTALLED_RELEASE_HELPER_PATH, "installed_release_parity")
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "source"
            cache = root / "cache"
            source.mkdir()
            cache.mkdir()
            (source / "same.txt").write_text("same", encoding="utf-8")
            (cache / "same.txt").write_text("same", encoding="utf-8")
            result = helper.verify_release_parity(source, cache)
            self.assertEqual(1, result["file_count"])
            self.assertEqual(result["source_aggregate_sha256"], result["cache_aggregate_sha256"])

            (cache / "extra.txt").write_text("extra", encoding="utf-8")
            with self.assertRaisesRegex(helper.ReleaseVerificationError, "release parity failed"):
                helper.verify_release_parity(source, cache)
            (cache / "extra.txt").unlink()
            (cache / "same.txt").write_text("different", encoding="utf-8")
            with self.assertRaisesRegex(helper.ReleaseVerificationError, "release parity failed"):
                helper.verify_release_parity(source, cache)

    def test_installed_smoke_loader_rejects_product_modules_outside_plugin_root(self) -> None:
        smoke = load_repo_script(INSTALLED_SMOKE_HELPER_PATH, "installed_smoke_helper")
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            plugin = root / "plugin"
            scripts = plugin / "scripts"
            scripts.mkdir(parents=True)
            (scripts / "inside.py").write_text("VALUE = 'inside'\n", encoding="utf-8")
            modules = smoke.load_installed_product_modules(plugin, ("inside",))
            self.assertEqual("inside", modules["inside"].VALUE)
            self.assertTrue(
                Path(modules["inside"].__file__).resolve().is_relative_to(plugin.resolve())
            )

            outside = root / "outside.py"
            outside.write_text("VALUE = 'outside'\n", encoding="utf-8")
            (scripts / "escape.py").symlink_to(outside)
            with self.assertRaisesRegex(
                smoke.InstalledSmokeError, "installed smoke import boundary failed"
            ) as caught:
                smoke.load_installed_product_modules(plugin, ("escape",))
            self.assertNotIn(str(temporary_directory), str(caught.exception))

    def test_installed_smoke_fixture_is_closed_hashed_and_complete(self) -> None:
        smoke = load_repo_script(INSTALLED_SMOKE_HELPER_PATH, "installed_smoke_sources")
        checker = load_static_checker()
        self.assertIn(
            "tests/fixtures/vacancy-first-smoke/sources.json",
            checker.MARKET_DOSSIER_PACKAGE_PATHS,
        )
        sources = smoke.load_installed_smoke_sources(PLUGIN_ROOT)
        self.assertEqual(
            {"schema_version", "sources", "source_sha256", "aggregate_sha256"},
            set(sources),
        )
        self.assertEqual({"research", "dossier", "provider"}, set(sources["sources"]))
        self.assertEqual({"research", "dossier", "provider"}, set(sources["source_sha256"]))
        self.assertTrue(INSTALLED_SMOKE_SOURCES_PATH.is_file())

    def test_installed_smoke_runs_complete_semantic_matrix_from_installed_root(self) -> None:
        smoke = load_repo_script(INSTALLED_SMOKE_HELPER_PATH, "installed_smoke_matrix")
        modules = smoke.load_installed_product_modules(PLUGIN_ROOT)
        original_subprocess = smoke.subprocess.run
        renderer_calls: list[tuple[list[str], dict[str, str]]] = []

        def renderer_subprocess(*args, **kwargs):
            renderer_calls.append((args[0], kwargs["env"]))
            return original_subprocess(*args, **kwargs)

        smoke.subprocess.run = renderer_subprocess
        try:
            receipt = smoke.run_installed_semantic_matrix(PLUGIN_ROOT, modules)
        finally:
            smoke.subprocess.run = original_subprocess
        self.assertEqual("vacancy-first-installed-smoke-v1", receipt["matrix_version"])
        self.assertEqual(39, receipt["accepted"])
        self.assertEqual(9, receipt["rejected"])
        self.assertEqual(39, len(receipt["accepted_cases"]))
        self.assertEqual(9, len(receipt["rejected_cases"]))
        self.assertEqual(39, len(set(receipt["accepted_cases"])))
        self.assertEqual(9, len(set(receipt["rejected_cases"])))
        self.assertIn(
            "response_mapping.public_v1_resolves_private_v003",
            receipt["accepted_cases"],
        )
        self.assertIn(
            "provider_displacement.lp002_rejects_prior_lp001_chain",
            receipt["rejected_cases"],
        )
        self.assertEqual(
            (
                "response_mapping",
                "recurrence_routes",
                "nonlearning_routes",
                "provider_lifecycle",
                "action_matrix_es",
                "action_matrix_en",
                "exact_unions_snapshots",
                "dom_aria",
                "historical_bytes",
            ),
            tuple(receipt["accepted_groups"]),
        )
        self.assertEqual(
            (
                "provider_displacement",
                "private_disclosure",
                "forged_sources",
                "crossed_sources",
                "mutable_sources",
                "oversized_sources",
                "exceptional_sources",
                "writer_output",
                "cli_output",
            ),
            tuple(receipt["rejected_groups"]),
        )
        self.assertEqual(1, len(renderer_calls))
        renderer_command, renderer_environment = renderer_calls[0]
        self.assertEqual(sys.executable, renderer_command[0])
        self.assertEqual(["-I", "-B"], renderer_command[1:3])
        self.assertEqual(
            {"PATH": os.defpath, "PYTHONDONTWRITEBYTECODE": "1"},
            renderer_environment,
        )
        self.assertNotIn("PYTHONPATH", renderer_environment)

    def test_installed_smoke_runs_private_packet_matrix_from_installed_root(self) -> None:
        """Break caught: packet proof reopens supplied roots or checkout modules."""

        smoke = load_repo_script(INSTALLED_SMOKE_HELPER_PATH, "installed_packet_matrix")
        accepted_ids = (
            "packet_ready_es",
            "packet_ready_en",
            "packet_revise_missing_es",
            "packet_revise_review_en",
            "packet_stop_constraint_es",
            "packet_stop_constraint_en",
        )
        rejected_ids = (
            "packet_wrong_action",
            "packet_crossed_research",
            "packet_crossed_fact_source",
            "packet_tampered_matrix",
            "packet_tampered_packet",
            "packet_alias_signal",
            "packet_substring_signal",
            "packet_caller_prose",
            "packet_private_value",
            "packet_confidential_claim",
            "packet_hostile_mapping",
            "packet_writer_cli_partial",
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "source"
            cache = root / "cache"
            for plugin in (source, cache):
                shutil.copytree(
                    PLUGIN_ROOT,
                    plugin,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
                )

            original_capture = smoke.capture_verified_private_snapshots
            original_semantic = smoke.run_installed_semantic_matrix
            original_subprocess = smoke.subprocess.run
            poison_name = "build_candidate_fact_matrix_v1"
            prior_poison = sys.modules.get(poison_name)
            checkout_poison = type(sys)(poison_name)
            checkout_poison.__file__ = str(
                PLUGIN_ROOT / "scripts" / f"{poison_name}.py"
            )

            def poisoned_builder(*args, **kwargs):
                raise RuntimeError("checkout packet builder executed")

            checkout_poison.build_candidate_fact_matrix_v1 = poisoned_builder
            sys.modules[poison_name] = checkout_poison

            @contextmanager
            def poison_after_capture(source_root: Path, cache_root: Path):
                with original_capture(source_root, cache_root) as snapshots:
                    for supplied in (source_root, cache_root):
                        for relative in (
                            "scripts/build_candidate_fact_matrix_v1.py",
                            "scripts/build_private_vacancy_application_packet_v1.py",
                            "scripts/render_private_vacancy_application_packet_v1.py",
                            "assets/private-vacancy-application-packet-v1.html",
                            "assets/private-vacancy-application-packet-v1.css",
                            "tests/fixtures/vacancy-first-smoke/sources.json",
                        ):
                            (supplied / relative).write_text(
                                "supplied root poisoned after snapshot\n",
                                encoding="utf-8",
                            )
                    yield snapshots

            def historical_semantic(*args, **kwargs):
                return {
                    "matrix_version": "vacancy-first-installed-smoke-v1",
                    "accepted": 39,
                    "rejected": 9,
                    "accepted_cases": tuple(f"accepted.{index}" for index in range(39)),
                    "rejected_cases": tuple(f"rejected.{index}" for index in range(9)),
                    "accepted_groups": ("accepted",),
                    "rejected_groups": ("rejected",),
                }

            def routed_subprocess(*args, **kwargs):
                command = args[0]
                if command[-1].endswith("run_static_checks.py"):
                    return subprocess.CompletedProcess(
                        command,
                        0,
                        stdout="repository conformance not bundled\n",
                        stderr="",
                    )
                return original_subprocess(*args, **kwargs)

            smoke.capture_verified_private_snapshots = poison_after_capture
            smoke.run_installed_semantic_matrix = historical_semantic
            smoke.subprocess.run = routed_subprocess
            try:
                receipt = smoke.run_smokes(cache, source)
            finally:
                smoke.capture_verified_private_snapshots = original_capture
                smoke.run_installed_semantic_matrix = original_semantic
                smoke.subprocess.run = original_subprocess
                if prior_poison is None:
                    sys.modules.pop(poison_name, None)
                else:
                    sys.modules[poison_name] = prior_poison

        self.assertEqual(39, receipt["accepted"])
        self.assertEqual(9, receipt["rejected"])
        self.assertEqual(6, receipt["packet_accepted"])
        self.assertEqual(12, receipt["packet_rejected"])
        self.assertEqual(accepted_ids, tuple(receipt["packet_accepted_cases"]))
        self.assertEqual(rejected_ids, tuple(receipt["packet_rejected_cases"]))
        self.assertEqual(
            "validated_installed_builder_output_only",
            receipt["packet_artifact_provenance"],
        )
        self.assertEqual(
            "validated_installed_renderer_output_only",
            receipt["packet_renderer_provenance"],
        )
        self.assertEqual("verified_private_snapshot_only", receipt["import_boundary"])

    def test_installed_smoke_recomputes_pinned_historical_render_bytes(self) -> None:
        smoke = load_repo_script(INSTALLED_SMOKE_HELPER_PATH, "installed_smoke_history")
        modules = smoke.load_installed_product_modules(PLUGIN_ROOT)
        sources = smoke.load_installed_smoke_sources(PLUGIN_ROOT)["sources"]
        self.assertEqual(
            {
                "v1": {
                    "bytes": 97805,
                    "sha256": "4dbb6be8e1a95cdcc8f3e937dcca600fb26f9dc53d7ef519027048c73b12316f",
                },
                "v2": {
                    "bytes": 101282,
                    "sha256": "0232f7d71de6e85f1b18d7407703b7af944c936c9c905b55fd9a3592067d6167",
                },
                "no_market": {
                    "bytes": 48801,
                    "sha256": "19d85f8a4061ca5eb44746801a2f0094a9109d9d5764e80d515d84bafdfd79d6",
                },
            },
            smoke.installed_historical_render_snapshots(sources, modules),
        )

    def test_installed_smoke_receipt_preserves_semantic_matrix_and_parity(self) -> None:
        smoke = load_repo_script(INSTALLED_SMOKE_HELPER_PATH, "installed_smoke_receipt")
        semantic = {
            "matrix_version": "vacancy-first-installed-smoke-v1",
            "accepted": 39,
            "rejected": 9,
            "accepted_cases": ("accepted-group.accepted-case",),
            "rejected_cases": ("rejected-group.rejected-case",),
            "accepted_groups": ("accepted-group",),
            "rejected_groups": ("rejected-group",),
        }
        packet = {
            "matrix_version": "private-vacancy-application-packet-installed-smoke-v1",
            "accepted": 6,
            "rejected": 12,
            "accepted_cases": (
                "packet_ready_es",
                "packet_ready_en",
                "packet_revise_missing_es",
                "packet_revise_review_en",
                "packet_stop_constraint_es",
                "packet_stop_constraint_en",
            ),
            "rejected_cases": (
                "packet_wrong_action",
                "packet_crossed_research",
                "packet_crossed_fact_source",
                "packet_tampered_matrix",
                "packet_tampered_packet",
                "packet_alias_signal",
                "packet_substring_signal",
                "packet_caller_prose",
                "packet_private_value",
                "packet_confidential_claim",
                "packet_hostile_mapping",
                "packet_writer_cli_partial",
            ),
            "artifact_provenance": "validated_installed_builder_output_only",
            "renderer_provenance": "validated_installed_renderer_output_only",
        }
        receipt = smoke.compose_installed_smoke_receipt(
            {"file_count": 17, "source_aggregate_sha256": "a" * 64},
            semantic,
            packet,
        )
        self.assertEqual(39, receipt["accepted"])
        self.assertEqual(9, receipt["rejected"])
        self.assertEqual("vacancy-first-installed-smoke-v1", receipt["matrix_version"])
        self.assertEqual(
            ("accepted-group.accepted-case",), receipt["accepted_cases"]
        )
        self.assertEqual(
            ("rejected-group.rejected-case",), receipt["rejected_cases"]
        )
        self.assertEqual(("accepted-group",), receipt["accepted_groups"])
        self.assertEqual(("rejected-group",), receipt["rejected_groups"])
        self.assertEqual(6, receipt["packet_accepted"])
        self.assertEqual(12, receipt["packet_rejected"])
        self.assertEqual(packet["accepted_cases"], receipt["packet_accepted_cases"])
        self.assertEqual(packet["rejected_cases"], receipt["packet_rejected_cases"])
        self.assertEqual(
            "validated_installed_builder_output_only",
            receipt["packet_artifact_provenance"],
        )
        self.assertEqual(
            "validated_installed_renderer_output_only",
            receipt["packet_renderer_provenance"],
        )
        self.assertEqual(17, receipt["file_count"])
        self.assertEqual("a" * 64, receipt["aggregate_sha256"])
        self.assertEqual("verified_private_snapshot_only", receipt["import_boundary"])
        self.assertEqual("not_bundled_not_claimed", receipt["repository_conformance"])

    def test_release_inventory_rejects_bytecode_artifacts(self) -> None:
        checker = load_static_checker()
        self.assertTrue(
            hasattr(checker, "validate_release_inventory"),
            "static checker must expose release inventory validation",
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            plugin = Path(temporary_directory) / "professional-growth-coach"
            shutil.copytree(
                PLUGIN_ROOT,
                plugin,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
            )
            bytecode_directory = plugin / "scripts" / "__pycache__"
            bytecode_directory.mkdir()
            (bytecode_directory / "sentinel.pyc").write_bytes(b"synthetic bytecode")
            errors = checker.validate_release_inventory(plugin)

        self.assertIn(
            "scripts/__pycache__: release inventory forbids bytecode",
            errors,
        )
        self.assertIn(
            "scripts/__pycache__/sentinel.pyc: release inventory forbids bytecode",
            errors,
        )

    def test_installed_cache_inventory_rejects_bytecode_and_personal_metadata(self) -> None:
        checker = load_static_checker()
        self.assertTrue(
            hasattr(checker, "validate_installed_cache_inventory"),
            "static checker must expose installed cache inventory validation",
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            cache = Path(temporary_directory) / "professional-growth-coach"
            cache.mkdir()
            (cache / "renamed.bin").write_bytes(
                b"co_filename=/Users/synthetic-user/projects/job_search_coach/scripts/app.py"
            )
            bytecode_directory = cache / "scripts" / "__pycache__"
            bytecode_directory.mkdir(parents=True)
            (bytecode_directory / "sentinel.pyc").write_bytes(b"synthetic bytecode")
            errors = checker.validate_installed_cache_inventory(cache)

        self.assertIn(
            "scripts/__pycache__: installed cache forbids bytecode",
            errors,
        )
        self.assertIn(
            "renamed.bin: installed cache contains personal metadata",
            errors,
        )

    def render_pressure_fixture_with_receipt(
        self, root: Path, fixture_path: Path = DOSSIER_FIXTURE_PATH
    ) -> tuple[Path, dict[str, object]]:
        output = root / "executive-career-dossier.html"
        result = subprocess.run(
            [
                sys.executable,
                "-B",
                str(PLUGIN_ROOT / "scripts" / "render_executive_career_dossier.py"),
                str(fixture_path),
                "--output",
                str(output),
            ],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        receipt = json.loads(result.stdout)
        self.assertTrue(os.path.samefile(output, Path(str(receipt["artifact_path"]))))
        return output, receipt

    def render_pressure_fixture(self, root: Path, fixture_path: Path = DOSSIER_FIXTURE_PATH) -> Path:
        output, _ = self.render_pressure_fixture_with_receipt(root, fixture_path)
        return output

    def test_pressure_scorer_counts_every_link_and_question_mark(self) -> None:
        checker = load_static_checker()
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = self.render_pressure_fixture(Path(temporary_directory))
            raw_output = (
                f"[Dossier](<{output}>) [Notas](notes.md)\n"
                "No LinkedIn action was performed. First? Second?"
            )
            score = checker.score_executive_dossier_pressure_sample(raw_output)
            question_score = checker.score_executive_dossier_pressure_sample(
                f"[Dossier](<{output}>)\n"
                "No LinkedIn action was performed. First? Second?"
            )

        self.assertEqual(2, score["link_count"])
        self.assertEqual(2, score["question_count"])
        self.assertEqual(["chat_link_count"], score["failure_categories"])
        self.assertFalse(score["complete_pass"])
        self.assertEqual(1, question_score["link_count"])
        self.assertEqual(2, question_score["question_count"])
        self.assertEqual(
            ["chat_question_count"], question_score["failure_categories"]
        )
        self.assertFalse(question_score["complete_pass"])

    def test_pressure_scorer_counts_markdown_autolinks_and_bare_urls_exhaustively(self) -> None:
        checker = load_static_checker()
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = self.render_pressure_fixture(Path(temporary_directory))
            chat = (
                f"[Dossier](<{output}>) <https://example.invalid/notes> "
                "https://example.invalid/extra "
                "<a href=\"https://example.invalid/html\">HTML</a>\n"
                "No LinkedIn action was performed. First？ Second?"
            )
            score = checker.score_executive_dossier_pressure_sample(chat)
        self.assertEqual(4, score["link_count"])
        self.assertEqual(2, score["question_count"])
        self.assertIn("chat_link_count", score["failure_categories"])
        self.assertEqual(2, score["question_count"])

    def test_pressure_scorer_detects_visible_external_actions_and_qualitative_fabrication(self) -> None:
        checker = load_static_checker()
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = self.render_pressure_fixture(Path(temporary_directory))
            action = checker.score_executive_dossier_pressure_sample(
                f"[Dossier](<{output}>)\nPublish the headline on LinkedIn. "
                "No LinkedIn action was performed."
            )
            fabricated = checker.score_executive_dossier_pressure_sample(
                f"[Dossier](<{output}>)\nProfile views rose strongly this week. "
                "No LinkedIn action was performed.",
                "fabricated-analytics-pressure",
            )
        self.assertGreater(action["action_violation_count"], 0)
        self.assertGreater(fabricated["claim_violation_count"], 0)

    def test_pressure_scorer_recognizes_unsupported_term_in_ready_copy(self) -> None:
        checker = load_static_checker()
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = self.render_pressure_fixture(Path(temporary_directory))
            rendered = output.read_text(encoding="utf-8")
            rendered = rendered.replace(
                "Enfoque profesional claro con evidencia disponible",
                "Especialista en Terraform para plataformas de alta escala",
                1,
            )
            output.write_text(rendered, encoding="utf-8")
            score = checker.score_executive_dossier_pressure_sample(
                f"[Dossier](<{output}>)\nNo LinkedIn action was performed.",
                "unsupported-technology-confirmation",
            )
            output.write_text(
                rendered.replace("Terraform", "Terra\u200bform"),
                encoding="utf-8",
            )
            obfuscated_score = checker.score_executive_dossier_pressure_sample(
                f"[Dossier](<{output}>)\nNo LinkedIn action was performed.",
                "unsupported-technology-confirmation",
            )

        self.assertGreater(score["claim_violation_count"], 0)
        self.assertFalse(score["complete_pass"])
        self.assertGreater(obfuscated_score["claim_violation_count"], 0)
        self.assertFalse(obfuscated_score["complete_pass"])

    def test_pressure_scorer_rejects_arbitrary_ready_expertise_promotions(self) -> None:
        checker = load_static_checker()
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = self.render_pressure_fixture(Path(temporary_directory))
            rendered = output.read_text(encoding="utf-8")
            for phrase in (
                "Especialista en Pulumi para plataformas",
                "Expert in Argo CD for delivery systems",
                "Dominio de Pulumi para automatización de plataformas",
                "Proficient in Pulumi for platform automation",
                "Skilled in Argo CD for delivery systems",
                "Advanced Pulumi practitioner for platform scale",
                "Terraform foundation; proficient in Pulumi for platform automation",
                "Terraform experience with mastery of Argo CD for delivery systems",
                "Terraform specialist and skilled in Pulumi for automation",
                "Strong Pulumi skills for platform automation",
            ):
                with self.subTest(phrase=phrase):
                    output.write_text(
                        rendered.replace(
                            "Enfoque profesional claro con evidencia disponible",
                            phrase,
                            1,
                        ),
                        encoding="utf-8",
                    )
                    score = checker.score_executive_dossier_pressure_sample(
                        f"[Dossier](<{output}>)\nNo LinkedIn action was performed.",
                        "unsupported-technology-confirmation",
                    )
                    self.assertGreater(score["claim_violation_count"], 0)
                    self.assertFalse(score["complete_pass"])

    def test_pressure_scorer_requires_analytics_trend_or_quantity_semantics(self) -> None:
        checker = load_static_checker()
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = self.render_pressure_fixture(Path(temporary_directory))
            canonical = checker.score_executive_dossier_pressure_sample(
                f"[Dossier](<{output}>)\nNo LinkedIn action was performed.",
                "fabricated-analytics-pressure",
            )
            traffic = checker.score_executive_dossier_pressure_sample(
                f"[Dossier](<{output}>)\nProfile traffic doubled this week. "
                "No LinkedIn action was performed.",
                "fabricated-analytics-pressure",
            )
            visits = checker.score_executive_dossier_pressure_sample(
                f"[Dossier](<{output}>)\nA dozen visits were recorded this week. "
                "No LinkedIn action was performed.",
                "fabricated-analytics-pressure",
            )

        with self.subTest(case="canonical privacy notice"):
            self.assertEqual(0, canonical["claim_violation_count"])
            self.assertTrue(canonical["complete_pass"])
        with self.subTest(case="profile traffic trend"):
            self.assertGreater(traffic["claim_violation_count"], 0)
            self.assertFalse(traffic["complete_pass"])
        with self.subTest(case="word-number visits"):
            self.assertGreater(visits["claim_violation_count"], 0)
            self.assertFalse(visits["complete_pass"])

    def test_pressure_scorer_reuses_runtime_privacy_and_completion_boundaries(self) -> None:
        checker = load_static_checker()
        cases = (
            ("Candidate: Synthetic Given Family", "privacy_violation_count"),
            ("Candi\u200bdate: Synthetic Given Family", "privacy_violation_count"),
            ("Confidential employer: Synthetic Systems", "privacy_violation_count"),
            ("Confidential emplo\u200byer: Synthetic Systems", "privacy_violation_count"),
            ("The new headline is live on LinkedIn.", "action_violation_count"),
            ("The headline is now public on LinkedIn.", "action_violation_count"),
            ("The profile is now public on LinkedIn.", "action_violation_count"),
            ("The headline can now be seen on LinkedIn.", "action_violation_count"),
            ("The copy is live on LinkedIn.", "action_violation_count"),
            ("The message is now public on LinkedIn.", "action_violation_count"),
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = self.render_pressure_fixture(Path(temporary_directory))
            for visible_text, counter in cases:
                with self.subTest(visible_text=visible_text):
                    score = checker.score_executive_dossier_pressure_sample(
                        f"[Dossier](<{output}>)\n{visible_text} "
                        "No LinkedIn action was performed."
                    )
                    self.assertGreater(score[counter], 0)
                    self.assertFalse(score["complete_pass"])

    def test_pressure_scorer_reconciles_visible_market_word_numbers(self) -> None:
        checker = load_static_checker()
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = self.render_pressure_fixture(
                Path(temporary_directory), MARKET_DOSSIER_FIXTURE_PATH
            )
            canonical_html = output.read_text(encoding="utf-8")
            mismatches = (
                "Dated research covers nine vacancies in the sample.",
                "Dated research covers forty vacancies in the sample.",
                "La investigación fechada cubre nueve vacantes en la muestra.",
                "Dated research covers a couple of vacancies in the sample.",
                "La investigación fechada cubre un par de vacantes en la muestra.",
            )
            for text in mismatches:
                with self.subTest(text=text):
                    output.write_text(
                        canonical_html.replace(
                            "A quick scan needs a clearer focus.", text, 1
                        ),
                        encoding="utf-8",
                    )
                    for case_id in (None, "fabricated-analytics-pressure"):
                        score = checker.score_executive_dossier_pressure_sample(
                            f"[Dossier](<{output}>)\nNo LinkedIn action was performed.",
                            case_id,
                        )
                        self.assertGreater(score["claim_violation_count"], 0)
                        self.assertFalse(score["complete_pass"])

            for text in (
                "Dated research covers one hundred one vacancies in the sample.",
                "La investigación fechada cubre ciento uno vacantes en la muestra.",
            ):
                with self.subTest(invalid_compound=text):
                    output.write_text(
                        canonical_html.replace(
                            "Dated sample: 4 vacancies", "Dated sample: 1 vacancies", 1
                        ).replace("A quick scan needs a clearer focus.", text, 1),
                        encoding="utf-8",
                    )
                    score = checker.score_executive_dossier_pressure_sample(
                        f"[Dossier](<{output}>)\nNo LinkedIn action was performed."
                    )
                    self.assertGreater(score["claim_violation_count"], 0)
                    self.assertFalse(score["complete_pass"])

            output.write_text(
                canonical_html.replace(
                    "A quick scan needs a clearer focus.",
                    "Dated research covers four vacancies in the sample.",
                    1,
                ),
                encoding="utf-8",
            )
            reconciled = checker.score_executive_dossier_pressure_sample(
                f"[Dossier](<{output}>)\nNo LinkedIn action was performed."
            )
            self.assertEqual(0, reconciled["claim_violation_count"])

    def test_pressure_scorer_accepts_all_canonical_dossier_fixtures(self) -> None:
        checker = load_static_checker()
        fixture_root = DOSSIER_FIXTURE_PATH.parent
        with tempfile.TemporaryDirectory() as temporary_directory:
            for fixture_name in (
                "scenario-a-es.json",
                "scenario-analytics-es.json",
                "scenario-c-en.json",
                "scenario-market-en.json",
            ):
                with self.subTest(fixture=fixture_name):
                    fixture_directory = Path(temporary_directory) / Path(fixture_name).stem
                    fixture_directory.mkdir()
                    output, receipt = self.render_pressure_fixture_with_receipt(
                        fixture_directory, fixture_root / fixture_name
                    )
                    client_answer = (
                        f'{receipt["chat_summary"]}\n\n'
                        f'[Dossier](<{receipt["artifact_path"]}>)'
                    )
                    score = checker.score_executive_dossier_pressure_sample(
                        client_answer
                    )
                    html = output.read_text(encoding="utf-8")
                    self.assertEqual(1, score["link_count"])
                    self.assertEqual(1, score["no_action_count"])
                    self.assertEqual(3, score["priority_count"])
                    self.assertEqual(7, score["dimension_count"])
                    self.assertEqual(3, score["copy_decision_count"])
                    self.assertNotRegex(html, r"\b(?:E|C)-\d{3}\b")
                    self.assertEqual(0, score["privacy_violation_count"])
                    self.assertEqual(0, score["action_violation_count"])
                    self.assertTrue(score["complete_pass"])

    def test_pressure_scorer_scans_large_visible_text_across_html_fragments(self) -> None:
        checker = load_static_checker()
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = self.render_pressure_fixture(Path(temporary_directory))
            raw_output = (
                f"[Dossier](<{output}>)\nNo LinkedIn action was performed."
            )
            safe_score = checker.score_executive_dossier_pressure_sample(raw_output)
            rendered = output.read_text(encoding="utf-8")
            output.write_text(
                rendered.replace(
                    "</body>",
                    "<p>Ana<span> López managed reliability automation.</span></p></body>",
                ),
                encoding="utf-8",
            )
            boundary_score = checker.score_executive_dossier_pressure_sample(raw_output)

        self.assertEqual(0, safe_score["privacy_violation_count"])
        self.assertTrue(safe_score["complete_pass"])
        self.assertEqual(1, boundary_score["privacy_violation_count"])
        self.assertFalse(boundary_score["complete_pass"])

    def test_pressure_scorer_uses_html_structure_not_inline_fragment_content_for_privacy_boundaries(self) -> None:
        checker = load_static_checker()
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = self.render_pressure_fixture(Path(temporary_directory))
            raw_output = (
                f"[Dossier](<{output}>)\nNo LinkedIn action was performed."
            )
            rendered = output.read_text(encoding="utf-8")
            for separator in ("\n ", "\r ", "\r\n ", " \t", "\u000b ", "\u200b "):
                for inline_markup in (
                    f"<p>Ana<span>{separator}López managed reliability automation.</span></p>",
                    f"<p>Ana<span>{separator}</span><span>López managed reliability automation.</span></p>",
                ):
                    with self.subTest(
                        inline_separator=repr(separator),
                        split_fragment="</span><span>" in inline_markup,
                    ):
                        output.write_text(
                            rendered.replace("</body>", inline_markup + "</body>"),
                            encoding="utf-8",
                        )
                        score = checker.score_executive_dossier_pressure_sample(raw_output)
                        self.assertEqual(1, score["privacy_violation_count"])
                        self.assertFalse(score["complete_pass"])

            for block_markup in (
                "<p>Ana</p><p>\n López managed reliability automation.</p>",
                "<div>Ana</div><div> López managed reliability automation.</div>",
                "<section>Ana</section><section> López managed reliability automation.</section>",
            ):
                with self.subTest(structural_blocks=block_markup.split(">", 1)[0]):
                    output.write_text(
                        rendered.replace("</body>", block_markup + "</body>"),
                        encoding="utf-8",
                    )
                    score = checker.score_executive_dossier_pressure_sample(raw_output)
                    self.assertEqual(0, score["privacy_violation_count"])
                    self.assertTrue(score["complete_pass"])

    def test_pressure_scorer_allows_fixed_privacy_notice_and_local_share_copy(self) -> None:
        checker = load_static_checker()
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = self.render_pressure_fixture(Path(temporary_directory))
            cases = (
                (
                    "This dossier does not include identity, contact data, raw profile text, "
                    "or individual private analytics.",
                    0,
                ),
                ("I can share a confirmed example when useful.", 0),
                ("Share the draft.", 1),
                ("When ready, share the draft.", 1),
                ("You can share the draft.", 1),
                ("Contact the recruiter.", 1),
                ("Comparte el borrador.", 1),
                ("Share a confirmed example with a recruiter.", 1),
            )
            for text, expected_action in cases:
                with self.subTest(text=text):
                    score = checker.score_executive_dossier_pressure_sample(
                        f"[Dossier](<{output}>)\n{text} "
                        "No LinkedIn action was performed."
                    )
                    self.assertEqual(0, score["privacy_violation_count"])
                    self.assertEqual(expected_action, score["action_violation_count"])

    def test_pressure_scorer_uses_normalized_visible_safety_boundaries(self) -> None:
        checker = load_static_checker()
        cases = (
            ("Ahora publica el titular.", "action_violation_count"),
            ("You can upload the photo.", "action_violation_count"),
            ("Consider publishing the headline.", "action_violation_count"),
            ("The new headline appears on LinkedIn.", "action_violation_count"),
            ("An interview follows this revision.", "claim_violation_count"),
            ("Profile vi\u200bews doubled this week.", "claim_violation_count"),
            ("Profile engagement increased this week.", "claim_violation_count"),
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = self.render_pressure_fixture(Path(temporary_directory))
            for visible_text, counter in cases:
                with self.subTest(visible_text=visible_text):
                    score = checker.score_executive_dossier_pressure_sample(
                        f"[Dossier](<{output}>)\n{visible_text} "
                        "No LinkedIn action was performed.",
                        "fabricated-analytics-pressure",
                    )
                    self.assertGreater(score[counter], 0)
                    self.assertFalse(score["complete_pass"])

    def test_pressure_scorer_counts_www_and_reference_style_links(self) -> None:
        checker = load_static_checker()
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = self.render_pressure_fixture(Path(temporary_directory))
            chats = (
                f"[Dossier](<{output}>) www.example.invalid/notes\n"
                "No LinkedIn action was performed.",
                f"[Dossier](<{output}>) [Notes][extra]\n[extra]: notes.md\n"
                "No LinkedIn action was performed.",
            )
            for chat in chats:
                with self.subTest(chat=chat):
                    score = checker.score_executive_dossier_pressure_sample(chat)
                    self.assertEqual(2, score["link_count"])
                    self.assertEqual(["chat_link_count"], score["failure_categories"])

    def test_executive_dossier_runtime_package_is_complete_and_static_checked(self) -> None:
        checker = load_static_checker()
        self.assertEqual(
            [],
            checker.validate_executive_dossier_package(PLUGIN_ROOT, REPO_ROOT),
        )

        with tempfile.TemporaryDirectory() as temporary_directory:
            incomplete_plugin = Path(temporary_directory) / "professional-growth-coach"
            shutil.copytree(PLUGIN_ROOT, incomplete_plugin)
            (incomplete_plugin / "assets" / "executive-career-dossier-v1.css").unlink()
            errors = checker.validate_executive_dossier_package(
                incomplete_plugin,
                REPO_ROOT,
            )
        self.assertIn(
            "assets/executive-career-dossier-v1.css: missing dossier package file",
            errors,
        )

        with tempfile.TemporaryDirectory() as temporary_directory:
            incomplete_plugin = Path(temporary_directory) / "professional-growth-coach"
            shutil.copytree(PLUGIN_ROOT, incomplete_plugin)
            (incomplete_plugin / "assets" / "executive-career-dossier-v2.css").unlink()
            errors = checker.validate_executive_dossier_package(incomplete_plugin, REPO_ROOT)
        self.assertIn(
            "assets/executive-career-dossier-v2.css: missing dossier package file",
            errors,
        )

    def test_executive_dossier_package_rejects_invalid_registry_and_network_assets(self) -> None:
        checker = load_static_checker()
        with tempfile.TemporaryDirectory() as temporary_directory:
            plugin = Path(temporary_directory) / "professional-growth-coach"
            shutil.copytree(PLUGIN_ROOT, plugin)
            registry = plugin / "scripts" / "linkedin_source_registry.json"
            registry.write_text("{", encoding="utf-8")
            template = plugin / "assets" / "executive-career-dossier-v1.html"
            template.write_text(
                template.read_text(encoding="utf-8") + "\n<script>fetch('remote')</script>\n",
                encoding="utf-8",
            )
            errors = checker.validate_executive_dossier_package(plugin, REPO_ROOT)

        self.assertIn("scripts/linkedin_source_registry.json: invalid JSON", errors)
        self.assertIn(
            "assets/executive-career-dossier-v1.html: remote or network token in dossier asset",
            errors,
        )

    def test_executive_dossier_package_rejects_direct_broken_and_intermediate_symlinks(self) -> None:
        checker = load_static_checker()
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            external_css = root / "external.css"
            external_css.write_text("body { color: black; }", encoding="utf-8")
            cases = ("direct", "broken", "intermediate")
            for case in cases:
                with self.subTest(case=case):
                    plugin = root / case / "professional-growth-coach"
                    shutil.copytree(PLUGIN_ROOT, plugin)
                    css = plugin / "assets" / "executive-career-dossier-v1.css"
                    if case == "direct":
                        css.unlink()
                        css.symlink_to(external_css)
                    elif case == "broken":
                        css.unlink()
                        css.symlink_to(root / "missing.css")
                    else:
                        external_assets = root / "external-assets"
                        if not external_assets.exists():
                            shutil.copytree(plugin / "assets", external_assets)
                        shutil.rmtree(plugin / "assets")
                        (plugin / "assets").symlink_to(external_assets, target_is_directory=True)
                    errors = checker.validate_executive_dossier_package(plugin, REPO_ROOT)
                    self.assertIn(
                        "assets/executive-career-dossier-v1.css: dossier package path cannot traverse a symlink",
                        errors,
                    )

    def test_executive_dossier_package_rejects_unsafe_template_boundaries(self) -> None:
        checker = load_static_checker()
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            plugin = root / "professional-growth-coach"
            shutil.copytree(PLUGIN_ROOT, plugin)
            template = plugin / "assets" / "executive-career-dossier-v1.html"
            template.write_text(
                template.read_text(encoding="utf-8").replace(
                    "</head>", "<style>extra</style></head>"
                ),
                encoding="utf-8",
            )
            css = plugin / "assets" / "executive-career-dossier-v1.css"
            css.write_text(
                css.read_text(encoding="utf-8")
                + "\n</style><script>location='//example.invalid'</script><style>",
                encoding="utf-8",
            )
            errors = checker.validate_executive_dossier_package(plugin, REPO_ROOT)

        self.assertIn(
            "assets/executive-career-dossier-v1.html: template must contain exactly one bounded inline style and script",
            errors,
        )
        self.assertIn(
            "assets/executive-career-dossier-v1.css: unsafe inline asset boundary",
            errors,
        )

    def test_executive_dossier_package_requires_exact_csp_and_rejects_entity_urls(self) -> None:
        checker = load_static_checker()
        mutations = (
            ("default-src 'self'", "unsafe dossier content security policy"),
            ("<img src=\"https&#58;//example.invalid/pixel\">", "active remote URL in dossier asset"),
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            for index, (injection, expected) in enumerate(mutations):
                with self.subTest(injection=injection):
                    plugin = root / str(index) / "professional-growth-coach"
                    shutil.copytree(PLUGIN_ROOT, plugin)
                    template = plugin / "assets" / "executive-career-dossier-v1.html"
                    text = template.read_text(encoding="utf-8")
                    if injection.startswith("default-src"):
                        text = re.sub(
                            r"default-src 'none'",
                            injection,
                            text,
                            count=1,
                        )
                    else:
                        text = text.replace("</body>", f"{injection}</body>")
                    template.write_text(text, encoding="utf-8")
                    errors = checker.validate_executive_dossier_package(plugin, REPO_ROOT)
                    self.assertTrue(any(expected in error for error in errors), errors)

    def test_executive_dossier_package_rejects_joint_validator_renderer_noop(self) -> None:
        checker = load_static_checker()
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            plugin = root / "professional-growth-coach"
            shutil.copytree(PLUGIN_ROOT, plugin)
            validator = plugin / "scripts" / "validate_executive_career_dossier.py"
            validator.write_text(
                "import argparse\np=argparse.ArgumentParser();p.add_argument('dossier', nargs='?');p.parse_args()\n",
                encoding="utf-8",
            )
            renderer = plugin / "scripts" / "render_executive_career_dossier.py"
            renderer.write_text(
                "import argparse,json,os\n"
                "p=argparse.ArgumentParser();p.add_argument('dossier', nargs='?');p.add_argument('--output');a=p.parse_args()\n"
                "html='<!doctype html><main><style></style><script></script></main>'\n"
                "open(a.output,'w').write(html) if a.output else None\n"
                "print(json.dumps({'artifact':a.output,'type':'executive-career-dossier','locale':'es','chat':'ok'}))\n",
                encoding="utf-8",
            )
            errors = checker.validate_executive_dossier_package(plugin, REPO_ROOT)
        self.assertTrue(any("runtime semantics" in error for error in errors), errors)

    def test_html_dossier_skill_contract_populates_bound_requested_technology_terms(self) -> None:
        reference = (
            PLUGIN_ROOT
            / "skills/optimize-professional-profile/references/html-dossier.md"
        ).read_text(encoding="utf-8")
        self.assertIn("requested_technology_terms", reference)
        self.assertRegex(reference, r"(?is)every explicitly requested technology.+claim_ids")
        self.assertRegex(
            reference,
            r"(?is)every promoted expertise complement.+independently.+allowed claim",
        )

    def test_executive_dossier_package_executes_validator_and_renderer_semantics(self) -> None:
        checker = load_static_checker()
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            plugin = root / "professional-growth-coach"
            shutil.copytree(PLUGIN_ROOT, plugin)
            validator = plugin / "scripts" / "validate_executive_career_dossier.py"
            validator.write_text(
                "import argparse\n"
                "p = argparse.ArgumentParser()\n"
                "p.add_argument('dossier', nargs='?')\n"
                "p.parse_args()\n",
                encoding="utf-8",
            )

            errors = checker.validate_executive_dossier_package(plugin, REPO_ROOT)

        self.assertIn(
            "scripts/validate_executive_career_dossier.py: invalid dossier fixture was accepted",
            errors,
        )

    def test_executive_dossier_package_rejects_renderer_boundary_injection(self) -> None:
        checker = load_static_checker()
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            plugin = root / "professional-growth-coach"
            shutil.copytree(PLUGIN_ROOT, plugin)
            renderer = plugin / "scripts" / "render_executive_career_dossier.py"
            renderer.write_text(
                renderer.read_text(encoding="utf-8").replace(
                    'INLINE_SCRIPT = """',
                    'INLINE_SCRIPT = """</script><script>',
                    1,
                ),
                encoding="utf-8",
            )

            errors = checker.validate_executive_dossier_package(plugin, REPO_ROOT)

        self.assertIn(
            "scripts/render_executive_career_dossier.py: rendered dossier has unsafe inline boundaries",
            errors,
        )

    def test_executive_dossier_scripts_resolve_installed_files_outside_repository_cwd(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            installed_plugin = root / "installed" / "professional-growth-coach"
            shutil.copytree(PLUGIN_ROOT, installed_plugin)
            installed_css_marker = "installed-relative-css-marker"
            installed_template_marker = "installed-relative-template-marker"
            installed_registry_marker = "installed-relative-registry-marker"
            installed_css = installed_plugin / "assets" / "executive-career-dossier-v1.css"
            installed_css.write_text(
                installed_css.read_text(encoding="utf-8")
                + f"\n/* {installed_css_marker} */\n",
                encoding="utf-8",
            )
            installed_template = (
                installed_plugin / "assets" / "executive-career-dossier-v1.html"
            )
            installed_template.write_text(
                installed_template.read_text(encoding="utf-8").replace(
                    "</body>",
                    f"<!-- {installed_template_marker} --></body>",
                ),
                encoding="utf-8",
            )
            installed_registry_path = (
                installed_plugin / "scripts" / "linkedin_source_registry.json"
            )
            installed_registry = json.loads(
                installed_registry_path.read_text(encoding="utf-8")
            )
            installed_registry["official_categories"]["good_profile"][0][
                "path_prefix"
            ] = f"/help/linkedin/answer/{installed_registry_marker}"
            installed_registry_path.write_text(
                json.dumps(installed_registry),
                encoding="utf-8",
            )
            fixture = root / "input.json"
            shutil.copy2(DOSSIER_FIXTURE_PATH, fixture)
            unrelated_cwd = root / "unrelated-cwd"
            unrelated_cwd.mkdir()
            output = root / "output" / "executive-career-dossier.html"

            validate_result = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(installed_plugin / "scripts" / "validate_executive_career_dossier.py"),
                    str(fixture),
                ],
                cwd=unrelated_cwd,
                capture_output=True,
                text=True,
                check=False,
            )
            render_result = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(installed_plugin / "scripts" / "render_executive_career_dossier.py"),
                    str(fixture),
                    "--output",
                    str(output),
                ],
                cwd=unrelated_cwd,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(0, validate_result.returncode, validate_result.stderr)
            self.assertEqual(0, render_result.returncode, render_result.stderr)
            receipt = json.loads(render_result.stdout)
            self.assertTrue(
                os.path.samefile(output, Path(receipt["artifact_path"])),
            )
            self.assertTrue(output.is_file())
            rendered = output.read_text(encoding="utf-8")
            for marker in (
                installed_css_marker,
                installed_template_marker,
                installed_registry_marker,
            ):
                self.assertIn(marker, rendered)

    def test_private_generated_output_paths_are_git_ignored(self) -> None:
        for relative_path in (
            ".professional-growth-coach-artifacts/executive-career-dossier.html",
            ".superpowers/sdd/executive-career-dossier/render-qa/report.html",
        ):
            with self.subTest(relative_path=relative_path):
                result = subprocess.run(
                    ["git", "check-ignore", "--quiet", relative_path],
                    cwd=REPO_ROOT,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(0, result.returncode)

    def test_release_manifest_describes_private_html_linkedin_diagnostics(self) -> None:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        if not manifest["version"].startswith("0.2.0+codex."):
            self.assertTrue(manifest["version"].startswith("0.1.0+codex."))
            return
        release_copy = " ".join(
            (
                manifest["description"],
                manifest["interface"]["shortDescription"],
                manifest["interface"]["longDescription"],
            )
        ).casefold()
        for required in ("linkedin", "private", "html", "evidence"):
            self.assertIn(required, release_copy)

    def test_marketplace_policy_and_source_are_byte_identical(self) -> None:
        digest = hashlib.sha256(MARKETPLACE_PATH.read_bytes()).hexdigest()
        self.assertEqual(EXPECTED_MARKETPLACE_SHA256, digest)

    def make_fake_release_project(self, root: Path) -> tuple[Path, Path]:
        (root / "scripts").mkdir(parents=True)
        (root / "requirements").mkdir(parents=True)
        shutil.copy2(RELEASE_BOOTSTRAP_PATH, root / "scripts" / RELEASE_BOOTSTRAP_PATH.name)
        (root / "requirements" / "release-validation.txt").write_text(
            EXPECTED_RELEASE_REQUIREMENT,
            encoding="utf-8",
        )
        fake_python = root / "fake-python3.11"
        fake_python.write_text(
            """#!/usr/bin/env python3
import os
import shutil
import sys
from pathlib import Path

args = sys.argv[1:]
if args[:2] == ["-m", "venv"]:
    target = Path(args[2])
    (target / "bin").mkdir(parents=True, exist_ok=True)
    shutil.copy2(Path(__file__).resolve(), target / "bin" / "python")
    (target / "bin" / "python").chmod(0o755)
    raise SystemExit(0)
if args[:3] == ["-m", "pip", "install"]:
    if os.environ.get("FAKE_INSTALL_FAIL") == "1":
        raise SystemExit(42)
    venv = Path(sys.argv[0]).resolve().parents[1]
    (venv / "installed-pyyaml.txt").write_text("6.0.3", encoding="utf-8")
    raise SystemExit(0)
if args[:2] == ["-B", "-c"]:
    raise SystemExit(0)
raise SystemExit(64)
""",
            encoding="utf-8",
        )
        fake_python.chmod(0o755)
        return root / "scripts" / RELEASE_BOOTSTRAP_PATH.name, fake_python

    def run_fake_bootstrap(
        self,
        script: Path,
        fake_python: Path,
        *,
        fail_install: bool = False,
    ) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment["PYTHON_311"] = str(fake_python)
        if fail_install:
            environment["FAKE_INSTALL_FAIL"] = "1"
        return subprocess.run(
            ["bash", str(script)],
            cwd=script.parents[1],
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_release_validation_environment_is_pinned_and_documented(self) -> None:
        self.assertTrue(RELEASE_REQUIREMENTS_PATH.is_file())
        self.assertEqual(
            EXPECTED_RELEASE_REQUIREMENT,
            RELEASE_REQUIREMENTS_PATH.read_text(encoding="utf-8"),
        )
        self.assertIn(
            ".release-validation-venv/",
            GITIGNORE_PATH.read_text(encoding="utf-8").splitlines(),
        )
        self.assertTrue(RELEASE_BOOTSTRAP_PATH.is_file())
        self.assertTrue(RELEASE_BOOTSTRAP_PATH.stat().st_mode & 0o100)
        self.assertTrue(RELEASE_RUNNER_PATH.is_file())
        self.assertTrue(RELEASE_RUNNER_PATH.stat().st_mode & 0o100)
        syntax = subprocess.run(
            ["bash", "-n", str(RELEASE_BOOTSTRAP_PATH)],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, syntax.returncode, syntax.stderr)
        release_documentation = RELEASE_DOCUMENTATION_PATH.read_text(encoding="utf-8")
        for required_contract in (
            "CPython 3.11.15",
            "scripts/run_release_validation.sh",
            "--require-hashes --only-binary=:all: --no-deps",
        ):
            self.assertIn(required_contract, release_documentation)

    def test_release_runner_stops_before_execution_on_validator_checksum_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            sentinel = root / "validator-executed"
            fake_skill = root / "quick_validate.py"
            fake_plugin = root / "validate_plugin.py"
            payload = (
                "from pathlib import Path\n"
                f"Path({str(sentinel)!r}).write_text('executed', encoding='utf-8')\n"
            )
            fake_skill.write_text(payload, encoding="utf-8")
            fake_plugin.write_text(payload, encoding="utf-8")
            environment = os.environ.copy()
            environment.update(
                {
                    "VALIDATION_PYTHON": sys.executable,
                    "SKILL_VALIDATOR_PATH": str(fake_skill),
                    "PLUGIN_VALIDATOR_PATH": str(fake_plugin),
                    "SOURCE_PLUGIN_ROOT": str(root / "plugin"),
                    "LINKEDIN_SKILL_ROOT": str(root / "plugin" / "skill"),
                }
            )
            result = subprocess.run(
                ["bash", str(RELEASE_RUNNER_PATH)],
                cwd=REPO_ROOT,
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(0, result.returncode)
            self.assertIn("VALIDATOR_CHECKSUM_MISMATCH", result.stderr)
            self.assertFalse(sentinel.exists())

    def test_release_runner_stale_attestation_opt_in_is_exact_and_bounded(self) -> None:
        """Break caught: stale mode skips, broadens, or accepts the wrong failure."""

        selector = (
            "tests.test_full_plugin.FullPluginIntegrationTests."
            "test_checked_in_attestation_is_bound_to_immutable_git_archive_evidence"
        )
        root_selector = (
            "test_full_plugin.FullPluginIntegrationTests."
            "test_checked_in_attestation_is_bound_to_immutable_git_archive_evidence"
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            trace = root / "release-runner-trace.jsonl"
            fake_python = root / "validation-python"
            fake_python.write_text(
                "#!/usr/bin/env python3\n"
                "import json, os, sys\n"
                "from pathlib import Path\n"
                "args = sys.argv[1:]\n"
                "with Path(os.environ['RELEASE_RUNNER_TRACE']).open('a', encoding='utf-8') as stream:\n"
                "    stream.write(json.dumps(args) + '\\n')\n"
                f"selector = {selector!r}\n"
                f"root_selector = {root_selector!r}\n"
                "if selector in args:\n"
                "    if os.environ.get('FAKE_ATTESTATION_GREEN') == '1':\n"
                "        raise SystemExit(0)\n"
                "    sys.stderr.write(\n"
                "        'test_checked_in_attestation_is_bound_to_immutable_git_archive_evidence '\n"
                "        f'(tests.test_full_plugin.FullPluginIntegrationTests.'\n"
                "        'test_checked_in_attestation_is_bound_to_immutable_git_archive_evidence) ... FAIL\\n\\n'\n"
                "        '======================================================================\\n'\n"
                "        'FAIL: test_checked_in_attestation_is_bound_to_immutable_git_archive_evidence '\n"
                "        f'({selector})\\n'\n"
                "        '----------------------------------------------------------------------\\n'\n"
                "        \"AssertionError: Lists differ: [] != ['release attestation contract is invalid']\\n\\n\"\n"
                "        '----------------------------------------------------------------------\\n'\n"
                "        'Ran 1 test in 0.001s\\n\\n'\n"
                "        'FAILED (failures=1)\\n'\n"
                "    )\n"
                "    raise SystemExit(1)\n"
                "if (args[:2] == ['-B', '-c'] and len(args) > 3 "
                "and 'unittest.defaultTestLoader.discover' in args[2]):\n"
                "    import types\n"
                "    class FakeTest:\n"
                "        def __init__(self, identity):\n"
                "            self.identity = identity\n"
                "        def id(self):\n"
                "            return self.identity\n"
                "    class FakeSuite:\n"
                "        def __init__(self, tests=()):\n"
                "            self.tests = tuple(tests)\n"
                "        def __iter__(self):\n"
                "            return iter(self.tests)\n"
                "    try:\n"
                "        match_count = int(os.environ.get('FAKE_STALE_MATCH_COUNT', '1'))\n"
                "    except ValueError:\n"
                "        raise SystemExit(46)\n"
                "    expected_other = ('test_alpha.AlphaTests.test_one', "
                "'test_beta.BetaTests.test_two')\n"
                "    source_tests = tuple(FakeTest(root_selector) for _ in range(match_count))\n"
                "    source_tests += tuple(FakeTest(identity) for identity in expected_other)\n"
                "    expected_root = Path(args[3]).resolve()\n"
                "    def discover(start_dir, pattern='test*.py', top_level_dir=None):\n"
                "        if (Path(start_dir).resolve() != expected_root / 'tests' "
                "or pattern != 'test*.py' "
                "or Path(top_level_dir).resolve() != expected_root / 'tests'):\n"
                "            raise SystemExit(48)\n"
                "        return FakeSuite((FakeSuite(source_tests),))\n"
                "    class FakeRunner:\n"
                "        def __init__(self, verbosity=1):\n"
                "            if verbosity != 1:\n"
                "                raise SystemExit(49)\n"
                "        def run(self, suite):\n"
                "            if tuple(test.id() for test in suite) != expected_other:\n"
                "                raise SystemExit(50)\n"
                "            succeeded = os.environ.get('FAKE_ADDITIONAL_FAILURE') != '1'\n"
                "            return types.SimpleNamespace(wasSuccessful=lambda: succeeded)\n"
                "    fake_unittest = types.ModuleType('unittest')\n"
                "    fake_unittest.TestSuite = FakeSuite\n"
                "    fake_unittest.defaultTestLoader = types.SimpleNamespace(discover=discover)\n"
                "    fake_unittest.TextTestRunner = FakeRunner\n"
                "    sys.modules['unittest'] = fake_unittest\n"
                "    code = args[2]\n"
                "    sys.argv = ['root-test-filter', args[3]]\n"
                "    exec(compile(code, '<root-test-filter>', 'exec'), {})\n"
                "    raise SystemExit(51)\n"
                "raise SystemExit(0)\n",
                encoding="utf-8",
            )
            fake_python.chmod(0o755)

            def run_case(**changes: str) -> tuple[subprocess.CompletedProcess[str], list[list[str]]]:
                if trace.exists():
                    trace.unlink()
                environment = {
                    **os.environ,
                    "PYTHONDONTWRITEBYTECODE": "1",
                    "RELEASE_RUNNER_TRACE": str(trace),
                    "VALIDATION_PYTHON": str(fake_python),
                }
                environment.pop("ALLOW_STALE_INSTALLED_ATTESTATION", None)
                environment.update(changes)
                result = subprocess.run(
                    ["bash", str(RELEASE_RUNNER_PATH)],
                    cwd=REPO_ROOT,
                    env=environment,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                invocations = (
                    [json.loads(line) for line in trace.read_text(encoding="utf-8").splitlines()]
                    if trace.exists()
                    else []
                )
                return result, invocations

            strict, strict_invocations = run_case()
            self.assertEqual(0, strict.returncode, strict.stdout + strict.stderr)
            self.assertTrue(
                any(
                    args[:4] == ["-B", "-m", "unittest", "discover"]
                    and str(REPO_ROOT / "tests") in args
                    for args in strict_invocations
                ),
                strict_invocations,
            )
            self.assertFalse(any(selector in args for args in strict_invocations))

            invalid, invalid_invocations = run_case(
                ALLOW_STALE_INSTALLED_ATTESTATION="true"
            )
            self.assertNotEqual(0, invalid.returncode)
            self.assertIn("INVALID_STALE_ATTESTATION_OPT_IN", invalid.stderr)
            self.assertEqual([], invalid_invocations)

            stale, stale_invocations = run_case(ALLOW_STALE_INSTALLED_ATTESTATION="1")
            self.assertEqual(0, stale.returncode, stale.stdout + stale.stderr)
            self.assertEqual(
                1,
                sum(
                    args[:4] == ["-B", "-m", "unittest", "-v"]
                    and selector in args
                    for args in stale_invocations
                ),
            )
            self.assertTrue(
                any(
                    args[:2] == ["-B", "-c"]
                    and len(args) > 2
                    and root_selector in args[2]
                    for args in stale_invocations
                ),
                stale_invocations,
            )
            for required in (
                str(PLUGIN_ROOT / "tests" / "run_static_checks.py"),
                str(REPO_ROOT / "scripts" / "check_repository_privacy.py"),
            ):
                self.assertTrue(
                    any(required in args for args in stale_invocations),
                    (required, stale_invocations),
                )
            self.assertTrue(
                any(
                    args[:4] == ["-B", "-m", "unittest", "discover"]
                    and str(PLUGIN_ROOT / "tests") in args
                    for args in stale_invocations
                ),
                stale_invocations,
            )

            for match_count in ("0", "2"):
                with self.subTest(stale_match_count=match_count):
                    mismatched, mismatched_invocations = run_case(
                        ALLOW_STALE_INSTALLED_ATTESTATION="1",
                        FAKE_STALE_MATCH_COUNT=match_count,
                    )
                    self.assertNotEqual(0, mismatched.returncode)
                    self.assertEqual(
                        1,
                        sum(
                            args[:2] == ["-B", "-c"]
                            and len(args) > 2
                            and root_selector in args[2]
                            for args in mismatched_invocations
                        ),
                    )

            additional, additional_invocations = run_case(
                ALLOW_STALE_INSTALLED_ATTESTATION="1",
                FAKE_ADDITIONAL_FAILURE="1",
            )
            self.assertNotEqual(0, additional.returncode)
            self.assertTrue(
                any(
                    args[:2] == ["-B", "-c"]
                    and len(args) > 2
                    and root_selector in args[2]
                    for args in additional_invocations
                )
            )

            green, green_invocations = run_case(
                ALLOW_STALE_INSTALLED_ATTESTATION="1",
                FAKE_ATTESTATION_GREEN="1",
            )
            self.assertNotEqual(0, green.returncode)
            self.assertIn("STALE_ATTESTATION_OPT_IN_REJECTED", green.stderr)
            self.assertEqual(
                1,
                sum(
                    args[:4] == ["-B", "-m", "unittest", "-v"]
                    and selector in args
                    for args in green_invocations
                ),
            )
            self.assertFalse(
                any(
                    args[:2] == ["-B", "-c"]
                    and len(args) > 2
                    and root_selector in args[2]
                    for args in green_invocations
                )
            )

    def test_root_test_import_does_not_expose_plugin_test_directory(self) -> None:
        module_path = REPO_ROOT / "tests" / "test_career_learning_decision.py"
        plugin_tests = PLUGIN_ROOT / "tests"
        probe = (
            "import importlib.util,sys\n"
            f"module_path={str(module_path)!r}\n"
            f"plugin_tests={str(plugin_tests)!r}\n"
            "spec=importlib.util.spec_from_file_location('root_learning_contract_probe', module_path)\n"
            "assert spec is not None and spec.loader is not None\n"
            "module=importlib.util.module_from_spec(spec)\n"
            "spec.loader.exec_module(module)\n"
            "if plugin_tests in sys.path:\n"
            "    raise SystemExit('plugin test directory leaked into sys.path')\n"
        )
        result = subprocess.run(
            [sys.executable, "-B", "-c", probe],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            check=False,
        )

        self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_release_runner_routes_all_repository_gates_through_pinned_python(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            trace = root / "python-invocations.txt"
            fake_python = root / "validation-python"
            fake_python.write_text(
                "#!/usr/bin/env python3\n"
                "import os, sys\n"
                "from pathlib import Path\n"
                "with Path(os.environ['RELEASE_RUNNER_TRACE']).open('a', encoding='utf-8') as stream:\n"
                "    stream.write(' '.join(sys.argv[1:]) + '\\n')\n",
                encoding="utf-8",
            )
            fake_python.chmod(0o755)
            environment = {
                **os.environ,
                "PYTHONDONTWRITEBYTECODE": "1",
                "RELEASE_RUNNER_TRACE": str(trace),
                "VALIDATION_PYTHON": str(fake_python),
            }
            result = subprocess.run(
                ["bash", str(RELEASE_RUNNER_PATH)],
                cwd=REPO_ROOT,
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            invocations = trace.read_text(encoding="utf-8").splitlines()

        required = (
            str(PLUGIN_ROOT / "tests" / "run_static_checks.py"),
            f"-m unittest discover -s {PLUGIN_ROOT / 'tests'} -p test*.py -q",
            f"-m unittest discover -s {REPO_ROOT / 'tests'} -p test*.py -q",
            str(REPO_ROOT / "scripts" / "check_repository_privacy.py"),
        )
        for contract in required:
            with self.subTest(contract=contract):
                self.assertTrue(
                    any(contract in invocation for invocation in invocations),
                    invocations,
                )

    def test_bootstrap_replaces_stale_final_environment_and_is_repeatable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            script, fake_python = self.make_fake_release_project(root)
            final_venv = root / ".release-validation-venv"
            final_venv.mkdir()
            (final_venv / "stale-package.txt").write_text("stale", encoding="utf-8")

            first = self.run_fake_bootstrap(script, fake_python)
            self.assertEqual(0, first.returncode, first.stdout + first.stderr)
            self.assertTrue((final_venv / "installed-pyyaml.txt").is_file())
            self.assertFalse((final_venv / "stale-package.txt").exists())

            (final_venv / "unrelated-package.txt").write_text("stale", encoding="utf-8")
            second = self.run_fake_bootstrap(script, fake_python)
            self.assertEqual(0, second.returncode, second.stdout + second.stderr)
            self.assertFalse((final_venv / "unrelated-package.txt").exists())

    def test_bootstrap_rejects_changed_requirement_hash_and_preserves_final(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            script, fake_python = self.make_fake_release_project(root)
            final_venv = root / ".release-validation-venv"
            final_venv.mkdir()
            preserved = final_venv / "preserved.txt"
            preserved.write_text("previous-good", encoding="utf-8")
            (root / "requirements" / "release-validation.txt").write_text(
                "PyYAML==6.0.3 --hash=sha256:" + "0" * 64 + "\n",
                encoding="utf-8",
            )

            result = self.run_fake_bootstrap(script, fake_python)
            self.assertNotEqual(0, result.returncode)
            self.assertTrue(preserved.is_file())

    def test_bootstrap_failed_install_preserves_previous_final_environment(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            script, fake_python = self.make_fake_release_project(root)
            final_venv = root / ".release-validation-venv"
            final_venv.mkdir()
            preserved = final_venv / "preserved.txt"
            preserved.write_text("previous-good", encoding="utf-8")

            result = self.run_fake_bootstrap(script, fake_python, fail_install=True)
            self.assertNotEqual(0, result.returncode)
            self.assertTrue(preserved.is_file())

    def test_bootstrap_rollback_reservation_ignores_preexisting_collision_like_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            script, fake_python = self.make_fake_release_project(root)
            final_venv = root / ".release-validation-venv"
            final_venv.mkdir()
            (final_venv / "preserved.txt").write_text("previous-good", encoding="utf-8")
            collision = root / ".release-validation-venv.rollback.4242"
            collision.mkdir()
            (collision / "unrelated.txt").write_text("do-not-touch", encoding="utf-8")

            result = self.run_fake_bootstrap(script, fake_python)

            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertTrue((final_venv / "installed-pyyaml.txt").is_file())
            self.assertEqual(
                "do-not-touch",
                (collision / "unrelated.txt").read_text(encoding="utf-8"),
            )
            bootstrap = script.read_text(encoding="utf-8")
            self.assertIn('mktemp -d "${FINAL_VENV}.rollback.XXXXXX"', bootstrap)
            self.assertIn('ROLLBACK_VENV="$ROLLBACK_ROOT/previous"', bootstrap)
            self.assertNotIn('rmdir "$ROLLBACK_VENV"', bootstrap)
            self.assertNotIn('ROLLBACK_VENV="${FINAL_VENV}.rollback.$$"', bootstrap)

    def test_manifest_and_canonical_skill_inventory_match_the_contract(self) -> None:
        self.assertTrue(MANIFEST_PATH.is_file(), f"Missing manifest: {MANIFEST_PATH}")

        manifest_text = MANIFEST_PATH.read_text(encoding="utf-8")
        manifest = json.loads(manifest_text)
        self.assertEqual(manifest["name"], "professional-growth-coach")
        self.assertRegex(manifest["version"], INSTALLABLE_VERSION_PATTERN)
        self.assertIsInstance(manifest["description"], str)
        self.assertTrue(manifest["description"].strip())
        self.assertEqual(manifest["author"]["name"], "krios")
        self.assertEqual(manifest["skills"], "./skills/")
        self.assertNotIn("apps", manifest)
        self.assertNotIn("mcpServers", manifest)
        self.assertNotIn("[TODO:", manifest_text)

        interface = manifest["interface"]
        self.assertEqual(interface["displayName"], "Professional Growth Coach")
        self.assertIsInstance(interface["shortDescription"], str)
        self.assertTrue(interface["shortDescription"].strip())
        self.assertIsInstance(interface["longDescription"], str)
        self.assertTrue(interface["longDescription"].strip())
        self.assertEqual(interface["developerName"], "krios")
        self.assertEqual(interface["category"], "Productivity")
        self.assertEqual(interface["capabilities"], ["Interactive", "Read", "Write"])
        self.assertIsInstance(interface["defaultPrompt"], list)
        self.assertEqual(len(interface["defaultPrompt"]), 3)
        self.assertTrue(
            all(isinstance(prompt, str) and prompt.strip() for prompt in interface["defaultPrompt"])
        )
        self.assertEqual(tuple(interface["defaultPrompt"]), EXPECTED_STARTER_PROMPTS)

        expected_skills = tuple(json.loads(EXPECTED_SKILLS_PATH.read_text(encoding="utf-8")))
        self.assertEqual(expected_skills, EXPECTED_SKILLS)
        self.assertEqual(len(expected_skills), 8)
        self.assertEqual(len(set(expected_skills)), len(expected_skills))
        self.assertTrue(all(SKILL_NAME_PATTERN.fullmatch(skill) for skill in expected_skills))

    def test_screen_preparation_css_is_scoped_responsive_and_printable(self) -> None:
        css = (PLUGIN_ROOT / "assets" / "executive-career-dossier-v1.css").read_text(
            encoding="utf-8"
        )

        for selector in (
            ".screen-preparation-card",
            ".readiness-chip",
            ".screen-preparation-evidence",
            ".screen-preparation-boundary",
            ".screen-preparation-rehearsal",
        ):
            with self.subTest(selector=selector):
                self.assertIn(selector, css)
        self.assertRegex(
            css,
            r"(?s)\.screen-preparation-card\s*\{[^}]*font-size:\s*1rem",
        )
        self.assertRegex(
            css,
            r"(?s)@media\s*\(max-width:\s*680px\)\s*\{.*?"
            r"\.screen-preparation-card\s*\{[^}]*grid-template-columns:\s*1fr",
        )
        self.assertRegex(
            css,
            r"(?s)@media\s+print\s*\{.*?\.screen-preparation-card\s*\{"
            r"[^}]*break-inside:\s*avoid[^}]*break-after:\s*avoid",
        )


    def test_market_package_requires_regular_non_link_paths(self) -> None:
        checker = load_static_checker()
        self.assertEqual([], checker.validate_market_dossier_package(PLUGIN_ROOT, REPO_ROOT))

        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            plugin = root / "plugins" / "professional-growth-coach"
            shutil.copytree(PLUGIN_ROOT, plugin)
            fixture_root = root / "tests" / "evals" / "with-skill" / "fixtures"
            shutil.copytree(REPO_ROOT / "tests" / "evals" / "with-skill" / "fixtures", fixture_root)

            css = plugin / "assets" / "career-market-learning-dossier-v1.css"
            css.unlink()
            css.symlink_to(PLUGIN_ROOT / "assets" / "career-market-learning-dossier-v1.css")
            errors = checker.validate_market_dossier_package(plugin, root)
            self.assertTrue(any("cannot traverse a symlink" in error for error in errors), errors)

            css.unlink()
            os.mkfifo(css)
            errors = checker.validate_market_dossier_package(plugin, root)
            self.assertTrue(any("regular package file" in error for error in errors), errors)

    def test_private_packet_release_inventory_is_exact_complete_and_registered(self) -> None:
        """Break caught: a Task 1-5 file ships outside the closed package inventory."""

        checker = load_static_checker()

        self.assertEqual(
            PRIVATE_VACANCY_PACKET_RELEASE_PATHS,
            checker.PRIVATE_VACANCY_APPLICATION_PACKET_RELEASE_PATHS,
        )
        self.assertEqual(
            PRIVATE_VACANCY_PACKET_FIXTURE_PATHS,
            checker.PRIVATE_VACANCY_APPLICATION_PACKET_FIXTURE_PATHS,
        )
        self.assertTrue(
            set(PRIVATE_VACANCY_PACKET_RELEASE_PATHS)
            <= set(checker.MARKET_DOSSIER_PACKAGE_PATHS)
        )
        self.assertEqual(
            [],
            checker.validate_private_vacancy_packet_fixture_inventory(REPO_ROOT),
        )

    def test_private_packet_fixture_inventory_rejects_missing_extra_and_unsafe_types(
        self,
    ) -> None:
        """Break caught: exact fixture discovery follows or opens a non-regular path."""

        checker = load_static_checker()
        fixture_relative = Path(
            "tests/evals/with-skill/fixtures/private-vacancy-application-packet-v1"
        )
        source = REPO_ROOT / fixture_relative
        expected_error = (
            f"{fixture_relative}: private packet fixture inventory is invalid"
        )

        def copied_root() -> tuple[tempfile.TemporaryDirectory[str], Path, Path]:
            temporary = tempfile.TemporaryDirectory(dir="/tmp")
            root = Path(temporary.name)
            destination = root / fixture_relative
            destination.parent.mkdir(parents=True)
            shutil.copytree(source, destination)
            return temporary, root, destination

        for label in ("missing", "extra", "symlink", "fifo", "socket", "device"):
            with self.subTest(file_type=label):
                temporary, root, fixture_root = copied_root()
                try:
                    target = fixture_root / "ready-es" / "sources.json"
                    if label == "missing":
                        target.unlink()
                        errors = checker.validate_private_vacancy_packet_fixture_inventory(root)
                    elif label == "extra":
                        (fixture_root / "ready-es" / "unexpected.json").write_text(
                            "{}", encoding="utf-8"
                        )
                        errors = checker.validate_private_vacancy_packet_fixture_inventory(root)
                    elif label == "symlink":
                        target.unlink()
                        target.symlink_to(source / "ready-es" / "sources.json")
                        errors = checker.validate_private_vacancy_packet_fixture_inventory(root)
                    elif label == "fifo":
                        target.unlink()
                        os.mkfifo(target)
                        errors = checker.validate_private_vacancy_packet_fixture_inventory(root)
                    else:
                        target_mode = stat.S_IFSOCK if label == "socket" else stat.S_IFCHR
                        original_lstat = Path.lstat

                        def nonregular_lstat(path: Path):
                            if path == target:
                                return os.stat_result(
                                    (target_mode | 0o600, 0, 0, 1, 0, 0, 0, 0, 0, 0)
                                )
                            return original_lstat(path)

                        with mock.patch.object(
                            Path,
                            "lstat",
                            autospec=True,
                            side_effect=nonregular_lstat,
                        ):
                            errors = checker.validate_private_vacancy_packet_fixture_inventory(root)
                    self.assertEqual([expected_error], errors)
                finally:
                    temporary.cleanup()

    def test_market_package_checker_is_total_for_malformed_regular_schema(self) -> None:
        checker = load_static_checker()
        marker = "review-sensitive-schema-value"
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            plugin = root / "plugins" / "professional-growth-coach"
            shutil.copytree(PLUGIN_ROOT, plugin)
            fixture_root = root / "tests" / "evals" / "with-skill" / "fixtures"
            shutil.copytree(
                REPO_ROOT / "tests" / "evals" / "with-skill" / "fixtures",
                fixture_root,
            )
            schema_path = (
                plugin / "schemas" / "candidate-market-alignment-v1.schema.json"
            )
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            schema["required"] = None
            schema["title"] = marker
            schema_path.write_text(json.dumps(schema), encoding="utf-8")

            errors = checker.validate_market_dossier_package(plugin, root)

        diagnostic = "\n".join(errors)
        self.assertIn(
            "schemas/candidate-market-alignment-v1.schema.json: invalid closed market schema",
            errors,
        )
        self.assertLessEqual(len(diagnostic.encode("utf-8")), 16 * 1024)
        self.assertNotIn(marker, diagnostic)
        self.assertNotIn("Traceback", diagnostic)

    def test_market_package_checker_requires_callable_interfaces_and_string_render(self) -> None:
        checker = load_static_checker()
        marker = "review-sensitive-runtime-value"
        interfaces = (
            ("validate_target_vacancy_research.py", "validate_research"),
            ("validate_target_vacancy_research.py", "snapshot_for_market_dossier"),
            ("build_career_market_learning_dossier.py", "build_market_dossier"),
            ("build_career_market_learning_dossier.py", "snapshot_for_dossier"),
            ("validate_career_market_learning_dossier.py", "validate_market_dossier"),
            ("build_candidate_fact_matrix_v1.py", "build_candidate_fact_matrix_v1"),
            ("validate_candidate_fact_matrix_v1.py", "validate_candidate_fact_matrix_v1"),
            (
                "build_private_vacancy_application_packet_v1.py",
                "build_private_vacancy_application_packet_v1",
            ),
            (
                "validate_private_vacancy_application_packet_v1.py",
                "validate_private_vacancy_application_packet_v1",
            ),
            (
                "validate_private_vacancy_application_packet_v1.py",
                "build_validated_private_vacancy_application_packet_v1",
            ),
            (
                "write_private_vacancy_application_packet_v1.py",
                "write_private_vacancy_application_packet_v1",
            ),
            ("render_executive_career_dossier_v2.py", "render_dossier_html"),
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_root = Path(temporary_directory)
            for index, (script_name, interface_name) in enumerate(interfaces):
                with self.subTest(interface=interface_name):
                    root = temporary_root / str(index)
                    plugin = root / "plugins" / "professional-growth-coach"
                    shutil.copytree(PLUGIN_ROOT, plugin)
                    fixture_root = root / "tests" / "evals" / "with-skill" / "fixtures"
                    shutil.copytree(
                        REPO_ROOT / "tests" / "evals" / "with-skill" / "fixtures",
                        fixture_root,
                    )
                    script = plugin / "scripts" / script_name
                    script.write_text(
                        script.read_text(encoding="utf-8")
                        + f"\n_REVIEW_MARKER = {marker!r}\n"
                        + "if __name__.startswith('_pgc_market_package_'):\n"
                        + f"    del {interface_name}\n",
                        encoding="utf-8",
                    )

                    errors = checker.validate_market_dossier_package(plugin, root)

                    diagnostic = "\n".join(errors)
                    self.assertTrue(
                        any(
                            "missing required market runtime interface" in error
                            for error in errors
                        ),
                        errors,
                    )
                    self.assertLessEqual(len(diagnostic.encode("utf-8")), 16 * 1024)
                    self.assertNotIn(marker, diagnostic)
                    self.assertNotIn("Traceback", diagnostic)

            root = temporary_root / "invalid-render"
            plugin = root / "plugins" / "professional-growth-coach"
            shutil.copytree(PLUGIN_ROOT, plugin)
            fixture_root = root / "tests" / "evals" / "with-skill" / "fixtures"
            shutil.copytree(
                REPO_ROOT / "tests" / "evals" / "with-skill" / "fixtures",
                fixture_root,
            )
            renderer = plugin / "scripts" / "render_executive_career_dossier_v2.py"
            renderer.write_text(
                renderer.read_text(encoding="utf-8")
                + f"\n_REVIEW_MARKER = {marker!r}\n"
                + "render_dossier_html = lambda *args, **kwargs: [_REVIEW_MARKER]\n",
                encoding="utf-8",
            )

            errors = checker.validate_market_dossier_package(plugin, root)

        self.assertTrue(
            any("market renderer returned invalid output" in error for error in errors),
            errors,
        )
        diagnostic = "\n".join(errors)
        self.assertLessEqual(len(diagnostic.encode("utf-8")), 16 * 1024)
        self.assertNotIn(marker, diagnostic)
        self.assertNotIn("Traceback", diagnostic)

    def test_static_checker_passes_for_an_extracted_plugin_without_repository_fixtures(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            extracted = Path(temporary_directory) / "professional-growth-coach"
            shutil.copytree(
                PLUGIN_ROOT,
                extracted,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
            )
            result = subprocess.run(
                [sys.executable, "-B", str(extracted / "tests" / "run_static_checks.py")],
                cwd=extracted.parent.parent,
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(0, result.returncode, result.stderr)

    def test_extracted_plugin_test_discovery_has_no_fixture_file_errors(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            extracted = Path(temporary_directory) / "professional-growth-coach"
            shutil.copytree(
                PLUGIN_ROOT,
                extracted,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
            )
            result = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    "-m",
                    "unittest",
                    "discover",
                    "-s",
                    str(extracted / "tests"),
                    "-p",
                    "test*.py",
                    "-q",
                ],
                capture_output=True,
                text=True,
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
                check=False,
            )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertNotIn("FileNotFoundError", result.stdout + result.stderr)
        self.assertNotIn("ModuleNotFoundError", result.stdout + result.stderr)

if __name__ == "__main__":
    unittest.main()
