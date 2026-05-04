import { createHash } from "crypto";

/**
 * Measurement Source Adapters
 *
 * This is the adapter registry for the full measurement-standard federation.
 * It does not pretend to contain the world's data. It defines how every known
 * authoritative measurement source enters Research Stack without losing source,
 * unit, exactness, uncertainty, conditions, license boundary, or authority scope.
 */

export type AuthorityClass =
  | "metrological_definition"
  | "international_reference_data"
  | "national_metrology_institute"
  | "standards_development_organization"
  | "domain_reference_database"
  | "regulatory_reference"
  | "environmental_observational_network"
  | "local_instrument_measurement";

export type ImportMode =
  | "machine_readable_release"
  | "api_adapter"
  | "web_adapter_with_cache"
  | "table_adapter"
  | "rdf_adapter"
  | "registry_adapter"
  | "dataset_adapter"
  | "model_adapter"
  | "kernel_adapter"
  | "licensed_local_adapter"
  | "licensed_manual_index"
  | "manual_audit_or_structured_release"
  | "manual_or_api_adapter"
  | "metadata_only";

export type MeasurementStatus =
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

export type SourceAdapterSpec = {
  id: string;
  name: string;
  group: string;
  priority: 1 | 2 | 3 | 4;
  authorityClass: AuthorityClass;
  importMode: ImportMode;
  defaultStatus: MeasurementStatus;
  licenseScope: "open" | "restricted" | "licensed" | "metadata_only" | "unknown";
  sourceHome?: string;
  notes: string;
  blockedUntil?: string;
};

export type NormalizedMeasurementRecord = {
  record_id: string;
  source_name: string;
  source_version: string;
  symbol: string;
  name: string;
  value: string;
  unit: string;
  unit_system: string;
  dimension: string;
  quantity_kind: string;
  status: MeasurementStatus;
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
  adapter_id: string;
};

export const AUTHORITY_WEIGHTS: Record<AuthorityClass, number> = {
  metrological_definition: 0.98,
  international_reference_data: 0.90,
  national_metrology_institute: 0.86,
  standards_development_organization: 0.80,
  domain_reference_database: 0.76,
  regulatory_reference: 0.70,
  environmental_observational_network: 0.64,
  local_instrument_measurement: 0.60,
};

