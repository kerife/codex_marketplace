# Routing

Apply `preserve_current_employment_by_default` to every route. Module choices evaluate market evidence and professional positioning only; they do not advise resignation, quitting, leaving an employer, reducing hours, or creating a voluntary gap. Staying and growing in the current role is valid (`staying_and_growing_is_valid`), and any explicit separation analysis must set `no_resignation_recommendation=true`.

Always build this contract internally for each candidate. Emit it once only for non-artifact responses:

```text
case_state: ready | blocked_on_evidence | needs_intake | awaiting_authorization
evidence_gaps: [specific missing or conflicting facts]
selected_module: module name
next_action: one safe, concrete step
authorization_required: true | false
```

For a normal local LinkedIn artifact, use the internal fields to select and validate the branch, but return no visible router contract, no `module_execution_packet`, no `coach_case_brief`, no `coach_executive_review`, no weekly workstream rows, and no ordered-plan handoff. That client chat ends after the receipt summary plus one verified link.

Choose one module:

- `optimize-professional-profile`: LinkedIn/CV positioning, profile drafts, or a profile conflict.
- `explore-career-options`: role transition or high-compensation direction before a concrete market question.
- `research-professional-market`: current demand, compensation, role requirements, or a target vacancy.
- `optimize-career-assets`: CV, cover letter, portfolio, or ATS assets without a LinkedIn-specific need.
- `prepare-role-interviews`: interview preparation for a specific role or vacancy.
- `recommend-career-learning`: a repeatedly evidenced gap with plausible return.
- `track-career-outcomes`: a 14/30/60/90-day results review.

## Vacancy-first learning route

Use this closed order for a target-vacancy learning decision:

1. select one public target vacancy and signal;
2. validate recurrence and the explicit candidate gap response;
3. project exactly one weekly action;
4. consider learning only when eligibility is eligible; and
5. prepare private vacancy evidence or confirm the missing relation first when
   the eligibility gate does not permit learning.

The recurrence threshold is at least two distinct active vacancies. One
vacancy is insufficient. Candidate support is not a gap, and an evidence score
is evidence coverage, never hiring probability. Provider choice is
user-selected and is never inferred from lexical display order. Professional
experience cannot be replaced by learning, a lab, a course, or a certificate.
The route produces a private draft and no external action: it never applies,
edits a profile, sends a message, enrolls, purchases, or schedules.

## Private learning proof sprint routing

When the validated v3 learning decision contains exactly one
`decision_code=build_bounded_proof` row, the root may hand the decision and one
validated `candidate-fact-matrix-v1` to
`build_validated_learning_proof_sprint_v1`. This is the only sprint input: do
not accept caller-authored plan/day/reuse rows, a second vacancy selector, or
an unbound project description. The builder derives the vacancy IDs,
requirement IDs, and usable candidate fact IDs from those frozen sources and
returns one opaque `learning-proof-sprint-v1` snapshot. A missing, conflicting,
forbidden, unsupported, stale, or locale-mismatched source yields no sprint.

Pass that same opaque snapshot to the JSON writer and private HTML renderer.
Each consumer revalidates the complete source binding before serializing bytes
or reading renderer assets. The artifact contains exactly one plan, five
ordered checkpoints, and three reuse maps for `linkedin`, `application_packet`,
and `interview`. The handoffs are manual re-entry cues only; they do not publish
or upload a project, edit LinkedIn, create an application, send a message,
schedule a calendar item, enroll, purchase, or start interview preparation.
Client-visible delivery stays identity-free and ends with the localized
no-external-action boundary.

## Recruiter-conversion observation routing

An explicit conversion receipt is a candidate-supplied observation only, not a candidate identity claim, aggregate, causal explanation, score, fit, or outcome proof. Apply this exact mapping: `contact_received` and `reply_received` → `clarify_context_before_reply`; `referral_received` → `prepare_fact_checked_summary`; `screen_requested` and `interview_requested` → `route_to_prepare-role-interviews`; `stop_decision` → `record_stop_decision`. The mapped value is a manual next step only. It must not auto-start a module, create a module packet, send, schedule, or create a calendar item. Keep normal CSV/outcome measurement and ordinary recruiter-reply and LinkedIn routes unchanged when the receipt is absent.

