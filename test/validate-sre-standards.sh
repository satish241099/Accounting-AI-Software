#!/usr/bin/env bash
set -euo pipefail

# Resolve repo root (parent of test/ where this script lives)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
STANDARDS="$REPO_ROOT/docs/sre/standards"
ADRS="$REPO_ROOT/docs/sre/adrs"
RUNBOOKS="$REPO_ROOT/docs/sre/runbooks"

# Validate each file has its required headings
# Check each file independently with its own required headings

# File: code-review-checklist.md
FILE="$STANDARDS/code-review-checklist.md"
if [[ ! -f "$FILE" ]]; then
  echo "Missing required file: $FILE" >&2
  exit 1
fi
for heading in "## Purpose" "## Scope" "## Invariants" "## PR Review Checklist"; do
  if ! grep -qF "$heading" "$FILE"; then
    echo "Missing heading '$heading' in code-review-checklist.md" >&2
    exit 1
  fi
done

# File: documentation-standards.md
FILE="$STANDARDS/documentation-standards.md"
if [[ ! -f "$FILE" ]]; then
  echo "Missing required file: $FILE" >&2
  exit 1
fi
for heading in "# SRE Foundation Documentation Standards" "## ADR Template" "## Runbook Template" "## Compliance Metadata Rules" "## Documentation Hierarchy" "## Review Cadence"; do
  if ! grep -qF "$heading" "$FILE"; then
    echo "Missing heading '$heading' in documentation-standards.md" >&2
    exit 1
  fi
done

# File: ci-quality-gates.md
FILE="$STANDARDS/ci-quality-gates.md"
if [[ ! -f "$FILE" ]]; then
  echo "Missing required file: $FILE" >&2
  exit 1
fi
for heading in "# SRE Foundation CI Quality Gates" "## CI Quality Gate: 1 - Dependency CVE Scan" "## CI Quality Gate: 2 - Lint + Static Analysis" "## CI Quality Gate: 3 - SLO Burn-Rate Validation" "## CI Quality Gate: 4 - Runbook Lint" "## CI Quality Gate: 5 - Deployment Safety Checks"; do
  if ! grep -qF "$heading" "$FILE"; then
    echo "Missing heading '$heading' in ci-quality-gates.md" >&2
    exit 1
  fi
done

# File: handoff-templates.md
FILE="$STANDARDS/handoff-templates.md"
if [[ ! -f "$FILE" ]]; then
  echo "Missing required file: $FILE" >&2
  exit 1
fi
for heading in "# SRE Foundation Handoff Templates" "## Purpose" "## Scope" "## 1. Observability Stack Handoff"; do
  if ! grep -qF "$heading" "$FILE"; then
    echo "Missing heading '$heading' in handoff-templates.md" >&2
    exit 1
  fi
done

# Verify README exists
if [[ ! -f "$STANDARDS/README.md" ]]; then
  echo "Missing README.md in docs/sre/standards" >&2
  exit 1
fi

# Verify index files under adrs and runbooks
if [[ ! -f "$ADRS/index.md" ]]; then
  echo "Missing ADR index file" >&2
  exit 1
fi
if [[ ! -f "$RUNBOOKS/index.md" ]]; then
  echo "Missing runbook index file" >&2
  exit 1
fi

echo "All validations passed"
exit 0