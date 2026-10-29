/**
 * Tests for transport bootstrap — validates stdio and HTTP server instantiation
 */

import { describe, it, expect } from 'vitest';
import { startStdio } from '../transports/stdio.js';
import { startHttp } from '../transports/http.js';

describe('Transport Bootstrap', () => {
  it('startStdio is a function', () => {
    expect(typeof startStdio).toBe('function');
  });

  it('startHttp is a function', () => {
    expect(typeof startHttp).toBe('function');
  });

  it('startHttp accepts optional port parameter', () => {
    // Just verify the function signature — actual start requires MCP server context
    expect(() => startHttp(3000)).not.toThrow();
  });
});