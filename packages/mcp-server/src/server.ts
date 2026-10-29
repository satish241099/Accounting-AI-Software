/**
 * MCP server factory — transport-agnostic core
 * Creates an MCPServer instance from @modelcontextprotocol/sdk
 * Exports startStdio() and startHttp() entrypoints
 */

import { MCPServer } from '@modelcontextprotocol/sdk';
import { z } from 'zod';
import { startStdio } from './transports/stdio.js';
import { startHttp } from './transports/http.js';
import { exportAllSchemas } from './schemas/json-schema.js';

// Initialize MCP server with transport-agnostic design
const server = new MCPServer({
  name: 'Malaysia Accounting SaaS MCP Server',
  version: '0.1.0',
  tools: [],
  resources: [],
});

// Register Zod schemas for tool contracts
const registerSchemas = () => {
  // Search compliance tool
  server.setTool('search_compliance', {
    schema: z.object({
      query: z.string().min(1).describe('Search query for compliance documents'),
      filters: z
        .object({
          document_type: z
            .enum(['act', 'regulation', 'guideline', 'circular', 'ruling'])
            .optional(),
          jurisdiction: z.string().optional(),
          effective_date_from: z.string().optional(),
          effective_date_to: z.string().optional(),
          language: z.enum(['en', 'ms', 'zh']).optional(),
        })
        .optional(),
    }),
    handler: async (params) => {
      // TODO: implement search with corpus store adapter (requires ACCO-011)
      return {
        refusal: true,
        reason: 'no_evidence',
        message: 'Search not yet implemented — awaiting ACCO-011 corpus build',
      };
    },
  });

  // Answer with citations tool
  server.setTool('answer_with_citations', {
    schema: z.object({
      query: z.string().min(1).describe('Question to answer with citations'),
      max_citations: z.number().int().positive().max(20).optional(),
      confidence_threshold: z.number().min(0).max(1).optional(),
    }),
    handler: async (params) => {
      // TODO: implement citation resolver (requires ACCO-011)
      return {
        refusal: true,
        reason: 'no_evidence',
        message: 'Answer not yet implemented — awaiting ACCO-011 corpus build',
      };
    },
  });

  // Get citation tool
  server.setTool('get_citation', {
    schema: z.object({
      citation_id: z.object({
        document_identity: z.string(),
        document_version: z.string(),
        section_anchor: z.string(),
      }),
    }),
    handler: async (params) => {
      // TODO: implement citation lookup (requires ACCO-011)
      return {
        refusal: true,
        reason: 'no_evidence',
        message: 'Citation lookup not yet implemented — awaiting ACCO-011 corpus build',
      };
    },
  });
};

// Register all schemas and handlers
registerSchemas();

/**
 * Export MCP server factory
 * Creates a new MCPServer configured for the Malaysia Accounting SaaS mission
 */
export const createMcpServer = (name: string, version: string): MCPServer => {
  const instance = new MCPServer({ name, version, tools: [], resources: [] });
  return instance;
};

/**
 * Entry point: start via stdio
 */
export const startMcpServer = (): void => {
  server.start();
};

/**
 * Start via stdio transport
 */
export const startStdio = (): void => {
  startMcpServer();
};

/**
 * Start via Streamable HTTP transport
 * @param port HTTP port (default: 8080)
 */
export const startHttp = (port: number = 8080): void => {
  startMcpServer();
};