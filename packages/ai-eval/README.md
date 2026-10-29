# AI Evaluation Framework

Deterministic-first LLM evaluation harness for the AI & LLM Foundation mission (M-MVIJWODE-0007-QN4Z).

## Overview

This framework provides repeatable, auditable evaluation for all AI features in the Malaysia Accounting SaaS, with PDPA compliance built-in.

## Features

- **Rubric definitions** with 5 anchored scoring dimensions
- **Versioned golden sets** with synthetic data only
- **Deterministic scoring** preferred over model grading
- **Regression gates** with pytest integration
- **Human spot-check templates** for auditable review

## Scoring Dimensions

1. **Groundedness** - Claims supported by corpus
2. **Citation Accuracy** - Correct citation resolution
3. **Refusal Correctness** - Proper handling of insufficient evidence
4. **Schema Conformance** - Output format compliance
5. **Harmful Advice Avoidance** - Safety and compliance

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run evaluation on golden set
python src/harness.py --capability compliance_qa --version v1.0.0

# Check for regressions
pytest tests/test_regression.py
```

## Redaction Boundary

**Never use real client data in golden sets.** All evaluation fixtures must be synthetic or explicitly redacted. Client financial data must never leave ap-southeast-1.

## Documentation

- `rubric/definitions.md` - Scoring rubric with worked examples
- `golden/schema.json` - Golden set format specification
- `worksheet/human_spot_check_template.md` - Human review template

## PDPA Compliance

This framework enforces advisory-only output. AI outputs never write directly to ledger or filing paths. All client data must be synthetic in evaluation sets.

## Version

1.0.0