## Recruiter follow-through checkpoint routing

An explicit `private-recruiter-followthrough-checkpoint-v1` is accepted only with its separately supplied, validated conversion receipt. Treat the pair as candidate-supplied, identity-free, non-aggregated observations. Replay of the same receipt/checkpoint pair is idempotent: do not append a CSV row, duplicate a route, create a packet, reuse an answer, or claim a new outcome. A `completed` checkpoint sourced from `screen_requested` or `interview_requested` may expose one manual cue to re-enter `prepare-role-interviews`; it never starts that module, transfers execution context, or bypasses its vacancy/fact intake. `declined` blocks preparation, and any `stop_decision` source blocks preparation regardless of state; route only to recording the stop. `accepted` and `deferred` remain checkpoints with no preparation authorization. Keep the ordinary CSV route and ordinary recruiter-reply route unchanged when the explicit checkpoint/receipt pair is absent.

## Private recruiter-practice routing

Before every other route, check for an explicit private recruiter-practice request. It takes precedence over recruiter-reply triage, every LinkedIn branch, and debug, eval, detail, raw, or internal-row requests. When it includes an identity-free vacancy summary and at least one supplied candidate fact, select `prepare-role-interviews` and create the separate private recruiter practice session. This is a private artifact branch for one recruiter-screen question, not a normal local LinkedIn artifact and not a client-report fallback.

If either required input is missing, including when both inputs are missing, use `needs_intake`, keep `authorization_required: false`, and ask exactly one concise question requesting only the missing identity-free vacancy summary or candidate fact. Do not ask a second question or infer the missing input from a profile, recruiter message, or prior case. Do not expose internal identifiers, router rows, module-execution packets, or raw vacancy or candidate-fact text in this intake response.

For a ready private session, the response is limited to the renderer's human summary once, one verified absolute local artifact link, and the statement `No external action is performed.` Keep it one-question/one-answer: score and feedback stay `unknown` before an observed answer, and later feedback uses only that answer and its rubric. Treat the observed answer as ephemeral and no-save-by-default. Do not expose internal identifiers, router rows, module-execution packets, or raw vacancy or candidate-fact text. When an explicit private recruiter-practice request is absent, retain the existing recruiter-reply triage and LinkedIn delivery behavior, including debug, eval, and detail_requested legacy output.

## Private recruiter-reply triage routing

After checking private recruiter-practice and before ordinary recruiter-reply routing, check for an explicit private recruiter-reply triage request. This narrow private branch takes precedence over ordinary `recruiter_reply_triage` (**private triage precedence**), but it does not change normal dossier or debug, eval, and detail_requested behavior when the request is not explicit.

Require an identity-free recruiter-reply summary and one supplied candidate fact. If either is missing, including when both are missing, use `needs_intake`, keep `authorization_required: false`, and ask exactly one concise intake question requesting only the missing identity-free recruiter-reply summary or supplied candidate fact. Do not infer either input from a raw reply, profile, recruiter message, or prior case. Do not retain or display a raw reply, identity, contact detail, internal identifier, router row, draft reply, action, proposed time, or calendar detail.

When both inputs are supplied, create only the closed `private-recruiter-reply-triage-v1` decision card, validate it with `validate_private_recruiter_reply_triage.py`, and render it with `render_private_recruiter_reply_triage.py`. Its private delivery is limited to the renderer's human summary once, one verified absolute local artifact link, and `No external action is performed.` The card may state a private handoff only when its closed contract permits it; it does not send, reply, accept, schedule, or create a calendar item. Do not expose internal identifiers, raw reply content, router rows, module-execution packets, or a normal dossier/client-report fallback in this branch.

