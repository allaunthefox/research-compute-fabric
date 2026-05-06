# Unreachable Code Analysis

This document identifies and categorizes unreachable code sections in the NoDupeLabs codebase. Each section is classified as:

- **Defensive Code**: Should remain but cannot be tested under normal conditions
- **Dead Code**: Should be removed as it serves no purpose
- **Testable**: Can be tested with special setup or mocking

---

## Summary

| File | Lines | Classification | Recommendation |
|------|-------|---------------|----------------|
| `nodupe/core/api/ipc.py` | 89-92 | Defensive | Keep with pragma |
| `nodupe/core/api/ipc.py` | 137-141 | Defensive | Keep with pragma |
| `nodupe/tools/hashing/autotune_logic.py` | 85-95 | Defensive | Keep with pragma |
| `nodupe/tools/hashing/autotune_logic.py` | 98-117 | Defensive | Keep with pragma |
| `nodupe/tools/hashing/hashing_tool.py` | 17-28 | Defensive | Keep with pragma |
| `nodupe/tools/databases/logging_.py` | 56-57 | By Design | Keep (disabled by design) |
| `nodupe/tools/similarity/__init__.py` | 28-35 | Defensive | Keep with pragma |
| `nodupe/tools/gpu/__init__.py` | 109-115 | Defensive | Keep with pragma |
| `nodupe/tools/gpu/__init__.py` | 194-200 | Defensive | Keep with pragma |
| `nodupe/tools/video/__init__.py` | 103-115 | Defensive | Keep with pragma |
| `nodupe/tools/databases/repository_interface.py` | 41-45 | Abstract | Keep (abstract methods) |

---

## Detailed Analysis

### 1. IPC Rate Limit Check Edge Case

**File:** `/home/prod/Workspaces/repos/github/NoDupeLabs/nodupe/core/api/ipc.py`
**Lines:** 89-92

```python
# Enforce Rate Limiting (Log Policy Compliance)
if not self.rate_limiter.check_rate_limit("ipc_client"):
    self._log_event(ActionCode.RATE_LIMIT_HIT, "Rate limit exceeded for IPC client", level="warning")
    self._send_error(conn, "Rate limit exceeded", None, code=ActionCode.RATE_LIMIT_HIT)
    return
```

**Why Unreachable:**
- The `RateLimiter` is initialized with `requests_per_minute=2000` (1000 requests per 30 seconds)
- The sliding window algorithm in `ratelimit.py` only blocks when requests exceed the limit within the window
- Under normal testing conditions with single-threaded tests, this limit is never reached
- The rate limiter uses a 60-second window, and tests complete well before accumulating 2000 requests

**Classification:** Defensive Code

**Recommendation:** Keep with `# pragma: no cover` - This is important defensive code for production use where high-volume IPC traffic could occur.

---

### 2. Security Risk Flagging (Unreachable with Current Config)

**File:** `/home/prod/Workspaces/repos/github/NoDupeLabs/nodupe/core/api/ipc.py`
**Lines:** 137-141

```python
# Security Risk Flagging
action_code = SENSITIVE_METHODS.get(method_name, ActionCode.FAU_SAR_REQ)
if action_code in RISK_LEVELS:
    risk = RISK_LEVELS[action_code]
    self._log_event(ActionCode.SECURITY_RISK_FLAGGED,
                   f"Sensitive method '{method_name}' called on tool '{tool_name}'",
                   risk_level=risk, tool=tool_name, method=method_name)
```

**Why Unreachable:**
- `SENSITIVE_METHODS` only contains `'extract_archive'` and `'delete_file'`
- These methods are not exposed via IPC in the current tool configuration
- `RISK_LEVELS` only contains codes >= 500000 (error codes), but `SENSITIVE_METHODS` maps to action codes like `OAIS_SIP_INGEST` (120000) and `DEDUP_RECLAIM` (250002)
- The condition `action_code in RISK_LEVELS` will never be True with current configuration

**Classification:** Defensive Code (with configuration issue)

**Recommendation:** Keep with `# pragma: no cover` - This is defensive security code. Consider fixing the `RISK_LEVELS` mapping to include the sensitive method action codes if security flagging is desired.

---

### 3. Optional Dependency Fallbacks (BLAKE3)

