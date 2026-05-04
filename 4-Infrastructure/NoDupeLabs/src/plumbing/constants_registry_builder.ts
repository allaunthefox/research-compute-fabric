import { createHash } from "crypto";
import { readFile, mkdir, writeFile } from "fs/promises";
import { dirname, join } from "path";
import { SOURCE_ADAPTERS, AUTHORITY_WEIGHTS, canImportNow, makeBlockedRecord, summarizeAdapterCoverage } from "./measurement_source_adapters.js";

/**
 * Constants Registry Builder
 *
 * Builds a normalized constants registry from local seed packs and the measurement
 * source adapter catalog.
 *
 * This module is deliberately conservative: it preserves exact/measured/environmental
 * distinctions and refuses to flatten all values into generic numbers.
 */

type ConstantStatus =
  | "exact"
  | "derived_exact"
  | "mathematical"
  | "measured"
  | "conventional"
  | "environmental"
  | "model"
  | "terminology"
  | "standard_definition"
  | "experimental_dataset"
  | "computed_reference"
  | "time_series_reference"
  | "unknown";

type RegistryRecord = {
  record_id: string;
  source_name: string;
  source_version: string;
  symbol: string;
  display_symbol?: string;
  name: string;
  value: string;
  unit: string;
  unit_system: string;
  dimension: string;
  quantity_kind: string;
  status: ConstantStatus;
  standard_uncertainty: string | null;
  relative_uncertainty: string | null;
  coverage: string;
  conditions: string;
  source_uri: string;
  provenance_hash: string;
  license_scope: string;
  audit_status: "seed" | "imported" | "verified" | "stale" | "conflict" | "deprecated" | "blocked";
  authority_weight: number;
  forest_role: string;
  blocked_uses: string[];
  notes: string;
  adapter_id?: string;
};

type AnyRecord = Record<string, unknown>;

const ROOT = process.cwd();

const DEFAULT_INPUTS = [
  "research-stack/constants/si_2019_exact_constants_v0.json",
  "research-stack/constants/physical_constants_foundation_v0.json",
];

const STATUS_WEIGHT: Record<ConstantStatus, number> = {
  exact: 0.98,
  derived_exact: 0.95,
  mathematical: 0.95,
  measured: 0.76,
  conventional: 0.70,
  environmental: 0.48,
  model: 0.62,
  terminology: 0.55,
  standard_definition: 0.80,
  experimental_dataset: 0.60,
  computed_reference: 0.58,
  time_series_reference: 0.64,
  unknown: 0.20,
};

function hashJson(value: unknown): string {
  return createHash("sha256").update(JSON.stringify(value)).digest("hex");
}

function asString(value: unknown, fallback = ""): string {
  if (value === null || value === undefined) return fallback;
  return String(value);
}

function normalizeStatus(value: unknown): ConstantStatus {
  const raw = asString(value, "unknown").trim();
  if (raw in STATUS_WEIGHT) return raw as ConstantStatus;
  if (raw === "definition_exact") return "exact";
  if (raw === "reference") return "measured";
  if (raw === "observational_time_series") return "time_series_reference";
  return "unknown";
}

function blockedUsesFor(status: ConstantStatus): string[] {
  switch (status) {
    case "exact":
    case "derived_exact":
    case "mathematical":
      return ["direct_basin_promotion", "substitute_for_empirical_conditions"];
    case "measured":
      return ["treat_as_exact", "use_without_uncertainty", "direct_basin_promotion"];
    case "conventional":
      return ["treat_as_local_measurement", "treat_as_universal_empirical_truth", "direct_basin_promotion"];
    case "environmental":
      return ["use_without_site_context", "treat_as_constant", "direct_basin_promotion"];
    case "model":
      return ["use_without_model_version", "use_outside_domain", "direct_basin_promotion"];
    case "experimental_dataset":
      return ["use_without_conditions", "use_without_instrument_metadata", "direct_basin_promotion"];
    case "computed_reference":
      return ["use_without_method_version", "treat_as_measurement", "direct_basin_promotion"];
    case "time_series_reference":
      return ["use_without_timestamp", "use_outside_temporal_validity", "direct_basin_promotion"];
    default:
      return ["route_without_audit", "direct_basin_promotion"];
  }
}