For `ready_for_private_prep`, the closed handoff is only a manual re-entry cue for `prepare-role-interviews`, scoped to one recruiter-screen question and an identity-free summary plus verified fact. It is **manual input only**: it does not auto-start, transfer execution context, create a `module_execution_packet`, or emit router rows. Its exact boundary is `candidate_answer_state=unanswered` and `score_state=unknown` until the candidate supplies an answer in a later explicit preparation request. Clarify-first and stop cards omit the handoff. Private triage precedence applies before all ordinary recruiter and LinkedIn routes; normal recruiter-reply behavior remains unchanged, including legacy debug/eval/detail behavior.

## Private first-interview conversion board routing

After an explicit private recruiter-reply triage or conversion observation, and
before manual `prepare-role-interviews`, check for an explicit request for
`private-first-interview-conversion-board-v2`. This new branch has precedence
over the frozen legacy compatibility surface. It is opt-in and does not replace
ordinary recruiter triage, recruiter practice, or interview preparation when
the request is absent.

| Úsalo cuando | Necesitas | Recibes | Siguiente paso |
| --- | --- | --- | --- |
| Ya existe una observación privada de triage o conversión y quieres decidir cómo preparar la primera entrevista. | La referencia privada validada que originó esa observación; pide sólo una confirmación breve y sin identidad si falta el contexto. | Un tablero local en borrador con centro de decisión, límite de procedencia, escalera de decisión, un punto de práctica y secuencia de revisión. | Revisa la rama aplicable y, sólo en una solicitud posterior explícita, responde la pregunta de práctica en privado. |

Never ask the client to paste raw JSON, source rows, provenance values, or a
final board. The opaque validated source bundle is an internal boundary, not a
client intake format.

Require one opaque, validated private source bundle. The v2 builder derives a
sanitized decision, sequence, proof cards, risk checks, rehearsal, seven-day
plan, decision ladder, and daily reviews; callers cannot supply raw source
rows, final board rows, or provenance metadata. The only provenance states are
`synthetic_fixture` and `composition_only`; composition-only is a migration
boundary and does not assert upstream provenance. Missing, crossed, stale,
mutated, unsafe, or incomplete inputs fail closed without a fallback artifact.

The output is a private offline JSON/HTML draft for manual review only. The
localized decision cockpit appears first, followed by the provenance boundary
and the decision ladder. The single practice gate then exposes only the exact
validated rehearsal question, its response structure, and `score=unknown`
before the review sequence. It asks the candidate to respond only in a later
explicit request; it never sends, shares, or publishes an answer. Visible
state and branch labels are localized wording rather than raw artifact enums,
so they remain client-facing guidance instead of executable states. It
keeps `draft_only=true`, `external_actions_authorized=false`,
`no_message_action=true`, and `no_calendar_action=true`. It must not send,
reply, connect, apply, publish, upload, schedule, or auto-start
`prepare-role-interviews`. The only next step is a separately authorized
manual review; a `stop` decision exposes the boundary and suppresses detailed
proof, rehearsal, week, and tracking surfaces.

The `private-first-interview-conversion-board-v1` route remains frozen legacy compatibility only. Do not select v1 for new requests; use v2 above. Existing
v1 artifacts and historical checks remain supported without modification.

### Private first-interview practice handoff

Only a `ready` v2 board may use
`private-first-interview-practice-handoff-v1`. Pass the exact opaque
`ValidatedPrivateFirstInterviewConversionBoardV2`; do not accept a rendered
artifact, raw source rows, or caller-supplied provenance. Revalidate the board
before projection and create exactly one `recruiter-practice-session-v2` in
`awaiting_answer` with its score still `unknown`, `observed_answer=null`, and
`local_save_mode=disabled`. The new handoff source is internal proof metadata;
never render its snapshot, digest, or IDs. `clarify`, `pause`, and `stop` fail
closed without a session or response invitation. A later explicit private
request may supply one ephemeral answer to the existing categorical-feedback
flow; it never creates a numeric readiness score, predicts an interview, or
authorizes external action.

