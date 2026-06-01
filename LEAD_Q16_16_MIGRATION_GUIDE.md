## Microstep Guide for Q16_16 Unification Migration

This guide provides precise steps for migrating any file from PhysicsScalar/ElectromagneticSpectrum to canonical FixedPoint Q16_16.

### 🔍 PRE-MIGRATION ASSESSMENT

1. **Check file dependencies:**
   ```bash
   cd /home/allaun/Research Stack
   grep -n "PhysicsScalar\|ElectromagneticSpectrum" 0-Core-Formalism/lean/Semantics/Semantics/FILENAME.lean
   ```

2. **Identify usage patterns:**
   - Type-only usage: `tension : PhysicsScalar.Q16_16` (simple migration)
   - Function usage: `PhysicsScalar.Q16_16.zero`, `mean3`, etc. (requires bridge)
   - Mixed usage: Both type and function calls

### 🔄 SIMPLE TYPE-ONLY MIGRATION

For files that only use Q16_16 as field types (like ManifoldStructures.lean):

**Step 1:** Update imports
```diff
-import Semantics.PhysicsScalar
+import Semantics.FixedPoint
```

**Step 2:** Update open statements  
```diff
-open Semantics.PhysicsScalar
+open Semantics.FixedPoint
```

**Step 3:** Test build
```bash
cd 0-Core-Formalism/lean/Semantics
lake build Semantics.FILENAME
```

### 🌉 FUNCTION-USING MIGRATION

For files that call PhysicsScalar functions:

**Step 1:** Add bridge import
```lean
import Semantics.PhysicsScalarBridge
```

**Step 2:** Replace specific function calls
```diff
-let value := PhysicsScalar.Q16_16.zero
+let value := Semantics.FixedPoint.Q16_16.zero

-let avg := PhysicsScalar.Q16_16.mean3 a b c  
+let avg := Semantics.PhysicsScalarBridge.add (Semantics.PhysicsScalarBridge.add a b) c
+let avg := Semantics.FixedPoint.Q16_16.ofRawInt ((avg_raw + 1) / 3)  -- manual conversion
```

**Step 3:** Use bridge for arithmetic
```diff
-let result := PhysicsScalar.Q16_16.add a b
+let result := Semantics.PhysicsScalarBridge.add a b
```

### ⚠️ COMMON COMPILATION ERRORS & FIXES

**Error:** `unknown identifier 'PhysicsScalar.Q16_16.zero'`
**Fix:** Replace with `Semantics.FixedPoint.Q16_16.zero` or use bridge

**Error:** `type mismatch PhysicsScalar.Q16_16 vs Q16_16`  
**Fix:** Ensure all references use the same Q16_16 variant throughout the file

**Error:** `unknown field 'tension'` 
**Fix:** The field name is the same; check that the import/open statements are correct

### 🧪 VERIFICATION STEPS

1. **Syntax check:**
   ```bash
   lake build Semantics.FILENAME --quiet
   ```

2. **Full build verification:**  
   ```bash
   lake build --quiet
   ```

3. **If build fails, common fixes:**
   - Check that all Q16_16 references use the same variant
   - Ensure PhysicsScalarBridge is imported when needed
   - Verify field names match between variants (they should be identical)

### 📋 MIGRATION PRIORITY LIST

**Phase 1 - Type-only files (easiest):**
1. ManifoldStructures.lean ✅ (completed)
2. Errors.lean
3. SensorField.lean (has complex dependencies - may need partial approach)

**Phase 2 - Simple function usage:**
4. BoundaryDynamics.lean
5. CausalGeometry.lean

**Phase 3 - Complex function usage:**
6. PhysicsEuclidean.lean (re-exports PhysicsScalar)
7. PhysicsLagrangian.lean (re-exports PhysicsScalar)

### 🛠️ BRIDGE FUNCTIONS AVAILABLE

In `Semantics.PhysicsScalarBridge`:
- `toFixedPoint : PhysicsScalar.Q16_16 → Semantics.FixedPoint.Q16_16`
- `fromFixedPoint : Semantics.FixedPoint.Q16_16 → PhysicsScalar.Q16_16`  
- `add`, `mul`, `sub` - bridged arithmetic operations

### 🚨 RISK MITIGATION

1. **Always backup:** `git stash` before starting
2. **Small changes:** Migrate one file at a time
3. **Test immediately:** Run `lake build` after each change
4. **Use bridge:** When in doubt, use PhysicsScalarBridge for compatibility
5. **Preserve semantics:** Pay attention to signed vs unsigned behavior differences

### ✅ SUCCESS CRITERIA

- File compiles with `lake build Semantics.FILENAME`  
- Full project builds with `lake build`
- No new type mismatch errors
- Functionality preserved (semantic equivalence maintained)

This microstep approach allows any LLM to systematically migrate files while maintaining build integrity and semantic correctness.