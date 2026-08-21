"""Behavioral contracts for the status-only executive career dossier v2."""

from __future__ import annotations

import copy
import hashlib
import html
import importlib.util
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "plugins" / "professional-growth-coach" / "scripts"
VALIDATOR_PATH = SCRIPTS / "validate_executive_career_dossier_v2.py"
RENDERER_PATH = SCRIPTS / "render_executive_career_dossier_v2.py"
V1_RENDERER_PATH = SCRIPTS / "render_executive_career_dossier.py"
FIXTURE_ROOT = REPO_ROOT / "tests" / "evals" / "with-skill" / "fixtures" / "executive-career-dossier"
V2_FIXTURE_ROOT = FIXTURE_ROOT.with_name("executive-career-dossier-v2")
RESEARCH_FIXTURE_ROOT = FIXTURE_ROOT.with_name("target-vacancy-research")
MARKET_FIXTURE_ROOT = FIXTURE_ROOT.with_name("career-market-learning-dossier")
NO_MARKET_RENDER_SNAPSHOTS = {
    "scenario-a-es.json": (48675, "87ad9699fa114cf3b25b487a62bd93ccff5ef80ff7965ecd1624b47bcb196d7a"),
    "scenario-c-en.json": (46730, "7ac97a6c4572af3ee04e7445aee6ea1ed4eebdbf10470a5ec99239ed7bb3ac21"),
}
COPY_MARKET_PLACEHOLDER_ES = (
    "Este dossier no incluye evidencia de mercado. Continúa con la evidencia del perfil ya revisada."
)

UNSAFE_COACHING_PROSE = (
    (
        "coach_observation",
        "Publish this on LinkedIn now.",
        "must remain a private review action",
    ),
    (
        "why_it_matters",
        "Publish this on LinkedIn now.",
        "must remain a private review action",
    ),
    (
        "coach_prompt",
        "Publish this on LinkedIn now.",
        "must remain a private review action",
    ),
    (
        "coach_observation",
        "The profile is now live on LinkedIn.",
        "must remain a private review action",
    ),
    (
        "why_it_matters",
        "The profile is now live on LinkedIn.",
        "must remain a private review action",
    ),
    (
        "coach_prompt",
        "The profile is now live on LinkedIn.",
        "must remain a private review action",
    ),
    (
        "coach_prompt",
        "Quit your job now.",
        "must preserve current employment by default",
    ),
    (
        "coach_observation",
        "There were 314 private profile views.",
        "analytics measures require observed aggregate analytics",
    ),
    (
        "why_it_matters",
        "Employers are actively hiring 1000 SREs.",
        "market claims require local dated market evidence",
    ),
)

SAFE_COACHING_PROSE = (
    ("coach_observation", "The incident response scope is ready for private review."),
    ("why_it_matters", "Technical scope supports a focused private coaching review."),
    ("coach_prompt", "Review the private incident response scope for technical clarity."),
)

CANONICAL_PROFILE_SECTIONS = (
    "photo", "banner", "name", "profile_url", "headline", "location",
    "contact_info", "about", "experience", "skills", "featured",
    "certifications", "education", "recommendations", "activity",
    "analytics", "job_preferences",
)


def unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, nested in pairs:
        if key in value:
            raise ValueError("duplicate JSON key")
        value[key] = nested
    return value


def load_v1_fixture(name: str) -> dict[str, object]:
    value = json.loads(
        (FIXTURE_ROOT / name).read_text(encoding="utf-8"), object_pairs_hook=unique_object
    )
    if not isinstance(value, dict):
        raise ValueError("fixture must be an object")
    return value


def make_v2_dossier(locale: str = "es") -> dict[str, object]:
    dossier = copy.deepcopy(load_v1_fixture(
        "scenario-a-es.json" if locale == "es" else "scenario-c-en.json"
    ))
    dossier["schema_version"] = "executive-career-dossier-v2"
    inspected = set(dossier["evidence_scope"]["inspected_sections"])
    dossier["section_coverage"] = []
    for section in CANONICAL_PROFILE_SECTIONS:
        if section in inspected:
            dossier["section_coverage"].append({
                "section": section,
                "availability": "inspected_present",
                "evidence_state": "verified",
                "reason": "inspected_content_available",
            })
            continue
        decision = "declined_for_session" if section == "certifications" else "pending_response"
        dossier["section_coverage"].append({
            "section": section,
            "availability": "unavailable",
            "evidence_state": "unknown",
            "reason": "inspection_declined" if decision == "declined_for_session" else "authorization_required",
            "inspection_request": {
                "access_type": "read_only_visible_section_inspection",
                "decision": decision,
                "scope": "current_session_only",
                "carry_forward": False,
            },
        })
    profile_sections = (
        {"E-001": "headline", "E-002": "about", "E-003": "experience", "E-004": "skills", "E-006": "photo", "E-007": "banner"}
        if locale == "es"
        else {"E-001": "headline", "E-002": "skills", "E-003": "about", "E-004": "experience", "E-005": "photo"}
    )
    for evidence in dossier["evidence"]:
        evidence["profile_section"] = profile_sections.get(evidence["id"])
    priority_sections = ("headline", "about", "experience")
    for priority, section in zip(dossier["priorities"], priority_sections, strict=True):
        priority["evidence_ids"] = (
            {"headline": ["E-001"], "about": ["E-002"], "experience": ["E-003"]}
            if locale == "es"
            else {"headline": ["E-001"], "about": ["E-003"], "experience": ["E-004"]}
        )[section]
        priority.update({
            "target_section": section,
            "coach_observation": f"Coach observation for {section}.",
            "why_it_matters": f"Evidence from {section} changes the review.",
            "coach_prompt": f"Complete the private template for {section}.",
            "client_template": {
                "template_id": "context_action_result_v1",
                "field_keys": ["context", "action", "result"],
            },
            "privacy_boundary": "no_raw_profile_text_or_private_values",
        })
    return dossier


def load_json_fixture(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_object)
    if not isinstance(value, dict):
        raise ValueError("fixture must be an object")
    return value