For that later answer, use `private-first-interview-practice-feedback-v1` only
with the exact opaque handoff, its matching snapshot, and one bounded answer.
The proof-bound consumer revalidates the session before rendering, emits one
`feedback_available` result with `score=unknown`, and keeps the answer
ephemeral. Unsafe, stale, crossed, or repeated input fails with a generic
diagnostic. Render the result through the proof-bound practice entry point;
passing a mutable session mapping to the generic renderer is not a valid
handoff. A single explicit revision may create `attempt=2,
final_attempt=true`; feedback from that handoff closes the practice cycle and
must not invite a third attempt. Ready boards and awaiting sessions may include
only a static re-entry capsule describing the bounded answer shape; blocked and
terminal states omit it. No external action is performed.

## Multi-module routing

Outside the normal local LinkedIn artifact branch, use a multi-module ordered plan when one self-service or coach mode request contains several safe workstreams, such as LinkedIn audit plus CV rewrite plus imminent interview preparation. The router contract still gets exactly one `selected_module`: choose the first module that should run safely after evidence and authorization gates. Then add an `ordered plan` with one line per later module. In the artifact branch, keep later-module planning internal and end the client chat after the verified link.

Ordered plan rules:

- Start with evidence repair or `optimize-professional-profile` when visible profile facts conflict with CV facts.
- Use `research-professional-market` before `explore-career-options` when current demand, compensation, geography, or role requirements are needed.
- Use `optimize-career-assets` before `prepare-role-interviews` when the vacancy-specific fact matrix is missing.
- Use `recommend-career-learning` only after repeated target evidence shows a gap and cheaper proof alternatives were considered.
- Use `track-career-outcomes` only after dated application, response, interview, or offer records are available for one isolated candidate.
- Keep coach mode candidates separated; never put two candidates in the same ordered plan item.

## Coach case brief

Outside the normal local LinkedIn artifact branch, add `coach_case_brief` for multi-module work as the bridge from routing to execution. The brief is not a motivational summary; it is the case manager's decision record for the next cycle. Use these fields exactly: `candidate_id`, `case_goal`, `coach_verdict`, `evidence_strength`, `primary_bottleneck`, `module_sequence`, `handoff_ready`, `first_interview_strategy`, `weekly_commitment`, `success_signal`, `stop_condition`, `privacy_boundary`, and `causality_boundary=descriptive_only_no_guaranteed_outcome`.

Set `handoff_ready=false` when evidence conflicts, target criteria are missing, assets are not vacancy-specific, or external action authorization is missing. For a first-interview goal, the safe sequence is usually `optimize-professional-profile > optimize-career-assets > research-professional-market > prepare-role-interviews > track-career-outcomes`: fix public positioning and proof first, prepare one targeted application packet, research the vacancy/market evidence, practice the first conversation, then measure outcomes. Do not include `recommend-career-learning` unless repeated role evidence shows a skill gap and a lower-effort proof asset would not close the gap.

The brief must preserve candidate isolation, avoid benchmarking without consent, and never promise interviews, offers, faster hiring, compensation increases, or causal lift from any intervention.

## Coach executive review

Outside the normal local LinkedIn artifact branch, add `coach_executive_review` after `coach_case_brief` for multi-module work. This is the one-screen executive decision the candidate can act on this week. Use these fields exactly: `candidate_id`, `diagnosis`, `decision`, `decision_rationale`, `priority_order`, `tradeoffs`, `risk_register`, `seven_day_plan`, `defer_until`, `first_interview_path`, `measurement_plan`, `leading_indicators`, `outcome_signals`, `privacy_boundary`, `authorization_gate`, and `causality_boundary=descriptive_only_no_guaranteed_outcome`.

The review should diagnose the blocking constraint in one phrase, choose one next-cycle decision, explain why that decision beats the obvious alternative, name the priority order, name the tradeoffs, list operational risks with mitigations, and state what to defer until evidence or authorization gates are satisfied. Candidate-facing fields must read like coach notes a person can act on, not snake_case compliance tokens. The `seven_day_plan` must use day-labelled actions, beginning with evidence repair when claims conflict. The `first_interview_path` should connect profile positioning, application packet, recruiter bridge, and stage-specific practice. The `measurement_plan` should separate controllable `leading_indicators` from observed `outcome_signals`; neither may be framed as proof that the intervention caused outcomes. Keep external actions blocked until exact action-and-target authorization.

