#!/usr/bin/env python3
"""Public builder for the private first-interview practice handoff."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any


_FAILURE = "private first-interview practice handoff is unavailable"


def _validator() -> Any:
    module_name = "validate_private_first_interview_practice_handoff"
    existing = sys.modules.get(module_name)
    if existing is not None:
        return existing
    path = Path(__file__).with_name("validate_private_first_interview_practice_handoff.py")
    specification = importlib.util.spec_from_file_location(module_name, path)
    if specification is None or specification.loader is None:
        raise RuntimeError(_FAILURE)
    module = importlib.util.module_from_spec(specification)
    sys.modules[module_name] = module
    specification.loader.exec_module(module)
    return module


_validate = _validator()
ValidatedPrivateFirstInterviewPracticeHandoff = _validate.ValidatedPrivateFirstInterviewPracticeHandoff


def build_private_first_interview_practice_handoff(board: object) -> ValidatedPrivateFirstInterviewPracticeHandoff:
    try:
        return _validate.validate_private_first_interview_practice_handoff(board)
    except Exception:
        raise ValueError(_FAILURE) from None
