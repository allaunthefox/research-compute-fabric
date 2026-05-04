import { createHash } from "crypto";
import { readFile, mkdir, writeFile } from "fs/promises";
import { dirname, join } from "path";
import { buildConstantsRegistry } from "./constants_registry_builder.js";

/**
 * Semantic Number Pattern Search
 *
 * Numeric motif detection for equation-forest cartography.
 *
 * Rule:
 *   number -> semantic role -> operator context -> equation road
 *   -> exactness/uncertainty/authority weighting -> HOLD candidate
 *
 * Raw numeric resemblance never creates a basin.
 */

type MotifRole =
  | "coefficient"
  | "exponent"
  | "ratio"
  | "constant"
  | "threshold"
  | "index"
  | "dimension"
  | "frequency"
  | "parameter"
  | "unknown";

type OperatorContext =
  | "additive"
  | "multiplicative"
  | "power"
  | "division"
  | "exponential"
  | "logarithmic"
  | "differential"
  | "integral"
  | "gradient"
  | "summation"
  | "normalization"
  | "frequency"
  | "unknown";

type ConstantRegistryRecord = {
  record_id: string;
  symbol: string;
  display_symbol?: string;
  name: string;
  value: string;
  unit: string;
  status: string;
  authority_weight: number;
  authority_family?: string;
  source_name: string;
  source_version: string;
  license_scope: string;
  audit_status: string;
  forest_role: string;
  blocked_uses: string[];
};

type EquationRecord = {
  name: string;
  domain: string;
  equation: string;
  variables?: string;
  meaning?: string;
  authority?: string;
  outcome?: string;
  layer?: string;
  bind?: string;
};

type NumericMotif = {
  motif_id: string;
  value: string;
  normalized_form: string;
  role: MotifRole;
  operator_context: OperatorContext;
  equation_id: string;
  equation_source: string;
  equation_domain: string;
  source_authority: string;
  exactness_status: string;
  source_family: string;
  license_boundary: string;
  audit_status: string;
  authority_weight: number;
  routing_weight: number;
  blocked_uses: string[];
  provenance_hash: string;
  outcome: "hold" | "candidate" | "scar" | "basin";
  notes: string;
};

type PatternRoad = {
  road_id: string;
  motif_key: string;
  motif_value: string;
  from_equation: string;
  to_equation: string;
  relation: "SHARES_MOTIF" | "SHARES_EXACT_CONSTANT" | "SHARES_MEASURED_CONSTANT" | "SHARES_ENVIRONMENTAL_PARAMETER";
  operator_context: OperatorContext;
  route_score: number;
  torsion_prior: number;
  outcome: "hold" | "candidate" | "scar" | "basin";
  blocked_uses: string[];
  provenance_hash: string;
};

const ROOT = process.cwd();

const DEFAULT_EQUATION_PACKS = [
  "research-stack/equation-packs/chemistry_physics_nspace_spine_v0.json",
];

const NUMERIC_RE = /(?<![A-Za-z_])(?:\d+\.\d+|\d+|\.\d+)(?:e[+-]?\d+)?/gi;

function sha256(value: unknown): string {
  return createHash("sha256").update(JSON.stringify(value)).digest("hex");
}

function clamp01(x: number): number {
  return Math.max(0, Math.min(1, x));
}

function normalizeNumber(raw: string): string {
  const cleaned = raw.trim();
  if (/^\d+$/.test(cleaned)) return cleaned;
  const n = Number(cleaned);
  if (!Number.isFinite(n)) return cleaned;
  if (Math.abs(n - 0.5) < 1e-12) return "1/2";
  if (Math.abs(n - 0.3333333333333333) < 1e-12) return "1/3";
  if (Math.abs(n - 0.6666666666666666) < 1e-12) return "2/3";
  if (Math.abs(n - 0.75) < 1e-12) return "3/4";
  return String(n);
}

