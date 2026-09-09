#!/usr/bin/env bash
# Wrapper around checks/repo_check.py, kept because CI, the README, and habit
# all say `bash checks/repo-check.sh`. The checks themselves live in the Python
# file; this only locates the repository root and the interpreter.
#
# Usage: checks/repo-check.sh [repo-root]
#        REPO_CHECK_LIVE=1 checks/repo-check.sh   # also runs `claude plugin validate`
# Exit codes: 0 all PASS (WARN and SKIP allowed), 1 at least one FAIL.

set -u

if ! command -v python3 >/dev/null 2>&1; then
  echo "FAIL  python3 not found on PATH" >&2
  exit 1
fi

HERE="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$HERE/repo_check.py" "${1:-$(cd "$HERE/.." && pwd)}"
