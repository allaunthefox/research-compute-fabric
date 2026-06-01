Q16_16 Type Unification - Analysis and Plan
=========================================

## Current State

There are 6 distinct Q16_16 type definitions causing fragmentation:

1. **Canonical**: `Semantics.FixedPoint.Q16_16` (Int subtype) - Used by ~421 files
2. **PhysicsScalar**: `Semantics.PhysicsScalar.Q16_16` (UInt32) - Used by 27 files
3. **ElectromagneticSpectrum**: `Semantics.ElectromagneticSpectrum.Q16_16` (UInt32) - Used by 17 files
4. **OTOM**: `external/OTOM/FixedPoint.Q16_16` (struct UInt32) - Standalone
5. **RcloneIntegration**: `Semantics.RcloneIntegration.Q16_16` (struct Int) - 3 files
6. **MetaManifoldProver**: `Semantics.MetaManifoldProver.Q16_16` (Int) - 0 files

## Semantic Differences

The main issue is semantic incompatibility:
- **Canonical FixedPoint**: Signed Int arithmetic with proper saturation
- **PhysicsScalar**: Unsigned UInt32 arithmetic with different overflow behavior
- **ElectromagneticSpectrum**: Minimal UInt32 subset

## Completed Work

1. **Created PhysicsScalarBridge.lean** - Compatibility layer for migration
2. **Created Q16_16_Unification_Demo.lean** - Demonstration of unification approach
3. **Analyzed migration scope** - Identified 27 PhysicsScalar + 17 ElectromagneticSpectrum consumers

## Migration Plan

### Phase 1: Compatibility Layer (DONE)
- ✅ PhysicsScalarBridge.lean created with conversion functions

### Phase 2: Incremental Migration
- Start with simple files that only use Q16_16 types (not functions)
- Progress to files using arithmetic operations
- Use bridge functions during transition

### Phase 3: Eliminate Duplicates
- Remove PhysicsScalar.lean once all consumers migrated
- Remove ElectromagneticSpectrum.lean
- Update all imports to use canonical Semantics.FixedPoint.Q16_16

## Risk Mitigation

1. **Semantic Incompatibility**: Bridge provides conversion but behavior may differ
2. **Proof Validity**: Existing proofs may need verification against canonical semantics
3. **Build Breakage**: Incremental approach minimizes disruption

## Benefits

- Single source of truth for Q16_16 arithmetic and proofs
- Eliminate code duplication across 6+ variants
- Centralize all Q16_16-related lemmas and theorems
- Simplify maintenance and future development
- Reduce cognitive load for developers