function normalizeOne(raw: AnyRecord, sourceName: string, sourceVersion: string): RegistryRecord {
  const status = normalizeStatus(raw.status ?? raw.exactness ?? raw.proof_status);
  const symbol = asString(raw.symbol ?? raw.display_symbol ?? raw.name, "unknown_symbol");
  const name = asString(raw.name ?? raw.title ?? symbol, symbol);
  const unit = asString(raw.unit, "1");
  const recordBasis = { sourceName, sourceVersion, symbol, name, value: raw.value ?? raw.exact_value ?? raw.formula ?? "" };
  const provenance_hash = hashJson({ raw, recordBasis });

  return {
    record_id: `${sourceName}:${symbol}`.replace(/[^A-Za-z0-9_.:-]/g, "_"),
    source_name: sourceName,
    source_version: sourceVersion,
    symbol,
    display_symbol: asString(raw.display_symbol ?? raw.symbol, symbol),
    name,
    value: asString(raw.value ?? raw.exact_value ?? raw.formula, ""),
    unit,
    unit_system: asString(raw.unit_system, "SI_or_contextual"),
    dimension: asString(raw.dimension, "unknown"),
    quantity_kind: asString(raw.quantity_kind ?? raw.forest_role, "unknown_quantity"),
    status,
    standard_uncertainty: raw.standard_uncertainty == null ? null : asString(raw.standard_uncertainty),
    relative_uncertainty: raw.relative_uncertainty == null ? null : asString(raw.relative_uncertainty),
    coverage: asString(raw.coverage, "global_or_unspecified"),
    conditions: asString(raw.conditions, "standard_or_unspecified"),
    source_uri: asString(raw.source_uri, "local_seed_pack"),
    provenance_hash,
    license_scope: asString(raw.license_scope, "seed_metadata"),
    audit_status: "seed",
    authority_weight: Number(raw.authority_weight ?? STATUS_WEIGHT[status]),
    forest_role: asString(raw.forest_role, "constant_anchor"),
    blocked_uses: Array.isArray(raw.blocked_uses) ? raw.blocked_uses.map(String) : blockedUsesFor(status),
    notes: asString(raw.notes ?? raw.exactness_note ?? raw.reason, ""),
  };
}

function normalizeAdapterBoundary(adapter: (typeof SOURCE_ADAPTERS)[number]): RegistryRecord {
  const blocked = makeBlockedRecord(adapter);
  const status = normalizeStatus(blocked.status);
  return {
    record_id: blocked.record_id,
    source_name: blocked.source_name,
    source_version: blocked.source_version,
    symbol: blocked.symbol,
    display_symbol: blocked.symbol,
    name: blocked.name,
    value: blocked.value,
    unit: blocked.unit,
    unit_system: blocked.unit_system,
    dimension: blocked.dimension,
    quantity_kind: blocked.quantity_kind,
    status,
    standard_uncertainty: blocked.standard_uncertainty,
    relative_uncertainty: blocked.relative_uncertainty,
    coverage: blocked.coverage,
    conditions: blocked.conditions,
    source_uri: blocked.source_uri,
    provenance_hash: blocked.provenance_hash,
    license_scope: blocked.license_scope,
    audit_status: blocked.audit_status,
    authority_weight: blocked.authority_weight,
    forest_role: blocked.forest_role,
    blocked_uses: blocked.blocked_uses,
    notes: `Source boundary from adapter ${adapter.id}. ${adapter.notes}`,
    adapter_id: adapter.id,
  };
}

