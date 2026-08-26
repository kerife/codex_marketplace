#!/usr/bin/env python3
"""Build a deterministic, source-bound private first-interview board."""

from __future__ import annotations

import hashlib
import importlib.util
import os
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any


def _validator_module() -> Any:
    path = Path(__file__).with_name("validate_private_first_interview_conversion_board_v1.py")
    origin = os.path.realpath(os.fspath(path))
    module_name = "_pgc_private_first_interview_validator_" + hashlib.sha256(origin.encode("utf-8")).hexdigest()
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


_validator = _validator_module()
ValidatedPrivateFirstInterviewConversionBoard = _validator.ValidatedPrivateFirstInterviewConversionBoard
_FAILURE = "private first-interview conversion board does not match validated sources"


def build_private_first_interview_conversion_board_v1(
    source_group: object,
) -> ValidatedPrivateFirstInterviewConversionBoard:
    """Build one validator-issued proof from a raw source group only.

    The builder intentionally does not accept a composite artifact. Final
    public rows are recomputed by the validator from the source group.
    """

    try:
        if not isinstance(source_group, Mapping):
            raise ValueError(_FAILURE)
        if "source_group" in source_group or not _validator._source_group_shape(source_group):
            raise ValueError(_FAILURE)
        return _validator.validate_private_first_interview_conversion_board_v1(source_group)
    except Exception:
        raise ValueError(_FAILURE) from None


if __name__ == "__main__":
    raise SystemExit("private first-interview conversion board builder is a library interface")
