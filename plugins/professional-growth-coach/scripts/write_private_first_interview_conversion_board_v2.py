#!/usr/bin/env python3
"""Write only an opaque, validated private first-interview board v2."""

from __future__ import annotations

import importlib.util
import json
import os
import secrets
import stat
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


_FAILURE = "cannot write private first-interview conversion board"
_MAX_INPUT_BYTES = 512 * 1024


def _sibling(name: str) -> Any:
    path = Path(__file__).with_name(name)
    module_name = path.stem
    existing = sys.modules.get(module_name)
    if existing is not None:
        return existing
    specification = importlib.util.spec_from_file_location(module_name, path)
    if specification is None or specification.loader is None:
        raise RuntimeError(_FAILURE)
    module = importlib.util.module_from_spec(specification)
    sys.modules[module_name] = module
    specification.loader.exec_module(module)
    return module


_validator = _sibling("validate_private_first_interview_conversion_board_v2.py")
_Validated = _validator.ValidatedPrivateFirstInterviewConversionBoardV2


class PrivateFirstInterviewConversionBoardV2WriteError(ValueError):
    """A fixed, no-echo private writer failure."""


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
        artifact = _validator._revalidate_validated_private_first_interview_conversion_board_v2(value)
        content = json.dumps(
            artifact, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        if len(content) > _MAX_INPUT_BYTES:
            raise ValueError(_FAILURE)
        return artifact, content
    except Exception:
        raise PrivateFirstInterviewConversionBoardV2WriteError(_FAILURE) from None


def _resolved_output_path(output_path: object) -> Path:
    try:
        expanded = Path(os.fspath(output_path)).expanduser()
        output = Path(os.path.abspath(os.fspath(expanded)))
        if output.name in {"", ".", ".."}:
            raise ValueError(_FAILURE)
        return output
    except Exception:
        raise PrivateFirstInterviewConversionBoardV2WriteError(_FAILURE) from None


def _trusted_system_alias(absolute: str) -> str:
    parts = Path(absolute).parts
    if len(parts) > 1 and parts[1] in {"tmp", "var"}:
        component = parts[1]
        alias = os.path.join(os.sep, component)
        private = os.path.join(os.sep, "private", component)
        if os.path.islink(alias) and os.path.realpath(alias) == private:
            suffix = os.path.join(*parts[2:]) if len(parts) > 2 else ""
            return os.path.join(private, suffix)
    return absolute


def _trusted_system_directory(metadata: os.stat_result) -> bool:
    return metadata.st_uid == 0 and stat.S_IMODE(metadata.st_mode) & 0o022 == 0


def _private_directory(metadata: os.stat_result, *, created: bool) -> bool:
    if not stat.S_ISDIR(metadata.st_mode):
        return False
    if created:
        return metadata.st_uid == os.getuid() and stat.S_IMODE(metadata.st_mode) == 0o700
    return (
        metadata.st_uid == os.getuid()
        and stat.S_IMODE(metadata.st_mode) & 0o022 == 0
    )


def _open_private_parent(parent: Path) -> int:
    absolute = _trusted_system_alias(os.path.abspath(os.fspath(parent)))
    private_parent = Path(absolute)
    if not private_parent.is_absolute() or private_parent.anchor != os.sep:
        raise OSError(_FAILURE)
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_CLOEXEC", 0)
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    if not flags or not nofollow:
        raise OSError(_FAILURE)
    descriptor = os.open(os.sep, flags)
    entered_user_directory = False
    try:
        for component in private_parent.parts[1:]:
            if component in {"", ".", ".."}:
                raise OSError(_FAILURE)
            created = False
            try:
                os.mkdir(component, 0o700, dir_fd=descriptor)
                created = True
            except FileExistsError:
                pass
            next_descriptor = os.open(component, flags | nofollow, dir_fd=descriptor)
            try:
                metadata = os.fstat(next_descriptor)
                if _private_directory(metadata, created=created):
                    entered_user_directory = True
                elif entered_user_directory or not _trusted_system_directory(metadata):
                    raise OSError(_FAILURE)
                if created:
                    os.fchmod(next_descriptor, 0o700)
            except BaseException:
                os.close(next_descriptor)
                raise
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
                    | getattr(os, "O_NOFOLLOW", 0)
                    | getattr(os, "O_CLOEXEC", 0),
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


def write_private_first_interview_conversion_board_v2(
    validated_board: object, output: Path, *, force: bool = False
) -> WriteReceipt:
    """Atomically write an exact v2 proof to a private, user-owned destination."""
    artifact, content = _canonical_bytes(validated_board)
    target = _resolved_output_path(output)
    try:
        locale = artifact.get("locale")
        if not isinstance(locale, str):
            raise ValueError(_FAILURE)
        _atomic_private_write(target, content, force=force)
        return WriteReceipt(
            artifact_type="private_first_interview_conversion_board",
            schema_version="private-first-interview-conversion-board-v2",
            locale=locale,
            output_path=target,
            private_draft=True,
            external_action_authorized=False,
        )
    except PrivateFirstInterviewConversionBoardV2WriteError:
        raise
    except Exception:
        raise PrivateFirstInterviewConversionBoardV2WriteError(_FAILURE) from None
