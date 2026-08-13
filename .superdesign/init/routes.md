# Artifact routes and entry points

There is no web router. The plugin exposes deterministic CLI entry points that write offline HTML artifacts.

| Artifact | Entry point | Template | Stylesheet |
| --- | --- | --- | --- |
| Executive career dossier | `scripts/render_executive_career_dossier.py` | `assets/executive-career-dossier-v1.html` | `assets/executive-career-dossier-v1.css` |
| Recruiter reply triage | `scripts/render_private_recruiter_reply_triage.py` | `assets/private-recruiter-reply-triage-v1.html` | `assets/private-recruiter-reply-triage-v1.css` |
| Recruiter practice session | `scripts/render_recruiter_practice_session.py` | `assets/recruiter-practice-session-v1.html` | `assets/recruiter-practice-session-v1.css` |
| Conversion outcome receipt | `scripts/render_private_recruiter_conversion_outcome.py` | `assets/private-recruiter-conversion-outcome-v1.html` | `assets/private-recruiter-conversion-outcome-v1.css` |
| Follow-through checkpoint receipt | `scripts/render_private_recruiter_followthrough_checkpoint.py` | `assets/private-recruiter-followthrough-checkpoint-v1.html` | `assets/private-recruiter-followthrough-checkpoint-v1.css` |

All routes are local-file artifacts. The privacy contract forbids external fetches and preserves no-action/manual-handoff boundaries.
