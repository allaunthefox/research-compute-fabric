import Database from "./sqlite.js";
import { join } from "path";
import { spawn } from "child_process";
import { existsSync } from "fs";

const dbPath = join(process.cwd(), "data", "substrate_index.db");
const db = new Database(dbPath);

const SEARCHSERVER = join(process.cwd(), "tools", "lean", "Semantics", ".lake", "build", "bin", "searchserver");

// Finite keyword→axis mapping (shim boundary). Lean receives only Fin 14 indices.
const KEYWORD_AXES = [
  ["substrate", 0],
  ["compression", 1],
  ["physics", 2],
  ["neural", 3],
  ["manifold", 3],
  ["lean", 4],
  ["market", 5],
  ["safety", 6],
  ["attestation", 7],
  ["hardware", 8],
  ["signal", 9],
  ["bio", 10],
  ["decision", 11],
  ["archive", 12],
  ["sovereign", 13],
];

function buildAxes(query) {
  const q = query.toLowerCase();
  const axes = new Set();
  for (const [kw, axis] of KEYWORD_AXES) {
    if (q.includes(kw)) axes.add(axis);
  }
  return Array.from(axes);
}

function floatToQ16_16(f) {
  return Math.max(0, Math.min(0xFFFFFFFF, Math.round(f * 65536)));
}

function callSearchServer(request) {
  return new Promise((resolve, reject) => {
    const proc = spawn(SEARCHSERVER, [], { stdio: ["pipe", "pipe", "pipe"] });
    let buffer = "";
    proc.stdout.setEncoding("utf-8");
    proc.stdout.on("data", chunk => { buffer += chunk; });
    proc.stdout.on("end", () => {
      const line = buffer.trim().split("\n")[0];
      if (!line) return reject(new Error("searchserver returned empty"));
      try {
        const resp = JSON.parse(line);
        if (resp.error) reject(new Error(resp.error));
        else resolve(resp);
      } catch (e) {
        reject(new Error("Invalid JSON from searchserver: " + line));
      }
    });
    proc.stderr.on("data", chunk => { console.error("[searchserver]", chunk.toString()); });
    proc.on("error", err => reject(err));
    proc.stdin.write(JSON.stringify(request) + "\n");
    proc.stdin.end();
  });
}

export async function hybridSearch(query, limit = 10) {
  const queryLower = query.toLowerCase();

  // 1. Keyword Recall (Sparse) — JS shim does SQLite I/O
  const keywordResults = db.prepare(`
    SELECT pkg, version, description 
    FROM packages 
    WHERE pkg LIKE ? OR description LIKE ? OR tags LIKE ?
    LIMIT 100
  `).all(`%${queryLower}%`, `%${queryLower}%`, `%${queryLower}%`);

  const keywordIds = keywordResults.map(r => `${r.pkg}@${r.version}`);

  if (!existsSync(SEARCHSERVER)) {
    return keywordResults.slice(0, limit).map(r => ({
      pkg: r.pkg,
      version: r.version,
      description: r.description ? r.description.substring(0, 200).replace(/\n/g, " ") + "..." : "No description available.",
      score: 1.0,
      ranker: "keyword-fallback"
    }));
  }

  // 2. Semantic Recall (Dense) — read records, delegate similarity to Lean
  const allRecords = db.prepare("SELECT pkg, version, description, concept_vector FROM packages").all();
  const records = allRecords.map(r => {
    const vec = JSON.parse(r.concept_vector || "[]");
    return {
      id: `${r.pkg}@${r.version}`,
      vector: vec.map(floatToQ16_16)
    };
  });

  const axes = buildAxes(query);

  // 3. Delegate ranking to Lean searchserver
  const resp = await callSearchServer({ axes, keywordIds, records });
  const ranked = (resp.results || [])
    .map(r => {
      const record = allRecords.find(x => `${x.pkg}@${x.version}` === r.id);
      return {
        pkg: r.id.split("@")[0],
        version: r.id.split("@")[1],
        description: record && record.description ? record.description.substring(0, 200).replace(/\n/g, " ") + "..." : "No description available.",
        score: r.score / 65536,
        ranker: "lean-searchserver"
      };
    })
    .slice(0, limit);

  return ranked;
}

// CLI Interface
const isCli = process.argv[1].includes('ene_search.js');
if (isCli) {
  const query = process.argv.slice(2).join(" ");
  if (!query || query === "--help" || query === "-h") {
    console.log("Usage: node ene_search.js <query>");
    console.log("\nSemantic Axes mapped to the 14D Phi-Manifold:");
    console.log(" 0: Substrate/Entropy   1: Compression      2: Physics/Energy");
    console.log(" 3: Neural/Manifold    4: Formal/Logic     5: Markets/MEV");
    console.log(" 6: Safety/Audit       7: Attestation      8: Hardware/FPGA");
    console.log(" 9: Signal/DSP        10: Bioinfo/DNA     11: Decisions");
    console.log("12: Archive           13: Sovereignty");
    process.exit(query ? 0 : 1);
  }
  
  hybridSearch(query).then(results => {
    console.log(`\nResults for: "${query}" (${results.length} found)`);
    if (results.length === 0) {
      console.log("   No records matched the query manifold.");
    }
    results.forEach((r, i) => {
       console.log(`[${i+1}] ${r.pkg} (Confidence: ${r.score.toFixed(4)})`);
       console.log(`    ${r.description}\n`);
    });
  }).catch(err => {
    console.error("Search Error:", err);
  });
}
