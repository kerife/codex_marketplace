#!/usr/bin/env python3
"""Build a sanitized private first-interview board from an opaque source bundle."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any


_FAILURE = "private first-interview conversion board does not match validated sources"


def _validator_module() -> Any:
    path = Path(__file__).with_name("validate_private_first_interview_conversion_board_v2.py")
    module_name = "validate_private_first_interview_conversion_board_v2"
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


_validator = _validator_module()
ValidatedPrivateFirstInterviewConversionBoardV2 = _validator.ValidatedPrivateFirstInterviewConversionBoardV2


def build_private_first_interview_conversion_board_v2(
    source_bundle: object, *, locale: str = "en", as_of_date: str
) -> ValidatedPrivateFirstInterviewConversionBoardV2:
    """Build from an exact issuer-created source bundle, never raw source data."""
    try:
        return _validator.validate_private_first_interview_conversion_board_v2(
            source_bundle, locale=locale, as_of_date=as_of_date
        )
    except Exception:
        raise ValueError(_FAILURE) from None


if __name__ == "__main__":
    raise SystemExit("private first-interview conversion board v2 builder is a library interface")
