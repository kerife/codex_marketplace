#!/usr/bin/env python3
"""Run installed-root-only vacancy-first release smokes."""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
from collections.abc import Mapping
from contextlib import contextmanager
from pathlib import Path
from pathlib import PurePosixPath
from types import ModuleType


MODULE_NAME_PATTERN = re.compile(r"[a-z][a-z0-9_]*")
DEFAULT_MODULES = (
    "semantic_provenance_snapshot",
    "build_career_market_learning_dossier",
    "build_career_market_learning_dossier_v2",
    "build_career_learning_decision",
    "build_career_learning_decision_v2",
    "derive_candidate_market_alignment_v2",
    "build_candidate_gap_response_v1",
    "validate_candidate_gap_response_v1",
    "build_candidate_gap_assessment_v1",
    "validate_candidate_gap_assessment_v1",
    "build_career_next_action_eligibility_v1",
    "validate_career_next_action_eligibility_v1",
    "project_career_learning_decision_v3",
    "build_career_learning_decision_v3",
    "validate_career_learning_decision_v3",
    "render_executive_career_dossier_v2",
)
SMOKE_SOURCES_RELATIVE = Path("tests/fixtures/vacancy-first-smoke/sources.json")
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")
MAX_SMOKE_SOURCES_BYTES = 64 * 1024
LEARNING_ACTIONS = frozenset(
    {
        "build_bounded_proof",
        "run_validation_lab",
        "research_provider_option",
        "run_role_search_experiment",
    }
)
CASE_RULES = (
    ("unavailable", "unavailable", "market_unavailable", "no_learning_yet", 0),
    ("selection_required", "selection_required", "selection_missing", "select_target_vacancy_and_signal", 0),
    ("insufficient_recurrence", "insufficient_recurrence", "recurrence_below_two", "prepare_private_vacancy_packet", 0),
    ("gap_unknown", "insufficient_gap_evidence", "gap_unknown", "confirm_gap_relation", 0),
    ("supported", "insufficient_gap_evidence", "candidate_supported", "prepare_private_vacancy_packet", 0),
    ("provider_choice", "provider_selection_required", "provider_choice_missing", "select_provider_option", 0),
    ("provider_evidence", "provider_evidence_required", "provider_evidence_missing", "no_learning_yet", 0),
    ("experience", "learning_not_applicable", "professional_experience_required", "prepare_private_vacancy_packet", 0),
    ("proof", "eligible", "proof_gap_recurrent", "build_bounded_proof", 1),
    ("practice", "eligible", "practice_gap_recurrent", "run_validation_lab", 1),
    ("terminology", "eligible", "terminology_gap_recurrent", "run_role_search_experiment", 1),
    ("knowledge", "eligible", "knowledge_gap_recurrent_provider_selected", "research_provider_option", 1),
)
RELATION_BY_CASE = {
    "insufficient_recurrence": "proof_gap",
    "gap_unknown": "unknown",
    "supported": "supported",
    "provider_choice": "knowledge_gap",
    "provider_evidence": "knowledge_gap",
    "experience": "professional_experience_gap",
    "proof": "proof_gap",
    "practice": "practice_gap",
    "terminology": "terminology_gap",
    "knowledge": "knowledge_gap",
}
ACCEPTED_GROUPS = (
    "response_mapping",
    "recurrence_routes",
    "nonlearning_routes",
    "provider_lifecycle",
    "action_matrix_es",
    "action_matrix_en",
    "exact_unions_snapshots",
    "dom_aria",
    "historical_bytes",
)
REJECTED_GROUPS = (
    "provider_displacement",
    "private_disclosure",
    "forged_sources",
    "crossed_sources",
    "mutable_sources",
    "oversized_sources",
    "exceptional_sources",
    "writer_output",
    "cli_output",
)
HISTORICAL_RENDER_SNAPSHOTS = {
    "v1": {
        "bytes": 97805,
        "sha256": "4dbb6be8e1a95cdcc8f3e937dcca600fb26f9dc53d7ef519027048c73b12316f",
    },
    "v2": {
        "bytes": 101282,
        "sha256": "0232f7d71de6e85f1b18d7407703b7af944c936c9c905b55fd9a3592067d6167",
    },
    "no_market": {
        "bytes": 48801,
        "sha256": "19d85f8a4061ca5eb44746801a2f0094a9109d9d5764e80d515d84bafdfd79d6",
    },
}


class InstalledSmokeError(RuntimeError):
    """One fixed-diagnostic installed smoke failure."""


_STABLE_STAT_FIELDS = ("st_dev", "st_ino", "st_size", "st_mtime_ns")


def _snapshot_inventory(root: Path) -> tuple[tuple[str, str], ...]:
    """Use the release verifier's closed regular-file inventory contract."""

    return _load_release_helper().release_inventory(root)


def _snapshot_relative_path(value: object) -> tuple[str, ...]:
    try:
        if not isinstance(value, str) or not value or "\x00" in value:
            raise ValueError
        value.encode("utf-8", errors="strict")
        relative = PurePosixPath(value)
        if (
            relative.is_absolute()
            or relative.as_posix() != value
            or not relative.parts
            or any(part in {"", ".", ".."} for part in relative.parts)
        ):
            raise ValueError
        return relative.parts
    except (TypeError, UnicodeError, ValueError):
        raise InstalledSmokeError("installed smoke failed") from None


def _private_snapshot_directory(root: Path, parts: tuple[str, ...]) -> Path:
    directory = root
    for part in parts:
        directory = directory / part
        directory.mkdir(mode=0o700, exist_ok=True)
        if directory.is_symlink() or not stat.S_ISDIR(directory.lstat().st_mode):
            raise OSError
        os.chmod(directory, 0o700)
    return directory


def _write_all(descriptor: int, payload: bytes) -> None:
    position = 0
    while position < len(payload):
        written = os.write(descriptor, payload[position:])
        if written <= 0:
            raise OSError
        position += written


