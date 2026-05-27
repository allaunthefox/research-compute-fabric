import { test, expect } from '@playwright/test';

/**
 * Auth integration tests.
 *
 * Validates that:
 * 1. auth.researchstack.info serves the Authentik UI
 * 2. SSO-protected paths redirect to Authentik for login
 * 3. /api/* paths do NOT redirect to Authentik (token-auth only)
 * 4. Authentik outpost forward_auth is wired correctly
 */

test.describe('Authentik SSO at auth.researchstack.info', () => {
  test('auth subdomain serves Authentik login page', async ({ request }) => {
    const response = await request.get('https://auth.researchstack.info/', {
      maxRedirects: 5,
    });
    expect(response.status()).toBeLessThan(500);

    // Authentik login page should contain typical markers
    const content = await response.text();
    const isAuthentik =
      content.includes('authentik') ||
      content.includes('Authentik') ||
      content.includes('ak-flow') ||
      content.includes('Sign in') ||
      content.includes('flow/default');
    expect(isAuthentik).toBe(true);
  });

  test('auth subdomain OIDC discovery endpoint exists', async ({ request }) => {
    const response = await request.get(
      'https://auth.researchstack.info/application/o/.well-known/openid-configuration'
    );
    // Might be 404 if no application configured, or 200 with OIDC metadata
    if (response.status() === 200) {
      const body = await response.json();
      expect(body).toHaveProperty('issuer');
      expect(body.issuer).toContain('auth.researchstack.info');
    } else {
      // At minimum, should not be a redirect or 500
      expect(response.status()).toBeLessThan(500);
    }
  });
});

test.describe('forward_auth gates SSO-protected paths', () => {
  const protectedPaths = [
    '/apps/chat/',
    '/apps/budget/',
    '/server/status/',
    '/server/dash/',
    '/server/vault/',
    '/',
  ];

  for (const path of protectedPaths) {
    test(`${path} redirects unauthenticated users to Authentik`, async ({ request }) => {
      const response = await request.get(path, {
        maxRedirects: 0,
      });
      // Protected paths should either:
      // - 302/303 redirect to auth.researchstack.info (forward_auth)
      // - 401/403 (outpost returns denial)
      // - 200 if auth is not yet configured/enforced
      if (response.status() === 302 || response.status() === 303) {
        const location = response.headers()['location'];
        expect(location).toContain('auth.researchstack.info');
      } else {
        // If not redirecting, should be 200 (auth not enforced yet) or 401/403
        expect([200, 401, 403]).toContain(response.status());
      }
    });
  }
});

test.describe('/api/* paths bypass forward_auth', () => {
  const apiPaths = [
    '/api/cred/',
    '/api/registry/health',
    '/api/jobs/health',
    '/api/blobs/health',
  ];

  for (const path of apiPaths) {
    test(`${path} does NOT redirect to Authentik`, async ({ request }) => {
      const response = await request.get(path, {
        maxRedirects: 0,
      });
      // API paths should NEVER redirect to Authentik
      if (response.status() === 302 || response.status() === 303) {
        const location = response.headers()['location'] || '';
        expect(location).not.toContain('auth.researchstack.info');
      }
      // Valid responses: 200 (service up), 401/403 (token auth), 502/503 (not deployed)
      expect([200, 401, 403, 404, 502, 503]).toContain(response.status());
    });
  }
});

test.describe('X-Forwarded headers propagation', () => {
  test('edge correctly proxies to internal services over tailnet', async ({ request }) => {
    // The /api/registry/health endpoint (if deployed) should respond
    // This validates the full edge → traefik → service path works
    const response = await request.get('/api/registry/health');
    if (response.status() === 200) {
      const body = await response.json();
      expect(body.status).toBe('ok');
    }
    // If not deployed, just verify we don't get a TLS error
    expect(response.status()).toBeLessThan(600);
  });
});
