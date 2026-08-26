import copy
import importlib
import json
import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = (
    ROOT
    / "tests"
    / "fixtures"
    / "private-first-interview-conversion-board-v1"
    / "accepted-en.json"
)
sys.path.insert(0, str(ROOT / "scripts"))

import build_private_first_interview_conversion_board_v2 as board_builder
import private_first_interview_source_bundle as source_bundle
import write_private_first_interview_conversion_board_v2 as board_writer


def _proof():
    source = json.loads(FIXTURE.read_text(encoding="utf-8"))["source_group"]
    bundle = source_bundle.issue_validated_private_first_interview_source_bundle(
        source, provenance_state="synthetic_fixture"
    )
    return board_builder.build_private_first_interview_conversion_board_v2(
        bundle, as_of_date="2026-08-26"
    )


class PrivateFirstInterviewConversionBoardV2WriterTests(unittest.TestCase):
    def _temporary_names(self, directory: Path, output: Path) -> list[Path]:
        return list(directory.glob(f".{output.name}.tmp-*"))

    def test_writes_only_exact_proof_as_canonical_private_bytes_and_minimal_receipt(self):
        proof = _proof()
        expected = json.dumps(
            proof.artifact, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "board.json"
            receipt = board_writer.write_private_first_interview_conversion_board_v2(proof, output)
            self.assertEqual(expected, output.read_bytes())
            self.assertEqual(0o600, stat.S_IMODE(output.stat().st_mode))
            self.assertEqual(
                {
                    "artifact_type": "private_first_interview_conversion_board",
                    "schema_version": "private-first-interview-conversion-board-v2",
                    "locale": "en",
                    "output_path": output,
                    "private_draft": True,
                    "external_action_authorized": False,
                },
                receipt.__dict__,
            )
            self.assertNotIn("digest", repr(receipt).lower())
            self.assertNotIn("id", repr(receipt).lower())

    def test_loading_v2_writer_first_preserves_the_public_v1_proof_identity(self):
        direct_identity = importlib.import_module(
            "private_first_interview_conversion_board_identity"
        )
        v1_validator = importlib.import_module(
            "validate_private_first_interview_conversion_board_v1"
        )
        self.assertIs(v1_validator._identity, direct_identity)

    def test_rejects_raw_or_forged_proof_without_writing_or_echoing_values(self):
        proof = _proof()
        artifact_json, source_json, metadata_json = board_writer._validator._identity._validation_payload_json(proof)
        forged = object.__new__(type(proof))
        object.__setattr__(forged, "_ValidatedPrivateFirstInterviewConversionBoardV2__artifact_json", artifact_json)
        object.__setattr__(forged, "_ValidatedPrivateFirstInterviewConversionBoardV2__source_group_json", source_json)
        object.__setattr__(forged, "_ValidatedPrivateFirstInterviewConversionBoardV2__metadata_json", metadata_json)
        unsafe_path = "source-value-must-not-echo.json"
        for candidate in (copy.deepcopy(proof.artifact), forged):
            with self.subTest(candidate=type(candidate).__name__), tempfile.TemporaryDirectory() as directory:
                output = Path(directory) / unsafe_path
                with self.assertRaises(board_writer.PrivateFirstInterviewConversionBoardV2WriteError) as raised:
                    board_writer.write_private_first_interview_conversion_board_v2(candidate, output)
                self.assertNotIn(unsafe_path, str(raised.exception))
                self.assertNotIn("source value", str(raised.exception).lower())
                self.assertFalse(output.exists())
                self.assertEqual([], self._temporary_names(Path(directory), output))

    def test_existing_regular_target_requires_force_and_force_replaces_only_regular_file(self):
        proof = _proof()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "board.json"
            output.write_bytes(b"keep")
            with self.assertRaises(board_writer.PrivateFirstInterviewConversionBoardV2WriteError):
                board_writer.write_private_first_interview_conversion_board_v2(proof, output)
            self.assertEqual(b"keep", output.read_bytes())
            board_writer.write_private_first_interview_conversion_board_v2(proof, output, force=True)
            self.assertNotEqual(b"keep", output.read_bytes())
            self.assertEqual(0o600, stat.S_IMODE(output.stat().st_mode))

    def test_rejects_symlink_directory_and_fifo_targets_without_touching_them(self):
        proof = _proof()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            regular = root / "regular.json"
            regular.write_bytes(b"keep")
            symlink = root / "symlink.json"
            symlink.symlink_to(regular)
            directory_target = root / "directory.json"
            directory_target.mkdir()
            fifo = root / "fifo.json"
            os.mkfifo(fifo)
            for output in (symlink, directory_target, fifo):
                with self.subTest(output=output.name):
                    with self.assertRaises(board_writer.PrivateFirstInterviewConversionBoardV2WriteError):
                        board_writer.write_private_first_interview_conversion_board_v2(proof, output, force=True)
                    self.assertEqual([], self._temporary_names(root, output))
            self.assertEqual(b"keep", regular.read_bytes())
            self.assertTrue(symlink.is_symlink())
            self.assertTrue(directory_target.is_dir())
            self.assertTrue(stat.S_ISFIFO(os.lstat(fifo).st_mode))

    def test_rejects_insecure_existing_parent_before_creating_output(self):
        proof = _proof()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            parent = root / "insecure"
            parent.mkdir(mode=0o700)
            parent.chmod(0o777)
            output = parent / "board.json"
            with self.assertRaises(board_writer.PrivateFirstInterviewConversionBoardV2WriteError):
                board_writer.write_private_first_interview_conversion_board_v2(proof, output)
            self.assertFalse(output.exists())
            self.assertEqual([], self._temporary_names(parent, output))

    def test_rejects_existing_parent_with_wrong_owner_before_creating_output(self):
        proof = _proof()
        original_fstat = board_writer.os.fstat
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            parent = root / "owned-by-someone-else"
            parent.mkdir(mode=0o700)
            output = parent / "board.json"

            wrong_owners = (parent.stat().st_uid + 1, 0)
            for owner in wrong_owners:
                with self.subTest(owner=owner):
                    def wrong_owner(descriptor):
                        metadata = original_fstat(descriptor)
                        if metadata.st_ino == parent.stat().st_ino:
                            values = list(metadata)
                            values[4] = owner
                            return os.stat_result(values)
                        return metadata

                    board_writer.os.fstat = wrong_owner
                    try:
                        with self.assertRaises(board_writer.PrivateFirstInterviewConversionBoardV2WriteError):
                            board_writer.write_private_first_interview_conversion_board_v2(proof, output)
                    finally:
                        board_writer.os.fstat = original_fstat
                    self.assertFalse(output.exists())
                    self.assertEqual([], self._temporary_names(parent, output))

    def test_creates_missing_private_parents_and_cleans_temporary_after_fsync_failure(self):
        proof = _proof()
        original_fsync = board_writer.os.fsync
        calls = {"count": 0}

        def fail_first_fsync(descriptor):
            calls["count"] += 1
            if calls["count"] == 1:
                raise OSError("simulated fsync failure")
            return original_fsync(descriptor)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "created" / "board.json"
            board_writer.os.fsync = fail_first_fsync
            try:
                with self.assertRaises(board_writer.PrivateFirstInterviewConversionBoardV2WriteError):
                    board_writer.write_private_first_interview_conversion_board_v2(proof, output)
            finally:
                board_writer.os.fsync = original_fsync
            self.assertEqual(0o700, stat.S_IMODE(output.parent.stat().st_mode))
            self.assertFalse(output.exists())
            self.assertEqual([], self._temporary_names(output.parent, output))


if __name__ == "__main__":
    unittest.main()
