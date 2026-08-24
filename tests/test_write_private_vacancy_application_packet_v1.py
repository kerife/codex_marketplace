"""Contract tests for the private vacancy-packet JSON writer."""

from __future__ import annotations

import importlib.util
import hashlib
import io
import json
import os
import shutil
import stat
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "plugins" / "professional-growth-coach" / "scripts"
FIXTURE = (
    ROOT
    / "tests"
    / "evals"
    / "with-skill"
    / "fixtures"
    / "private-vacancy-application-packet-v1"
    / "ready-es"
)


def load_script(name: str):
    path = SCRIPTS / name
    specification = importlib.util.spec_from_file_location(
        f"private_vacancy_packet_writer_test_{path.stem}", path
    )
    if specification is None or specification.loader is None:
        raise AssertionError("private vacancy packet writer module is unavailable")
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


def load_independent_script(scripts: Path, name: str, namespace: str):
    path = scripts / name
    specification = importlib.util.spec_from_file_location(
        f"private_vacancy_packet_independent_{namespace}_{path.stem}", path
    )
    if specification is None or specification.loader is None:
        raise AssertionError("independent private vacancy packet module is unavailable")
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


def identity_module_name(scripts: Path) -> str:
    origin = os.path.realpath(scripts / "private_vacancy_packet_identity.py")
    return "_pgc_private_vacancy_packet_identity_" + hashlib.sha256(
        origin.encode("utf-8")
    ).hexdigest()


WRITER = load_script("write_private_vacancy_application_packet_v1.py")


def load_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError("fixture root must be an object")
    return value


class ExplodingPath:
    def __fspath__(self) -> str:
        raise RuntimeError("review-sensitive-path")


