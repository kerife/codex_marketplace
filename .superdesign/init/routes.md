# Artifact routes and entry points

There is no web router. The plugin exposes deterministic CLI entry points that write offline HTML artifacts.

| Artifact | Entry point | Template | Stylesheet |
| --- | --- | --- | --- |
| Executive career dossier v1 | `scripts/render_executive_career_dossier.py` | `assets/executive-career-dossier-v1.html` | `assets/executive-career-dossier-v1.css` |
| Executive career dossier v2 | `scripts/render_executive_career_dossier_v2.py` | v1 HTML shell plus validated fragments | `assets/executive-career-dossier-v1.css` + `assets/executive-career-dossier-v2.css` |
| Recruiter reply triage | `scripts/render_private_recruiter_reply_triage.py` | `assets/private-recruiter-reply-triage-v1.html` | `assets/private-recruiter-reply-triage-v1.css` |
| Recruiter practice session | `scripts/render_recruiter_practice_session.py` | `assets/recruiter-practice-session-v1.html` | `assets/recruiter-practice-session-v1.css` |
| Conversion outcome receipt | `scripts/render_private_recruiter_conversion_outcome.py` | `assets/private-recruiter-conversion-outcome-v1.html` | `assets/private-recruiter-conversion-outcome-v1.css` |
| Follow-through checkpoint receipt | `scripts/render_private_recruiter_followthrough_checkpoint.py` | `assets/private-recruiter-followthrough-checkpoint-v1.html` | `assets/private-recruiter-followthrough-checkpoint-v1.css` |
| Private vacancy application packet | `scripts/render_private_vacancy_application_packet_v1.py` | `assets/private-vacancy-application-packet-v1.html` | `assets/private-vacancy-application-packet-v1.css` |

All routes are local-file artifacts. The privacy contract forbids external fetches and preserves no-action/manual-handoff boundaries.

The v2 route accepts optional, prevalidated offline market and learning bundles;
they are inputs to the dossier artifact rather than additional routes. Version 1
composition requires its alignment input. Version 2 composition recomputes
alignment, accepts market-only input without provider research, and requires
independently validated provider research when learning v2 is present. Versions
cannot be mixed. The market-only Decide ahora / Decide now and proof-to-cost
learning cards are omitted when market evidence is unavailable. DecisionTrace
is a rendered coach-priority subcomponent, not a persisted route or standalone
artifact. LearningSignalRoute is the compact, ARIA-labelled per-decision group
that projects public term labels, localized support, vacancy ordinals,
recurrence, deterministic basis, and localized decision without source values.

The v3 route accepts `career-learning-decision-v3` only with its response,
assessment, and eligibility sources. WeeklyDecision is a rendered subcomponent,
not a separate route: it is the sole primary weekly imperative and leaves the
inspection authorization visibly secondary. Its v3-only stylesheet is
`assets/career-learning-eligibility-v1.css`; unavailable eligibility omits the
card and preserves the existing safe step.

The private vacancy packet route captures and validates the packet plus its source group once, then writes a mode-600 HTML artifact atomically. JSON and HTML writers can consume the same in-process opaque snapshot; neither route authorizes an external action.

| Private first-interview conversion board | `scripts/render_private_first_interview_conversion_board_v1.py` | `assets/private-first-interview-conversion-board-v1.html` | `assets/private-first-interview-conversion-board-v1.css` |
| Private first-interview conversion board v2 | `scripts/render_private_first_interview_conversion_board_v2.py` | `assets/private-first-interview-conversion-board-v2.html` | `assets/private-first-interview-conversion-board-v2.css` |

This explicit private route sits after recruiter triage and before manual
`prepare-role-interviews`; it is source-bound, offline, draft-only, and never
performs external action.

The v2 board consumes the sanitized proof only. Its fixed trust strip is read
after the decision and before preparation detail: synthetic fixtures are
labelled as test data, composition-only sources ask for source review, original
text is not stored, and manual review remains required.
