#!/usr/bin/env python3
"""Render a validated learning proof sprint as private, offline HTML."""

from __future__ import annotations

import argparse
import html
import importlib.util
import json
import os
import secrets
import stat
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any


ASSET_ROOT = Path(__file__).resolve().parents[1] / "assets"
TEMPLATE_PATH = ASSET_ROOT / "learning-proof-sprint-v1.html"
CSS_PATH = ASSET_ROOT / "learning-proof-sprint-v1.css"
STATIC_TEMPLATE_TOKEN = "{{"


def _load_asset_loader() -> Any:
    path = Path(__file__).with_name("private_asset_loader.py")
    specification = importlib.util.spec_from_file_location(
        "learning_proof_sprint_asset_loader", path
    )
    if specification is None or specification.loader is None:
        raise RuntimeError("private renderer asset loader is unavailable")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


ASSET_LOADER = _load_asset_loader()


def _load_validator() -> Any:
    path = Path(__file__).with_name("validate_learning_proof_sprint_v1.py")
    name = "_pgc_learning_proof_sprint_renderer_validator"
    existing = sys.modules.get(name)
    if existing is not None:
        return existing
    specification = importlib.util.spec_from_file_location(name, path)
    if specification is None or specification.loader is None:
        raise RuntimeError("learning proof sprint validator is unavailable")
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


VALIDATOR = _load_validator()


COPY = {
    "en": {
        "title": "Private learning proof sprint",
        "skip": "Skip to sprint content",
        "kicker": "Candidate-owned evidence project",
        "heading": "Five-day proof sprint",
        "intro": "A private execution plan that turns one bounded gap into reviewable evidence.",
        "status_label": "Artifact status",
        "status": "Draft only · no external action",
        "plan_label": "Sprint brief",
        "plan_heading": "Start with the proof, not the purchase",
        "goal": "Sprint goal",
        "gap": "Target gap",
        "deliverable": "Deliverable",
        "publication_gate": "Publication gate",
        "timeline_label": "Execution timeline",
        "timeline_heading": "Five private checkpoints",
        "day": "Day",
        "artifact_piece": "Artifact piece",
        "proof_check": "Proof check",
        "risk_check": "Risk check",
        "acceptance_test": "Acceptance test",
        "timebox": "Candidate timebox",
        "owner": "Owner",
        "measurement_signal": "Measurement signal",
        "next_safe_action": "Next safe action",
        "candidate": "Candidate",
        "candidate_with_coach_review": "Candidate with coach review",
        "handoffs_label": "Evidence reuse",
        "handoffs_heading": "Three private handoffs",
        "linkedin": "LinkedIn",
        "application_packet": "Application packet",
        "interview": "Interview",
        "source_artifacts": "Source sprint artifacts",
        "reuse_goal": "Reuse goal",
        "safe_claim": "Safe claim",
        "proof_boundary": "Proof boundary",
        "required_review": "Required review",
        "blocked_claims": "Keep out of public copy",
        "boundary_heading": "Private boundary",
        "boundary": "This artifact stays draft-only. Do not publish, share, upload, enroll, pay, message, or schedule from this page.",
        "footer": "No external action was taken.",
        "employment_boundary": "This analysis evaluates professional options; it does not recommend resigning, leaving a job, or stopping your job search; you decide what comes next.",
    },
    "es": {
        "title": "Sprint privado de prueba de aprendizaje",
        "skip": "Ir al contenido del sprint",
        "kicker": "Proyecto de evidencia propiedad de la persona",
        "heading": "Sprint de prueba en cinco días",
        "intro": "Un plan privado de ejecución que convierte una brecha acotada en evidencia revisable.",
        "status_label": "Estado del artefacto",
        "status": "Solo borrador · sin acción externa",
        "plan_label": "Resumen del sprint",
        "plan_heading": "Empieza por la prueba, no por la compra",
        "goal": "Objetivo del sprint",
        "gap": "Brecha objetivo",
        "deliverable": "Entregable",
        "publication_gate": "Puerta de publicación",
        "timeline_label": "Línea de ejecución",
        "timeline_heading": "Cinco puntos de control privados",
        "day": "Día",
        "artifact_piece": "Pieza del artefacto",
        "proof_check": "Comprobación de prueba",
        "risk_check": "Comprobación de riesgo",
        "acceptance_test": "Prueba de aceptación",
        "timebox": "Tiempo de la persona",
        "owner": "Responsable",
        "measurement_signal": "Señal de medición",
        "next_safe_action": "Siguiente acción segura",
        "candidate": "Persona candidata",
        "candidate_with_coach_review": "Persona candidata con revisión del coach",
        "handoffs_label": "Reutilización de evidencia",
        "handoffs_heading": "Tres entregas privadas",
        "linkedin": "LinkedIn",
        "application_packet": "Paquete de postulación",
        "interview": "Entrevista",
        "source_artifacts": "Artefactos fuente del sprint",
        "reuse_goal": "Objetivo de reutilización",
        "safe_claim": "Afirmación segura",
        "proof_boundary": "Límite de la prueba",
        "required_review": "Revisión requerida",
        "blocked_claims": "Mantener fuera del texto público",
        "boundary_heading": "Límite privado",
        "boundary": "Este artefacto permanece como borrador. No publiques, compartas, subas, te inscribas, pagues, envíes mensajes ni agendes desde esta página.",
        "footer": "No se realizó ninguna acción externa.",
        "employment_boundary": "Este análisis evalúa opciones profesionales; no recomienda renunciar, dejar un empleo ni abandonar tu búsqueda; tú decides qué sigue.",
    },
}