def market_alignment(
    research: dict[str, object], dossier: dict[str, object]
) -> dict[str, object]:
    scripts = str(SCRIPTS)
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    from dossier_snapshot import snapshot_for_dossier
    from validate_target_vacancy_research import snapshot_for_market_dossier

    configured = {
        "python": ("verified_match", ["E-001"]),
        "kubernetes": ("candidate_reported_match", ["E-003"]),
        "terraform": ("adjacent_evidence", ["E-004"]),
        "observability": ("unknown", []),
        "linux": ("explicit_gap", ["E-003"]),
    }
    signals = {
        requirement["signal"]
        for vacancy in research["vacancies"]
        for requirement in vacancy["requirements"]
    }
    return {
        "schema_version": "candidate-market-alignment-v1",
        "research_snapshot": snapshot_for_market_dossier(research),
        "executive_dossier_snapshot": snapshot_for_dossier(dossier),
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


def market_case(
    research_name: str, dossier_name: str
) -> tuple[dict[str, object], dict[str, object], dict[str, object], dict[str, object]]:
    dossier = load_json_fixture(V2_FIXTURE_ROOT / dossier_name)
    research = load_json_fixture(RESEARCH_FIXTURE_ROOT / research_name)
    market = load_json_fixture(MARKET_FIXTURE_ROOT / research_name)
    return dossier, market, research, market_alignment(research, dossier)


def learning_case(
    research_name: str, dossier_name: str, count: int = 3, decision_count: int = 3
) -> tuple[dict[str, object], dict[str, object], dict[str, object], dict[str, object], dict[str, object]]:
    """Build a small validated learning bundle for renderer contract tests."""
    if count == 0:
        dossier, market, research, alignment = market_case(research_name, dossier_name)
    elif count < 5:
        dossier, market, research, alignment = build_limited_market_case(count)
    else:
        dossier, market, research, alignment = market_case(research_name, dossier_name)
    scripts = str(SCRIPTS)
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    from build_career_learning_decision import build_learning_bundle

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
    rows = [
        {
            "decision_rank": 1,
            "target_role": "Senior SRE / Platform Engineer",
            "gap_type": "proof",
            "option_type": "portfolio_project",
            "option_name": "Terraform and observability proof artifact",
            "provider_or_owner": "candidate-owned proof project",
            "source_gap_ids": [evidence_id],
            "vacancy_ids": vacancy_ids[: min(2, len(vacancy_ids))],
            "market_evidence_state": "current dated vacancy evidence",
            "cost_time_band": "unknown: candidate effort requires separate confirmation",
            "expected_signal_boundary": "bounded hypothesis: creates inspectable evidence without promising a hiring outcome",
            "portfolio_or_no_learning_alternative": "Complete one bounded proof artifact before buying another credential.",
            "overbuying_risk": "Avoid certificate collecting before one higher-signal artifact is complete.",
            "decision": "do_now",
            "decision_basis": "Repeated vacancy evidence supports a candidate-owned proof artifact before a purchase.",
            "next_action_gate": "No external action; exact authorization is required before publication, sharing, or messaging.",
            "outcome_boundary": "not_an_interview_offer_salary_or_roi_prediction",
            "draft_only": True,
            "no_external_action": True,
            "provider_source": None,
        },
        {
            "decision_rank": 2,
            "target_role": "Senior SRE / Platform Engineer",
            "gap_type": "knowledge",
            "option_type": "course",
            "option_name": "Terraform Associate study path",
            "provider_or_owner": "HashiCorp",
            "source_gap_ids": [evidence_id],
            "vacancy_ids": vacancy_ids[: min(2, len(vacancy_ids))],
            "market_evidence_state": "current dated vacancy evidence",
            "cost_time_band": "unknown: current cost and candidate effort require separate confirmation",
            "expected_signal_boundary": "bounded hypothesis: may corroborate knowledge without promising a hiring outcome",
            "portfolio_or_no_learning_alternative": "Build a bounded Terraform proof artifact before enrolling.",
            "overbuying_risk": "Avoid paying before a cheaper proof comparison is reviewed.",
            "decision": "research_first",
            "decision_basis": "Repeated vacancy evidence supports research, but official provider cost and eligibility remain unknown.",
            "next_action_gate": "No external action; purchase or enrollment requires exact authorization after source review.",
            "outcome_boundary": "not_an_interview_offer_salary_or_roi_prediction",
            "draft_only": True,
            "no_external_action": True,
            "provider_source": provider_source,
        },
        {
            "decision_rank": 3,
            "target_role": "Senior SRE / Platform Engineer",
            "gap_type": "low_return",
            "option_type": "no_learning_yet",
            "option_name": "Finish the current proof artifact first",
            "provider_or_owner": "none",
            "source_gap_ids": [evidence_id],
            "vacancy_ids": vacancy_ids[: min(2, len(vacancy_ids))],
            "market_evidence_state": "current dated vacancy evidence",
            "cost_time_band": "unknown: candidate effort requires separate confirmation",
            "expected_signal_boundary": "bounded hypothesis: protects time for higher-signal proof without promising a hiring outcome",
            "portfolio_or_no_learning_alternative": "Use the existing proof artifact as the lower-cost alternative.",
            "overbuying_risk": "Avoid starting a course before the evidence gap is reviewed again.",
            "decision": "do_now",
            "decision_basis": "Candidate-owned evidence is a higher-priority next move than generic learning.",
            "next_action_gate": "No external action; exact authorization is required before publication, sharing, or messaging.",
            "outcome_boundary": "not_an_interview_offer_salary_or_roi_prediction",
            "draft_only": True,
            "no_external_action": True,
            "provider_source": None,
        },
    ]
    rows.extend(
        [
            {
                **copy.deepcopy(rows[0]),
                "decision_rank": 4,
                "option_type": "lab",
                "option_name": "Observability incident-response lab",
                "decision": "research_first",
            },
            {
                **copy.deepcopy(rows[0]),
                "decision_rank": 5,
                "option_type": "role_search",
                "option_name": "Search for a role that values existing proof",
                "decision": "defer",
            },
        ]
    )
    rows = rows[:decision_count]
    if not vacancy_ids:
        rows = []
    bundle = build_learning_bundle(research, market, dossier, rows)
    return dossier, market, research, alignment, bundle


def build_limited_market_case(
    count: int,
) -> tuple[dict[str, object], dict[str, object], dict[str, object], dict[str, object]]:
    dossier = load_json_fixture(V2_FIXTURE_ROOT / "scenario-c-en.json")
    research = load_json_fixture(RESEARCH_FIXTURE_ROOT / "limited-four-en.json")
    research["employers"] = research["employers"][:count]
    research["vacancies"] = research["vacancies"][:count]
    alignment = market_alignment(research, dossier)
    scripts = str(SCRIPTS)
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    from build_career_market_learning_dossier import build_market_dossier

    return dossier, build_market_dossier(research, dossier, alignment), research, alignment


def load_validator() -> object:
    specification = importlib.util.spec_from_file_location(
        "validate_executive_career_dossier_v2", VALIDATOR_PATH
    )
    assert specification is not None and specification.loader is not None
    validator = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = validator
    specification.loader.exec_module(validator)
    return validator


def load_renderer() -> object:
    specification = importlib.util.spec_from_file_location(
        "render_executive_career_dossier_v2", RENDERER_PATH
    )
    assert specification is not None and specification.loader is not None
    renderer = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = renderer
    specification.loader.exec_module(renderer)
    return renderer


def load_v1_renderer() -> object:
    specification = importlib.util.spec_from_file_location(
        "render_executive_career_dossier_decide_now_v1", V1_RENDERER_PATH
    )
    assert specification is not None and specification.loader is not None
    renderer = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = renderer
    specification.loader.exec_module(renderer)
    return renderer


def visible_text(rendered: str) -> str:
    without_code = re.sub(r"(?is)<(?:style|script)\b.*?</(?:style|script)>", " ", rendered)
    return " ".join(html.unescape(re.sub(r"(?s)<[^>]+>", " ", without_code)).split())


def decide_now_region(rendered: str) -> tuple[set[str], str, str]:
    match = re.search(
        r'<section(?=[^>]*class="[^"]*\bdecide-now\b[^"]*")'
        r'(?=[^>]*aria-labelledby="decide-now-title")'
        r'(?=[^>]*aria-describedby="([^"]+)")[^>]*>(.*?)</section>',
        rendered,
        re.DOTALL,
    )
    if match is None:
        raise AssertionError("Decide now section is missing")
    return set(re.findall(r'<a href="#([^"]+)">', match.group(2))), match.group(1), match.group(2)


class DossierDOMAudit(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: list[str] = []
        self.references: list[str] = []
        self.classes: list[str] = []
        self.tag_counts: dict[str, int] = {}
        self.heading_levels: list[int] = []
        self.start_tags: list[tuple[str, dict[str, str | None]]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.tag_counts[tag] = self.tag_counts.get(tag, 0) + 1
        values = dict(attrs)
        self.start_tags.append((tag, values))
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self.heading_levels.append(int(tag[1]))
        identifier = values.get("id")
        if identifier:
            self.ids.append(identifier)
        for field in ("aria-labelledby", "aria-describedby"):
            references = values.get(field)
            if references:
                self.references.extend(references.split())
        classes = values.get("class")
        if classes:
            self.classes.extend(classes.split())


class ExecutiveCareerDossierV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.validator = load_validator()

    def test_v2_requires_the_exact_canonical_section_ledger(self) -> None:
        dossier = make_v2_dossier()
        self.assertEqual(self.validator.validate_dossier(dossier), [])
        self.assertEqual(tuple(row["section"] for row in dossier["section_coverage"]), CANONICAL_PROFILE_SECTIONS)
        for mutation in (
            dossier["section_coverage"][:-1],
            list(reversed(dossier["section_coverage"])),
            dossier["section_coverage"] + [copy.deepcopy(dossier["section_coverage"][0])],
        ):
            invalid = copy.deepcopy(dossier)
            invalid["section_coverage"] = mutation
            self.assertIn(
                "section_coverage must contain every canonical section exactly once in canonical order",
                self.validator.validate_dossier(invalid),
            )

    def test_unavailable_sections_require_current_session_read_only_decisions(self) -> None:
        dossier = make_v2_dossier()
        dossier["section_coverage"][10] = {
            "section": "featured", "availability": "unavailable", "evidence_state": "unknown",
            "reason": "authorization_required", "inspection_request": {
                "access_type": "read_only_visible_section_inspection", "decision": "pending_response",
                "scope": "current_session_only", "carry_forward": False,
            },
        }
        self.assertEqual(self.validator.validate_dossier(dossier), [])
        missing = copy.deepcopy(dossier)
        del missing["section_coverage"][10]["inspection_request"]
        self.assertIn("section_coverage[10] unavailable section requires inspection_request", self.validator.validate_dossier(missing))
        forbidden = make_v2_dossier()
        forbidden["section_coverage"][0]["inspection_request"] = copy.deepcopy(dossier["section_coverage"][10]["inspection_request"])
        self.assertIn("section_coverage[0] inspected section forbids inspection_request", self.validator.validate_dossier(forbidden))

    def test_ledger_state_matrix_is_closed_and_status_only(self) -> None:
        dossier = make_v2_dossier()
        cases = (
            ("inspected_present", "verified", "inspected_content_available", None),
            ("inspected_absent", "verified", "inspected_section_absent", None),
            ("candidate_supplied", "candidate_reported", "candidate_material_supplied", None),
            ("unavailable", "unknown", "authorization_required", "pending_response"),
            ("unavailable", "unknown", "inspection_declined", "declined_for_session"),
            ("unavailable", "unknown", "authorized_inspection_failed", "authorized_inspection_failed"),
        )
        for availability, state, reason, decision in cases:
            with self.subTest(availability=availability, decision=decision):
                invalid = copy.deepcopy(dossier)
                row = invalid["section_coverage"][10]
                row.update({"availability": availability, "evidence_state": state, "reason": reason})
                if decision is None:
                    row.pop("inspection_request", None)
                else:
                    row["inspection_request"]["decision"] = decision
                if availability == "candidate_supplied":
                    invalid["evidence"].append({
                        "id": "E-999", "state": "candidate_reported", "section": "proof",
                        "source_kind": "candidate_statement", "paraphrase": "Candidate material was supplied.",
                        "capture_ref": None, "profile_section": "featured",
                    })
                if availability == "inspected_present":
                    invalid["evidence"].append({
                        "id": "E-998", "state": "verified", "section": "proof",
                        "source_kind": "authorized_visible", "paraphrase": "Visible section was inspected.",
                        "capture_ref": "CAP-001", "profile_section": "featured",
                    })
                self.assertEqual(self.validator.validate_dossier(invalid), [])
        for mutation in (
            {"decision": "authorized_for_session"},
            {"carry_forward": True},
            {"access_type": "write_visible_section_inspection"},
            {"scope": "future_sessions"},
        ):
            invalid = make_v2_dossier()
            invalid["section_coverage"][10]["inspection_request"].update(mutation)
            self.assertTrue(self.validator.validate_dossier(invalid))

    def test_legacy_scope_is_a_constraint_not_the_complete_ledger(self) -> None:
        dossier = make_v2_dossier()
        self.assertEqual(self.validator.validate_dossier(dossier), [])
        contradictory = copy.deepcopy(dossier)
        contradictory["section_coverage"][4].update({
            "availability": "unavailable", "evidence_state": "unknown", "reason": "authorization_required",
            "inspection_request": {"access_type": "read_only_visible_section_inspection", "decision": "pending_response", "scope": "current_session_only", "carry_forward": False},
        })
        self.assertIn("section_coverage[4] contradicts evidence_scope.inspected_sections", self.validator.validate_dossier(contradictory))
        unavailable = copy.deepcopy(dossier)
        unavailable["evidence_scope"]["unavailable_sections"] = ["featured"]
        unavailable["section_coverage"][10] = {"section": "featured", "availability": "inspected_absent", "evidence_state": "verified", "reason": "inspected_section_absent"}
        self.assertIn("section_coverage[10] contradicts evidence_scope.unavailable_sections", self.validator.validate_dossier(unavailable))

    def test_present_or_candidate_rows_require_section_evidence_without_score_mutation(self) -> None:
        dossier = make_v2_dossier()
        before = copy.deepcopy(dossier)
        self.assertEqual(self.validator.validate_dossier(dossier), [])
        self.assertEqual(dossier, before)
        missing = copy.deepcopy(dossier)
        missing["evidence"][0]["profile_section"] = None
        self.assertIn("section_coverage[4] requires evidence for its profile_section", self.validator.validate_dossier(missing))
        pending = copy.deepcopy(dossier)
        pending["section_coverage"][10]["inspection_request"]["decision"] = "pending_response"
        declined = copy.deepcopy(pending)
        declined["section_coverage"][10].update({"reason": "inspection_declined"})
        declined["section_coverage"][10]["inspection_request"]["decision"] = "declined_for_session"
        self.assertEqual(pending["coverage"], declined["coverage"])
        self.assertEqual(self.validator.validate_dossier(pending), [])
        self.assertEqual(self.validator.validate_dossier(declined), [])

    def test_contextual_priorities_bind_same_section_evidence(self) -> None:
        dossier = make_v2_dossier()
        self.assertEqual(self.validator.validate_dossier(dossier), [])
        dossier["priorities"][0]["evidence_ids"] = ["E-002"]
        self.assertIn("priorities[0].evidence_ids must bind to the target section", self.validator.validate_dossier(dossier))

    def test_priority_contract_is_closed_and_safe(self) -> None:
        for field in ("target_section", "coach_observation", "why_it_matters", "coach_prompt", "client_template", "privacy_boundary"):
            invalid = make_v2_dossier()
            del invalid["priorities"][0][field]
            self.assertTrue(self.validator.validate_dossier(invalid), field)
        for field_keys in ([], ["context", "action", "result", "scope", "metric", "target_role"], ["context", "context"]):
            invalid = make_v2_dossier()
            invalid["priorities"][0]["client_template"]["field_keys"] = field_keys
            self.assertTrue(self.validator.validate_dossier(invalid), field_keys)
        invalid = make_v2_dossier()
        invalid["priorities"][0]["client_template"]["template_id"] = "unknown_template"
        self.assertTrue(self.validator.validate_dossier(invalid))

    def test_new_coaching_prose_reuses_v1_action_employment_analytics_and_market_guards(self) -> None:
        for field, value, diagnostic in UNSAFE_COACHING_PROSE:
            with self.subTest(field=field, diagnostic=diagnostic):
                dossier = make_v2_dossier()
                dossier["priorities"][0][field] = value
                errors = self.validator.validate_dossier(dossier)
                self.assertIn(f"priorities[0].{field} {diagnostic}", errors)
                self.assertNotIn(value, "\n".join(errors))

        for field, value in SAFE_COACHING_PROSE:
            with self.subTest(field=field):
                dossier = make_v2_dossier()
                dossier["priorities"][0][field] = value
                self.assertEqual(self.validator.validate_dossier(dossier), [])

    def test_v2_dated_market_coaching_prose_and_projection_use_v1_hire_and_hiring_semantics(self) -> None:
        source = load_v1_fixture("scenario-market-en.json")
        dossier = make_v2_dossier("en")
        market_evidence = copy.deepcopy(source["evidence"][-1])
        market_evidence["profile_section"] = None
        dossier["evidence"].append(market_evidence)
        dossier["market_context"] = copy.deepcopy(source["market_context"])
        self.assertEqual(self.validator.project_v2_to_v1(dossier), source)

        for text in (
            "Employers actively hire SREs.",
            "Employers are actively hiring SREs.",
        ):
            with self.subTest(text=text, surface="v2 coaching prose"):
                unlinked = copy.deepcopy(dossier)
                unlinked["priorities"][0]["why_it_matters"] = text
                self.assertIn(
                    "priorities[0].why_it_matters market claims require local dated market evidence",
                    self.validator.validate_dossier(unlinked),
                )

            with self.subTest(text=text, surface="v1 projection", evidence="unlinked"):
                projected = self.validator.project_v2_to_v1(dossier)
                projected["priorities"][0]["why_now"] = text
                self.assertEqual(self.validator._v1.validate_dossier(projected), [])

        safe = copy.deepcopy(dossier)
        safe["priorities"][0]["why_it_matters"] = (
            "Technical controls remain available for private review."
        )
        self.assertEqual(self.validator.validate_dossier(safe), [])

    def test_v2_schema_checker_runs_before_semantic_validation(self) -> None:
        dossier = make_v2_dossier()
        dossier["section_coverage"][0]["availability"] = "unsupported"
        errors = self.validator.validate_dossier(dossier)
        self.assertIn("v2 schema validation failed", errors)
        self.assertNotIn("unsupported", "\n".join(errors))

    def test_v2_direct_validation_is_total_for_self_and_nested_cycles(self) -> None:
        self_cycle: dict[str, object] = {}
        self_cycle["opaque_self_cycle"] = self_cycle
        nested_cycle: dict[str, object] = {"branch": []}
        nested_cycle["branch"].append({"opaque_nested_cycle": nested_cycle})
        for value in (self_cycle, nested_cycle):
            with self.subTest(kind="self" if value is self_cycle else "nested"):
                errors = self.validator.validate_dossier(value)
                self.assertEqual(errors, ["v2 dossier contains cyclic data", "v2 schema validation failed"])
                self.assertNotIn("opaque", "\n".join(errors))

    def test_v2_external_action_guard_applies_to_every_coaching_field(self) -> None:
        for field in ("coach_observation", "why_it_matters", "coach_prompt"):
            for unsafe in (
                "Consider publishing this on LinkedIn.",
                "The next step is sending the message to the recruiter.",
                "Conectar contexto y publicar esto en LinkedIn.",
            ):
                with self.subTest(field=field, unsafe=unsafe):
                    dossier = make_v2_dossier()
                    dossier["priorities"][0][field] = unsafe
                    errors = self.validator.validate_dossier(dossier)
                    self.assertIn(f"priorities[0].{field} must remain a private review action", errors)
                    self.assertNotIn(unsafe, "\n".join(errors))

    def test_exact_internal_writing_fixture_phrase_remains_valid(self) -> None:
        dossier = make_v2_dossier()
        dossier["priorities"][0]["coach_observation"] = (
            "La apertura describe responsabilidades sin conectar todavía contexto y resultado."
        )
        self.assertEqual(self.validator.validate_dossier(dossier), [])

    def test_projection_deep_copy_isolation_survives_nested_mutation(self) -> None:
        source = make_v2_dossier()
        original = copy.deepcopy(source)
        projected = self.validator.project_v2_to_v1(source)
        projected["evidence"][0]["paraphrase"] = "changed"
        projected["priorities"][0]["evidence_ids"].append("E-999")
        self.assertEqual(source, original)

    def test_every_locale_section_question_and_declined_failed_state_is_explicit(self) -> None:
        renderer = load_renderer()
        for locale, labels in renderer.SECTION_LABELS.items():
            for section, label in labels.items():
                with self.subTest(locale=locale, section=section):
                    question = renderer.AUTHORIZATION_QUESTIONS[locale][section]
                    self.assertIn(label, question)
                    self.assertIn("sesión" if locale == "es" else "session", question)
        dossier = make_v2_dossier()
        for row in dossier["section_coverage"]:
            request = row.get("inspection_request")
            if isinstance(request, dict):
                request["decision"] = "declined_for_session"
                row["reason"] = "inspection_declined"
        dossier["section_coverage"][10]["inspection_request"]["decision"] = "authorized_inspection_failed"
        dossier["section_coverage"][10]["reason"] = "authorized_inspection_failed"
        self.assertIsNone(self.validator.select_pending_inspection_section(dossier))

    def test_every_ledger_and_request_boundary_rejects_session_or_positive_authorization_fields(self) -> None:
        mutations = (
            ("section_coverage", 10, "session_id"),
            ("section_coverage", 10, "authorized_for_session"),
            ("inspection_request", 10, "session_id"),
            ("inspection_request", 10, "authorization_granted"),
        )
        for boundary, index, key in mutations:
            with self.subTest(boundary=boundary, key=key):
                dossier = make_v2_dossier()
                target = dossier["section_coverage"][index]
                if boundary == "inspection_request":
                    target = target["inspection_request"]
                target[key] = True
                errors = self.validator.validate_dossier(dossier)
                self.assertTrue(errors)
                self.assertNotIn(key, "\n".join(errors))

    def test_every_evidence_record_requires_a_canonical_or_null_profile_section(self) -> None:
        for label, replacement in (("missing", None), ("unknown", "unknown_section"), ("number", 3), ("array", [])):
            with self.subTest(replacement=label):
                dossier = make_v2_dossier()
                if label == "missing":
                    del dossier["evidence"][4]["profile_section"]
                else:
                    dossier["evidence"][4]["profile_section"] = replacement
                self.assertTrue(self.validator.validate_dossier(dossier))

    def test_selector_falls_back_to_canonical_pending_section_not_targeted_by_a_priority(self) -> None:
        dossier = make_v2_dossier()
        for row in dossier["section_coverage"]:
            if isinstance(row.get("inspection_request"), dict):
                row["inspection_request"]["decision"] = "declined_for_session"
                row["reason"] = "inspection_declined"
        dossier["section_coverage"][10]["inspection_request"]["decision"] = "pending_response"
        dossier["section_coverage"][10]["reason"] = "authorization_required"
        self.assertEqual(self.validator.select_pending_inspection_section(dossier), "featured")

    def test_v2_diagnostics_do_not_echo_new_prose_values(self) -> None:
        sentinels = (
            "/private/path/profile.json", "https://www.linkedin.com/in/example",
            "person@example.test", "unsafe\x1b[31m", "unsafe\u202evalue",
        )
        for field in ("coach_observation", "why_it_matters", "coach_prompt", "privacy_boundary"):
            for sentinel in sentinels:
                with self.subTest(field=field, sentinel=repr(sentinel)):
                    dossier = make_v2_dossier()
                    dossier["priorities"][0][field] = sentinel
                    errors = self.validator.validate_dossier(dossier)
                    self.assertTrue(errors)
                    self.assertNotIn(sentinel, "\n".join(errors))

    def test_selector_returns_one_pending_priority_then_ledger_section(self) -> None:
        dossier = make_v2_dossier()
        dossier["section_coverage"][4].update({
            "availability": "unavailable", "evidence_state": "unknown", "reason": "authorization_required",
            "inspection_request": {"access_type": "read_only_visible_section_inspection", "decision": "pending_response", "scope": "current_session_only", "carry_forward": False},
        })
        self.assertEqual(self.validator.select_pending_inspection_section(dossier), "headline")
        dossier["section_coverage"][4].update({"availability": "inspected_present", "evidence_state": "verified", "reason": "inspected_content_available"})
        dossier["section_coverage"][7].update({
            "availability": "unavailable", "evidence_state": "unknown", "reason": "authorization_required",
            "inspection_request": {"access_type": "read_only_visible_section_inspection", "decision": "pending_response", "scope": "current_session_only", "carry_forward": False},
        })
        self.assertEqual(self.validator.select_pending_inspection_section(dossier), "about")
        for row in dossier["section_coverage"]:
            request = row.get("inspection_request")
            if isinstance(request, dict):
                request["decision"] = "declined_for_session"
                row["reason"] = "inspection_declined"
        self.assertIsNone(self.validator.select_pending_inspection_section(dossier))


class ExecutiveCareerDossierV2RendererTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.renderer = load_renderer()
        cls.validator = load_validator()

    def test_localized_ledger_has_one_named_region_and_exact_semantic_rows(self) -> None:
        expected_labels = {
            "es": (
                "Foto", "Banner", "Nombre", "URL del perfil", "Titular", "Ubicación",
                "Información de contacto", "Acerca de", "Experiencia", "Aptitudes",
                "Destacado", "Certificaciones", "Educación", "Recomendaciones",
                "Actividad", "Analítica", "Preferencias de empleo",
            ),
            "en": (
                "Photo", "Banner", "Name", "Profile URL", "Headline", "Location",
                "Contact information", "About", "Experience", "Skills", "Featured",
                "Certifications", "Education", "Recommendations", "Activity",
                "Analytics", "Job preferences",
            ),
        }
        for locale in ("es", "en"):
            with self.subTest(locale=locale):
                rendered = self.renderer.render_dossier_html(make_v2_dossier(locale))
                regions = re.findall(
                    r'<section class="section-block section-coverage-ledger" aria-labelledby="([^"]+)">(.*?)</section>',
                    rendered,
                    re.DOTALL,
                )
                self.assertEqual(len(regions), 1)
                region_label, body = regions[0]
                self.assertEqual(len(re.findall(rf'<h2 id="{re.escape(region_label)}">', body)), 1)
                rows = re.findall(
                    r'<li class="section-coverage-row"><article aria-labelledby="([^"]+)">\s*'
                    r'<h3 id="\1">([^<]+)</h3>\s*<dl class="section-coverage-facts">(.*?)</dl>\s*'
                    r'</article></li>',
                    body,
                    re.DOTALL,
                )
                self.assertEqual(len(rows), 17)
                self.assertEqual(tuple(label for _, label, _ in rows), expected_labels[locale])
                self.assertEqual(len({heading_id for heading_id, _, _ in rows}), 17)
                for _, _, facts in rows:
                    self.assertIn("<dt>", facts)
                    self.assertIn("<dd>", facts)
                    self.assertGreaterEqual(facts.count("<dt>"), 2)
                    self.assertEqual(facts.count("<dt>"), len(re.findall(r"<dd(?:\s|>)", facts)))

    def test_unavailable_rows_show_localized_reason_and_request_decision(self) -> None:
        for locale, labels in (
            ("es", ("No disponible", "Autorización requerida", "Respuesta pendiente")),
            ("en", ("Unavailable", "Authorization required", "Response pending")),
        ):
            with self.subTest(locale=locale):
                rendered = self.renderer.render_dossier_html(make_v2_dossier(locale))
                for label in labels:
                    self.assertIn(label, rendered)
                self.assertIn('class="section-coverage-request"', rendered)

    def test_three_named_coach_cards_render_closed_blank_templates_without_legacy_priority_copy(self) -> None:
        for locale in ("es", "en"):
            with self.subTest(locale=locale):
                dossier = make_v2_dossier(locale)
                rendered = self.renderer.render_dossier_html(dossier)
                cards = re.findall(
                    r'<article class="card span-4 coach-priority-card" aria-labelledby="([^"]+)">(.*?)</article>',
                    rendered,
                    re.DOTALL,
                )
                self.assertEqual(len(cards), 3)
                self.assertNotIn('class="timebox"', rendered)
                for (heading_id, card), priority in zip(cards, dossier["priorities"], strict=True):
                    self.assertEqual(len(re.findall(rf'<h3 id="{re.escape(heading_id)}">', card)), 1)
                    self.assertIn('class="coach-observation"', card)
                    self.assertIn('class="coach-prompt"', card)
                    self.assertIn('class="coach-template"', card)
                    blanks = re.findall(r'<li><span class="coach-template-field">[^<]+</span><span class="coach-template-blank" role="img" aria-label="[^"]+"></span></li>', card)
                    self.assertGreaterEqual(len(blanks), 1)
                    self.assertLessEqual(len(blanks), 5)
                    for old_value in ("problem", "action"):
                        self.assertNotIn(str(priority[old_value]), card)

    def test_coach_templates_expose_localized_private_blank_and_boundary(self) -> None:
        for locale, expected in (
            ("es", ("No incluyas texto sin procesar del perfil, datos de contacto ni valores privados.", "Espacio en blanco para completar en privado")),
            ("en", ("Do not include raw profile text, contact data, or private values.", "Blank for private completion")),
        ):
            with self.subTest(locale=locale):
                rendered = self.renderer.render_dossier_html(make_v2_dossier(locale))
                self.assertIn(expected[0], rendered)
                self.assertIn(expected[1], rendered)
                self.assertEqual(rendered.count('class="coach-template" aria-labelledby='), 3)
                self.assertEqual(rendered.count('aria-describedby="coach-template-boundary-'), 3)

    def test_visible_product_surface_excludes_internal_and_private_values(self) -> None:
        dossier = make_v2_dossier("es")
        rendered_text = visible_text(self.renderer.render_dossier_html(dossier))
        forbidden = {
            "read_only_visible_section_inspection", "pending_response",
            "declined_for_session", "authorization_required",
            "context_action_result_v1", "profile_url", "contact_info",
            "/private/path/profile.json", "https://www.linkedin.com/in/example",
            "person@example.test",
        }
        forbidden.update(record["id"] for record in dossier["evidence"])
        for token in forbidden:
            with self.subTest(token=token):
                self.assertNotIn(token, rendered_text)

    def test_writer_rejects_unsafe_new_coaching_prose_before_creating_visible_output(self) -> None:
        for field, value, diagnostic in UNSAFE_COACHING_PROSE:
            with self.subTest(field=field, diagnostic=diagnostic):
                dossier = make_v2_dossier()
                dossier["priorities"][0][field] = value
                with tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    source = root / "unsafe.json"
                    output = root / "unsafe.html"
                    source.write_text(json.dumps(dossier), encoding="utf-8")
                    with self.assertRaises(self.renderer.DossierValidationError) as context:
                        self.renderer.write_dossier_html(source, output)
                    self.assertFalse(output.exists())
                errors = "\n".join(context.exception.errors)
                self.assertIn(f"priorities[0].{field} {diagnostic}", errors)
                self.assertNotIn(value, errors)

    def test_all_coaching_fields_fail_writer_and_cli_before_output(self) -> None:
        for field in ("coach_observation", "why_it_matters", "coach_prompt"):
            with self.subTest(field=field):
                dossier = make_v2_dossier()
                unsafe = "Conectar contexto y publicar esto en LinkedIn."
                dossier["priorities"][0][field] = unsafe
                with tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    source = root / "unsafe.json"
                    output = root / "unsafe.html"
                    source.write_text(json.dumps(dossier), encoding="utf-8")
                    result = subprocess.run(
                        [sys.executable, "-B", str(VALIDATOR_PATH), str(source)],
                        cwd=REPO_ROOT, text=True, capture_output=True, check=False,
                    )
                    self.assertEqual(result.returncode, 2)
                    self.assertIn(f"priorities[0].{field} must remain a private review action", result.stderr)
                    self.assertNotIn(unsafe, result.stderr)
                    with self.assertRaises(self.renderer.DossierValidationError) as context:
                        self.renderer.write_dossier_html(source, output)
                    self.assertFalse(output.exists())
                errors = "\n".join(context.exception.errors)
                self.assertIn(f"priorities[0].{field} must remain a private review action", errors)
                self.assertNotIn(unsafe, errors)

    def test_market_placeholder_is_one_bounded_non_recommendation_state(self) -> None:
        for name in ("scenario-a-es.json", "scenario-c-en.json"):
            with self.subTest(name=name):
                dossier = json.loads((V2_FIXTURE_ROOT / name).read_text(encoding="utf-8"))
                rendered = self.renderer.render_dossier_html(dossier)
                regions = re.findall(
                    r'<section class="card market-unavailable-card span-12" aria-labelledby="market-unavailable-title">(.*?)</section>',
                    rendered,
                    re.DOTALL,
                )
                self.assertEqual(len(regions), 1)
                text_value = visible_text(regions[0]).casefold()
                self.assertNotIn("<progress", regions[0].casefold())
                self.assertNotRegex(text_value, r"\d+(?:\.\d+)?%")
                for forbidden in (
                    "score", "vacancy", "vacante", "employer", "empleador",
                    "course", "curso", "paid", "pago",
                ):
                    self.assertNotIn(forbidden, text_value)

    def test_no_market_bytes_are_protected_while_complete_market_requires_trusted_group(self) -> None:
        for fixture_name, (byte_count, digest) in NO_MARKET_RENDER_SNAPSHOTS.items():
            with self.subTest(fixture=fixture_name):
                dossier = load_json_fixture(V2_FIXTURE_ROOT / fixture_name)
                rendered = self.renderer.render_dossier_html(dossier)
                self.assertEqual(byte_count, len(rendered.encode("utf-8")))
                self.assertEqual(digest, hashlib.sha256(rendered.encode("utf-8")).hexdigest())

        dossier, market, research, alignment = market_case(
            "complete-five-es.json", "scenario-a-es.json"
        )
        rendered = self.renderer.render_dossier_html(
            dossier,
            market,
            market_research=research,
            market_alignment=alignment,
        )
        self.assertEqual(5, rendered.count('class="vacancy-alignment-card"'))

    def test_dated_market_state_has_a_separate_bounded_truthful_surface(self) -> None:
        source = load_v1_fixture("scenario-market-en.json")
        dossier = make_v2_dossier("en")
        market_evidence = copy.deepcopy(source["evidence"][-1])
        market_evidence["profile_section"] = None
        dossier["evidence"].append(market_evidence)
        dossier["market_context"] = copy.deepcopy(source["market_context"])
        self.assertEqual(self.validator.validate_dossier(dossier), [])
        rendered = self.renderer.render_dossier_html(dossier)
        self.assertIn('class="card market-evidence-available-card span-12"', rendered)
        self.assertNotIn("This dossier includes no market evidence.", rendered)
        surface = re.search(r'<section class="card market-evidence-available-card span-12".*?</section>', rendered, re.DOTALL)
        self.assertIsNotNone(surface)
        for forbidden in ("e-008", "vacancy", "http", "score"):
            self.assertNotIn(forbidden, visible_text(surface.group(0)).casefold())

    def test_complete_market_composition_has_labelled_progress_matrix_recurrence_and_gap_route(self) -> None:
        dossier, market, research, alignment = market_case(
            "complete-five-es.json", "scenario-a-es.json"
        )

        rendered = self.renderer.render_dossier_html(
            dossier,
            market,
            market_research=research,
            market_alignment=alignment,
        )

        self.assertNotIn(
            '<div class="dossier-grid section-block">\n      <section class="section-block market-summary"',
            rendered,
        )

        cards = re.findall(
            r'<article class="vacancy-alignment-card" aria-labelledby="([^"]+)">(.*?)</article>',
            rendered,
            re.DOTALL,
        )
        self.assertEqual(5, len(cards))
        self.assertEqual(
            [(row["employer"], row["title"]) for row in market["vacancies"]],
            [
                (
                    re.search(r'class="vacancy-employer">([^<]+)</', card).group(1),
                    re.search(r'<h3 id="[^"]+">([^<]+)</h3>', card).group(1),
                )
                for _, card in cards
            ],
        )
        for index, ((labelled_by, card), vacancy) in enumerate(
            zip(cards, market["vacancies"], strict=True), start=1
        ):
            employer_id = f"vacancy-alignment-employer-{index}"
            heading_id = f"vacancy-alignment-title-{index}"
            score_id = f"vacancy-alignment-score-{index}"
            self.assertEqual(f"{employer_id} {heading_id}", labelled_by)
            self.assertIn(
                f'<p id="{employer_id}" class="vacancy-employer">', card
            )
            self.assertIn(f'<h3 id="{heading_id}">', card)
            self.assertIn(
                f'<p id="{score_id}" class="vacancy-alignment-score">'
                f'{vacancy["alignment_percent"]} de 100</p>',
                card,
            )
            self.assertRegex(
                card,
                rf'<progress class="vacancy-alignment-progress" value="{vacancy["alignment_percent"]}" '
                rf'max="100" aria-labelledby="{employer_id} {heading_id} {score_id}">',
            )

        audit = DossierDOMAudit()
        audit.feed(rendered)
        self.assertEqual(len(audit.ids), len(set(audit.ids)))
        self.assertEqual(set(), set(audit.references) - set(audit.ids))

        self.assertEqual(1, rendered.count('<table class="market-matrix">'))
        self.assertIn('<caption>Matriz de evidencia de la muestra</caption>', rendered)
        self.assertIn('<th id="market-matrix-col-signal" scope="col">Señal</th>', rendered)
        self.assertIn('<th id="market-matrix-col-profile" scope="col">Evidencia del perfil</th>', rendered)
        vacancy_headers = re.findall(
            r'<th id="market-matrix-col-v([1-5])" scope="col"><span aria-hidden="true">V\1</span>'
            r'<span class="visually-hidden">([^<]+)</span></th>',
            rendered,
        )
        self.assertEqual(5, len(vacancy_headers))
        key_items = re.findall(
            r'<li class="market-vacancy-key-item"><strong>V([1-5])</strong> — ([^<]+)</li>',
            rendered,
        )
        self.assertEqual(5, len(key_items))
        for index, vacancy in enumerate(market["vacancies"], start=1):
            full_label = f'{vacancy["employer"]} · {vacancy["title"]}'
            self.assertIn((str(index), full_label), key_items)
            self.assertIn((str(index), full_label), vacancy_headers)
            self.assertIn(
                f'data-label="V{index} · {full_label}"', rendered
            )

        rows = re.findall(
            r'<tr class="market-matrix-row">(.*?)</tr>', rendered, re.DOTALL
        )
        self.assertEqual(len(market["matrix_rows"]), len(rows))
        for row in rows:
            row_heading = re.search(
                r'<th id="([^"]+)" scope="row">([^<]+)</th>', row
            )
            self.assertIsNotNone(row_heading)
            cells = re.findall(r'<td ([^>]+)>(.*?)</td>', row, re.DOTALL)
            self.assertEqual(6, len(cells))
            for attributes, body in cells:
                self.assertIn('data-label="', attributes)
                self.assertIn('headers="', attributes)
                self.assertRegex(
                    body,
                    r'<span class="matrix-state-symbol" aria-hidden="true">[✓●≈!?—]</span>'
                    r'<span class="matrix-state-text">[^<]+</span>',
                )

        recurrence_rows = re.findall(
            r'<div class="recurrence-row" aria-labelledby="([^"]+)">(.*?)</div>',
            rendered,
            re.DOTALL,
        )
        self.assertEqual(len(market["recurrence_rows"]), len(recurrence_rows))
        for index, ((heading_id, body), row) in enumerate(
            zip(recurrence_rows, market["recurrence_rows"], strict=True), start=1
        ):
            fraction_id = f"recurrence-fraction-{index}"
            self.assertIn(f'id="{heading_id}"', body)
            self.assertIn(
                f'<span id="{fraction_id}" class="recurrence-fraction">'
                f'{row["display_fraction"]}</span>',
                body,
            )
            self.assertRegex(
                body,
                rf'<progress class="recurrence-progress" value="{row["occurrences"]}" '
                rf'max="{row["sample_size"]}" aria-labelledby="{heading_id} {fraction_id}">',
            )
        self.assertNotIn("market demand", visible_text(rendered).casefold())

        route = re.findall(
            r'<section class="gap-closure-route" aria-labelledby="gap-closure-route-title">(.*?)</section>',
            rendered,
            re.DOTALL,
        )
        self.assertEqual(1, len(route))
        self.assertEqual(4, len(re.findall(r'<li>', route[0])))
        for priority in dossier["priorities"]:
            self.assertEqual(1, visible_text(rendered).count(priority["why_it_matters"]))
        market_region = rendered[
            rendered.index('<section class="section-block market-summary"'):
            rendered.index('<section class="section-block" aria-labelledby="copy-title">')
        ]
        market_text = visible_text(market_region)
        for forbidden in ("curso", "course", "certificación", "certification"):
            self.assertNotIn(forbidden, market_text.casefold())

        self.assertNotIn("aria-live", market_region)
        forbidden_values = {
            market["source_research_snapshot"],
            market["source_executive_dossier_snapshot"],
            "Synthetic test requirement.",
        }
        for vacancy in research["vacancies"]:
            forbidden_values.update(
                {
                    vacancy["vacancy_id"],
                    vacancy["employer_id"],
                    vacancy["source_url"],
                    *[item["requirement_id"] for item in vacancy["requirements"]],
                }
            )
            if vacancy["official_referrer_url"] is not None:
                forbidden_values.add(vacancy["official_referrer_url"])
        forbidden_values.update(
            evidence_id
            for row in alignment["signal_bindings"]
            for evidence_id in row["evidence_ids"]
        )
        for value in forbidden_values:
            with self.subTest(forbidden=value):
                self.assertNotIn(value, rendered)

    def test_decide_now_precedes_coverage_and_uses_semantic_references_without_actions_or_echo(self) -> None:
        dossier, market, research, alignment = market_case(
            "complete-five-es.json", "scenario-a-es.json"
        )
        rendered = self.renderer.render_dossier_html(
            dossier,
            market,
            market_research=research,
            market_alignment=alignment,
        )

        references, described_by, region = decide_now_region(rendered)
        self.assertLess(
            rendered.index('class="section-block decide-now"'),
            rendered.index('class="section-block section-coverage-ledger"'),
        )
        pending = self.validator.select_pending_inspection_section(dossier)
        pending_index = next(
            index for index, row in enumerate(dossier["section_coverage"], start=1)
            if row["section"] == pending
        )
        self.assertEqual(
            {
                "coach-priority-title-1",
                "coach-priority-title-2",
                "coach-priority-title-3",
                f"section-coverage-title-{pending_index}",
                "market-context-title",
            },
            references,
        )
        self.assertEqual("decide-now-summary", described_by)
        self.assertNotRegex(region, r"<(?:button|input|select|textarea|form)\b")
        self.assertNotRegex(region, r'<a href="https?://')
        for forbidden in (
            market["source_research_snapshot"],
            market["source_executive_dossier_snapshot"],
            *(
                value
                for vacancy in research["vacancies"]
                for value in (vacancy["vacancy_id"], vacancy["employer_id"], vacancy["source_url"])
            ),
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, region)

        v1_rendered = load_v1_renderer().render_dossier_html(
            load_v1_fixture("scenario-a-es.json")
        )
        self.assertNotIn('class="section-block decide-now"', v1_rendered)

    def test_decide_now_uses_zero_market_without_score_recurrence_or_gap_route(self) -> None:
        dossier, market, research, alignment = market_case(
            "unavailable-es.json", "scenario-a-es.json"
        )
        rendered = self.renderer.render_dossier_html(
            dossier,
            market,
            market_research=research,
            market_alignment=alignment,
        )

        references, _described_by, region = decide_now_region(rendered)
        self.assertIn("market-context-title", references)
        self.assertNotIn("vacancy-alignment", region)
        self.assertNotIn("recurrence-row", region)
        self.assertNotIn("gap-closure-route", region)
        self.assertNotIn("<progress", region)
        self.assertNotRegex(visible_text(region), r"\b\d+(?:\.\d+)?%\b|\b\d+/0\b")

    def test_decide_now_uses_actual_one_to_five_denominators_and_one_pending_authorization(self) -> None:
        for count in range(1, 6):
            with self.subTest(count=count):
                if count == 5:
                    dossier, market, research, alignment = market_case(
                        "complete-five-es.json", "scenario-a-es.json"
                    )
                    authorization = "¿Autorizas inspeccionar"
                else:
                    dossier, market, research, alignment = build_limited_market_case(count)
                    authorization = "Do you authorize read-only inspection"
                rendered = self.renderer.render_dossier_html(
                    dossier,
                    market,
                    market_research=research,
                    market_alignment=alignment,
                )

                _references, _described_by, region = decide_now_region(rendered)
                text = visible_text(region)
                self.assertEqual(1, text.count(authorization))
                self.assertEqual(
                    [row["display_fraction"] for row in market["recurrence_rows"]],
                    re.findall(r"\b\d+/\d+\b", text),
                )
                self.assertTrue(
                    all(f"/{count}" in fraction for fraction in re.findall(r"\b\d+/\d+\b", text))
                )

    def test_decide_now_styles_cover_responsive_print_and_forced_colors_without_fixed_tracks(self) -> None:
        css = (REPO_ROOT / "plugins" / "professional-growth-coach" / "assets" / "career-market-learning-dossier-v1.css").read_text(encoding="utf-8")
        for contract in (
            ".decide-now-card",
            "@media (max-width: 640px)",
            "@media print",
            "@media (forced-colors: active)",
            "@media (prefers-reduced-motion: reduce)",
            "background: Canvas",
            "color: CanvasText",
            "background: Highlight",
            "color: HighlightText",
        ):
            with self.subTest(contract=contract):
                self.assertIn(contract, css)
        self.assertNotIn("min-width: 7rem", css)

    def test_learning_panel_is_omitted_without_bundle_and_for_zero_market(self) -> None:
        dossier, market, research, alignment = market_case(
            "unavailable-es.json", "scenario-a-es.json"
        )
        legacy = self.renderer.render_dossier_html(dossier)
        self.assertNotIn('class="learning-decision"', legacy)
        unavailable = learning_case(
            "unavailable-es.json", "scenario-a-es.json", count=0
        )
        rendered = self.renderer.render_dossier_html(
            unavailable[0],
            unavailable[1],
            market_research=unavailable[2],
            market_alignment=unavailable[3],
            learning_decision=unavailable[4],
        )
        self.assertNotIn('class="learning-decision"', rendered)
        self.assertNotIn("learning-decision-title", rendered)

    def test_learning_panel_renders_three_to_five_conversational_rows_without_private_or_external_content(self) -> None:
        for count in (3, 5):
            with self.subTest(count=count):
                case = learning_case(
                    "complete-five-es.json", "scenario-a-es.json", count=count, decision_count=count
                )
                rendered = self.renderer.render_dossier_html(
                    case[0],
                    case[1],
                    market_research=case[2],
                    market_alignment=case[3],
                    learning_decision=case[4],
                )
                self.assertIn('class="section-block learning-decision"', rendered)
                expected_learning_title = (
                    "Qué estudiar —y qué no comprar aún—"
                    if case[0]["locale"] == "es"
                    else "What to study—and what not to buy yet"
                )
                self.assertIn(expected_learning_title, visible_text(rendered))
                panel = re.search(
                    r'<section class="section-block learning-decision".*?</section>',
                    rendered,
                    re.DOTALL,
                )
                self.assertIsNotNone(panel)
                panel_text = visible_text(panel.group(0))
                expected_signal = self.renderer._signal_label(case[1]["matrix_rows"][0]["signal"])
                self.assertIn(expected_signal, panel_text)
                expected_target_label = "Target role" if case[0]["locale"] != "es" else "Rol objetivo"
                self.assertIn(expected_target_label, panel_text)
                self.assertEqual(
                    count,
                    len(re.findall(r'class="[^"]*\blearning-decision-card\b[^"]*"', panel.group(0))),
                )
                self.assertTrue(
                    "bounded learning hypothesis" in panel_text or "hipótesis acotada" in panel_text
                )
                self.assertNotRegex(panel.group(0), r"<(?:button|input|select|textarea|form)\b")
                self.assertNotRegex(panel.group(0), r'<a href="https?://')
                for forbidden in (
                    *(
                        value
                        for vacancy in case[2]["vacancies"]
                        for value in (vacancy["vacancy_id"], vacancy["employer_id"], vacancy["source_url"])
                    ),
                    *(
                        evidence_id
                        for row in case[4]["decisions"]
                        for evidence_id in row["source_gap_ids"]
                    ),
                    case[4]["source_market_snapshot"],
                    case[4]["source_dossier_snapshot"],
                    case[4]["source_research_snapshot"],
                ):
                    self.assertNotIn(forbidden, panel.group(0))
                self.assertLess(
                    rendered.index('class="section-block learning-decision"'),
                    rendered.index('class="gap-closure-route"'),
                )

    def test_learning_panel_has_one_decide_now_internal_anchor_and_rejects_invalid_bundle_before_output(self) -> None:
        case = learning_case("complete-five-es.json", "scenario-a-es.json", count=3)
        rendered = self.renderer.render_dossier_html(
            case[0],
            case[1],
            market_research=case[2],
            market_alignment=case[3],
            learning_decision=case[4],
        )
        references, _described_by, decide_region = decide_now_region(rendered)
        self.assertIn("learning-decision-title", references)
        self.assertEqual(1, decide_region.count('href="#learning-decision-title"'))
        for field, unsafe_text in (
            ("option_name", "file:///Users/private/profile.json"),
            ("option_name", "Enroll now: example course"),
            ("target_role", "candidate name Example Person Senior SRE"),
            ("decision_basis", "Guaranteed interview preparation"),
            ("option_name", "Buy this course"),
            ("next_action_gate", "exact authorization required before Send a message"),
            ("target_role", "example.com/profile"),
            ("provider_or_owner", "ID-12345"),
            ("option_name", "Compra este curso"),
            ("decision_basis", "Te ayuda a conseguir empleo"),
            ("option_name", "case-123456"),
            ("option_name", "case-123"),
            ("provider_or_owner", "private-id-x"),
            ("option_name", "ID-1"),
            ("provider_or_owner", "account-id-xy"),
            ("decision_basis", "foo.ai/profile"),
            ("decision_basis", "foo.xyz/profile"),
            ("option_name", "Ensures an interview"),
            ("option_name", "Esta opción garantiza contratación"),
        ):
            with self.subTest(field=field, unsafe_text=unsafe_text):
                invalid = copy.deepcopy(case[4])
                invalid["decisions"][0][field] = unsafe_text
                with self.assertRaises(self.renderer.DossierValidationError) as raised:
                    self.renderer.render_dossier_html(
                        case[0],
                        case[1],
                        market_research=case[2],
                        market_alignment=case[3],
                        learning_decision=invalid,
                    )
                self.assertNotIn(unsafe_text, "\n".join(raised.exception.errors))
        for invalid in ({}, "not-a-learning-mapping"):
            with self.subTest(invalid=type(invalid).__name__):
                with self.assertRaises(self.renderer.DossierValidationError):
                    self.renderer.render_dossier_html(
                        case[0],
                        case[1],
                        market_research=case[2],
                        market_alignment=case[3],
                        learning_decision=invalid,
                    )

    def test_learning_panel_uses_dynamic_one_to_five_sample_counts(self) -> None:
        for count in range(1, 6):
            with self.subTest(count=count):
                case = learning_case(
                    "complete-five-es.json", "scenario-a-es.json", count=count
                )
                rendered = self.renderer.render_dossier_html(
                    case[0],
                    case[1],
                    market_research=case[2],
                    market_alignment=case[3],
                    learning_decision=case[4],
                )
                panel = re.search(
                    r'<section class="section-block learning-decision".*?</section>',
                    rendered,
                    re.DOTALL,
                )
                self.assertIsNotNone(panel)
                self.assertIn(f"N={count}", visible_text(panel.group(0)))

    def test_learning_decision_styles_cover_responsive_print_dark_forced_colors_and_motion(self) -> None:
        css = (REPO_ROOT / "plugins" / "professional-growth-coach" / "assets" / "career-market-learning-dossier-v1.css").read_text(encoding="utf-8")
        for contract in (
            ".learning-decision-card",
            "@media (max-width: 640px)",
            "@media screen and (prefers-color-scheme: dark)",
            "@media print",
            "@media (forced-colors: active)",
            "@media (prefers-reduced-motion: reduce)",
            "background: Canvas",
            "color: CanvasText",
            "background: Highlight",
            "color: HighlightText",
        ):
            with self.subTest(contract=contract):
                self.assertIn(contract, css)

    def test_limited_market_composition_uses_dynamic_n_without_padding(self) -> None:
        for count in (1, 2, 3, 4):
            with self.subTest(count=count):
                dossier, market, research, alignment = build_limited_market_case(count)
                rendered = self.renderer.render_dossier_html(
                    dossier,
                    market,
                    market_research=research,
                    market_alignment=alignment,
                )
                self.assertEqual(count, rendered.count('class="vacancy-alignment-card"'))
                self.assertEqual(count, rendered.count('class="vacancy-alignment-progress"'))
                self.assertEqual(count, rendered.count('class="market-vacancy-key-item"'))
                self.assertEqual(
                    [f"{row['occurrences']}/{count}" for row in market["recurrence_rows"]],
                    re.findall(r'class="recurrence-fraction">([^<]+)</span>', rendered),
                )
                for index in range(1, count + 1):
                    self.assertIn(f'id="market-matrix-col-v{index}"', rendered)
                self.assertNotIn(f'id="market-matrix-col-v{count + 1}"', rendered)
                self.assertNotIn("Synthetic test limit.", rendered)
                self.assertEqual(
                    1,
                    rendered.count(
                        "The bounded search ended before five vacancies were gathered."
                    ),
                )

    def test_validated_unavailable_market_bundle_is_distinct_from_legacy_placeholder(self) -> None:
        dossier, market, research, alignment = market_case(
            "unavailable-es.json", "scenario-a-es.json"
        )
        legacy = self.renderer.render_dossier_html(dossier)
        rendered = self.renderer.render_dossier_html(
            dossier,
            market,
            market_research=research,
            market_alignment=alignment,
        )

        self.assertIn(COPY_MARKET_PLACEHOLDER_ES, legacy)
        self.assertNotIn("Synthetic test unavailability.", legacy)
        self.assertNotIn(COPY_MARKET_PLACEHOLDER_ES, rendered)
        self.assertNotIn("Synthetic test unavailability.", rendered)
        self.assertEqual(
            1,
            rendered.count(
                "La búsqueda acotada no produjo vacantes verificables para esta muestra."
            ),
        )
        self.assertEqual(1, rendered.count('class="card market-unavailable-card span-12"'))
        self.assertEqual(1, rendered.count('aria-labelledby="market-context-title"'))
        self.assertEqual(0, rendered.count('class="vacancy-alignment-progress"'))
        self.assertEqual(0, rendered.count('class="recurrence-row"'))
        self.assertNotIn('<table class="market-matrix">', rendered)
        unavailable_region = re.findall(
            r'<section class="section-block market-summary" aria-labelledby="market-context-title">(.*?)</section>',
            rendered,
            re.DOTALL,
        )
        self.assertEqual(1, len(unavailable_region))
        self.assertNotIn("<section", unavailable_region[0])
        self.assertNotRegex(visible_text(unavailable_region[0]), r"\b\d+(?:\.\d+)?%\b")
        for forbidden in (
            market["source_research_snapshot"],
            market["source_executive_dossier_snapshot"],
        ):
            self.assertNotIn(forbidden, rendered)

    def test_market_inputs_are_all_or_none_and_trusted_composition_rejects_source_mutation(self) -> None:
        dossier, market, research, alignment = market_case(
            "complete-five-es.json", "scenario-a-es.json"
        )
        values = {
            "market_dossier": market,
            "market_research": research,
            "market_alignment": alignment,
        }
        names = tuple(values)
        for mask in range(1, 7):
            kwargs = {
                name: values[name] if mask & (1 << index) else None
                for index, name in enumerate(names)
            }
            with self.subTest(partial=tuple(name for name, value in kwargs.items() if value is not None)):
                with self.assertRaises(self.renderer.DossierValidationError):
                    self.renderer.render_dossier_html(dossier, **kwargs)

        mutations = []
        changed_research = copy.deepcopy(research)
        changed_research["vacancies"][0]["title"] = "Changed fixture role"
        mutations.append((market, changed_research, alignment, "Changed fixture role"))
        changed_alignment = copy.deepcopy(alignment)
        changed_alignment["research_snapshot"] = "snap-market-sha256-" + "0" * 64
        mutations.append((market, research, changed_alignment, "0" * 64))
        for field, value in (
            ("source_research_snapshot", "snap-market-sha256-" + "1" * 64),
            ("source_executive_dossier_snapshot", "snap-dossier-sha256-" + "2" * 64),
        ):
            changed_market = copy.deepcopy(market)
            changed_market[field] = value
            mutations.append((changed_market, research, alignment, value))
        changed_market = copy.deepcopy(market)
        changed_market["matrix_rows"][0]["evidence_ids"] = ["E-999"]
        mutations.append((changed_market, research, alignment, "E-999"))
        changed_market = copy.deepcopy(market)
        changed_market["matrix_rows"][0]["cells"][1]["requirements"][0]["source_paraphrase"] = "Changed paraphrase."
        mutations.append((changed_market, research, alignment, "Changed paraphrase."))
        changed_market = copy.deepcopy(market)
        changed_market["vacancies"][0]["employer"] = "Changed employer"
        mutations.append((changed_market, research, alignment, "Changed employer"))

        for changed_market, changed_research, changed_alignment, sentinel in mutations:
            with self.subTest(sentinel=sentinel):
                with self.assertRaises(self.renderer.DossierValidationError) as context:
                    self.renderer.render_dossier_html(
                        dossier,
                        changed_market,
                        market_research=changed_research,
                        market_alignment=changed_alignment,
                    )
                self.assertNotIn(sentinel, "\n".join(context.exception.errors))


    def test_shipped_fixtures_have_complete_resolved_noninteractive_dom(self) -> None:
        for name in ("scenario-a-es.json", "scenario-c-en.json"):
            with self.subTest(name=name):
                dossier = json.loads((V2_FIXTURE_ROOT / name).read_text(encoding="utf-8"))
                rendered = self.renderer.render_dossier_html(dossier)
                audit = DossierDOMAudit()
                audit.feed(rendered)

                self.assertEqual(audit.tag_counts.get("h1"), 1)
                self.assertEqual(audit.tag_counts.get("main"), 1)
                self.assertEqual(audit.tag_counts.get("footer"), 1)
                self.assertEqual(len(audit.ids), len(set(audit.ids)))
                self.assertEqual(set(audit.references) - set(audit.ids), set())
                self.assertEqual(audit.classes.count("section-coverage-row"), 17)
                self.assertEqual(audit.classes.count("coach-priority-card"), 3)
                self.assertEqual(audit.classes.count("market-unavailable-card"), 1)
                self.assertNotIn('data-priority-card="true"', rendered)
                self.assertNotIn('class="timebox"', rendered)
                skip_links = [
                    attrs for tag, attrs in audit.start_tags
                    if tag == "a" and "skip-link" in (attrs.get("class") or "").split()
                ]
                self.assertEqual(len(skip_links), 1)
                self.assertEqual(skip_links[0].get("href"), "#main-content")
                main_targets = [attrs for tag, attrs in audit.start_tags if tag == "main"]
                self.assertEqual(len(main_targets), 1)
                self.assertEqual(main_targets[0].get("id"), "main-content")
                self.assertEqual(main_targets[0].get("tabindex"), "-1")
                self.assertEqual(audit.heading_levels[0], 1)
                self.assertEqual(set(audit.heading_levels), {1, 2, 3, 4})
                self.assertTrue(
                    all(
                        next_level <= level + 1
                        for level, next_level in zip(audit.heading_levels, audit.heading_levels[1:])
                    )
                )
                templates = re.findall(
                    r'<section class="coach-template"[^>]*>(.*?)</section>',
                    rendered,
                    re.DOTALL,
                )
                self.assertEqual(len(templates), 3)
                for template in templates:
                    self.assertNotRegex(
                        template,
                        r"<(?:a|button|input|select|textarea)\b",
                    )

    def test_chat_summary_asks_exactly_one_first_pending_authorization_question(self) -> None:
        summary = self.renderer.build_chat_summary(make_v2_dossier("es"))
        self.assertIn(
            "¿Autorizas inspeccionar en modo solo lectura la sección Nombre durante esta sesión?",
            summary,
        )
        self.assertNotIn("Certificaciones", summary)
        self.assertEqual(summary.count("¿Autorizas inspeccionar"), 1)
        self.assertNotIn(make_v2_dossier("es")["questions"][0]["question"], summary)
        self.assertLessEqual(len(summary.split()), 180)

        english = json.loads(
            (V2_FIXTURE_ROOT / "scenario-c-en.json").read_text(encoding="utf-8")
        )
        summary = self.renderer.build_chat_summary(english)
        self.assertIn(
            "Do you authorize read-only inspection of the Banner section during this session?",
            summary,
        )
        self.assertEqual(summary.count("Do you authorize read-only inspection"), 1)
        self.assertNotIn(
            "Do you authorize read-only inspection of the Name section during this session?",
            summary,
        )
        self.assertNotIn("Certifications", summary)
        self.assertLessEqual(len(summary.split()), 180)

    def test_chat_summary_executes_every_localized_section_question(self) -> None:
        renderer = load_renderer()
        for locale, questions in renderer.AUTHORIZATION_QUESTIONS.items():
            for section, expected in questions.items():
                with self.subTest(locale=locale, section=section):
                    dossier = make_v2_dossier(locale)
                    for row in dossier["section_coverage"]:
                        request = row.get("inspection_request")
                        if isinstance(request, dict):
                            row["reason"] = "inspection_declined"
                            request["decision"] = "declined_for_session"
                    target = next(row for row in dossier["section_coverage"] if row["section"] == section)
                    scope = dossier["evidence_scope"]
                    scope["inspected_sections"] = [name for name in scope["inspected_sections"] if name != section]
                    target.update({
                        "availability": "unavailable",
                        "evidence_state": "unknown",
                        "reason": "authorization_required",
                        "inspection_request": {
                            "access_type": "read_only_visible_section_inspection",
                            "decision": "pending_response",
                            "scope": "current_session_only",
                            "carry_forward": False,
                        },
                    })
                    summary = renderer.build_chat_summary(dossier)
                    matches = [question for question in questions.values() if question in summary]
                    self.assertEqual(matches, [expected])
                    self.assertEqual(summary.count(expected), 1)

    def test_chat_summary_declined_and_failed_requests_keep_the_fallback_question(self) -> None:
        renderer = load_renderer()
        for locale in renderer.AUTHORIZATION_QUESTIONS:
            with self.subTest(locale=locale):
                dossier = make_v2_dossier(locale)
                for row in dossier["section_coverage"]:
                    request = row.get("inspection_request")
                    if isinstance(request, dict):
                        row["reason"] = "inspection_declined"
                        request["decision"] = "declined_for_session"
                failed = next(row for row in dossier["section_coverage"] if row["section"] == "featured")
                failed["reason"] = "authorized_inspection_failed"
                failed["inspection_request"]["decision"] = "authorized_inspection_failed"
                summary = renderer.build_chat_summary(dossier)
                self.assertIn(dossier["questions"][0]["question"], summary)
                self.assertFalse(any(question in summary for question in renderer.AUTHORIZATION_QUESTIONS[locale].values()))

    def test_chat_summary_retains_v1_behavior_when_no_inspection_request_is_pending(self) -> None:
        dossier = make_v2_dossier("en")
        for row in dossier["section_coverage"]:
            request = row.get("inspection_request")
            if isinstance(request, dict) and request["decision"] == "pending_response":
                row["reason"] = "inspection_declined"
                request["decision"] = "declined_for_session"
        summary = self.renderer.build_chat_summary(dossier)
        self.assertNotIn("Do you authorize read-only inspection", summary)
        self.assertIn(dossier["questions"][0]["question"], summary)

    def test_shipped_fixtures_are_valid_and_project_deep_equal_to_v1_sources(self) -> None:
        for name in ("scenario-a-es.json", "scenario-c-en.json"):
            with self.subTest(name=name):
                source = load_v1_fixture(name)
                dossier = json.loads((V2_FIXTURE_ROOT / name).read_text(encoding="utf-8"))
                self.assertEqual(self.validator.validate_dossier(dossier), [])
                self.assertEqual(self.validator.project_v2_to_v1(dossier), source)

    def test_shipped_fixture_ledger_uses_the_required_pending_and_declined_matrix(self) -> None:
        for name in ("scenario-a-es.json", "scenario-c-en.json"):
            with self.subTest(name=name):
                dossier = json.loads((V2_FIXTURE_ROOT / name).read_text(encoding="utf-8"))
                evidence_sections = {
                    record["profile_section"]
                    for record in dossier["evidence"]
                    if record["profile_section"] is not None
                }
                rows = {row["section"]: row for row in dossier["section_coverage"]}
                self.assertEqual(rows["featured"]["reason"], "authorization_required")
                self.assertEqual(rows["featured"]["inspection_request"]["decision"], "pending_response")
                self.assertEqual(rows["certifications"]["reason"], "inspection_declined")
                self.assertEqual(rows["certifications"]["inspection_request"]["decision"], "declined_for_session")
                self.assertEqual(dossier["analytics"]["state"], "not_requested")
                for section in CANONICAL_PROFILE_SECTIONS:
                    if section in evidence_sections or section == "certifications":
                        continue
                    self.assertEqual(rows[section]["availability"], "unavailable")
                    self.assertEqual(rows[section]["reason"], "authorization_required")
                    self.assertEqual(rows[section]["inspection_request"]["decision"], "pending_response")

    def test_writer_keeps_the_v2_artifact_private(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "dossier-v2.html"
            receipt = self.renderer.write_dossier_html(
                V2_FIXTURE_ROOT / "scenario-a-es.json", output
            )
            self.assertEqual(stat.S_IMODE(output.stat().st_mode), 0o600)
            self.assertEqual(receipt.artifact_type, "text/html")


    def test_writer_loads_complete_market_group_once_and_keeps_output_private(self) -> None:
        dossier, market, research, alignment = market_case(
            "complete-five-es.json", "scenario-a-es.json"
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = {}
            for name, value in (
                ("dossier", dossier),
                ("market", market),
                ("research", research),
                ("alignment", alignment),
            ):
                path = root / f"{name}.json"
                path.write_text(json.dumps(value), encoding="utf-8")
                paths[name] = path
            output = root / "dossier-with-market.html"
            receipt = self.renderer.write_dossier_html(
                paths["dossier"],
                output,
                market_dossier_path=paths["market"],
                market_research_path=paths["research"],
                market_alignment_path=paths["alignment"],
            )

            self.assertTrue(receipt.artifact_path.is_absolute())
            self.assertEqual(0o600, stat.S_IMODE(output.stat().st_mode))
            self.assertEqual(5, output.read_text(encoding="utf-8").count('class="vacancy-alignment-card"'))
            with self.assertRaises(FileExistsError):
                self.renderer.write_dossier_html(
                    paths["dossier"],
                    output,
                    market_dossier_path=paths["market"],
                    market_research_path=paths["research"],
                    market_alignment_path=paths["alignment"],
                )
            receipt = self.renderer.write_dossier_html(
                paths["dossier"],
                output,
                market_dossier_path=paths["market"],
                market_research_path=paths["research"],
                market_alignment_path=paths["alignment"],
                force=True,
            )
            self.assertTrue(receipt.artifact_path.is_absolute())
            self.assertTrue(os.path.samefile(output, receipt.artifact_path))

    def test_writer_rejects_partial_market_path_group_before_creating_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "partial.html"
            with self.assertRaises(self.renderer.DossierValidationError):
                self.renderer.write_dossier_html(
                    V2_FIXTURE_ROOT / "scenario-a-es.json",
                    output,
                    market_dossier_path=MARKET_FIXTURE_ROOT / "complete-five-es.json",
                )
            self.assertFalse(output.exists())

    def test_writer_and_cli_reject_invalid_learning_before_creating_an_artifact(self) -> None:
        dossier, market, research, alignment, bundle = learning_case(
            "complete-five-es.json", "scenario-a-es.json", count=3
        )
        bundle["decisions"][0]["option_name"] = "Enroll now: example course"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = {}
            for name, value in (
                ("dossier", dossier),
                ("market", market),
                ("research", research),
                ("alignment", alignment),
                ("learning", bundle),
            ):
                path = root / f"{name}.json"
                path.write_text(json.dumps(value), encoding="utf-8")
                paths[name] = path
            writer_output = root / "writer.html"
            with self.assertRaises(self.renderer.DossierValidationError):
                self.renderer.write_dossier_html(
                    paths["dossier"], writer_output,
                    market_dossier_path=paths["market"],
                    market_research_path=paths["research"],
                    market_alignment_path=paths["alignment"],
                    learning_decision_path=paths["learning"],
                )
            self.assertFalse(writer_output.exists())
            cli_output = root / "cli.html"
            result = subprocess.run(
                [
                    sys.executable, "-B", str(RENDERER_PATH), str(paths["dossier"]),
                    "--market-dossier", str(paths["market"]),
                    "--market-research", str(paths["research"]),
                    "--market-alignment", str(paths["alignment"]),
                    "--learning-decision", str(paths["learning"]),
                    "--output", str(cli_output),
                ],
                cwd=root, capture_output=True, text=True, check=False, timeout=20,
            )
            self.assertEqual(2, result.returncode)
            self.assertFalse(cli_output.exists())

class ExecutiveCareerDossierV2LoadAndCliTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.validator = load_validator()

    def test_loader_uses_fixed_errors_for_malformed_private_inputs(self) -> None:
        cases = ((b'{"locale":"es","locale":"en"}', "duplicate JSON key"), (b'\xff', "v2 dossier must be valid UTF-8 JSON"), (b'[]', "v2 dossier must be a JSON object"))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for index, (raw, message) in enumerate(cases):
                with self.subTest(message=message):
                    path = root / f"case-{index}.json"
                    path.write_bytes(raw)
                    with self.assertRaisesRegex(self.validator.DossierLoadError, message):
                        self.validator.load_dossier(path)

    def test_loader_rejects_depth_size_fifo_and_symlinks(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            deep = root / "deep.json"; deep.write_text('{"a":' + "[" * 14 + "0" + "]" * 14 + "}", encoding="utf-8")
            with self.assertRaisesRegex(self.validator.DossierLoadError, "maximum nesting depth"):
                self.validator.load_dossier(deep)
            oversized = root / "large.json"; oversized.write_bytes(b" " * (256 * 1024 + 1))
            with self.assertRaisesRegex(self.validator.DossierLoadError, "256 KiB"):
                self.validator.load_dossier(oversized)
            target = root / "target.json"; target.write_text("{}", encoding="utf-8")
            link = root / "link.json"; link.symlink_to(target)
            with self.assertRaisesRegex(self.validator.DossierLoadError, "symlink"):
                self.validator.load_dossier(link)
            linked_parent = root / "linked-parent"; linked_parent.symlink_to(root, target_is_directory=True)
            with self.assertRaisesRegex(self.validator.DossierLoadError, "cannot read v2 dossier"):
                self.validator.load_dossier(linked_parent / "target.json")
            fifo = root / "input.fifo"; os.mkfifo(fifo)
            with self.assertRaisesRegex(self.validator.DossierLoadError, "cannot read v2 dossier"):
                self.validator.load_dossier(fifo)

    def test_cli_returns_bounded_non_echoing_diagnostics(self) -> None:
        for sentinel in ("person@example.test", "https://example.test/private", "/private/path.json", "line\nbreak", "ansi\x1b[31m", "bidi\u202evalue"):
            with self.subTest(sentinel=repr(sentinel)):
                dossier = make_v2_dossier()
                dossier[sentinel] = "bad"
                with tempfile.TemporaryDirectory() as directory:
                    path = Path(directory) / "invalid.json"
                    path.write_text(json.dumps(dossier), encoding="utf-8")
                    result = subprocess.run([sys.executable, "-B", str(VALIDATOR_PATH), str(path)], cwd=REPO_ROOT, text=True, capture_output=True, check=False)
                self.assertEqual(result.returncode, 2)
                self.assertTrue(result.stderr)
                self.assertLessEqual(len(result.stderr.encode("utf-8")), 16 * 1024)
                self.assertNotIn("Traceback", result.stderr)
                self.assertNotIn(sentinel, result.stderr)

    def test_cli_rejects_row_request_and_template_attacks_without_traceback(self) -> None:
        mutations = (
            ("row", "session_id", "opaque-session-value"),
            ("request", "authorization_granted", True),
            ("template", "field_keys", [{"x": "y"}]),
            ("template", "field_keys", [["context"]]),
        )
        for boundary, key, value in mutations:
            with self.subTest(boundary=boundary, key=key):
                dossier = make_v2_dossier()
                if boundary == "row":
                    dossier["section_coverage"][10][key] = value
                elif boundary == "request":
                    dossier["section_coverage"][10]["inspection_request"][key] = value
                else:
                    dossier["priorities"][0]["client_template"][key] = value
                with tempfile.TemporaryDirectory() as directory:
                    path = Path(directory) / "invalid.json"
                    path.write_text(json.dumps(dossier), encoding="utf-8")
                    result = subprocess.run([sys.executable, "-B", str(VALIDATOR_PATH), str(path)], cwd=REPO_ROOT, text=True, capture_output=True, check=False)
                self.assertEqual(result.returncode, 2)
                self.assertNotIn("Traceback", result.stderr)
                self.assertLessEqual(len(result.stderr.encode("utf-8")), 16 * 1024)

    def test_cli_rejects_unsafe_new_coaching_prose_with_fixed_non_echoing_diagnostics(self) -> None:
        for field, value, diagnostic in UNSAFE_COACHING_PROSE:
            with self.subTest(field=field, diagnostic=diagnostic):
                dossier = make_v2_dossier()
                dossier["priorities"][0][field] = value
                with tempfile.TemporaryDirectory() as directory:
                    path = Path(directory) / "unsafe.json"
                    path.write_text(json.dumps(dossier), encoding="utf-8")
                    result = subprocess.run(
                        [sys.executable, "-B", str(VALIDATOR_PATH), str(path)],
                        cwd=REPO_ROOT,
                        text=True,
                        capture_output=True,
                        check=False,
                    )
                self.assertEqual(result.returncode, 2)
                self.assertIn(f"priorities[0].{field} {diagnostic}", result.stderr)
                self.assertNotIn("Traceback", result.stderr)
                self.assertNotIn(value, result.stderr)
                self.assertLessEqual(len(result.stderr.encode("utf-8")), 16 * 1024)

    def test_cli_decoder_recursion_and_truncation_are_bounded(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            recursive = root / "recursive.json"
            recursive.write_text("[" * 1200 + "0" + "]" * 1200, encoding="utf-8")
            result = subprocess.run([sys.executable, "-B", str(VALIDATOR_PATH), str(recursive)], cwd=REPO_ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(result.returncode, 2)
            self.assertNotIn("Traceback", result.stderr)
            invalid = make_v2_dossier()
            invalid["section_coverage"] = [None] * 700
            path = root / "many-errors.json"
            path.write_text(json.dumps(invalid), encoding="utf-8")
            result = subprocess.run([sys.executable, "-B", str(VALIDATOR_PATH), str(path)], cwd=REPO_ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(result.returncode, 2)
            self.assertLessEqual(len(result.stderr.encode("utf-8")), 16 * 1024)
            self.assertIn("validation diagnostics truncated; additional errors omitted", result.stderr)

    def test_cli_accepts_a_valid_v2_dossier(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "valid.json"
            path.write_text(json.dumps(make_v2_dossier()), encoding="utf-8")
            result = subprocess.run([sys.executable, "-B", str(VALIDATOR_PATH), str(path)], cwd=REPO_ROOT, text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")

    def test_renderer_cli_accepts_all_market_flags_and_emits_one_private_receipt_line(self) -> None:
        dossier, _market, research, alignment = market_case(
            "complete-five-es.json", "scenario-a-es.json"
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            alignment_path = root / "alignment.json"
            alignment_path.write_text(json.dumps(alignment), encoding="utf-8")
            output = root / "rendered.html"
            result = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(RENDERER_PATH),
                    str(V2_FIXTURE_ROOT / "scenario-a-es.json"),
                    "--output",
                    str(output),
                    "--market-dossier",
                    str(MARKET_FIXTURE_ROOT / "complete-five-es.json"),
                    "--market-research",
                    str(RESEARCH_FIXTURE_ROOT / "complete-five-es.json"),
                    "--market-alignment",
                    str(alignment_path),
                ],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual(1, len(result.stdout.splitlines()))
            receipt = json.loads(result.stdout)
            self.assertTrue(Path(receipt["artifact_path"]).is_absolute())
            self.assertTrue(os.path.samefile(output, receipt["artifact_path"]))
            self.assertEqual(0o600, stat.S_IMODE(output.stat().st_mode))
            self.assertEqual(5, output.read_text(encoding="utf-8").count('class="vacancy-alignment-card"'))

            partial = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(RENDERER_PATH),
                    str(V2_FIXTURE_ROOT / "scenario-a-es.json"),
                    "--output",
                    str(root / "partial.html"),
                    "--market-research",
                    str(RESEARCH_FIXTURE_ROOT / "complete-five-es.json"),
                ],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(2, partial.returncode)
            self.assertFalse((root / "partial.html").exists())
            self.assertNotIn("Traceback", partial.stderr)
