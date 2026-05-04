import express from "express";
import { timingSafeEqual, createHash } from "crypto";
import { mkdir, readFile, readdir, stat, writeFile } from "fs/promises";
import { join, resolve, relative, extname, dirname } from "path";
import neo4j from "neo4j-driver";

/**
 * PRIVATE Topological Engine Connector
 *
 * Obsidian + Neo4j bridge for Research Stack.
 *
 * Authority boundary:
 * - Obsidian = local human-readable vault/workbench mirror
 * - Neo4j = private graph traversal/query engine
 * - Graph.lean = canonical graph authority
 * - ENE = provenance/archive authority
 *
 * SECURITY RULES:
 * - Never expose this router directly to the public internet.
 * - TOPOLOGICAL_ENGINE_TOKEN is mandatory and must be >=32 chars.
 * - Mount only behind localhost, VPN, tailnet, SSH tunnel, or private reverse proxy.
 * - Keep Neo4j Bolt/Browser private.
 * - Do not log secrets, request bodies, ENE keys, or vault contents.
 *
 * Mount from server.js:
 *   import topologicalEngineRouter from "./connectors/topological-engine/neo4j_obsidian_connector_router.js";
 *   app.use("/topology", topologicalEngineRouter);
 */

const router = express.Router();

const VAULT_ROOT = resolve(process.env.OBSIDIAN_VAULT_PATH || join(process.cwd(), "obsidian-vault"));
const MAX_READ_BYTES = Number(process.env.OBSIDIAN_MAX_READ_BYTES || 1_000_000);

