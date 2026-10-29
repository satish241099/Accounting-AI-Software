#!/usr/bin/env bash
# Automated validation that required docs exist and contain required headings.
# Run: bash test/validate-standards.sh
# Exit 0 if all checks pass; exit 1 on first failure.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
QUALITY_DIR="$ROOT_DIR/docs/quality"

errors=0

# --- Checklist ---

check() {
  local label="$1"
  local result="$2"
  if [ "$result" = "true" ]; then
    echo "  ✅ $label"
  else
    echo "  ❌ $label"
    errors=$((errors + 1))
  fi
}

# --- 1. docs/quality/README.md exists and links the four standards ---

echo "▶ Checking docs/quality/README.md exists"
check "README.md exists" "$([ -f "$QUALITY_DIR/README.md" ] && echo true || echo false)"

echo "▶ Checking README.md lists the four standards"
readme_content="$(cat "$QUALITY_DIR/README.md")"
check "README.md lists code-quality-standards.md" "$(echo "$readme_content" | grep -q 'code-quality-standards.md' && echo true || echo false)"
check "README.md lists documentation-conventions.md" "$(echo "$readme_content" | grep -q 'documentation-conventions.md' && echo true || echo false)"
check "README.md lists ci-quality-gates.md" "$(echo "$readme_content" | grep -q 'ci-quality-gates.md' && echo true || echo false)"
check "README.md lists pr-review-checklist.md" "$(echo "$readme_content" | grep -q 'pr-review-checklist.md' && echo true || echo false)"

# --- 2. code-quality-standards.md exists and has required sections ---

echo ""
echo "▶ Checking code-quality-standards.md exists"
check "code-quality-standards.md exists" "$([ -f "$QUALITY_DIR/code-quality-standards.md" ] && echo true || echo false)"

if [ -f "$QUALITY_DIR/code-quality-standards.md" ]; then
  cq_content="$(cat "$QUALITY_DIR/code-quality-standards.md")"

  echo "▶ Checking required sections in code-quality-standards.md"
  check "Scope & principles section exists" "$(echo "$cq_content" | grep -q '## Scope' && echo true || echo false)"
  check "Financial invariants section exists" "$(echo "$cq_content" | grep -q 'Financial Invariants' && echo true || echo false)"
  check "Tenant isolation section exists" "$(echo "$cq_content" | grep -q '### Tenant Isolation' && echo true || echo false)"
  check "Temporal correctness section exists" "$(echo "$cq_content" | grep -q '### Temporal Correctness' && echo true || echo false)"
  check "Determinism & idempotency section exists" "$(echo "$cq_content" | grep -q '### Determinism & Idempotency' && echo true || echo false)"
  check "Audit trail section exists" "$(echo "$cq_content" | grep -q '### Audit Trail' && echo true || echo false)"
  check "Linting rule categories exist" "$(echo "$cq_content" | grep -q '### (Correctness|Style|Security)' && echo true || echo false)"
  check "Static analysis policy exists" "$(echo "$cq_content" | grep -q 'Static Analysis Policy' && echo true || echo false)"
  test -n "$(echo "$cq_content" | grep -c 'decimal-cents as integers')" && check "Financial invariants mention decimal-cents as integers" "true" || check "Financial invariants mention decimal-cents as integers" "false"
fi

# --- 3. documentation-conventions.md exists and has required sections ---

echo ""
echo "▶ Checking documentation-conventions.md exists"
check "documentation-conventions.md exists" "$([ -f "$QUALITY_DIR/documentation-conventions.md" ] && echo true || echo false)"