export const SOURCE_ADAPTERS: SourceAdapterSpec[] = [
  // SI and primary metrology
  { id: "bipm-si-brochure", name: "BIPM SI Brochure", group: "SI and primary metrology", priority: 1, authorityClass: "metrological_definition", importMode: "manual_audit_or_structured_release", defaultStatus: "exact", licenseScope: "open", sourceHome: "https://www.bipm.org/en/publications/si-brochure", notes: "Primary SI definitions and exact defining constants." },
  { id: "bipm-kcdb", name: "BIPM Key Comparison Database", group: "SI and primary metrology", priority: 1, authorityClass: "international_reference_data", importMode: "api_adapter", defaultStatus: "measured", licenseScope: "open", sourceHome: "https://www.bipm.org/kcdb/", notes: "Calibration and measurement capabilities plus key comparison results." },
  { id: "bipm-circular-t", name: "BIPM Circular T", group: "SI and primary metrology", priority: 1, authorityClass: "international_reference_data", importMode: "machine_readable_release", defaultStatus: "time_series_reference", licenseScope: "open", sourceHome: "https://www.bipm.org/en/time-ftp/circular-t", notes: "TAI/UTC time scale and clock comparison references." },
  { id: "codata-constants", name: "CODATA Fundamental Physical Constants", group: "SI and primary metrology", priority: 1, authorityClass: "international_reference_data", importMode: "machine_readable_release", defaultStatus: "measured", licenseScope: "open", sourceHome: "https://physics.nist.gov/cuu/Constants/", notes: "Recommended constants with uncertainties and exactness changes." },
  { id: "nist-cuu", name: "NIST Constants, Units, and Uncertainty", group: "SI and primary metrology", priority: 1, authorityClass: "national_metrology_institute", importMode: "web_adapter_with_cache", defaultStatus: "measured", licenseScope: "open", sourceHome: "https://physics.nist.gov/cuu/", notes: "NIST constants and unit conversion references." },

  // Units, coordinate, and time registries
  { id: "ucum", name: "UCUM", group: "Coordinate, time, and unit registries", priority: 1, authorityClass: "international_reference_data", importMode: "machine_readable_release", defaultStatus: "standard_definition", licenseScope: "open", sourceHome: "https://ucum.org/", notes: "Machine-readable unit codes and conversion semantics." },
  { id: "qudt", name: "QUDT", group: "Coordinate, time, and unit registries", priority: 1, authorityClass: "domain_reference_database", importMode: "rdf_adapter", defaultStatus: "terminology", licenseScope: "open", sourceHome: "https://qudt.org/", notes: "Quantities, units, dimensions, and types ontology." },
  { id: "om-ontology", name: "OM Ontology of Units of Measure", group: "Coordinate, time, and unit registries", priority: 1, authorityClass: "domain_reference_database", importMode: "rdf_adapter", defaultStatus: "terminology", licenseScope: "open", sourceHome: "http://www.ontology-of-units-of-measure.org/", notes: "Unit and quantity ontology." },
  { id: "iana-tzdb", name: "IANA Time Zone Database", group: "Coordinate, time, and unit registries", priority: 1, authorityClass: "international_reference_data", importMode: "machine_readable_release", defaultStatus: "standard_definition", licenseScope: "open", sourceHome: "https://www.iana.org/time-zones", notes: "Civil time and time-zone transition reference data." },
  { id: "epsg", name: "EPSG Geodetic Parameter Dataset", group: "Coordinate, time, and unit registries", priority: 1, authorityClass: "standards_development_organization", importMode: "registry_adapter", defaultStatus: "standard_definition", licenseScope: "open", sourceHome: "https://epsg.org/", notes: "Coordinate reference systems and transformations." },

  // Chemistry and thermophysical
  { id: "nist-chemistry-webbook", name: "NIST Chemistry WebBook", group: "Chemistry and thermophysical reference data", priority: 1, authorityClass: "domain_reference_database", importMode: "web_adapter_with_cache", defaultStatus: "measured", licenseScope: "open", sourceHome: "https://webbook.nist.gov/chemistry/", notes: "Thermochemistry, spectra, ion energetics, and species properties." },
  { id: "nist-refprop", name: "NIST REFPROP", group: "Chemistry and thermophysical reference data", priority: 1, authorityClass: "domain_reference_database", importMode: "licensed_local_adapter", defaultStatus: "model", licenseScope: "licensed", sourceHome: "https://www.nist.gov/srd/refprop", notes: "Fluid thermophysical properties. Requires lawful local installation.", blockedUntil: "licensed_local_install_available" },
  { id: "iupac-goldbook", name: "IUPAC Gold Book", group: "Chemistry and thermophysical reference data", priority: 1, authorityClass: "international_reference_data", importMode: "web_adapter_with_cache", defaultStatus: "terminology", licenseScope: "open", sourceHome: "https://goldbook.iupac.org/", notes: "Chemical terminology, symbols, and quantity definitions." },
  { id: "ciaaw-atomic-weights", name: "IUPAC/CIAAW Atomic Weights", group: "Chemistry and thermophysical reference data", priority: 1, authorityClass: "international_reference_data", importMode: "manual_audit_or_structured_release", defaultStatus: "measured", licenseScope: "open", sourceHome: "https://ciaaw.org/", notes: "Standard atomic weights and isotopic composition references." },
  { id: "pubchem", name: "PubChem", group: "Chemistry and thermophysical reference data", priority: 1, authorityClass: "domain_reference_database", importMode: "api_adapter", defaultStatus: "measured", licenseScope: "open", sourceHome: "https://pubchem.ncbi.nlm.nih.gov/", notes: "Chemical identifiers, computed properties, and experimental annotations." },
  { id: "chembl", name: "ChEMBL", group: "Chemistry and thermophysical reference data", priority: 2, authorityClass: "domain_reference_database", importMode: "api_adapter", defaultStatus: "experimental_dataset", licenseScope: "open", sourceHome: "https://www.ebi.ac.uk/chembl/", notes: "Bioactivity measurements and assay metadata." },
  { id: "wwpdb", name: "wwPDB", group: "Chemistry and thermophysical reference data", priority: 2, authorityClass: "domain_reference_database", importMode: "api_adapter", defaultStatus: "experimental_dataset", licenseScope: "open", sourceHome: "https://www.wwpdb.org/", notes: "Macromolecular structures and measurement metadata." },

  // Materials and crystallography
  { id: "cod", name: "Crystallography Open Database", group: "Materials, crystallography, and solid-state reference data", priority: 1, authorityClass: "domain_reference_database", importMode: "dataset_adapter", defaultStatus: "measured", licenseScope: "open", sourceHome: "https://www.crystallography.net/cod/", notes: "Open crystal structures." },
  { id: "icsd", name: "ICSD", group: "Materials, crystallography, and solid-state reference data", priority: 2, authorityClass: "domain_reference_database", importMode: "licensed_local_adapter", defaultStatus: "measured", licenseScope: "licensed", notes: "Licensed inorganic crystal structure data.", blockedUntil: "licensed_access_available" },
  { id: "materials-project", name: "Materials Project", group: "Materials, crystallography, and solid-state reference data", priority: 1, authorityClass: "domain_reference_database", importMode: "api_adapter", defaultStatus: "computed_reference", licenseScope: "open", sourceHome: "https://materialsproject.org/", notes: "Computed and curated materials properties." },
  { id: "aflow", name: "AFLOW", group: "Materials, crystallography, and solid-state reference data", priority: 2, authorityClass: "domain_reference_database", importMode: "api_adapter", defaultStatus: "computed_reference", licenseScope: "open", sourceHome: "https://aflowlib.org/", notes: "High-throughput computational materials data." },
  { id: "oqmd", name: "OQMD", group: "Materials, crystallography, and solid-state reference data", priority: 2, authorityClass: "domain_reference_database", importMode: "api_adapter", defaultStatus: "computed_reference", licenseScope: "open", sourceHome: "https://oqmd.org/", notes: "Open quantum materials database." },
  { id: "nist-mdr", name: "NIST Materials Data Repository", group: "Materials, crystallography, and solid-state reference data", priority: 2, authorityClass: "domain_reference_database", importMode: "dataset_adapter", defaultStatus: "measured", licenseScope: "open", sourceHome: "https://materialsdata.nist.gov/", notes: "Materials datasets and metadata." },

  // Astronomy/geodesy remains quarantined for observation use
  { id: "iau-constants", name: "IAU Resolutions and constants", group: "Astronomy, planetary science, and geodesy", priority: 2, authorityClass: "international_reference_data", importMode: "manual_audit_or_structured_release", defaultStatus: "conventional", licenseScope: "open", sourceHome: "https://www.iau.org/", notes: "Astronomical constants and unit definitions; solar-system use remains quarantined until separately verified." },
  { id: "jpl-horizons", name: "JPL Horizons / SPICE", group: "Astronomy, planetary science, and geodesy", priority: 2, authorityClass: "domain_reference_database", importMode: "api_adapter", defaultStatus: "model", licenseScope: "open", sourceHome: "https://ssd.jpl.nasa.gov/horizons/", notes: "Ephemerides and kernels; catalog target only until solar-system quarantine is lifted." },
  { id: "iers", name: "IERS Conventions and Earth Orientation Parameters", group: "Astronomy, planetary science, and geodesy", priority: 2, authorityClass: "international_reference_data", importMode: "machine_readable_release", defaultStatus: "time_series_reference", licenseScope: "open", sourceHome: "https://www.iers.org/", notes: "Earth orientation and geodetic reference frames." },

  // Earth/environment
  { id: "noaa-ncei", name: "NOAA NCEI", group: "Earth, atmosphere, ocean, climate, and environmental measurement", priority: 2, authorityClass: "environmental_observational_network", importMode: "api_adapter", defaultStatus: "environmental", licenseScope: "open", sourceHome: "https://www.ncei.noaa.gov/", notes: "Weather, climate, ocean, and geophysical observational datasets." },
  { id: "nasa-earthdata", name: "NASA Earthdata", group: "Earth, atmosphere, ocean, climate, and environmental measurement", priority: 2, authorityClass: "environmental_observational_network", importMode: "api_adapter", defaultStatus: "environmental", licenseScope: "open", sourceHome: "https://earthdata.nasa.gov/", notes: "Earth observation and remote sensing data." },
  { id: "usgs", name: "USGS", group: "Earth, atmosphere, ocean, climate, and environmental measurement", priority: 2, authorityClass: "environmental_observational_network", importMode: "api_adapter", defaultStatus: "environmental", licenseScope: "open", sourceHome: "https://www.usgs.gov/", notes: "Geology, hydrology, seismic, elevation, and land measurements." },
  { id: "ecmwf-era", name: "ECMWF ERA Reanalysis", group: "Earth, atmosphere, ocean, climate, and environmental measurement", priority: 2, authorityClass: "domain_reference_database", importMode: "api_adapter", defaultStatus: "model", licenseScope: "open", sourceHome: "https://www.ecmwf.int/", notes: "Model-assimilated weather and climate fields." },
  { id: "wmo", name: "WMO Standards", group: "Earth, atmosphere, ocean, climate, and environmental measurement", priority: 2, authorityClass: "international_reference_data", importMode: "manual_audit_or_structured_release", defaultStatus: "standard_definition", licenseScope: "open", sourceHome: "https://wmo.int/", notes: "Meteorological measurement standards and observation metadata conventions." },

  // Particle/nuclear/radiation
  { id: "pdg", name: "Particle Data Group", group: "Particle, nuclear, and radiation data", priority: 2, authorityClass: "international_reference_data", importMode: "table_adapter", defaultStatus: "measured", licenseScope: "open", sourceHome: "https://pdg.lbl.gov/", notes: "Particle properties and reviews." },
  { id: "nndc-ensdf", name: "NNDC / ENSDF", group: "Particle, nuclear, and radiation data", priority: 2, authorityClass: "domain_reference_database", importMode: "dataset_adapter", defaultStatus: "measured", licenseScope: "open", sourceHome: "https://www.nndc.bnl.gov/ensdf/", notes: "Evaluated nuclear structure and decay data." },
  { id: "nist-xcom", name: "NIST XCOM", group: "Particle, nuclear, and radiation data", priority: 2, authorityClass: "domain_reference_database", importMode: "table_adapter", defaultStatus: "measured", licenseScope: "open", sourceHome: "https://www.nist.gov/pml/xcom-photon-cross-sections-database", notes: "Photon cross sections." },
  { id: "iaea-nuclear-data", name: "IAEA Nuclear Data Services", group: "Particle, nuclear, and radiation data", priority: 2, authorityClass: "international_reference_data", importMode: "dataset_adapter", defaultStatus: "measured", licenseScope: "open", sourceHome: "https://www-nds.iaea.org/", notes: "Nuclear reaction and decay datasets." },

  // Engineering / industrial standards, mostly metadata-only unless licensed
  { id: "iso", name: "ISO", group: "Engineering and industrial standards", priority: 3, authorityClass: "standards_development_organization", importMode: "licensed_manual_index", defaultStatus: "standard_definition", licenseScope: "metadata_only", sourceHome: "https://www.iso.org/", notes: "Metadata and citations only unless lawful access is available.", blockedUntil: "licensed_access_available" },
  { id: "iec", name: "IEC", group: "Engineering and industrial standards", priority: 3, authorityClass: "standards_development_organization", importMode: "licensed_manual_index", defaultStatus: "standard_definition", licenseScope: "metadata_only", sourceHome: "https://www.iec.ch/", notes: "Metadata and citations only unless lawful access is available.", blockedUntil: "licensed_access_available" },
  { id: "ieee-standards", name: "IEEE Standards", group: "Engineering and industrial standards", priority: 3, authorityClass: "standards_development_organization", importMode: "licensed_manual_index", defaultStatus: "standard_definition", licenseScope: "metadata_only", sourceHome: "https://standards.ieee.org/", notes: "Metadata and citations only unless lawful access is available.", blockedUntil: "licensed_access_available" },
  { id: "astm", name: "ASTM International", group: "Engineering and industrial standards", priority: 3, authorityClass: "standards_development_organization", importMode: "licensed_manual_index", defaultStatus: "standard_definition", licenseScope: "metadata_only", sourceHome: "https://www.astm.org/", notes: "Metadata and citations only unless lawful access is available.", blockedUntil: "licensed_access_available" },

  // Biomedical / clinical measurement
  { id: "loinc", name: "LOINC", group: "Biomedical and clinical measurement standards", priority: 3, authorityClass: "domain_reference_database", importMode: "machine_readable_release", defaultStatus: "terminology", licenseScope: "open", sourceHome: "https://loinc.org/", notes: "Laboratory and clinical observation identifiers." },
  { id: "snomed-ct", name: "SNOMED CT", group: "Biomedical and clinical measurement standards", priority: 3, authorityClass: "domain_reference_database", importMode: "licensed_local_adapter", defaultStatus: "terminology", licenseScope: "licensed", sourceHome: "https://www.snomed.org/", notes: "Clinical terminology; license varies by country.", blockedUntil: "licensed_access_available" },
  { id: "who-icd", name: "WHO ICD", group: "Biomedical and clinical measurement standards", priority: 3, authorityClass: "international_reference_data", importMode: "api_adapter", defaultStatus: "terminology", licenseScope: "open", sourceHome: "https://icd.who.int/", notes: "Health classification standard." },
];