def _copy_snapshot_file(
    source_root: Path,
    relative_parts: tuple[str, ...],
    expected_digest: str,
    destination: Path,
) -> None:
    """Copy one inventory entry through stable, no-follow descriptors only."""

    directory_flags = (
        os.O_RDONLY
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    file_flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    source_directory = os.open(source_root, directory_flags)
    source_descriptor: int | None = None
    destination_descriptor: int | None = None
    try:
        if not stat.S_ISDIR(os.fstat(source_directory).st_mode):
            raise OSError
        for part in relative_parts[:-1]:
            child_directory = os.open(part, directory_flags, dir_fd=source_directory)
            if not stat.S_ISDIR(os.fstat(child_directory).st_mode):
                os.close(child_directory)
                raise OSError
            os.close(source_directory)
            source_directory = child_directory
        source_descriptor = os.open(relative_parts[-1], file_flags, dir_fd=source_directory)
        before = os.fstat(source_descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise OSError
        destination_descriptor = os.open(
            destination,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
            0o600,
        )
        digest = hashlib.sha256()
        while True:
            payload = os.read(source_descriptor, 1024 * 1024)
            if not payload:
                break
            digest.update(payload)
            _write_all(destination_descriptor, payload)
        after = os.fstat(source_descriptor)
        current = os.stat(
            relative_parts[-1], dir_fd=source_directory, follow_symlinks=False
        )
        if (
            not stat.S_ISREG(current.st_mode)
            or any(
                getattr(before, field) != getattr(after, field)
                or getattr(after, field) != getattr(current, field)
                for field in _STABLE_STAT_FIELDS
            )
            or digest.hexdigest() != expected_digest
        ):
            raise OSError
        os.fchmod(destination_descriptor, 0o600)
    finally:
        if destination_descriptor is not None:
            os.close(destination_descriptor)
        if source_descriptor is not None:
            os.close(source_descriptor)
        os.close(source_directory)


def _capture_private_snapshot(source_root: Path, destination_root: Path) -> None:
    inventory = _snapshot_inventory(source_root)
    if not inventory:
        raise InstalledSmokeError("installed smoke failed")
    destination_root.mkdir(mode=0o700)
    os.chmod(destination_root, 0o700)
    previous_relative: str | None = None
    for relative, expected_digest in inventory:
        relative_parts = _snapshot_relative_path(relative)
        if (
            not isinstance(expected_digest, str)
            or SHA256_PATTERN.fullmatch(expected_digest) is None
            or previous_relative is not None
            and relative <= previous_relative
        ):
            raise InstalledSmokeError("installed smoke failed")
        previous_relative = relative
        destination_directory = _private_snapshot_directory(
            destination_root, relative_parts[:-1]
        )
        _copy_snapshot_file(
            source_root,
            relative_parts,
            expected_digest,
            destination_directory / relative_parts[-1],
        )


@contextmanager
def capture_verified_private_snapshots(source_archive: Path, plugin_root: Path):
    """Capture two independent private release snapshots and verify their parity."""

    try:
        temporary_directory = tempfile.TemporaryDirectory(prefix="pgc-installed-smoke-")
    except (OSError, RuntimeError, TypeError, ValueError):
        raise InstalledSmokeError("installed smoke failed") from None
    try:
        temporary_root = Path(temporary_directory.name)
        os.chmod(temporary_root, 0o700)
        source_snapshot = temporary_root / "source-archive"
        plugin_snapshot = temporary_root / "plugin-root"
        try:
            _capture_private_snapshot(source_archive, source_snapshot)
            _capture_private_snapshot(plugin_root, plugin_snapshot)
            _load_release_helper().verify_release_parity(source_snapshot, plugin_snapshot)
        except (InstalledSmokeError, OSError, RuntimeError, TypeError, UnicodeError, ValueError):
            raise InstalledSmokeError("installed smoke failed") from None
        yield source_snapshot, plugin_snapshot
    finally:
        temporary_directory.cleanup()


def _canonical_sha256(value: object) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def load_installed_smoke_sources(plugin_root: Path) -> dict[str, object]:
    """Load one closed, self-hashed source group from the installed root."""

    try:
        root = plugin_root.resolve(strict=True)
        path = root / SMOKE_SOURCES_RELATIVE
        if not (
            root.is_dir()
            and path.is_file()
            and not path.is_symlink()
            and path.resolve(strict=True).is_relative_to(root)
            and path.stat().st_size <= MAX_SMOKE_SOURCES_BYTES
        ):
            raise InstalledSmokeError
        value = json.loads(path.read_text(encoding="utf-8"))
        if not (
            isinstance(value, dict)
            and set(value)
            == {"schema_version", "sources", "source_sha256", "aggregate_sha256"}
            and value.get("schema_version") == "vacancy-first-smoke-sources-v1"
            and isinstance(value.get("sources"), dict)
            and set(value["sources"]) == {"research", "dossier", "provider"}
            and all(isinstance(item, dict) for item in value["sources"].values())
            and isinstance(value.get("source_sha256"), dict)
            and set(value["source_sha256"]) == {"research", "dossier", "provider"}
            and all(
                isinstance(item, str) and SHA256_PATTERN.fullmatch(item)
                for item in value["source_sha256"].values()
            )
            and isinstance(value.get("aggregate_sha256"), str)
            and SHA256_PATTERN.fullmatch(value["aggregate_sha256"])
        ):
            raise InstalledSmokeError
        current_hashes = {
            name: _canonical_sha256(value["sources"][name])
            for name in ("research", "dossier", "provider")
        }
        if current_hashes != value["source_sha256"]:
            raise InstalledSmokeError
        aggregate = hashlib.sha256(
            b"".join(
                name.encode("utf-8")
                + b"\0"
                + current_hashes[name].encode("ascii")
                + b"\n"
                for name in sorted(current_hashes)
            )
        ).hexdigest()
        if aggregate != value["aggregate_sha256"]:
            raise InstalledSmokeError
        return value
    except (OSError, RuntimeError, TypeError, UnicodeError, ValueError, json.JSONDecodeError):
        raise InstalledSmokeError("installed smoke sources are invalid") from None


def _descendant(path: object, root: Path) -> bool:
    try:
        return Path(str(path)).resolve(strict=True).is_relative_to(root)
    except (OSError, RuntimeError, TypeError, ValueError):
        return False


def load_installed_product_modules(
    plugin_root: Path, module_names: tuple[str, ...] = DEFAULT_MODULES
) -> dict[str, ModuleType]:
    """Load product modules only from the exact supplied installed scripts root."""

    loaded: dict[str, ModuleType] = {}
    unique_names: list[str] = []
    saved_modules: dict[str, ModuleType] = {}
    previous_path = list(sys.path)
    try:
        root = plugin_root.resolve(strict=True)
        scripts = (root / "scripts").resolve(strict=True)
        if not (
            root.is_dir()
            and scripts.is_dir()
            and scripts.is_relative_to(root)
            and not plugin_root.is_symlink()
            and not (root / "scripts").is_symlink()
            and isinstance(module_names, tuple)
            and module_names
        ):
            raise InstalledSmokeError
        installed_stems = {
            path.stem
            for path in scripts.glob("*.py")
            if path.is_file() and not path.is_symlink()
        }
        for name in module_names:
            if not isinstance(name, str) or MODULE_NAME_PATTERN.fullmatch(name) is None:
                raise InstalledSmokeError
            path = scripts / f"{name}.py"
            if (
                name not in installed_stems
                or not path.is_file()
                or path.is_symlink()
                or not path.resolve(strict=True).is_relative_to(scripts)
            ):
                raise InstalledSmokeError
        for name in installed_stems:
            existing = sys.modules.pop(name, None)
            if isinstance(existing, ModuleType):
                saved_modules[name] = existing
        sys.path.insert(0, str(scripts))
        for index, name in enumerate(module_names):
            path = scripts / f"{name}.py"
            unique_name = f"_pgc_installed_smoke_{index}_{name}"
            specification = importlib.util.spec_from_file_location(unique_name, path)
            if specification is None or specification.loader is None:
                raise InstalledSmokeError
            module = importlib.util.module_from_spec(specification)
            sys.modules[unique_name] = module
            unique_names.append(unique_name)
            specification.loader.exec_module(module)
            loaded[name] = module

        audited_names = installed_stems | set(unique_names)
        for name in audited_names:
            module = sys.modules.get(name)
            if module is not None and not _descendant(getattr(module, "__file__", None), root):
                raise InstalledSmokeError
        for module in loaded.values():
            if not _descendant(getattr(module, "__file__", None), root):
                raise InstalledSmokeError
            for value in vars(module).values():
                if (
                    isinstance(value, ModuleType)
                    and getattr(value, "__name__", "") in installed_stems
                    and not _descendant(getattr(value, "__file__", None), root)
                ):
                    raise InstalledSmokeError
        return loaded
    except (ImportError, OSError, RuntimeError, TypeError, ValueError):
        raise InstalledSmokeError("installed smoke import boundary failed") from None
    finally:
        sys.path[:] = previous_path
        for name in unique_names:
            sys.modules.pop(name, None)
        for name in tuple(sys.modules):
            if name not in saved_modules and name in locals().get("installed_stems", set()):
                sys.modules.pop(name, None)
        sys.modules.update(saved_modules)


def _source_group(
    sources: Mapping[str, object],
    modules: Mapping[str, ModuleType],
    locale: str,
    *,
    recurrent: bool = True,
    provider_mode: str = "absent",
) -> dict[str, object]:
    research = copy.deepcopy(sources["research"])
    dossier = copy.deepcopy(sources["dossier"])
    provider = copy.deepcopy(sources["provider"])
    research["locale"] = locale
    dossier["locale"] = locale
    provider["locale"] = locale
    if recurrent:
        research["vacancies"][0]["requirements"][0]["signal"] = "terraform"
    if provider_mode == "absent":
        provider = None
    elif provider_mode == "empty":
        for option in provider["options"]:
            option["covered_signals"] = []
    market = modules["build_career_market_learning_dossier_v2"].build_market_dossier_v2(
        research, dossier
    )
    return {
        "research": research,
        "dossier": dossier,
        "market": market,
        "provider": provider,
    }


def _unavailable_group(
    sources: Mapping[str, object], modules: Mapping[str, ModuleType], locale: str
) -> dict[str, object]:
    group = _source_group(sources, modules, locale)
    research = group["research"]
    research["state"] = "market_evidence_unavailable"
    research["search_limit"].update(
        {
            "limit_reason": "market_evidence_unavailable",
            "limitation": "Synthetic smoke unavailability.",
        }
    )
    research["employers"] = []
    research["vacancies"] = []
    group["market"] = modules[
        "build_career_market_learning_dossier_v2"
    ].build_market_dossier_v2(research, group["dossier"])
    return group


def _selection_payload(
    market: Mapping[str, object], relation: str, provider_ordinal: str | None = None
) -> dict[str, object]:
    vacancies = market["vacancies"]
    index = next(
        position
        for position, vacancy in enumerate(vacancies)
        if isinstance(vacancy, Mapping) and vacancy.get("vacancy_id") == "V-003"
    )
    return {
        "selected_vacancy_ordinal": f"V{index + 1}",
        "selected_signal": "terraform",
        "relation": relation,
        "selected_provider_ordinal": provider_ordinal,
    }


def _build_case(
    name: str,
    locale: str,
    sources: Mapping[str, object],
    modules: Mapping[str, ModuleType],
) -> dict[str, object]:
    if name == "unavailable":
        group = _unavailable_group(sources, modules, locale)
    else:
        provider_mode = (
            "present" if name in {"provider_choice", "knowledge"} else "absent"
        )
        group = _source_group(
            sources,
            modules,
            locale,
            recurrent=name != "insufficient_recurrence",
            provider_mode=provider_mode,
        )
    payload = None
    if name not in {"unavailable", "selection_required"}:
        payload = _selection_payload(
            group["market"],
            RELATION_BY_CASE[name],
            "L1" if name == "knowledge" else None,
        )
    response = modules["build_candidate_gap_response_v1"].build_candidate_gap_response_v1(
        group["research"], group["market"], payload, group["provider"]
    )
    assessment = modules[
        "build_candidate_gap_assessment_v1"
    ].build_candidate_gap_assessment_v1(
        group["research"],
        group["dossier"],
        group["market"],
        response,
        group["provider"],
    )
    eligibility = modules[
        "build_career_next_action_eligibility_v1"
    ].build_career_next_action_eligibility_v1(
        group["research"],
        group["dossier"],
        group["market"],
        response,
        assessment,
        group["provider"],
    )
    learning = modules[
        "build_career_learning_decision_v3"
    ].build_career_learning_decision_v3(
        group["research"],
        group["dossier"],
        group["market"],
        response,
        assessment,
        eligibility,
        group["provider"],
    )
    validators = (
        modules["validate_candidate_gap_response_v1"].validate_candidate_gap_response_v1(
            response, group["research"], group["market"], group["provider"]
        ),
        modules["validate_candidate_gap_assessment_v1"].validate_candidate_gap_assessment_v1(
            assessment,
            group["research"],
            group["dossier"],
            group["market"],
            response,
            group["provider"],
        ),
        modules[
            "validate_career_next_action_eligibility_v1"
        ].validate_career_next_action_eligibility_v1(
            eligibility,
            group["research"],
            group["dossier"],
            group["market"],
            response,
            assessment,
            group["provider"],
        ),
        modules[
            "validate_career_learning_decision_v3"
        ].validate_career_learning_decision_v3(
            learning,
            group["research"],
            group["dossier"],
            group["market"],
            response,
            assessment,
            eligibility,
            group["provider"],
        ),
    )
    if any(errors for errors in validators):
        raise InstalledSmokeError
    return {
        **group,
        "response": response,
        "assessment": assessment,
        "eligibility": eligibility,
        "learning": learning,
    }


class _OnePassMapping(Mapping[str, object]):
    def __init__(self, value: dict[str, object]):
        self._value = value
        self.exhausted = False

    def __getitem__(self, key: str) -> object:
        if self.exhausted:
            raise RuntimeError("private")
        return self._value[key]

    def __iter__(self):
        return iter(self._value)

    def __len__(self) -> int:
        return len(self._value)

    def items(self):
        if self.exhausted:
            raise RuntimeError("private")

        def captured():
            try:
                yield from self._value.items()
            finally:
                self.exhausted = True

        return captured()


class _RaisingMapping(Mapping[str, object]):
    def __getitem__(self, key: str) -> object:
        raise RuntimeError("private")

    def __iter__(self):
        raise RuntimeError("private")

    def __len__(self) -> int:
        raise RuntimeError("private")


def _expect_generic_rejection(callable_value: object, diagnostic: str) -> None:
    try:
        callable_value()
    except (RuntimeError, ValueError) as error:
        if str(error) != diagnostic or error.__cause__ is not None:
            raise InstalledSmokeError
    else:
        raise InstalledSmokeError


def _historical_v1_alignment(
    sources: Mapping[str, object], modules: Mapping[str, ModuleType]
) -> dict[str, object]:
    configured = {
        "python": ("verified_match", ["E-001"]),
        "kubernetes": ("candidate_reported_match", ["E-003"]),
        "terraform": ("adjacent_evidence", ["E-004"]),
        "observability": ("unknown", []),
        "linux": ("explicit_gap", ["E-003"]),
    }
    research = sources["research"]
    dossier = sources["dossier"]
    signals = {
        requirement["signal"]
        for vacancy in research["vacancies"]
        for requirement in vacancy["requirements"]
    }
    snapshots = modules["derive_candidate_market_alignment_v2"]
    return {
        "schema_version": "candidate-market-alignment-v1",
        "research_snapshot": snapshots.snapshot_for_market_dossier(research),
        "executive_dossier_snapshot": snapshots.snapshot_for_dossier(dossier),
        "signal_bindings": [
            {
                "signal": signal,
                "support_state": configured[signal][0],
                "evidence_ids": configured[signal][1],
            }
            for signal in sorted(signals)
        ],
        "privacy_boundary": "identity_free_evidence_references_only",
    }


def _historical_v1_decisions(market: Mapping[str, object]) -> list[dict[str, object]]:
    vacancy_ids = [row["vacancy_id"] for row in market["vacancies"]]
    evidence_id = next(
        (
            evidence_id
            for row in market["matrix_rows"]
            for evidence_id in row["evidence_ids"]
        ),
        "E-001",
    )
    provider_source = {
        "provider": "HashiCorp",
        "option": "Terraform Associate",
        "source_title": "HashiCorp Certified: Terraform Associate",
        "source_date": market["as_of_date"],
        "source_state": "active",
        "url": "https://developer.hashicorp.com/certifications/infrastructure-automation",
        "geography": "unknown: official page does not establish Mexico eligibility",
        "availability": "active: official provider page is available",
        "current_cost": "unknown: official page does not state the current fee",
        "currency": "unknown: no verified currency",
        "tax": "unknown: tax treatment is not stated",
        "duration": "provider duration unknown: official page does not state exam duration",
        "prerequisite": "unknown: official page does not state prerequisites",
        "renewal": "unknown: official page does not state renewal",
        "maintenance": "unknown: official page does not state maintenance",
        "unknowns": "Mexico eligibility and preparation time are not stated",
    }
    common = {
        "target_role": "Senior SRE / Platform Engineer",
        "source_gap_ids": [evidence_id],
        "vacancy_ids": vacancy_ids[:2],
        "market_evidence_state": "current dated vacancy evidence",
        "outcome_boundary": "not_an_interview_offer_salary_or_roi_prediction",
        "draft_only": True,
        "no_external_action": True,
    }
    return [
        {
            **common,
            "decision_rank": 1,
            "gap_type": "proof",
            "option_type": "portfolio_project",
            "option_name": "Terraform and observability proof artifact",
            "provider_or_owner": "candidate-owned proof project",
            "cost_time_band": "unknown: candidate effort requires separate confirmation",
            "expected_signal_boundary": "bounded hypothesis: creates inspectable evidence without promising a hiring outcome",
            "portfolio_or_no_learning_alternative": "Complete one bounded proof artifact before buying another credential.",
            "overbuying_risk": "Avoid certificate collecting before one higher-signal artifact is complete.",
            "decision": "do_now",
            "decision_basis": "Repeated vacancy evidence supports a candidate-owned proof artifact before a purchase.",
            "next_action_gate": "No external action; exact authorization is required before publication, sharing, or messaging.",
            "provider_source": None,
        },
        {
            **common,
            "decision_rank": 2,
            "gap_type": "knowledge",
            "option_type": "course",
            "option_name": "Terraform Associate study path",
            "provider_or_owner": "HashiCorp",
            "cost_time_band": "unknown: current cost and candidate effort require separate confirmation",
            "expected_signal_boundary": "bounded hypothesis: may corroborate knowledge without promising a hiring outcome",
            "portfolio_or_no_learning_alternative": "Build a bounded Terraform proof artifact before enrolling.",
            "overbuying_risk": "Avoid paying before a cheaper proof comparison is reviewed.",
            "decision": "research_first",
            "decision_basis": "Repeated vacancy evidence supports research, but official provider cost and eligibility remain unknown.",
            "next_action_gate": "No external action; purchase or enrollment requires exact authorization after source review.",
            "provider_source": provider_source,
        },
        {
            **common,
            "decision_rank": 3,
            "gap_type": "low_return",
            "option_type": "no_learning_yet",
            "option_name": "Finish the current proof artifact first",
            "provider_or_owner": "none",
            "cost_time_band": "unknown: candidate effort requires separate confirmation",
            "expected_signal_boundary": "bounded hypothesis: protects time for higher-signal proof without promising a hiring outcome",
            "portfolio_or_no_learning_alternative": "Use the existing proof artifact as the lower-cost alternative.",
            "overbuying_risk": "Avoid starting a course before the evidence gap is reviewed again.",
            "decision": "do_now",
            "decision_basis": "Candidate-owned evidence is a higher-priority next move than generic learning.",
            "next_action_gate": "No external action; exact authorization is required before publication, sharing, or messaging.",
            "provider_source": None,
        },
    ]


def installed_historical_render_snapshots(
    sources: Mapping[str, object], modules: Mapping[str, ModuleType]
) -> dict[str, dict[str, object]]:
    """Recompute v1, v2, and no-market render bytes from installed sources."""

    research = sources["research"]
    dossier = sources["dossier"]
    provider = sources["provider"]
    alignment = _historical_v1_alignment(sources, modules)
    market_v1 = modules["build_career_market_learning_dossier"].build_market_dossier(
        research, dossier, alignment
    )
    learning_v1 = modules["build_career_learning_decision"].build_learning_bundle(
        research, market_v1, dossier, _historical_v1_decisions(market_v1)
    )
    market_v2 = modules[
        "build_career_market_learning_dossier_v2"
    ].build_market_dossier_v2(research, dossier)
    requests_v2 = [
        {
            "decision_rank": rank,
            "decision_code": code,
            "source_signals": ["terraform"],
            "provider_option_id": provider_option_id,
        }
        for rank, code, provider_option_id in (
            (1, "build_bounded_proof", None),
            (2, "run_validation_lab", None),
            (3, "research_provider_option", "LP-001"),
            (4, "defer_learning_purchase", None),
        )
    ]
    learning_v2 = modules["build_career_learning_decision_v2"].build_learning_bundle_v2(
        research, market_v2, dossier, provider, requests_v2
    )
    renderer = modules["render_executive_career_dossier_v2"].render_dossier_html
    rendered = {
        "v1": renderer(
            dossier,
            market_v1,
            market_research=research,
            market_alignment=alignment,
            learning_decision=learning_v1,
        ),
        "v2": renderer(
            dossier,
            market_v2,
            market_research=research,
            learning_decision=learning_v2,
            provider_research=provider,
        ),
        "no_market": renderer(dossier),
    }
    return {
        name: {
            "bytes": len(value.encode("utf-8")),
            "sha256": hashlib.sha256(value.encode("utf-8")).hexdigest(),
        }
        for name, value in rendered.items()
    }


def _semantic_matrix_receipt(
    accepted_matrix: tuple[tuple[str, str, bool], ...],
    rejected_matrix: tuple[tuple[str, str, bool], ...],
) -> dict[str, object]:
    def collect(
        matrix: tuple[tuple[str, str, bool], ...],
        expected_groups: tuple[str, ...],
        expected_count: int,
    ) -> tuple[tuple[str, ...], tuple[str, ...]]:
        case_ids: list[str] = []
        groups: list[str] = []
        for group, case, passed in matrix:
            if passed is not True:
                raise InstalledSmokeError
            case_id = f"{group}.{case}"
            if case_id in case_ids:
                raise InstalledSmokeError
            case_ids.append(case_id)
            if group not in groups:
                groups.append(group)
        if len(case_ids) != expected_count or tuple(groups) != expected_groups:
            raise InstalledSmokeError
        return tuple(case_ids), tuple(groups)

    accepted_cases, accepted_groups = collect(
        accepted_matrix, ACCEPTED_GROUPS, 39
    )
    rejected_cases, rejected_groups = collect(
        rejected_matrix, REJECTED_GROUPS, 9
    )
    return {
        "matrix_version": "vacancy-first-installed-smoke-v1",
        "accepted": len(accepted_cases),
        "rejected": len(rejected_cases),
        "accepted_cases": accepted_cases,
        "rejected_cases": rejected_cases,
        "accepted_groups": accepted_groups,
        "rejected_groups": rejected_groups,
    }


def run_installed_semantic_matrix(
    plugin_root: Path, modules: Mapping[str, ModuleType]
) -> dict[str, object]:
    """Run the complete closed Task 7 matrix against installed modules only."""

    try:
        source_document = load_installed_smoke_sources(plugin_root)
        sources = source_document["sources"]
        built: dict[tuple[str, str], dict[str, object]] = {}
        action_matrix_results: dict[str, bool] = {}
        for name, state, basis, action, learning_count in CASE_RULES:
            case = _build_case(name, "es", sources, modules)
            built[(name, "es")] = case
            eligibility = case["eligibility"]
            decisions = case["learning"]["decisions"]
            action_matrix_results[name] = (
                eligibility["state"] == state
                and eligibility["decision_basis_code"] == basis
                and eligibility["recommended_next_action"] == action
                and len(decisions) == learning_count
                and int(action in LEARNING_ACTIONS) == learning_count
            )
            if not action_matrix_results[name]:
                raise InstalledSmokeError
        eligibility_copy = modules["build_career_next_action_eligibility_v1"].COPY
        learning_copy = modules["project_career_learning_decision_v3"].COPY
        required_actions = {row[3] for row in CASE_RULES}
        localized_copy_results: dict[str, tuple[bool, bool]] = {}
        for locale in ("es", "en"):
            locale_copy = eligibility_copy.get(locale)
            projected_copy = learning_copy.get(locale)
            action_copy_valid = (
                isinstance(locale_copy, Mapping)
                and isinstance(locale_copy.get("states"), Mapping)
                and isinstance(locale_copy.get("actions"), Mapping)
                and required_actions <= set(locale_copy["actions"])
                and all(
                    isinstance(value, str) and value.strip()
                    for value in locale_copy["states"].values()
                )
            )
            learning_copy_valid = (
                isinstance(projected_copy, Mapping)
                and LEARNING_ACTIONS <= set(projected_copy["decision_bases"])
                and all(
                    isinstance(value, str) and value.strip()
                    for value in projected_copy["decision_bases"].values()
                )
            )
            localized_copy_results[locale] = (
                action_copy_valid,
                learning_copy_valid,
            )
            if not action_copy_valid or not learning_copy_valid:
                raise InstalledSmokeError
        if (
            eligibility_copy["es"]["actions"] == eligibility_copy["en"]["actions"]
            or learning_copy["es"]["decision_bases"]
            == learning_copy["en"]["decision_bases"]
        ):
            raise InstalledSmokeError

        public_v1_sources = copy.deepcopy(sources)
        public_v1_sources["research"]["vacancies"] = sorted(
            public_v1_sources["research"]["vacancies"],
            key=lambda vacancy: vacancy.get("vacancy_id") != "V-003",
        )
        public_v1 = _source_group(
            public_v1_sources, modules, "es", recurrent=False
        )
        public_v1_payload = {
            "selected_vacancy_ordinal": "V1",
            "selected_signal": "terraform",
            "relation": "proof_gap",
            "selected_provider_ordinal": None,
        }
        public_v1_response = modules[
            "build_candidate_gap_response_v1"
        ].build_candidate_gap_response_v1(
            public_v1["research"],
            public_v1["market"],
            public_v1_payload,
            public_v1["provider"],
        )
        public_v1_assessment = modules[
            "build_candidate_gap_assessment_v1"
        ].build_candidate_gap_assessment_v1(
            public_v1["research"],
            public_v1["dossier"],
            public_v1["market"],
            public_v1_response,
            public_v1["provider"],
        )
        public_v1_valid = (
            modules[
                "validate_candidate_gap_response_v1"
            ].validate_candidate_gap_response_v1(
                public_v1_response,
                public_v1["research"],
                public_v1["market"],
                public_v1["provider"],
            )
            == []
            and modules[
                "validate_candidate_gap_assessment_v1"
            ].validate_candidate_gap_assessment_v1(
                public_v1_assessment,
                public_v1["research"],
                public_v1["dossier"],
                public_v1["market"],
                public_v1_response,
                public_v1["provider"],
            )
            == []
        )
        if not (
            public_v1_valid
            and public_v1_response["selected_vacancy_ordinal"] == "V1"
            and public_v1_assessment["selected_vacancy_id"] == "V-003"
            and "V-003" not in json.dumps(public_v1_response, sort_keys=True)
        ):
            raise InstalledSmokeError

        proof = built[("proof", "es")]
        insufficient = built[("insufficient_recurrence", "es")]
        if not (
            proof["assessment"]["selected_vacancy_id"] == "V-003"
            and "V-003" not in json.dumps(proof["response"], sort_keys=True)
            and insufficient["eligibility"]["recurrence"] == "1/5"
            and insufficient["learning"]["decisions"] == []
            and proof["eligibility"]["recurrence"] == "2/5"
            and len(proof["learning"]["decisions"]) == 1
        ):
            raise InstalledSmokeError
        expected_nonlearning = {
            "supported": "prepare_private_vacancy_packet",
            "gap_unknown": "confirm_gap_relation",
            "experience": "prepare_private_vacancy_packet",
        }
        if any(
            built[(name, "es")]["eligibility"]["recommended_next_action"] != action
            or built[(name, "es")]["learning"]["decisions"]
            for name, action in expected_nonlearning.items()
        ):
            raise InstalledSmokeError

        absent = built[("provider_evidence", "es")]
        choice = built[("provider_choice", "es")]
        selected = built[("knowledge", "es")]
        empty_group = _source_group(
            sources, modules, "es", provider_mode="empty"
        )
        empty_payload = _selection_payload(empty_group["market"], "knowledge_gap")
        empty_response = modules[
            "build_candidate_gap_response_v1"
        ].build_candidate_gap_response_v1(
            empty_group["research"], empty_group["market"], empty_payload, empty_group["provider"]
        )
        empty_assessment = modules[
            "build_candidate_gap_assessment_v1"
        ].build_candidate_gap_assessment_v1(
            empty_group["research"], empty_group["dossier"], empty_group["market"], empty_response, empty_group["provider"]
        )
        empty_eligibility = modules[
            "build_career_next_action_eligibility_v1"
        ].build_career_next_action_eligibility_v1(
            empty_group["research"], empty_group["dossier"], empty_group["market"], empty_response, empty_assessment, empty_group["provider"]
        )
        if not (
            absent["eligibility"]["state"] == "provider_evidence_required"
            and empty_eligibility["state"] == "provider_evidence_required"
            and choice["eligibility"]["state"] == "provider_selection_required"
            and selected["eligibility"]["selected_provider_option_id"] == "LP-001"
        ):
            raise InstalledSmokeError

        row = proof["learning"]["decisions"][0]
        if not (
            row["requirement_ids"] == ["V-001-R-01", "V-003-R-01"]
            and row["vacancy_ids"] == ["V-001", "V-003"]
            and row["claim_ids"] == ["C-002"]
            and row["source_evidence_ids"] == ["E-004"]
            and all(
                isinstance(proof["learning"].get(field), str)
                and "sha256-" in proof["learning"][field]
                for field in (
                    "source_research_snapshot",
                    "source_dossier_snapshot",
                    "source_alignment_snapshot",
                    "source_market_snapshot",
                    "source_gap_response_snapshot",
                    "source_gap_assessment_snapshot",
                    "source_next_action_eligibility_snapshot",
                )
            )
        ):
            raise InstalledSmokeError

        rendered = modules["render_executive_career_dossier_v2"].render_dossier_html(
            proof["dossier"],
            proof["market"],
            market_research=proof["research"],
            learning_decision=proof["learning"],
            provider_research=proof["provider"],
            gap_response=proof["response"],
            gap_assessment=proof["assessment"],
            next_action_eligibility=proof["eligibility"],
        )
        if not (
            rendered.count('class="card span-12 weekly-decision"') == 1
            and rendered.count('class="weekly-decision-action"') == 1
            and 'aria-labelledby="weekly-decision-title weekly-decision-vacancy"' in rendered
            and 'aria-describedby="weekly-decision-evidence weekly-decision-boundary"' in rendered
        ):
            raise InstalledSmokeError
        private_values = (
            "LP-001",
            "V-003-R-01",
            "https://developer.hashicorp.com",
            "Synthetic test requirement.",
            "proof_gap_recurrent",
        )
        private_disclosure_rejected = not any(
            value in rendered for value in private_values
        )
        if not private_disclosure_rejected:
            raise InstalledSmokeError

        lp002_group = _source_group(
            sources, modules, "es", provider_mode="present"
        )
        lp002_group["provider"]["options"][0]["option"] = "A learning option"
        lp002_group["provider"]["options"][1]["option"] = "B learning option"
        lp002_group["provider"]["options"][1]["covered_signals"] = ["terraform"]
        lp002_payload = _selection_payload(
            lp002_group["market"], "knowledge_gap", "L2"
        )
        lp002_response = modules[
            "build_candidate_gap_response_v1"
        ].build_candidate_gap_response_v1(
            lp002_group["research"],
            lp002_group["market"],
            lp002_payload,
            lp002_group["provider"],
        )
        lp002_assessment = modules[
            "build_candidate_gap_assessment_v1"
        ].build_candidate_gap_assessment_v1(
            lp002_group["research"],
            lp002_group["dossier"],
            lp002_group["market"],
            lp002_response,
            lp002_group["provider"],
        )
        lp002_eligibility = modules[
            "build_career_next_action_eligibility_v1"
        ].build_career_next_action_eligibility_v1(
            lp002_group["research"],
            lp002_group["dossier"],
            lp002_group["market"],
            lp002_response,
            lp002_assessment,
            lp002_group["provider"],
        )
        lp002_learning = modules[
            "build_career_learning_decision_v3"
        ].build_career_learning_decision_v3(
            lp002_group["research"],
            lp002_group["dossier"],
            lp002_group["market"],
            lp002_response,
            lp002_assessment,
            lp002_eligibility,
            lp002_group["provider"],
        )
        lp002_valid = (
            lp002_response["selected_provider_ordinal"] == "L2"
            and lp002_assessment["selected_provider_option_id"] == "LP-002"
            and lp002_eligibility["selected_provider_option_id"] == "LP-002"
            and lp002_learning["decisions"][0]["provider_option_id"] == "LP-002"
        )
        provider_displacement_rejected = modules[
            "validate_career_learning_decision_v3"
        ].validate_career_learning_decision_v3(
            selected["learning"],
            lp002_group["research"],
            lp002_group["dossier"],
            lp002_group["market"],
            lp002_response,
            lp002_assessment,
            lp002_eligibility,
            lp002_group["provider"],
        ) == ["career learning decision v3 does not match validated sources"]
        if not lp002_valid or not provider_displacement_rejected:
            raise InstalledSmokeError

        forged = copy.deepcopy(proof["eligibility"])
        forged["recommended_next_action"] = "run_validation_lab"
        _expect_generic_rejection(
            lambda: modules["build_career_learning_decision_v3"].build_career_learning_decision_v3(
                proof["research"], proof["dossier"], proof["market"], proof["response"], proof["assessment"], forged
            ),
            "career learning decision v3 is invalid",
        )
        forged_sources_rejected = True
        crossed = built[("insufficient_recurrence", "es")]
        crossed_sources_rejected = modules[
            "validate_career_learning_decision_v3"
        ].validate_career_learning_decision_v3(
            proof["learning"],
            crossed["research"],
            crossed["dossier"],
            crossed["market"],
            proof["response"],
            proof["assessment"],
            proof["eligibility"],
        ) == ["career learning decision v3 does not match validated sources"]
        if not crossed_sources_rejected:
            raise InstalledSmokeError

        mutable = _OnePassMapping(copy.deepcopy(proof["eligibility"]))
        mutable_result = modules[
            "build_career_learning_decision_v3"
        ].build_career_learning_decision_v3(
            proof["research"], proof["dossier"], proof["market"], proof["response"], proof["assessment"], mutable
        )
        mutable_sources_rejected = mutable.exhausted and mutable_result == proof["learning"]
        if not mutable_sources_rejected:
            raise InstalledSmokeError
        _expect_generic_rejection(
            lambda: modules["build_career_learning_decision_v3"].build_career_learning_decision_v3(
                proof["research"], proof["dossier"], proof["market"], proof["response"], proof["assessment"], {"text": "x" * 4097}
            ),
            "career learning decision v3 is invalid",
        )
        oversized_sources_rejected = True
        _expect_generic_rejection(
            lambda: modules["build_career_learning_decision_v3"].build_career_learning_decision_v3(
                proof["research"], proof["dossier"], proof["market"], proof["response"], proof["assessment"], _RaisingMapping()
            ),
            "career learning decision v3 is invalid",
        )
        exceptional_sources_rejected = True

        historical_snapshots = installed_historical_render_snapshots(sources, modules)
        historical_bytes_valid = historical_snapshots == HISTORICAL_RENDER_SNAPSHOTS
        if not historical_bytes_valid:
            raise InstalledSmokeError

        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            paths = {}
            for name in (
                "dossier", "market", "research", "learning", "response", "assessment", "eligibility"
            ):
                path = root / f"{name}.json"
                path.write_text(json.dumps(proof[name], ensure_ascii=False), encoding="utf-8")
                paths[name] = path
            writer_output = root / "writer.html"
            try:
                modules["render_executive_career_dossier_v2"].write_dossier_html(
                    paths["dossier"],
                    writer_output,
                    market_dossier_path=paths["market"],
                    market_research_path=paths["research"],
                    learning_decision_path=paths["learning"],
                    gap_response_path=paths["response"],
                )
            except Exception:
                pass
            else:
                raise InstalledSmokeError
            writer_output_rejected = not writer_output.exists()
            if not writer_output_rejected:
                raise InstalledSmokeError
            cli_output = root / "cli.html"
            result = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(plugin_root / "scripts/render_executive_career_dossier_v2.py"),
                    str(paths["dossier"]),
                    "--output",
                    str(cli_output),
                    "--market-dossier",
                    str(paths["market"]),
                    "--market-research",
                    str(paths["research"]),
                    "--learning-decision",
                    str(paths["learning"]),
                    "--gap-response",
                    str(paths["response"]),
                ],
                cwd=root,
                capture_output=True,
                text=True,
                check=False,
                timeout=60,
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            )
            cli_output_rejected = (
                result.returncode == 2
                and not cli_output.exists()
                and "Traceback" not in result.stderr
            )
            if not cli_output_rejected:
                raise InstalledSmokeError

        nonlearning_results = {
            name: (
                built[(name, "es")]["eligibility"]["recommended_next_action"]
                == action,
                built[(name, "es")]["learning"]["decisions"] == [],
            )
            for name, action in expected_nonlearning.items()
        }
        exact_unions_valid = (
            row["requirement_ids"] == ["V-001-R-01", "V-003-R-01"]
            and row["vacancy_ids"] == ["V-001", "V-003"]
            and row["claim_ids"] == ["C-002"]
            and row["source_evidence_ids"] == ["E-004"]
        )
        exact_snapshots_valid = all(
            isinstance(proof["learning"].get(field), str)
            and "sha256-" in proof["learning"][field]
            for field in (
                "source_research_snapshot",
                "source_dossier_snapshot",
                "source_alignment_snapshot",
                "source_market_snapshot",
                "source_gap_response_snapshot",
                "source_gap_assessment_snapshot",
                "source_next_action_eligibility_snapshot",
            )
        )
        dom_aria_valid = (
            rendered.count('class="card span-12 weekly-decision"') == 1
            and rendered.count('class="weekly-decision-action"') == 1
            and 'aria-labelledby="weekly-decision-title weekly-decision-vacancy"'
            in rendered
            and 'aria-describedby="weekly-decision-evidence weekly-decision-boundary"'
            in rendered
        )
        accepted_matrix = (
            ("response_mapping", "public_v1_is_persisted", public_v1_response["selected_vacancy_ordinal"] == "V1"),
            ("response_mapping", "public_v1_resolves_private_v003", public_v1_assessment["selected_vacancy_id"] == "V-003"),
            ("response_mapping", "private_v003_is_not_persisted_publicly", "V-003" not in json.dumps(public_v1_response, sort_keys=True)),
            ("response_mapping", "response_and_assessment_validate", public_v1_valid),
            ("recurrence_routes", "one_of_five_is_exact", insufficient["eligibility"]["recurrence"] == "1/5"),
            ("recurrence_routes", "one_of_five_routes_private_packet", insufficient["eligibility"]["recommended_next_action"] == "prepare_private_vacancy_packet"),
            ("recurrence_routes", "one_of_five_has_zero_learning", insufficient["learning"]["decisions"] == []),
            ("recurrence_routes", "two_of_five_is_exact", proof["eligibility"]["recurrence"] == "2/5"),
            ("recurrence_routes", "two_of_five_proof_has_one_learning", len(proof["learning"]["decisions"]) == 1),
            ("nonlearning_routes", "supported_action", nonlearning_results["supported"][0]),
            ("nonlearning_routes", "supported_zero_learning", nonlearning_results["supported"][1]),
            ("nonlearning_routes", "unknown_action", nonlearning_results["gap_unknown"][0]),
            ("nonlearning_routes", "unknown_zero_learning", nonlearning_results["gap_unknown"][1]),
            ("nonlearning_routes", "experience_action", nonlearning_results["experience"][0]),
            ("nonlearning_routes", "experience_zero_learning", nonlearning_results["experience"][1]),
            ("provider_lifecycle", "provider_absent", absent["eligibility"]["state"] == "provider_evidence_required"),
            ("provider_lifecycle", "provider_empty", empty_eligibility["state"] == "provider_evidence_required"),
            ("provider_lifecycle", "provider_choice", choice["eligibility"]["state"] == "provider_selection_required"),
            ("provider_lifecycle", "l1_selects_lp001", selected["eligibility"]["selected_provider_option_id"] == "LP-001"),
            ("provider_lifecycle", "l2_is_public_selection", lp002_response["selected_provider_ordinal"] == "L2"),
            ("provider_lifecycle", "l2_resolves_lp002_chain", lp002_valid),
            *(
                ("action_matrix_es", name, action_matrix_results[name])
                for name, *_ in CASE_RULES
            ),
            ("action_matrix_en", "all_actions_have_copy", localized_copy_results["en"][0] and eligibility_copy["es"]["actions"] != eligibility_copy["en"]["actions"]),
            ("action_matrix_en", "all_learning_bases_have_copy", localized_copy_results["en"][1] and learning_copy["es"]["decision_bases"] != learning_copy["en"]["decision_bases"]),
            ("exact_unions_snapshots", "exact_provenance_unions", exact_unions_valid),
            ("exact_unions_snapshots", "all_source_snapshots", exact_snapshots_valid),
            ("dom_aria", "single_named_weekly_card", dom_aria_valid),
            ("historical_bytes", "v1_v2_no_market_pinned", historical_bytes_valid),
        )
        rejected_matrix = (
            ("provider_displacement", "lp002_rejects_prior_lp001_chain", provider_displacement_rejected),
            ("private_disclosure", "private_values_absent", private_disclosure_rejected),
            ("forged_sources", "forged_action_rejected", forged_sources_rejected),
            ("crossed_sources", "crossed_group_rejected", crossed_sources_rejected),
            ("mutable_sources", "one_pass_input_is_not_reread", mutable_sources_rejected),
            ("oversized_sources", "oversized_group_rejected", oversized_sources_rejected),
            ("exceptional_sources", "exceptional_mapping_rejected", exceptional_sources_rejected),
            ("writer_output", "invalid_group_leaves_no_output", writer_output_rejected),
            ("cli_output", "invalid_group_leaves_no_output", cli_output_rejected),
        )
        return _semantic_matrix_receipt(accepted_matrix, rejected_matrix)
    except (InstalledSmokeError, OSError, RuntimeError, TypeError, ValueError, subprocess.TimeoutExpired):
        raise InstalledSmokeError("installed semantic smoke matrix failed") from None


