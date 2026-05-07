import { mkdirSync, readFileSync, writeFileSync } from "fs";
import { basename, join } from "path";
import { createHash } from "crypto";
import { pkgIngest } from "./ene.js";

const AXES = {
  substrate: ["substrate", "ene", "manifold", "n-space", "field"],
  compression: ["compression", "codec", "s3c", "shell-3", "binding"],
  physics: ["phi", "landauer", "thermodynamic", "energy", "mass"],
  neural: ["cognitive", "neural", "homeostatic", "load"],
  lean: ["lean", "theorem", "formal", "proof", "s3c.lean"],
  safety: ["verification", "invariant", "admissibility", "audit"],
  attestation: ["provenance", "session", "transcript", "hash"],
  hardware: ["fpga", "hardware", "verilog"],
  signal: ["echo", "wave", "j-score", "spectral"],
  decision: ["linear", "notion", "next theorem", "roadmap"],
  archive: ["chatgpt", "archive", "ingest"],
  sovereignty: ["sovereign", "identity"]
};

const KEY_TERMS = [
  "S3C",
  "PIST",
  "DIAT",
  "Bracket Algebra",
  "massPlus",
  "massZero",
  "hyperbola mass",
  "primitive set",
  "n-space",
  "throat",
  "emission gate",
  "ENE",
  "Linear",
  "Notion",
  "HDMI",
  "DVI",
  "TMDS",
  "sRGB",
  "CE-sRGB",
  "NIICore",
  "Virtual HDMI Blitter",
  "DynamicCanal",
  "FAMM",
  "SemanticMass",
  "MassNumber",
  "Hutter"
];

function usage() {
  console.error("Usage: node scripts/ingest_chatgpt_session.mjs /path/to/chatgpt-export.json");
  process.exit(2);
}

function slugify(value) {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_+|_+$/g, "");
}

function isoTime(value) {
  if (!value) return null;
  const d = new Date(value);
  return Number.isNaN(d.getTime()) ? null : d.toISOString();
}

function transcript(messages) {
  return messages.map((msg) => {
    const role = String(msg.role || "unknown").toUpperCase();
    const stamp = isoTime(msg.timestamp) || "unknown-time";
    return `[${role}][${stamp}]\n${msg.content || ""}`;
  }).join("\n\n---\n\n");
}

function tagsFor(text) {
  const lower = text.toLowerCase();
  const tags = new Set(["chatgpt", "session", "research", "ene-ingest"]);
  for (const [axis, terms] of Object.entries(AXES)) {
    for (const term of terms) {
      if (lower.includes(term.toLowerCase())) {
        tags.add(term);
        tags.add(`axis:${axis}`);
      }
    }
  }
  for (const term of KEY_TERMS) {
    if (lower.includes(term.toLowerCase())) tags.add(term);
  }
  return [...tags].sort();
}

function importantMessages(messages) {
  return messages.filter((msg) => {
    const content = String(msg.content || "");
    return KEY_TERMS.some((term) => content.toLowerCase().includes(term.toLowerCase()));
  });
}