**File:** `/home/prod/Workspaces/repos/github/NoDupeLabs/nodupe/tools/hashing/autotune_logic.py`
**Lines:** 85-95

```python
# Add BLAKE3 if available
if HAS_BLAKE3 and BLAKE3_MODULE is not None:
    def blake3_func(data: bytes) -> str:
        """TODO: Document blake3_func."""
        if BLAKE3_MODULE:
            return BLAKE3_MODULE.blake3(data).hexdigest()
        return hashlib.sha256(data).hexdigest()  # fallback
    algorithms['blake3'] = blake3_func
```

**Why Unreachable:**
- `HAS_BLAKE3` is set at module load time based on whether `blake3` package is installed
- In the test environment, `blake3` is always installed (it's a test dependency)
- The inner `if BLAKE3_MODULE:` check is redundant since the outer condition already verifies it's not None
- The fallback `return hashlib.sha256(data).hexdigest()` inside `blake3_func` can never execute

**Classification:** Defensive Code

**Recommendation:** Keep with `# pragma: no cover` - This provides graceful degradation for environments without BLAKE3. Consider removing the redundant inner check.

---

### 4. Optional Dependency Fallbacks (xxHash)

**File:** `/home/prod/Workspaces/repos/github/NoDupeLabs/nodupe/tools/hashing/autotune_logic.py`
**Lines:** 98-117

```python
# Add xxHash if available
if HAS_XXHASH and XXHASH_MODULE is not None:
    def xxh3_func(data: bytes) -> str:
        """TODO: Document xxh3_func."""
        if XXHASH_MODULE:
            return XXHASH_MODULE.xxh3_64(data).hexdigest()
        return hashlib.sha256(data).hexdigest()  # fallback
    # ... similar for xxh64_func and xxh128_func
```

**Why Unreachable:**
- Same pattern as BLAKE3 above
- `xxhash` is installed in test environment
- The fallback paths inside the hash functions are never executed

**Classification:** Defensive Code

**Recommendation:** Keep with `# pragma: no cover` - Provides graceful degradation. Consider refactoring to remove redundant checks.

---

### 5. Import Fallback (Standalone Execution)

**File:** `/home/prod/Workspaces/repos/github/NoDupeLabs/nodupe/tools/hashing/hashing_tool.py`
**Lines:** 17-28

```python
# Standard High-Assurance Import Pattern for standalone tools
try:
    from nodupe.core.tool_system.base import Tool, ToolMetadata
    from .hasher_logic import FileHasher
except (ImportError, ValueError):
    # Stand-alone mode: resolve parent paths manually
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, "../../../"))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    from nodupe.core.tool_system.base import Tool, ToolMetadata
    from nodupe.tools.hashing.hasher_logic import FileHasher
```

**Why Unreachable:**
- When running as part of the installed package, the first import always succeeds
- The fallback path is only triggered when running the file directly outside the package context
- In test environment, the package is always installed, so imports succeed on first try

**Classification:** Defensive Code

**Recommendation:** Keep with `# pragma: no cover` - This is important for standalone script execution. The fallback enables the tool to run independently.

---

### 6. Disabled Logging Path (By Design)

**File:** `/home/prod/Workspaces/repos/github/NoDupeLabs/nodupe/tools/databases/logging_.py`
**Lines:** 56-57

```python
if not self.enabled:
    return
```

**Why Unreachable:**
- `self.enabled` is initialized to `True` and never set to `False` in normal operation
- The `set_enabled(False)` method exists but is not called anywhere in the codebase
- This is intentionally designed as an early-exit guard for future functionality

**Classification:** By Design (Defensive)

**Recommendation:** Keep without pragma - This is a design feature allowing runtime disabling of logging. Tests could be added to cover this path by calling `set_enabled(False)`.

---

### 7. Optional Dependency Fallbacks (NumPy/FAISS)

**File:** `/home/prod/Workspaces/repos/github/NoDupeLabs/nodupe/tools/similarity/__init__.py`
**Lines:** 28-35

```python
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    np = None
    NUMPY_AVAILABLE = False

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    faiss = None
    FAISS_AVAILABLE = False
```

**Why Unreachable:**
- NumPy and FAISS are installed in the test environment
- The `except ImportError` blocks are never executed during testing
- These are module-level guards for optional dependencies

**Classification:** Defensive Code

**Recommendation:** Keep with `# pragma: no cover` on the except blocks - Essential for graceful degradation when optional dependencies are missing.

---

### 8. Optional Dependency Fallbacks (CUDA/PyTorch)

**File:** `/home/prod/Workspaces/repos/github/NoDupeLabs/nodupe/tools/gpu/__init__.py`
**Lines:** 109-115, 194-200

```python
# CUDA Backend (lines 109-115)
except ImportError:
    logger.warning("PyTorch not available for CUDA backend")
except Exception as e:
    logger.error(f"Failed to initialize CUDA backend: {e}")

# Metal Backend (lines 194-200)
except ImportError:
    logger.warning("PyTorch not available for Metal backend")
except Exception as e:
    logger.error(f"Failed to initialize Metal backend: {e}")
```

**Why Unreachable:**
- PyTorch is installed in the test environment
- CUDA/Metal hardware may not be available, but the ImportError for PyTorch itself won't occur
- The `Exception` handlers catch initialization failures that don't occur in test environment

**Classification:** Defensive Code

**Recommendation:** Keep with `# pragma: no cover` - Critical for supporting diverse hardware configurations.

---

### 9. Optional Dependency Fallbacks (OpenCV/PIL)

**File:** `/home/prod/Workspaces/repos/github/NoDupeLabs/nodupe/tools/video/__init__.py`
**Lines:** 103-115

```python
try:
    import cv2
    frame = cv2.imread(str(frame_path))
    if frame is not None:
        frames.append(frame)
except ImportError:
    # Fallback: use PIL if OpenCV not available
    try:
        from PIL import Image
        frame = np.array(Image.open(frame_path))
        frames.append(frame)
    except ImportError:
        logger.warning("Neither OpenCV nor PIL available for frame loading")
```

**Why Unreachable:**
- OpenCV is installed in the test environment
- The nested fallback to PIL and the warning for neither being available never execute

**Classification:** Defensive Code

**Recommendation:** Keep with `# pragma: no cover` - Provides graceful degradation for video processing.

---

### 10. Abstract Method Stubs

**File:** `/home/prod/Workspaces/repos/github/NoDupeLabs/nodupe/tools/databases/repository_interface.py`
**Lines:** 41-45, 86-90

```python
def create(self, table: str, data: Dict[str, Any]) -> int:
    """Create a new record in the specified table."""
    raise NotImplementedError("create must be implemented by subclasses")

def read(self, table: str, record_id: int) -> Optional[Dict[str, Any]]:
    """Read a record by ID from the specified table."""
    raise NotImplementedError("read must be implemented by subclasses")
```

**Why Unreachable:**
- These are abstract method stubs in a base class
- They're designed to be overridden by subclasses
- Calling these directly would be a programming error

**Classification:** Abstract Interface (Not truly unreachable - error path)

**Recommendation:** Keep without pragma - This is the standard Python pattern for abstract methods before ABC enforcement. Consider using `@abstractmethod` decorator instead.

---

## Recommendations Summary

### Immediate Actions

1. **Apply `# pragma: no cover` comments** to all defensive code sections (Items 1-5, 7-9)
2. **Add tests** for Item 6 (disabled logging path) by calling `set_enabled(False)`
3. **Consider refactoring** Item 10 to use `@abstractmethod` decorator for clearer intent

### Code Quality Improvements

1. **Fix RISK_LEVELS mapping** in `codes.py` to include sensitive method action codes if security flagging is desired
2. **Remove redundant inner checks** in `autotune_logic.py` hash function definitions
3. **Document the standalone execution pattern** more clearly in `hashing_tool.py`

### Dead Code Candidates

None identified. All unreachable code serves a defensive or design purpose.

---

## Files Modified

After applying pragmas, the following files will have `# pragma: no cover` comments:

- `nodupe/core/api/ipc.py`
- `nodupe/tools/hashing/autotune_logic.py`
- `nodupe/tools/hashing/hashing_tool.py`
- `nodupe/tools/similarity/__init__.py`
- `nodupe/tools/gpu/__init__.py`
- `nodupe/tools/video/__init__.py`

---

## Verification

To verify coverage exclusions are working:

```bash
pytest --cov=nodupe --cov-report=term-missing tests/ 2>&1 | grep -E "pragma"
```

Lines marked with `# pragma: no cover` should not appear in the missing lines report.
