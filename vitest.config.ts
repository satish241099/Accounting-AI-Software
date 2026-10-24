import { defineConfig } from 'vitest/config';
import { readFileSync } from 'node:fs';

export default defineConfig({
  test: {
    environment: 'node',
    globals: true,
    // Serial execution avoids EmbeddedPostgres connection exhaustion on Windows
    // where multiple pg clients open in parallel.
    concurrent: false,
    // Global setup/teardown uses embedded-postgres (real PostgreSQL,
    // not pg-mem). docker-compose.test.yml remains the CI infra path.
    setupFiles: [],
  },
});