function normalizeImportableAdapterBoundary(adapter: (typeof SOURCE_ADAPTERS)[number]): RegistryRecord {
  const body = { adapter_id: adapter.id, source_home: adapter.sourceHome, status: "adapter_registered" };
  return {
    record_id: `${adapter.id}:adapter_registered`,
    source_name: adapter.name,
    source_version: "adapter_registered_v0",
    symbol: adapter.id,
    display_symbol: adapter.id,
    name: `${adapter.name} adapter registration`,
    value: "adapter_registered_no_values_imported_yet",
    unit: "n/a",
    unit_system: "n/a",
    dimension: "n/a",
    quantity_kind: "source_adapter",
    status: normalizeStatus(adapter.defaultStatus),
    standard_uncertainty: null,
    relative_uncertainty: null,
    coverage: adapter.group,
    conditions: "Adapter registered; upstream values require explicit fetch/import/audit.",
    source_uri: adapter.sourceHome || "",
    provenance_hash: hashJson(body),
    license_scope: adapter.licenseScope,
    audit_status: "seed",
    authority_weight: AUTHORITY_WEIGHTS[adapter.authorityClass],
    forest_role: "measurement_source_adapter",
    blocked_uses: ["routing_as_measurement_value", "direct_basin_promotion", "claiming_database_import_before_adapter_run"],
    notes: adapter.notes,
    adapter_id: adapter.id,
  };
}

function extractRecordsFromPack(pack: AnyRecord): AnyRecord[] {
  const records: AnyRecord[] = [];
  for (const key of ["constants", "defining_constants", "exact_derived_from_defining_constants", "not_exact_after_2019"]) {
    const value = pack[key];
    if (Array.isArray(value)) records.push(...value as AnyRecord[]);
  }
  return records;
}

function dedupe(records: RegistryRecord[]): RegistryRecord[] {
  const byId = new Map<string, RegistryRecord>();
  for (const record of records) {
    const key = record.record_id;
    const existing = byId.get(key);
    if (!existing || record.authority_weight > existing.authority_weight) {
      byId.set(key, record);
    }
  }
  return [...byId.values()].sort((a, b) => a.record_id.localeCompare(b.record_id));
}

async function loadPack(path: string): Promise<{ pack: AnyRecord; path: string }> {
  const raw = await readFile(join(ROOT, path), "utf8");
  return { pack: JSON.parse(raw) as AnyRecord, path };
}

export async function buildConstantsRegistry(inputPaths = DEFAULT_INPUTS, outputPath = "research-stack/constants/constants_registry_v0.json") {
  const normalized: RegistryRecord[] = [];

  for (const inputPath of inputPaths) {
    const { pack } = await loadPack(inputPath);
    const sourceName = asString(pack.pack_id ?? pack.catalog_id ?? inputPath, inputPath);
    const sourceVersion = asString(pack.source_context && typeof pack.source_context === "object" ? (pack.source_context as AnyRecord).standard : pack.title, "v0");
    const records = extractRecordsFromPack(pack);
    for (const raw of records) normalized.push(normalizeOne(raw, sourceName, sourceVersion));
  }

  for (const adapter of SOURCE_ADAPTERS) {
    normalized.push(canImportNow(adapter) ? normalizeImportableAdapterBoundary(adapter) : normalizeAdapterBoundary(adapter));
  }

  const deduped = dedupe(normalized);
  const output = {
    registry_id: "constants_registry_v0",
    generated_utc: new Date().toISOString(),
    source_inputs: inputPaths,
    adapter_coverage: summarizeAdapterCoverage(),
    record_count: deduped.length,
    rule: "Exactness, uncertainty, source boundaries, and allowed-use limits are preserved. This registry does not promote basins by itself.",
    records: deduped,
  };

  const fullOut = join(ROOT, outputPath);
  await mkdir(dirname(fullOut), { recursive: true });
  await writeFile(fullOut, JSON.stringify(output, null, 2) + "\n", "utf8");
  return output;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  buildConstantsRegistry()
    .then((out) => {
      console.log(`Wrote constants registry with ${out.record_count} records.`);
      console.log(`Adapter count: ${out.adapter_coverage.adapter_count}`);
    })
    .catch((error) => {
      console.error(error);
      process.exit(1);
    });
}
