import express from "express";
import { createHash, timingSafeEqual } from "crypto";

/**
 * PRIVATE Wolfram Alpha Connector Surface
 *
 * Bounded computational oracle for Research Stack.
 *
 * Authority boundary:
 * - Wolfram Alpha = computational check / external calculation surface
 * - Graph.lean = canonical proof / graph authority
 * - ENE = provenance / archive authority
 * - FAMM = route-memory outcome layer after authority gating
 *
 * SECURITY RULES:
 * - Never expose this router directly to the public internet.
 * - WOLFRAM_CONNECTOR_TOKEN is mandatory and must be >=32 chars.
 * - WOLFRAM_APP_ID is mandatory and must never be committed.
 * - Mount only behind localhost, VPN, tailnet, SSH tunnel, or private reverse proxy.
 * - Do not log queries if they contain private project material.
 *
 * Mount from server.js:
 *   import wolframRouter from "./connectors/wolfram/wolfram_alpha_connector_router.js";
 *   app.use("/wolfram", wolframRouter);
 */

const router = express.Router();
const WOLFRAM_BASE = "https://api.wolframalpha.com/v2";
const MAX_QUERY_CHARS = Number(process.env.WOLFRAM_MAX_QUERY_CHARS || 1600);
const DEFAULT_TIMEOUT_MS = Number(process.env.WOLFRAM_TIMEOUT_MS || 15000);

function requireConnectorToken(req, res, next) {
  const token = process.env.WOLFRAM_CONNECTOR_TOKEN;
  if (!token || token.length < 32) {
    return res.status(503).json({
      ok: false,
      error: "Wolfram connector disabled: set WOLFRAM_CONNECTOR_TOKEN to a private random value of at least 32 characters",
    });
  }

  const header = req.headers.authorization || "";
  const presented = header.startsWith("Bearer ") ? header.slice("Bearer ".length) : "";
  const a = Buffer.from(presented);
  const b = Buffer.from(token);

  if (a.length !== b.length || !timingSafeEqual(a, b)) {
    return res.status(401).json({ ok: false, error: "unauthorized" });
  }
  next();
}

function requireAppId() {
  const appId = process.env.WOLFRAM_APP_ID;
  if (!appId) throw new Error("WOLFRAM_APP_ID is required");
  return appId;
}

function assertQuery(query) {
  const q = String(query || "").trim();
  if (!q) throw new Error("query is required");
  if (q.length > MAX_QUERY_CHARS) throw new Error(`query exceeds WOLFRAM_MAX_QUERY_CHARS=${MAX_QUERY_CHARS}`);
  return q;
}

function receiptFor(payload) {
  return createHash("sha256").update(JSON.stringify(payload)).digest("hex");
}

async function fetchWithTimeout(url, timeoutMs = DEFAULT_TIMEOUT_MS) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(url, { signal: controller.signal });
    const text = await response.text();
    if (!response.ok) throw new Error(`Wolfram request failed: HTTP ${response.status} ${text.slice(0, 200)}`);
    return text;
  } finally {
    clearTimeout(timer);
  }
}

function sanitizePods(wolframJson) {
  const queryresult = wolframJson?.queryresult || {};
  const pods = Array.isArray(queryresult.pods) ? queryresult.pods : [];
  return pods.map((pod) => ({
    id: pod.id,
    title: pod.title,
    scanner: pod.scanner,
    primary: Boolean(pod.primary),
    position: pod.position,
    subpods: Array.isArray(pod.subpods)
      ? pod.subpods.map((s) => ({
          title: s.title || "",
          plaintext: s.plaintext || "",
        }))
      : [],
  }));
}

router.use(express.json({ limit: "2mb" }));
router.use(requireConnectorToken);

router.get("/health", (_req, res) => {
  res.json({
    ok: true,
    service: "PRIVATE Wolfram Alpha connector",
    appIdConfigured: Boolean(process.env.WOLFRAM_APP_ID),
    tokenRequired: true,
    maxQueryChars: MAX_QUERY_CHARS,
    timeoutMs: DEFAULT_TIMEOUT_MS,
    exposurePolicy: "private-only: localhost/VPN/tailnet/SSH tunnel/private proxy; never public internet",
    authorityScope: "computational_check_only_not_proof_authority",
    timestamp: new Date().toISOString(),
  });
});

