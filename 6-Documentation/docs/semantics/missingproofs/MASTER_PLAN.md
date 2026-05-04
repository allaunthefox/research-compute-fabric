# MASTER PLAN — Complete Research Stack Remaining Work

**Document ID:** MASTER_PLAN_2026-04-19  
**Authority:** AGENTS.md §9 — Research prioritization  
**Scope:** All remaining P0, P1, P2, and Layer M work

---

## Executive Summary

**Current Status:** 6 assignments complete, computational verification framework established  
**Remaining Work:** Documentation updates, symbolic proof generalization, Layer M expansion  
**Estimated Effort:** 4-6 weeks for complete closure  

---

## Phase 0: Documentation Reconciliation (1-2 days)

### Problem
Documentation (RESEARCH_ROADMAP, MATH_MODEL_MAP) lists items as "OPEN" that are actually **computationally verified** with complete frameworks.

### Action Items
| File | Task | Lines | Status |
|------|------|-------|--------|
| `RESEARCH_ROADMAP.md` | Update P0 missingLinkODE status | ~338-339 | ⏳ Pending |
| `RESEARCH_ROADMAP.md` | Update P1 General Proofs section | ~339 | ⏳ Pending |
| `RESEARCH_ROADMAP.md` | Mark Key Lemmas as complete | ~370-376 | ⏳ Pending |
| `MATH_MODEL_MAP.md` | Update theorems 122-124 status | ~356-358 | ⏳ Pending |
| `MATH_MODEL_MAP.md` | Update theorem 131 status | ~365 | ⏳ Pending |
| `MATH_MODEL_MAP_BY_DOMAIN.md` | Sync with main map | All | ⏳ Pending |

### Deliverable
All documentation accurately reflects **computationally verified + framework established** status for completed work.

---

## Phase 1: Symbolic Proof Generalization (3-4 weeks)

### Current State
All P0/P1/P2 theorems have **computational verification** via `native_decide`.  
**Gap:** Symbolic proofs for unbounded/general cases (no concrete values).

### Symbolic Proof Targets

#### Tier 1: Critical for CAI Analysis (1 week)
| Theorem | Domain | Approach | Difficulty |
|---------|--------|----------|------------|
| `caiBounds` (162) upper bound | AM-GM | Real→Float transfer | Medium |
| `rscuSumSynonymous` symbolic | Enumeration | General fold proof | Hard |
| `speciesBetterThanGeneric` | Entropy | Real analysis | Hard |

#### Tier 2: P1 Geometry (1-2 weeks)
| Theorem | Domain | Approach | Difficulty |
|---------|--------|----------|------------|
| `tipCoordinateMassResonance` general | Diophantine | Hyperbola parametrization | Research |
| `tipCoordinateMirrorResonance` general | Integer arith | Symmetric solution space | Research |
| `fortyFiveLineFactorRevelation` general | Number theory | Fermat's theorem formalization | Research |

#### Tier 3: P0 ODE (1-2 weeks)
| Theorem | Domain | Approach | Difficulty |
|---------|--------|----------|------------|
| `missingLinkODE` general existence | Analysis | Picard iteration convergence | Research |
| `missingLinkODEUniqueness` symbolic | Lipschitz | Contraction mapping | Hard |

### Research Strategy
1. **Real→Float Transfer:** Prove in ℝ, transfer to Float for representable values
2. **Q16_16 Alternative:** Convert Float-heavy proofs to fixed-point (AGENTS.md compliance)
3. **Constructive Witnesses:** Provide explicit algorithms (Euler, Fermat) rather than pure existence

---

## Phase 2: Layer M Model Expansion (2-3 weeks)

### Current State
- **Layer M proven:** 30 models (44% auto-proven)
- **Remaining:** 38 models from 68 total
- **Approach:** `native_decide` for concrete values, pattern matching for families

### Remaining Model Categories

#### Category A: Enumeration-Based (Week 1)
| Model Range | Count | Approach | Status |
|-------------|-------|----------|--------|
| Codon/AA mappings | ~8 | Exhaustive enumeration | Ready |
| Species variants | ~5 | Computational per-species | Ready |
| Start/stop variants | ~3 | Case analysis | Ready |

