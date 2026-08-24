---
name: optimize-career-assets
description: Use when drafting or auditing a truthful CV, vacancy-tailored application materials, ATS-oriented improvements, or a portfolio evidence plan.
---

# Optimize Career Assets

Turn supplied candidate facts and a target vacancy into reviewable drafts. Read [asset-workflow.md](references/asset-workflow.md), [ats-and-truthfulness.md](references/ats-and-truthfulness.md), and [candidate-fact-matrix.md](assets/candidate-fact-matrix.md) before drafting. Preserve candidate isolation and minimize personal data.

## Evidence rules

Every material item begins with exactly one canonical prefix: `verified:`, `candidate-reported:`, `inferred:`, or `unknown:`. Optional qualifiers after the colon are allowed, for example `verified: (CV)` or `unknown: (unavailable)`. Never use slash compounds. A candidate fact receives a stable candidate fact ID. Every rewritten claim must map to a candidate fact ID or be labeled recommendation. Never upgrade a candidate-reported fact to verified.

Do not invent experience, skills, Terraform, Argo CD, metrics, scope, seniority, employers, outcomes, certifications, work authorization, or portfolio artifacts. A missing requirement is a genuine skill gap, not a keyword to stuff. Reconcile LinkedIn and CV wording; where they conflict, label `unknown: (conflicting)` and do not choose a version without confirmation.

## Draft and diagnose

Use impact-first bullets: state the supported action, context, and result only where the fact matrix supports it. When a result or metric is absent, retain the action and context or use a confirmation placeholder; do not create a number or invented metrics. Tailor terminology to the supplied vacancy only where it truthfully describes an existing fact. Treat vacancy requirements as candidate-reported only when supplied by the candidate; otherwise mark the vacancy source appropriately.

ATS feedback is an audit, not a score. Separate formatting, terminology, evidence, and genuine skill gap findings. Do not claim compatibility with an opaque ATS or promise an ATS score, ranking, interview, or outcome. Give plain-text export recommendations such as a readable heading hierarchy, conventional section names, selectable text, and a human review after export.

For portfolio ideas, propose only evidence plans whose material the candidate owns or whose rights holder has granted documented permission that explicitly covers public disclosure. Candidate approval alone cannot authorize employer or third-party material. Name the fact ID demonstrated and record the ownership or permission evidence plus a confidentiality review. Secrets and customer data are always forbidden, even with candidate approval or rights-holder permission. Never include credentials, tokens, private keys, or customer data in a portfolio.

Content eligibility does not authorize execution. Even when ownership or documented rights-holder permission makes material eligible, retain the separate action gate and obtain exact action-and-target authorization immediately before any external share, publication, upload, or export.

## Private vacancy application packet v1

Use this versioned branch only when the root router supplies the complete validated composite and recomputes `recommended_next_action=prepare_private_vacancy_packet`. Eligibility remains the sole vacancy and trigger authority; accept no independent selector. Read [candidate-fact-matrix-v1.schema.json](../../schemas/candidate-fact-matrix-v1.schema.json), [private-vacancy-application-packet-v1.schema.json](../../schemas/private-vacancy-application-packet-v1.schema.json), and the exact invocation in [asset-workflow.md](references/asset-workflow.md). Do not hand-author the retired identity-bearing prose packet.

The versioned schema is the packet field contract. Keep every claim source-recomputed and truthful, preserve the no-outcome boundary, and leave the artifact private with manual review required and external action unauthorized. Creating or approving the draft grants neither consent nor authority to apply, send, upload, export, share, or publish. The legacy textual `application_claim_review_matrix` evaluator remains unchanged for ordinary text asset coaching; it is a review gate, not versioned execution proof.

Execution proof is the validated packet JSON, rendered HTML, and exact CLI receipt from the same captured source group. On success, return only the root skill's four-section identity-free artifact delivery. Do not emit the ordinary asset response, candidate or provenance IDs, router fields, a `module_execution_packet`, source bindings, or receipt JSON.

## Required response

Return these exact sections, with labels on material claims:

```text
fact_matrix
ats_gap_map
master_cv_recommendations
vacancy_tailored_draft
application_packet
portfolio_evidence_plan
consistency_report
```

The validated private vacancy-packet branch replaces this ordinary seven-section response with the root artifact delivery.

## Action gate

Drafting, local analysis, and authorized read-only inspection are allowed. Immediately before any CV or LinkedIn edit, application, upload, message, share, publication, or external export, obtain explicit action-and-target authorization. A request for optimization, a draft approval, or earlier general consent does not authorize execution. Do not edit, apply, upload, message, share, publish, or export without exact action-and-target authorization.
