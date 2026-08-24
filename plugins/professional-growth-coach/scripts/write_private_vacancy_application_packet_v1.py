#!/usr/bin/env python3
"""Atomically write one validator-approved private vacancy application packet."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import secrets
import stat
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any


_MAX_INPUT_BYTES = 512 * 1024
_FAILURE = "cannot write private vacancy application packet"


def _sibling(name: str) -> Any:
    path = Path(__file__).with_name(name)
    specification = importlib.util.spec_from_file_location(f"_pgc_{path.stem}", path)
    if specification is None or specification.loader is None:
        raise RuntimeError("private vacancy packet dependency is unavailable")
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


def _packet_identity() -> Any:
    path = Path(__file__).with_name("private_vacancy_packet_identity.py")
    origin = os.path.realpath(os.fspath(path))
    module_name = (
        "_pgc_private_vacancy_packet_identity_"
        + hashlib.sha256(origin.encode("utf-8")).hexdigest()
    )
    existing = sys.modules.get(module_name)
    if existing is not None:
        if os.path.realpath(os.fspath(getattr(existing, "__file__", ""))) != origin:
            raise RuntimeError("private vacancy packet identity is unavailable")
        return existing
    specification = importlib.util.spec_from_file_location(module_name, path)
    if specification is None or specification.loader is None:
        raise RuntimeError("private vacancy packet identity is unavailable")
    module = importlib.util.module_from_spec(specification)
    sys.modules[module_name] = module
    try:
        specification.loader.exec_module(module)
    except BaseException:
        if sys.modules.get(module_name) is module:
            del sys.modules[module_name]
        raise
    return module


_loader = _sibling("private_input_loader.py")
_snapshot = _sibling("semantic_provenance_snapshot.py")
_validator = _sibling("validate_private_vacancy_application_packet_v1.py")
_identity = _packet_identity()

ValidatedPrivateVacancyPacket = _identity.ValidatedPrivateVacancyPacket
validate_private_vacancy_application_packet_v1 = (
    _validator.validate_private_vacancy_application_packet_v1
)


class PrivateVacancyApplicationPacketWriteError(ValueError):
    """Raised with the fixed, no-echo writer diagnostic."""


@dataclass(frozen=True)
class PrivateVacancyApplicationPacketWriteReceipt:
    artifact_type: str
    schema_version: str
    locale: str
    readiness_state: str
    vacancy_id: str
    output_path: Path
    private_draft: bool
    external_action_authorized: bool


def _canonical_bytes(validated_packet: object) -> tuple[dict[str, object], bytes]:
    try:
        artifact = _validator._revalidate_validated_private_vacancy_packet(
            validated_packet
        )
        if not isinstance(artifact, dict):
            raise ValueError("artifact is unavailable")
        content = json.dumps(
            artifact,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except Exception:
        raise PrivateVacancyApplicationPacketWriteError(_FAILURE) from None
    return artifact, content


def _resolved_output_path(output_path: object) -> Path:
    try:
        expanded = Path(os.fspath(output_path)).expanduser()
        absolute = os.path.abspath(os.fspath(expanded))
        parts = Path(absolute).parts
        if (
            len(parts) > 1
            and parts[1] in {"tmp", "var"}
            and os.path.islink(os.path.join(os.sep, parts[1]))
            and os.path.realpath(os.path.join(os.sep, parts[1]))
            == os.path.join(os.sep, "private", parts[1])
        ):
            absolute = os.path.join(os.sep, "private", parts[1], *parts[2:])
        return Path(absolute)
    except Exception:
        raise PrivateVacancyApplicationPacketWriteError(_FAILURE) from None


def _receipt_for(
    artifact: Mapping[str, object], output_path: Path
) -> PrivateVacancyApplicationPacketWriteReceipt:
    try:
        target_binding = artifact["target_binding"]
        readiness = artifact["readiness"]
        if not isinstance(target_binding, Mapping) or not isinstance(readiness, Mapping):
            raise ValueError("artifact is unavailable")
        return PrivateVacancyApplicationPacketWriteReceipt(
            artifact_type="private_vacancy_application_packet",
            schema_version=artifact["schema_version"],
            locale=artifact["locale"],
            readiness_state=readiness["state"],
            vacancy_id=target_binding["vacancy_id"],
            output_path=output_path,
            private_draft=True,
            external_action_authorized=False,
        )
    except Exception:
        raise PrivateVacancyApplicationPacketWriteError(_FAILURE) from None


def _open_private_parent(parent: Path) -> int:
    if not parent.is_absolute() or parent.anchor != os.sep:
        raise OSError("output parent is unsafe")
    no_follow = getattr(os, "O_NOFOLLOW", 0)
    directory_flag = getattr(os, "O_DIRECTORY", 0)
    flags = os.O_RDONLY | directory_flag
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
            system_alias = (
                index == 0
                and component in {"tmp", "var"}
                and os.path.islink(os.path.join(os.sep, component))
                and os.path.realpath(os.path.join(os.sep, component))
                == os.path.join(os.sep, "private", component)
            )
            next_descriptor = os.open(
                component,
                flags | (0 if system_alias else no_follow),
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
            target_status = os.stat(
                output.name,
                dir_fd=parent_descriptor,
                follow_symlinks=False,
            )
        except FileNotFoundError:
            target_status = None
        if target_status is not None:
            if stat.S_ISLNK(target_status.st_mode):
                raise OSError("output target is a symbolic link")
            if not stat.S_ISREG(target_status.st_mode):
                raise OSError("output target is not a regular file")
            if not force:
                raise FileExistsError("output already exists")
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
        if temporary_name is None or descriptor is None:
            raise OSError("cannot create private temporary artifact")
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
            temporary_name = None
        else:
            try:
                os.link(
                    temporary_name,
                    output.name,
                    src_dir_fd=parent_descriptor,
                    dst_dir_fd=parent_descriptor,
                    follow_symlinks=False,
                )
            except FileExistsError as error:
                raise FileExistsError("output already exists") from error
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


def write_private_vacancy_application_packet_v1(
    validated_packet: object,
    output_path: object,
    *,
    force: bool = False,
) -> PrivateVacancyApplicationPacketWriteReceipt:
    """Write only an opaque, fully validated private packet snapshot."""
    artifact, content = _canonical_bytes(validated_packet)
    output = _resolved_output_path(output_path)
    receipt = _receipt_for(artifact, output)
    try:
        _atomic_private_write(output, content, force=force)
    except Exception:
        raise PrivateVacancyApplicationPacketWriteError(_FAILURE) from None
    return receipt


def _load_source_group(path: Path) -> dict[str, object]:
    try:
        raw = _loader.read_bounded_bytes(path, _MAX_INPUT_BYTES)
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_validator._unique_object)
        return _snapshot.bounded_plain_snapshot(value)
    except Exception:
        raise PrivateVacancyApplicationPacketWriteError(_FAILURE) from None


def _load_validated_packet(packet_path: Path, source_group_path: Path):
    try:
        artifact = _validator.load_private_vacancy_application_packet_v1(packet_path)
        source_group = _load_source_group(source_group_path)
        return validate_private_vacancy_application_packet_v1(artifact, source_group)
    except Exception:
        raise PrivateVacancyApplicationPacketWriteError(_FAILURE) from None


def _receipt_payload(
    receipt: PrivateVacancyApplicationPacketWriteReceipt,
) -> dict[str, object]:
    return {
        "artifact_type": receipt.artifact_type,
        "schema_version": receipt.schema_version,
        "locale": receipt.locale,
        "readiness_state": receipt.readiness_state,
        "vacancy_id": receipt.vacancy_id,
        "output_path": str(receipt.output_path),
        "private_draft": receipt.private_draft,
        "external_action_authorized": receipt.external_action_authorized,
    }


def _receipt_matches(
    receipt: object,
    validated_packet: object,
    output_path: object,
) -> bool:
    try:
        artifact, _ = _canonical_bytes(validated_packet)
        expected = _receipt_for(artifact, _resolved_output_path(output_path))
        return receipt == expected
    except Exception:
        return False


class _NoEchoArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise PrivateVacancyApplicationPacketWriteError(_FAILURE)


def _cli(argv: list[object] | None = None) -> int:
    parser = _NoEchoArgumentParser(description="Write a private vacancy application packet.")
    parser.add_argument("packet", type=Path)
    parser.add_argument("--source-group", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--force", action="store_true")
    try:
        args = parser.parse_args(argv)
        validated = _load_validated_packet(args.packet, args.source_group)
        receipt = write_private_vacancy_application_packet_v1(
            validated, args.output, force=args.force
        )
        if not _receipt_matches(receipt, validated, args.output):
            raise PrivateVacancyApplicationPacketWriteError(_FAILURE)
        print(json.dumps(_receipt_payload(receipt), ensure_ascii=False, separators=(",", ":")))
        return 0
    except SystemExit as error:
        return 0 if error.code == 0 else 2
    except BaseException:
        print(_FAILURE, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(_cli())