function classifyOperatorContext(equation: string, token: string): OperatorContext {
  const i = equation.indexOf(token);
  const around = i >= 0 ? equation.slice(Math.max(0, i - 8), Math.min(equation.length, i + token.length + 8)) : equation;
  if (/\^|sqrt|power/i.test(around)) return "power";
  if (/exp|e\^/i.test(around)) return "exponential";
  if (/log|ln/i.test(around)) return "logarithmic";
  if (/∇|grad|d\/d|d²|dot|¨|˙/i.test(equation)) return "gradient";
  if (/Σ|sum/i.test(equation)) return "summation";
  if (/Hz|s\^-1|frequency|nu|ν/i.test(equation)) return "frequency";
  if (/\//.test(around)) return "division";
  if (/\*/.test(around) || /[A-Za-z_]\s*\(/.test(around)) return "multiplicative";
  if (/\+|-/.test(around)) return "additive";
  return "unknown";
}

function classifyRole(equation: string, token: string, normalized: string): MotifRole {
  const context = classifyOperatorContext(equation, token);
  if (context === "power") return "exponent";
  if (context === "division" && /\//.test(equation)) return "ratio";
  if (context === "frequency") return "frequency";
  if (/^[0-9]+$/.test(normalized) && /[Nn]|index|Σ|sum/.test(equation)) return "index";
  if (["1/2", "1/3", "2/3", "3/4"].includes(normalized)) return "ratio";
  return "coefficient";
}

function exactnessWeight(status: string): number {
  switch (status) {
    case "exact": return 0.98;
    case "derived_exact": return 0.95;
    case "mathematical": return 0.95;
    case "measured": return 0.76;
    case "conventional": return 0.70;
    case "environmental": return 0.48;
    case "model": return 0.62;
    default: return 0.30;
  }
}

function contextWeight(context: OperatorContext): number {
  switch (context) {
    case "power": return 0.86;
    case "exponential": return 0.84;
    case "gradient": return 0.88;
    case "frequency": return 0.82;
    case "division": return 0.78;
    case "multiplicative": return 0.72;
    default: return 0.55;
  }
}

function relationForStatus(status: string): PatternRoad["relation"] {
  if (status === "exact" || status === "derived_exact" || status === "mathematical") return "SHARES_EXACT_CONSTANT";
  if (status === "environmental") return "SHARES_ENVIRONMENTAL_PARAMETER";
  if (status === "measured") return "SHARES_MEASURED_CONSTANT";
  return "SHARES_MOTIF";
}

async function readJson<T>(path: string): Promise<T> {
  return JSON.parse(await readFile(join(ROOT, path), "utf8")) as T;
}

async function writeJson(path: string, value: unknown) {
  const full = join(ROOT, path);
  await mkdir(dirname(full), { recursive: true });
  await writeFile(full, JSON.stringify(value, null, 2) + "\n", "utf8");
}

function constantMatches(equation: string, constants: ConstantRegistryRecord[]): ConstantRegistryRecord[] {
  const matches: ConstantRegistryRecord[] = [];
  for (const c of constants) {
    const symbols = [c.symbol, c.display_symbol].filter(Boolean).map(String);
    for (const s of symbols) {
      if (!s || s.length < 1) continue;
      const escaped = s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
      const re = new RegExp(`(^|[^A-Za-z0-9_])${escaped}([^A-Za-z0-9_]|$)`);
      if (re.test(equation)) {
        matches.push(c);
        break;
      }
    }
  }
  return matches;
}

function motifFromNumber(eq: EquationRecord, token: string, equationSource: string): NumericMotif {
  const normalized = normalizeNumber(token);
  const operator_context = classifyOperatorContext(eq.equation, token);
  const role = classifyRole(eq.equation, token, normalized);
  const status = "unknown";
  const routing_weight = clamp01(exactnessWeight(status) * contextWeight(operator_context));
  const body = { eq: eq.name, token, normalized, operator_context, role };
  return {
    motif_id: `motif:${sha256(body).slice(0, 16)}`,
    value: token,
    normalized_form: normalized,
    role,
    operator_context,
    equation_id: eq.name,
    equation_source: equationSource,
    equation_domain: eq.domain,
    source_authority: eq.authority || "unknown",
    exactness_status: status,
    source_family: "numeric_literal",
    license_boundary: "local_equation_pack",
    audit_status: "seed",
    authority_weight: 0.30,
    routing_weight,
    blocked_uses: ["raw_numeric_resemblance", "direct_basin_promotion"],
    provenance_hash: sha256(body),
    outcome: "hold",
    notes: "Raw numeric literal. Requires operator/domain context, baseline, perturbation, and authority gates.",
  };
}

function motifFromConstant(eq: EquationRecord, c: ConstantRegistryRecord, equationSource: string): NumericMotif {
  const operator_context = classifyOperatorContext(eq.equation, c.symbol);
  const routing_weight = clamp01(Number(c.authority_weight || exactnessWeight(c.status)) * exactnessWeight(c.status) * contextWeight(operator_context));
  const body = { eq: eq.name, constant: c.record_id, operator_context };
  return {
    motif_id: `motif:${sha256(body).slice(0, 16)}`,
    value: c.value,
    normalized_form: c.symbol,
    role: "constant",
    operator_context,
    equation_id: eq.name,
    equation_source: equationSource,
    equation_domain: eq.domain,
    source_authority: eq.authority || "unknown",
    exactness_status: c.status,
    source_family: c.source_name,
    license_boundary: c.license_scope,
    audit_status: c.audit_status,
    authority_weight: Number(c.authority_weight || exactnessWeight(c.status)),
    routing_weight,
    blocked_uses: [...new Set([...(c.blocked_uses || []), "direct_basin_promotion"])],
    provenance_hash: sha256(body),
    outcome: "hold",
    notes: `${c.name}; ${c.status}. Constants anchor routing and dimensional checks only.`,
  };
}

function buildRoads(motifs: NumericMotif[]): PatternRoad[] {
  const groups = new Map<string, NumericMotif[]>();
  for (const motif of motifs) {
    const key = `${motif.normalized_form}|${motif.operator_context}|${motif.exactness_status}`;
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key)!.push(motif);
  }

  const roads: PatternRoad[] = [];
  for (const [key, group] of groups) {
    const uniqueByEquation = [...new Map(group.map((m) => [m.equation_id, m])).values()];
    for (let i = 0; i < uniqueByEquation.length; i += 1) {
      for (let j = i + 1; j < uniqueByEquation.length; j += 1) {
        const a = uniqueByEquation[i];
        const b = uniqueByEquation[j];
        const sharedWeight = Math.min(a.routing_weight, b.routing_weight);
        const sameDomainPenalty = a.equation_domain === b.equation_domain ? 0 : 0.08;
        const projectionPenalty = a.blocked_uses.includes("raw_numeric_resemblance") || b.blocked_uses.includes("raw_numeric_resemblance") ? 0.25 : 0;
        const route_score = clamp01(sharedWeight - sameDomainPenalty - projectionPenalty);
        const torsion_prior = clamp01(1 - route_score);
        const body = { a: a.motif_id, b: b.motif_id, key, route_score };
        roads.push({
          road_id: `road:${sha256(body).slice(0, 16)}`,
          motif_key: key,
          motif_value: a.normalized_form,
          from_equation: a.equation_id,
          to_equation: b.equation_id,
          relation: relationForStatus(a.exactness_status),
          operator_context: a.operator_context,
          route_score,
          torsion_prior,
          outcome: "hold",
          blocked_uses: [...new Set([...a.blocked_uses, ...b.blocked_uses, "direct_basin_promotion_without_graph_audit"])],
          provenance_hash: sha256(body),
        });
      }
    }
  }
  return roads.sort((a, b) => b.route_score - a.route_score);
}

async function loadEquations(paths: string[]): Promise<{ records: EquationRecord[]; sources: Map<string, string> }> {
  const records: EquationRecord[] = [];
  const sources = new Map<string, string>();
  for (const path of paths) {
    const pack = await readJson<{ pack_id?: string; equations?: EquationRecord[] }>(path);
    for (const eq of pack.equations || []) {
      records.push(eq);
      sources.set(eq.name, pack.pack_id || path);
    }
  }
  return { records, sources };
}

export async function runSemanticNumberPatternSearch(options: {
  equationPacks?: string[];
  constantsRegistryPath?: string;
  outputDir?: string;
} = {}) {
  const equationPacks = options.equationPacks || DEFAULT_EQUATION_PACKS;
  const constantsRegistryPath = options.constantsRegistryPath || "research-stack/constants/constants_registry_v0.json";
  const outputDir = options.outputDir || "research-stack/semantic-number-patterns";

  // Ensure registry exists before motif extraction.
  const registry = await buildConstantsRegistry(undefined, constantsRegistryPath) as unknown as { records: ConstantRegistryRecord[] };
  const constants = registry.records || [];
  const { records: equations, sources } = await loadEquations(equationPacks);

  const motifs: NumericMotif[] = [];
  for (const eq of equations) {
    const equationSource = sources.get(eq.name) || "unknown_pack";
    const constantHits = constantMatches(eq.equation, constants);
    for (const c of constantHits) motifs.push(motifFromConstant(eq, c, equationSource));

    const numberHits = eq.equation.match(NUMERIC_RE) || [];
    for (const token of numberHits) motifs.push(motifFromNumber(eq, token, equationSource));
  }

  const roads = buildRoads(motifs);
  const falseAttractors = roads.filter((r) => r.route_score < 0.35 || r.blocked_uses.includes("raw_numeric_resemblance"));
  const torsionCandidates = roads.map((r) => ({
    road_id: r.road_id,
    motif_key: r.motif_key,
    from_equation: r.from_equation,
    to_equation: r.to_equation,
    torsion_prior: r.torsion_prior,
    route_score: r.route_score,
    outcome: "hold",
    next_gate: "graph_diff + perturbation + randomized_baseline + Graph.lean audit",
  }));

  const summary = {
    generated_utc: new Date().toISOString(),
    equation_pack_count: equationPacks.length,
    equation_count: equations.length,
    constant_registry_records: constants.length,
    motif_count: motifs.length,
    road_count: roads.length,
    false_attractor_count: falseAttractors.length,
    rule: "Every result remains HOLD. No numeric motif, exact constant, or shared pattern can become a basin without gates.",
  };

  await writeJson(`${outputDir}/numeric_motifs.json`, { summary, motifs });
  await writeJson(`${outputDir}/numeric_pattern_roads.json`, { summary, roads });
  await writeJson(`${outputDir}/numeric_torsion_candidates.json`, { summary, torsion_candidates: torsionCandidates });
  await writeJson(`${outputDir}/false_attractor_report.json`, { summary, false_attractors: falseAttractors });

  return { summary, motifs, roads, falseAttractors };
}

if (import.meta.url === `file://${process.argv[1]}`) {
  runSemanticNumberPatternSearch()
    .then(({ summary }) => {
      console.log(JSON.stringify(summary, null, 2));
    })
    .catch((error) => {
      console.error(error);
      process.exit(1);
    });
}
