# MCP Server — Malaysia Accounting SaaS

**Mission:** M-MVKTMUFU-000V-OQTS (Malaysia Accounting SaaS Core Foundation)
**MCP Spec Revision:** `2025-03-26` (latest stable as of 2026-10-25)

## Overview

A transport-agnostic MCP server skeleton for compliance-focused tool handlers in the Malaysia Accounting SaaS platform. Implements Zod schemas for tool/input contracts with JSON Schema export, dual stdio and Streamable HTTP transports.

## Tools

| Tool | Description |
|------|-------------|
| `search_compliance` | Search compliance documents by query with filters |
| `answer_with_citations` | Answer queries with per-claim citations and confidence/refusal |
| `get_citation` | Retrieve exact cited chunk with source metadata |

## Transports

- **stdio:** Standard I/O transport for CLI usage
- **Streamable HTTP:** HTTP transport with SSE streaming support

## Usage

```bash
# Build
pnpm build

# Run via stdio
pnpm start:stdio

# Run via HTTP
pnpm start:http
```

## Constraints

- **Public regulatory text ONLY** — no Restricted-class data configuration
- **PDPA 2024 compliance** — AWS ap-southeast-1 residency, no non-region outbound calls
- **Refusal-first design** — machine-readable refusal reason codes (`no_evidence`, `blocked_source`, `restricted_content`, `schema_violation`, `citation_missing`)
- **Stable citation identity** — `document_identity + document_version + section_anchor` (NOT chunk ID)
- **Audit hooks** — per tool call: caller identity, tool, query, chunk IDs, timestamp

## Related Tasks

- ACCO-011 (corpus build) — provides manifest, chunking strategy, metadata schema
- ACCO-046 (MCP server) — this task
- ACCO-058 (manifest skeleton/schema) — DONE

## Development

```bash
# Install dependencies
pnpm install

# Type check
pnpm typecheck

# Lint
pnpm lint

# Run tests
pnpm test
```
