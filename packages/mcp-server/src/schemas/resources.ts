/**
 * Zod schemas for MCP resources with stable citation identity
 */

import { z } from 'zod';
import { CitationIdentity } from '../types/mcp.js';

/** Resource metadata with stable citation identity */
export const ResourceMetadataSchema = z.object({
  /** Stable document identifier */
  document_identity: z.string(),
  /** Document version (hash or semantic version) */
  document_version: z.string(),
  /** Section anchor within document */
  section_anchor: z.string(),
  /** Source URI or path */
  source_uri: z.string().url().optional(),
  /** Effective date of the regulation/text */
  effective_date: z.string().optional(),
  /** Language code (en, ms, zh) */
  language: z.enum(['en', 'ms', 'zh']).optional(),
  /** Document type */
  document_type: z.enum(['act', 'regulation', 'guideline', 'circular', 'ruling']).optional(),
  /** Jurisdiction (e.g., 'MY' for Malaysia) */
  jurisdiction: z.string().optional(),
});

/** Compliance document resource */
export const ComplianceDocumentResourceSchema = z.object({
  uri: z.string().describe('Resource URI (e.g., compliance:document:identity:version)'),
  name: z.string().describe('Human-readable document name'),
  description: z.string().optional(),
  mimeType: z.literal('text/markdown').or(z.literal('application/json')),
  metadata: ResourceMetadataSchema,
});

/** Resource list output */
export const ResourceListOutputSchema = z.object({
  resources: z.array(ComplianceDocumentResourceSchema),
});

/** Type exports */
export type ResourceMetadata = z.infer<typeof ResourceMetadataSchema>;
export type ComplianceDocumentResource = z.infer<typeof ComplianceDocumentResourceSchema>;
export type ResourceListOutput = z.infer<typeof ResourceListOutputSchema>;