function buildBrief({ title, sourcePath, json, body, tags }) {
  const hits = importantMessages(json.messages || []);
  const lastHits = hits.slice(-18);
  const sha256 = createHash("sha256").update(body).digest("hex");
  const lower = `${title}\n${body}`.toLowerCase();
  const isScaleRuleSession =
    lower.includes("wrinkle-in-time scale rule") ||
    lower.includes("operator first, scale later") ||
    lower.includes("atomized math problem with mass numbers");
  const isHdmiFabricSession =
    lower.includes("hdmi as computation fabric") ||
    lower.includes("virtual hdmi blitter") ||
    lower.includes("tmds") ||
    lower.includes("ce-srgb") ||
    lower.includes("srgb niicore");

  const bullets = isHdmiFabricSession
    ? [
        "Raw session converted to ENE package provenance.",
        "Working concept: HDMI/DVI-style display machinery as deterministic compute/witness fabric, not display-only output.",
        "Virtual HDMI/Display Blitter maps raster pixels or cells into command/state packets.",
        "TMDS/DVI timing acts as a timing-law plane; sRGB and CE-sRGB-NIICore act as payload and compute-packet surfaces.",
        "DynamicCanal plus Hot/Cold FAMM route admissible paths, scars, and recovery through the fabric.",
        "Semantic Prime Refraction, Chirality Destabilizer, and hybrid sandpile sections are search-graph targets, not Hutter-safe compression claims by default."
      ]
    : isScaleRuleSession
    ? [
        "Raw session converted to ENE package provenance.",
        "Canonical rule: `operator first, scale later`; do not bind physical constants until the operator class is stable.",
        "Wrinkle-in-Time scale rule: model-cell size is relative to the observer, solver, or substrate manipulating it.",
        "Mass numbers are scale-invariant identity/load/coupling/conservation tags before they are literal nuclear values.",
        "FPGA target: conservation-preserving event cells with mass/load, strain, phase, edge state, threshold, energy, and emitted wave amplitude.",
        "No-CFD rule: if a problem tries to become a continuous fluid simulation, renormalize it into a solid lattice event or emitted wave packet."
      ]
    : [
        "Raw session converted to ENE package provenance.",
        "Working concept: S3C is a shell-manifold codec that preserves topologically significant values.",
        "Bridge claim: S3C open-shell mass, `massPlus = a * bPlus`, is the PIST hyperbola mass.",
        "Closed-shell mass, `massZero = a * bZero`, is the codec/contact/throat mass.",
        "Primitive-set rebuild direction: replace scalar divisor-chain tail estimates with n-space transport, bracket admissibility, DIAT witnesses, and PIST/S3C mass flow.",
        "Immediate theorem target: prove `S3C.massPlus n = PIST_Hyperbola_Index n`, then formalize the S3C emission gate as geometric admissibility on the PIST shell manifold."
      ];

  const trackerSeeds = isHdmiFabricSession
    ? [
        "Linear: update RES-2377 with graph/search seeds from the HDMI computation-fabric session.",
        "Wiki: preserve Virtual HDMI Blitter, TMDS Timing Plane, CE-sRGB-NIICore, and Hot/Cold FAMM in the Concept Archive.",
        "ENE: retain transcript, HDMI brief, GraphML edge list, and local graph export as provenance artifacts."
      ]
    : isScaleRuleSession
    ? [
        "Linear: create implementation issue for a Lean/FPGA `RenormalizedMassNumberFractureAutomaton` primitive.",
        "Notion: create knowledge-capture page for the Wrinkle-in-Time scale rule and no-CFD solid-wave atomization path.",
        "ENE: retain transcript, corrected brief, and GraphML concept surface as separate provenance artifacts."
      ]
    : [
        "Linear: create implementation issue for ENE/Notion/Linear propagation of the S3C/PIST bridge brief.",
        "Notion: create knowledge-capture page for the S3C shell-manifold codec and primitive-set transport rebuild.",
        "ENE: retain full transcript as source package and this brief as surface artifact."
      ];

  const excerpts = lastHits.map((msg) => {
    const content = String(msg.content || "").replace(/\s+/g, " ").trim();
    return `- ${msg.role} ${msg.timestamp || ""}: ${content.slice(0, 700)}`;
  }).join("\n");

  return `# ${title} — ENE Ingest Brief

**Source:** \`${sourcePath}\`  
**Chat URL:** ${json.url || "not recorded"}  
**Timestamp:** ${json.timestamp || "not recorded"}  
**Messages:** ${(json.messages || []).length}  
**SHA-256:** \`${sha256}\`

## Ingest Summary
${bullets.map((b) => `- ${b}`).join("\n")}

## Tags
${tags.map((tag) => `\`${tag}\``).join(", ")}

## Tracker Seeds
${trackerSeeds.map((seed) => `- ${seed}`).join("\n")}

## Recent Relevant Excerpts
${excerpts}
`;
}

const inputPath = process.argv[2];
if (!inputPath) usage();

const json = JSON.parse(readFileSync(inputPath, "utf8"));
if (!Array.isArray(json.messages)) {
  throw new Error("Expected ChatGPT export with a messages array.");
}

const title = json.title || basename(inputPath, ".json");
const body = transcript(json.messages);
const tags = tagsFor(`${title}\n${body}`);
const lowerSession = `${title}\n${body}`.toLowerCase();
const isScaleRuleSession =
  lowerSession.includes("wrinkle-in-time scale rule") ||
  lowerSession.includes("operator first, scale later") ||
  lowerSession.includes("atomized math problem with mass numbers");
const isHdmiFabricSession =
  lowerSession.includes("hdmi as computation fabric") ||
  lowerSession.includes("virtual hdmi blitter") ||
  lowerSession.includes("tmds") ||
  lowerSession.includes("ce-srgb") ||
  lowerSession.includes("srgb niicore");
const slug = slugify(title);
const outDir = join(process.cwd(), "data", "ingested", "chatgpt");
mkdirSync(outDir, { recursive: true });

const briefPath = join(outDir, `${slug}_ene_brief.md`);
const bodyPath = join(outDir, `${slug}_transcript.md`);

writeFileSync(bodyPath, `# ${title} Transcript\n\n${body}\n`);
writeFileSync(briefPath, buildBrief({ title, sourcePath: inputPath, json, body, tags }));

