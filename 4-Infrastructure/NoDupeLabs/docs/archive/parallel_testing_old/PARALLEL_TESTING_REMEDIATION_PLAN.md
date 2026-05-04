# Parallel Testing Remediation Plan

**Date:** 2026-02-22
**Status:** In Progress

---

## Problem Analysis

### Current State
- **114 tests** use `use_processes=False` (threads only)
- **48 tests** use `use_processes=True` (actual processes)
- **Ratio:** 70% threads vs 30% processes

### Root Causes

1. **Local functions in test methods** - Can't be pickled
   ```python
   def test_something(self):
       def func(x):  # ❌ Can't pickle!
           return x * 2
       Parallel.process_in_parallel(func, items, use_processes=True)  # Will fail
   ```

2. **Lambdas in test code** - Can't be pickled
   ```python
   Parallel.map_parallel(lambda x: x*2, items, use_processes=True)  # ❌ Will fail
   ```

3. **Test methods as functions** - Can't be pickled
   ```python
   def test_something(self):
       Parallel.process_in_parallel(self._double, items, use_processes=True)  # ❌ Will fail
   ```

---

## Files Requiring Updates

### Priority 1: Core Parallel Tests

| File | Lines | Tests | Issue | Action |
|------|-------|-------|-------|--------|
| `test_parallel_logic.py` | 1942 | ~80 | Local functions | Replace with test_helpers |
| `test_parallel_logic_comprehensive.py` | 775 | ~40 | Local functions | Replace with test_helpers |
| `test_parallel_logic_coverage.py` | 1251 | ~78 | Mixed | Add process tests |

### Priority 2: Other Test Files

| File | Issue | Count | Action |
|------|-------|-------|--------|
| `test_100_coverage_final.py` | Local functions | ~10 | Update |
| `test_coverage_gaps_final.py` | Local functions | ~5 | Update |

---

## Remediation Strategy

### Step 1: Import test_helpers
```python
from tests.parallel.test_helpers import (
    square_number,
    double_number,
    identity,
    add_one,
    # ... etc
)
```

### Step 2: Replace Local Functions
```python
# BEFORE
def test_process_in_parallel_basic(self):
    def func(x):
        return x * 2
    results = Parallel.process_in_parallel(func, [1,2,3], use_processes=False)

# AFTER  
def test_process_in_parallel_basic(self):
    # Test with threads (local function OK)
    def func(x):
        return x * 2
    thread_results = Parallel.process_in_parallel(func, [1,2,3], use_processes=False)
    
    # Test with processes (pickle-safe required)
    process_results = Parallel.process_in_parallel(
        double_number, [1,2,3], use_processes=True
    )
    
    assert thread_results == process_results == [2, 4, 6]
```

### Step 3: Add Process-Specific Tests
For each major test, add a companion test that verifies the process path:

```python
def test_process_in_parallel_with_processes(self):
    """Verify ProcessPoolExecutor code path works."""
    items = [1, 2, 3, 4, 5]
    
    results = Parallel.process_in_parallel(
        double_number,  # ✅ Pickle-safe
        items,
        workers=2,
        use_processes=True  # ✅ Actually test processes
    )
    
    assert results == [2, 4, 6, 8, 10]
```

---

## Implementation Checklist

### test_parallel_logic.py
- [ ] Import test_helpers at top
- [ ] Replace local functions in 20+ tests
- [ ] Add use_processes=True variants
- [ ] Add process-specific tests

### test_parallel_logic_comprehensive.py
- [ ] Import test_helpers at top
- [ ] Replace local functions in 15+ tests
- [ ] Add use_processes=True variants

### test_parallel_logic_coverage.py
- [ ] Import test_helpers at top
- [ ] Add process tests for uncovered paths
- [ ] Verify InterpreterPoolExecutor mocking

### test_100_coverage_final.py
- [ ] Replace local functions
- [ ] Add process tests

### test_coverage_gaps_final.py
- [ ] Replace local functions
- [ ] Add process tests

---

## Success Metrics

| Metric | Before | Target | After |
|--------|--------|--------|-------|
| Tests with use_processes=True | 48 | 100+ | TBD |
| Tests with use_processes=False | 114 | <100 | TBD |
| Ratio (process:thread) | 30:70 | 50:50 | TBD |
| Files using test_helpers | 1 | 6+ | TBD |

---

## Timeline

| Phase | Files | Duration | Status |
|-------|-------|----------|--------|
| 1 | test_parallel_logic.py | 2-3 hours | ⏳ Pending |
| 2 | test_parallel_logic_comprehensive.py | 1-2 hours | ⏳ Pending |
| 3 | test_parallel_logic_coverage.py | 1-2 hours | ⏳ Pending |
| 4 | Other files | 1 hour | ⏳ Pending |
| 5 | Verification | 1 hour | ⏳ Pending |

---

## Notes

- **Don't break existing tests** - Add process variants, don't replace thread tests
- **Use test_helpers consistently** - Import from single source
- **Document why** - Add comments explaining thread vs process choice
- **Measure coverage** - Verify ProcessPoolExecutor paths are now covered
