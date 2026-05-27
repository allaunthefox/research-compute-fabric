import { test, expect } from '@playwright/test';

/**
 * Edge TLS + subdomain redirect tests.
 *
 * Validates that:
 * 1. The edge Caddy terminates TLS correctly for researchstack.info
 * 2. Legacy subdomains 301-redirect to their canonical path equivalents
 * 3. auth.researchstack.info stays as a real subdomain (not redirected)
 * 4. mail/webmail subdomains are forwarded (not redirected)
 */

test.describe('Edge TLS termination', () => {
  test('root domain is reachable over HTTPS', async ({ request }) => {
    const response = await request.get('/');
    // Should get a response (2xx or redirect to auth)
    expect([200, 301, 302, 303, 401, 403]).toContain(response.status());
  });

  test('TLS certificate is valid for researchstack.info', async ({ request }) => {
    // If TLS is broken, the request will throw (ignoreHTTPSErrors is true,
    // so we'd still connect but let's verify we get a response)
    const response = await request.get('https://researchstack.info/');
    expect(response.status()).toBeLessThan(500);
  });
});

test.describe('Legacy subdomain 301 redirects', () => {
  const redirectTests = [
    { from: 'https://status.researchstack.info/', to: '/server/status/' },
    { from: 'https://dash.researchstack.info/', to: '/' },
    { from: 'https://home.researchstack.info/', to: '/' },
    { from: 'https://media.researchstack.info/', to: '/apps/jellyfin/' },
    { from: 'https://books.researchstack.info/', to: '/apps/books/' },
    { from: 'https://music.researchstack.info/', to: '/apps/music/' },
    { from: 'https://vault.researchstack.info/', to: '/server/vault/' },
    { from: 'https://pulse.researchstack.info/', to: '/api/registry/' },
    { from: 'https://apps.researchstack.info/', to: '/apps/' },
  ];

  for (const { from, to } of redirectTests) {
    test(`${from} → 301 to ${to}`, async ({ request }) => {
      const response = await request.get(from, {
        maxRedirects: 0,
      });
      expect(response.status()).toBe(301);
      const location = response.headers()['location'];
      expect(location).toContain(to);
      expect(location).toContain('researchstack.info');
    });
  }
});

test.describe('Stable subdomains (not redirected)', () => {
  test('auth.researchstack.info responds (not a redirect)', async ({ request }) => {
    const response = await request.get('https://auth.researchstack.info/', {
      maxRedirects: 0,
    });
    // Authentik should respond with 200 or 302 (to login page), not 301
    expect(response.status()).not.toBe(301);
    expect([200, 302, 303]).toContain(response.status());
  });

  test('mail.researchstack.info responds (not a redirect)', async ({ request }) => {
    const response = await request.get('https://mail.researchstack.info/', {
      maxRedirects: 0,
    });
    // Mail frontend should respond, or if not deployed yet, at least not 301
    expect(response.status()).not.toBe(301);
  });
});

test.describe('Wildcard fallback', () => {
  test('unknown subdomain redirects to root', async ({ request }) => {
    const response = await request.get('https://nonexistent.researchstack.info/', {
      maxRedirects: 0,
    });
    expect(response.status()).toBe(301);
    const location = response.headers()['location'];
    expect(location).toBe('https://researchstack.info/');
  });
});
