/**
 * MCP Protocol Types for Malaysia Accounting SaaS
 */

export type RefusalReason =
  | 'no_evidence'
  | 'blocked_source'
  | 'restricted_content'
  | 'schema_violation'
  | 'citation_missing';

export interface CitationIdentity {
  /** Stable document identifier (NOT chunk ID) */
  document_identity: string;
  /** Document version hash or number */
  document_version: string;
  /** Section anchor within the document */
  section_anchor: string;
}

export interface ComplianceChunk {
  citation: CitationIdentity;
  content: string;
  source?: string;
  effective_date?: string;
  section?: string;
}

export interface AuditEvent {
  caller_identity: string;
  tool: string;
  query: string;
  chunk_ids: string[];
  timestamp: string;
}
