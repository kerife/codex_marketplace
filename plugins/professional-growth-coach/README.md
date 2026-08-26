# Professional Growth Coach

Professional Growth Coach is a local Codex plugin for evidence-based professional-growth coaching. It helps employees evaluate market options, strengthen their current role, and prepare reversible next steps while preserving current employment by default. It routes one candidate case at a time, keeps candidate records isolated, and sends work to focused modules:

- `optimize-professional-profile`
- `explore-career-options`
- `research-professional-market`
- `optimize-career-assets`
- `prepare-role-interviews`
- `recommend-career-learning`
- `track-career-outcomes`

Use the root `professional-growth-coach` skill when the request spans multiple areas or needs intake, routing, consent, or action-boundary checks.

## Employment continuity

This plugin evaluates the market; it does not encourage resignation. `preserve_current_employment_by_default` and `no_resignation_recommendation=true` apply to every module. Staying and growing in the current role, developing skills, exploring options, or `do_nothing_now` are valid outcomes. Path decisions are research/positioning decisions only, never instructions to resign, quit, leave an employer, reduce hours, or create a voluntary gap.

## Privacy

Keep one `candidate_id` per case. Coach mode must split combined requests into separately labelled candidate sections before analysis. Cross-candidate benchmarking stays off unless explicit consent is recorded, and consent never authorizes external actions.

The plugin can prepare drafts, plans, rubrics, and analyses. It must ask again before editing LinkedIn, publishing content, sending messages, applying to jobs, uploading files, or sharing candidate work with a third party.

By default, a normal local LinkedIn dossier also performs a read-only bounded search for up to five current SRE, Platform Engineering, or DevOps vacancies in Mexico or a stated remote arrangement. It searches five distinct recognized employers first, prioritizes official employer or employer-operated ATS pages, and uses LinkedIn Jobs only as a labelled backup. Every included posting is opened and confirmed active with an access date. One through four verified postings remain a documented limited sample; zero becomes unavailable; the plugin never pads with expired, duplicate, inaccessible, or incompatible postings and never infers work authorization or remote eligibility.

The private dossier shows reproducible evidence alignment and `k/N` recurrence over the actual included sample. This does not change the LinkedIn profile score, predict hiring fit, or authorize applying, messaging, connecting, following, publishing, enrolling, or purchasing. Course and certification recommendations remain unevaluated until the separate learning step.

The HTML renderer accepts exactly one coherent composition generation. Market
v1 keeps its required supplied alignment and may add learning v1. Market v2
recomputes alignment from the validated vacancy research and executive dossier;
it can render without learning or provider research, while learning v2 requires
its independently validated provider-research source. Mixed versions, crossed
sources, and incomplete groups fail before HTML is assembled or written. A
learning v2 card projects one compact row per validated signal using only the
public term label, localized support, public vacancy ordinals, recurrence,
source-recomputed basis, and localized decision. It does not render source
links, snapshots, source prose, raw enums, or internal provenance identifiers.

The vacancy-first v3 composition adds the independently persisted gap response,
source-resolved assessment, recomputed next-action eligibility, and zero-or-one
learning decision as one all-or-none group. The user first selects one public
vacancy-and-signal pair. The gate then requires recurrence in at least two
distinct active vacancies plus an explicit candidate gap relation, and projects
exactly one private weekly action. Candidate support is not a gap; market scores
are evidence coverage, never hiring probability; provider choice is
user-selected; and professional experience cannot be replaced by learning.
When the gate is not eligible, prepare private vacancy evidence or confirm the
missing relation first. No external action is performed.

The v3 renderer CLI requires `--gap-response`, `--gap-assessment`, and
`--next-action-eligibility` together with the coherent v3 market/research/
learning group. Partial or crossed groups fail before output. These flags read
local identity-free artifacts only; they do not apply, edit a profile, message,
purchase, enroll, schedule, or publish.

### Private learning proof sprint v1

When a validated v3 decision selects `build_bounded_proof`, the learning module
can derive a private `learning-proof-sprint-v1` from exactly one decision and one
validated `candidate-fact-matrix-v1`. The builder derives vacancy, requirement,
and usable fact IDs; callers cannot provide sprint rows or choose a second target.
It emits exactly one plan, five ordered checkpoints, and three private reuse maps
for LinkedIn, the application packet, and interview preparation. The JSON and HTML
writers accept only the opaque validator snapshot, preserve mode `600`, and keep
`external_action_authorized=false`.

The offline renderer presents a semantic five-day timeline and three handoff cards
in Spanish or English. It has responsive, print, dark-mode, forced-colors, and
reduced-motion hooks, but no buttons, external links, forms, or automated handoff.
The artifact is a review plan, not a published project, credential, interview
prediction, application, message, upload, enrollment, purchase, or calendar action.

### Private vacancy application packet v1

When recomputed eligibility selects `prepare_private_vacancy_packet`, the root
routes the complete private composite to `optimize-career-assets`. Eligibility
remains the only vacancy selector. Missing or crossed inputs fail without an
untyped fallback. The versioned entry points are:

- `schemas/candidate-fact-matrix-v1.schema.json`
- `schemas/private-vacancy-application-packet-v1.schema.json`
- `scripts/build_private_vacancy_application_packet_v1.py`
- `scripts/validate_private_vacancy_application_packet_v1.py`
- `scripts/write_private_vacancy_application_packet_v1.py`
- `scripts/render_private_vacancy_application_packet_v1.py`

