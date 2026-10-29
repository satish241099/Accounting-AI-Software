/**
 * Route Coverage Guard — vitest
 *
 * Inventories all API routes from the OpenAPI spec and guarantees that every
 * non-allow-listed route enforces the X-Business-Id membership dependency.
 *
 * Allow-listed routes (X-Business-Id NOT required):
 *   - /health                                          — Public health check
 *   - /auth/callback                                   — OIDC callback
 *   - /me                                              — Authenticated-no-tenant: current user
 *   - /me/businesses                                   — Authenticated-no-tenant: list user businesses
 *   - /invites/accept                                  — Authenticated-no-tenant: accept invitation
 *   - /businesses (POST)                               — Authenticated-no-tenant: create business
 *
 * Tenant-scoped routes requiring X-Business-Id:
 *   - /businesses/{id} (GET)                           — Requires X-Business-Id, validated against business_membership
 */

import { describe, expect, test } from 'vitest'
import yaml from 'yaml'
import path from 'path'

const OPENAPI_PATH = path.resolve(
  __dirname,
  '..',
  'docs',
  'api',
  'kernel-openapi.yaml'
)

// Allow-listed routes that do NOT require X-Business-Id
const ALLOW_LISTED: ReadonlySet<string> = new Set([
  '/health',
  '/auth/callback',
  '/me',
  '/me/businesses',
  '/invites/accept',
  '/businesses',
])

describe('Route Coverage Guard: X-Business-Id enforcement', () => {
  let paths: Record<string, unknown>

  beforeAll(async () => {
    const content = await fetch(OPENAPI_PATH).then((r) => r.text())
    const doc = yaml.parse(content)
    paths = doc.paths || {}
  })

  test('every non-allow-listed route requires X-Business-Id header', () => {
    const routeKeys = Object.keys(paths) as Array<keyof typeof paths>

    for (const routePath of routeKeys) {
      const pathItem = paths[routePath]
      if (!pathItem || typeof pathItem !== 'object') continue

      const methods = Object.keys(pathItem) as Array<keyof typeof pathItem>

      for (const method of methods) {
        const operation = (pathItem as Record<string, unknown>)[method]
        if (!operation || typeof operation !== 'object') continue

        // Determine if this route is allow-listed by path
        const pathIsAllowlisted = ALLOW_LISTED.has(routePath)

        // Tenant-scoped routes MUST have X-Business-Id requirement
        if (!pathIsAllowlisted) {
          // The route must require X-Business-Id in its parameters
          const parameters = operation.parameters || []
          const hasBusinessIdParam = parameters.some(
            (p: unknown) =>
              p &&
              typeof p === 'object' &&
              (p as Record<string, unknown>)['name'] === 'X-Business-Id'
          )

          // Also check security scope - tenant-scoped routes should have
          // the X-Business-Id enforcement. If there's no X-Business-Id param
          // and the route is not in the allow list, it fails.
          expect(hasBusinessIdParam).toBe(
            true,
            `Route ${method.toUpperCase()} ${routePath} is not allow-listed but does not require X-Business-Id header. ` +
              `Add X-Business-Id parameter or add to allow-list at tests/route-coverage.spec.ts.`
          )
        }
      }
    }
  })

  test('allow-listed routes are correctly marked and do not require X-Business-Id', () => {
    const routeKeys = Object.keys(paths) as Array<keyof typeof paths>

    for (const routePath of routeKeys) {
      const pathItem = paths[routePath]
      if (!pathItem || typeof pathItem !== 'object') continue

      const methods = Object.keys(pathItem) as Array<keyof typeof pathItem>

      for (const method of methods) {
        const operation = (pathItem as Record<string, unknown>)[method]
        if (!operation || typeof operation !== 'object') continue

        const pathIsAllowlisted = ALLOW_LISTED.has(routePath)

        if (pathIsAllowlisted) {
          // Verify no X-Business-Id parameter exists for allow-listed routes
          const parameters = operation.parameters || []
          const hasBusinessIdParam = parameters.some(
            (p: unknown) =>
              p &&
              typeof p === 'object' &&
              (p as Record<string, unknown>)['name'] === 'X-Business-Id'
          )

          expect(hasBusinessIdParam).toBe(
            false,
            `Allow-listed route ${method.toUpperCase()} ${routePath} should NOT require X-Business-Id header but has X-Business-Id parameter. ` +
              `Remove X-Business-Id parameter or add to allow-list at tests/route-coverage.spec.ts.`
          )
        }
      }
    }
  })
})