/**
 * Export Zod schemas to JSON Schema files
 * Writes tools and resources JSON Schemas to dist/schemas/
 */

import { z } from 'zod';
import { jsonSchemaTransform } from 'zod-to-json-schema';
import * as fs from 'fs/promises';
import * as path from 'path';

const SCHEMAS_DIR = path.resolve(__dirname, '../../dist/schemas');
const ensureDir = () => fs.mkdir(SCHEMAS_DIR, { recursive: true });

/** Write JSON schema for a Zod object */
const writeJsonSchema = async (schema: z.ZodObject, name: string) => {
  ensureDir();
  const json = JSON.stringify(
    schema._def.transform(jsonSchemaTransform),
    null,
    2
  );
  await fs.writeFile(path.join(SCHEMAS_DIR, `${name}.json`), json);
};

export const exportSchemas = async () => {
  await ensureDir();

  // Export tool schemas
  await writeJsonSchema(
    z.object({
      query: z.string().min(1),
      filters: z.object({
        document_type: z.enum(['act', 'regulation', 'guideline', 'circular', 'ruling']).optional(),
      }).optional(),
    }),
    'search-compliance-input'
  );

  await writeJsonSchema(
    z.object({
      refusal: z.literal(true),
      reason: z.enum(['no_evidence', 'blocked_source', 'restricted_content', 'schema_violation', 'citation_missing']),
      message: z.string(),
    }),
    'refusal-schema'
  );

  // Export resource schemas
  await writeJsonSchema(
    z.object({
      document_identity: z.string(),
      document_version: z.string(),
      section_anchor: z.string(),
    }),
    'resource-metadata'
  );

  console.log('JSON Schemas exported to', SCHEMAS_DIR);
};

export const exportAllSchemas = async () => {
  await exportSchemas();
  console.log('All schemas exported successfully');
};