TARGET_ASSETS = ("linkedin", "application_packet", "interview")
REQUIRED_PLAN_FIELDS = ("sprint_goal", "target_gap", "deliverable", "publication_gate")
REQUIRED_DAY_FIELDS = (
    "daily_goal", "artifact_piece", "proof_check", "risk_check", "acceptance_test",
    "candidate_timebox", "owner", "measurement_signal", "next_safe_action",
)
REQUIRED_HANDOFF_FIELDS = (
    "source_sprint_artifacts", "reuse_goal", "safe_claim", "proof_boundary",
    "required_review", "blocked_claims",
)


class LearningProofSprintRenderValidationError(ValueError):
    """Raised when a learning proof sprint cannot be rendered safely."""

    def __init__(self, errors: Sequence[str]):
        self.errors = tuple(errors)
        super().__init__("learning proof sprint validation failed")


class RenderReceipt:
    __slots__ = ("artifact_path", "artifact_type", "locale")

    def __init__(self, artifact_path: Path, artifact_type: str, locale: str) -> None:
        self.artifact_path = artifact_path
        self.artifact_type = artifact_type
        self.locale = locale


def _text(value: object, locale: str) -> str:
    """Resolve a localized value while preserving an explicit string boundary."""
    if isinstance(value, Mapping):
        selected = value.get(locale, value.get("en", ""))
        return str(selected) if selected is not None else ""
    if isinstance(value, (list, tuple)):
        return " · ".join(_text(item, locale) for item in value)
    return str(value) if value is not None else ""


def _escaped(value: object, locale: str) -> str:
    return html.escape(_text(value, locale), quote=True)


