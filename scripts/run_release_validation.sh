#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd -P)"
SYSTEM_SKILLS_ROOT="${CODEX_SYSTEM_SKILLS_ROOT:-${CODEX_HOME:-$HOME/.codex}/skills/.system}"
VALIDATION_PYTHON="${VALIDATION_PYTHON:-$PROJECT_ROOT/.release-validation-venv/bin/python}"
SKILL_VALIDATOR_PATH="${SKILL_VALIDATOR_PATH:-$SYSTEM_SKILLS_ROOT/skill-creator/scripts/quick_validate.py}"
PLUGIN_VALIDATOR_PATH="${PLUGIN_VALIDATOR_PATH:-$SYSTEM_SKILLS_ROOT/plugin-creator/scripts/validate_plugin.py}"
SOURCE_PLUGIN_ROOT="${SOURCE_PLUGIN_ROOT:-$PROJECT_ROOT/plugins/professional-growth-coach}"
LINKEDIN_SKILL_ROOT="${LINKEDIN_SKILL_ROOT:-$SOURCE_PLUGIN_ROOT/skills/optimize-professional-profile}"
EXPECTED_SKILL_SHA256="6cc9dc3199c935916cf6f73fcbbbb0e3bb1b58c8f5109fefa499978908164f51"
EXPECTED_PLUGIN_SHA256="ebda00d55d7518b127f675f062fb5c6e7a1ffdc0a99df1a55ac594400d7d3228"
STALE_ATTESTATION_TEST="tests.test_full_plugin.FullPluginIntegrationTests.test_checked_in_attestation_is_bound_to_immutable_git_archive_evidence"
ALLOW_STALE_ATTESTATION=0

if [[ "${ALLOW_STALE_INSTALLED_ATTESTATION+x}" == "x" ]]; then
  if [[ "$ALLOW_STALE_INSTALLED_ATTESTATION" != "1" ]]; then
    echo "INVALID_STALE_ATTESTATION_OPT_IN" >&2
    exit 1
  fi
  ALLOW_STALE_ATTESTATION=1
fi

for required_path in "$VALIDATION_PYTHON" "$SKILL_VALIDATOR_PATH" "$PLUGIN_VALIDATOR_PATH"; do
  if [[ ! -f "$required_path" ]]; then
    echo "RELEASE_VALIDATION_INPUT_MISSING" >&2
    exit 1
  fi
done

actual_skill_sha="$(shasum -a 256 "$SKILL_VALIDATOR_PATH" | awk '{print $1}')"
actual_plugin_sha="$(shasum -a 256 "$PLUGIN_VALIDATOR_PATH" | awk '{print $1}')"
if [[ "$actual_skill_sha" != "$EXPECTED_SKILL_SHA256" ]]; then
  echo "VALIDATOR_CHECKSUM_MISMATCH: quick_validate.py" >&2
  exit 1
fi
if [[ "$actual_plugin_sha" != "$EXPECTED_PLUGIN_SHA256" ]]; then
  echo "VALIDATOR_CHECKSUM_MISMATCH: validate_plugin.py" >&2
  exit 1
fi

VALIDATION_VENV="$(cd "$(dirname "$VALIDATION_PYTHON")/.." && pwd -P)"
VALIDATION_VENV="$VALIDATION_VENV" "$VALIDATION_PYTHON" -B -c \
  'import os, platform, sys, yaml; from pathlib import Path; root = Path(os.environ["VALIDATION_VENV"]).resolve(); assert platform.python_implementation() == "CPython"; assert sys.version_info[:3] == (3, 11, 15); assert sys.platform == "darwin"; assert platform.machine() == "arm64"; assert yaml.__version__ == "6.0.3"; assert Path(yaml.__file__).resolve().is_relative_to(root)'

"$VALIDATION_PYTHON" -B "$SKILL_VALIDATOR_PATH" "$LINKEDIN_SKILL_ROOT"
PYTHONDONTWRITEBYTECODE=1 "$VALIDATION_PYTHON" -B "$PLUGIN_VALIDATOR_PATH" "$SOURCE_PLUGIN_ROOT"
PYTHONDONTWRITEBYTECODE=1 "$VALIDATION_PYTHON" -B "$SOURCE_PLUGIN_ROOT/tests/run_static_checks.py"
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$SOURCE_PLUGIN_ROOT/scripts${PYTHONPATH:+:$PYTHONPATH}" \
  "$VALIDATION_PYTHON" -B -m unittest discover -s "$SOURCE_PLUGIN_ROOT/tests" -p 'test*.py' -q
if [[ "$ALLOW_STALE_ATTESTATION" == "0" ]]; then
  PYTHONDONTWRITEBYTECODE=1 "$VALIDATION_PYTHON" -B -m unittest discover \
    -s "$PROJECT_ROOT/tests" -p 'test*.py' -q
else
  set +e
  stale_output="$(
    PYTHONDONTWRITEBYTECODE=1 "$VALIDATION_PYTHON" -B -m unittest -v \
      "$STALE_ATTESTATION_TEST" 2>&1
  )"
  stale_status=$?
  set -e
  expected_failure_line="FAIL: test_checked_in_attestation_is_bound_to_immutable_git_archive_evidence ($STALE_ATTESTATION_TEST)"
  failure_count="$(grep -c '^FAIL:' <<<"$stale_output" || true)"
  error_count="$(grep -c '^ERROR:' <<<"$stale_output" || true)"
  exact_failure_count="$(grep -Fxc "$expected_failure_line" <<<"$stale_output" || true)"
  exact_assertion_count="$(
    grep -Fxc "AssertionError: Lists differ: [] != ['release attestation contract is invalid']" \
      <<<"$stale_output" || true
  )"
  exact_summary_count="$(grep -Fxc 'FAILED (failures=1)' <<<"$stale_output" || true)"
  exact_run_count="$(grep -Ec '^Ran 1 test in [0-9.]+s$' <<<"$stale_output" || true)"
  if [[
    "$stale_status" != "1"
    || "$failure_count" != "1"
    || "$error_count" != "0"
    || "$exact_failure_count" != "1"
    || "$exact_assertion_count" != "1"
    || "$exact_summary_count" != "1"
    || "$exact_run_count" != "1"
  ]]; then
    echo "STALE_ATTESTATION_OPT_IN_REJECTED" >&2
    exit 1
  fi
  ROOT_TEST_FILTER='import sys, unittest
from pathlib import Path
root = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(root))
target = "tests.test_full_plugin.FullPluginIntegrationTests.test_checked_in_attestation_is_bound_to_immutable_git_archive_evidence"
def flatten(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from flatten(item)
        else:
            yield item
discovered = unittest.defaultTestLoader.discover(str(root / "tests"), pattern="test*.py", top_level_dir=str(root))
tests = tuple(flatten(discovered))
matches = tuple(test for test in tests if test.id() == target)
if len(matches) != 1:
    raise SystemExit(2)
filtered = unittest.TestSuite(test for test in tests if test.id() != target)
result = unittest.TextTestRunner(verbosity=1).run(filtered)
raise SystemExit(0 if result.wasSuccessful() else 1)'
  PYTHONDONTWRITEBYTECODE=1 "$VALIDATION_PYTHON" -B -c "$ROOT_TEST_FILTER" \
    "$PROJECT_ROOT"
fi
PYTHONDONTWRITEBYTECODE=1 "$VALIDATION_PYTHON" -B "$PROJECT_ROOT/scripts/check_repository_privacy.py"
