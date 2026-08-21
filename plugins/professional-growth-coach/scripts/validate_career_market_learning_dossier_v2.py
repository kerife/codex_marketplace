#!/usr/bin/env python3
"""Validate source-recomputed career market learning dossiers v2."""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any


def _sibling(name: str) -> Any:
    path = Path(__file__).with_name(name)
    specification = importlib.util.spec_from_file_location(f"_pgc_{path.stem}", path)
    if specification is None or specification.loader is None:
        raise RuntimeError("required market dossier dependency is unavailable")
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


_builder = _sibling("build_career_market_learning_dossier_v2.py")
_alignment = _builder._alignment


def _canonical_json(value: Mapping[str, object]) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def validate_market_dossier_v2(
    value: object, research: object, executive_dossier: object
) -> list[str]:
    """Return no errors only for the exact source-recomputed canonical object."""
    try:
        if not _alignment._safe_tree(value):
            return ["market dossier does not match validated sources"]
        value_copy = copy.deepcopy(value)
        research_copy, dossier_copy = _builder._validated_source_copies(research, executive_dossier)
        alignment = _alignment.derive_candidate_market_alignment_v2(research_copy, dossier_copy)
        expected = _builder._project_market_v2(research_copy, dossier_copy, alignment)
        if not isinstance(value_copy, Mapping) or _canonical_json(value_copy) != _canonical_json(expected):
            return ["market dossier does not match validated sources"]
        return []
    except Exception:
        return ["market dossier does not match validated sources"]
