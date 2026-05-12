import "dotenv/config";
import express from "express";
import { exec, spawn } from "child_process";
import Database from "./sqlite.js";
import { join } from "path";
import { notion, notionDatabaseId, validateNotionConfig } from "./notion.js";
import { pkgIngest } from "./ene.js";
import { createLinearIssue } from "./linear.js";
import { z } from "zod";
import workspaceRouter from "./workspace.js";


const app = express();
app.use(express.json());
app.use(express.static("public"));


const PORT = process.env.PORT || 3000;

// ============================================================================
// Lean BindServer Subprocess Wrapper
// ============================================================================
class LeanBindServer {
  constructor() {
    this.binary = join(process.cwd(), "tools", "lean", "Semantics", ".lake", "build", "bin", "bindserver");
    this.proc = null;
    this.queue = [];
    this.buffer = "";
    this._start();
  }

  _start() {
    try {
      this.proc = spawn(this.binary, [], { stdio: ["pipe", "pipe", "pipe"] });
      this.proc.stdout.setEncoding("utf-8");
      this.proc.stdout.on("data", (chunk) => {
        this.buffer += chunk;
        let idx;
        while ((idx = this.buffer.indexOf("\n")) !== -1) {
          const line = this.buffer.slice(0, idx).trim();
          this.buffer = this.buffer.slice(idx + 1);
          if (line) this._handleLine(line);
        }
      });
      this.proc.on("error", (err) => {
        console.error("[bindserver] process error:", err.message);
      });
      this.proc.on("close", (code) => {
        console.error("[bindserver] process exited with code", code);
        this.proc = null;
      });
    } catch (err) {
      console.error("[bindserver] failed to start:", err.message);
    }
  }

  _handleLine(line) {
    const pending = this.queue.shift();
    if (!pending) {
      console.error("[bindserver] unexpected response:", line);
      return;
    }
    try {
      const resp = JSON.parse(line);
      if (resp.error) pending.reject(new Error(resp.error));
      else pending.resolve(resp);
    } catch (e) {
      pending.reject(new Error("Invalid JSON from bindserver: " + line));
    }
  }

  async call(request) {
    return new Promise((resolve, reject) => {
      if (!this.proc || this.proc.killed) {
        reject(new Error("bindserver not running"));
        return;
      }
      this.queue.push({ resolve, reject });
      this.proc.stdin.write(JSON.stringify(request) + "\n");
    });
  }
}

const leanServer = new LeanBindServer();

// ============================================================================
// API Endpoints
// ============================================================================

app.get("/", (_req, res) => {
  res.json({ status: "ok", service: "research-stack" });
});

app.get("/health/notion", async (_req, res) => {
  try {
    const result = await validateNotionConfig();
    res.json(result);
  } catch (error) {
    res.status(500).json({ ok: false, error: error.message });
  }
});

app.get("/health/network", async (_req, res) => {
  const status = {
    timestamp: new Date().toISOString(),
    substrate: "OFFLINE",
    tailscale: "CHECKING",
    remotes: {
      witnessSources: "CONFIGURED",
      i2p: "OFFLINE"
    }
  };

  // Dynamic i2p Enforcement & Health Check
  try {
    const { execSync } = await import("child_process");
    const wardenResult = execSync("python3 tools/scripts/i2p_warden.py").toString();
    status.remotes.i2p = wardenResult.includes("healthy") || wardenResult.includes("recovered") ? "ONLINE" : "OFFLINE";
  } catch (e) {
    status.remotes.i2p = "ERROR";
    console.error("[NETWORK] Warden execution failed:", e.message);
  }

  try {
    const db = new Database(join(process.cwd(), "data", "substrate_index.db"), { readonly: true });
    const count = db.prepare("SELECT count(*) as c FROM packages").get().c;
    status.substrate = `OK (${count} records)`;
    db.close();
  } catch (e) { status.substrate = "ERROR: " + e.message; }
  exec("ping -c 1 -W 2 100.127.111.7", (err) => {
    status.tailscale = err ? "OFFLINE" : "ONLINE";
    console.log(`[NETWORK] Tailscale: ${status.tailscale} | Substrate: ${status.substrate}`);
  });
  res.json(status);
});

// Cross-Node ENE Sync (Broadcast Receiver)
app.post("/sync/ene", async (req, res) => {
  try {
    const record = req.body;
    if (!record.pkg || !record.version) {
      return res.status(400).json({ ok: false, error: "Malformed sync record" });
    }

    const db = new Database(join(process.cwd(), "data", "substrate_index.db"));
    const insert = db.prepare(`
      INSERT OR IGNORE INTO packages (
        pkg, version, domain, tier, description, tags, source,
        sha256, quality_status, audit_rationale, indexed_utc, concept_vector, concept_anchor
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `);

    insert.run(
      record.pkg,
      record.version,
      record.domain || "SYNCED",
      record.tier || "RESEARCH",
      record.description || "",
      typeof record.tags === 'string' ? record.tags : JSON.stringify(record.tags || []),
      "OMNI_SYNC",
      record.sha256 || null,
      record.quality_status || null,
      record.audit_rationale || null,
      new Date().toISOString(),
      typeof record.concept_vector === 'string' ? record.concept_vector : JSON.stringify(record.concept_vector || []),
      typeof record.concept_anchor === 'string' ? record.concept_anchor : JSON.stringify(record.concept_anchor || {})
    );

    db.close();
    res.json({ ok: true, message: `Synced ${record.pkg} to local substrate` });
    console.log(`[SYNC] Accepted package: ${record.pkg} from remote node`);
  } catch (error) {
    res.status(500).json({ ok: false, error: error.message });
  }
});