The validator's `build_validated_private_vacancy_application_packet_v1`
captures the complete composite once, builds and fully revalidates the packet,
and returns one opaque snapshot. The JSON and HTML writers recompute that
carried complete binding before output and emit closed eight-field receipts.
No caller-supplied packet JSON is required by the root route. The client receives only a private summary, readiness decision,
verified local artifact link, and approval boundary. The draft does not
authorize an application, upload, export, message, publication, or other
external action. No external action is performed.

### Private first-interview conversion board v2

New private first-interview requests use
`private-first-interview-conversion-board-v2`. The builder accepts only an
opaque validated source bundle and persists a sanitized projection; callers do
not provide a raw source group or artifact. The `board-trust-strip` distinguishes
synthetic fixture data from the `composition-only` v1 adapter, states that
original text is not stored, and requires manual review. `composition-only`
does not claim external provenance. The board is local, draft-only, identity-free,
and never performs an external action. It writes only a mode-600 private draft
after exact proof revalidation.

| Úsalo cuando | Necesitas | Recibes | Siguiente paso |
| --- | --- | --- | --- |
| Ya existe una observación privada de triage o conversión y quieres preparar la primera entrevista. | La referencia privada validada de esa observación; si falta contexto, una confirmación breve y sin identidad. | Un tablero privado con centro de decisión, límite de procedencia, escalera de decisión, un punto de práctica y secuencia de revisión. | Revisa la rama segura y, sólo en una solicitud posterior explícita, responde la pregunta de práctica en privado. |

No se pide JSON crudo, filas fuente ni valores de procedencia al cliente: la
fuente validada opaca es un límite interno. El centro de decisión localizado va
antes del límite de procedencia; la escalera va inmediatamente después de ese
límite. Un único punto de práctica va después de la escalera y antes de la
secuencia: muestra la pregunta y la estructura de respuesta ya validadas,
mantiene la puntuación como `unknown`, y sólo permite responder en una
solicitud posterior explícita. No envíes, compartas ni publiques esa respuesta.
Las etiquetas visibles traducen los estados y ramas; los enums del artefacto no
son instrucciones para el cliente.

`private-first-interview-conversion-board-v1` is frozen legacy compatibility
only. New requests must use v2.

### Private first-interview conversion board v1 (frozen legacy compatibility)

After an explicit recruiter triage or conversion observation, and before
manual `prepare-role-interviews`, the root can create a private
`private-first-interview-conversion-board-v1`. It accepts one validated,
same-group recruiter-outreach and seven-day plan composition, recomputes the
decision, and produces a source-bound JSON/HTML review board with proof
signals, risk checks, rehearsal, a seven-day sequence, a decision ladder, and
daily review templates. A `stop` state is fail-closed and suppresses detailed
preparation surfaces.

The board is offline, identity-free, draft-only, and requires manual review.
It never sends a message, schedules a calendar item, applies, edits a profile,
publishes, uploads, or performs another external action. Its private writer
creates a mode-600 artifact only after validator-issued proof is revalidated.

### Installed test scope

An extracted marketplace cache contains the package-local validators, renderers,
schemas, and their package tests. Repository-only conformance tests remain in
the source checkout because they depend on root `tests/evals` fixtures and
repository integration tools; their absence from an installed cache is not a
runtime or package failure. The installed static runner reports package checks
separately and never claims repository conformance from an extracted cache.

The installed smoke receipt keeps the historical vacancy-first matrix at
exactly 39 accepted and 9 rejected cases. The private packet increment is a
separate matrix with exactly 6 accepted and 12 rejected case IDs; it is never
reported as a combined 45/21 result. Packet artifacts and HTML are generated
only by installed builders and the installed renderer after archive/cache
parity is captured, with `verified_private_snapshot_only` as the import
boundary. Rejections remain generic, do not echo private input, and do not
leave partial output.

## Installation

This source tree is repo-local at `plugins/professional-growth-coach`. Source edits do not update the installed plugin cache. A separate explicitly authorized installation is required to publish a source increment into the local marketplace cache; existing chats may continue using their loaded version, so verify the new installation from a fresh chat. Use the repo-local marketplace workflow only after the exact target and command are approved.

## Starter prompts

- “Analiza mi perfil de LinkedIn y entrégame una conclusión breve más un dossier HTML privado y completo. No inventes datos ni realices acciones externas.”
- “Compare professional-growth options for a synthetic SQL/Airflow/dbt background, then tell me what market evidence is missing.”
- “Prepare me for this interview using the supplied vacancy and my candidate fact matrix.”
- “Build a first-interview recruiter screen brief, objection response map, and draft-only outreach funnel from my confirmed evidence; do not send anything.”
- “Build a private first-interview conversion board from my confirmed recruiter triage and seven-day plan; do not perform external actions.”
- “Crea un tablero privado v2 de primera entrevista desde una fuente validada; no realices acciones externas.”
- “Build a private first-interview board v2 from a validated source bundle; do not perform external actions.”

## Self-service example

Use self-service mode when one candidate asks for their own professional-growth plan:

```text
candidate_id: candidate-synthetic-01
mode: self-service
target: Data Platform Specialist
stack: SQL, Airflow, dbt
request: Audit LinkedIn, identify CV gaps, and prepare interview drills for this vacancy.
```

Expected routing: start with `professional-growth-coach`, preserve evidence labels, then produce an ordered plan across professional positioning, assets, market research, and conversation preparation.

## Coach mode example

Use coach mode when helping multiple people:

```text
mode: coach
candidates:
  - candidate_id: candidate-a
    request: LinkedIn audit for SRE roles.
  - candidate_id: candidate-b
    request: Enterprise AE transition learning plan.
```

Expected routing: split the request into isolated candidate sections. Do not reuse facts, outcomes, metrics, or drafts across candidates.
