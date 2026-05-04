# Hutter Prize & Signal Policy: Testing Specification

This document consolidates the original prompts and logic used to formalize the Research Stack's compression validation and dynamic routing.

**Last Updated:** 2026-04-27
**Status:** Testing specification reference

## 1. Hutter Prize: Minimal Validation Path
To get usable data for the pipeline without synthetic artifacts:

### Setup
1. **Clone Dataset**: `git clone https://huggingface.co/datasets/leloy/enwik8`
2. **Pull Shard**: `git lfs pull --include="test-00000-of-00002.parquet"`
3. **Extraction**:
   ```python
   import pyarrow.parquet as pq
   table = pq.read_table("test-00000-of-00002.parquet")
   rows = table["input_ids"]
   windows = rows[:1000] # each window is 128 bytes
   data = [list(w) for w in windows]
   ```

### Sanity Metrics
- `cells_per_window` ≈ 64 (pack bytes → 4-bit Cell)
- `distinct_cells` << `total_cells`
- `distinct_signatures` << `distinct_cells`
- `repeated_patches` > 0
- `admissible_ratio` ~ 1.0

---

## 2. Signal Policy Logic
Make signal data first-class as policy input without letting it touch truth.

### Dynamic Transition Law
$$S_{t+1} = apply(route(sig(S_t), signalBand_t, priority_t))$$

### Core Implementation (Lean 4)
```lean
namespace ExtensionScaffold.Compression.SignalPolicy

inductive SignalBand where
  | quiet | active | stressed | extreme

def SignalBand.weight : SignalBand -> Float
  | .quiet => 0.0 | .active => 1.0 | .stressed => 2.0 | .extreme => 3.0

def policyOfBand : SignalBand -> SignalPolicy
  | .quiet    => { exploreBias := 0.0, tunnelBias := 0.0, promoteBias := 1.0, gossipBias := 0.0 }
  | .active   => { exploreBias := 0.5, tunnelBias := 0.5, promoteBias := 0.5, gossipBias := 0.5 }
  | .stressed => { exploreBias := 1.0, tunnelBias := 1.0, promoteBias := -0.5, gossipBias := 1.0 }
  | .extreme  => { exploreBias := 1.5, tunnelBias := 1.5, promoteBias := -1.0, gossipBias := 0.5 }

-- Resulting Logic:
-- Signal becomes a band -> Band changes policy -> Policy changes routing/promotion/budget.
-- State and Admissibility stay untouched.
```

## 3. Comparative Test Plan
Run baseline routing on Hutter shard stats vs. signal-biased routing. Compare:
1. **Route Replacement Rate**
2. **Promotion Count**
3. **Tunnel Count**
4. **Admissibility Stability**

---
*Portable Reference - Gemini CLI*