def _validate(sprint: Mapping[str, object]) -> tuple[str, Mapping[str, object], list[Mapping[str, object]], list[Mapping[str, object]]]:
    errors: list[str] = []
    locale = sprint.get("locale")
    if locale not in COPY:
        errors.append("locale must be en or es")
        locale = "en"
    plan = sprint.get("plan")
    if not isinstance(plan, Mapping):
        errors.append("plan must be an object")
        plan = {}
    for field in REQUIRED_PLAN_FIELDS:
        if not _text(plan.get(field), str(locale)).strip():
            errors.append(f"plan.{field} is required")

    days = sprint.get("days")
    if not isinstance(days, Sequence) or isinstance(days, (str, bytes)):
        days = []
        errors.append("days must be a list")
    day_rows: list[Mapping[str, object]] = []
    if isinstance(days, Sequence) and not isinstance(days, (str, bytes)):
        if len(days) != 5:
            errors.append("days must contain exactly five rows")
        seen_days: list[object] = []
        for index, day in enumerate(days, 1):
            if not isinstance(day, Mapping):
                errors.append(f"days[{index}] must be an object")
                continue
            day_rows.append(day)
            number = day.get("day_number")
            seen_days.append(number)
            if number != index:
                errors.append(f"days[{index}].day_number must be {index}")
            for field in REQUIRED_DAY_FIELDS:
                if not _text(day.get(field), str(locale)).strip():
                    errors.append(f"days[{index}].{field} is required")
            if day.get("owner") not in {"candidate", "candidate_with_coach_review"}:
                errors.append(f"days[{index}].owner is invalid")
        if seen_days != [1, 2, 3, 4, 5]:
            errors.append("days must cover day_number 1 through 5")

    handoffs = sprint.get("handoffs", sprint.get("reuse_map"))
    if not isinstance(handoffs, Sequence) or isinstance(handoffs, (str, bytes)):
        handoffs = []
        errors.append("handoffs must be a list")
    handoff_rows: list[Mapping[str, object]] = []
    if isinstance(handoffs, Sequence) and not isinstance(handoffs, (str, bytes)):
        if len(handoffs) != 3:
            errors.append("handoffs must contain exactly three rows")
        seen_assets: list[object] = []
        for index, handoff in enumerate(handoffs, 1):
            if not isinstance(handoff, Mapping):
                errors.append(f"handoffs[{index}] must be an object")
                continue
            handoff_rows.append(handoff)
            asset = handoff.get("target_asset")
            seen_assets.append(asset)
            if asset != TARGET_ASSETS[index - 1]:
                errors.append(f"handoffs[{index}].target_asset must be {TARGET_ASSETS[index - 1]}")
            for field in REQUIRED_HANDOFF_FIELDS:
                if not _text(handoff.get(field), str(locale)).strip():
                    errors.append(f"handoffs[{index}].{field} is required")
        if seen_assets != list(TARGET_ASSETS):
            errors.append("handoffs must cover linkedin, application_packet, and interview")

    delivery = sprint.get("delivery")
    if isinstance(delivery, Mapping):
        if delivery.get("draft_only") is not True:
            errors.append("delivery.draft_only must be true")
        if delivery.get("no_external_action") is not True:
            errors.append("delivery.no_external_action must be true")

    if errors:
        raise LearningProofSprintRenderValidationError(sorted(set(errors)))
    return str(locale), plan, day_rows, handoff_rows


def _plan_html(plan: Mapping[str, object], labels: Mapping[str, str], locale: str) -> str:
    fields = (
        ("goal", "sprint_goal"),
        ("gap", "target_gap"),
        ("deliverable", "deliverable"),
        ("publication_gate", "publication_gate"),
    )
    return '<dl class="sprint-plan-grid">' + "".join(
        f'<div><dt>{labels[label]}</dt><dd>{_escaped(plan[field], locale)}</dd></div>'
        for label, field in fields
    ) + "</dl>"


def _day_html(day: Mapping[str, object], labels: Mapping[str, str], locale: str) -> str:
    number = int(day["day_number"])
    owner = labels[str(day["owner"])]
    return f'''<li class="sprint-day">
      <div class="sprint-day-marker" aria-hidden="true">{number}</div>
      <article class="sprint-day-card" aria-labelledby="sprint-day-{number}-heading">
        <header class="sprint-day-header">
          <p class="sprint-day-label">{labels["day"]} {number}</p>
          <h3 id="sprint-day-{number}-heading">{_escaped(day["daily_goal"], locale)}</h3>
        </header>
        <dl class="sprint-day-facts">
          <div><dt>{labels["artifact_piece"]}</dt><dd>{_escaped(day["artifact_piece"], locale)}</dd></div>
          <div><dt>{labels["timebox"]}</dt><dd>{_escaped(day["candidate_timebox"], locale)}</dd></div>
          <div><dt>{labels["owner"]}</dt><dd>{html.escape(owner, quote=True)}</dd></div>
          <div><dt>{labels["measurement_signal"]}</dt><dd>{_escaped(day["measurement_signal"], locale)}</dd></div>
        </dl>
        <div class="sprint-proof-check"><h4>{labels["proof_check"]}</h4><p>{_escaped(day["proof_check"], locale)}</p></div>
        <div class="sprint-risk-check"><h4>{labels["risk_check"]}</h4><p>{_escaped(day["risk_check"], locale)}</p></div>
        <div class="sprint-acceptance"><h4>{labels["acceptance_test"]}</h4><p>{_escaped(day["acceptance_test"], locale)}</p></div>
        <p class="sprint-safe-action"><span class="field-label">{labels["next_safe_action"]}</span><br>{_escaped(day["next_safe_action"], locale)}</p>
      </article>
    </li>'''


