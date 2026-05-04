# ENE SessionArchive Schema Coverage Report

**Generated:** 2026-04-18  
**Source:** `ExtensionScaffold/ENE/SessionArchive.lean` vs imported records  
**Status:** Schema supports types, but migration uses defaults

---

## Schema Types (Defined in SessionArchive.lean)

### SessionSource (5 values)
| Value | Used? | Notes |
|-------|-------|-------|
| `userEditSession` | ❌ No | Interactive editing sessions |
| `antigravityCodingSession` | ❌ No | AG coding workflows |
| `ptosBootSession` | ✅ Yes | Graph address records |
| `eneSwarmSession` | ❌ No | ENE swarm runs |
| `archivedResearchSession` | ✅ Yes | Most imported records |

**Coverage:** 2/5 (40%)

### SessionRecordKind (5 values)
| Value | Used? | Notes |
|-------|-------|-------|
| `provenance` | ❌ No | Origin/lineage records |
| `bootAttestation` | ✅ Yes | Graph OS manifest |
| `swarmRun` | ❌ No | ENE swarm executions |
| `researchSession` | ✅ Yes | JSON catalogs |
| `ingestAttestation` | ✅ Yes | SQLite packages |

**Coverage:** 3/5 (60%)

### ArtifactRole (6 values)
| Value | Used? | Notes |
|-------|-------|-------|
| `created` | ❌ No | New artifacts |
| `modified` | ❌ No | Changed artifacts |
| `related` | ✅ Yes | All records (default) |
| `dependency` | ❌ No | Required components |
| `empiricalAnchor` | ❌ No | Hardware/physical refs |
| `codeback` | ❌ No | Derived code |

**Coverage:** 1/6 (17%) — **UNDERUTILIZED**

### ArtifactType (14 values)
| Value | Used? | Notes |
|-------|-------|-------|
| `rustModule` | ❌ No | *.rs files |
| `rustBinary` | ❌ No | Compiled Rust |
| `pythonTest` | ❌ No | *.py test scripts |
| `jsonSchema` | ❌ No | Schema definitions |
| `verilog` | ❌ No | *.v files |
| `vhdl` | ❌ No | *.vhd files |
| `boardLayout` | ❌ No | PCB files |
| `shader` | ❌ No | *.wgsl files |
| `document` | ❌ No | *.md specs |
| `script` | ❌ No | Shell scripts |
| `dataFile` | ✅ Yes | All records (default) |
| `chatSession` | ❌ No | Chat transcripts |
| `attestation` | ❌ No | Verification proofs |
| `other` | ❌ No | Uncategorized |

**Coverage:** 1/14 (7%) — **SEVERELY UNDERUTILIZED**

---

## Gap Analysis

### What's Missing in Migration

**Source JSON files contain:**
- `python_script` → Should map to `ArtifactType.pythonTest`
- `rust_module` → Should map to `ArtifactType.rustModule`
- `specification` → Should map to `ArtifactType.document`
- `theorem_document` → Should map to `ArtifactType.document`
- `academic_paper` → Should map to `ArtifactType.document`
- `video` → Should map to `ArtifactType.other`

**SessionArchive has examples of:**
- `regimeTrackerAndHardeningRecord` uses `.created`, `.modified` roles
- `sovereignStackBootRecord` uses `.empiricalAnchor` role
- `eneSwarmRunRecord` uses `.codeback` role
- Various artifact types: `.rustModule`, `.rustBinary`, `.pythonTest`, `.jsonSchema`

### Current Migration vs Schema Capability

```
Current:   { role := .related, artifactType := .dataFile, ... }
Capacity:  { role := .created/.modified/.dependency/.empiricalAnchor/.codeback,
             artifactType := .rustModule/.pythonTest/.document/.chatSession/... }
```

---

## Recommendations

### 1. Enhance Migration Script
Update `ene_import.py` to detect file types and set appropriate `ArtifactType`:

```python
type_map = {
    '.py': 'pythonTest',
    '.rs': 'rustModule',
    '.md': 'document',
    '.json': 'jsonSchema',
    '.toml': 'other',
}
```

### 2. Add Role Inference
Set `ArtifactRole` based on context:
- If file was imported from catalog → `.related`
- If file was created in session → `.created`
- If file is a dependency → `.dependency`

### 3. Add Missing SessionSource/Kind Combinations
If importing:
- Chat session transcripts → `SessionSource.eneSwarmSession`
- Code generation outputs → `SessionSource.antigravityCodingSession`

---

## Schema Extension Needed?

**No.** The existing schema in `SessionArchive.lean` covers all observed types:
- 5 SessionSource values
- 5 SessionRecordKind values  
- 6 ArtifactRole values
- 14 ArtifactType values

The issue is **migration fidelity**, not schema coverage.

---

## Files

| File | Purpose |
|------|---------|
| `SessionArchive.lean` | Schema definition (complete) |
| `ene_import.py` | Migration script (needs enhancement) |
| `AutoImported.lean` | Generated records (uses defaults) |

---

## Conclusion

✅ **Schema is sufficient** — All legacy database types can be represented  
⚠️ **Migration needs work** — Currently uses `dataFile`/`related` for everything  
💡 **Enhancement path clear** — Add type detection to `ene_import.py`
