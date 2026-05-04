# Measurement Registry Operating Doctrine

This registry exists because Research Stack must not pretend that mathematical or physical quantities are understood merely because they have names, symbols, or familiar-looking numbers.

## Prime rule

```text
A number is not knowledge until it carries:
source → unit → exactness → uncertainty → conditions → authority → allowed use
```

## Registry roles

The measurement registry separates these cases:

| Class | Meaning | Basin use |
|---|---|---|
| `exact` | Exact by definition, e.g. SI defining constants | Anchor only |
| `derived_exact` | Algebraically exact from exact constants | Anchor only |
| `mathematical` | Exact symbolic mathematical object | Symbolic anchor only |
| `measured` | Experimentally evaluated with uncertainty | Requires uncertainty + source |
| `conventional` | Defined reference convention | Reference-frame only |
| `environmental` | Local/site/context dependent | Blocked unless measured or modeled |
| `model` | Model output/reference model | Requires model version + domain validity |
| `standard_definition` | Standards-body definition/test method | Metadata or licensed content boundary |

## What this prevents

- Treating CODATA measured values as exact.
- Treating standard gravity as local gravity.
- Treating sea-level air density as a universal constant.
- Treating a diagram, paper, or LLM answer as proof.
- Treating a Wolfram answer as a proof object.
- Treating a pretty ratio as a law.

## Import pipeline

```text
source catalog
→ source adapter
→ raw record
→ normalized record
→ unit normalization
→ exactness classifier
→ uncertainty attachment
→ provenance hash
→ ENE receipt
→ constants_registry.json
→ Semantic Number Pattern Search
→ weighted route candidates
```

## Human-safe operating mode

When the system does not know, it must say one of:

```text
HOLD: source known, value not audited
HOLD: exactness unknown
HOLD: uncertainty missing
HOLD: local conditions missing
HOLD: unit conversion unresolved
SCAR: previously misused as exact
QUARANTINE: region requires separate verification
```

## Authority hierarchy

```text
Graph.lean = canonical graph/proof authority
SI definitions = exact metrological anchors
CODATA/NIST/BIPM/IAU/etc. = reference authority with source-specific uncertainty rules
ENE = provenance/archive authority
Wolfram = computational witness only
Neo4j = candidate topology only
Notion/Airtable/Drive/Obsidian = mirrors/registries/workbenches
Ace/Mermaid/GraphML = projections/transports only
```

## Required fields before a value can affect routing

Every value that enters routing must carry:

```yaml
record_id:
source_name:
source_version:
symbol:
name:
value:
unit:
dimension:
quantity_kind:
status:
standard_uncertainty:
relative_uncertainty:
coverage:
conditions:
source_uri:
provenance_hash:
license_scope:
audit_status:
authority_weight:
forest_role:
blocked_uses:
```

## Required fields before real-world simulation use

Real-world extreme-resolution simulation also requires:

```yaml
temperature:
pressure:
humidity:
altitude:
latitude:
longitude:
time_standard:
reference_frame:
material_state:
instrument_or_source:
calibration_status:
uncertainty_model:
```

If those are missing, the route remains HOLD.
