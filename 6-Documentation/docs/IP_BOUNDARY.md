# Solvent License Boundary Architecture

## The Problem
MIT-licensed software (PageIndex) integrated with proprietary IP (CFF, eigenmass, NUVMAP)
must be architected so the MIT license does NOT propagate to proprietary code.

## The Solution: Clean Module Boundary

```
/home/allaun/                                    ← Workspace root
├── third_party/                                 ← ALL MIT/LICENSE-FOREIGN CODE
│   └── pageindex/                               ← VectifyAI/PageIndex (MIT)
│       ├── LICENSE                              ← MIT license (UNTOUCHED)
│       ├── ...                                  ← MIT code (NEVER MODIFIED)
│       └── NOTICE                               ← Attribution notice
│
├── cff/                                         ← PROPRIETARY CODE
│   ├── core/
│   │   ├── __init__.py                          ← Proprietary header
│   │   ├── cff.py                               ← Proprietary header
│   │   ├── fingerprint.py                       ← Proprietary header
│   │   └── schema.py                            ← Proprietary header
│   ├── gpu/
│   │   └── eigenmass_engine.py                  ← Proprietary header
│   ├── adapter/                                 ← ADAPTER LAYER (Proprietary)
│   │   └── pageindex_adapter.py                 ← Interfaces with MIT code, proprietary itself
│   ├── nuvmap/
│   ├── ingestion/
│   └── ...
│
├── LICENSE                                      ← Proprietary global license
├── THIRD_PARTY_NOTICES.txt                      ← Lists ALL third-party licenses
└── IP_BOUNDARY.md                               ← This document
```

## Key Rules (Legally Defensible)

### 1. NEVER modify files inside third_party/
   - PageIndex source lives exactly as cloned
   - No patches, no inline changes, no forked copies
   - Configuration is done via env vars / config files OUTSIDE third_party/

### 2. Adapter layer NEVER includes MIT code
   - pageindex_adapter.py imports PageIndex as a library
   - Does NOT copy, paste, or inline MIT-licensed code
   - Contains ONLY proprietary glue logic

### 3. Proprietary modules NEVER import from MIT code directly
   - Only the adapter layer touches PageIndex
   - CFF core, eigenmass engine, NUVMAP engine remain clean
   - This prevents "derivative work" contamination

### 4. Third-party notices file is COMPLETE
   - Lists ALL foreign licenses, their terms, and attributions
   - Updated whenever a new third-party dep is added

### 5. Copyright headers on EVERY proprietary file
   - Standard header: "PROPRIETARY — ALL RIGHTS RESERVED"
   - Date, entity, and explicit prohibition of copying

## Why This Works

MIT license requires:
  1. Copyright notice included in copies of the MIT software → SATISFIED (third_party/ untouched)
  2. Permission notice included → SATISFIED (LICENSE file preserved)

MIT does NOT require:
  - Derivative works to be MIT-licensed
  - Combined works to be MIT-licensed
  - Proprietary code that uses MIT code to be disclosed

The adapter pattern ensures our code "uses" PageIndex (imports its API)
without "modifying" or "distributing" it in a way that triggers copyleft.

## Verification Checklist
- [ ] All third_party/ files retain original copyright headers
- [ ] All proprietary files have proprietary headers
- [ ] No MIT-licensed code copied into proprietary directories
- [ ] Adapter layer imports only, no inlining
- [ ] THIRD_PARTY_NOTICES.txt is current
- [ ] Root LICENSE file reflects proprietary status