const fullResult = pkgIngest({
  title,
  body,
  kind: "chat_session",
  tags,
  sessionId: json.url || inputPath,
  notionId: null,
  metric: null,
  witness: { trace_hash: createHash("sha256").update(body).digest("hex") },
  sigma: isHdmiFabricSession
    ? {
        sigma_codon: "HDMI-COMPUTE-FABRIC",
        classify: "FORMING",
        observe: "ChatGPT session captures virtual HDMI/display blitter routing, TMDS timing plane, CE-sRGB-NIICore payload semantics, DynamicCanal, and Hot/Cold FAMM compute-fabric recovery.",
        prove: "Next formal target is a minimal graph/search-backed spec and hardware smoke path for the DVI/TMDS texel transmitter surface.",
        tags
      }
    : isScaleRuleSession
    ? {
        sigma_codon: "WRINKLE-SCALE-RULE",
        classify: "FORMING",
        observe: "ChatGPT session captures operator-first scale, mass-number event cells, no-CFD solid-wave routing, and galaxy-atom renormalization.",
        prove: "Next formal target is a Lean/FPGA conservation-preserving fracture event cell with scale-delayed mass-number tags.",
        tags
      }
    : {
        sigma_codon: "S3C-PIST-DIAT",
        classify: "FORMING",
        observe: "ChatGPT session captures S3C/PIST bridge, primitive-set transport rebuild, and ENE/Linear/Notion propagation intent.",
        prove: "Next formal target is S3C.massPlus = PIST hyperbola mass.",
        tags
      }
});

const brief = readFileSync(briefPath, "utf8");
const briefResult = pkgIngest({
  title: `${title} ENE Brief`,
  body: brief,
  kind: "research_brief",
  tags: [
    ...new Set([
      ...tags,
      "brief",
      isHdmiFabricSession ? "hdmi-compute-fabric" : isScaleRuleSession ? "scale-rule" : "s3c-pist-bridge"
    ])
  ],
  sessionId: json.url || inputPath,
  notionId: null,
  metric: null,
  witness: { trace_hash: createHash("sha256").update(brief).digest("hex") },
  sigma: isHdmiFabricSession
    ? {
        sigma_codon: "HDMI-COMPUTE-BRIEF",
        classify: "FORMING",
        observe: "Distilled HDMI compute-fabric object for wiki, ENE, Linear, and semantic graph/search tracking.",
        prove: "Formalize TMDS timing-plane invariants, virtual blitter packet shape, and graph evidence paths before attaching compression claims.",
        tags: [...new Set([...tags, "brief", "hdmi", "tmds", "virtual-blitter", "ce-srgb-niicore", "compute-fabric"])]
      }
    : isScaleRuleSession
    ? {
        sigma_codon: "WRINKLE-SCALE-BRIEF",
        classify: "FORMING",
        observe: "Distilled scale-rule object for Notion/Linear surface tracking.",
        prove: "Formalize operator-first renormalization and mass-number event-cell invariants.",
        tags: [...new Set([...tags, "brief", "scale-rule", "mass-number-fracture"])]
      }
    : {
        sigma_codon: "S3C-PIST-BRIDGE",
        classify: "FORMING",
        observe: "Distilled bridge object for Notion/Linear surface tracking.",
        prove: "Formalize massPlus equivalence and gate admissibility.",
        tags: [...new Set([...tags, "brief", "bridge"])]
      }
});

console.log(JSON.stringify({
  ok: true,
  source: inputPath,
  title,
  messages: json.messages.length,
  bodyPath,
  briefPath,
  tags,
  ene: {
    transcript: fullResult,
    brief: briefResult
  }
}, null, 2));
