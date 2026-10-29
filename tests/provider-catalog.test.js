const fs = require('fs');
const path = require('path');

const CATALOG_PATH = path.join(__dirname, '..', '.fusion', 'provider-catalog.json');

describe('Provider Catalog', () => {
  let catalog;

  beforeAll(() => {
    const content = fs.readFileSync(CATALOG_PATH, 'utf-8');
    catalog = JSON.parse(content);
  });

  test('catalog has valid version', () => {
    expect(catalog.version).toBe('1.0');
  });

  test('catalog has providers array', () => {
    expect(Array.isArray(catalog.providers)).toBe(true);
    expect(catalog.providers.length).toBeGreaterThan(0);
  });

  test('freellmapi provider exists with required fields', () => {
    const freellmapi = catalog.providers.find(p => p.name === 'freellmapi');
    expect(freellmapi).toBeDefined();
    expect(freellmapi.type).toBe('cloudflare');
    expect(freellmapi.model).toBeDefined();
    expect(freellmapi.endpoint).toBeDefined();
    expect(freellmapi.fallback_model).toBeDefined();
    expect(freellmapi.fallback_provider).toBe('aws-bedrock');
    expect(freellmapi.region).toBe('ap-southeast-1');
    expect(freellmapi.pdpa_compliant).toBe(true);
  });

  test('aws-bedrock provider exists with required fields', () => {
    const bedrock = catalog.providers.find(p => p.name === 'aws-bedrock');
    expect(bedrock).toBeDefined();
    expect(bedrock.type).toBe('bedrock');
    expect(bedrock.model).toBeDefined();
    expect(bedrock.endpoint).toBeDefined();
    expect(bedrock.region).toBe('ap-southeast-1');
    expect(bedrock.pdpa_compliant).toBe(true);
  });

  test('all providers have PDPA-compliant region', () => {
    catalog.providers.forEach(provider => {
      expect(provider.region).toBe('ap-southeast-1');
      expect(provider.pdpa_compliant).toBe(true);
    });
  });

  test('freellmapi has fallback configured', () => {
    const freellmapi = catalog.providers.find(p => p.name === 'freellmapi');
    expect(freellmapi.fallback_model).toBeDefined();
    expect(freellmapi.fallback_provider).toBeDefined();
  });
});