def _load_release_helper() -> ModuleType:
    path = Path(__file__).resolve().with_name("verify_installed_plugin_release.py")
    specification = importlib.util.spec_from_file_location("_pgc_release_helper", path)
    if specification is None or specification.loader is None:
        raise InstalledSmokeError("installed smoke failed")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def compose_installed_smoke_receipt(
    parity: Mapping[str, object], semantic: Mapping[str, object]
) -> dict[str, object]:
    """Combine verified parity and semantic results without changing counts."""

    return {
        "matrix_version": semantic["matrix_version"],
        "accepted": semantic["accepted"],
        "rejected": semantic["rejected"],
        "accepted_cases": semantic["accepted_cases"],
        "rejected_cases": semantic["rejected_cases"],
        "accepted_groups": semantic["accepted_groups"],
        "rejected_groups": semantic["rejected_groups"],
        "file_count": parity["file_count"],
        "aggregate_sha256": parity["source_aggregate_sha256"],
        "import_boundary": "verified_private_snapshot_only",
        "repository_conformance": "not_bundled_not_claimed",
    }


def run_smokes(plugin_root: Path, source_archive: Path) -> dict[str, object]:
    try:
        with capture_verified_private_snapshots(source_archive, plugin_root) as (
            source_snapshot,
            plugin_snapshot,
        ):
            release_helper = _load_release_helper()
            parity = release_helper.verify_release_parity(source_snapshot, plugin_snapshot)
            modules = load_installed_product_modules(plugin_snapshot)
            required = {
                "build_candidate_gap_response_v1": "build_candidate_gap_response_v1",
                "validate_candidate_gap_response_v1": "validate_candidate_gap_response_v1",
                "build_candidate_gap_assessment_v1": "build_candidate_gap_assessment_v1",
                "validate_candidate_gap_assessment_v1": "validate_candidate_gap_assessment_v1",
                "build_career_next_action_eligibility_v1": "build_career_next_action_eligibility_v1",
                "validate_career_next_action_eligibility_v1": "validate_career_next_action_eligibility_v1",
                "project_career_learning_decision_v3": "project_career_learning_decision_v3",
                "build_career_learning_decision_v3": "build_career_learning_decision_v3",
                "validate_career_learning_decision_v3": "validate_career_learning_decision_v3",
                "render_executive_career_dossier_v2": "render_dossier_html",
            }
            for module_name, interface in required.items():
                if not callable(getattr(modules[module_name], interface, None)):
                    raise InstalledSmokeError

            snapshot = modules["semantic_provenance_snapshot"]
            safe_group = {"signal": "terraform", "recurrence": [2, True, None]}
            if snapshot.bounded_plain_snapshot(safe_group) != safe_group:
                raise InstalledSmokeError
            rejected = 0
            hostile_values: list[object] = []
            cycle: list[object] = []
            cycle.append(cycle)
            hostile_values.append({"cycle": cycle})
            hostile_values.append({"oversized": "x" * 4097})
            hostile_values.append({"too_many": list(range(151))})
            for value in hostile_values:
                try:
                    snapshot.bounded_plain_snapshot(value)
                except ValueError as error:
                    if str(error) != "semantic input group is invalid":
                        raise InstalledSmokeError
                    rejected += 1
                else:
                    raise InstalledSmokeError

            schema_names = (
                "candidate-gap-response-v1.schema.json",
                "candidate-gap-assessment-v1.schema.json",
                "career-next-action-eligibility-v1.schema.json",
                "career-learning-decision-v3.schema.json",
            )
            for name in schema_names:
                schema = json.loads(
                    (plugin_snapshot / "schemas" / name).read_text(encoding="utf-8")
                )
                if schema.get("type") != "object" or schema.get("additionalProperties") is not False:
                    raise InstalledSmokeError

            environment = dict(os.environ)
            environment["PYTHONDONTWRITEBYTECODE"] = "1"
            static = subprocess.run(
                [sys.executable, "-B", str(plugin_snapshot / "tests" / "run_static_checks.py")],
                cwd=plugin_snapshot,
                env=environment,
                capture_output=True,
                text=True,
                check=False,
                timeout=1800,
            )
            if static.returncode != 0 or "repository conformance not bundled" not in static.stdout:
                raise InstalledSmokeError
            if rejected != len(hostile_values):
                raise InstalledSmokeError
            semantic = run_installed_semantic_matrix(plugin_snapshot, modules)
            return compose_installed_smoke_receipt(parity, semantic)
    except (InstalledSmokeError, OSError, RuntimeError, TypeError, ValueError, json.JSONDecodeError):
        raise InstalledSmokeError("installed smoke failed") from None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run installed vacancy-first smokes.")
    parser.add_argument("--plugin-root", type=Path, required=True)
    parser.add_argument("--source-archive", type=Path, required=True)
    arguments = parser.parse_args(argv)
    try:
        print(json.dumps(run_smokes(arguments.plugin_root, arguments.source_archive), sort_keys=True))
    except InstalledSmokeError as error:
        print(str(error), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
