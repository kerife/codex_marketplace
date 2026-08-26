#!/usr/bin/env python3
"""Write only opaque, validated private learning-proof sprint snapshots."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import secrets
import stat
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def _sibling(name: str) -> Any:
    path = Path(__file__).with_name(name)
    if path.stem == "learning_proof_sprint_identity":
        origin = os.path.realpath(os.fspath(path))
        module_name = "_pgc_learning_proof_sprint_identity_" + hashlib.sha256(origin.encode("utf-8")).hexdigest()
        existing = sys.modules.get(module_name)
        if existing is not None:
            return existing
    else:
        module_name = path.stem if path.stem == "private_prose_safety" else f"_pgc_{path.stem}"
    specification = importlib.util.spec_from_file_location(module_name, path)
    if specification is None or specification.loader is None:
        raise RuntimeError("learning proof sprint dependency is unavailable")
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


_validator = _sibling("validate_learning_proof_sprint_v1.py")
_loader = _sibling("private_input_loader.py")

ValidatedLearningProofSprint = _validator.ValidatedLearningProofSprint
_FAILURE = "cannot write learning proof sprint"
_MAX_INPUT_BYTES = 512 * 1024


class LearningProofSprintWriteError(ValueError):
    """Raised with one fixed, no-echo writer diagnostic."""


@dataclass(frozen=True)
class LearningProofSprintWriteReceipt:
    artifact_type: str
    schema_version: str
    locale: str
    output_path: Path
    private_draft: bool
    external_action_authorized: bool


def _canonical_bytes(value: object) -> tuple[dict[str, object], bytes]:
    try:
        artifact = _validator._revalidate_validated_learning_proof_sprint(value)
        content = json.dumps(artifact, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return artifact, content
    except Exception:
        raise LearningProofSprintWriteError(_FAILURE) from None


def _resolved_output_path(output_path: object) -> Path:
    try:
        expanded = Path(os.fspath(output_path)).expanduser()
        absolute = os.path.abspath(os.fspath(expanded))
        if Path(absolute).is_symlink():
            raise ValueError("output target is unsafe")
        return Path(absolute)
    except Exception:
        raise LearningProofSprintWriteError(_FAILURE) from None


def _open_private_parent(parent: Path) -> int:
    if not parent.is_absolute() or parent.anchor != os.sep:
        raise OSError("output parent is unsafe")
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    descriptor = os.open(os.sep, flags)
    try:
        for index, component in enumerate(parent.parts[1:]):
            if component in {"", ".", ".."}:
                raise OSError("output parent is unsafe")
            created = False
            try:
                os.mkdir(component, 0o700, dir_fd=descriptor)
                created = True
            except FileExistsError:
                pass
            alias = (
                index == 0
                and component in {"tmp", "var"}
                and os.path.islink(os.path.join(os.sep, component))
                and os.path.realpath(os.path.join(os.sep, component)) == os.path.join(os.sep, "private", component)
            )
            next_descriptor = os.open(
                component,
                flags | (0 if alias else getattr(os, "O_NOFOLLOW", 0)),
                dir_fd=descriptor,
            )
            if not stat.S_ISDIR(os.fstat(next_descriptor).st_mode):
                os.close(next_descriptor)
                raise OSError("output parent is not a directory")
            if created:
                os.fchmod(next_descriptor, 0o700)
            os.close(descriptor)
            descriptor = next_descriptor
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def _atomic_private_write(output: Path, content: bytes, *, force: bool) -> None:
    if not output.name or output.name in {".", ".."}:
        raise OSError("output name is unsafe")
    parent_descriptor = _open_private_parent(output.parent)
    temporary_name: str | None = None
    descriptor: int | None = None
    try:
        try:
            target = os.stat(output.name, dir_fd=parent_descriptor, follow_symlinks=False)
        except FileNotFoundError:
            target = None
        if target is not None:
            if stat.S_ISLNK(target.st_mode) or not stat.S_ISREG(target.st_mode):
                raise OSError("output target is unsafe")
            if not force:
                raise FileExistsError("output already exists")
        for _ in range(100):
            candidate = f".{output.name}.tmp-{secrets.token_hex(8)}"
            try:
                descriptor = os.open(
                    candidate,
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
                    0o600,
                    dir_fd=parent_descriptor,
                )
                temporary_name = candidate
                break
            except FileExistsError:
                continue
        if descriptor is None or temporary_name is None:
            raise OSError("cannot create private temporary artifact")
        with os.fdopen(descriptor, "wb") as stream:
            descriptor = None
            os.fchmod(stream.fileno(), 0o600)
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        if force:
            os.replace(temporary_name, output.name, src_dir_fd=parent_descriptor, dst_dir_fd=parent_descriptor)
        else:
            os.link(temporary_name, output.name, src_dir_fd=parent_descriptor, dst_dir_fd=parent_descriptor, follow_symlinks=False)
            os.unlink(temporary_name, dir_fd=parent_descriptor)
        temporary_name = None
        os.fsync(parent_descriptor)
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if temporary_name is not None:
            try:
                os.unlink(temporary_name, dir_fd=parent_descriptor)
            except FileNotFoundError:
                pass
        os.close(parent_descriptor)


def write_learning_proof_sprint_v1(
    validated_sprint: object, output_path: object, *, force: bool = False
) -> LearningProofSprintWriteReceipt:
    """Write one opaque proof; mappings and forged proof classes are rejected."""
    artifact, content = _canonical_bytes(validated_sprint)
    output = _resolved_output_path(output_path)
    try:
        locale = artifact["locale"]
        if not isinstance(locale, str):
            raise ValueError("locale unavailable")
        _atomic_private_write(output, content, force=force)
        return LearningProofSprintWriteReceipt(
            artifact_type="learning_proof_sprint",
            schema_version="learning-proof-sprint-v1",
            locale=locale,
            output_path=output,
            private_draft=True,
            external_action_authorized=False,
        )
    except LearningProofSprintWriteError:
        raise
    except Exception:
        raise LearningProofSprintWriteError(_FAILURE) from None


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate key")
        result[key] = value
    return result


def _load_validated(path: Path, source_path: Path):
    try:
        artifact = _validator.load_learning_proof_sprint_v1(path)
        raw = _loader.read_bounded_bytes(source_path, _MAX_INPUT_BYTES)
        source = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object)
        return _validator.validate_learning_proof_sprint_v1(artifact, source)
    except Exception:
        raise LearningProofSprintWriteError(_FAILURE) from None


def _cli(argv: list[object] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write a private learning proof sprint.")
    parser.add_argument("sprint", type=Path)
    parser.add_argument("--source-group", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--force", action="store_true")
    try:
        args = parser.parse_args(argv)
        validated = _load_validated(args.sprint, args.source_group)
        receipt = write_learning_proof_sprint_v1(validated, args.output, force=args.force)
        print(json.dumps({
            "artifact_type": receipt.artifact_type,
            "schema_version": receipt.schema_version,
            "locale": receipt.locale,
            "output_path": str(receipt.output_path),
            "private_draft": receipt.private_draft,
            "external_action_authorized": receipt.external_action_authorized,
        }, ensure_ascii=False, separators=(",", ":")))
        return 0
    except SystemExit as error:
        return 0 if error.code == 0 else 2
    except BaseException:
        print(_FAILURE, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(_cli())
