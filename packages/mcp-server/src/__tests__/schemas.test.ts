/**
 * Tests for Zod schemas — validates parsing and JSON Schema export
 */

import { describe, it, expect } from 'vitest';
import {
  SearchComplianceInputSchema,
  SearchComplianceOutputSchema,
  AnswerWithCitationsInputSchema,
  GetCitationInputSchema,
  RefusalSchema,
  CitationIdentitySchema,
} from '../schemas/tools.js';
import { ResourceMetadataSchema } from '../schemas/resources.js';

describe('Zod Schemas', () => {
  it('SearchComplianceInputSchema validates valid input', () => {
    const input = { query: 'SST registration threshold' };
    const parsed = SearchComplianceInputSchema.parse(input);
    expect(parsed.query).toBe('SST registration threshold');
  });

  it('SearchComplianceInputSchema rejects empty query', () => {
    const input = { query: '' };
    expect(() => SearchComplianceInputSchema.parse(input)).toThrow();
  });

  it('RefusalSchema validates refusal reason codes', () => {
    const refusal = {
      refusal: true,
      reason: 'no_evidence',
      message: 'No evidence found',
    };
    expect(() => RefusalSchema.parse(refusal)).not.toThrow();
  });

  it('RefusalSchema rejects invalid reason codes', () => {
    const refusal = {
      refusal: true,
      reason: 'invalid_reason',
      message: 'Test',
    };
    expect(() => RefusalSchema.parse(refusal)).toThrow();
  });

  it('CitationIdentitySchema validates stable triple', () => {
    const citation = {
      document_identity: 'act-sst-2024',
      document_version: 'v1.0',
      section_anchor: 'section-12',
    };
    expect(() => CitationIdentitySchema.parse(citation)).not.toThrow();
  });

  it('GetCitationInputSchema validates citation identity', () => {
    const input = {
      citation_id: {
        document_identity: 'act-sst-2024',
        document_version: 'v1.0',
        section_anchor: 'section-12',
      },
    };
    expect(() => GetCitationInputSchema.parse(input)).not.toThrow();
  });

  it('ResourceMetadataSchema validates metadata fields', () => {
    const metadata = {
      document_identity: 'act-sst-2024',
      document_version: 'v1.0',
      section_anchor: 'section-12',
      document_type: 'act' as const,
      jurisdiction: 'MY',
    };
    expect(() => ResourceMetadataSchema.parse(metadata)).not.toThrow();
  });
});