router.post("/short", async (req, res) => {
  try {
    const appId = requireAppId();
    const query = assertQuery(req.body?.query);
    const url = new URL(`${WOLFRAM_BASE}/result`);
    url.searchParams.set("appid", appId);
    url.searchParams.set("i", query);
    url.searchParams.set("units", String(req.body?.units || "metric"));

    const plaintext = await fetchWithTimeout(url);
    const receipt = receiptFor({ surface: "wolfram-short", query, plaintext });
    res.json({
      ok: true,
      surface: "wolfram-short",
      query,
      plaintext,
      receipt,
      authorityScope: "computational_check_only",
      outcome: "hold",
    });
  } catch (error) {
    res.status(400).json({ ok: false, error: error.message });
  }
});

router.post("/query", async (req, res) => {
  try {
    const appId = requireAppId();
    const query = assertQuery(req.body?.query);
    const url = new URL(`${WOLFRAM_BASE}/query`);
    url.searchParams.set("appid", appId);
    url.searchParams.set("input", query);
    url.searchParams.set("output", "json");
    url.searchParams.set("format", "plaintext");
    url.searchParams.set("units", String(req.body?.units || "metric"));
    url.searchParams.set("podstate", String(req.body?.podstate || ""));

    if (Array.isArray(req.body?.includePodIds)) {
      for (const podId of req.body.includePodIds) url.searchParams.append("includepodid", String(podId));
    }
    if (Array.isArray(req.body?.excludePodIds)) {
      for (const podId of req.body.excludePodIds) url.searchParams.append("excludepodid", String(podId));
    }

    const raw = await fetchWithTimeout(url);
    const parsed = JSON.parse(raw);
    const pods = sanitizePods(parsed);
    const receipt = receiptFor({ surface: "wolfram-query", query, pods });

    res.json({
      ok: true,
      surface: "wolfram-query",
      query,
      success: Boolean(parsed?.queryresult?.success),
      error: Boolean(parsed?.queryresult?.error),
      numpods: parsed?.queryresult?.numpods || pods.length,
      pods,
      receipt,
      authorityScope: "computational_check_only",
      outcome: "hold",
    });
  } catch (error) {
    res.status(400).json({ ok: false, error: error.message });
  }
});

router.post("/validate-equation", async (req, res) => {
  try {
    const appId = requireAppId();
    const equation = assertQuery(req.body?.equation);
    const variable = String(req.body?.variable || "").trim();
    const domain = String(req.body?.domain || "general");
    const query = variable ? `solve ${equation} for ${variable}` : `simplify ${equation}`;

    const url = new URL(`${WOLFRAM_BASE}/query`);
    url.searchParams.set("appid", appId);
    url.searchParams.set("input", query);
    url.searchParams.set("output", "json");
    url.searchParams.set("format", "plaintext");

    const raw = await fetchWithTimeout(url);
    const parsed = JSON.parse(raw);
    const pods = sanitizePods(parsed);
    const primaryPods = pods.filter((p) => p.primary || /result|solution|alternate form|simplification/i.test(p.title || ""));
    const receipt = receiptFor({ surface: "wolfram-validate-equation", equation, variable, domain, primaryPods });

    res.json({
      ok: true,
      surface: "wolfram-validate-equation",
      equation,
      variable: variable || null,
      domain,
      wolframQuery: query,
      success: Boolean(parsed?.queryresult?.success),
      primaryPods,
      pods,
      receipt,
      authorityScope: "computational_check_only_not_proof",
      outcome: "hold",
      nextGate: "Graph.lean or independent derivation required before basin promotion",
    });
  } catch (error) {
    res.status(400).json({ ok: false, error: error.message });
  }
});

router.post("/numeric-probe", async (req, res) => {
  try {
    const appId = requireAppId();
    const expression = assertQuery(req.body?.expression);
    const assumptions = String(req.body?.assumptions || "").trim();
    const query = assumptions ? `N[${expression}] assuming ${assumptions}` : `N[${expression}]`;

    const url = new URL(`${WOLFRAM_BASE}/query`);
    url.searchParams.set("appid", appId);
    url.searchParams.set("input", query);
    url.searchParams.set("output", "json");
    url.searchParams.set("format", "plaintext");

    const raw = await fetchWithTimeout(url);
    const parsed = JSON.parse(raw);
    const pods = sanitizePods(parsed);
    const receipt = receiptFor({ surface: "wolfram-numeric-probe", expression, assumptions, pods });

    res.json({
      ok: true,
      surface: "wolfram-numeric-probe",
      expression,
      assumptions: assumptions || null,
      wolframQuery: query,
      success: Boolean(parsed?.queryresult?.success),
      pods,
      receipt,
      authorityScope: "numeric_probe_only",
      outcome: "hold",
    });
  } catch (error) {
    res.status(400).json({ ok: false, error: error.message });
  }
});

export default router;
