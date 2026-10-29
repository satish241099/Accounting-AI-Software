/**
 * Zod schemas for MCP tool input/output contracts
 * Enforces refusal reason codes: no_evidence, blocked_source, restricted_content, schema_violation, citation_missing
 */

import { z } from 'zod';
import { RefusalReason, CitationIdentity, ComplianceChunk } from '../types/mcp.js';

/** Shared refusal schema */
export const RefusalSchema = z.object({
  refusal: z.literal(true),
  reason: z.enum([
    'no_evidence',
    'blocked_source',
    'restricted_content',
    'schema_violation',
    'citation_missing'
  ] as [RefusalReason, ...RefusalReason[]]),
  message: z.string(),
});

/** Citation identity — stable triple (NOT chunk ID) */
export const CitationIdentitySchema = z.object({
  document_identity: z.string().describe('Stable document identifier'),
  document_version: z.string().describe('Document version hash or number'),
  section_anchor: z.string().describe('Section anchor within the document'),
});

/** Compliance chunk with citation */
export const ComplianceChunkSchema = z.object({
  citation: CitationIdentitySchema,
  content: z.string(),
  source: z.string().optional(),
  effective_date: z.string().optional(),
  section: z.string().optional(),
});

/** Search compliance tool input */
export const SearchComplianceInputSchema = z.object({
  query: z.string().min(1).describe('Search query for compliance documents'),
  filters: z.object({
    document_type: z.enum(['act', 'regulation', 'guideline', 'circular', 'ruling']).optional(),
    jurisdiction: z.string().optional(),
    effective_date_from: z.string().optional(),
    effective_date_to: z.string().optional(),
    language: z.enum(['en', 'ms', 'zh']).optional(),
  }).optional().describe('Optional filters for search'),
});

/** Search compliance tool output — ranked chunks or refusal */
export const SearchComplianceOutputSchema = z.union([
  z.object({
    refusal: z.literal(false),
    chunks: z.array(ComplianceChunkSchema).describe('Ranked compliance chunks with citations'),
    total_matches: z.number().int().nonnegative(),
  }),
  RefusalSchema,
]);

/** Answer with citations tool input */
export const AnswerWithCitationsInputSchema = z.object({
  query: z.string().min(1).describe('Question to answer with citations'),
  max_citations: z.number().int().positive().max(20).optional().default(10),
  confidence_threshold: z.number().min(0).max(1).optional().default(0.7),
});

/** Answer with citations tool output — answer + citations or refusal */
export const AnswerWithCitationsOutputSchema = z.union([
  z.object({
    refusal: z.literal(false),
    answer: z.string(),
    citations: z.array(z.object({
      citation: CitationIdentitySchema,
      claim: z.string(),
      confidence: z.number().min(0).max(1),
    })).describe('Per-claim citations with confidence'),
    overall_confidence: z.number().min(0).max(1),
  }),
  RefusalSchema,
]);

/** Get citation tool input */
export const GetCitationInputSchema = z.object({
  citation_id: CitationIdentitySchema.describe('Stable citation identity triple'),
});

/** Get citation tool output — exact chunk or refusal */
export const GetCitationOutputSchema = z.union([
  z.object({
    refusal: z.literal(false),
    chunk: ComplianceChunkSchema,
  }),
  RefusalSchema,
]);

/** Tool definitions for JSON Schema export */
export const ToolSchemas = {
  search_compliance: {
    input: SearchComplianceInputSchema,
    output: SearchComplianceOutputSchema,
  },
  answer_with_citations: {
    input: AnswerWithCitationsInputSchema,
    output: AnswerWithCitationsOutputSchema,
  },
  get_citation: {
    input: GetCitationInputSchema,
    output: GetCitationOutputSchema,
  },
} as const;

/** Type exports */
export type SearchComplianceInput = z.infer<typeof SearchComplianceInputSchema>;
export type SearchComplianceOutput = z.infer<typeof SearchComplianceOutputSchema>;
export type AnswerWithCitationsInput = z.infer<typeof AnswerWithCitationsInputSchema>;
export type AnswerWithCitationsOutput = z.infer<typeof AnswerWithCitationsOutputSchema>;
export type GetCitationInput = z.infer<typeof GetCitationInputSchema>;
export type GetCitationOutput = z.infer<typeof GetCitationOutputSchema>;