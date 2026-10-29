const fs = require('fs');
const path = require('path');

const ROUTING_PATH = path.join(__dirname, '..', '.fusion', 'routing-rules.json');

describe('Routing Rules', () => {
  let routing;

  beforeAll(() => {
    const content = fs.readFileSync(ROUTING_PATH, 'utf-8');
    routing = JSON.parse(content);
  });

  test('routing rules has valid version', () => {
    expect(routing.version).toBe('1.0');
  });

  test('routing rules has agent_routes array', () => {
    expect(Array.isArray(routing.agent_routes)).toBe(true);
  });

  test('Legacy Modernization Specialist (agent-9fde6dbd) has routing configured', () => {
    const legacyRoute = routing.agent_routes.find(r => r.agent_id === 'agent-9fde6dbd');
    expect(legacyRoute).toBeDefined();
    expect(legacyRoute.provider).toBe('freellmapi');
    expect(Array.isArray(legacyRoute.fallback_chain)).toBe(true);
    expect(legacyRoute.fallback_chain).toContain('aws-bedrock');
  });

  test('Architecture Lead (agent-7535016b) has routing configured', () => {
    const archRoute = routing.agent_routes.find(r => r.agent_id === 'agent-7535016b');
    expect(archRoute).toBeDefined();
    expect(archRoute.provider).toBe('freellmapi');
    expect(Array.isArray(archRoute.fallback_chain)).toBe(true);
    expect(archRoute.fallback_chain).toContain('aws-bedrock');
  });

  test('global fallback is configured', () => {
    expect(routing.global_fallback).toBeDefined();
    expect(routing.global_fallback.provider).toBe('aws-bedrock');
    expect(routing.global_fallback.model).toBeDefined();
  });

  test('all agent routes have fallback chains', () => {
    routing.agent_routes.forEach(route => {
      expect(Array.isArray(route.fallback_chain)).toBe(true);
      expect(route.fallback_chain.length).toBeGreaterThan(0);
    });
  });

  test('fallback chain references valid providers', () => {
    const providerNames = routing.providers?.map(p => p.name) || ['freellmapi', 'aws-bedrock'];
    routing.agent_routes.forEach(route => {
      route.fallback_chain.forEach(fallback => {
        expect(providerNames).toContain(fallback);
      });
    });
  });
});