# Reproducible release validation

The release validation contract is macOS arm64 with CPython 3.11.15. It uses an
ignored, repository-local environment and the sole locked dependency in
`requirements/release-validation.txt`. The bootstrap does not upgrade pip or
install unrelated packages; its install contract is
`--require-hashes --only-binary=:all: --no-deps`.

From the repository root, create or refresh the environment:

```bash
bash scripts/bootstrap_release_validation.sh
```

The executable release runner verifies these SHA-256 digests before either
validator can execute:

- `quick_validate.py`: `6cc9dc3199c935916cf6f73fcbbbb0e3bb1b58c8f5109fefa499978908164f51`
- `validate_plugin.py`: `ebda00d55d7518b127f675f062fb5c6e7a1ffdc0a99df1a55ac594400d7d3228`

With `CODEX_SYSTEM_SKILLS_ROOT` set to the system skills directory, run:

```bash
bash scripts/run_release_validation.sh
```

Before changing the plugin manifest, run the repository integration gates from
the repository root:

```bash
python3 -B -m unittest tests.test_plugin_structure tests.test_repository_privacy -v
python3 -B plugins/professional-growth-coach/tests/run_static_checks.py
python3 -B scripts/check_repository_privacy.py
```

The static gate treats the executive dossier schema, validator, renderer,
source registry, HTML/CSS assets, and skill reference as one installed-relative
package. It rejects direct, broken, and intermediate symlinks; parses the schema
and registry; requires one bounded inline style and script; and executes the
package-local validator and renderer from an unrelated directory against a
valid fixture plus an invalid mutation. It also rejects network-capable asset
tokens, verifies generated output paths stay ignored, and revalidates the
pressure-summary source hashes. The privacy gate scans committed evaluation
evidence and an explicit dossier schema/validator/renderer/assets/test inventory.
Any generated dossier artifact forced into the Git index is read from its
immutable stage-zero blob by object ID, with regular-file, size, and UTF-8 checks;
ordinary ignored, unstaged artifacts remain local. Findings expose only path,
rule ID, and count.

When the same runner is executed from an extracted marketplace cache, it enters
package-only mode. It validates the bundled schemas, scripts, assets, skills,
and package-local tests with the plugin root as the path anchor, then reports
`repository conformance not bundled`. Root `tests/evals` fixtures, repository
privacy/integration gates, and the official release validator remain
repository-only; a cache run must not silently turn missing fixtures into a
passing full-suite claim. Any test selector not explicitly classified as
repository-only must still fail on an import or fixture error.

The dossier's deterministic content boundary is deliberately explicit. Every
unsupported technology from the request must be recorded in
`requested_technology_terms`, bound to the exact claim IDs and evidence paraphrases;
the validator rejects an unbound or unsupported requested technology in ready copy.
This deterministic boundary extracts arbitrary explicit expertise/specialist promotions
from ready copy after Unicode-format normalization and requires an exact ledger term plus
a bound allowed claim. Because raw requests are not retained, requested technologies that
are both omitted from the ledger and never promoted as expertise cannot be reconstructed
later; the skill contract therefore requires every explicitly requested technology to be
populated before validation.
Identity labels, self-introductions, raw-copy indicators, contacts, profile URLs,
and structured identity fields are rejected. Contextual person/company
disclosures (for example, a named person paired with `described` or a company
paired with `works at`) are also rejected before triage rendering. A standalone
proper name still cannot be distinguished reliably from a product, role, or
organization without the original private profile or a per-candidate denylist,
either of which would violate this identity-free package boundary. Therefore
upstream evidence must still be paraphrased and redacted before construction.
Because the triage locale contract is limited to `en`/`es`, prose letters from
unsupported writing systems are rejected as well; future multilingual support
must replace that guard with an explicit locale-aware redaction policy. The
validator's fixed privacy booleans are not proof about undeclared external input.

Only after those gates and independent review pass may the source manifest move
to the approved release version and describe evidence-backed private HTML
LinkedIn diagnostics. Re-run the integration gates, the full test suite, and the
checksum-gated official validators on that exact tree. The marketplace file must
remain byte-identical, and this release-validation workflow does not install the
plugin or modify its cache or Codex configuration.

Any interpreter, wheel, requirements hash, or official-validator digest change
requires an explicit lock and evidence update. Do not satisfy this release gate
from a global Python installation or a mutable developer dependency cache.

## Vacancy-first v3 release evidence

Before any manifest cachebuster, validate the all-or-none renderer CLI group:
`--gap-response`, `--gap-assessment`, and `--next-action-eligibility`. The
source gates must cover the four closed schemas, shared bounded snapshot,
builders/validators, v3 projector, isolated CSS, canonical fixtures, routing,
privacy inventory, and historical v1/v2 bytes.

Installation is a later, separately authorized release step. Resolve the cache
from exactly one installed and enabled plugin-list row whose name, marketplace,
and version match. Use only `cache family / plugin / exact enabled reported version`;
never use an alias, glob, `latest`, lexicographic selection, cache
deletion, or manual configuration mutation.

Compare the immutable Git archive and installed cache using identical non-zero
sorted POSIX relative paths and per-file SHA-256 digests. The aggregate digest
records each path as UTF-8, then NUL, then its lowercase file digest, then LF.
Reject symlinks, unreadable/non-regular files, personal metadata, `.pyc`,
`.pyo`, and `__pycache__` on both sides. Diagnostics expose only relative paths
or fixed generic failures.

Before semantic execution, the installed smoke harness captures the validated
archive and installed cache into separate private snapshots, verifies snapshot
parity, and then uses only the cache snapshot for imports, schemas, fixtures,
static checks, renderer/CLI subprocesses, and the semantic matrix. Snapshot
directories are private and copied files are not hardlinked. This protects the
release evidence against ordinary concurrent cache updates; it does not claim
isolation from an active malicious process running under the same UID. Every
imported semantic module must resolve below that snapshot root; mutable
checkout imports fail closed. During module loading and the complete semantic
run, controller import paths are limited to the snapshot scripts plus the
interpreter's resolved standard-library and locked site-package roots;
untrusted preloaded modules and namespace search locations fail closed, and the
prior controller import state is restored. Static and renderer children use
isolated interpreter mode with a minimal environment that does not carry
`PYTHONPATH`. Installed static checks must state `repository conformance not
bundled` rather than turning absent repository fixtures into a full-suite pass.
The final attestation records archive/cache counts and aggregate digests,
accepted and rejected smokes, no-echo/atomicity, repository-only scope,
external actions not executed, and `visual QA not run` unless empirical browser
evidence exists.
