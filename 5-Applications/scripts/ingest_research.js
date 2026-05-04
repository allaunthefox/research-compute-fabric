import fs from 'fs';
import Database from 'better-sqlite3';
import { join } from 'path';
import { createHash } from 'crypto';

const SOURCE_FILE = '/home/allaun/Documents/DeleteMe/ChatGPT-Ricci_Flow_and_Turbulence.json';
const dbPath = join(process.cwd(), "data", "substrate_index.db");

async function ingest() {
  console.log(`🚀 Starting manual ENE ingestion of ${SOURCE_FILE}...`);

  if (!fs.existsSync(SOURCE_FILE)) {
    console.error(`❌ Source file not found: ${SOURCE_FILE}`);
    return;
  }

  // 1. Read and Parse JSON
  const rawData = fs.readFileSync(SOURCE_FILE, 'utf-8');
  const data = JSON.parse(rawData);
  const title = data.title || 'Ricci Flow and Turbulence Research';
  const timestamp = data.timestamp || new Date().toISOString();

  // 2. Format Body
  let body = `# ${title}\n\n`;
  body += `**Source:** ChatGPT Export\n`;
  body += `**Timestamp:** ${timestamp}\n\n---\n\n`;

  for (const msg of data.messages) {
    const role = msg.role === 'user' ? 'USER' : 'ASSISTANT';
    body += `### ${role}\n${msg.content}\n\n`;
  }

  const pkgName = `aiscroll/${title.toLowerCase().replace(/[^a-z0-9]/g, '_')}`;
  const sha256 = createHash("sha256").update(body).digest("hex");
  const version = new Date().toISOString().replace(/[:.]/g, "-");

  // 3. ENE Ingestion (Direct SQLite)
  console.log('\n[1/1] Anchoring to ENE Substrate (Direct SQL)...');
  const db = new Database(dbPath);
  
  try {
    const stmt = db.prepare(`
      INSERT INTO packages (
        pkg, version, tier, domain, archetype, 
        description, tags, source, 
        sha256, indexed_utc, model_status,
        foam_score, verification_basis,
        idea_weights, extension_points, concept_vector, analog_map, concept_anchor
      ) VALUES (
        ?, ?, ?, ?, ?, 
        ?, ?, ?,
        ?, ?, ?,
        ?, ?,
        ?, ?, ?, ?, ?
      )
    `);

    const result = stmt.run(
      pkgName,
      version,
      "RESEARCH",
      "neural_manifold",
      "chat_session",
      body.substring(0, 2000), // Description matches ene.js logic
      JSON.stringify(['ricci_flow', 'turbulence', 'behavioral_manifold', 'market_filter']),
      "YourAIScroll",
      sha256,
      new Date().toISOString(),
      "INGESTED",
      body.length / 65536.0, // dummy foam score
      "manual_verified",
      JSON.stringify({}),
      JSON.stringify([]),
      JSON.stringify(['ricci_flow', 'turbulence']),
      JSON.stringify({ sigma_codon: 'RESEARCH', classify: 'thermodynamic_manifold' }),
      JSON.stringify({ domain: "research", concept: title, resolution: "SEED" })
    );

    console.log(`✅ ENE Ingest Success: ${pkgName} @ ${version} (RowID: ${result.lastInsertRowid})`);
  } catch (e) {
    console.error(`❌ ENE Ingest Failed: ${e.message}`);
  } finally {
    db.close();
  }

  console.log('\n🏁 Manual ENE ingestion complete.');
}

ingest().catch(console.error);