if [ -f "$QUALITY_DIR/documentation-conventions.md" ]; then
  dc_content="$(cat "$QUALITY_DIR/documentation-conventions.md")"

  echo "▶ Checking required sections in documentation-conventions.md"
  check "Module header convention exists" "$(echo "$dc_content" | grep -q 'Module Header Convention' && echo true || echo false)"
  check "JSDoc/TSDoc example exists" "$(echo "$dc_content" | grep -q 'TypeScript.*JSDoc' && echo true || echo false)"
  check "Python docstring example exists" "$(echo "$dc_content" | grep -q 'Google.style docstrings' && echo true || echo false)"
  check "PHPDoc example exists" "$(echo "$dc_content" | grep -q 'PHPDoc' && echo true || echo false)"
  check "OpenAPI 3.1 mention exists" "$(echo "$dc_content" | grep -q 'OpenAPI 3.1' && echo true || echo false)"
  check "Docs hierarchy section exists" "$(echo "$dc_content" | grep -q 'Docs Hierarchy' && echo true || echo false)"
fi

# --- 4. ci-quality-gates.md exists and has required sections ---

echo ""
echo "▶ Checking ci-quality-gates.md exists"
check "ci-quality-gates.md exists" "$([ -f "$QUALITY_DIR/ci-quality-gates.md" ] && echo true || echo false)"

if [ -f "$QUALITY_DIR/ci-quality-gates.md" ]; then
  cg_content="$(cat "$QUALITY_DIR/ci-quality-gates.md")"

  echo "▶ Checking required gates in ci-quality-gates.md"
  check "Gate 1: Dependency CVE Scan exists" "$(echo "$cg_content" | grep -q 'Dependency CVE Scan' && echo true || echo false)"
  check "Gate 2: Lint + Static Analysis exists" "$(echo "$cg_content" | grep -q 'Lint + Static Analysis' && echo true || echo false)"
  check "Gate 3: Financial Math Property-Based Tests exists" "$(echo "$cg_content" | grep -q 'Financial Math Property' && echo true || echo false)"
  check "Gate 4: OpenAPI Schema Validation exists" "$(echo "$cg_content" | grep -q 'OpenAPI Schema Validation' && echo true || echo false)"
  check "Gate 5: Docstring Coverage exists" "$(echo "$cg_content" | grep -q 'Docstring Coverage' && echo true || echo false)"
  check "Pass/Fail semantics table exists" "$(echo "$cg_content" | grep -q 'Pass/Fail Semantics' && echo true || echo false)"
fi

# --- 5. pr-review-checklist.md exists and has required sections ---

echo ""
echo "▶ Checking pr-review-checklist.md exists"
check "pr-review-checklist.md exists" "$([ -f "$QUALITY_DIR/pr-review-checklist.md" ] && echo true || echo false)"

if [ -f "$QUALITY_DIR/pr-review-checklist.md" ]; then
  pr_content="$(cat "$QUALITY_DIR/pr-review-checklist.md")"

  echo "▶ Checking required invariant sections in pr-review-checklist.md"
  check "Determinism checklist exists" "$(echo "$pr_content" | grep -q '### 1. Determinism' && echo true || echo false)"
  check "Idempotency checklist exists" "$(echo "$pr_content" | grep -q '### 2. Idempotency' && echo true || echo false)"
  check "Audit Trail checklist exists" "$(echo "$pr_content" | grep -q '### 3. Audit Trail' && echo true || echo false)"
  check "Explicit Tenant Context checklist exists" "$(echo "$pr_content" | grep -q '### 4. Explicit Tenant Context' && echo true || echo false)"
  check "No Token/PII Logging checklist exists" "$(echo "$pr_content" | grep -q '### 5. No Token' && echo true || echo false)"
  check "As-of-Dated Tax Logic checklist exists" "$(echo "$pr_content" | grep -q '### 6. As-of-Dated' && echo true || echo false)"
  check "Fail-Loud on Compliance checklist exists" "$(echo "$pr_content" | grep -q '### 7. Fail-Loud' && echo true || echo false)"
  check "Waiver process exists" "$(echo "$pr_content" | grep -q 'Waiver Process' && echo true || echo false)"
fi

# --- Summary ---

echo ""
if [ "$errors" -eq 0 ]; then
  echo "🎉 All checks passed (0 errors)."
  exit 0
else
  echo "❌ $errors check(s) failed."
  exit 1
fi