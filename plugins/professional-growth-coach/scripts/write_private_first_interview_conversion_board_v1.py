#!/usr/bin/env python3
"""Write only an opaque, validated private first-interview board."""

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
    origin = os.path.realpath(os.fspath(path))
    module_name = "_pgc_private_first_interview_writer_" + hashlib.sha256(
        (origin + name).encode("utf-8")
    ).hexdigest()
    existing = sys.modules.get(module_name)
    if existing is not None:
        return existing
    specification = importlib.util.spec_from_file_location(module_name, path)
    if specification is None or specification.loader is None:
        raise RuntimeError("private first-interview dependency is unavailable")
    module = importlib.util.module_from_spec(specification)
    sys.modules[module_name] = module
    specification.loader.exec_module(module)
    return module


_validator = _sibling("validate_private_first_interview_conversion_board_v1.py")
_identity = _validator._identity
_Validated = _identity.ValidatedPrivateFirstInterviewConversionBoard
_FAILURE = "cannot write private first-interview conversion board"
_MAX_INPUT_BYTES = 512 * 1024


class PrivateFirstInterviewConversionBoardWriteError(ValueError):
    """A bounded, no-echo private writer failure."""


@dataclass(frozen=True)
class WriteReceipt:
    artifact_type: str
    schema_version: str
    locale: str
    output_path: Path
    private_draft: bool
    external_action_authorized: bool


def _canonical_bytes(value: object) -> tuple[dict[str, object], bytes]:
    try:
        if type(value) is not _Validated:
            raise TypeError(_FAILURE)
        artifact = _validator._revalidate_validated_private_first_interview_conversion_board(value)
        content = json.dumps(
            artifact, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        if len(content) > _MAX_INPUT_BYTES:
            raise ValueError(_FAILURE)
        return artifact, content
    except Exception:
        raise PrivateFirstInterviewConversionBoardWriteError(_FAILURE) from None


def _resolved_output_path(output_path: object) -> Path:
    try:
        expanded = Path(os.fspath(output_path)).expanduser()
        absolute = Path(os.path.abspath(os.fspath(expanded)))
        if absolute.name in {"", ".", ".."} or absolute.is_symlink():
            raise ValueError(_FAILURE)
        return absolute
    except Exception:
        raise PrivateFirstInterviewConversionBoardWriteError(_FAILURE) from None


def _open_private_parent(parent: Path) -> int:
    if not parent.is_absolute() or parent.anchor != os.sep:
        raise OSError(_FAILURE)
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    descriptor = os.open(os.sep, flags)
    try:
        for index, component in enumerate(parent.parts[1:]):
            if component in {"", ".", ".."}:
                raise OSError(_FAILURE)
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
                and os.path.realpath(os.path.join(os.sep, component))
                == os.path.join(os.sep, "private", component)
            )
            next_descriptor = os.open(
                component,
                flags | (0 if alias else getattr(os, "O_NOFOLLOW", 0)),
                dir_fd=descriptor,
            )
            if not stat.S_ISDIR(os.fstat(next_descriptor).st_mode):
                os.close(next_descriptor)
                raise OSError(_FAILURE)
            if created:
                os.fchmod(next_descriptor, 0o700)
            os.close(descriptor)
            descriptor = next_descriptor
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def _atomic_private_write(output: Path, content: bytes, *, force: bool) -> None:
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
                raise OSError(_FAILURE)
            if not force:
                raise FileExistsError(_FAILURE)
        for _ in range(100):
            candidate = f".{output.name}.tmp-{secrets.token_hex(8)}"
            try:
                descriptor = os.open(
                    candidate,
                    os.O_WRONLY
                    | os.O_CREAT
                    | os.O_EXCL
                    | getattr(os, "O_NOFOLLOW", 0),
                    0o600,
                    dir_fd=parent_descriptor,
                )
                temporary_name = candidate
                break
            except FileExistsError:
                continue
        if descriptor is None or temporary_name is None:
            raise OSError(_FAILURE)
        with os.fdopen(descriptor, "wb") as stream:
            descriptor = None
            os.fchmod(stream.fileno(), 0o600)
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        if force:
            os.replace(
                temporary_name,
                output.name,
                src_dir_fd=parent_descriptor,
                dst_dir_fd=parent_descriptor,
            )
        else:
            os.link(
                temporary_name,
                output.name,
                src_dir_fd=parent_descriptor,
                dst_dir_fd=parent_descriptor,
                follow_symlinks=False,
            )
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


def write_private_first_interview_conversion_board_v1(
    validated_board: object, output: Path, *, force: bool = False
) -> WriteReceipt:
    """Atomically write one exact validator-issued board with mode 0600."""

    artifact, content = _canonical_bytes(validated_board)
    target = _resolved_output_path(output)
    try:
        locale = artifact.get("locale")
        if not isinstance(locale, str):
            raise ValueError(_FAILURE)
        _atomic_private_write(target, content, force=force)
        return WriteReceipt(
            artifact_type="private_first_interview_conversion_board",
            schema_version="private-first-interview-conversion-board-v1",
            locale=locale,
            output_path=target,
            private_draft=True,
            external_action_authorized=False,
        )
    except PrivateFirstInterviewConversionBoardWriteError:
        raise
    except Exception:
        raise PrivateFirstInterviewConversionBoardWriteError(_FAILURE) from None


def _cli(argv: list[object] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write a private first-interview conversion board.")
    parser.add_argument("artifact", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--force", action="store_true")
    try:
        args = parser.parse_args(argv)
        raw = json.loads(args.artifact.read_text(encoding="utf-8"))
        validated = _validator.validate_private_first_interview_conversion_board_v1(raw)
        receipt = write_private_first_interview_conversion_board_v1(validated, args.output, force=args.force)
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
