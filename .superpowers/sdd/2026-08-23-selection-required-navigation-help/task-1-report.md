# Task 1 report — selection-required navigation help

## Status

DONE

## Implementation

- Added localized ES/EN selection-format help only for `selection_required`.
- Added exactly two internal anchors to `#market-vacancy-key-title` and `#market-matrix-title`.
- Added stable ID `weekly-decision-selection-help` and inserted it between evidence and boundary in `aria-describedby`.
- Preserved one primary action, no selected vacancy/signal/recurrence, no external URL or control, unavailable empty output, all other state output, and v1/v2 byte baselines.
- Updated the two minimal Superdesign contract notes requested by UX pre-review; did not modify canvas state. Refreshed only the required post-implementation resume fingerprints and timestamp while preserving draft/version 5 and all other fields.

## TDD evidence

Controller-captured RED before production:

```text
Ran 1 test in 323.081s
FAILED (failures=2)
```

The failures were the missing ES and EN selection-format help.

First implementation run exposed one expected rendering defect in both locales: HTML-to-visible-text normalization inserted a space before the final period because the period was outside the final anchor.

```text
Ran 1 test in 322.089s
FAILED (failures=2)
```

After the minimal punctuation-boundary correction and the security pre-review assertions:

```text
$ python3 -m unittest tests.test_executive_career_dossier_v2.ExecutiveCareerDossierV2RendererTests.test_v3_selection_required_links_one_localized_help_to_market_choices
Ran 1 test in 322.029s
OK
```

## Focused adjacent verification

```text
$ python3 -m unittest \
  tests.test_executive_career_dossier_v2.ExecutiveCareerDossierV2RendererTests.test_v3_every_state_has_exact_es_en_copy_and_one_primary_action \
  tests.test_executive_career_dossier_v2.ExecutiveCareerDossierV2RendererTests.test_v3_public_vacancy_ordinal_title_and_employer_are_visible_and_named \
  tests.test_executive_career_dossier_v2.ExecutiveCareerDossierV2RendererTests.test_v3_unavailable_preserves_one_existing_safe_step_only \
  tests.test_executive_career_dossier_v2.ExecutiveCareerDossierV2RendererTests.test_historical_v1_v2_bytes_and_inline_css_exclude_v3_selectors
Ran 4 tests in 44.251s
OK
```

The historical baseline test also asserts that v1/v2 omit `weekly-decision-selection-help`.

## Diff and artifact verification

```text
$ git diff --check
# exit 0, no output

$ find . -type d -name __pycache__ -o -type f -name '*.pyc' -o -type f -name '*.pyo'
# exit 0, no output

$ python3 -c '<parse resume JSON; assert draft version 5; assert both recorded fingerprints equal current SHA-256>'
resume JSON and fingerprints OK
```

`.superdesign/tmp/` exists only as ignored temporary output and is not included in the commit.

## Files included

- `.gitignore` — controller-authored ignore for temporary Superdesign output.
- `.superdesign/resume.json` — controller-authored draft-v5 resume state with exact post-implementation fingerprints and refreshed timestamp.
- `.superdesign/design-system.md` — minimal internal-link contract parity.
- `.superdesign/init/extractable-components.md` — minimal component contract parity.
- `plugins/professional-growth-coach/scripts/render_executive_career_dossier_v2.py` — bounded production implementation.
- `tests/test_executive_career_dossier_v2.py` — controller-authored RED plus required fragment-target uniqueness and v1/v2 absence assertions.
- `.superpowers/sdd/2026-08-23-selection-required-navigation-help/task-1-report.md` — this evidence report.

## Self-review

- State gate is exact (`selection_required` only).
- Both localized phrases are visible and each fragment link appears once.
- Each link target ID appears exactly once in the full rendered document.
- The help ID appears once and only in the selected state.
- Existing non-selection `aria-describedby` bytes remain unchanged.
- No CSS, schema, builder, validator, external action, or unrelated code changed.
- Resume JSON parses and its renderer/design-system fingerprints equal the current SHA-256 values.

## Concerns

None.
