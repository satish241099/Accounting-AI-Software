/**
 * stdio transport bootstrap for MCP server
 * Uses @modelcontextprotocol/sdk StdioServerTransport
 * Transport-agnostic: handler code is identical for stdio and HTTP
 */

import { MCPServer, StdioServerTransport } from '@modelcontextprotocol/sdk';
import { createMcpServer } from './server.js';

/** Create and start MCP server via stdio transport */
export const startStdio = (): void => {
  const server = createMcpServer('Malaysia Accounting SaaS MCP Server', '0.1.0');
  server.setTransport(new StdioServerTransport());
  server.start();
};

export default startStdio;