def _handoff_html(handoff: Mapping[str, object], labels: Mapping[str, str], locale: str, index: int) -> str:
    asset = str(handoff["target_asset"])
    return f'''<li class="sprint-handoff">
      <header class="sprint-handoff-header">
        <p class="handoff-index">0{index}</p>
        <h3>{labels[asset]}</h3>
      </header>
      <dl class="sprint-handoff-facts">
        <div><dt>{labels["source_artifacts"]}</dt><dd>{_escaped(handoff["source_sprint_artifacts"], locale)}</dd></div>
        <div><dt>{labels["reuse_goal"]}</dt><dd>{_escaped(handoff["reuse_goal"], locale)}</dd></div>
        <div><dt>{labels["safe_claim"]}</dt><dd>{_escaped(handoff["safe_claim"], locale)}</dd></div>
        <div><dt>{labels["proof_boundary"]}</dt><dd>{_escaped(handoff["proof_boundary"], locale)}</dd></div>
        <div><dt>{labels["required_review"]}</dt><dd>{_escaped(handoff["required_review"], locale)}</dd></div>
      </dl>
      <div class="sprint-blocked-claims"><h4>{labels["blocked_claims"]}</h4><p>{_escaped(handoff["blocked_claims"], locale)}</p></div>
    </li>'''


def _render_artifact_html(sprint: Mapping[str, object]) -> str:
    if not isinstance(sprint, Mapping):
        artifact = getattr(sprint, "artifact", None)
        if isinstance(artifact, Mapping):
            sprint = artifact
        else:
            raise LearningProofSprintRenderValidationError(("sprint must be an object",))
    locale, plan, days, handoffs = _validate(sprint)
    labels = COPY[locale]
    template = ASSET_LOADER.read_private_asset(ASSET_ROOT.parent, TEMPLATE_PATH)
    css = ASSET_LOADER.read_private_asset(ASSET_ROOT.parent, CSS_PATH)
    replacements = {
        "{{LANG}}": html.escape(locale, quote=True),
        "{{TITLE}}": labels["title"],
        "{{INLINE_CSS}}": css,
        "{{SKIP}}": labels["skip"],
        "{{KICKER}}": labels["kicker"],
        "{{HEADING}}": labels["heading"],
        "{{INTRO}}": labels["intro"],
        "{{STATUS_LABEL}}": labels["status_label"],
        "{{STATUS}}": labels["status"],
        "{{PLAN_LABEL}}": labels["plan_label"],
        "{{PLAN_HEADING}}": labels["plan_heading"],
        "{{PLAN}}": _plan_html(plan, labels, locale),
        "{{TIMELINE_LABEL}}": labels["timeline_label"],
        "{{TIMELINE_HEADING}}": labels["timeline_heading"],
        "{{DAYS}}": "\n".join(_day_html(day, labels, locale) for day in days),
        "{{HANDOFFS_LABEL}}": labels["handoffs_label"],
        "{{HANDOFFS_HEADING}}": labels["handoffs_heading"],
        "{{HANDOFFS}}": "\n".join(_handoff_html(handoff, labels, locale, index) for index, handoff in enumerate(handoffs, 1)),
        "{{BOUNDARY_HEADING}}": labels["boundary_heading"],
        "{{BOUNDARY}}": labels["boundary"],
        "{{FOOTER}}": labels["footer"],
        "{{EMPLOYMENT_BOUNDARY}}": labels["employment_boundary"],
    }
    for token, replacement in replacements.items():
        template = template.replace(token, replacement)
    if STATIC_TEMPLATE_TOKEN in template:
        raise RuntimeError("learning proof sprint template token contract is invalid")
    return template


def _validated_artifact(validated_sprint: object) -> Mapping[str, object]:
    """Unwrap only the validator-issued immutable proof object."""
    if type(validated_sprint) is not VALIDATOR.ValidatedLearningProofSprint:
        raise LearningProofSprintRenderValidationError(("validated learning proof sprint is required",))
    try:
        artifact = VALIDATOR._revalidate_validated_learning_proof_sprint(validated_sprint)
    except Exception:
        raise LearningProofSprintRenderValidationError(("validated learning proof sprint is required",)) from None
    if not isinstance(artifact, Mapping):
        raise LearningProofSprintRenderValidationError(("validated learning proof sprint is required",))
    return artifact


def render_learning_proof_sprint_v1(validated_sprint: object) -> str:
    """Render only an opaque, source-validated sprint snapshot."""
    return _render_artifact_html(_validated_artifact(validated_sprint))


def render_learning_proof_sprint_html(validated_sprint: object) -> str:
    """Render only an opaque, source-validated sprint snapshot."""
    return render_learning_proof_sprint_v1(validated_sprint)


render_learning_proof_sprint_v1_html = render_learning_proof_sprint_html


