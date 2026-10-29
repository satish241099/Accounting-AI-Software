/**
 * Streamable HTTP transport bootstrap for MCP server
 * Uses @modelcontextprotocol/sdk StreamableHTTPServerTransport
 * Transport-agnostic: handler code is identical for stdio and HTTP
 */

import { MCPServer, StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk';
import { createMcpServer } from './server.js';

/** Create and start MCP server via Streamable HTTP transport */
export const startHttp = (port: number = 8080): void => {
  const server = createMcpServer('Malaysia Accounting SaaS MCP Server', '0.1.0');
  server.setTransport(new StreamableHTTPServerTransport({ port }));
  server.start();
};

export default startHttp;