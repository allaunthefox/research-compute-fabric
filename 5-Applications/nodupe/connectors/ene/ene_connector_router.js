import express from "express";
import Database from "better-sqlite3";
import { join } from "path";
import { createHash, timingSafeEqual } from "crypto";
import { z } from "zod";
import { pkgIngest } from "../../ene.js";
import { hybridSearch } from "../../ene_search.js";

/**
 * PRIVATE ENE Connector Router
 *
 * Exposes ENE as a bounded local/private HTTP connector surface.
 * Authority: ENE is provenance/archive authority only.
 *
 * SECURITY RULES:
 * - Never expose this router directly to the public internet.
 * - ENE_CONNECTOR_TOKEN is mandatory.
 * - Mount only behind localhost, VPN, tailnet, SSH tunnel, or a private reverse proxy.
 * - Do not log request bodies or secrets.
 *
 * Mount from server.js:
 *   import eneConnectorRouter from "./connectors/ene/ene_connector_router.js";
 *   app.use("/ene", eneConnectorRouter);
 */

const router = express.Router();
const dbPath = join(process.cwd(), "data", "substrate_index.db");

function requireConnectorToken(req, res, next) {
  const token = process.env.ENE_CONNECTOR_TOKEN;
  if (!token || token.length < 32) {
    return res.status(503).json({
      ok: false,
      error: "ENE connector disabled: set ENE_CONNECTOR_TOKEN to a private random value of at least 32 characters",
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

router.use(express.json({ limit: "10mb" }));
router.use(requireConnectorToken);

function openDb(readonly = false) {
  return new Database(dbPath, { readonly });
}

function safeJsonParse(value, fallback) {
  if (value == null || value === "") return fallback;
  if (typeof value !== "string") return value;
  try { return JSON.parse(value); } catch { return fallback; }
}

function rowToPackage(row) {
  if (!row) return null;
  return {
    pkg: row.pkg,
    version: row.version,
    tier: row.tier,
    domain: row.domain,
    archetype: row.archetype,
    description: row.description,
    tags: safeJsonParse(row.tags, []),
    source: row.source,
    sessionId: row.session_id,
    notionId: row.notion_id,
    sha256: row.sha256,
    indexedUtc: row.indexed_utc,
    modelStatus: row.model_status,
    qualityStatus: row.quality_status,
    foamScore: row.foam_score,
    verificationBasis: row.verification_basis,
    conceptVector: safeJsonParse(row.concept_vector, []),
    conceptAnchor: safeJsonParse(row.concept_anchor, {}),
    auditRationale: safeJsonParse(row.audit_rationale, row.audit_rationale),
  };
}

function ensureConnectorTables(db) {
  db.exec(`
    CREATE TABLE IF NOT EXISTS route_memory (
      route_signature TEXT PRIMARY KEY,
      artifact_id TEXT,
      modules_touched_json TEXT NOT NULL DEFAULT '[]',
      transform_chain_json TEXT NOT NULL DEFAULT '[]',
      cost REAL NOT NULL,
      torsion REAL NOT NULL,
      coherence REAL NOT NULL,
      conflicts_json TEXT NOT NULL,
      outcome TEXT NOT NULL,
      receipt_hash TEXT,
      created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS famm_field (
      route_signature TEXT PRIMARY KEY,
      basin_strength REAL NOT NULL DEFAULT 0,
      scar_strength REAL NOT NULL DEFAULT 0,
      unresolved_torsion REAL NOT NULL DEFAULT 0,
      last_updated TEXT NOT NULL
    );
  `);
}

const IngestSchema = z.object({
  title: z.string().min(1),
  body: z.string().default(""),
  kind: z.string().default("archive_note"),
  tags: z.array(z.string()).default([]),
  sessionId: z.string().nullable().optional(),
  notionId: z.string().nullable().optional(),
  metric: z.object({ cost: z.union([z.number(), z.string()]).optional() }).passthrough().optional(),
  witness: z.object({ trace_hash: z.string().optional() }).passthrough().optional(),
  sigma: z.any().optional(),
});

const SyncSchema = z.object({
  pkg: z.string().min(1),
  version: z.string().min(1),
  domain: z.string().optional(),
  tier: z.string().optional(),
  description: z.string().optional(),
  tags: z.union([z.string(), z.array(z.string())]).optional(),
  sha256: z.string().optional().nullable(),
  quality_status: z.string().optional().nullable(),
  audit_rationale: z.any().optional().nullable(),
  concept_vector: z.any().optional(),
  concept_anchor: z.any().optional(),
});

const FammRouteSchema = z.object({
  routeSignature: z.string().min(1),
  artifactId: z.string().nullable().optional(),
  cost: z.number().default(0),
  torsion: z.number().default(0),
  coherence: z.number().default(1),
  conflicts: z.array(z.string()).default([]),
  outcome: z.enum(["unresolved", "basin", "scar", "hold", "pass", "fail", "unsafe"]).default("unresolved"),
  receiptHash: z.string().nullable().optional(),
});

router.get("/health", (_req, res) => {
  try {
    const db = openDb(true);
    const packageCount = db.prepare("SELECT count(*) AS c FROM packages").get().c;
    let routeCount = 0;
    let fammCount = 0;
    try { routeCount = db.prepare("SELECT count(*) AS c FROM route_memory").get().c; } catch {}
    try { fammCount = db.prepare("SELECT count(*) AS c FROM famm_field").get().c; } catch {}
    db.close();
    res.json({
      ok: true,
      service: "PRIVATE ENE connector",
      dbPath,
      packageCount,
      routeCount,
      fammCount,
      tokenRequired: true,
      exposurePolicy: "private-only: localhost/VPN/tailnet/SSH tunnel/private proxy; never public internet",
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    res.status(500).json({ ok: false, error: error.message, dbPath });
  }
});

router.post("/ingest", (req, res) => {
  try {
    const input = IngestSchema.parse(req.body);
    const result = pkgIngest(input);
    res.json({ ok: true, ...result });
  } catch (error) {
    res.status(400).json({ ok: false, error: error.message });
  }
});

router.post("/search", async (req, res) => {
  try {
    const query = String(req.body?.query || "").trim();
    const limit = Math.max(1, Math.min(Number(req.body?.limit || 10), 50));
    if (!query) return res.status(400).json({ ok: false, error: "query is required" });
    const results = await hybridSearch(query, limit);
    res.json({ ok: true, query, results });
  } catch (error) {
    res.status(500).json({ ok: false, error: error.message });
  }
});

router.get("/package", (req, res) => {
  try {
    const pkg = String(req.query.pkg || "");
    const version = String(req.query.version || "");
    if (!pkg) return res.status(400).json({ ok: false, error: "pkg is required" });
    const db = openDb(true);
    const row = version
      ? db.prepare("SELECT * FROM packages WHERE pkg = ? AND version = ?").get(pkg, version)
      : db.prepare("SELECT * FROM packages WHERE pkg = ? ORDER BY indexed_utc DESC LIMIT 1").get(pkg);
    db.close();
    if (!row) return res.status(404).json({ ok: false, error: "package not found" });
    res.json({ ok: true, package: rowToPackage(row) });
  } catch (error) {
    res.status(500).json({ ok: false, error: error.message });
  }
});

router.post("/sync", (req, res) => {
  try {
    const record = SyncSchema.parse(req.body);
    const db = openDb(false);
    const insert = db.prepare(`
      INSERT OR IGNORE INTO packages (
        pkg, version, domain, tier, description, tags, source,
        sha256, quality_status, audit_rationale, indexed_utc, concept_vector, concept_anchor
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `);
    const result = insert.run(
      record.pkg,
      record.version,
      record.domain || "SYNCED",
      record.tier || "RESEARCH",
      record.description || "",
      typeof record.tags === "string" ? record.tags : JSON.stringify(record.tags || []),
      "ENE_CONNECTOR_SYNC",
      record.sha256 || null,
      record.quality_status || null,
      typeof record.audit_rationale === "string" ? record.audit_rationale : JSON.stringify(record.audit_rationale || null),
      new Date().toISOString(),
      typeof record.concept_vector === "string" ? record.concept_vector : JSON.stringify(record.concept_vector || []),
      typeof record.concept_anchor === "string" ? record.concept_anchor : JSON.stringify(record.concept_anchor || {})
    );
    db.close();
    res.json({ ok: true, inserted: result.changes > 0, pkg: record.pkg, version: record.version });
  } catch (error) {
    res.status(400).json({ ok: false, error: error.message });
  }
});

router.post("/famm/route", (req, res) => {
  try {
    const route = FammRouteSchema.parse(req.body);
    const db = openDb(false);
    ensureConnectorTables(db);
    db.prepare(`
      INSERT OR REPLACE INTO route_memory
      (route_signature, artifact_id, cost, torsion, coherence, conflicts_json, outcome, receipt_hash, created_at)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    `).run(route.routeSignature, route.artifactId || null, route.cost, route.torsion, route.coherence, JSON.stringify(route.conflicts), route.outcome, route.receiptHash || null, new Date().toISOString());

    const current = db.prepare("SELECT * FROM famm_field WHERE route_signature = ?").get(route.routeSignature);
    let basin = current?.basin_strength || 0;
    let scar = current?.scar_strength || 0;
    let unresolved = current?.unresolved_torsion || 0;
    if (route.outcome === "basin" || route.outcome === "pass") basin += Math.max(1, 8 - route.torsion);
    else if (["scar", "fail", "unsafe"].includes(route.outcome)) scar += Math.max(1, route.torsion);
    else unresolved += Math.max(1, route.torsion);

    db.prepare(`
      INSERT OR REPLACE INTO famm_field
      (route_signature, basin_strength, scar_strength, unresolved_torsion, last_updated)
      VALUES (?, ?, ?, ?, ?)
    `).run(route.routeSignature, basin, scar, unresolved, new Date().toISOString());
    db.close();
    res.json({ ok: true, route, famm: { routeSignature: route.routeSignature, basin, scar, unresolved } });
  } catch (error) {
    res.status(400).json({ ok: false, error: error.message });
  }
});

router.post("/export", (req, res) => {
  try {
    const limit = Math.max(1, Math.min(Number(req.body?.limit || 100), 1000));
    const db = openDb(true);
    const rows = db.prepare("SELECT * FROM packages ORDER BY indexed_utc DESC LIMIT ?").all(limit);
    db.close();
    const packages = rows.map(rowToPackage);
    const receipt = createHash("sha256").update(JSON.stringify(packages)).digest("hex");
    res.json({ ok: true, count: packages.length, receipt, packages });
  } catch (error) {
    res.status(500).json({ ok: false, error: error.message });
  }
});

export default router;