def _open_private_parent(parent: Path) -> int:
    if not parent.is_absolute() or parent.anchor != os.sep:
        raise OSError("output parent must be absolute")
    descriptor = os.open(os.sep, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        for index, component in enumerate(parent.parts[1:]):
            if component in {"", ".", ".."}:
                raise OSError("output parent is unsafe")
            try:
                os.mkdir(component, 0o700, dir_fd=descriptor)
                created = True
            except FileExistsError:
                created = False
            alias = (
                index == 0
                and component in {"tmp", "var"}
                and os.path.islink(os.path.join(os.sep, component))
                and os.path.realpath(os.path.join(os.sep, component)) == os.path.join(os.sep, "private", component)
            )
            next_descriptor = os.open(
                component,
                os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | (0 if alias else getattr(os, "O_NOFOLLOW", 0)),
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


def _atomic_private_write(output: Path, content: bytes, *, force: bool = False) -> None:
    parent = _open_private_parent(output.parent)
    temporary: str | None = None
    descriptor: int | None = None
    try:
        try:
            status = os.stat(output.name, dir_fd=parent, follow_symlinks=False)
        except FileNotFoundError:
            status = None
        if status is not None:
            if stat.S_ISLNK(status.st_mode):
                raise OSError("output target is a symbolic link")
            if not stat.S_ISREG(status.st_mode):
                raise OSError("output target is not a regular file")
            if not force:
                raise FileExistsError("output already exists")
        for _ in range(100):
            candidate = f".{output.name}.tmp-{secrets.token_hex(8)}"
            try:
                descriptor = os.open(
                    candidate,
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
                    0o600,
                    dir_fd=parent,
                )
                temporary = candidate
                break
            except FileExistsError:
                continue
        if temporary is None or descriptor is None:
            raise OSError("cannot create private temporary artifact")
        with os.fdopen(descriptor, "wb") as stream:
            descriptor = None
            os.fchmod(stream.fileno(), 0o600)
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        if force:
            os.replace(temporary, output.name, src_dir_fd=parent, dst_dir_fd=parent)
        else:
            os.link(temporary, output.name, src_dir_fd=parent, dst_dir_fd=parent, follow_symlinks=False)
            os.unlink(temporary, dir_fd=parent)
        temporary = None
        os.fsync(parent)
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if temporary:
            try:
                os.unlink(temporary, dir_fd=parent)
            except FileNotFoundError:
                pass
        os.close(parent)


def write_learning_proof_sprint_html(
    validated_sprint: object, output: Path, *, force: bool = False
) -> RenderReceipt:
    artifact = _validated_artifact(validated_sprint)
    return _write_learning_proof_sprint_artifact(artifact, output, force=force)


write_learning_proof_sprint_html_v1 = write_learning_proof_sprint_html
write_learning_proof_sprint_v1_html = write_learning_proof_sprint_html


def _write_learning_proof_sprint_artifact(
    artifact: Mapping[str, object], output: Path, *, force: bool = False
) -> RenderReceipt:
    rendered = _render_artifact_html(artifact)
    target = Path(os.path.abspath(os.fspath(output)))
    _atomic_private_write(target, rendered.encode("utf-8"), force=force)
    return RenderReceipt(target, "text/html", str(artifact["locale"]))


write_validated_learning_proof_sprint_html_v1 = write_learning_proof_sprint_html


def _load_json(path: Path) -> Mapping[str, object]:
    if path.is_symlink():
        raise ValueError("symlink input")
    raw = VALIDATOR._loader.read_bounded_bytes(path, 512 * 1024)
    value = json.loads(raw.decode("utf-8"), object_pairs_hook=VALIDATOR._unique_object)
    if not isinstance(value, Mapping):
        raise ValueError("sprint input must be a JSON object")
    return value


def _cli(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render a private learning proof sprint.")
    parser.add_argument("input", type=Path)
    parser.add_argument("--source-group", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--force", action="store_true")
    try:
        args = parser.parse_args(argv)
        sprint = _load_json(args.input)
        source_group = _load_json(args.source_group)
        validated = VALIDATOR.validate_learning_proof_sprint_v1(sprint, source_group)
        result = write_learning_proof_sprint_html(validated, args.output, force=args.force)
    except SystemExit as error:
        return 0 if error.code == 0 else 3
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(str(error), file=sys.stderr)
        return 3
    print(json.dumps({"artifact_path": str(result.artifact_path), "artifact_type": result.artifact_type, "locale": result.locale}, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
