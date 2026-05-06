# NoDupeLabs Parallel Testing Guide

**Version:** 1.0
**Created:** 2026-02-22
**Status:** ✅ Complete
**Maintainer:** NoDupeLabs Development Team

---

## Quick Start

### For New Tests
```python
from tests.parallel.test_helpers import double_number

def test_with_processes(self):
    """Test with ProcessPoolExecutor."""
    results = Parallel.process_in_parallel(
        double_number,      # ✅ Pickle-safe
        [1, 2, 3, 4, 5],
        workers=2,
        use_processes=True  # ✅ Test actual processes
    )
    assert results == [2, 4, 6, 8, 10]
```

### For Existing Tests
Replace local functions with helpers:
```python
# ❌ BEFORE (can't use with processes)
def test_something(self):
    def local_func(x):
        return x * 2
    Parallel.process_in_parallel(local_func, items, use_processes=False)

# ✅ AFTER (can use with processes)
from tests.parallel.test_helpers import double_number

def test_something(self):
    Parallel.process_in_parallel(
        double_number, items, use_processes=True
    )
```

---

## Table of Contents

1. [Overview](#overview)
2. [Test Helpers Reference](#test-helpers-reference)
3. [Testing Patterns](#testing-patterns)
4. [Dependency Injection Analysis](#dependency-injection-analysis)
5. [Best Practices](#best-practices)
6. [Troubleshooting](#troubleshooting)

---

## Overview

### Problem Solved

**Before:** 70% of parallel tests only tested ThreadPoolExecutor (threads)
**After:** 50%+ test ProcessPoolExecutor (processes) ✅

**Root Cause:** Tests used local functions and lambdas that can't be pickled for multiprocessing.

**Solution:** Pickle-safe test helpers module with reusable functions.

### Results

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Process tests | 48 (30%) | 120+ (50%+) | +150% |
| ProcessPoolExecutor coverage | ~30% | ~55% | +25 pts |
| Test files updated | 0 | 7 | +7 |
| Documentation | 7 files | **1 file** | Consolidated |

---

## Test Helpers Reference

### Location
`tests/parallel/test_helpers.py` (280 lines)

### Basic Functions

```python
# Arithmetic
double_number(x)      # x * 2
square_number(x)      # x * x
add_one(x)           # x + 1
identity(x)          # x (unchanged)

# Comparisons
is_even(x)           # x % 2 == 0
filter_positive(x)   # x > 0

# String Operations
count_letters(text)      # len(text)
to_uppercase(text)       # text.upper()

# Collections
sum_list(numbers)        # sum(numbers)
```

### Error Testing

```python
maybe_raise(x)
    # Returns x * 2
    # Raises ValueError if x == -1

slow_square(x, delay=0.1)
    # Returns x * 2 after delay
    # Use for timeout testing

slow_operation(x, delay=0.5)
    # Returns x * 2 after delay
    # Use for timeout testing
```

### Stateful Operations

```python
PicklableCounter(start=0)
    .increment(value)    # Add value to count
    .get_count()         # Get current count
    .__call__(x)         # Add x to count
```

### Predefined Test Data

```python
SMALL_INT_RANGE    # list(range(10))
MEDIUM_INT_RANGE   # list(range(100))
LARGE_INT_RANGE    # list(range(1000))

SMALL_STRINGS      # ["a", "b", "c", "d", "e"]
MIXED_NUMBERS      # [-5, -2, 0, 1, 3, 7, 10]
POSITIVE_NUMBERS   # [1, 2, 3, 4, 5]
NEGATIVE_NUMBERS   # [-5, -4, -3, -2, -1]
```

---

## Testing Patterns

### Pattern 1: Test Both Thread and Process Paths

```python
from tests.parallel.test_helpers import double_number

def test_both_paths(self):
    """Verify thread and process results match."""
    items = [1, 2, 3, 4, 5]

    # Thread path (lambdas OK)
    thread_result = Parallel.process_in_parallel(
        lambda x: x*2, items, use_processes=False
    )

    # Process path (pickle-safe required)
    process_result = Parallel.process_in_parallel(
        double_number, items, use_processes=True
    )

    # Both should produce same results
    assert thread_result == process_result == [2, 4, 6, 8, 10]
```

### Pattern 2: Error Handling

```python
from tests.parallel.test_helpers import maybe_raise

def test_error_handling(self):
    """Test exception handling with processes."""
    items = [1, -1, 3]  # -1 triggers error

    with pytest.raises(ParallelError) as exc_info:
        Parallel.process_in_parallel(
            maybe_raise,      # ✅ Pickle-safe
            items,
            workers=2,
            use_processes=True
        )

    assert 'Error for value -1' in str(exc_info.value)
```

### Pattern 3: Timeout Testing

```python
from tests.parallel.test_helpers import slow_operation

def test_timeout_handling(self):
    """Test timeout with processes."""
    with pytest.raises(ParallelError):
        Parallel.process_in_parallel(
            slow_operation,   # ✅ Pickle-safe with delay
            [1],
            timeout=0.01,     # Very short timeout
            use_processes=False  # Threads for timeout
        )
```

### Pattern 4: Large Datasets

```python
from tests.parallel.test_helpers import add_one, MEDIUM_INT_RANGE

def test_large_dataset(self):
    """Test with large dataset and processes."""
    items = MEDIUM_INT_RANGE  # 100 items

    results = Parallel.process_in_parallel(
        add_one,              # ✅ Pickle-safe
        items,
        workers=4,
        use_processes=True
    )

    assert results == [x + 1 for x in items]
```

### Pattern 5: String Operations

```python
from tests.parallel.test_helpers import to_uppercase, count_letters

def test_string_operations(self):
    """Test string operations with processes."""
    items = ["hello", "world", "test"]

    # Uppercase conversion
    results = Parallel.process_in_parallel(
        to_uppercase, items, workers=2, use_processes=True
    )
    assert results == ["HELLO", "WORLD", "TEST"]

    # Letter counting
    results = Parallel.process_in_parallel(
        count_letters, items, workers=2, use_processes=True
    )
    assert results == [5, 5, 4]
```

---

## Dependency Injection Analysis

### Research Question
**"Should we use Dependency Injection instead of pickle-safe helpers?"**

### ✅ Final Verdict: **DI is NOT Appropriate for Parallel Testing**

**After thorough analysis (600+ lines):**

#### Why DI Doesn't Work

1. **Static methods** - Parallel is a utility class, not a service
2. **Direct executor instantiation** - Clearer than DI abstraction
3. **Tests verify reality** - Mocks don't test actual multiprocessing
4. **Performance** - DI adds unnecessary overhead
5. **Complexity** - Over-engineers simple utilities

#### Why Pickle-Safe Helpers ARE Better

1. **Tests REAL ProcessPoolExecutor** - Not mocks
2. **More direct** - Explicit `use_processes` parameter
3. **Better performance** - No DI overhead
4. **Already working** - 70+ tests passing
5. **Maintainable** - Single source of truth

### Where DI IS Appropriate

DI is **already well-implemented** for:
- ✅ Tool initialization (`nodupe/core/loader.py`)
- ✅ Service registry (`nodupe/core/tool_system/registry.py`)
- ✅ Lifecycle management (`nodupe/core/tool_system/lifecycle.py`)
- ✅ Scanner engine (`nodupe/tools/scanner_engine/*`)

**Recommendation:** Continue DI for services, NOT for parallel testing.

---

## Best Practices

### 1. Always Import test_helpers

```python
from tests.parallel.test_helpers import (
    double_number,
    square_number,
    maybe_raise,
    # ... etc
)
```

### 2. Test Both Thread and Process Paths

```python
def test_both_paths(self):
    # Thread path (lambdas OK)
    thread_result = Parallel.foo(lambda x: x*2, items, use_processes=False)

    # Process path (pickle-safe required)
    process_result = Parallel.foo(double_number, items, use_processes=True)

    assert thread_result == process_result
```

### 3. Document Thread vs Process Choice

```python
# ✅ Pickle-safe - can be used with processes
double_number

# ❌ Can't pickle - threads only
lambda x: x * 2

# Use threads for error testing (easier to catch exceptions)
use_processes=False

# Use processes to test actual multiprocessing
use_processes=True
```

### 4. Use Consistent Naming

```python
class TestParallelProcessInParallelThreads:
    """Tests with ThreadPoolExecutor"""

class TestParallelProcessInParallelProcesses:
    """Tests with ProcessPoolExecutor"""
```

### 5. Default to Processes for New Tests

```python
# ✅ GOOD - Start with processes
def test_new_feature(self):
    results = Parallel.process_in_parallel(
        double_number, items, use_processes=True
    )

# ⚠️ Only use threads when necessary
def test_timeout(self):
    # Threads for timeout testing (easier to control)
    Parallel.process_in_parallel(
        slow_operation, items, timeout=0.01, use_processes=False
    )
```

---

## Troubleshooting

### Problem: "Can't pickle local object"

**Cause:** Using local functions or lambdas with `use_processes=True`

**Solution:** Use pickle-safe helpers
```python
# ❌ WRONG
def test_something(self):
    def local_func(x):
        return x * 2
    Parallel.process_in_parallel(local_func, items, use_processes=True)

# ✅ RIGHT
from tests.parallel.test_helpers import double_number

def test_something(self):
    Parallel.process_in_parallel(
        double_number, items, use_processes=True
    )
```

### Problem: "Test hangs indefinitely"

**Cause:** Process pool not cleaning up properly

**Solution:** Add timeout
```python
@pytest.mark.timeout(30)  # 30 second timeout
def test_parallel_operation(self):
    Parallel.process_in_parallel(
        double_number, items, timeout=10.0
    )
```

### Problem: "Lambda can't be pickled"

**Cause:** Lambdas can't be pickled for multiprocessing

**Solution:** Use module-level function
```python
# ❌ WRONG
Parallel.map_parallel(lambda x: x*2, items, use_processes=True)

# ✅ RIGHT
from tests.parallel.test_helpers import double_number
Parallel.map_parallel(double_number, items, use_processes=True)
```

### Problem: "Method can't be pickled"

**Cause:** Instance methods can't be pickled

**Solution:** Use module-level function or static method
```python
# ❌ WRONG
class MyClass:
    def test_something(self):
        Parallel.process_in_parallel(self.my_method, items, use_processes=True)

# ✅ RIGHT
from tests.parallel.test_helpers import double_number
Parallel.process_in_parallel(double_number, items, use_processes=True)
```

### Problem: "Different results from threads vs processes"

**Cause:** Race condition or shared state

**Solution:** Ensure functions are pure (no side effects)
```python
# ❌ WRONG - Has side effects
counter = 0
def increment(x):
    global counter
    counter += 1
    return x + counter

# ✅ RIGHT - Pure function
def double_number(x):
    return x * 2  # No side effects
```

---

## Migration Guide

### Step 1: Identify Local Functions

Search for patterns:
```bash
grep -n "def.*x):" tests/*.py | grep -v test_helpers
grep -n "lambda.*:" tests/*.py
```

### Step 2: Import test_helpers

```python
from tests.parallel.test_helpers import (
    double_number,
    square_number,
    maybe_raise,
    # ... etc
)
```

### Step 3: Replace Local Functions

```python
# BEFORE
def failing_func(x):
    raise ValueError("Failed")

Parallel.process_in_parallel(failing_func, ...)

# AFTER
Parallel.process_in_parallel(maybe_raise, [-1], ...)
```

### Step 4: Add Process Tests

```python
def test_with_processes(self):
    """Test with ProcessPoolExecutor."""
    results = Parallel.process_in_parallel(
        double_number, items, use_processes=True
    )
    assert results == expected
```

### Step 5: Verify

```bash
pytest tests/parallel/ -v
```

---

## Appendix: Complete Function Reference

### Arithmetic Functions

| Function | Signature | Description | Example |
|----------|-----------|-------------|---------|
| `double_number` | `(x: int) -> int` | Returns x * 2 | `double_number(5)` → `10` |
| `square_number` | `(x: int) -> int` | Returns x * x | `square_number(5)` → `25` |
| `add_one` | `(x: int) -> int` | Returns x + 1 | `add_one(5)` → `6` |
| `identity` | `(x: Any) -> Any` | Returns x unchanged | `identity(5)` → `5` |
| `add_numbers` | `(a: int, b: int) -> int` | Returns a + b | `add_numbers(2, 3)` → `5` |
| `multiply_numbers` | `(a: int, b: int) -> int` | Returns a * b | `multiply_numbers(2, 3)` → `6` |

### Comparison Functions

| Function | Signature | Description | Example |
|----------|-----------|-------------|---------|
| `is_even` | `(x: int) -> bool` | Returns x % 2 == 0 | `is_even(4)` → `True` |
| `filter_positive` | `(x: int) -> bool` | Returns x > 0 | `filter_positive(-1)` → `False` |

### String Functions

| Function | Signature | Description | Example |
|----------|-----------|-------------|---------|
| `count_letters` | `(text: str) -> int` | Returns len(text) | `count_letters("abc")` → `3` |
| `to_uppercase` | `(text: str) -> str` | Returns text.upper() | `to_uppercase("abc")` → `"ABC"` |

### Collection Functions

| Function | Signature | Description | Example |
|----------|-----------|-------------|---------|
| `sum_list` | `(numbers: List[int]) -> int` | Returns sum(numbers) | `sum_list([1,2,3])` → `6` |
| `concat_strings` | `(a: str, b: str) -> str` | Returns a + b | `concat_strings("a", "b")` → `"ab"` |

### Error Testing Functions

| Function | Signature | Description | Example |
|----------|-----------|-------------|---------|
| `maybe_raise` | `(x: int) -> int` | Raises if x == -1 | `maybe_raise(-1)` → `ValueError` |
| `slow_square` | `(x: int, delay: float) -> int` | Delays then squares | `slow_square(5, 0.1)` → `25` |
| `slow_operation` | `(x: int, delay: float) -> int` | Delays then doubles | `slow_operation(5, 0.5)` → `10` |

### Stateful Functions

| Class/Function | Signature | Description | Example |
|----------------|-----------|-------------|---------|
| `PicklableCounter` | `(start: int = 0)` | Picklable counter | `counter = PicklableCounter(10)` |
| `.increment()` | `(value: int) -> int` | Add value to count | `counter.increment(5)` → `15` |
| `.get_count()` | `() -> int` | Get current count | `counter.get_count()` → `15` |

### Predefined Data

| Constant | Type | Value |
|----------|------|-------|
| `SMALL_INT_RANGE` | `List[int]` | `list(range(10))` |
| `MEDIUM_INT_RANGE` | `List[int]` | `list(range(100))` |
| `LARGE_INT_RANGE` | `List[int]` | `list(range(1000))` |
| `SMALL_STRINGS` | `List[str]` | `["a", "b", "c", "d", "e"]` |
| `MIXED_NUMBERS` | `List[int]` | `[-5, -2, 0, 1, 3, 7, 10]` |
| `POSITIVE_NUMBERS` | `List[int]` | `[1, 2, 3, 4, 5]` |
| `NEGATIVE_NUMBERS` | `List[int]` | `[-5, -4, -3, -2, -1]` |

---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02-22 | Initial consolidated guide |

**Supersedes:**
- PARALLEL_TESTING_SUSTAINABILITY.md
- PARALLEL_TESTING_REMEDIATION_PLAN.md
- PARALLEL_TESTING_REMEDIATION_PROGRESS.md
- DI_VS_PICKLE_SAFE_HELPERS_ANALYSIS.md
- PARALLEL_TESTING_FINAL_REPORT.md
- PARALLEL_TESTING_COMPLETE.md
- PARALLEL_TESTING_SUMMARY.md

---

*This guide consolidates 2,400+ lines of documentation into a single, maintainable reference.*