## Weekly operating plan

Outside the normal local LinkedIn artifact branch, add `coach_weekly_operating_plan` after `coach_executive_review` for multi-module work, followed by exactly five `coach_weekly_workstream` rows. This is the operating board for the next seven days. The plan row uses `coach_weekly_operating_plan=multi_module_weekly_execution_board` and fields `candidate_id`, `weekly_goal`, `source_review`, `workstream_count=5`, `sequence_model=evidence_repair_to_assets_to_market_to_interview_to_measurement`, `primary_constraint`, `week_exit_criteria`, `blocked_external_actions`, `measurement_boundary=leading_indicators_are_observations_not_causal_proof`, `privacy_boundary=single_candidate_only_no_benchmark_without_consent`, `authorization_gate=exact_action_and_target_required_before_external_action`, `draft_only=true`, and `no_external_action=true`.

Workstream rows use `coach_weekly_workstream=weekly_execution_lane` and cover exactly `linkedin_positioning`, `application_packet`, `market_targeting`, `interview_prep`, and `outcome_tracking`. Each row needs `candidate_id`, `workstream`, `module`, `objective`, `required_evidence`, `deliverable`, `done_when`, `risk_if_skipped`, `metric_to_log`, `owner=candidate|candidate_with_coach_review`, `day_range`, `authorization_need`, `next_safe_action`, `draft_only=true`, and `no_external_action=true`. Keep every workstream private/draft-only until exact action-and-target authorization. Do not promise first interviews, recruiter replies, offers, compensation, faster hiring, ranking, or causal lift.

Choose exactly one `case_state` in this order:

For a normal local LinkedIn diagnostic with at least one inspectable or supplied LinkedIn section, a conflicting or unsupported claim remains `unknown` and blocked for public copy but does not block the entire honest diagnostic. The case may remain `ready` for a private partial dossier when the unresolved issue can be isolated: mark affected copy `requires_confirmation` or `omit`, keep every other claim within its evidence boundary, and put at most the first decision-changing question in chat. Use `blocked_on_evidence` only when the unresolved issue blocks the entire honest diagnostic. If there is no other inspectable or supplied evidence, do not create a dossier; ask exactly one useful intake question.

Outside that narrow partial-dossier exception:

1. Use `blocked_on_evidence` for a source conflict or unsupported material claim. This wins over every later state.
2. Otherwise use `needs_intake` when a required goal, location, constraint, or target detail is missing.
3. Otherwise use `awaiting_authorization` only when evidence and intake are sufficient and a requested external action has an exact action and target ready for authorization.
4. Otherwise use `ready`.

Route a source conflict to `optimize-professional-profile`; ask for confirmation and do not draft the disputed section as ready public copy. The private partial dossier exception above may still diagnose supported sections and hold the disputed copy. Set `authorization_required: true` independently whenever the request includes an external action, even if an unresolved conflict or intake gap wins the `case_state`. Drafting and analysis alone require `false`.

## Recruiter reply and send-now routing

When neither an explicit private recruiter-practice request nor an explicit private recruiter-reply triage request is present, inbound recruiter replies, recruiter screen invitations, proposed times, and user requests to send, reply, confirm, accept, schedule, book, or create a calendar item route to `optimize-professional-profile` first so the response includes `recruiter_reply_triage`. Use `awaiting_authorization` only after the exact recipient, finalized draft, action, and target are known; otherwise keep the safe next step as triage or clarification. In all of these cases set `authorization_required: true` because the user is asking for an external action. For a proposed time, keep `proposed_time_state=do_not_accept_or_propose_time_without_exact_authorization`, `no_calendar_action=true`, and `draft_only=true`; do not report that a message was sent, a screen was scheduled, a time was accepted, or a calendar event was created. A prior approval or general send instruction is insufficient unless immediately before execution it names the exact action, exact target, and exact final content or asset identity when content or assets apply.