app.post("/tsdm/packet", express.json(), (req, res) => {
  const { payload } = req.body;
  if (!payload || !payload.startsWith("0xTS")) {
    return res.status(400).json({ error: "Invalid TSDM packet format" });
  }
  console.log(`[TSDM] Received compressed packet: ${payload.substring(0, 16)}...`);
  // Hardware routing logic maps here
  res.json({ status: "blitted", message: "Spectral signature XOR-accumulated" });
});

app.post("/ingest", async (req, res) => {
  try {
    const { title, body, kind = "archive_note", tags = [], target = "notion" } = req.body;
    let lean;
    try {
      const bindResp = await leanServer.call({
        metricKind: "control",
        left: { value: 1.0 },
        right: { value: 1.0 },
        useHistory: false,
        historyLen: 0,
        historyCost: 0.0,
        historyTorsion: 0.0,
      });
      lean = {
        metric: {
          cost: bindResp.cost,
          tensor: bindResp.metricTensor,
          torsion: bindResp.metricTorsion,
          reference: `bindserver:${target}`,
        },
        witness: {
          trace_hash: bindResp.traceHash,
          conserved: bindResp.lawful,
        },
      };
    } catch (err) {
      console.error("[ingest] bindserver call failed:", err.message);
      lean = {
        metric: { cost: 0x00010000, tensor: "control", torsion: 0, reference: "fallback" },
        witness: { trace_hash: `fallback:${target}`, conserved: false },
      };
    }
    const humanCost = (lean.metric.cost / 65536).toFixed(4);
    const pkgName = `aiscroll/${title.toLowerCase().replace(/[^a-z0-9]/g, "_")}`;
    const version = new Date().toISOString();

    let linearIssue = null;
    let notionPage = null;

    // 1. Common Side Effects (Linear/Notion) based on target
    if (target === "ene" || target === "notion") {
      // Linear Sync (always for ENE, optional for Notion?)
      try {
        linearIssue = await createLinearIssue({ title, description: body.substring(0, 2000), pkgName });
      } catch (err) { console.warn("Linear sync failed:", err.message); }

      // Notion Sync
      try {
        notionPage = await notion.pages.create({
          parent: { database_id: notionDatabaseId },
          properties: {
            "Name": { title: [{ text: { content: title || "Untitled" } }] },
            "Kind": { select: { name: kind } },
            "Tags": { multi_select: tags.map((tag) => ({ name: tag })) },
            "Package": { rich_text: [{ text: { content: pkgName } }] },
            "Version": { rich_text: [{ text: { content: version } }] },
            "Resolution": { select: { name: "SEED" } },
            "Assemblage Cost": { number: parseFloat(humanCost) },
            "Lean Witness": { rich_text: [{ text: { content: lean.witness.trace_hash } }] }
          },
          children: [{ object: "block", type: "paragraph", paragraph: { rich_text: [{ type: "text", text: { content: body || "" } }] } }]
        });
      } catch (err) { console.warn("Notion sync failed:", err.message); }
    }

    // 2. Primary Target Action
    if (target === "ene") {
      const result = pkgIngest({
        title,
        body,
        kind,
        tags,
        sessionId: linearIssue ? linearIssue.url : null,
        notionId: notionPage ? notionPage.id : null,
        metric: lean.metric,
        witness: lean.witness,
        sigma: req.body.sigma // Pass sigma from request
      });
      return res.json({ ...result, linear: linearIssue, notion: notionPage ? { id: notionPage.id, url: notionPage.url } : null, cost: humanCost });
    }

    if (target === "forgejo" || target === "github") {
      const shim = target === "forgejo" ? "forgejo_shim.py" : "github_shim.py";
      exec(`python3 tools/scripts/${shim} "${title}" "${body}" "${humanCost}" "${lean.witness.trace_hash}"`, (error, stdout) => {
        if (error) console.error(`${target} Shim Error: ${error.message}`);
        console.log(`${target} Shim Output: ${stdout}`);
      });
      return res.json({ ok: true, status: "sent_to_shim", cost: humanCost, witness: lean.witness.trace_hash });
    }

    // Default: Notion Only
    if (notionPage) {
      return res.json({ ok: true, pageId: notionPage.id, url: notionPage.url, cost: humanCost });
    } else {
      throw new Error("Target action failed to produce a result.");
    }
  } catch (error) {
    res.status(500).json({ ok: false, error: error.message });
  }
});

// Workspace Routes
app.use("/workspace", workspaceRouter);

app.listen(PORT, () => {

  console.log(`Research Stack server running on http://localhost:${PORT}`);
});
