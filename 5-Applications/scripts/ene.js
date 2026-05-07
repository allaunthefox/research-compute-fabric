import Database from "./sqlite.js";
import { join } from "path";
import { createHash } from "crypto";

const dbPath = join(process.cwd(), "data", "substrate_index.db");

export function pkgIngest({ title, body, kind, tags, sessionId, notionId, metric, witness, sigma }) {
  const db = new Database(dbPath);
  
  try {
    const pkgName = `aiscroll/${title.toLowerCase().replace(/[^a-z0-9]/g, "_")}`;
    const version = new Date().toISOString().replace(/[:.]/g, "-");
    const timestamp = new Date().toISOString();
    
    // Create a simple SHA256 of the body for provenance
    const sha256 = createHash("sha256").update(body).digest("hex");

    // Enhance description with Sigma metatyping if available
    let description = body.substring(0, 500);
    if (sigma) {
      description = `[SIGMA: ${sigma.sigma_codon || 'UNK'}] ${sigma.classify || 'data'}\n` +
                    `OBSERVE: ${sigma.observe || ''}\n` +
                    `PROVE: ${sigma.prove || ''}\n---\n` +
                    description;
    }

    const stmt = db.prepare(`
      INSERT INTO packages (
        pkg, version, tier, domain, archetype, 
        description, tags, source, session_id, notion_id,
        sha256, indexed_utc, model_status,
        foam_score, verification_basis,
        idea_weights, extension_points, concept_vector, analog_map, concept_anchor,
        audit_rationale
      ) VALUES (
        ?, ?, ?, ?, ?, 
        ?, ?, ?, ?, ?,
        ?, ?, ?,
        ?, ?,
        ?, ?, ?, ?, ?,
        ?
      )
    `);

    const result = stmt.run(
      pkgName,
      version,
      "RESEARCH",
      "neural_manifold",
      kind || "chat_session",
      description,
      JSON.stringify(tags || []),
      "YourAIScroll",
      sessionId || null,
      notionId || null,
      sha256,
      timestamp,
      "INGESTED",
      metric ? parseFloat(metric.cost) / 65536.0 : 0.0, // Convert Q16.16 to float for foam_score
      witness ? witness.trace_hash : "unverified",
      JSON.stringify({}), // idea_weights
      JSON.stringify([]), // extension_points
      JSON.stringify(sigma ? sigma.tags : []), // Use sigma tags for concept_vector as placeholder
      JSON.stringify(sigma || {}), // analog_map as placeholder for sigma object
      JSON.stringify({ domain: "research", concept: title, resolution: "SEED" }), // concept_anchor
      sigma ? JSON.stringify(sigma) : null // audit_rationale
    );

    return {
      ok: true,
      pkg: pkgName,
      version: version,
      rowid: result.lastInsertRowid
    };
  } catch (error) {
    console.error("ENE Ingest Error:", error);
    throw error;
  } finally {
    db.close();
  }
}
