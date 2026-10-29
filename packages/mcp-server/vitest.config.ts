import { defineConfig } from 'vitest/config'
import path from 'path'

export default defineConfig({
  test: {
    testTimeout: 5000,
    expect: {
      timeout: 5000,
    },
    globals: true,
    include: ['src/**/*.spec.ts', 'src/**/*.test.ts'],
    exclude: ['node_modules', 'dist'],
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },
})