function requireConnectorToken(req, res, next) {
  const token = process.env.TOPOLOGICAL_ENGINE_TOKEN;
  if (!token || token.length < 32) {
    return res.status(503).json({
      ok: false,
      error: "Topological Engine disabled: set TOPOLOGICAL_ENGINE_TOKEN to a private random value of at least 32 characters",
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

router.use(express.json({ limit: "5mb" }));
router.use(requireConnectorToken);

function vaultSafePath(notePath) {
  const clean = String(notePath || "").replace(/^\/+/, "");
  const full = resolve(VAULT_ROOT, clean);
  if (!full.startsWith(VAULT_ROOT)) throw new Error("path escapes vault root");
  return full;
}

function sha256(text) {
  return createHash("sha256").update(text).digest("hex");
}

function getDriver() {
  const uri = process.env.NEO4J_URI;
  const user = process.env.NEO4J_USER;
  const password = process.env.NEO4J_PASSWORD;
  if (!uri || !user || !password) throw new Error("NEO4J_URI, NEO4J_USER, and NEO4J_PASSWORD are required");
  return neo4j.driver(uri, neo4j.auth.basic(user, password));
}

function frontmatterFromProperties(properties = {}) {
  const lines = ["---"];
  for (const [key, value] of Object.entries(properties)) {
    const safeKey = String(key).replace(/[^A-Za-z0-9_\-]/g, "_");
    if (Array.isArray(value)) lines.push(`${safeKey}: ${JSON.stringify(value)}`);
    else if (value && typeof value === "object") lines.push(`${safeKey}: ${JSON.stringify(value)}`);
    else lines.push(`${safeKey}: ${JSON.stringify(value ?? "")}`);
  }
  lines.push("---", "");
  return lines.join("\n");
}

function extractWikiLinks(markdown) {
  const links = [];
  const re = /\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]/g;
  let match;
  while ((match = re.exec(markdown)) !== null) links.push(match[1].trim());
  return [...new Set(links)];
}

async function listMarkdownFiles(root, prefix = "") {
  const out = [];
  const dir = join(root, prefix);
  let entries = [];
  try { entries = await readdir(dir, { withFileTypes: true }); } catch { return out; }
  for (const entry of entries) {
    const rel = join(prefix, entry.name);
    if (entry.isDirectory()) out.push(...await listMarkdownFiles(root, rel));
    else if (entry.isFile() && extname(entry.name).toLowerCase() === ".md") out.push(rel);
  }
  return out;
}

router.get("/health", async (_req, res) => {
  let neo4jOk = false;
  let neo4jError = null;
  try {
    const driver = getDriver();
    const session = driver.session();
    await session.run("RETURN 1 AS ok");
    await session.close();
    await driver.close();
    neo4jOk = true;
  } catch (err) {
    neo4jError = err.message;
  }

  res.json({
    ok: true,
    service: "PRIVATE Obsidian + Neo4j Topological Engine",
    vaultRoot: VAULT_ROOT,
    neo4jOk,
    neo4jError,
    tokenRequired: true,
    exposurePolicy: "private-only: localhost/VPN/tailnet/SSH tunnel/private proxy; never public internet",
    timestamp: new Date().toISOString(),
  });
});

router.post("/obsidian/write-note", async (req, res) => {
  try {
    const title = String(req.body?.title || "Untitled");
    const folder = String(req.body?.folder || "Research Stack");
    const body = String(req.body?.body || "");
    const properties = {
      artifact_id: req.body?.artifact_id || `obsidian:${sha256(`${title}\n${body}`).slice(0, 16)}`,
      artifact_class: req.body?.artifact_class || "TextNote",
      authority_scope: req.body?.authority_scope || "local_workbench_mirror",
      source_uri: req.body?.source_uri || "",
      body_hash: sha256(body),
      route_signature: req.body?.route_signature || "",
      outcome: req.body?.outcome || "hold",
      torsion: req.body?.torsion ?? 0,
      coherence: req.body?.coherence ?? 1,
      source_of_truth: req.body?.source_of_truth || "Obsidian mirror; not canonical",
      quarantine_status: req.body?.quarantine_status || "none",
      created_utc: new Date().toISOString(),
      ...(req.body?.properties || {}),
    };
    const safeTitle = title.replace(/[\\/:*?"<>|]/g, "_");
    const noteRel = join(folder, `${safeTitle}.md`);
    const notePath = vaultSafePath(noteRel);
    await mkdir(dirname(notePath), { recursive: true });
    const content = `${frontmatterFromProperties(properties)}# ${title}\n\n${body}\n`;
    await writeFile(notePath, content, "utf8");
    res.json({ ok: true, notePath: noteRel, bodyHash: properties.body_hash, artifactId: properties.artifact_id });
  } catch (error) {
    res.status(400).json({ ok: false, error: error.message });
  }
});

router.get("/obsidian/read-note", async (req, res) => {
  try {
    const notePath = vaultSafePath(req.query.path);
    const s = await stat(notePath);
    if (s.size > MAX_READ_BYTES) return res.status(413).json({ ok: false, error: "note exceeds maximum read size" });
    const content = await readFile(notePath, "utf8");
    res.json({ ok: true, path: relative(VAULT_ROOT, notePath), content, bodyHash: sha256(content), links: extractWikiLinks(content) });
  } catch (error) {
    res.status(400).json({ ok: false, error: error.message });
  }
});

router.post("/obsidian/search", async (req, res) => {
  try {
    const query = String(req.body?.query || "").toLowerCase().trim();
    const limit = Math.max(1, Math.min(Number(req.body?.limit || 20), 100));
    if (!query) return res.status(400).json({ ok: false, error: "query is required" });
    const files = await listMarkdownFiles(VAULT_ROOT);
    const hits = [];
    for (const file of files) {
      if (hits.length >= limit) break;
      const full = vaultSafePath(file);
      const s = await stat(full);
      if (s.size > MAX_READ_BYTES) continue;
      const content = await readFile(full, "utf8");
      const hay = `${file}\n${content}`.toLowerCase();
      if (hay.includes(query)) hits.push({ path: file, title: file.replace(/\.md$/i, ""), bodyHash: sha256(content), links: extractWikiLinks(content) });
    }
    res.json({ ok: true, query, hits });
  } catch (error) {
    res.status(500).json({ ok: false, error: error.message });
  }
});

router.post("/neo4j/cypher", async (req, res) => {
  const driver = getDriver();
  const session = driver.session();
  try {
    const cypher = String(req.body?.cypher || "").trim();
    const params = req.body?.params || {};
    const readOnly = req.body?.readOnly !== false;
    if (!cypher) return res.status(400).json({ ok: false, error: "cypher is required" });
    if (readOnly && !/^\s*(MATCH|RETURN|WITH|CALL\s+db\.|CALL\s+apoc\.meta\.)/i.test(cypher)) {
      return res.status(403).json({ ok: false, error: "readOnly mode allows MATCH/RETURN/WITH/db metadata only" });
    }
    const result = await session.run(cypher, params);
    const records = result.records.map(r => Object.fromEntries(r.keys.map(k => [k, r.get(k)])));
    res.json({ ok: true, records, summary: { queryType: result.summary.queryType } });
  } catch (error) {
    res.status(400).json({ ok: false, error: error.message });
  } finally {
    await session.close();
    await driver.close();
  }
});

router.post("/neo4j/upsert-road", async (req, res) => {
  const driver = getDriver();
  const session = driver.session();
  try {
    const r = req.body || {};
    const required = ["sourceId", "sourceLabel", "targetId", "targetLabel", "relation"];
    for (const key of required) if (!r[key]) return res.status(400).json({ ok: false, error: `${key} is required` });
    const params = {
      sourceId: String(r.sourceId),
      sourceLabel: String(r.sourceLabel),
      targetId: String(r.targetId),
      targetLabel: String(r.targetLabel),
      relation: String(r.relation),
      authority_scope: r.authority_scope || "candidate",
      outcome: r.outcome || "hold",
      torsion: Number(r.torsion || 0),
      coherence: Number(r.coherence ?? 1),
      provenance_hash: r.provenance_hash || sha256(JSON.stringify(r)),
      source_of_truth: r.source_of_truth || "Neo4j candidate; Graph.lean audit required",
      quarantine_status: r.quarantine_status || "none",
      updated_utc: new Date().toISOString(),
    };
    const cypher = `
      MERGE (a:Node {id: $sourceId})
      SET a.label = $sourceLabel
      MERGE (b:Node {id: $targetId})
      SET b.label = $targetLabel
      MERGE (a)-[rel:ROAD {relation: $relation}]->(b)
      SET rel.authority_scope = $authority_scope,
          rel.outcome = $outcome,
          rel.torsion = $torsion,
          rel.coherence = $coherence,
          rel.provenance_hash = $provenance_hash,
          rel.source_of_truth = $source_of_truth,
          rel.quarantine_status = $quarantine_status,
          rel.updated_utc = $updated_utc
      RETURN a, rel, b
    `;
    const result = await session.run(cypher, params);
    res.json({ ok: true, records: result.records.length, road: params });
  } catch (error) {
    res.status(400).json({ ok: false, error: error.message });
  } finally {
    await session.close();
    await driver.close();
  }
});

router.post("/neo4j/import-obsidian-links", async (req, res) => {
  const driver = getDriver();
  const session = driver.session();
  try {
    const limit = Math.max(1, Math.min(Number(req.body?.limit || 1000), 10000));
    const files = (await listMarkdownFiles(VAULT_ROOT)).slice(0, limit);
    let roads = 0;
    for (const file of files) {
      const full = vaultSafePath(file);
      const content = await readFile(full, "utf8");
      const sourceId = file.replace(/\.md$/i, "");
      await session.run("MERGE (n:ObsidianNote {id:$id}) SET n.path=$path, n.body_hash=$bodyHash", { id: sourceId, path: file, bodyHash: sha256(content) });
      for (const target of extractWikiLinks(content)) {
        await session.run(`
          MERGE (a:ObsidianNote {id:$sourceId})
          MERGE (b:ObsidianNote {id:$targetId})
          MERGE (a)-[r:WIKILINKS_TO]->(b)
          SET r.authority_scope='local_workbench_mirror', r.outcome='hold', r.torsion=1, r.coherence=0.5, r.updated_utc=$updated
        `, { sourceId, targetId: target, updated: new Date().toISOString() });
        roads += 1;
      }
    }
    res.json({ ok: true, notesScanned: files.length, roadsImported: roads });
  } catch (error) {
    res.status(500).json({ ok: false, error: error.message });
  } finally {
    await session.close();
    await driver.close();
  }
});

export default router;