## Private vacancy application packet routing

The explicit private recruiter-practice, explicit private recruiter-reply triage, and ordinary recruiter-reply/send-now routes remain higher-precedence. Only otherwise consider the packet branch. Require one complete composite source group with `eligibility_group` containing `eligibility`, `research`, `executive_dossier`, `market_dossier`, `gap_response`, `gap_assessment`, and `provider_research`, plus `candidate_fact_group` containing `candidate_fact_matrix` and `source_group`. This composite is the only packet input; require no caller-supplied packet JSON.

Eligibility remains the sole target-vacancy and trigger authority. Route the complete composite to `optimize-career-assets` and call `build_validated_private_vacancy_application_packet_v1` exactly once. That boundary captures the composite once, recomputes eligibility, requires `recommended_next_action` to equal `prepare_private_vacancy_packet`, builds the deterministic packet, fully revalidates it against the same frozen composite, and returns one opaque snapshot; there is no second vacancy selector. If any composite member is absent, request only the missing identity-free private evidence in one bounded question. Produce no packet, do not fall through to an untyped packet or another module, and perform no external action.

Pass that same opaque snapshot to `write_private_vacancy_application_packet_v1` and `write_private_vacancy_application_packet_html_v1`. Each consumer fully recomputes the carried artifact from the carried frozen composite before serializing bytes, reading renderer assets, resolving a destination, or publishing output. Execution proof requires the resulting private packet JSON, rendered HTML, and exact receipts from that same opaque snapshot and captured composite source group. Crossed, incomplete, stale, forged, or mismatched values are failure, not proof. Follow the exact in-process workflow and receipt checks in `optimize-career-assets/references/asset-workflow.md`; never expose receipt JSON in client chat.

The client delivery contains exactly:

```text
private_packet_summary
readiness_decision
verified_local_artifact
approval_boundary
```

Use a localized bounded summary; the validated localized readiness headline and rationale without raw enums; one verified absolute local Markdown link to the private HTML; and the private-draft/manual-review boundary with external authorization false. Include none of `candidate_id`, router contract, `module_execution_packet`, internal fact IDs, source IDs, snapshot IDs, source bindings, raw source prose, receipt JSON, or hidden authorization. The last visible line is `No se realiza ninguna acción externa.` for Spanish or `No external action is performed.` for English. No upload, export, application, message, publication, scheduling, purchase, enrollment, or other external action occurs.

## Ready module execution

If the chosen state is `ready`, execute the selected module rather than returning a routing-only answer. For the explicit private recruiter-practice or private recruiter-reply triage branches, the validated private artifact is the execution proof; do not emit a router contract, `module_execution_packet`, or internal identifiers. The validated private vacancy-packet branch is separate and follows the same execution-proof and no-router rule. Otherwise, outside the normal local LinkedIn artifact branch, add one `module_execution_packet` row with `candidate_id`, `selected_module`, `execution_depth`, `delivered_sections`, `evidence_ids`, `candidate_next_practice`, `authorization_gate`, and `causality_boundary=descriptive_only_no_guaranteed_outcome`. In the normal LinkedIn artifact branch, the validated dossier and renderer receipt are the execution proof and stay out of client-visible contract rows.

For a `ready prepare-role-interviews` route, include the useful core sections from the interview skill in the same response: `competency_map`, `likely_questions`, `truthful_story_bank`, `practice_answer_coaching`, `role_practice`, `mock_interview`, `scorecard`, `interviewer_questions`, `follow_up_draft`, `first_interview_conversion_plan`, `recruiter_screen_brief`, `recruiter_bridge_script`, `vacancy_candidate_gap_map`, `objection_response_map`, `question_bank`, and `follow_up_lifecycle`. Use stable `V-###`, `F-###`, and `Q-###` IDs. If those sections cannot be delivered from the available vacancy and candidate facts, mark the case `needs_intake` or `blocked_on_evidence` instead of `ready`.
