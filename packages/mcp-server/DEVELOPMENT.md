# MCP Server Development Notes

## Status

**Current State:** Scaffolded (Step 1 complete)
**Blocked on:** ACCO-011 (corpus build) for Steps 2-3 implementation

## Completed (2026-10-25)

- ✅ Step 1: Scaffold project structure and TypeScript setup
  - `package.json` with dependencies: `@modelcontextprotocol/sdk`, `zod`, `zod-to-json-schema`
  - `tsconfig.json` targeting ES2022, strict mode
  - `src/server.ts` with `createMcpServer()` factory
  - `README.md` with mission linkage M-MVKTMUFU-000V-OQTS and MCP spec revision pin
  - Test scaffolding: `src/__tests__/schemas.test.ts`, `src/__tests__/transports.test.ts`

## Pending (Awaiting ACCO-011)

- ⏳ Step 2: Define Zod schemas for tools and resources
  - `src/schemas/tools.ts` — DONE (scaffolded, needs ACCO-011 corpus metadata schema alignment)
  - `src/schemas/resources.ts` — DONE (scaffolded, needs ACCO-011 manifest format)
  - `src/schemas/index.ts` — DONE
  - `src/schemas/json-schema.ts` — DONE (export helper)
  - **Blocker:** ACCO-011 must hand off chunk metadata schema (`acc011-scr-0.9.0-draft`)

- ⏳ Step 3: Setup stdio and Streamable HTTP transports
  - `src/transports/stdio.ts` — DONE (scaffolded)
  - `src/transports/http.ts` — DONE (scaffolded)
  - `src/types/mcp.ts` — DONE (refusal reasons, citation identity)
  - **Blocker:** ACCO-011 must hand off corpus store adapter contract

## ACCO-011 Handoff Requirements

When ACCO-011 completes, it must provide:
1. Corpus manifest format + example artifact
2. Chunking strategy (deterministic, section_anchor-bound)
3. Chunk metadata schema (`acc011-scr-0.9.0-draft`)
4. Build command + output shape (JSONL chunk files location/format)

## Next Actions (When Unblocked)

1. Align Zod schemas with ACCO-011 chunk metadata schema
2. Implement corpus store adapter (reads ACCO-011 JSONL chunk files)
3. Build citation resolver (stable triple → current chunk)
4. Implement transport-agnostic tool handlers
5. Add refusal factory, audit emitter, data-classification guard
6. Wire transports + server bootstrap
7. Protocol compliance test suite

## MCP Spec Version

**Pinned Revision:** `2025-03-26` (latest stable as of 2026-10-25)
**SDK Package:** `@modelcontextprotocol/sdk@^1.12.1`

## Hard Constraints (Non-Negotiable)

- Public regulatory text ONLY — no Restricted-class data configuration
- PDPA 2024: AWS ap-southeast-1 residency, no non-region outbound calls
- Refusal = first-class schema-valid outcome (never error/fallback)
- Audit hook per tool call
- Stable citation identity: `document_identity + document_version + section_anchor`
- Machine-readable refusal reason codes: `no_evidence`, `blocked_source`, `restricted_content`, `schema_violation`, `citation_missing`