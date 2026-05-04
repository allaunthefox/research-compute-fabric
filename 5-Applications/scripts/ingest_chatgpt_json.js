import { readFileSync } from "fs";
import { pkgIngest } from "./ene.js";

// Keyword→axis mapping (14D Phi-Manifold)
const KEYWORD_AXES = {
  "substrate": ["layer-3", "rollup", "chain", "infrastructure", "substrate"],
  "compression": [],
  "physics": ["theoretical", "model", "computation", "physics", "simulation"],
  "neural": ["neural", "network", "ai", "agent", "computation"],
  "manifold": ["manifold", "geometry", "scalar", "projection"],
  "lean": [],
  "market": ["crypto", "blockchain", "degen", "trading", "defi", "token"],
  "safety": ["verification", "audit", "security"],
  "attestation": [],
  "hardware": ["fpga", "hardware", "compute"],
  "signal": [],
  "bio": [],
  "decision": ["decision", "choice", "verification", "proof"],
  "archive": [],
  "sovereign": []
};

// Extract keywords from content and map to axes
function extractAutoTags(content) {
  const contentLower = content.toLowerCase();
  const rawTags = [];
  const axisTags = [];
  
  for (const [axis, keywords] of Object.entries(KEYWORD_AXES)) {
    for (const kw of keywords) {
      if (contentLower.includes(kw)) {
        rawTags.push(kw);
        if (!axisTags.includes(axis)) {
          axisTags.push(axis);
        }
      }
    }
  }
  
  return { rawTags, axisTags };
}

// Read the JSON file
const jsonPath = "/home/allaun/Documents/DeleteMe/ChatGPT-Layer_3_Crypto_Networks.json";
const jsonData = JSON.parse(readFileSync(jsonPath, "utf-8"));

// Format the conversation as a single body
const body = jsonData.messages.map(msg => {
  const role = msg.role.toUpperCase();
  const time = new Date(msg.timestamp).toISOString();
  return `[${role}][${time}]\n${msg.content}`;
}).join("\n\n---\n\n");

// Extract autotags from content
const { rawTags, axisTags } = extractAutoTags(body);

// Base tags + extracted tags
const tags = [
  "chatgpt",
  "layer-3",
  "crypto",
  "networks",
  "blockchain",
  ...rawTags,
  ...axisTags.map(axis => `axis:${axis}`)
];

// Ingest into ENE
try {
  const result = pkgIngest({
    title: jsonData.title,
    body: body,
    kind: "chat_session",
    tags: tags,
    sessionId: null,
    notionId: null,
    metric: null,
    witness: null,
    sigma: null
  });
  
  console.log("✅ Successfully ingested ChatGPT conversation into ENE");
  console.log(`   Package: ${result.pkg}`);
  console.log(`   Version: ${result.version}`);
  console.log(`   Row ID: ${result.rowid}`);
  console.log(`   Raw tags: ${rawTags.join(", ")}`);
  console.log(`   Axis tags: ${axisTags.join(", ")}`);
} catch (error) {
  console.error("❌ Failed to ingest:", error.message);
  process.exit(1);
}