class PrivateVacancyApplicationPacketWriterTests(unittest.TestCase):
    """The writer accepts one opaque proof and never leaks failed inputs."""

    def _packet(self) -> dict[str, object]:
        return load_json(FIXTURE / "application-packet.json")

    def _sources(self) -> dict[str, object]:
        return load_json(FIXTURE / "sources.json")

    def _validated(self):
        return WRITER.validate_private_vacancy_application_packet_v1(
            self._packet(), self._sources()
        )

    def _run_cli(self, packet: Path, sources: Path, output: Path, *extra: str):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            result = WRITER._cli(
                [
                    str(packet),
                    "--source-group",
                    str(sources),
                    "--output",
                    str(output),
                    *extra,
                ]
            )
        return result, stdout.getvalue(), stderr.getvalue()

    def _write_inputs(self, directory: Path) -> tuple[Path, Path]:
        packet = directory / "packet-input.json"
        sources = directory / "sources-input.json"
        packet.write_text(json.dumps(self._packet()), encoding="utf-8")
        sources.write_text(json.dumps(self._sources()), encoding="utf-8")
        return packet, sources

    def _assert_failed_without_leak(
        self, result: int, stdout: str, stderr: str, marker: str
    ) -> None:
        self.assertEqual(2, result)
        self.assertEqual("", stdout)
        self.assertEqual("cannot write private vacancy application packet\n", stderr)
        self.assertNotIn(marker, stderr)

    def test_writes_canonical_utf8_with_private_atomic_receipt(self) -> None:
        """Break caught: JSON is not canonical or a successful write is not atomic/private."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            output = directory / "packet.json"
            replace = WRITER.os.replace
            fsync = WRITER.os.fsync
            with patch.object(WRITER.os, "replace", wraps=replace) as replace_spy, patch.object(
                WRITER.os, "fsync", wraps=fsync
            ) as fsync_spy:
                receipt = WRITER.write_private_vacancy_application_packet_v1(
                    self._validated(), output, force=True
                )

            expected = json.dumps(
                self._packet(), ensure_ascii=False, sort_keys=True, separators=(",", ":")
            ).encode("utf-8")
            self.assertEqual(expected, output.read_bytes())
            self.assertNotIn(b"\\u", output.read_bytes())
            self.assertEqual(0o600, stat.S_IMODE(output.stat().st_mode))
            self.assertEqual(output.resolve(), receipt.output_path)
            self.assertEqual("private_vacancy_application_packet", receipt.artifact_type)
            self.assertEqual("private-vacancy-application-packet-v1", receipt.schema_version)
            self.assertTrue(receipt.private_draft)
            self.assertFalse(receipt.external_action_authorized)
            self.assertEqual(1, replace_spy.call_count)
            source_name, destination_name = replace_spy.call_args.args
            self.assertEqual(output.name, destination_name)
            self.assertTrue(source_name.startswith(f".{output.name}.tmp-"))
            self.assertGreaterEqual(fsync_spy.call_count, 2)
            self.assertEqual([], list(directory.glob(f".{output.name}.tmp-*")))

    def test_rejects_nonopaque_writer_input_before_touching_destination(self) -> None:
        """Break caught: an artifact-shaped mapping bypasses the opaque validation proof."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "packet.json"
            output.write_bytes(b"previous-private-bytes")
            for forged in (self._packet(), {"review-sensitive-secret": "forged"}):
                with self.subTest(forged_type=type(forged).__name__):
                    with self.assertRaises(
                        WRITER.PrivateVacancyApplicationPacketWriteError
                    ) as caught:
                        WRITER.write_private_vacancy_application_packet_v1(
                            forged, output, force=True
                        )
                    self.assertEqual(
                        "cannot write private vacancy application packet",
                        str(caught.exception),
                    )
            self.assertEqual(b"previous-private-bytes", output.read_bytes())
            self.assertEqual([], list(output.parent.glob(f".{output.name}.tmp-*")))

    def test_accepts_opaque_snapshot_from_independently_loaded_validator_only(self) -> None:
        """Break caught: a separately imported canonical validator proof fails identity checks."""
        module_names: list[str] = []
        prior_identity_modules: dict[str, object | None] = {}

        def independent_modules(scripts: Path, namespace: str, *, writer_first: bool):
            shared_name = identity_module_name(scripts)
            if shared_name not in prior_identity_modules:
                prior_identity_modules[shared_name] = sys.modules.get(shared_name)
            sys.modules.pop(shared_name, None)
            ordered = (
                ("write_private_vacancy_application_packet_v1.py", "writer"),
                ("validate_private_vacancy_application_packet_v1.py", "validator"),
            )
            if not writer_first:
                ordered = tuple(reversed(ordered))
            modules = {}
            for name, role in ordered:
                module = load_independent_script(scripts, name, f"{namespace}_{role}")
                modules[role] = module
                module_names.append(module.__name__)
            return modules["validator"], modules["writer"]

        try:
            validator_first, writer_after_validator = independent_modules(
                SCRIPTS, "validator_first", writer_first=False
            )
            validator_after_writer, writer_first = independent_modules(
                SCRIPTS, "writer_first", writer_first=True
            )
            with tempfile.TemporaryDirectory() as temporary_directory:
                copied_plugin = Path(temporary_directory) / "professional-growth-coach"
                shutil.copytree(SCRIPTS.parent, copied_plugin)
                copied_validator, copied_writer = independent_modules(
                    copied_plugin / "scripts", "copied_plugin", writer_first=False
                )
                cases = (
                    (validator_first, writer_after_validator, "validator-first.json"),
                    (validator_after_writer, writer_first, "writer-first.json"),
                    (copied_validator, copied_writer, "copied-plugin.json"),
                )
                snapshots = []
                for validator, writer, filename in cases:
                    with self.subTest(filename=filename):
                        snapshot = validator.validate_private_vacancy_application_packet_v1(
                            self._packet(), self._sources()
                        )
                        snapshots.append(snapshot)
                        self.assertIsNot(validator, writer._validator)
                        self.assertIs(
                            validator.ValidatedPrivateVacancyPacket,
                            writer.ValidatedPrivateVacancyPacket,
                        )
                        receipt = writer.write_private_vacancy_application_packet_v1(
                            snapshot, Path(temporary_directory) / filename
                        )
                        self.assertEqual("V-003", receipt.vacancy_id)

                self.assertIsNot(
                    validator_first.ValidatedPrivateVacancyPacket,
                    copied_validator.ValidatedPrivateVacancyPacket,
                )

                with self.assertRaises(
                    writer_after_validator.PrivateVacancyApplicationPacketWriteError
                ):
                    writer_after_validator.write_private_vacancy_application_packet_v1(
                        snapshots[2], Path(temporary_directory) / "cross-package.json"
                    )

                class Spoof(writer_after_validator.ValidatedPrivateVacancyPacket):
                    pass

                spoof = object.__new__(Spoof)
                with self.assertRaises(
                    writer_after_validator.PrivateVacancyApplicationPacketWriteError
                ):
                    writer_after_validator.write_private_vacancy_application_packet_v1(
                        spoof, Path(temporary_directory) / "spoof.json"
                    )
        finally:
            for name in module_names:
                sys.modules.pop(name, None)
            for name, module in prior_identity_modules.items():
                if module is None:
                    sys.modules.pop(name, None)
                else:
                    sys.modules[name] = module

    def test_cli_captures_complete_group_once_and_emits_exact_receipt_after_replace(self) -> None:
        """Break caught: CLI writes before full validation or emits a broadened receipt."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            packet, sources = self._write_inputs(directory)
            output = directory / "packet.json"
            validate = WRITER.validate_private_vacancy_application_packet_v1
            with patch.object(WRITER, "validate_private_vacancy_application_packet_v1", wraps=validate) as spy:
                result, stdout, stderr = self._run_cli(packet, sources, output)

            self.assertEqual(0, result)
            self.assertEqual("", stderr)
            self.assertEqual(1, spy.call_count)
            receipt = json.loads(stdout)
            self.assertEqual(
                [
                    "artifact_type",
                    "schema_version",
                    "locale",
                    "readiness_state",
                    "vacancy_id",
                    "output_path",
                    "private_draft",
                    "external_action_authorized",
                ],
                list(receipt),
            )
            self.assertEqual("private_vacancy_application_packet", receipt["artifact_type"])
            self.assertEqual("private-vacancy-application-packet-v1", receipt["schema_version"])
            self.assertEqual("es", receipt["locale"])
            self.assertEqual("ready_for_manual_authorization", receipt["readiness_state"])
            self.assertEqual("V-003", receipt["vacancy_id"])
            self.assertEqual(str(output.resolve()), receipt["output_path"])
            self.assertTrue(receipt["private_draft"])
            self.assertFalse(receipt["external_action_authorized"])

    def test_cli_rejects_tampered_crossed_and_duplicate_json_without_stdout(self) -> None:
        """Break caught: untrusted artifact/source files reach the destination or diagnostics."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            packet, sources = self._write_inputs(directory)
            tampered = self._packet()
            tampered["readiness"]["external_action_authorized"] = True
            packet.write_text(json.dumps(tampered), encoding="utf-8")
            result, stdout, stderr = self._run_cli(packet, sources, directory / "tampered.json")
            self._assert_failed_without_leak(result, stdout, stderr, "external_action_authorized")

            packet, sources = self._write_inputs(directory)
            crossed = self._sources()
            crossed["candidate_fact_group"]["source_group"]["locale"] = "en"
            sources.write_text(json.dumps(crossed), encoding="utf-8")
            result, stdout, stderr = self._run_cli(packet, sources, directory / "crossed.json")
            self._assert_failed_without_leak(result, stdout, stderr, "candidate_fact_group")

            packet.write_text(
                '{"schema_version":"private-vacancy-application-packet-v1",'
                '"schema_version":"review-sensitive-secret"}',
                encoding="utf-8",
            )
            result, stdout, stderr = self._run_cli(packet, sources, directory / "duplicate.json")
            self._assert_failed_without_leak(result, stdout, stderr, "review-sensitive-secret")
            self.assertFalse((directory / "tampered.json").exists())
            self.assertFalse((directory / "crossed.json").exists())
            self.assertFalse((directory / "duplicate.json").exists())

    def test_cli_failure_preserves_existing_destination_and_cleans_temp(self) -> None:
        """Break caught: a replacement failure damages the previous private artifact."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            packet, sources = self._write_inputs(directory)
            output = directory / "packet.json"
            output.write_bytes(b"previous-private-bytes")
            replace = WRITER.os.replace

            def fail_replace(*args, **kwargs):
                raise OSError("review-sensitive-replace-failure")

            with patch.object(WRITER.os, "replace", side_effect=fail_replace):
                result, stdout, stderr = self._run_cli(packet, sources, output, "--force")

            self._assert_failed_without_leak(result, stdout, stderr, "review-sensitive-replace-failure")
            self.assertEqual(b"previous-private-bytes", output.read_bytes())
            self.assertEqual([], list(directory.glob(f".{output.name}.tmp-*")))
            self.assertIsNotNone(replace)

    def test_cli_rejects_destination_and_ordinary_exceptions_generically(self) -> None:
        """Break caught: destination or unexpected failures leak paths or exception text."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            packet, sources = self._write_inputs(directory)
            occupied = directory / "occupied"
            occupied.mkdir()
            result, stdout, stderr = self._run_cli(packet, sources, occupied)
            self._assert_failed_without_leak(result, stdout, stderr, str(occupied))

            output = directory / "ordinary.json"
            with patch.object(
                WRITER, "write_private_vacancy_application_packet_v1", side_effect=RuntimeError("review-sensitive-secret")
            ):
                result, stdout, stderr = self._run_cli(packet, sources, output)
            self._assert_failed_without_leak(result, stdout, stderr, "review-sensitive-secret")
            self.assertFalse(output.exists())

    def test_cli_rejects_symbolic_link_destination_without_touching_its_target(self) -> None:
        """Break caught: resolving output follows a link and replaces another private file."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            packet, sources = self._write_inputs(directory)
            target = directory / "private-target.json"
            target.write_bytes(b"previous-private-bytes")
            output = directory / "packet-link.json"
            output.symlink_to(target)

            result, stdout, stderr = self._run_cli(packet, sources, output, "--force")

            self._assert_failed_without_leak(result, stdout, stderr, str(output))
            self.assertTrue(output.is_symlink())
            self.assertEqual(b"previous-private-bytes", target.read_bytes())

    def test_cli_rejects_receipt_mismatch_and_hostile_path_without_output(self) -> None:
        """Break caught: output receipt is trusted or path coercion escapes the no-echo boundary."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            packet, sources = self._write_inputs(directory)
            output = directory / "packet.json"
            bad_receipt = WRITER.PrivateVacancyApplicationPacketWriteReceipt(
                artifact_type="private_vacancy_application_packet",
                schema_version="private-vacancy-application-packet-v1",
                locale="es",
                readiness_state="ready_for_manual_authorization",
                vacancy_id="V-003",
                output_path=output.resolve(),
                private_draft=False,
                external_action_authorized=False,
            )
            with patch.object(
                WRITER, "write_private_vacancy_application_packet_v1", return_value=bad_receipt
            ):
                result, stdout, stderr = self._run_cli(packet, sources, output)
            self._assert_failed_without_leak(result, stdout, stderr, "V-003")
            self.assertFalse(output.exists())

            stdout = io.StringIO()
            stderr = io.StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                result = WRITER._cli(
                    [
                        str(packet),
                        "--source-group",
                        str(sources),
                        "--output",
                        ExplodingPath(),
                    ]
                )
            self._assert_failed_without_leak(result, stdout.getvalue(), stderr.getvalue(), "review-sensitive-path")


if __name__ == "__main__":
    unittest.main()
