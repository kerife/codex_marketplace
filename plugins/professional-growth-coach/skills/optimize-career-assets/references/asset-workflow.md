# Truthful asset workflow

## Inputs and fact matrix

Collect candidate facts, their source, evidence label, and a stable candidate fact ID before drafting. Keep each fact's scope, date, and confidentiality status. Read the supplied target vacancy as evidence, not proof that the candidate has a requirement. Missing source, scope, metric, or result remains `unknown:`.

## Master CV and tailoring

Create a master CV recommendation from supported facts. For each vacancy-tailored bullet, map the rewritten claim to a candidate fact ID or label it recommendation. Use impact-first writing: supported action, supported context, then supported result. If the result is absent, use no metric or a `[confirm: result]` placeholder. Do not translate adjacent experience into Terraform or Argo CD experience.

Use vacancy terminology only when it truthfully names the candidate's work. A truthful transferable phrasing is preferable to keyword stuffing. A recommendation can say `inferred: recommendation=complete a candidate-owned Terraform lab before claiming Terraform familiarity`; it cannot state that the lab or skill already exists.

## Versioned private vacancy packet

Use [candidate-fact-matrix-v1.schema.json](../../../schemas/candidate-fact-matrix-v1.schema.json) and [private-vacancy-application-packet-v1.schema.json](../../../schemas/private-vacancy-application-packet-v1.schema.json) as the only field contracts. The complete source group contains `eligibility_group` with `eligibility`, `research`, `executive_dossier`, `market_dossier`, `gap_response`, `gap_assessment`, and `provider_research`, plus `candidate_fact_group` with `candidate_fact_matrix` and `source_group`. Capture it once. Eligibility remains the sole target and packet-trigger authority; recompute `prepare_private_vacancy_packet` and accept no second selector.

From the plugin root, render the private local artifact with exactly this invocation shape:

```text
python3 -B scripts/render_private_vacancy_application_packet_v1.py <packet-json> --source-group <complete-source-group-json> --output <private-output.html>
```

The CLI must exit zero after atomically publishing the HTML. The successful receipt contains exactly:

```text
artifact_type
schema_version
locale
readiness_state
vacancy_id
output_path
private_draft
external_action_authorized
```

Require `artifact_type=private_vacancy_application_packet`, packet-matching version/locale/readiness/vacancy values, the resolved output path, `private_draft=true`, and `external_action_authorized=false`. Treat the validated packet JSON, rendered HTML, and CLI receipt as execution proof only when they derive from the same captured composite source group; a mismatch is not execution proof. If a canonical private JSON copy is needed, use `write_private_vacancy_application_packet_v1.py` with the same packet and source-group arguments and require the same receipt shape.

Missing, crossed, stale, invalid, failed, or partial inputs produce no client artifact claim and no fallback packet. The legacy textual `application_claim_review_matrix` remains available only for ordinary text asset evaluation; do not treat it as the versioned schema, receipt, consent, or authorization. Its compatibility vocabulary remains `candidate_id`, `target_vacancy_id`, `matched_evidence`, `role_requirements`, `unsupported_or_missing_claims`, `recruiter_summary`, `message_angle`, `first_interview_prep_handoff`, `tracking_event`, `approval_gate`, `draft_only=true`, `consent=not_granted`, and `causality_boundary=no_outcome_guarantee`; none is a v1 client-delivery field. Root delivery exposes only the four client fields and the localized no-external-action line, never candidate/fact/source/snapshot IDs, bindings, raw source prose, paths other than the verified local artifact link, or receipt JSON.

## Portfolio and export

Portfolio evidence plans name the candidate fact ID, the intended demonstration, and evidence that the candidate owns the material or has documented rights-holder permission explicitly covering public disclosure. Candidate approval alone cannot authorize employer or third-party material. Secrets and customer data are always forbidden, even with candidate approval or rights-holder permission; never include credentials, tokens, private keys, or customer data.

Record content eligibility separately from execution authorization. Ownership or public-disclosure permission does not authorize execution. Immediately before a share, publication, upload, or export, obtain exact action-and-target authorization under the skill's action gate.

Recommend a simple export: conventional headings, readable fonts, selectable text, a single-column layout where practical, and a manual text-extraction check. These are formatting recommendations, not a promise of behavior in an opaque ATS.

## Consistency check

Compare LinkedIn and CV title, employer, dates, scope, skills, metrics, and public portfolio links. Mark agreement with the source labels. Mark unresolved differences as `unknown: (conflicting)` and hold the affected rewrite for confirmation.