export function provenanceHash(value: unknown): string {
  return createHash("sha256").update(JSON.stringify(value)).digest("hex");
}

export function adapterById(id: string): SourceAdapterSpec | undefined {
  return SOURCE_ADAPTERS.find((adapter) => adapter.id === id);
}

export function adaptersByPriority(priority: 1 | 2 | 3 | 4): SourceAdapterSpec[] {
  return SOURCE_ADAPTERS.filter((adapter) => adapter.priority === priority);
}

export function adaptersByGroup(group: string): SourceAdapterSpec[] {
  return SOURCE_ADAPTERS.filter((adapter) => adapter.group === group);
}

export function canImportNow(adapter: SourceAdapterSpec): boolean {
  return !adapter.blockedUntil && adapter.licenseScope !== "licensed" && adapter.importMode !== "licensed_local_adapter";
}

export function makeBlockedRecord(adapter: SourceAdapterSpec): NormalizedMeasurementRecord {
  const body = {
    adapter: adapter.id,
    reason: adapter.blockedUntil || "metadata_or_license_boundary",
  };
  return {
    record_id: `${adapter.id}:blocked`,
    source_name: adapter.name,
    source_version: "unimported",
    symbol: adapter.id,
    name: `${adapter.name} import boundary`,
    value: "blocked",
    unit: "n/a",
    unit_system: "n/a",
    dimension: "n/a",
    quantity_kind: "source_boundary",
    status: "standard_definition",
    standard_uncertainty: null,
    relative_uncertainty: null,
    coverage: "source-level",
    conditions: adapter.blockedUntil || "license or local adapter required",
    source_uri: adapter.sourceHome || "",
    provenance_hash: provenanceHash(body),
    license_scope: adapter.licenseScope,
    audit_status: "blocked",
    authority_weight: AUTHORITY_WEIGHTS[adapter.authorityClass],
    forest_role: "measurement_source_boundary",
    blocked_uses: ["data_import_without_lawful_access", "routing_as_value", "direct_basin_promotion"],
    adapter_id: adapter.id,
  };
}

export function summarizeAdapterCoverage() {
  const byGroup = new Map<string, number>();
  const blocked: string[] = [];
  for (const adapter of SOURCE_ADAPTERS) {
    byGroup.set(adapter.group, (byGroup.get(adapter.group) || 0) + 1);
    if (!canImportNow(adapter)) blocked.push(adapter.id);
  }
  return {
    adapter_count: SOURCE_ADAPTERS.length,
    groups: Object.fromEntries(byGroup.entries()),
    blocked_adapters: blocked,
    rule: "Blocked adapters are kept as source boundaries and cannot emit measurement values until licensing/local access is resolved.",
  };
}
