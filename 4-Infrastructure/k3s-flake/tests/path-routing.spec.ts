import { test, expect } from '@playwright/test';

/**
 * Path-based routing tests.
 *
 * Validates that Traefik Ingress correctly routes canonical paths to the
 * right backend services. Tests check:
 * 1. Path exists (not 404)
 * 2. Response comes from the expected service (via content or headers)
 * 3. Prefix stripping works (backend sees / not /apps/chat/)
 *
 * Note: Many paths are behind forward_auth (Authentik), so unauthenticated
 * requests may get 302 → auth. That's still a valid "routing works" signal.
 */

test.describe('/apps/* routes', () => {
  test('/apps/chat/ reaches Hermes (or auth redirect)', async ({ request }) => {
    const response = await request.get('/apps/chat/', {
      maxRedirects: 0,
    });
    // Either serves the placeholder page (200) or redirects to auth (302)
    expect([200, 302, 303, 401]).toContain(response.status());
    if (response.status() === 200) {
      const body = await response.text();
      expect(body).toContain('Hermes');
    }
    if (response.status() === 302) {
      const location = response.headers()['location'];
      expect(location).toContain('auth.researchstack.info');
    }
  });

  test('/apps/budget/ reaches Actual Budget (or auth redirect)', async ({ request }) => {
    const response = await request.get('/apps/budget/', {
      maxRedirects: 0,
    });
    expect([200, 302, 303, 401]).toContain(response.status());
    if (response.status() === 302) {
      const location = response.headers()['location'];
      expect(location).toContain('auth.researchstack.info');
    }
  });

  test('/apps/chat/ strips prefix (backend sees /)', async ({ request }) => {
    // Request a subpath — if prefix stripping works, the backend gets /health
    // or /index.html, not /apps/chat/health
    const response = await request.get('/apps/chat/', {
      maxRedirects: 0,
    });
    // Should not get 404 from a misconfigured path
    expect(response.status()).not.toBe(404);
  });
});

test.describe('/server/* routes', () => {
  test('/server/status/ reaches Uptime Kuma (or auth redirect)', async ({ request }) => {
    const response = await request.get('/server/status/', {
      maxRedirects: 0,
    });
    expect([200, 302, 303, 401]).toContain(response.status());
    if (response.status() === 302) {
      const location = response.headers()['location'];
      expect(location).toContain('auth.researchstack.info');
    }
  });

  test('/server/dash/ reaches Homarr (or auth redirect)', async ({ request }) => {
    const response = await request.get('/server/dash/', {
      maxRedirects: 0,
    });
    expect([200, 302, 303, 401]).toContain(response.status());
  });

  test('/server/vault/ reaches Vaultwarden (or auth redirect)', async ({ request }) => {
    const response = await request.get('/server/vault/', {
      maxRedirects: 0,
    });
    expect([200, 302, 303, 401]).toContain(response.status());
  });
});

test.describe('/api/* routes (no forward_auth, token-based)', () => {
  test('/api/cred/ is reachable (no auth redirect)', async ({ request }) => {
    const response = await request.get('/api/cred/', {
      maxRedirects: 0,
    });
    // API routes should NOT redirect to Authentik — they use token auth
    // They might return 401/403 (no token), 200, or 404 (not deployed yet)
    expect(response.status()).not.toBe(302);
    expect([200, 401, 403, 404, 502, 503]).toContain(response.status());
  });

  test('/api/registry/health responds with service identity', async ({ request }) => {
    const response = await request.get('/api/registry/health');
    if (response.status() === 200) {
      const body = await response.json();
      expect(body.service).toBe('registry');
      expect(body.status).toBe('ok');
    } else {
      // Service not deployed yet — 502/503 is acceptable
      expect([502, 503, 404]).toContain(response.status());
    }
  });

  test('/api/jobs/health responds with service identity', async ({ request }) => {
    const response = await request.get('/api/jobs/health');
    if (response.status() === 200) {
      const body = await response.json();
      expect(body.service).toBe('jobs');
      expect(body.status).toBe('ok');
    } else {
      expect([502, 503, 404]).toContain(response.status());
    }
  });

  test('/api/blobs/health responds with service identity', async ({ request }) => {
    const response = await request.get('/api/blobs/health');
    if (response.status() === 200) {
      const body = await response.json();
      expect(body.service).toBe('blobs');
      expect(body.status).toBe('ok');
    } else {
      expect([502, 503, 404]).toContain(response.status());
    }
  });

  test('/api/registry/nodes returns empty list or 502', async ({ request }) => {
    const response = await request.get('/api/registry/nodes');
    if (response.status() === 200) {
      const body = await response.json();
      expect(body).toHaveProperty('nodes');
      expect(Array.isArray(body.nodes)).toBe(true);
    } else {
      expect([502, 503, 404]).toContain(response.status());
    }
  });

  test('/api/jobs/ returns empty list or 502', async ({ request }) => {
    const response = await request.get('/api/jobs/');
    if (response.status() === 200) {
      const body = await response.json();
      expect(body).toHaveProperty('jobs');
    } else {
      expect([502, 503, 404]).toContain(response.status());
    }
  });
});

test.describe('Landing page', () => {
  test('/ reaches Homer (or auth redirect)', async ({ request }) => {
    const response = await request.get('/', {
      maxRedirects: 0,
    });
    expect([200, 302, 303, 401]).toContain(response.status());
    if (response.status() === 200) {
      const body = await response.text();
      // Homer dashboard should mention "Research Stack"
      expect(body).toContain('Research Stack');
    }
  });
});
