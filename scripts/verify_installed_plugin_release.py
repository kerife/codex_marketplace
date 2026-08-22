#!/usr/bin/env python3
"""Resolve and verify one exact installed plugin release without mutable aliases."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import sys
from pathlib import Path
from typing import Mapping


NAME_PATTERN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
VERSION_PATTERN = re.compile(r"0\.2\.0\+codex\.\d{14}")
MAX_PLUGIN_LIST_BYTES = 1024 * 1024
_PERSONAL_METADATA_PATTERNS = (
    re.compile(
        rb"/(?:Users/[^/\x00]+|private|var|opt|Applications|Volumes|root|srv|usr|tmp)"
        rb"(?:/[^/\x00]+)*/job_search_coach(?:/|\x00)",
        re.I,
    ),
    re.compile(
        rb"[A-Za-z]:[\\/](?:[^\\/\x00]+[\\/])*job_search_coach(?:[\\/]|\x00)",
        re.I,
    ),
)


class ReleaseVerificationError(ValueError):
    """One fixed-diagnostic release verification failure."""


def _safe_component(value: object, pattern: re.Pattern[str]) -> bool:
    return isinstance(value, str) and pattern.fullmatch(value) is not None


def resolve_exact_installed_cache(
    plugin_list: object,
    plugin: str,
    marketplace: str,
    expected_version: str,
    cache_family: Path,
) -> Path:
    """Return only cache-family/plugin/exact-version for one enabled installed row."""

    try:
        if not (
            _safe_component(plugin, NAME_PATTERN)
            and _safe_component(marketplace, NAME_PATTERN)
            and _safe_component(expected_version, VERSION_PATTERN)
            and isinstance(cache_family, Path)
            and cache_family.is_absolute()
            and cache_family.is_dir()
            and not cache_family.is_symlink()
            and isinstance(plugin_list, Mapping)
        ):
            raise ReleaseVerificationError
        rows = plugin_list.get("installed")
        if not isinstance(rows, list):
            raise ReleaseVerificationError
        identity_rows = [
            row
            for row in rows
            if isinstance(row, Mapping)
            and row.get("name") == plugin
            and row.get("marketplaceName") == marketplace
        ]
        if len(identity_rows) != 1:
            raise ReleaseVerificationError
        row = identity_rows[0]
        if not (
            row.get("pluginId") == f"{plugin}@{marketplace}"
            and row.get("version") == expected_version
            and row.get("installed") is True
            and row.get("enabled") is True
        ):
            raise ReleaseVerificationError
        expected = cache_family / plugin / expected_version
        family_real = cache_family.resolve(strict=True)
        expected_real = expected.resolve(strict=True)
        if not (
            expected_real == family_real / plugin / expected_version
            and expected_real.is_relative_to(family_real)
            and expected_real.is_dir()
            and not expected.is_symlink()
            and not (cache_family / plugin).is_symlink()
        ):
            raise ReleaseVerificationError
        return expected
    except (OSError, RuntimeError, TypeError, ValueError):
        raise ReleaseVerificationError("installed plugin resolution failed") from None


def _file_digest(path: Path) -> tuple[str, bytes]:
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise OSError
        digest = hashlib.sha256()
        collected = bytearray()
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
            collected.extend(chunk)
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    current = path.lstat()
    stable_fields = ("st_dev", "st_ino", "st_size", "st_mtime_ns")
    if any(getattr(before, field) != getattr(after, field) for field in stable_fields):
        raise OSError
    if any(getattr(after, field) != getattr(current, field) for field in stable_fields):
        raise OSError
    return digest.hexdigest(), bytes(collected)


def release_inventory(root: Path) -> tuple[tuple[str, str], ...]:
    """Return sorted POSIX relative paths and lowercase SHA-256 digests."""

    try:
        if not isinstance(root, Path) or not root.is_dir() or root.is_symlink():
            raise ReleaseVerificationError
        entries: list[tuple[str, str]] = []
        for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()):
            relative = path.relative_to(root).as_posix()
            if path.is_symlink() or path.name == "__pycache__":
                raise ReleaseVerificationError
            if path.is_dir():
                continue
            if not path.is_file() or path.suffix.lower() in {".pyc", ".pyo"}:
                raise ReleaseVerificationError
            relative.encode("utf-8", errors="strict")
            digest, payload = _file_digest(path)
            if any(pattern.search(payload) for pattern in _PERSONAL_METADATA_PATTERNS):
                raise ReleaseVerificationError
            entries.append((relative, digest))
        if not entries:
            raise ReleaseVerificationError
        return tuple(entries)
    except (OSError, RuntimeError, TypeError, UnicodeError, ValueError):
        raise ReleaseVerificationError("release inventory is invalid") from None


def _aggregate_inventory(inventory: tuple[tuple[str, str], ...]) -> str:
    digest = hashlib.sha256()
    for relative, file_digest in inventory:
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(file_digest.encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def aggregate_release_digest(root: Path) -> str:
    return _aggregate_inventory(release_inventory(root))


def verify_release_parity(source_root: Path, cache_root: Path) -> dict[str, object]:
    try:
        source = release_inventory(source_root)
        cache = release_inventory(cache_root)
        if source != cache:
            raise ReleaseVerificationError
        source_aggregate = _aggregate_inventory(source)
        cache_aggregate = _aggregate_inventory(cache)
        if source_aggregate != cache_aggregate:
            raise ReleaseVerificationError
        return {
            "file_count": len(source),
            "source_aggregate_sha256": source_aggregate,
            "cache_aggregate_sha256": cache_aggregate,
            "sorted_relative_inventory_equal": True,
            "per_file_sha256_equal": True,
        }
    except (OSError, RuntimeError, TypeError, UnicodeError, ValueError):
        raise ReleaseVerificationError("release parity failed") from None


def _read_plugin_list(path: Path) -> object:
    try:
        if not path.is_file() or path.is_symlink() or path.stat().st_size > MAX_PLUGIN_LIST_BYTES:
            raise ReleaseVerificationError
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
        raise ReleaseVerificationError("installed plugin resolution failed") from None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify one exact installed plugin release.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    resolve_parser = subparsers.add_parser("resolve")
    resolve_parser.add_argument("--plugin-list", type=Path, required=True)
    resolve_parser.add_argument("--plugin", required=True)
    resolve_parser.add_argument("--marketplace", required=True)
    resolve_parser.add_argument("--expected-version", required=True)
    resolve_parser.add_argument("--cache-family", type=Path, required=True)
    parity_parser = subparsers.add_parser("parity")
    parity_parser.add_argument("--source-root", type=Path, required=True)
    parity_parser.add_argument("--cache-root", type=Path, required=True)
    arguments = parser.parse_args(argv)
    try:
        if arguments.command == "resolve":
            resolved = resolve_exact_installed_cache(
                _read_plugin_list(arguments.plugin_list),
                arguments.plugin,
                arguments.marketplace,
                arguments.expected_version,
                arguments.cache_family,
            )
            print(resolved)
        else:
            print(
                json.dumps(
                    verify_release_parity(arguments.source_root, arguments.cache_root),
                    sort_keys=True,
                    separators=(",", ":"),
                )
            )
    except ReleaseVerificationError as error:
        print(str(error), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
