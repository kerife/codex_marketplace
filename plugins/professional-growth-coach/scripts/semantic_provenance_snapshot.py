#!/usr/bin/env python3
"""Capture bounded semantic inputs into one detached built-in snapshot."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass


MAX_DEPTH = 32
MAX_NODES = 10_000
MAX_ITEMS = 150
MAX_STRING = 4096


@dataclass
class _Budget:
    nodes: int = 0

    def consume(self) -> None:
        self.nodes += 1
        if self.nodes > MAX_NODES:
            raise ValueError("node budget exceeded")


def _plain_snapshot(
    value: object,
    *,
    depth: int,
    active: set[int],
    budget: _Budget,
) -> object:
    budget.consume()
    if depth > MAX_DEPTH:
        raise ValueError("depth budget exceeded")
    if type(value) is str:
        if len(value) > MAX_STRING or any(
            0xD800 <= ord(character) <= 0xDFFF for character in value
        ):
            raise ValueError("string is invalid")
        return value
    if value is None or type(value) in {bool, int}:
        return value
    if not isinstance(value, (Mapping, list, tuple)):
        raise ValueError("value is not a JSON value")

    identity = id(value)
    if identity in active:
        raise ValueError("active-path cycle")
    active.add(identity)
    try:
        if isinstance(value, Mapping):
            result: dict[str, object] = {}
            count = 0
            for key, nested in value.items():
                count += 1
                if count > MAX_ITEMS:
                    raise ValueError("mapping item budget exceeded")
                captured_key = _plain_snapshot(
                    key, depth=depth + 1, active=active, budget=budget
                )
                if type(captured_key) is not str or captured_key in result:
                    raise ValueError("mapping key is invalid")
                result[captured_key] = _plain_snapshot(
                    nested, depth=depth + 1, active=active, budget=budget
                )
            return result

        items: list[object] = []
        for nested in value:
            if len(items) >= MAX_ITEMS:
                raise ValueError("collection item budget exceeded")
            items.append(
                _plain_snapshot(
                    nested, depth=depth + 1, active=active, budget=budget
                )
            )
        return items
    finally:
        active.discard(identity)


def bounded_plain_snapshot(group: object) -> dict[str, object]:
    """Capture one bounded mapping traversal or fail with a fixed diagnostic."""
    try:
        budget = _Budget()
        captured = _plain_snapshot(group, depth=0, active=set(), budget=budget)
    except Exception:
        raise ValueError("semantic input group is invalid") from None
    if not isinstance(captured, dict):
        raise ValueError("semantic input group is invalid") from None
    return captured


def bounded_tree(value: object) -> bool:
    """Return whether one value fits the shared semantic snapshot boundary."""
    try:
        _plain_snapshot(value, depth=0, active=set(), budget=_Budget())
        return True
    except Exception:
        return False