#### Category B: Float Inequalities (Week 2)
| Model Range | Count | Approach | Status |
|-------------|-------|----------|--------|
| CAI bounds variants | ~12 | Real analysis proof | Needs work |
| Entropy comparisons | ~6 | AM-GM + monotonicity | Needs work |
| Thermodynamic bounds | ~4 | Conservation laws | Ready |

#### Category C: Research-Level (Week 3)
| Model Range | Count | Approach | Status |
|-------------|-------|----------|--------|
| ODE existence variants | ~3 | Euler/Picard framework | Framework ready |
| Braid topology | ~2 | Combinatorial | Open |
| Factorization geometry | ~2 | Number theory | Open |

---

## Phase 3: Infrastructure & Polish (1 week)

### Code Quality
| Task | File | Effort | Status |
|------|------|--------|--------|
| Remove all `sorry` placeholders | AVMR.lean | 1 day | ⏳ Critical |
| Add `#eval` witnesses for all theorems | AVMR.lean | 2 days | ⏳ Needed |
| Standardize theorem documentation | AVMR.lean | 1 day | ⏳ Formatting |
| Lake build zero warnings | All | Ongoing | 🔄 Active |

### Testing
| Task | Coverage | Status |
|------|----------|--------|
| `lake build` passes | 100% | ✅ Current |
| `native_decide` theorems verified | All concrete | ✅ Current |
| Symbolic proof regression tests | New proofs | ⏳ Needed |

---

## Resource Allocation

### Subagent Assignments (Proposed)
| Subagent | Phase | Focus Area | Duration |
|----------|-------|------------|----------|
| **Cascade** | Phase 0 | Documentation reconciliation | 2 days |
| **Ω (ODE)** | Phase 1, Tier 3 | ODE general existence | 1-2 weeks |
| **α₁** | Phase 1, Tier 2 | Hyperbola geometry | 1-2 weeks |
| **α₂** | Phase 1, Tier 2 | Mirror resonance general | 1 week |
| **α₃** | Phase 1, Tier 2 | Fermat factorization | 1-2 weeks |
| **β₁** | Phase 2, Cat A | Enumeration proofs | 1 week |
| **β₂** | Phase 2, Cat B | Float inequalities | 1-2 weeks |
| **β₃** | Phase 2, Cat C | Research-level models | 1-2 weeks |
| **δ (Docs)** | Phase 3 | Code quality, `#eval` | 1 week |

### Dependency Graph
```
Phase 0 (Docs)
     │
     ├──────┬────────┬────────┐
     │      │        │        │
Phase 1   Tier 1   Tier 2   Tier 3  (Symbolic - parallel)
     │      │        │        │
     └──────┴────────┴────────┘
              │
         Phase 2 (Layer M - parallel)
              │
         Phase 3 (Polish)
```

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Symbolic proofs intractable | Medium | High | Stay with computational + framework |
| Float→ℝ transfer fails | Low | Medium | Use Q16_16 fixed-point |
| Lake build breaks | Low | High | CI pipeline, incremental builds |
| Research-level proofs require external help | High | Medium | Document gaps, flag for experts |

---

## Success Criteria

**Phase 0:** All documentation reflects actual completion status  
**Phase 1:** All P0/P1 theorems have either symbolic proof OR documented framework  
**Phase 2:** Layer M reaches 70%+ auto-proven (47+ models from 68)  
**Phase 3:** Zero `sorry`, all theorems have computational or symbolic proof  

---

## Timeline Summary

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| 0: Documentation | 1-2 days | Accurate status tracking |
| 1: Symbolic Generalization | 3-4 weeks | Theorems with general proofs |
| 2: Layer M Expansion | 2-3 weeks | 47+ models proven |
| 3: Infrastructure | 1 week | Code quality, zero `sorry` |
| **Total** | **6-8 weeks** | **Research stack complete** |

---

## Immediate Next Steps

1. **Today:** Begin Phase 0 — Update RESEARCH_ROADMAP.md to reflect actual status
2. **This Week:** Assign subagents to Phase 1 tiers based on expertise
3. **Next Week:** Begin Phase 2 Layer M expansion with enumeration-based models

---

*Plan Version: 1.0*  
*Created: 2026-04-19*  
*Authority: AGENTS.md §9*  
*Status: APPROVED FOR EXECUTION*
